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
