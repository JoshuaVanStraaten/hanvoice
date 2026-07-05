/** MediaRecorder wrapper: one active recording at a time. Recordings are
 * normalized to 16 kHz mono WAV before they're handed back — Azure's REST
 * API can't decode webm/mp4 containers. While recording, `level` reports live
 * mic loudness (0–1) and a silence gate watches it: after ~2.5 s of quiet
 * following speech the recording stops itself and is delivered via
 * `onAutoStop`. A hard cap (caller-scaled, ≤ 30 s to match the backend size
 * ceiling) always applies; a take with no speech at all is discarded via
 * `onSilentDiscard` instead of wasting a scored attempt. */

import { useCallback, useEffect, useRef, useState } from "react";

import { toWav16kMono } from "../lib/audio";
import { createSilenceGate, type SilenceGate } from "../lib/silenceGate";

const ABSOLUTE_MAX_MS = 30_000;

function pickMimeType(): string | undefined {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return candidates.find((type) => MediaRecorder.isTypeSupported(type));
}

export type RecorderPhase = "idle" | "armed" | "hearing" | "finishing";

export interface StartOptions {
  /** Hard cap for this take (clamped to 30 s). Default 30 s. */
  maxDurationMs?: number;
  /** Recording stopped itself (silence or cap) — submit this. */
  onAutoStop?: (audio: Blob) => void;
  /** Cap hit without any speech — nothing worth submitting. */
  onSilentDiscard?: () => void;
}

export interface Recorder {
  isRecording: boolean;
  /** Live input loudness while recording, 0–1. */
  level: number;
  /** What the silence gate is doing (drives the caption + countdown arc). */
  phase: RecorderPhase;
  /** 0–1 through the silence window while `phase === "finishing"`. */
  silenceProgress: number;
  /** Human-readable mic failure (permission denied, no device). */
  error: string | null;
  start(options?: StartOptions): Promise<void>;
  /** Stops and resolves with the recording; null if nothing was captured. */
  stop(): Promise<Blob | null>;
}

export function useRecorder(): Recorder {
  const [isRecording, setIsRecording] = useState(false);
  const [level, setLevel] = useState(0);
  const [phase, setPhase] = useState<RecorderPhase>("idle");
  const [silenceProgress, setSilenceProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const meterCtxRef = useRef<AudioContext | null>(null);
  const meterFrameRef = useRef<number | null>(null);
  const gateRef = useRef<SilenceGate | null>(null);
  const optionsRef = useRef<StartOptions>({});

  const stopMeter = useCallback(() => {
    if (meterFrameRef.current !== null) cancelAnimationFrame(meterFrameRef.current);
    meterFrameRef.current = null;
    void meterCtxRef.current?.close().catch(() => undefined);
    meterCtxRef.current = null;
    gateRef.current = null;
    setLevel(0);
    setPhase("idle");
    setSilenceProgress(0);
  }, []);

  const stop = useCallback(async (): Promise<Blob | null> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") return null;
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    stopMeter();
    const raw = await new Promise<Blob | null>((resolve) => {
      const chunks: BlobPart[] = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.push(event.data);
      };
      recorder.onstop = () => {
        recorder.stream.getTracks().forEach((track) => track.stop());
        recorderRef.current = null;
        setIsRecording(false);
        resolve(chunks.length ? new Blob(chunks, { type: recorder.mimeType }) : null);
      };
      recorder.stop();
    });
    if (!raw) return null;
    try {
      return await toWav16kMono(raw);
    } catch {
      // Decoding failed (rare codec edge case) — send the original and let
      // the backend report whatever the provider says.
      return raw;
    }
  }, [stopMeter]);

  /** The gate decided: end the take and route the blob (or lack of one). */
  const autoStop = useCallback(
    (discard: boolean) => {
      void stop().then((audio) => {
        if (discard) optionsRef.current.onSilentDiscard?.();
        else if (audio) optionsRef.current.onAutoStop?.(audio);
      });
    },
    [stop],
  );

  const startMeter = useCallback(
    (stream: MediaStream) => {
      try {
        const ctx = new AudioContext();
        meterCtxRef.current = ctx;
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        ctx.createMediaStreamSource(stream).connect(analyser);
        const samples = new Uint8Array(analyser.fftSize);
        const tick = () => {
          analyser.getByteTimeDomainData(samples);
          let sumOfSquares = 0;
          for (let i = 0; i < samples.length; i++) {
            const deviation = (samples[i] ?? 128) - 128;
            sumOfSquares += deviation * deviation;
          }
          // RMS of speech peaks around ~40 on this 0-128 scale.
          const loudness = Math.min(1, Math.sqrt(sumOfSquares / samples.length) / 40);
          setLevel(loudness);
          const gate = gateRef.current;
          if (gate) {
            const event = gate.sample(loudness, performance.now());
            setPhase(gate.phase);
            setSilenceProgress(gate.silenceProgress);
            if (event) {
              autoStop(event === "capDiscard");
              return; // stop() tears the meter down — no next frame
            }
          }
          meterFrameRef.current = requestAnimationFrame(tick);
        };
        tick();
      } catch {
        // Metering is cosmetic and the gate depends on it — recording
        // continues; the fallback timeout below still caps the take.
      }
    },
    [autoStop],
  );

  const start = useCallback(
    async (options: StartOptions = {}) => {
      setError(null);
      if (recorderRef.current) return; // already recording
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
        setError("This browser can't record audio — try Chrome, Edge, or Safari.");
        return;
      }
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch {
        setError("Microphone access is blocked. Allow it in your browser settings.");
        return;
      }
      optionsRef.current = options;
      const maxDurationMs = Math.min(options.maxDurationMs ?? ABSOLUTE_MAX_MS, ABSOLUTE_MAX_MS);
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      setPhase("armed");
      gateRef.current = createSilenceGate({ maxDurationMs });
      startMeter(stream);
      // Fallback for when the meter (and so the gate) couldn't start: assume
      // the learner spoke and submit whatever was captured at the cap.
      timeoutRef.current = setTimeout(() => autoStop(false), maxDurationMs + 500);
    },
    [autoStop, startMeter],
  );

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (meterFrameRef.current !== null) cancelAnimationFrame(meterFrameRef.current);
      void meterCtxRef.current?.close().catch(() => undefined);
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.stream.getTracks().forEach((track) => track.stop());
        recorder.stop();
      }
    };
  }, []);

  return { isRecording, level, phase, silenceProgress, error, start, stop };
}
