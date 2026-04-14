import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import { type JobPhase, type RankingEntry } from "./mockGateways";
import { createAuthGateway, createUploadGateway } from "./ingressGateway";
import { createStateGateway, type StateGateway } from "./stateGateway";

type View = "home" | "submit" | "ranking";
type SubmitStatus = "idle" | "validating" | "submitting" | "success" | "failure";

const authGateway = createAuthGateway();
const uploadGateway = createUploadGateway();
const stateGateway = createStateGateway();

function supportsFailureSimulation(
  gateway: StateGateway
): gateway is StateGateway & { setFailNext: (shouldFail: boolean) => void } {
  return "setFailNext" in gateway && typeof gateway.setFailNext === "function";
}

function createInitialJobPhases(): Record<JobPhase, boolean> {
  return {
    queued: false,
    processing: false,
    completed: false,
    failed: false,
  };
}

function createSessionId(): string {
  const date = new Date().toISOString().slice(0, 10);
  const suffix = Math.random().toString(36).slice(2, 10);
  return `spa-${date}-${suffix}`;
}

function App() {
  const [view, setView] = useState<View>("home");
  const [nickname, setNickname] = useState("");
  const [password, setPassword] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>("idle");
  const [submitMessage, setSubmitMessage] = useState("No submission yet.");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobPhases, setJobPhases] = useState(createInitialJobPhases);
  const [ranking, setRanking] = useState<RankingEntry[]>([]);
  const [rankingLoading, setRankingLoading] = useState(false);
  const [rankingError, setRankingError] = useState<string | null>(null);
  const [rankingUpdatedAt, setRankingUpdatedAt] = useState<string | null>(null);
  const [latestSubmission, setLatestSubmission] = useState<RankingEntry | null>(null);
  const [forceFailureNextSubmit, setForceFailureNextSubmit] = useState(false);

  const cameraInputRef = useRef<HTMLInputElement | null>(null);
  const libraryInputRef = useRef<HTMLInputElement | null>(null);
  const sessionIdRef = useRef<string>(createSessionId());

  useEffect(() => {
    void refreshRanking();
  }, []);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return;
    }

    const nextPreviewUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(nextPreviewUrl);

    return () => {
      URL.revokeObjectURL(nextPreviewUrl);
    };
  }, [selectedFile]);

  const displayRanking = useMemo(() => {
    if (!latestSubmission) {
      return ranking;
    }

    const withoutLatest = ranking.filter((item) => item.id !== latestSubmission.id);
    return [latestSubmission, ...withoutLatest].sort((a, b) => b.score - a.score);
  }, [latestSubmission, ranking]);

  const rankingPreview = useMemo(() => displayRanking.slice(0, 5), [displayRanking]);

  const hasCredentials = password.trim().length > 0 && nickname.trim().length > 0;
  const canSubmit = selectedFile !== null && hasCredentials;
  const canSimulateFailure = supportsFailureSimulation(stateGateway);
  const gatewayDebug = stateGateway.getDebugInfo?.() ?? { mode: "unknown" };
  const ingressDebug = authGateway.getDebugInfo?.() ?? { mode: "unknown" };
  const uploadDebug = uploadGateway.getDebugInfo?.() ?? { mode: "unknown" };

  function resetSubmitState() {
    setSubmitStatus("idle");
    setSubmitMessage("Ready to submit.");
    setUploadProgress(0);
    setJobPhases(createInitialJobPhases());
  }

  function onSelectFile(file: File | null) {
    if (!file) {
      return;
    }
    setSelectedFile(file);
    resetSubmitState();
    setView("submit");
  }

  function onCameraInputChange(event: ChangeEvent<HTMLInputElement>) {
    onSelectFile(event.target.files?.[0] ?? null);
    event.target.value = "";
  }

  function onLibraryInputChange(event: ChangeEvent<HTMLInputElement>) {
    onSelectFile(event.target.files?.[0] ?? null);
    event.target.value = "";
  }

  async function refreshRanking() {
    setRankingLoading(true);
    setRankingError(null);
    try {
      const nextRanking = await stateGateway.getRanking();
      setRanking(nextRanking);
      setRankingUpdatedAt(new Date().toLocaleTimeString());
    } catch {
      setRankingError("Failed to load ranking. Try refreshing.");
    } finally {
      setRankingLoading(false);
    }
  }

  function markJobPhase(phase: JobPhase) {
    setJobPhases((prev) => ({
      ...prev,
      [phase]: true,
    }));
  }

  async function onSubmitPhoto() {
    if (!selectedFile) {
      setSubmitStatus("failure");
      setSubmitMessage("Choose a photo first.");
      return;
    }

    if (!password.trim()) {
      setSubmitStatus("failure");
      setSubmitMessage("Enter class code before submitting.");
      return;
    }

    if (!nickname.trim()) {
      setSubmitStatus("failure");
      setSubmitMessage("Enter nickname before submitting.");
      return;
    }

    setSubmitStatus("validating");
    setSubmitMessage("Validating class code...");
    setUploadProgress(0);
    setJobPhases(createInitialJobPhases());

    try {
      if (supportsFailureSimulation(stateGateway)) {
        stateGateway.setFailNext(forceFailureNextSubmit);
      }

      const initResult = await authGateway.initUploadSession({
        password: password.trim(),
        nickname: nickname.trim(),
        sessionId: sessionIdRef.current,
        contentType: selectedFile.type || "image/jpeg",
        originalFilename: selectedFile.name,
        fileSizeBytes: selectedFile.size,
      });
      if (!initResult.accepted) {
        setSubmitStatus("failure");
        setSubmitMessage(initResult.message ?? "Class code is invalid.");
        return;
      }

      setSubmitStatus("submitting");
      setSubmitMessage("Uploading photo...");
      await uploadGateway.uploadPhoto(
        initResult.uploadTarget,
        selectedFile,
        (progress) => {
          setUploadProgress(progress);
        },
        initResult.uploadHeaders
      );

      setSubmitMessage("Photo accepted. Processing...");
      const finalResult = await stateGateway.awaitJobCompletion(initResult.jobId, (phase) => {
        markJobPhase(phase);
      });

      if (finalResult.status === "completed") {
        setSubmitStatus("success");
        setSubmitMessage(`Photo processed successfully for ${nickname.trim()}.`);
        setLatestSubmission({
          id: `local-${nickname.trim().toLowerCase()}`,
          name: nickname.trim(),
          score: 31 + Math.floor(Math.random() * 7),
          lastUpdateLabel: new Date().toLocaleTimeString(),
        });
        void refreshRanking();
      } else {
        setSubmitStatus("failure");
        setSubmitMessage(finalResult.message ?? "Processing failed.");
      }
    } catch (error) {
      setSubmitStatus("failure");
      const message = error instanceof Error ? error.message : "Submission failed. Check connection and retry.";
      setSubmitMessage(message);
    } finally {
      setForceFailureNextSubmit(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <h1>ITA Photo Flow</h1>
        <p>Capture or choose a photo, then submit with class code.</p>
      </header>

      <section className="view-card">
        {view === "home" && (
          <>
            <h2>Session Entry</h2>
            <div className="credentials-row">
              <div className="field-group">
                <label className="label" htmlFor="nickname">
                  Nickname
                </label>
                <input
                  id="nickname"
                  className="input"
                  type="text"
                  inputMode="text"
                  autoComplete="nickname"
                  value={nickname}
                  onChange={(event) => setNickname(event.target.value)}
                  placeholder="Your display name"
                />
              </div>
              <div className="field-group">
                <label className="label" htmlFor="class-code">
                  Code
                </label>
                <input
                  id="class-code"
                  className="input"
                  type="text"
                  inputMode="text"
                  autoComplete="off"
                  value={password}
                  maxLength={6}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="6-char code"
                />
              </div>
            </div>
            <div className="actions-grid">
              <button
                className="btn btn-primary"
                type="button"
                disabled={!hasCredentials}
                onClick={() => cameraInputRef.current?.click()}
              >
                Capture Photo
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                disabled={!hasCredentials}
                onClick={() => libraryInputRef.current?.click()}
              >
                Choose Photo
              </button>
            </div>

            <section className="ranking-panel">
              <div className="panel-header">
                <h3>Ranking Preview</h3>
                <button className="link-btn" type="button" onClick={() => void refreshRanking()}>
                  Refresh
                </button>
              </div>
              {rankingLoading && <p className="muted">Loading ranking...</p>}
              {rankingError && <p className="status-error">{rankingError}</p>}
              {!rankingLoading && !rankingError && rankingPreview.length === 0 && (
                <p className="muted">No ranking data yet.</p>
              )}
              {!rankingLoading && !rankingError && rankingPreview.length > 0 && (
                <ol className="ranking-list">
                  {rankingPreview.map((item) => (
                    <li key={item.id}>
                      <span>{item.name}</span>
                      <strong>{item.score}</strong>
                    </li>
                  ))}
                </ol>
              )}
              <p className="muted">Updated: {rankingUpdatedAt ?? "not yet"}</p>
            </section>
          </>
        )}

        {view === "submit" && (
          <>
            <h2>Capture and Submit</h2>
            {previewUrl ? (
              <img className="preview" src={previewUrl} alt="Selected preview" />
            ) : (
              <p className="muted">No photo selected yet.</p>
            )}
            <p className="muted">
              {selectedFile
                ? `${selectedFile.name} (${Math.round(selectedFile.size / 1024)} KB)`
                : "Use capture or choose buttons to select a photo."}
            </p>

            <div className="actions-grid">
              <button
                className="btn btn-secondary"
                type="button"
                disabled={!hasCredentials}
                onClick={() => cameraInputRef.current?.click()}
              >
                Retake
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                disabled={!hasCredentials}
                onClick={() => libraryInputRef.current?.click()}
              >
                Change Photo
              </button>
            </div>

            <button className="btn btn-primary btn-block" type="button" disabled={!canSubmit} onClick={onSubmitPhoto}>
              Submit
            </button>

            {canSimulateFailure && (
              <label className="checkbox-row" htmlFor="force-failure">
                <input
                  id="force-failure"
                  type="checkbox"
                  checked={forceFailureNextSubmit}
                  onChange={(event) => setForceFailureNextSubmit(event.target.checked)}
                />
                Simulate failure on next submit
              </label>
            )}

            <section className="status-panel">
              <h3>Status</h3>
              <p className={`status status-${submitStatus}`}>{submitMessage}</p>
              <p className="muted">
                Gateway: {gatewayDebug.mode}
                {gatewayDebug.mode === "ms4" && gatewayDebug.baseUrl ? ` (${gatewayDebug.baseUrl})` : ""}
              </p>
              <p className="muted">
                Ingress: {ingressDebug.mode}
                {ingressDebug.mode === "ms1" && ingressDebug.baseUrl ? ` (${ingressDebug.baseUrl})` : ""}
              </p>
              <p className="muted">Upload: {uploadDebug.mode}</p>
              <p className="muted">Upload progress: {uploadProgress}%</p>
              <ul className="phase-list">
                <li className={jobPhases.queued ? "active" : ""}>Queued</li>
                <li className={jobPhases.processing ? "active" : ""}>Processing</li>
                <li className={jobPhases.completed ? "active success" : ""}>Completed</li>
                <li className={jobPhases.failed ? "active error" : ""}>Failed</li>
              </ul>
            </section>
          </>
        )}

        {view === "ranking" && (
          <>
            <div className="panel-header">
              <h2>Ranking</h2>
              <button className="link-btn" type="button" onClick={() => void refreshRanking()}>
                Refresh
              </button>
            </div>
            {rankingLoading && <p className="muted">Loading ranking...</p>}
            {rankingError && <p className="status-error">{rankingError}</p>}
            {!rankingLoading && !rankingError && ranking.length === 0 && (
              <p className="muted">No ranking data yet.</p>
            )}
            {!rankingLoading && !rankingError && displayRanking.length > 0 && (
              <ol className="ranking-list ranking-list-full">
                {displayRanking.map((item) => (
                  <li key={item.id}>
                    <div>
                      <span>{item.name}</span>
                      <small>{item.lastUpdateLabel}</small>
                    </div>
                    <strong>{item.score}</strong>
                  </li>
                ))}
              </ol>
            )}
          </>
        )}
      </section>

      <nav className="bottom-nav" aria-label="Main navigation">
        <button
          className={`nav-btn ${view === "home" ? "active" : ""}`}
          type="button"
          onClick={() => setView("home")}
        >
          Home
        </button>
        <button
          className={`nav-btn ${view === "submit" ? "active" : ""}`}
          type="button"
          onClick={() => setView("submit")}
        >
          Submit
        </button>
        <button
          className={`nav-btn ${view === "ranking" ? "active" : ""}`}
          type="button"
          onClick={() => setView("ranking")}
        >
          Ranking
        </button>
      </nav>

      <input
        ref={cameraInputRef}
        className="hidden-input"
        type="file"
        accept="image/*"
        capture="environment"
        onChange={onCameraInputChange}
      />
      <input
        ref={libraryInputRef}
        className="hidden-input"
        type="file"
        accept="image/*"
        onChange={onLibraryInputChange}
      />
    </main>
  );
}

export default App;
