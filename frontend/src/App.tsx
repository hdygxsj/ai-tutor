import { useState } from "react";

import { AppShell } from "./components/AppShell";
import type { AppMenuKey } from "./components/AppShell";
import { AssignmentsPage } from "./pages/AssignmentsPage";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LearningPlanPage } from "./pages/LearningPlanPage";
import { SettingsPage } from "./pages/SettingsPage";

const PAGES: Record<AppMenuKey, JSX.Element> = {
  assignments: <AssignmentsPage />,
  chat: <ChatPage />,
  dashboard: <DashboardPage />,
  learning: <LearningPlanPage />,
  settings: <SettingsPage />,
};

export default function App() {
  const [activeKey, setActiveKey] = useState<AppMenuKey>("chat");

  return (
    <AppShell activeKey={activeKey} onSelect={setActiveKey}>
      {PAGES[activeKey]}
    </AppShell>
  );
}
