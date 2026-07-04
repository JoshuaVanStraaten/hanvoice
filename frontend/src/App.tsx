/** Protected layout: gate on auth, then render the app shell around the
 * active route. Mounted as the parent of every authenticated route. */

import { Outlet } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { RequireAuth } from "./components/RequireAuth";

export function App() {
  return (
    <RequireAuth>
      <AppShell>
        <Outlet />
      </AppShell>
    </RequireAuth>
  );
}
