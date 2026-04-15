import { describe, expect, it, vi } from "vitest";
import { createAuthGateway, createUploadGateway, readIngressGatewayConfig } from "./ingressGateway";

function responseOk(payload: unknown): Response {
  return new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } });
}

function responseError(status: number, payload: unknown): Response {
  return new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json" } });
}

describe("readIngressGatewayConfig", () => {
  it("defaults to mock mode", () => {
    const config = readIngressGatewayConfig({});
    expect(config.mode).toBe("mock");
    expect(config.ms1BaseUrl).toBe("");
  });

  it("normalizes ms1 mode values", () => {
    const config = readIngressGatewayConfig({
      VITE_INGRESS_GATEWAY_MODE: "MS1",
      VITE_MS1_API_BASE_URL: "https://si01n8xiyc.execute-api.eu-central-1.amazonaws.com///",
    });
    expect(config.mode).toBe("ms1");
    expect(config.ms1BaseUrl).toBe("https://si01n8xiyc.execute-api.eu-central-1.amazonaws.com");
  });
});

describe("create gateways", () => {
  it("returns mock adapters by default", () => {
    const authGateway = createAuthGateway({});
    const uploadGateway = createUploadGateway({});
    expect(authGateway.getDebugInfo?.().mode).toBe("mock");
    expect(uploadGateway.getDebugInfo?.().mode).toBe("mock");
  });

  it("returns ms1 auth + presigned upload gateways in ms1 mode", () => {
    const env = {
      VITE_INGRESS_GATEWAY_MODE: "ms1",
      VITE_MS1_API_BASE_URL: "https://si01n8xiyc.execute-api.eu-central-1.amazonaws.com",
    };
    const authGateway = createAuthGateway(env);
    const uploadGateway = createUploadGateway(env);
    expect(authGateway.getDebugInfo?.().mode).toBe("ms1");
    expect(uploadGateway.getDebugInfo?.().mode).toBe("s3-presigned");
  });
});

describe("ms1 auth gateway behavior", () => {
  it("maps successful ms1 init response", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        responseOk({
          accepted: true,
          uploadId: "upl-1",
          classRunId: "cr-aaaa1111",
          uploadUrl: "https://example-presigned",
          uploadHeaders: { "Content-Type": "image/jpeg" },
        })
      );
    const gateway = createAuthGateway({
      VITE_INGRESS_GATEWAY_MODE: "ms1",
      VITE_MS1_API_BASE_URL: "https://ms1.example",
    });
    const result = await gateway.initUploadSession({
      password: "class2026",
      nickname: "ava",
      sessionId: "s-1",
      contentType: "image/jpeg",
      originalFilename: "x.jpg",
      fileSizeBytes: 123,
    });
    expect(result.accepted).toBe(true);
    expect(result.jobId).toBe("upl-1");
    expect(result.classRunId).toBe("cr-aaaa1111");
    expect(result.uploadTarget).toBe("https://example-presigned");
    fetchSpy.mockRestore();
  });

  it("maps ms1 validation error to rejected result", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(responseError(401, { error: { message: "Invalid class code." } }));
    const gateway = createAuthGateway({
      VITE_INGRESS_GATEWAY_MODE: "ms1",
      VITE_MS1_API_BASE_URL: "https://ms1.example",
    });
    const result = await gateway.initUploadSession({
      password: "wrong",
      nickname: "ava",
      sessionId: "s-1",
      contentType: "image/jpeg",
    });
    expect(result.accepted).toBe(false);
    expect(result.message).toContain("Invalid class code");
    fetchSpy.mockRestore();
  });
});
