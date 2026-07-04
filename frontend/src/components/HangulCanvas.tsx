/** Shared Hangul drawing surface: transparent canvas over a faint tracing
 * guide, exported composited onto clean white so the vision model never sees
 * the guide. Used by the Write tab (free practice) and write lesson blocks. */

import { useRef, useState } from "react";

import { Button } from "./ui";

export const CANVAS_SIZE = 320; // CSS px; internal resolution scales with DPR

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

/** Render with `key={target}` when the target can change on the same screen —
 * a new target remounts the canvas with a clean slate. */
export function HangulCanvas({
  target,
  submitting,
  submitLabel = "Check my writing",
  onSubmit,
}: {
  target: string;
  submitting: boolean;
  submitLabel?: string;
  onSubmit: (imageBase64: string) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const currentStroke = useRef<Stroke>([]);
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [showGuide, setShowGuide] = useState(true);

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

  function handleSubmit() {
    const canvas = canvasRef.current;
    if (!canvas || strokes.length === 0) return;
    onSubmit(exportPng(canvas));
  }

  const dpr = typeof window === "undefined" ? 1 : Math.min(window.devicePixelRatio || 1, 2);

  return (
    <div className="space-y-3">
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
          disabled={strokes.length === 0 || submitting}
        >
          Undo
        </Button>
        <Button
          variant="quiet"
          onClick={() => updateStrokes([])}
          disabled={strokes.length === 0 || submitting}
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
        <Button onClick={handleSubmit} disabled={strokes.length === 0 || submitting}>
          {submitting ? "Checking…" : submitLabel}
        </Button>
      </div>
    </div>
  );
}
