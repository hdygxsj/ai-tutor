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
  startIntake: vi.fn(),
}));

test("renders the task 6 application shell", () => {
  render(<App />);

  expect(screen.getByText("AI Dream")).toBeInTheDocument();
  expect(screen.getByText("机器学习教师 Agent")).toBeInTheDocument();
  expect(screen.getByText("Dashboard")).toBeInTheDocument();
});

test("renders auxiliary pages after clicking menu items", async () => {
  const user = userEvent.setup();

  render(<App />);

  await user.click(menuItem("AI 导师"));
  expect(screen.getByRole("heading", { name: "引导式学习对话" })).toBeInTheDocument();
  expect(screen.getByText("等待任务接入对话流。")).toBeInTheDocument();

  await user.click(menuItem("学习计划"));
  expect(screen.getByRole("heading", { name: "学习计划" })).toBeInTheDocument();
  expect(screen.getByText("创建学习计划后，这里会展示课程模块。")).toBeInTheDocument();

  await user.click(menuItem("作业反馈"));
  expect(screen.getByRole("heading", { name: "作业与修订" })).toBeInTheDocument();
  expect(screen.getByText("当前还没有待处理作业。")).toBeInTheDocument();

  await user.click(menuItem("设置"));
  expect(screen.getByRole("heading", { name: "学习者偏好" })).toBeInTheDocument();
  expect(screen.getByText("设置表单将在后续任务中启用。")).toBeInTheDocument();
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
