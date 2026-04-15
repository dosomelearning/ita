import { describe, expect, it, vi } from "vitest";
import { Ms4StateGateway, createStateGateway, readGatewayConfig } from "./stateGateway";

function okResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function errorResponse(status: number, payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("readGatewayConfig", () => {
  it("defaults to mock mode", () => {
    const config = readGatewayConfig({});
    expect(config.mode).toBe("mock");
    expect(config.ms4BaseUrl).toBe("");
  });

  it("normalizes base URL and mode", () => {
    const config = readGatewayConfig({
      VITE_STATE_GATEWAY_MODE: "MS4",
      VITE_MS4_API_BASE_URL: "https://ita.dosomelearning.com///",
    });
    expect(config.mode).toBe("ms4");
    expect(config.ms4BaseUrl).toBe("https://ita.dosomelearning.com");
  });
});

describe("createStateGateway", () => {
  it("returns mock gateway unless ms4 mode and base url are provided", async () => {
    const gw1 = createStateGateway({});
    const gw2 = createStateGateway({ VITE_STATE_GATEWAY_MODE: "ms4" });
    expect("setFailNext" in gw1).toBe(true);
    expect("setFailNext" in gw2).toBe(true);
  });

  it("returns ms4 gateway when configured", () => {
    const gw = createStateGateway({
      VITE_STATE_GATEWAY_MODE: "ms4",
      VITE_MS4_API_BASE_URL: "https://ita.dosomelearning.com",
    });
    expect(gw).toBeInstanceOf(Ms4StateGateway);
  });
});

describe("Ms4StateGateway", () => {
  it("polls until completed and emits phase transitions", async () => {
    const phases: string[] = [];
    const fetchImpl = vi
      .fn<(...args: [RequestInfo | URL, RequestInit | undefined]) => Promise<Response>>()
      .mockResolvedValueOnce(okResponse({ uploadId: "u1", status: "queued" }))
      .mockResolvedValueOnce(okResponse({ uploadId: "u1", status: "processing" }))
      .mockResolvedValueOnce(okResponse({ uploadId: "u1", status: "completed" }));
    const gateway = new Ms4StateGateway("https://ita.dosomelearning.com", {
      fetchImpl,
      waitImpl: async () => undefined,
      pollIntervalMs: 1,
      maxWaitMs: 1000,
    });

    const result = await gateway.awaitJobCompletion("u1", (phase) => {
      phases.push(phase);
    });

    expect(result.status).toBe("completed");
    expect(phases).toEqual(["queued", "processing", "completed"]);
    expect(fetchImpl).toHaveBeenCalledTimes(3);
  });

  it("fails after repeated not found responses", async () => {
    const fetchImpl = vi
      .fn<(...args: [RequestInfo | URL, RequestInit | undefined]) => Promise<Response>>()
      .mockResolvedValue(errorResponse(404, { error: { code: "UPLOAD_NOT_FOUND" } }));
    const gateway = new Ms4StateGateway("https://ita.dosomelearning.com", {
      fetchImpl,
      waitImpl: async () => undefined,
      pollIntervalMs: 1,
      maxWaitMs: 1000,
      maxNotFoundResponses: 2,
    });

    const result = await gateway.awaitJobCompletion("missing", () => undefined);

    expect(result.status).toBe("failed");
    expect(result.message?.toLowerCase()).toContain("not found");
    expect(fetchImpl).toHaveBeenCalledTimes(3);
  });

  it("maps failed status with server message", async () => {
    const fetchImpl = vi
      .fn<(...args: [RequestInfo | URL, RequestInit | undefined]) => Promise<Response>>()
      .mockResolvedValue(
        okResponse({
          uploadId: "u1",
          status: "failed",
          error: { message: "Processing pipeline failed in ms3." },
        })
      );
    const gateway = new Ms4StateGateway("https://ita.dosomelearning.com", {
      fetchImpl,
      waitImpl: async () => undefined,
      pollIntervalMs: 1,
      maxWaitMs: 1000,
    });

    const result = await gateway.awaitJobCompletion("u1", () => undefined);

    expect(result.status).toBe("failed");
    expect(result.message).toContain("ms3");
  });

  it("loads activity feed items from ms4", async () => {
    const fetchImpl = vi
      .fn<(...args: [RequestInfo | URL, RequestInit | undefined]) => Promise<Response>>()
      .mockResolvedValue(
        okResponse({
          sessionId: "cr-a1",
          items: [
            {
              uploadId: "upl-1",
              nickname: "ava",
              eventType: "detection_completed",
              statusAfter: "processing",
              eventTime: "2026-04-15T18:00:00.123Z",
              producer: "ms2",
              outcome: "in_progress",
            },
          ],
        })
      );
    const gateway = new Ms4StateGateway("https://ita.dosomelearning.com", { fetchImpl });

    const items = await gateway.getActivities("cr-a1", 20);

    expect(items).toHaveLength(1);
    expect(items[0].uploadId).toBe("upl-1");
    expect(items[0].outcome).toBe("in_progress");
  });
});
