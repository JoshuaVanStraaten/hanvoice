/** Explanation step: structured segments (text / chars / example / tip).
 * Every taught glyph is audible — bare jamo play their carrier syllable
 * (ㄱ → 가), shown as "in 가" under the card. Reading is self-attested —
 * Continue marks the block passed. */

import type { ReactNode } from "react";

import { AudioButton, blockAudioProps } from "../AudioButton";
import { Button } from "../ui";
import { audioTextFor, isCarrier } from "../../lib/hangulAudio";
import type { ExplainPayload, ExplainSegment } from "../../lib/types";

/** The only inline formatting explain text supports: **bold**. */
export function renderBold(body: string): ReactNode[] {
  return body
    .split(/\*\*(.+?)\*\*/g)
    .map((part, index) =>
      index % 2 === 1 ? <strong key={index}>{part}</strong> : part,
    );
}

function Segment({ blockId, segment }: { blockId: number; segment: ExplainSegment }) {
  switch (segment.type) {
    case "text":
      return <p className="text-sm leading-relaxed text-ink">{renderBold(segment.body)}</p>;
    case "tip":
      return (
        <p className="rounded-lg border border-taegeuk-blue/20 bg-taegeuk-blue/5 p-3 text-sm text-ink">
          <span aria-hidden>💡 </span>
          {renderBold(segment.body)}
        </p>
      );
    case "chars":
      return (
        <ul className="flex flex-wrap justify-center gap-2">
          {segment.items.map((item) => {
            const played = audioTextFor(item.ko, item.audio);
            return (
              <li
                key={item.ko}
                className="flex w-24 flex-col items-center gap-1 rounded-lg border border-line bg-paper-raised p-3 text-center"
              >
                <span lang="ko" className="hangul-display text-4xl text-ink">
                  {item.ko}
                </span>
                {item.label && (
                  <span className="text-sm font-semibold text-taegeuk-blue">{item.label}</span>
                )}
                {item.note && <span className="text-xs text-ink-soft">{item.note}</span>}
                <span className="mt-1 flex items-center gap-1.5">
                  <AudioButton size="sm" {...blockAudioProps(blockId, item.ko, played)} />
                  {isCarrier(item.ko, item.audio) && (
                    <span lang="ko" className="text-xs text-ink-soft">
                      in {played}
                    </span>
                  )}
                </span>
              </li>
            );
          })}
        </ul>
      );
    case "example":
      return (
        <ul className="space-y-2">
          {segment.items.map((item) => (
            <li
              key={item.ko}
              className="flex items-center gap-3 rounded-lg border border-line bg-paper-raised px-3 py-2"
            >
              <AudioButton
                size="sm"
                {...blockAudioProps(blockId, item.ko, audioTextFor(item.ko, item.audio))}
              />
              <span lang="ko" className="hangul-display text-xl text-ink">
                {item.ko}
              </span>
              <span className="text-sm text-ink-soft">
                {[item.roman, item.en].filter(Boolean).join(" · ")}
              </span>
            </li>
          ))}
        </ul>
      );
  }
}

export function ExplainBlock({
  blockId,
  payload,
  completing,
  onContinue,
}: {
  blockId: number;
  payload: ExplainPayload;
  completing: boolean;
  onContinue: () => void;
}) {
  return (
    <div className="space-y-4">
      {(payload.segments ?? []).map((segment, index) => (
        <Segment key={index} blockId={blockId} segment={segment} />
      ))}
      <div className="text-center">
        <Button onClick={onContinue} disabled={completing}>
          {completing ? "Saving…" : "Continue"}
        </Button>
      </div>
    </div>
  );
}
