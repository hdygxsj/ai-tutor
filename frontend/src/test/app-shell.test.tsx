import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, expect, test, vi } from "vitest";

import App from "../App";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    value: vi.fn().mockImplementation((query: string) => ({
      addEventListener: vi.fn(),
      addListener: vi.fn(),
      dispatchEvent: vi.fn(),
      matches: false,
      media: query,
      onchange: null,
      removeEventListener: vi.fn(),
      removeListener: vi.fn(),
    })),
    writable: true,
  });
});

vi.mock("../api/client", () => ({
  fetchDashboard: vi.fn().mockResolvedValue({
    active_plan_title: "M1 机器学习入门",
    assigned_count: 0,
    mastery_average: 0,
    next_action: "继续学习下一课",
  }),
  fetchActivePlan: vi.fn().mockResolvedValue(null),
  fetchTutorSettings: vi.fn().mockResolvedValue({
    base_url: "",
    has_api_key: false,
    model_name: "",
    provider: "fake",
  }),
  listCourses: vi.fn().mockResolvedValue([]),
  listAgentSessions: vi.fn().mockResolvedValue([]),
  createAgentSession: vi.fn(),
  createCourse: vi.fn(),
  activateCourse: vi.fn(),
  saveTutorSettings: vi.fn(),
  sendTutorMessage: vi.fn(),
  startIntake: vi.fn(),
  testTutorSettings: vi.fn(),
}));

test("renders the Agent workspace shell with top navigation", () => {
  const { container } = render(<App />);
  const header = container.querySelector(".app-shell__header");

  expect(screen.getByText("AI Dream")).toBeInTheDocument();
  expect(screen.getByText("Agent 课程工作台")).toBeInTheDocument();
  expect(header).toBeInTheDocument();
  expect(header).not.toHaveTextContent("当前课程");
  expect(header).not.toHaveTextContent("本会话 0 tokens");
  expect(screen.getByText("Dashboard")).toBeInTheDocument();
  expect(screen.getAllByText("AI 导师").length).toBeGreaterThan(0);
  expect(screen.getByText(initialGreeting)).toBeInTheDocument();
});

test("renders auxiliary pages after clicking menu items", async () => {
  const user = userEvent.setup();

  render(<App />);

  await user.click(menuItem("学习计划"));
  expect(screen.getByRole("heading", { name: "学习计划" })).toBeInTheDocument();
  expect(await screen.findByText("创建学习计划后，这里会展示课程模块。")).toBeInTheDocument();

  await user.click(menuItem("作业反馈"));
  expect(screen.getByRole("heading", { name: "作业与修订" })).toBeInTheDocument();
  expect(screen.getByText("当前还没有待处理作业。")).toBeInTheDocument();

  await user.click(menuItem("设置"));
  expect(screen.getByRole("heading", { name: "学习者偏好" })).toBeInTheDocument();
  expect(await screen.findByText("AI 导师配置")).toBeInTheDocument();
});

function menuItem(label: string): HTMLElement {
  const item = screen
    .getAllByText(label)
    .map((element) => element.closest('[role="menuitem"]'))
    .find((element): element is HTMLElement => element instanceof HTMLElement);

  if (!item) {
    throw new Error(`Menu item "${label}" was not found.`);
  }

  return item;
}

const initialGreeting =
  "你好，我是 AI Dream 导师。你可以告诉我今天想学习什么，我会用当前 Settings 中配置的导师 provider 帮你拆解下一步。";
