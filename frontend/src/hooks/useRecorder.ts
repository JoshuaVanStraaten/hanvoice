/** MediaRecorder wrapper: one active recording at a time. Recordings are
 * normalized to 16 kHz mono WAV before they're handed back — Azure's REST
 * API can't decode webm/mp4 containers. Auto-stops at 30 seconds, matching
 * the backend's size ceiling. While recording, `level` reports live mic
 * loudness (0–1) so the UI can show the voice actually coming through. */

import { useCallback, useEffect, useRef, useState } from "react";

import { toWav16kMono } from "../lib/audio";

const MAX_RECORDING_MS = 30_000;

function pickMimeType(): string | undefined {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return candidates.find((type) => MediaRecorder.isTypeSupported(type));
}

export interface Recorder {
  isRecording: boolean;
  /** Live input loudness while recording, 0–1. */
  level: number;
  /** Human-readable mic failure (permission denied, no device). */
  error: string | null;
  start(): Promise<void>;
  /** Stops and resolves with the recording; null if nothing was captured. */
  stop(): Promise<Blob | null>;
}

export function useRecorder(): Recorder {
  const [isRecording, setIsRecording] = useState(false);
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const meterCtxRef = useRef<AudioContext | null>(null);
  const meterFrameRef = useRef<number | null>(null);

  const startMeter = useCallback((stream: MediaStream) => {
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
        setLevel(Math.min(1, Math.sqrt(sumOfSquares / samples.length) / 40));
        meterFrameRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch {
      // Metering is cosmetic — recording continues without it.
    }
  }, []);

  const stopMeter = useCallback(() => {
    if (meterFrameRef.current !== null) cancelAnimationFrame(meterFrameRef.current);
    meterFrameRef.current = null;
    void meterCtxRef.current?.close().catch(() => undefined);
    meterCtxRef.current = null;
    setLevel(0);
  }, []);

  const stop = useCallback(async (): Promise<Blob | null> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") return null;
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

  const start = useCallback(async () => {
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
    const mimeType = pickMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    recorderRef.current = recorder;
    recorder.start();
    setIsRecording(true);
    startMeter(stream);
    timeoutRef.current = setTimeout(() => void stop(), MAX_RECORDING_MS);
  }, [startMeter, stop]);

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

  return { isRecording, level, error, start, stop };
}
