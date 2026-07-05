/** The dojang (도장) — Korea's red name-seal — stamped onto the paper when a
 * step is passed. The one loud celebration in the app: everything around it
 * stays quiet so the thump lands. Ends tilted like a real hand stamp. */

export function Dojang({ label = "Passed" }: { label?: string }) {
  return (
    <div className="flex justify-center py-1" role="status">
      <span
        aria-hidden
        className="dojang-stamp inline-flex size-16 flex-col items-center justify-center gap-0.5 rounded-md bg-taegeuk-red text-white shadow-[0_2px_10px_rgb(199_62_58/0.45),inset_0_0_0_2px_rgb(255_255_255/0.85),inset_0_0_0_4px_var(--color-taegeuk-red)]"
      >
        <span lang="ko" className="hangul-display text-lg leading-none">
          통
        </span>
        <span lang="ko" className="hangul-display text-lg leading-none">
          과
        </span>
      </span>
      <span className="sr-only">{label}</span>
    </div>
  );
}
