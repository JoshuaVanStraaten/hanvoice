/** Decides when a recording should stop itself.
 *
 * Fed one (level, timestamp) sample per animation frame by useRecorder:
 * once speech is heard (level ≥ ONSET_LEVEL), a sustained drop below
 * SILENCE_LEVEL for SILENCE_WINDOW_MS fires the gate. The two thresholds are
 * deliberately apart (hysteresis) so breath noise between them neither
 * triggers speech nor resets the silence clock. At maxDurationMs the gate
 * fires regardless — or discards if nothing was ever said, so a silent take
 * never wastes a scored attempt.
 *
 * Thresholds are on useRecorder's 0–1 RMS scale (speech peaks ≈ 1). Tuned
 * against a live mic on 2026-07-05; founder delegated exact values. */

export const ONSET_LEVEL = 0.15;
export const SILENCE_LEVEL = 0.08;
export const SILENCE_WINDOW_MS = 2500;

export type GatePhase = "armed" | "hearing" | "finishing";
export type GateEvent = "fire" | "capFire" | "capDiscard";

export interface SilenceGate {
  /** Feed one meter sample; returns an event at most once, then goes inert. */
  sample(level: number, nowMs: number): GateEvent | null;
  readonly phase: GatePhase;
  /** 0–1 through the silence window while finishing (drives the countdown arc). */
  readonly silenceProgress: number;
}

export function createSilenceGate({ maxDurationMs }: { maxDurationMs: number }): SilenceGate {
  let startedAt: number | null = null;
  let heardSpeech = false;
  let silenceSince: number | null = null;
  let done = false;
  let phase: GatePhase = "armed";
  let silenceProgress = 0;

  return {
    get phase() {
      return phase;
    },
    get silenceProgress() {
      return silenceProgress;
    },
    sample(level: number, nowMs: number): GateEvent | null {
      if (done) return null;
      startedAt ??= nowMs;

      if (level >= ONSET_LEVEL) {
        heardSpeech = true;
        silenceSince = null;
      } else if (heardSpeech && level < SILENCE_LEVEL && silenceSince === null) {
        silenceSince = nowMs;
      }

      if (nowMs - startedAt >= maxDurationMs) {
        done = true;
        return heardSpeech ? "capFire" : "capDiscard";
      }

      if (silenceSince !== null) {
        phase = "finishing";
        silenceProgress = Math.min(1, (nowMs - silenceSince) / SILENCE_WINDOW_MS);
        if (nowMs - silenceSince >= SILENCE_WINDOW_MS) {
          done = true;
          return "fire";
        }
      } else {
        phase = heardSpeech ? "hearing" : "armed";
        silenceProgress = 0;
      }
      return null;
    },
  };
}
