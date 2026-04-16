import { useEffect, useRef, useState, type CSSProperties, type ChangeEvent } from "react";
import { type ActivityEntry, type JobPhase } from "./mockGateways";
import { createAuthGateway, createUploadGateway } from "./ingressGateway";
import { createStateGateway, type StateGateway } from "./stateGateway";
import {
  sanitizeClassCodeInput,
  sanitizeNicknameInput,
  validateClassCode,
  validateNickname,
} from "./inputValidation";

type View = "home" | "submit" | "activity";
type SubmitStatus = "idle" | "validating" | "submitting" | "success" | "failure";
const ACTIVITY_LIMIT = 200;
const MAX_FACE_COUNT = 99;
const FACE_TILE_SIZE_PX = 40;
const FACE_TILE_GAP_PX = 10;
const MOBILE_FACE_GRID_RESERVED_WIDTH_PX = 200;
const MOBILE_BREAKPOINT_PX = 768;

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
  const [isFaceGridModalOpen, setIsFaceGridModalOpen] = useState(false);
  const [modalFaceCount, setModalFaceCount] = useState<number>(0);
  const [modalFaceTitle, setModalFaceTitle] = useState<string>("Extracted Faces");
  const [viewportWidth, setViewportWidth] = useState<number>(() =>
    typeof window === "undefined" ? 1024 : window.innerWidth
  );

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

  useEffect(() => {
    function onResize() {
      setViewportWidth(window.innerWidth);
    }
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
    };
  }, []);

  useEffect(() => {
    if (!isFaceGridModalOpen) {
      return;
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsFaceGridModalOpen(false);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isFaceGridModalOpen]);

  const nicknameError = validateNickname(nickname);
  const classCodeError = validateClassCode(password);
  const hasValidCredentials = nicknameError === null && classCodeError === null;
  const canSubmit = selectedFile !== null && hasValidCredentials;
  const canSimulateFailure = supportsFailureSimulation(stateGateway);
  const clampedFaceCount = clampFaceCount(lastFaceCount);
  const clampedModalFaceCount = clampFaceCount(modalFaceCount);
  const faceGridColumns = computeFaceGridColumns(clampedModalFaceCount, viewportWidth);
  const faceSlots = createFaceSlots(clampedModalFaceCount);
  const gatewayDebug = stateGateway.getDebugInfo?.() ?? { mode: "unknown" };
  const ingressDebug = authGateway.getDebugInfo?.() ?? { mode: "unknown" };
  const uploadDebug = uploadGateway.getDebugInfo?.() ?? { mode: "unknown" };

  function resetSubmitState() {
    setSubmitStatus("idle");
    setSubmitMessage("Ready to submit.");
    setUploadProgress(0);
    setJobPhases(createInitialJobPhases());
    setLastFaceCount(null);
    setIsFaceGridModalOpen(false);
    setModalFaceCount(0);
    setModalFaceTitle("Extracted Faces");
  }

  function openFaceGridModal(faceCount: number | null | undefined, title: string) {
    const nextFaceCount = clampFaceCount(typeof faceCount === "number" ? faceCount : 0);
    if (nextFaceCount < 1) {
      return;
    }
    setModalFaceCount(nextFaceCount);
    setModalFaceTitle(title);
    setIsFaceGridModalOpen(true);
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

    if (classCodeError) {
      setSubmitStatus("failure");
      setSubmitMessage(classCodeError);
      return;
    }

    if (nicknameError) {
      setSubmitStatus("failure");
      setSubmitMessage(nicknameError);
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
        password,
        nickname,
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
        setSubmitMessage(`Photo processed successfully for ${nickname}.`);
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
                  onChange={(event) => setNickname(sanitizeNicknameInput(event.target.value))}
                  placeholder="Your display name"
                />
                {nickname.length > 0 && nicknameError && <p className="status-error">{nicknameError}</p>}
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
                  onChange={(event) => setPassword(sanitizeClassCodeInput(event.target.value))}
                  placeholder="Class code"
                />
                {password.length > 0 && classCodeError && <p className="status-error">{classCodeError}</p>}
              </div>
            </div>
            <div className="actions-grid">
              <button
                className="btn btn-primary"
                type="button"
                disabled={!hasValidCredentials}
                onClick={() => cameraInputRef.current?.click()}
              >
                Capture Photo
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                disabled={!hasValidCredentials}
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
                        {typeof item.faceCount === "number" && (
                          <button
                            className="activity-face-count-btn"
                            type="button"
                            onClick={() => openFaceGridModal(item.faceCount, `${item.nickname} · ${item.eventType}`)}
                          >
                            <span className="activity-face-count">{item.faceCount}</span>
                          </button>
                        )}
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
                disabled={!hasValidCredentials}
                onClick={() => cameraInputRef.current?.click()}
              >
                Retake
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                disabled={!hasValidCredentials}
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
                  <p className="faces-count-label">Extraction Success</p>
                  <button
                    className="face-count-link"
                    type="button"
                    onClick={() => openFaceGridModal(lastFaceCount, "Latest Submit Result")}
                    disabled={clampedFaceCount < 1}
                  >
                    <span className="faces-count-number">{lastFaceCount}</span>
                    <span className="face-count-link-text">extracted faces</span>
                  </button>
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
                      {typeof item.faceCount === "number" && (
                        <button
                          className="activity-face-count-btn"
                          type="button"
                          onClick={() => openFaceGridModal(item.faceCount, `${item.nickname} · ${item.eventType}`)}
                        >
                          <span className="activity-face-count">{item.faceCount}</span>
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </>
        )}
      </section>

      {isFaceGridModalOpen && (
        <div className="modal-overlay" role="presentation" onClick={() => setIsFaceGridModalOpen(false)}>
          <section
            className="modal-card faces-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Extracted faces matrix"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="panel-header">
              <h3>{modalFaceTitle}</h3>
              <button className="link-btn" type="button" onClick={() => setIsFaceGridModalOpen(false)}>
                Close
              </button>
            </div>
            <p className="muted">
              Empty matrix shell: {clampedModalFaceCount} slot{clampedModalFaceCount === 1 ? "" : "s"}.
            </p>
            <div className="faces-grid" style={{ "--faces-grid-columns": String(faceGridColumns) } as CSSProperties}>
              {faceSlots.map((slotIndex) => (
                <div className="face-slot" key={slotIndex} aria-hidden="true" />
              ))}
            </div>
          </section>
        </div>
      )}

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

function clampFaceCount(faceCount: number | null): number {
  if (typeof faceCount !== "number" || Number.isNaN(faceCount)) {
    return 0;
  }
  return Math.max(0, Math.min(MAX_FACE_COUNT, Math.floor(faceCount)));
}

function createFaceSlots(faceCount: number): number[] {
  return Array.from({ length: faceCount }, (_, index) => index + 1);
}

function computeFaceGridColumns(faceCount: number, viewportWidth: number): number {
  if (faceCount <= 0) {
    return 1;
  }
  const preferredColumns = Math.min(10, Math.max(1, Math.ceil(Math.sqrt(faceCount))));
  if (viewportWidth > MOBILE_BREAKPOINT_PX) {
    return Math.min(faceCount, preferredColumns);
  }

  const mobileAvailableWidth = Math.max(40, viewportWidth - MOBILE_FACE_GRID_RESERVED_WIDTH_PX);
  const mobileMaxColumns = Math.max(
    1,
    Math.floor((mobileAvailableWidth + FACE_TILE_GAP_PX) / (FACE_TILE_SIZE_PX + FACE_TILE_GAP_PX))
  );
  return Math.max(1, Math.min(faceCount, preferredColumns, mobileMaxColumns));
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
