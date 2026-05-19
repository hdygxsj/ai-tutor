import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { fetchDashboard, startIntake } from "../api/client";
import { DashboardPage } from "../pages/DashboardPage";
import type { DashboardSummary, LearningPlanSummary } from "../types/learning";

vi.mock("../api/client", () => ({
  fetchDashboard: vi.fn(),
  startIntake: vi.fn(),
}));

const mockedFetchDashboard = vi.mocked(fetchDashboard);
const mockedStartIntake = vi.mocked(startIntake);

beforeEach(() => {
  mockedFetchDashboard.mockReset();
  mockedStartIntake.mockReset();
});

afterEach(() => {
  cleanup();
});

test("renders the learning dashboard and next action", async () => {
  mockedFetchDashboard.mockResolvedValue({
    active_plan_title: "M1 机器学习入门",
    assigned_count: 3,
    mastery_average: 4,
    next_action: "完成线性回归练习",
  });

  render(<DashboardPage />);

  expect(await screen.findByText("今日学习面板")).toBeInTheDocument();
  expect(screen.getByText("完成线性回归练习")).toBeInTheDocument();
  expect(screen.getByText("待完成作业")).toBeInTheDocument();
  expect(metricCard("待完成作业")).toHaveTextContent("3");
  expect(screen.getByText("平均掌握度")).toBeInTheDocument();
  expect(metricCard("平均掌握度")).toHaveTextContent("4/ 5");
  expect(screen.getByText("当前课程")).toBeInTheDocument();
  expect(metricCard("当前课程")).toHaveTextContent("M1 机器学习入门");
});

test("shows a retryable error when dashboard loading fails", async () => {
  mockedFetchDashboard
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValueOnce({
      active_plan_title: "M1 机器学习入门",
      assigned_count: 3,
      mastery_average: 4,
      next_action: "完成线性回归练习",
    });

  render(<DashboardPage />);

  expect(await screen.findByText("学习面板加载失败")).toBeInTheDocument();
  expect(screen.getByText(/检查后端服务/)).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "重试" }));

  expect(await screen.findByText("完成线性回归练习")).toBeInTheDocument();
  expect(mockedFetchDashboard).toHaveBeenCalledTimes(2);
});

test("shows an explicit error when creating the sample plan fails", async () => {
  mockedFetchDashboard.mockResolvedValue({
    active_plan_title: "M1 机器学习入门",
    assigned_count: 3,
    mastery_average: 4,
    next_action: "完成线性回归练习",
  });
  mockedStartIntake.mockRejectedValue(new Error("create failed"));

  render(<DashboardPage />);

  await screen.findByText("完成线性回归练习");
  const createButton = screen.getByRole("button", {
    name: "创建 M1 示例学习计划",
  });

  await userEvent.click(createButton);

  expect(await screen.findByText("创建学习计划失败")).toBeInTheDocument();
  expect(screen.getByText(/稍后重试/)).toBeInTheDocument();
  expect(createButton).not.toBeDisabled();
});

test("creates the sample plan and reloads dashboard data", async () => {
  mockedFetchDashboard
    .mockResolvedValueOnce({
      active_plan_title: "暂无课程",
      assigned_count: 0,
      mastery_average: 0,
      next_action: "创建学习计划开始",
    })
    .mockResolvedValueOnce({
      active_plan_title: "M1 示例学习计划",
      assigned_count: 2,
      mastery_average: 3,
      next_action: "学习监督式学习基础",
    });
  mockedStartIntake.mockResolvedValue(samplePlan());

  render(<DashboardPage />);

  await screen.findByText("创建学习计划开始");
  await userEvent.click(
    screen.getByRole("button", { name: "创建 M1 示例学习计划" }),
  );

  expect(mockedStartIntake).toHaveBeenCalledWith({
    goal: "完成 M1 机器学习入门学习计划",
    background: "已有基础 Python 经验，希望建立机器学习核心概念和练习闭环。",
    weekly_hours: 6,
  });
  expect(await screen.findByText("学习监督式学习基础")).toBeInTheDocument();
  expect(metricCard("当前课程")).toHaveTextContent("M1 示例学习计划");
  expect(metricCard("待完成作业")).toHaveTextContent("2");
  expect(mockedFetchDashboard).toHaveBeenCalledTimes(2);
});

test("keeps the newest dashboard response when requests resolve out of order", async () => {
  const initialRequest = deferred<DashboardSummary>();
  const reloadRequest = deferred<DashboardSummary>();

  mockedFetchDashboard
    .mockImplementationOnce(() => initialRequest.promise)
    .mockImplementationOnce(() => reloadRequest.promise);
  mockedStartIntake.mockResolvedValue(samplePlan());

  render(<DashboardPage />);

  await userEvent.click(
    screen.getByRole("button", { name: "创建 M1 示例学习计划" }),
  );
  await waitFor(() => expect(mockedFetchDashboard).toHaveBeenCalledTimes(2));

  await act(async () => {
    reloadRequest.resolve({
      active_plan_title: "最新课程",
      assigned_count: 4,
      mastery_average: 5,
      next_action: "继续最新学习建议",
    });
  });

  expect(await screen.findByText("继续最新学习建议")).toBeInTheDocument();
  expect(metricCard("当前课程")).toHaveTextContent("最新课程");

  await act(async () => {
    initialRequest.resolve({
      active_plan_title: "旧课程",
      assigned_count: 1,
      mastery_average: 2,
      next_action: "旧学习建议",
    });
  });

  await waitFor(() => {
    expect(screen.queryByText("旧学习建议")).not.toBeInTheDocument();
    expect(metricCard("当前课程")).toHaveTextContent("最新课程");
    expect(metricCard("待完成作业")).toHaveTextContent("4");
  });
});

function metricCard(title: string): HTMLElement {
  const titleElement = screen.getByText(title);
  const card = titleElement.closest(".ant-card");

  expect(card).not.toBeNull();

  return card as HTMLElement;
}

function samplePlan(): LearningPlanSummary {
  return {
    goal: "完成 M1 机器学习入门学习计划",
    id: "plan-1",
    lessons: [],
    status: "active",
    title: "M1 示例学习计划",
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((innerResolve, innerReject) => {
    resolve = innerResolve;
    reject = innerReject;
  });

  return { promise, reject, resolve };
}
