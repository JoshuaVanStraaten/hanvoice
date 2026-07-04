/** Mobile-first app shell: a slim top bar and a fixed bottom tab bar.
 * Nav is "learning" territory, so it lives in taegeuk blue; the Talk tab is
 * the one speaking action and picks up red when active. Safe-area insets keep
 * the bar clear of the iOS home indicator. */

import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

interface Tab {
  to: string;
  label: string;
  /** Talk is a speaking action — it reads red rather than blue when active. */
  speak?: boolean;
  icon: ReactNode;
}

const iconProps = {
  width: 22,
  height: 22,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

const TABS: Tab[] = [
  {
    to: "/home",
    label: "Home",
    icon: (
      <svg {...iconProps}>
        <path d="M3 10.5 12 3l9 7.5" />
        <path d="M5 9.5V21h14V9.5" />
      </svg>
    ),
  },
  {
    to: "/lessons",
    label: "Lessons",
    icon: (
      <svg {...iconProps}>
        <path d="M4 5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v14l-5-2.5L7 19V5" />
      </svg>
    ),
  },
  {
    to: "/talk",
    label: "Talk",
    speak: true,
    icon: (
      <svg {...iconProps}>
        <rect x="9" y="3" width="6" height="11" rx="3" />
        <path d="M5 11a7 7 0 0 0 14 0" />
        <path d="M12 18v3" />
      </svg>
    ),
  },
  {
    to: "/write",
    label: "Write",
    icon: (
      <svg {...iconProps}>
        <path d="M12 20h9" />
        <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
      </svg>
    ),
  },
  {
    to: "/settings",
    label: "Profile",
    icon: (
      <svg {...iconProps}>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </svg>
    ),
  },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col bg-paper">
      <header className="sticky top-0 z-10 border-b border-line bg-paper/90 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-2xl items-center px-4">
          <span className="text-lg font-bold tracking-tight">
            <span className="text-taegeuk-red">한</span>
            <span className="text-taegeuk-blue">Voice</span>
          </span>
        </div>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1 px-4 pt-4 pb-24">{children}</main>

      <nav
        aria-label="Primary"
        className="fixed inset-x-0 bottom-0 z-10 border-t border-line bg-paper-raised/95 backdrop-blur"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <ul className="mx-auto flex w-full max-w-2xl">
          {TABS.map((tab) => (
            <li key={tab.to} className="flex-1">
              <NavLink
                to={tab.to}
                className={({ isActive }) =>
                  [
                    "flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium transition-colors",
                    isActive
                      ? tab.speak
                        ? "text-taegeuk-red"
                        : "text-taegeuk-blue"
                      : "text-ink-soft hover:text-ink",
                  ].join(" ")
                }
              >
                {tab.icon}
                <span>{tab.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
