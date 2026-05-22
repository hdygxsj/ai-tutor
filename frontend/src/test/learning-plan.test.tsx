import { render, screen } from "@testing-library/react";
import { beforeAll, beforeEach, expect, test, vi } from "vitest";

import { fetchActivePlan } from "../api/client";
import { LearningPlanPage } from "../pages/LearningPlanPage";

vi.mock("../api/client", () => ({
  fetchActivePlan: vi.fn(),
}));

const mockedFetchActivePlan = vi.mocked(fetchActivePlan);

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

beforeEach(() => {
  mockedFetchActivePlan.mockResolvedValue({
    goal: "我想学习线性回归",
    id: "plan-1",
    lessons: [
      {
        id: "lesson-1",
        mastery_score: 1,
        next_action: "完成 autograd 概念作业",
        objective: "理解线性回归训练流程",
        status: "assignment_ready",
        title: "线性回归入门",
      },
    ],
    status: "active",
    title: "机器学习教师计划",
  });
});

test("renders the active learning plan and tasks", async () => {
  render(<LearningPlanPage />);

  expect(await screen.findByText("机器学习教师计划")).toBeInTheDocument();
  expect(screen.getByText("我想学习线性回归")).toBeInTheDocument();
  expect(screen.getByText("线性回归入门")).toBeInTheDocument();
  expect(screen.getByText("理解线性回归训练流程")).toBeInTheDocument();
  expect(screen.getByText("完成 autograd 概念作业")).toBeInTheDocument();
  expect(screen.queryByText("创建学习计划后，这里会展示课程模块。")).not.toBeInTheDocument();
});

test("shows an empty state when no plan exists", async () => {
  mockedFetchActivePlan.mockResolvedValue(null);

  render(<LearningPlanPage />);

  expect(await screen.findByText("创建学习计划后，这里会展示课程模块。")).toBeInTheDocument();
});

test("shows a helpful error when the active plan cannot load", async () => {
  mockedFetchActivePlan.mockRejectedValue(new Error("读取学习计划失败"));

  render(<LearningPlanPage />);

  expect(await screen.findByText("读取学习计划失败")).toBeInTheDocument();
});
