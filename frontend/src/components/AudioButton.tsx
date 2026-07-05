/** A small round play button: fetches base64 audio once, replays from memory.
 * Teaching audio is enrichment — failures stay quiet, the text remains. */

import { useRef, useState } from "react";

import { apiGet } from "../lib/api";

export function AudioButton({
  path,
  label,
  size = "md",
}: {
  /** API path returning `{ audio_base64 }` (mp3). */
  path: string;
  /** Accessible name, e.g. "Hear ㄱ (sounds like 가)". */
  label: string;
  size?: "sm" | "md";
}) {
  const cached = useRef<string | null>(null);
  const [pending, setPending] = useState(false);

  async function play() {
    if (pending) return;
    if (!cached.current) {
      setPending(true);
      try {
        const response = await apiGet<{ audio_base64: string }>(path);
        cached.current = response.audio_base64;
      } catch {
        return;
      } finally {
        setPending(false);
      }
    }
    void new Audio(`data:audio/mpeg;base64,${cached.current}`).play().catch(() => undefined);
  }

  return (
    <button
      type="button"
      onClick={() => void play()}
      disabled={pending}
      aria-label={label}
      className={`flex items-center justify-center rounded-full bg-taegeuk-blue/10 text-taegeuk-blue transition-colors hover:bg-taegeuk-blue/20 disabled:opacity-50 ${
        size === "sm" ? "size-7" : "size-9"
      }`}
    >
      {pending ? (
        <span className="size-2 animate-pulse rounded-full bg-taegeuk-blue" aria-hidden />
      ) : (
        <svg
          width={size === "sm" ? 12 : 16}
          height={size === "sm" ? 12 : 16}
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden
        >
          <path d="M8 5.5v13l11-6.5z" />
        </svg>
      )}
    </button>
  );
}

/** Path + label for a taught glyph's audio on a block (carrier-aware). */
export function blockAudioProps(
  blockId: number,
  glyph: string,
  playedText: string,
): { path: string; label: string } {
  return {
    path: `/lessons/blocks/${blockId}/audio?text=${encodeURIComponent(playedText)}`,
    label: playedText === glyph ? `Hear ${glyph}` : `Hear ${glyph} (sounds like ${playedText})`,
  };
}
