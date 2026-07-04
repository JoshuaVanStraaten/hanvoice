/** MediaRecorder wrapper: one active recording at a time. Recordings are
 * normalized to 16 kHz mono WAV before they're handed back — Azure's REST
 * API can't decode webm/mp4 containers. Auto-stops at 30 seconds, matching
 * the backend's size ceiling. */

import { useCallback, useEffect, useRef, useState } from "react";

import { toWav16kMono } from "../lib/audio";

const MAX_RECORDING_MS = 30_000;

function pickMimeType(): string | undefined {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return candidates.find((type) => MediaRecorder.isTypeSupported(type));
}

export interface Recorder {
  isRecording: boolean;
  /** Human-readable mic failure (permission denied, no device). */
  error: string | null;
  start(): Promise<void>;
  /** Stops and resolves with the recording; null if nothing was captured. */
  stop(): Promise<Blob | null>;
}

export function useRecorder(): Recorder {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stop = useCallback(async (): Promise<Blob | null> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") return null;
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
  }, []);

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
    timeoutRef.current = setTimeout(() => void stop(), MAX_RECORDING_MS);
  }, [stop]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.stream.getTracks().forEach((track) => track.stop());
        recorder.stop();
      }
    };
  }, []);

  return { isRecording, error, start, stop };
}
