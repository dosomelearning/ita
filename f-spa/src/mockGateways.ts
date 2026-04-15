export type JobPhase = "queued" | "processing" | "completed" | "failed";

export interface InitUploadResult {
  accepted: boolean;
  uploadTarget: string;
  jobId: string;
  classRunId?: string;
  message?: string;
}

export interface JobCompletionResult {
  status: "completed" | "failed";
  message?: string;
}

export interface RankingEntry {
  id: string;
  name: string;
  score: number;
  lastUpdateLabel: string;
}

export interface ActivityEntry {
  uploadId: string;
  nickname: string;
  eventType: string;
  statusAfter: JobPhase;
  eventTime: string;
  producer: "ms2" | "ms3";
  outcome: "queued" | "in_progress" | "success" | "failure";
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}

export class MockAuthGateway {
  async initUploadSession(password: string): Promise<InitUploadResult> {
    await wait(250);

    const normalized = password.trim().toLowerCase();
    if (normalized.length < 4 || normalized === "wrong") {
      return {
        accepted: false,
        uploadTarget: "",
        jobId: "",
        message: "Invalid class code. Ask instructor for current code.",
      };
    }

    const suffix = Math.random().toString(36).slice(2, 8);
    return {
      accepted: true,
      uploadTarget: "mock://s3/presigned-url",
      jobId: `job-${suffix}`,
      classRunId: `cr-mock-${normalized}`,
    };
  }
}

export class MockUploadGateway {
  async uploadPhoto(
    _uploadTarget: string,
    _file: File,
    onProgress: (percentage: number) => void
  ): Promise<void> {
    const checkpoints = [10, 25, 40, 60, 80, 100];
    for (const checkpoint of checkpoints) {
      await wait(140);
      onProgress(checkpoint);
    }
  }
}

export class MockStateGateway {
  private failNext = false;

  setFailNext(shouldFail: boolean): void {
    this.failNext = shouldFail;
  }

  async awaitJobCompletion(
    _jobId: string,
    onPhase: (phase: JobPhase) => void
  ): Promise<JobCompletionResult> {
    await wait(280);
    onPhase("queued");
    await wait(500);
    onPhase("processing");
    await wait(600);

    if (this.failNext) {
      this.failNext = false;
      onPhase("failed");
      return {
        status: "failed",
        message: "Mock processing failed. You can retry now.",
      };
    }

    onPhase("completed");
    return { status: "completed" };
  }

  async getRanking(): Promise<RankingEntry[]> {
    await wait(300);
    const baseline: Array<Pick<RankingEntry, "id" | "name">> = [
      { id: "p1", name: "Ava Novak" },
      { id: "p2", name: "Liam Bauer" },
      { id: "p3", name: "Mia Horvat" },
      { id: "p4", name: "Noah Zoric" },
      { id: "p5", name: "Ema Kralj" },
      { id: "p6", name: "Luka Varga" },
      { id: "p7", name: "Nika Sever" },
      { id: "p8", name: "Jan Oblak" },
    ];

    const now = new Date();
    return baseline
      .map((entry, index) => ({
        ...entry,
        score: 30 - index * 2 + Math.floor(Math.random() * 5),
        lastUpdateLabel: now.toLocaleTimeString(),
      }))
      .sort((a, b) => b.score - a.score);
  }

  async getActivities(_classRunId: string, limit = 20): Promise<ActivityEntry[]> {
    await wait(220);
    const users = ["Ava Novak", "Liam Bauer", "Mia Horvat", "Noah Zoric", "Ema Kralj"];
    const now = Date.now();
    const items: ActivityEntry[] = Array.from({ length: Math.min(Math.max(limit, 1), 20) }).map((_, idx) => {
      const phaseIndex = idx % 3;
      const statusAfter: JobPhase = phaseIndex === 0 ? "failed" : phaseIndex === 1 ? "processing" : "completed";
      return {
        uploadId: `upl-mock-${1000 + idx}`,
        nickname: users[idx % users.length],
        eventType:
          statusAfter === "failed"
            ? "detection_failed"
            : statusAfter === "processing"
            ? "detection_completed"
            : "extraction_completed",
        statusAfter,
        eventTime: new Date(now - idx * 17_000).toISOString(),
        producer: statusAfter === "completed" ? "ms3" : "ms2",
        outcome:
          statusAfter === "failed" ? "failure" : statusAfter === "completed" ? "success" : "in_progress",
      };
    });
    return items;
  }
}
