/** Shared stub shell for pages not yet built out. Each real page (M7/M8)
 * replaces its own file wholesale; this keeps the router type-checking and
 * navigable in the meantime without pretending a feature is finished. */

import type { ReactNode } from "react";

export function PagePlaceholder({
  title,
  milestone,
  children,
}: {
  title: string;
  milestone: string;
  children?: ReactNode;
}) {
  return (
    <section className="space-y-2">
      <h1 className="text-2xl font-bold">{title}</h1>
      <p className="text-sm text-ink-soft">Coming in {milestone}.</p>
      {children}
    </section>
  );
}
