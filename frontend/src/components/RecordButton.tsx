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

const STOP_ICON = (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
    <rect x="7" y="7" width="10" height="10" rx="1.5" />
  </svg>
);

export function RecordButton({
  isRecording,
  onPress,
  disabled = false,
  size = "md",
}: {
  isRecording: boolean;
  onPress: () => void;
  disabled?: boolean;
  size?: "md" | "lg";
}) {
  return (
    <button
      type="button"
      onClick={onPress}
      disabled={disabled}
      aria-label={isRecording ? "Stop recording" : "Start recording"}
      aria-pressed={isRecording}
      className={[
        size === "lg" ? "size-16" : "size-12",
        "flex items-center justify-center rounded-full text-white transition-colors",
        "bg-taegeuk-red hover:bg-taegeuk-red-deep disabled:cursor-not-allowed disabled:bg-ink-soft/40",
        isRecording ? "speak-ring-active" : "",
      ].join(" ")}
    >
      {isRecording ? STOP_ICON : MIC_ICON}
    </button>
  );
}
