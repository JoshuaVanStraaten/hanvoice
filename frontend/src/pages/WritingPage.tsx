/** Hangul handwriting practice. The canvas is transparent with a faint
 * tracing guide *behind* it — export composites strokes onto clean white so
 * the vision model never sees the guide. Targets spell out the phrases the
 * learner already says: 안녕하세요, 감사합니다. */

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Button, Card, ErrorNote, ScoreRing, Spinner } from "../components/ui";
import { useActivityInvalidation } from "../hooks/queries";
import { apiPost } from "../lib/api";
import type { HandwritingAttempt } from "../lib/types";

const TARGETS = ["안", "녕", "하", "세", "요", "감", "사", "합", "니", "다"];
const CANVAS_SIZE = 320; // CSS px; internal resolution scales with DPR

type Stroke = Array<{ x: number; y: number }>;

function drawStrokes(canvas: HTMLCanvasElement, strokes: Stroke[]): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const scale = canvas.width / CANVAS_SIZE;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // Thick strokes on purpose: the vision model downscales the image and
  // stops perceiving thin lines — 12px reads like a marker, not a wisp.
  ctx.lineWidth = 12 * scale;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.strokeStyle = "#23262c"; // ink
  for (const stroke of strokes) {
    if (stroke.length < 2) continue;
    ctx.beginPath();
    const first = stroke[0];
    if (!first) continue;
    ctx.moveTo(first.x * scale, first.y * scale);
    for (const point of stroke.slice(1)) ctx.lineTo(point.x * scale, point.y * scale);
    ctx.stroke();
  }
}

/** Strokes composited onto white, as base64 PNG without the data: prefix. */
function exportPng(canvas: HTMLCanvasElement): string {
  const offscreen = document.createElement("canvas");
  offscreen.width = canvas.width;
  offscreen.height = canvas.height;
  const ctx = offscreen.getContext("2d");
  if (!ctx) throw new Error("Canvas export failed");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, offscreen.width, offscreen.height);
  ctx.drawImage(canvas, 0, 0);
  return offscreen.toDataURL("image/png").split(",")[1] ?? "";
}

export function WritingPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const currentStroke = useRef<Stroke>([]);
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [targetIndex, setTargetIndex] = useState(0);
  const [showGuide, setShowGuide] = useState(true);
  const invalidateActivity = useActivityInvalidation();

  const target = TARGETS[targetIndex] ?? TARGETS[0] ?? "안";

  const submit = useMutation({
    mutationFn: (imageBase64: string) =>
      apiPost<HandwritingAttempt>("/handwriting/attempts", {
        target_text: target,
        image_base64: imageBase64,
      }),
    onSuccess: () => invalidateActivity(),
  });

  function localPoint(event: React.PointerEvent<HTMLCanvasElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * CANVAS_SIZE,
      y: ((event.clientY - rect.top) / rect.height) * CANVAS_SIZE,
    };
  }

  function handlePointerDown(event: React.PointerEvent<HTMLCanvasElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    currentStroke.current = [localPoint(event)];
  }

  function handlePointerMove(event: React.PointerEvent<HTMLCanvasElement>) {
    if (currentStroke.current.length === 0) return;
    currentStroke.current.push(localPoint(event));
    const canvas = canvasRef.current;
    if (canvas) drawStrokes(canvas, [...strokes, currentStroke.current]);
  }

  function handlePointerUp() {
    // Capture before clearing the ref: the state updater runs *after* this
    // handler returns, and must not read the already-emptied ref.
    const stroke = currentStroke.current;
    if (stroke.length === 0) return;
    currentStroke.current = [];
    setStrokes((existing) => [...existing, stroke]);
  }

  function updateStrokes(next: Stroke[]) {
    setStrokes(next);
    const canvas = canvasRef.current;
    if (canvas) drawStrokes(canvas, next);
  }

  function selectTarget(index: number) {
    setTargetIndex(index);
    updateStrokes([]);
    submit.reset();
  }

  function handleSubmit() {
    const canvas = canvasRef.current;
    if (!canvas || strokes.length === 0) return;
    submit.mutate(exportPng(canvas));
  }

  const dpr = typeof window === "undefined" ? 1 : Math.min(window.devicePixelRatio || 1, 2);

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Write</h1>
        <p className="text-sm text-ink-soft">
          Trace the character, then get scored on proportion, strokes, and legibility.
        </p>
      </header>

      {/* Target picker */}
      <div className="flex flex-wrap gap-1.5" aria-label="Choose a character">
        {TARGETS.map((char, index) => (
          <button
            key={`${char}-${index}`}
            type="button"
            lang="ko"
            onClick={() => selectTarget(index)}
            aria-pressed={index === targetIndex}
            className={`hangul-display size-10 rounded-lg border text-lg ${
              index === targetIndex
                ? "border-taegeuk-blue bg-taegeuk-blue/10 text-taegeuk-blue"
                : "border-line bg-paper-raised text-ink-soft"
            }`}
          >
            {char}
          </button>
        ))}
      </div>

      <Card className="space-y-3">
        <div className="relative mx-auto" style={{ width: CANVAS_SIZE, height: CANVAS_SIZE }}>
          {/* Tracing guide sits behind the transparent canvas — never exported. */}
          <div
            aria-hidden
            className="absolute inset-0 flex items-center justify-center rounded-lg border border-line bg-white"
          >
            {showGuide && (
              <span
                lang="ko"
                className="hangul-display select-none text-ink/10"
                style={{ fontSize: CANVAS_SIZE * 0.72, lineHeight: 1 }}
              >
                {target}
              </span>
            )}
          </div>
          <canvas
            ref={canvasRef}
            width={CANVAS_SIZE * dpr}
            height={CANVAS_SIZE * dpr}
            className="absolute inset-0 h-full w-full rounded-lg"
            style={{ touchAction: "none" }}
            aria-label={`Drawing canvas — write ${target}`}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
          />
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2">
          <Button
            variant="quiet"
            onClick={() => updateStrokes(strokes.slice(0, -1))}
            disabled={strokes.length === 0 || submit.isPending}
          >
            Undo
          </Button>
          <Button
            variant="quiet"
            onClick={() => updateStrokes([])}
            disabled={strokes.length === 0 || submit.isPending}
          >
            Clear
          </Button>
          <Button
            variant="quiet"
            onClick={() => setShowGuide((value) => !value)}
            aria-pressed={showGuide}
          >
            {showGuide ? "Hide guide" : "Show guide"}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={strokes.length === 0 || submit.isPending}
          >
            {submit.isPending ? "Checking…" : "Check my writing"}
          </Button>
        </div>
      </Card>

      {submit.isPending && <Spinner label="Scoring your writing" />}
      {submit.isError && <ErrorNote error={submit.error} retry={() => submit.reset()} />}

      {submit.isSuccess && (
        <Card className="space-y-3">
          <div className="flex justify-center gap-3">
            <ScoreRing score={submit.data.scores.overall_score} label="Overall" />
            <ScoreRing score={submit.data.scores.proportion_score} label="Proportion" />
            <ScoreRing score={submit.data.scores.stroke_score} label="Strokes" />
            <ScoreRing score={submit.data.scores.legibility_score} label="Legibility" />
          </div>
          <p className="text-center text-sm text-ink-soft">{submit.data.scores.feedback}</p>
          {targetIndex < TARGETS.length - 1 && (
            <div className="text-center">
              <Button onClick={() => selectTarget(targetIndex + 1)}>
                Next character: {TARGETS[targetIndex + 1]}
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
