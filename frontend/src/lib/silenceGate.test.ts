import { describe, expect, it } from "vitest";

import {
  ONSET_LEVEL,
  SILENCE_LEVEL,
  SILENCE_WINDOW_MS,
  createSilenceGate,
} from "./silenceGate";

const QUIET = SILENCE_LEVEL / 2;
const LOUD = ONSET_LEVEL + 0.1;

describe("createSilenceGate", () => {
  it("stays armed while nothing loud is heard", () => {
    const gate = createSilenceGate({ maxDurationMs: 10_000 });
    expect(gate.sample(QUIET, 0)).toBeNull();
    expect(gate.sample(QUIET, 1000)).toBeNull();
    expect(gate.phase).toBe("armed");
  });

  it("moves to hearing on speech onset", () => {
    const gate = createSilenceGate({ maxDurationMs: 10_000 });
    gate.sample(QUIET, 0);
    expect(gate.sample(LOUD, 100)).toBeNull();
    expect(gate.phase).toBe("hearing");
  });

  it("counts silence after speech and fires at the window", () => {
    const gate = createSilenceGate({ maxDurationMs: 30_000 });
    gate.sample(LOUD, 0);
    expect(gate.sample(QUIET, 1000)).toBeNull();
    expect(gate.phase).toBe("finishing");
    expect(gate.sample(QUIET, 2000)).toBeNull();
    expect(gate.silenceProgress).toBeGreaterThan(0);
    expect(gate.silenceProgress).toBeLessThan(1);
    expect(gate.sample(QUIET, 1000 + SILENCE_WINDOW_MS - 1)).toBeNull();
    expect(gate.sample(QUIET, 1000 + SILENCE_WINDOW_MS)).toBe("fire");
  });

  it("resets the silence clock when speech resumes", () => {
    const gate = createSilenceGate({ maxDurationMs: 30_000 });
    gate.sample(LOUD, 0);
    gate.sample(QUIET, 1000);
    gate.sample(LOUD, 2000); // spoke again
    expect(gate.phase).toBe("hearing");
    expect(gate.sample(QUIET, 3000)).toBeNull(); // silence restarts here
    expect(gate.sample(QUIET, 3000 + SILENCE_WINDOW_MS - 1)).toBeNull();
    expect(gate.sample(QUIET, 3000 + SILENCE_WINDOW_MS)).toBe("fire");
  });

  it("mid levels (between silence and onset) do not reset the clock", () => {
    const gate = createSilenceGate({ maxDurationMs: 30_000 });
    gate.sample(LOUD, 0);
    gate.sample(QUIET, 1000);
    gate.sample((SILENCE_LEVEL + ONSET_LEVEL) / 2, 2000); // breath noise
    expect(gate.sample(QUIET, 1000 + SILENCE_WINDOW_MS)).toBe("fire");
  });

  it("discards at the cap when speech was never detected", () => {
    const gate = createSilenceGate({ maxDurationMs: 4000 });
    gate.sample(QUIET, 0);
    expect(gate.sample(QUIET, 3999)).toBeNull();
    expect(gate.sample(QUIET, 4000)).toBe("capDiscard");
  });

  it("submits at the cap when speech was detected", () => {
    const gate = createSilenceGate({ maxDurationMs: 4000 });
    gate.sample(LOUD, 0);
    gate.sample(LOUD, 3000);
    expect(gate.sample(LOUD, 4000)).toBe("capFire");
  });

  it("emits an event only once", () => {
    const gate = createSilenceGate({ maxDurationMs: 30_000 });
    gate.sample(LOUD, 0);
    gate.sample(QUIET, 1000);
    expect(gate.sample(QUIET, 1000 + SILENCE_WINDOW_MS)).toBe("fire");
    expect(gate.sample(QUIET, 2000 + SILENCE_WINDOW_MS)).toBeNull();
  });
});
