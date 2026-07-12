/** Shared frame for the public legal pages (terms, privacy, refunds).
 * Static content, no data fetching — these pages must load even if the API
 * is down, and Paddle's site review reads them without JavaScript context. */

import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function LegalLayout({
  title,
  updated,
  children,
}: {
  title: string;
  updated: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-dvh bg-paper">
      <header className="mx-auto flex h-14 w-full max-w-3xl items-center justify-between px-4">
        <Link to="/" className="text-lg font-bold tracking-tight">
          <span className="text-taegeuk-red">한</span>
          <span className="text-taegeuk-blue">Voice</span>
        </Link>
        <Link to="/login" className="text-sm font-semibold text-taegeuk-blue">
          Log in
        </Link>
      </header>

      <main className="mx-auto w-full max-w-3xl space-y-6 px-4 pt-10 pb-16">
        <header className="space-y-1">
          <h1 className="text-3xl font-bold">{title}</h1>
          <p className="text-sm text-ink-soft">Last updated: {updated}</p>
        </header>
        <div className="space-y-6 text-sm leading-relaxed [&_h2]:text-lg [&_h2]:font-bold [&_h2]:text-ink [&_li]:ml-5 [&_li]:list-disc [&_section]:space-y-2 text-ink-soft">
          {children}
        </div>
        <nav className="flex gap-4 border-t border-line pt-6 text-xs">
          <Link to="/terms" className="font-semibold text-taegeuk-blue">
            Terms of Service
          </Link>
          <Link to="/privacy" className="font-semibold text-taegeuk-blue">
            Privacy Policy
          </Link>
          <Link to="/refunds" className="font-semibold text-taegeuk-blue">
            Refund Policy
          </Link>
        </nav>
      </main>
    </div>
  );
}
