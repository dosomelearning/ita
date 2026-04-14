import { MockStateGateway, type JobCompletionResult, type JobPhase, type RankingEntry } from "./mockGateways";

export interface StateGateway {
  awaitJobCompletion(jobId: string, onPhase: (phase: JobPhase) => void): Promise<JobCompletionResult>;
  getRanking(): Promise<RankingEntry[]>;
  setFailNext?(shouldFail: boolean): void;
  getDebugInfo?(): { mode: "mock" | "ms4"; baseUrl?: string };
}

interface Ms4StatusResponse {
  uploadId: string;
  status: JobPhase;
  updatedAt?: string;
  progress?: Record<string, unknown> | null;
  results?: Record<string, unknown> | null;
  error?: {
    code?: string;
    message?: string;
    retryable?: boolean;
    details?: Record<string, unknown>;
  } | null;
}

interface GatewayConfig {
  mode: "mock" | "ms4";
  ms4BaseUrl: string;
}

interface Ms4GatewayOptions {
  pollIntervalMs?: number;
  maxWaitMs?: number;
  maxNotFoundResponses?: number;
  fetchImpl?: typeof fetch;
  waitImpl?: (ms: number) => Promise<void>;
}

const DEFAULT_POLL_INTERVAL_MS = 1500;
const DEFAULT_MAX_WAIT_MS = 120000;
const DEFAULT_MAX_NOT_FOUND_RESPONSES = 10;

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

function normalizeBaseUrl(input: string): string {
  return input.trim().replace(/\/+$/, "");
}

export function readGatewayConfig(env: Record<string, string | undefined> = import.meta.env): GatewayConfig {
  const modeRaw = (env.VITE_STATE_GATEWAY_MODE ?? "mock").trim().toLowerCase();
  const mode = modeRaw === "ms4" ? "ms4" : "mock";
  const ms4BaseUrl = normalizeBaseUrl(env.VITE_MS4_API_BASE_URL ?? "");
  return { mode, ms4BaseUrl };
}

export class Ms4StateGateway implements StateGateway {
  private readonly rankingGateway: MockStateGateway;
  private readonly fetchImpl: typeof fetch;
  private readonly waitImpl: (ms: number) => Promise<void>;
  private readonly pollIntervalMs: number;
  private readonly maxWaitMs: number;
  private readonly maxNotFoundResponses: number;

  constructor(
    private readonly ms4BaseUrl: string,
    options: Ms4GatewayOptions = {},
    rankingGateway: MockStateGateway = new MockStateGateway()
  ) {
    this.rankingGateway = rankingGateway;
    this.fetchImpl = options.fetchImpl ?? globalThis.fetch.bind(globalThis);
    this.waitImpl = options.waitImpl ?? wait;
    this.pollIntervalMs = options.pollIntervalMs ?? DEFAULT_POLL_INTERVAL_MS;
    this.maxWaitMs = options.maxWaitMs ?? DEFAULT_MAX_WAIT_MS;
    this.maxNotFoundResponses = options.maxNotFoundResponses ?? DEFAULT_MAX_NOT_FOUND_RESPONSES;
  }

  async awaitJobCompletion(jobId: string, onPhase: (phase: JobPhase) => void): Promise<JobCompletionResult> {
    const startedAt = Date.now();
    const seenPhases = new Set<JobPhase>();
    let notFoundResponses = 0;

    while (Date.now() - startedAt <= this.maxWaitMs) {
      const statusResult = await this.fetchStatus(jobId);

      if (statusResult.kind === "not_found") {
        notFoundResponses += 1;
        if (notFoundResponses > this.maxNotFoundResponses) {
          return {
            status: "failed",
            message: "Upload status not found in MS4. Retry after MS1 is connected.",
          };
        }
        await this.waitImpl(this.pollIntervalMs);
        continue;
      }

      if (statusResult.kind === "error") {
        return {
          status: "failed",
          message: statusResult.message,
        };
      }

      const status = statusResult.payload.status;
      if (!seenPhases.has(status)) {
        seenPhases.add(status);
        onPhase(status);
      }

      if (status === "completed") {
        return { status: "completed" };
      }
      if (status === "failed") {
        const apiMessage = statusResult.payload.error?.message;
        return {
          status: "failed",
          message: apiMessage || "Processing failed.",
        };
      }

      await this.waitImpl(this.pollIntervalMs);
    }

    return {
      status: "failed",
      message: "Timed out waiting for processing status from MS4.",
    };
  }

  async getRanking(): Promise<RankingEntry[]> {
    return this.rankingGateway.getRanking();
  }

  getDebugInfo(): { mode: "mock" | "ms4"; baseUrl?: string } {
    return { mode: "ms4", baseUrl: this.ms4BaseUrl };
  }

  private async fetchStatus(
    jobId: string
  ): Promise<{ kind: "ok"; payload: Ms4StatusResponse } | { kind: "not_found" } | { kind: "error"; message: string }> {
    const endpoint = `${this.ms4BaseUrl}/v1/uploads/${encodeURIComponent(jobId)}/status`;
    let response: Response;
    try {
      response = await this.fetchImpl(endpoint, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
    } catch (error) {
      const message = formatFetchError(error);
      return {
        kind: "error",
        message: `Status request to MS4 failed (${message}). Endpoint: ${endpoint}`,
      };
    }

    if (response.status === 404) {
      return { kind: "not_found" };
    }

    const payload = await parseJsonBody(response);
    if (!response.ok) {
      const message =
        typeof payload?.error?.message === "string" && payload.error.message.length > 0
          ? payload.error.message
          : "MS4 returned an error while retrieving status.";
      return { kind: "error", message };
    }

    const status = payload?.status;
    if (status !== "queued" && status !== "processing" && status !== "completed" && status !== "failed") {
      return { kind: "error", message: "MS4 response contained invalid status value." };
    }
    return { kind: "ok", payload: payload as Ms4StatusResponse };
  }
}

async function parseJsonBody(response: Response): Promise<any> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export function createStateGateway(env: Record<string, string | undefined> = import.meta.env): StateGateway {
  const config = readGatewayConfig(env);
  if (config.mode === "ms4" && config.ms4BaseUrl.length > 0) {
    return new Ms4StateGateway(config.ms4BaseUrl);
  }
  return new MockStateGatewayAdapter(new MockStateGateway());
}

function formatFetchError(error: unknown): string {
  if (error instanceof Error) {
    const name = error.name || "Error";
    const message = error.message || "no message";
    return `${name}: ${message}`;
  }
  return String(error);
}

class MockStateGatewayAdapter implements StateGateway {
  constructor(private readonly gateway: MockStateGateway) {}

  awaitJobCompletion(jobId: string, onPhase: (phase: JobPhase) => void): Promise<JobCompletionResult> {
    return this.gateway.awaitJobCompletion(jobId, onPhase);
  }

  getRanking(): Promise<RankingEntry[]> {
    return this.gateway.getRanking();
  }

  setFailNext(shouldFail: boolean): void {
    this.gateway.setFailNext(shouldFail);
  }

  getDebugInfo(): { mode: "mock" } {
    return { mode: "mock" };
  }
}
