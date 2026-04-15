import { MockAuthGateway, MockUploadGateway } from "./mockGateways";

export interface UploadInitInput {
  password: string;
  nickname: string;
  sessionId: string;
  contentType: string;
  originalFilename?: string;
  fileSizeBytes?: number;
}

export interface InitUploadResult {
  accepted: boolean;
  uploadTarget: string;
  jobId: string;
  classRunId?: string;
  uploadHeaders?: Record<string, string>;
  message?: string;
}

export interface AuthGateway {
  initUploadSession(input: UploadInitInput): Promise<InitUploadResult>;
  getDebugInfo?(): { mode: "mock" | "ms1"; baseUrl?: string };
}

export interface UploadGateway {
  uploadPhoto(
    uploadTarget: string,
    file: File,
    onProgress: (percentage: number) => void,
    uploadHeaders?: Record<string, string>
  ): Promise<void>;
  getDebugInfo?(): { mode: "mock" | "s3-presigned" };
}

interface IngressGatewayConfig {
  mode: "mock" | "ms1";
  ms1BaseUrl: string;
}

function normalizeBaseUrl(input: string): string {
  return input.trim().replace(/\/+$/, "");
}

export function readIngressGatewayConfig(
  env: Record<string, string | undefined> = import.meta.env
): IngressGatewayConfig {
  const modeRaw = (env.VITE_INGRESS_GATEWAY_MODE ?? "mock").trim().toLowerCase();
  const mode = modeRaw === "ms1" ? "ms1" : "mock";
  const ms1BaseUrl = normalizeBaseUrl(env.VITE_MS1_API_BASE_URL ?? "");
  return { mode, ms1BaseUrl };
}

export function createAuthGateway(env: Record<string, string | undefined> = import.meta.env): AuthGateway {
  const config = readIngressGatewayConfig(env);
  if (config.mode === "ms1" && config.ms1BaseUrl.length > 0) {
    return new Ms1AuthGateway(config.ms1BaseUrl);
  }
  return new MockAuthGatewayAdapter(new MockAuthGateway());
}

export function createUploadGateway(env: Record<string, string | undefined> = import.meta.env): UploadGateway {
  const config = readIngressGatewayConfig(env);
  if (config.mode === "ms1" && config.ms1BaseUrl.length > 0) {
    return new PresignedUploadGateway();
  }
  return new MockUploadGatewayAdapter(new MockUploadGateway());
}

class Ms1AuthGateway implements AuthGateway {
  private readonly fetchImpl: typeof fetch;

  constructor(private readonly baseUrl: string) {
    this.fetchImpl = globalThis.fetch.bind(globalThis);
  }

  getDebugInfo(): { mode: "mock" | "ms1"; baseUrl?: string } {
    return { mode: "ms1", baseUrl: this.baseUrl };
  }

  async initUploadSession(input: UploadInitInput): Promise<InitUploadResult> {
    let response: Response;
    try {
      response = await this.fetchImpl(`${this.baseUrl}/v1/uploads/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          password: input.password,
          nickname: input.nickname,
          sessionId: input.sessionId,
          contentType: input.contentType,
          originalFilename: input.originalFilename,
          fileSizeBytes: input.fileSizeBytes,
        }),
      });
    } catch (error) {
      return {
        accepted: false,
        uploadTarget: "",
        jobId: "",
        message: `MS1 request failed (${formatError(error)}).`,
      };
    }

    const payload = await safeJson(response);
    if (!response.ok) {
      const message =
        typeof payload?.error?.message === "string" ? payload.error.message : "Upload init failed. Try again.";
      return {
        accepted: false,
        uploadTarget: "",
        jobId: "",
        message,
      };
    }

    const uploadUrl = payload?.uploadUrl;
    const uploadId = payload?.uploadId;
    if (typeof uploadUrl !== "string" || !uploadUrl || typeof uploadId !== "string" || !uploadId) {
      return {
        accepted: false,
        uploadTarget: "",
        jobId: "",
        message: "MS1 response is missing upload target details.",
      };
    }

    return {
      accepted: true,
      uploadTarget: uploadUrl,
      jobId: uploadId,
      classRunId: typeof payload?.classRunId === "string" ? payload.classRunId : undefined,
      uploadHeaders:
        payload?.uploadHeaders && typeof payload.uploadHeaders === "object"
          ? (payload.uploadHeaders as Record<string, string>)
          : undefined,
    };
  }
}

class PresignedUploadGateway implements UploadGateway {
  getDebugInfo(): { mode: "mock" | "s3-presigned" } {
    return { mode: "s3-presigned" };
  }

  uploadPhoto(
    uploadTarget: string,
    file: File,
    onProgress: (percentage: number) => void,
    uploadHeaders: Record<string, string> = {}
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("PUT", uploadTarget, true);
      for (const [key, value] of Object.entries(uploadHeaders)) {
        xhr.setRequestHeader(key, value);
      }
      if (!uploadHeaders["Content-Type"]) {
        xhr.setRequestHeader("Content-Type", file.type || "application/octet-stream");
      }

      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) {
          return;
        }
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          onProgress(100);
          resolve();
          return;
        }
        if (xhr.status === 0) {
          reject(new Error("Upload blocked before response (likely S3 CORS)."));
          return;
        }
        reject(new Error(`Upload failed with status ${xhr.status}.`));
      };

      xhr.onerror = () => {
        reject(new Error("Upload failed due to network/CORS error."));
      };

      xhr.send(file);
    });
  }
}

class MockAuthGatewayAdapter implements AuthGateway {
  constructor(private readonly gateway: MockAuthGateway) {}

  getDebugInfo(): { mode: "mock" } {
    return { mode: "mock" };
  }

  async initUploadSession(input: UploadInitInput): Promise<InitUploadResult> {
    return this.gateway.initUploadSession(input.password);
  }
}

class MockUploadGatewayAdapter implements UploadGateway {
  constructor(private readonly gateway: MockUploadGateway) {}

  getDebugInfo(): { mode: "mock" } {
    return { mode: "mock" };
  }

  uploadPhoto(
    uploadTarget: string,
    file: File,
    onProgress: (percentage: number) => void,
    _uploadHeaders?: Record<string, string>
  ): Promise<void> {
    return this.gateway.uploadPhoto(uploadTarget, file, onProgress);
  }
}

async function safeJson(response: Response): Promise<any> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function formatError(error: unknown): string {
  if (error instanceof Error) {
    return `${error.name}: ${error.message}`;
  }
  return String(error);
}
