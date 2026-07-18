/** Shared frame for the auth pages: wordmark on paper, one centered card. */

import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { Card } from "./ui";

export function AuthLayout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-6 bg-paper px-4 py-10">
      <Link to="/" className="text-2xl font-bold tracking-tight">
        <span className="text-taegeuk-red">한</span>
        <span className="text-taegeuk-blue">Voice</span>
      </Link>
      <Card className="w-full max-w-sm space-y-4">
        <h1 className="text-xl font-bold">{title}</h1>
        {children}
      </Card>
    </div>
  );
}

/** "Continue with Google" + divider, shared by login and signup. */
export function GoogleAuthButton({
  onError,
  signInWithGoogle,
}: {
  onError: (message: string) => void;
  signInWithGoogle: () => Promise<void>;
}) {
  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={() => {
          signInWithGoogle().catch((err: unknown) => {
            onError(err instanceof Error ? err.message : "Google sign-in failed.");
          });
        }}
        className="flex w-full items-center justify-center gap-2 rounded-lg border border-line bg-paper px-3 py-2.5 text-sm font-semibold hover:bg-paper-raised"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
          <path
            fill="#4285F4"
            d="M23.5 12.27c0-.85-.08-1.66-.22-2.45H12v4.64h6.45a5.52 5.52 0 0 1-2.39 3.62v3h3.87c2.26-2.09 3.57-5.16 3.57-8.81Z"
          />
          <path
            fill="#34A853"
            d="M12 24c3.24 0 5.96-1.07 7.93-2.91l-3.87-3c-1.07.72-2.45 1.15-4.06 1.15-3.12 0-5.77-2.11-6.71-4.95H1.29v3.1A12 12 0 0 0 12 24Z"
          />
          <path
            fill="#FBBC05"
            d="M5.29 14.29a7.2 7.2 0 0 1 0-4.58v-3.1H1.29a12 12 0 0 0 0 10.78l4-3.1Z"
          />
          <path
            fill="#EA4335"
            d="M12 4.77c1.76 0 3.34.6 4.58 1.79l3.44-3.44A11.98 11.98 0 0 0 1.29 6.61l4 3.1C6.23 6.88 8.88 4.77 12 4.77Z"
          />
        </svg>
        Continue with Google
      </button>
      <div className="flex items-center gap-3 text-xs text-ink-soft">
        <span className="h-px flex-1 bg-line" />
        or
        <span className="h-px flex-1 bg-line" />
      </div>
    </div>
  );
}

/** Text input styled for the auth forms. */
export function AuthField({
  id,
  label,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { id: string; label: string }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <input
        id={id}
        className="w-full rounded-lg border border-line bg-paper px-3 py-2.5 text-sm placeholder:text-ink-soft/70"
        {...props}
      />
    </div>
  );
}
