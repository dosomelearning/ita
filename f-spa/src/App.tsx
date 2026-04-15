import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { type ActivityEntry, type JobPhase } from "./mockGateways";
import { createAuthGateway, createUploadGateway } from "./ingressGateway";
import { createStateGateway, type StateGateway } from "./stateGateway";

type View = "home" | "submit" | "activity";
type SubmitStatus = "idle" | "validating" | "submitting" | "success" | "failure";
const ACTIVITY_LIMIT = 200;

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
  const [classRunId, setClassRunId] = useState<string>("");
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [activitiesLoading, setActivitiesLoading] = useState(false);
  const [activitiesError, setActivitiesError] = useState<string | null>(null);
  const [activitiesUpdatedAt, setActivitiesUpdatedAt] = useState<string | null>(null);
  const [forceFailureNextSubmit, setForceFailureNextSubmit] = useState(false);
  const [lastFaceCount, setLastFaceCount] = useState<number | null>(null);

  const cameraInputRef = useRef<HTMLInputElement | null>(null);
  const libraryInputRef = useRef<HTMLInputElement | null>(null);
  const sessionIdRef = useRef<string>(createSessionId());

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

  useEffect(() => {
    if (!classRunId) {
      return;
    }
    void refreshActivities(classRunId);
  }, [classRunId]);

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
    setLastFaceCount(null);
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

  async function refreshActivities(runId: string) {
    if (!runId.trim()) {
      setActivities([]);
      setActivitiesUpdatedAt(null);
      return;
    }
    setActivitiesLoading(true);
    setActivitiesError(null);
    try {
      const nextItems = await stateGateway.getActivities(runId, ACTIVITY_LIMIT);
      setActivities(nextItems);
      setActivitiesUpdatedAt(new Date().toLocaleTimeString());
    } catch {
      setActivitiesError("Failed to load activity feed. Try refreshing.");
    } finally {
      setActivitiesLoading(false);
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
      const nextClassRunId = initResult.classRunId?.trim() ?? "";
      if (nextClassRunId) {
        setClassRunId(nextClassRunId);
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
        setLastFaceCount(typeof finalResult.faceCount === "number" ? finalResult.faceCount : null);
      } else {
        setSubmitStatus("failure");
        setSubmitMessage(finalResult.message ?? "Processing failed.");
        setLastFaceCount(null);
      }
      if (nextClassRunId) {
        void refreshActivities(nextClassRunId);
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
                <h3>Activity Feed</h3>
                <button
                  className="link-btn"
                  type="button"
                  onClick={() => {
                    if (classRunId) {
                      void refreshActivities(classRunId);
                    }
                  }}
                >
                  Refresh
                </button>
              </div>
              {activitiesLoading && <p className="muted">Loading activities...</p>}
              {activitiesError && <p className="status-error">{activitiesError}</p>}
              {!activitiesLoading && !activitiesError && activities.length === 0 && (
                <p className="muted">No activities yet. Submit a photo to begin.</p>
              )}
              {!activitiesLoading && !activitiesError && activities.length > 0 && (
                <ol className="activity-list">
                  {activities.slice(0, 5).map((item) => (
                    <li className={`activity-item ${activityRowClassName(item)}`} key={`${item.uploadId}-${item.eventTime}-${item.eventType}`}>
                      <div className="activity-main">
                        <strong>{item.nickname}</strong>
                        <small>
                          {item.eventType} · {formatEventTime(item.eventTime)}
                        </small>
                      </div>
                      <div className="activity-meta">
                        <span>{item.producer}</span>
                        <span>{item.statusAfter}</span>
                        {typeof item.faceCount === "number" && <span className="activity-face-count">{item.faceCount}</span>}
                      </div>
                    </li>
                  ))}
                </ol>
              )}
              <p className="muted">Class run: {classRunId || "not initialized yet"}</p>
              <p className="muted">Updated: {activitiesUpdatedAt ?? "not yet"}</p>
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
              {submitStatus === "success" && lastFaceCount !== null && (
                <div className="faces-count-panel">
                  <p className="faces-count-label">Faces Detected</p>
                  <p className="faces-count-number">{lastFaceCount}</p>
                </div>
              )}
            </section>
          </>
        )}

        {view === "activity" && (
          <>
            <div className="panel-header">
              <h2>Activity Feed</h2>
              <button
                className="link-btn"
                type="button"
                onClick={() => {
                  if (classRunId) {
                    void refreshActivities(classRunId);
                  }
                }}
              >
                Refresh
              </button>
            </div>
            {activitiesLoading && <p className="muted">Loading activity feed...</p>}
            {activitiesError && <p className="status-error">{activitiesError}</p>}
            {!activitiesLoading && !activitiesError && activities.length === 0 && (
              <p className="muted">No activities available.</p>
            )}
            {!activitiesLoading && !activitiesError && activities.length > 0 && (
              <ol className="activity-list activity-list-full">
                {activities.map((item) => (
                  <li className={`activity-item ${activityRowClassName(item)}`} key={`${item.uploadId}-${item.eventTime}-${item.eventType}`}>
                    <div className="activity-main">
                      <strong>{item.nickname}</strong>
                      <small>
                        {item.eventType} · {formatEventTime(item.eventTime)}
                      </small>
                    </div>
                    <div className="activity-meta">
                      <span>{item.producer}</span>
                      <span>{item.statusAfter}</span>
                      {typeof item.faceCount === "number" && <span className="activity-face-count">{item.faceCount}</span>}
                    </div>
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
          className={`nav-btn ${view === "activity" ? "active" : ""}`}
          type="button"
          onClick={() => setView("activity")}
        >
          Activity
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

function formatEventTime(eventTime: string): string {
  const parsed = new Date(eventTime);
  if (Number.isNaN(parsed.getTime())) {
    return eventTime;
  }
  return parsed.toLocaleTimeString();
}

function activityRowClassName(item: ActivityEntry): string {
  if (item.statusAfter === "failed") {
    return "activity-item-failed";
  }
  if (item.statusAfter === "completed" && typeof item.faceCount === "number") {
    return "activity-item-completed";
  }
  return "";
}

export default App;
