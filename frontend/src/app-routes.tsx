import { AssignmentsPage } from "./pages/AssignmentsPage";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ExperimentsPage } from "./pages/ExperimentsPage";
import { LearningPlanPage } from "./pages/LearningPlanPage";
import { SettingsPage } from "./pages/SettingsPage";

export type AppMenuKey =
  | "dashboard"
  | "chat"
  | "learning"
  | "assignments"
  | "experiments"
  | "settings";

export interface AppRoute {
  element: JSX.Element;
  key: AppMenuKey;
  path: string;
}

export const APP_ROUTES: AppRoute[] = [
  { element: <ChatPage />, key: "chat", path: "/chat" },
  { element: <DashboardPage />, key: "dashboard", path: "/dashboard" },
  { element: <LearningPlanPage />, key: "learning", path: "/learning" },
  { element: <AssignmentsPage />, key: "assignments", path: "/assignments" },
  { element: <ExperimentsPage />, key: "experiments", path: "/experiments" },
  { element: <SettingsPage />, key: "settings", path: "/settings" },
];

export const DEFAULT_APP_ROUTE = APP_ROUTES[0];

export const APP_ROUTE_BY_KEY = APP_ROUTES.reduce(
  (routes, route) => ({
    ...routes,
    [route.key]: route,
  }),
  {} as Record<AppMenuKey, AppRoute>,
);

export function resolveAppRoute(pathname: string): {
  route: AppRoute;
  shouldReplace: boolean;
} {
  const normalizedPath = normalizePath(pathname);
  const route = APP_ROUTES.find((candidate) => candidate.path === normalizedPath);

  if (route) {
    return { route, shouldReplace: false };
  }

  return { route: DEFAULT_APP_ROUTE, shouldReplace: true };
}

function normalizePath(pathname: string) {
  if (pathname === "/") {
    return pathname;
  }

  return pathname.replace(/\/+$/, "");
}
