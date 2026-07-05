/** The red speak ring — the app's signature control. Press to record, press
 * again to stop. Red is reserved for speaking; this is where it lives. */

const MIC_ICON = (
  <svg
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0" />
    <path d="M12 18v3" />
  </svg>
);

/** Bars weighted unevenly so the meter reads as a voice, not a gauge. */
const BAR_WEIGHTS = [0.55, 0.85, 1, 0.7, 0.45];

function VoiceBars({ level }: { level: number }) {
  return (
    <span className="flex h-6 items-center gap-[3px]" aria-hidden>
      {BAR_WEIGHTS.map((weight, index) => (
        <span
          key={index}
          className="w-1 rounded-full bg-white transition-[height] duration-75 ease-out"
          style={{ height: `${Math.round(18 + Math.min(1, level) * weight * 82)}%` }}
        />
      ))}
    </span>
  );
}

/** Countdown ring while the silence gate runs down — the visible promise
 * that auto-stop is about to fire, so it never feels haunted. */
function SilenceArc({ progress }: { progress: number }) {
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  return (
    <svg
      viewBox="0 0 100 100"
      className="pointer-events-none absolute inset-0 size-full -rotate-90 motion-reduce:hidden"
      aria-hidden
    >
      <circle
        cx="50"
        cy="50"
        r={radius}
        fill="none"
        stroke="white"
        strokeOpacity="0.9"
        strokeWidth="5"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={circumference * progress}
      />
    </svg>
  );
}

export function RecordButton({
  isRecording,
  onPress,
  disabled = false,
  size = "md",
  level = 0,
  silenceProgress = 0,
}: {
  isRecording: boolean;
  onPress: () => void;
  disabled?: boolean;
  size?: "md" | "lg";
  /** Live mic loudness (0-1) shown as dancing bars while recording. */
  level?: number;
  /** 0-1 through the auto-stop silence window; > 0 draws the countdown arc. */
  silenceProgress?: number;
}) {
  return (
    <button
      type="button"
      onClick={onPress}
      disabled={disabled}
      aria-label={isRecording ? "Stop recording and get scored" : "Start recording"}
      title={isRecording ? "Tap to stop" : undefined}
      aria-pressed={isRecording}
      className={[
        size === "lg" ? "size-16" : "size-12",
        "relative flex items-center justify-center rounded-full text-white transition-colors",
        "bg-taegeuk-red hover:bg-taegeuk-red-deep disabled:cursor-not-allowed disabled:bg-ink-soft/40",
        isRecording ? "speak-ring-active" : "",
      ].join(" ")}
    >
      {isRecording && silenceProgress > 0 && <SilenceArc progress={silenceProgress} />}
      {isRecording ? <VoiceBars level={level} /> : MIC_ICON}
    </button>
  );
}
