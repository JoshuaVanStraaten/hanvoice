import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-paper px-4">
      <p className="hangul-display text-5xl text-taegeuk-blue">길을 잃었어요</p>
      <p className="text-sm text-ink-soft">That page doesn&apos;t exist.</p>
      <Link to="/" className="font-semibold text-taegeuk-blue">
        Back to HanVoice
      </Link>
    </div>
  );
}
