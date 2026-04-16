import { describe, expect, it } from "vitest";
import { MockAuthGateway, MockStateGateway } from "./mockGateways";

describe("MockAuthGateway", () => {
  it("rejects short or invalid code", async () => {
    const gateway = new MockAuthGateway();
    const result = await gateway.initUploadSession("bad code");
    expect(result.accepted).toBe(false);
  });

  it("accepts valid class code", async () => {
    const gateway = new MockAuthGateway();
    const result = await gateway.initUploadSession("class2026!@");
    expect(result.accepted).toBe(true);
    expect(result.jobId.startsWith("job-")).toBe(true);
  });
});

describe("MockStateGateway", () => {
  it("can simulate a failed job", async () => {
    const phases: string[] = [];
    const gateway = new MockStateGateway();
    gateway.setFailNext(true);

    const result = await gateway.awaitJobCompletion("job-test", (phase) => {
      phases.push(phase);
    });

    expect(result.status).toBe("failed");
    expect(phases).toContain("queued");
    expect(phases).toContain("processing");
    expect(phases).toContain("failed");
  });

  it("returns faceCount on successful completion", async () => {
    const gateway = new MockStateGateway();
    const result = await gateway.awaitJobCompletion("job-test", () => undefined);
    expect(result.status).toBe("completed");
    expect(typeof result.faceCount).toBe("number");
    expect((result.faceCount ?? 0) > 0).toBe(true);
  });
});
