/** Route table. Public routes (marketing + auth) render bare; every
 * authenticated route nests under <App/>, which enforces auth and wraps
 * the page in the mobile app shell. */

import { createBrowserRouter } from "react-router-dom";

import { App } from "./App";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { PasswordResetPage } from "./pages/PasswordResetPage";
import { TermsPage } from "./pages/TermsPage";
import { PrivacyPage } from "./pages/PrivacyPage";
import { RefundsPage } from "./pages/RefundsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LessonsPage } from "./pages/LessonsPage";
import { LessonDetailPage } from "./pages/LessonDetailPage";
import { TalkPage } from "./pages/TalkPage";
import { ConversationPage } from "./pages/ConversationPage";
import { WritingPage } from "./pages/WritingPage";
import { ProgressPage } from "./pages/ProgressPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SubscriptionPage } from "./pages/SubscriptionPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignupPage /> },
  { path: "/reset-password", element: <PasswordResetPage /> },
  { path: "/terms", element: <TermsPage /> },
  { path: "/privacy", element: <PrivacyPage /> },
  { path: "/refunds", element: <RefundsPage /> },
  {
    element: <App />,
    children: [
      { path: "/home", element: <DashboardPage /> },
      { path: "/lessons", element: <LessonsPage /> },
      { path: "/lessons/:slug", element: <LessonDetailPage /> },
      { path: "/talk", element: <TalkPage /> },
      { path: "/talk/:sessionId", element: <ConversationPage /> },
      { path: "/write", element: <WritingPage /> },
      { path: "/progress", element: <ProgressPage /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "/subscription", element: <SubscriptionPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
