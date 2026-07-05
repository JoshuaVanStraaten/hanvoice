/** Small shared UI primitives. Feature components live next to their pages. */

import { useEffect, useState } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { ApiError } from "../lib/api";

function prefersReducedMotion(): boolean {
  return (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

type ButtonVariant = "primary" | "speak" | "quiet";

const buttonStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-taegeuk-blue text-white hover:bg-taegeuk-blue-deep disabled:bg-ink-soft/40",
  speak: "bg-taegeuk-red text-white hover:bg-taegeuk-red-deep disabled:bg-ink-soft/40",
  quiet: "bg-transparent text-taegeuk-blue hover:bg-taegeuk-blue/10",
};

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      className={`rounded-full px-5 py-2.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed ${buttonStyles[variant]} ${className}`}
      {...props}
    />
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-(--radius-card) border border-line bg-paper-raised p-4 ${className}`}
    >
      {children}
    </div>
  );
}

/** A shimmering placeholder shaped like the content it becomes. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-lg ${className}`} aria-hidden />;
}

/** Card-shaped loading state for lists (lessons, progress). */
export function SkeletonCards({ count = 3, label = "Loading" }: { count?: number; label?: string }) {
  return (
    <div className="space-y-3" role="status" aria-label={label}>
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          className="space-y-3 rounded-(--radius-card) border border-line bg-paper-raised p-4"
        >
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-3 w-2/3" />
          <Skeleton className="h-1.5 w-full" />
        </div>
      ))}
      <span className="sr-only">{label}</span>
    </div>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-8 text-ink-soft" role="status">
      <span className="size-2 animate-pulse rounded-full bg-taegeuk-blue" />
      <span className="size-2 animate-pulse rounded-full bg-taegeuk-blue [animation-delay:150ms]" />
      <span className="size-2 animate-pulse rounded-full bg-taegeuk-red [animation-delay:300ms]" />
      <span className="sr-only">{label}</span>
    </div>
  );
}

export function ErrorNote({ error, retry }: { error: unknown; retry?: () => void }) {
  const message =
    error instanceof ApiError || error instanceof Error
      ? error.message
      : "Something went wrong.";
  const quota = error instanceof ApiError && error.isQuotaExceeded;
  return (
    <div
      role="alert"
      className="rounded-(--radius-card) border border-taegeuk-red/30 bg-taegeuk-red/5 p-4 text-sm"
    >
      <p className="text-ink">{message}</p>
      <div className="mt-2 flex gap-4">
        {retry && !quota && (
          <button className="font-semibold text-taegeuk-blue" onClick={retry}>
            Try again
          </button>
        )}
        {quota && (
          <a className="font-semibold text-taegeuk-blue" href="/subscription">
            See plans
          </a>
        )}
      </div>
    </div>
  );
}

/** 0–100 score shown as a ring; red while low, jade when strong. The arc
 * sweeps in and the number counts up on reveal (skipped for reduced motion). */
export function ScoreRing({ score, label }: { score: number; label: string }) {
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const [revealed, setRevealed] = useState(false);
  const [shown, setShown] = useState(() => (prefersReducedMotion() ? clamped : 0));

  useEffect(() => {
    // Two frames in: the arc transitions from empty, the number counts up.
    const frame = requestAnimationFrame(() => setRevealed(true));
    if (prefersReducedMotion()) {
      setShown(clamped);
      return () => cancelAnimationFrame(frame);
    }
    const startedAt = performance.now();
    let counting: number;
    const count = (now: number) => {
      const t = Math.min(1, (now - startedAt) / 700);
      setShown(clamped * (1 - (1 - t) ** 3)); // ease-out cubic
      if (t < 1) counting = requestAnimationFrame(count);
    };
    counting = requestAnimationFrame(count);
    return () => {
      cancelAnimationFrame(frame);
      cancelAnimationFrame(counting);
    };
  }, [clamped]);

  const color =
    clamped >= 80 ? "var(--color-jade)" : clamped >= 60 ? "var(--color-taegeuk-blue)" : "var(--color-taegeuk-red)";
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="64" height="64" viewBox="0 0 64 64" role="img" aria-label={`${label}: ${Math.round(clamped)} out of 100`}>
        <circle cx="32" cy="32" r={radius} fill="none" stroke="var(--color-line)" strokeWidth="6" />
        <circle
          className="score-arc"
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - (revealed ? clamped : 0) / 100)}
          transform="rotate(-90 32 32)"
        />
        <text x="32" y="37" textAnchor="middle" className="fill-ink text-sm font-bold">
          {Math.round(shown)}
        </text>
      </svg>
      <span className="text-xs text-ink-soft">{label}</span>
    </div>
  );
}

export function MeterBar({
  used,
  limit,
  label,
}: {
  used: number;
  limit: number;
  label: string;
}) {
  const fraction = limit > 0 ? Math.min(1, used / limit) : 1;
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-ink-soft">
        <span>{label}</span>
        <span>
          {used} / {limit}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-line">
        <div
          className={`h-full rounded-full ${fraction >= 1 ? "bg-taegeuk-red" : "bg-taegeuk-blue"}`}
          style={{ width: `${fraction * 100}%` }}
        />
      </div>
    </div>
  );
}
