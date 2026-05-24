import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, beforeEach, expect, test, vi } from "vitest";

import {
  activateCourse,
  createCourse,
  fetchCourseTimeline,
  listCourses,
} from "../api/client";
import { LearningPlanPage } from "../pages/LearningPlanPage";

vi.mock("../api/client", () => ({
  activateCourse: vi.fn(),
  createCourse: vi.fn(),
  fetchCourseTimeline: vi.fn(),
  listCourses: vi.fn(),
}));

const mockedActivateCourse = vi.mocked(activateCourse);
const mockedCreateCourse = vi.mocked(createCourse);
const mockedFetchCourseTimeline = vi.mocked(fetchCourseTimeline);
const mockedListCourses = vi.mocked(listCourses);

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
  window.localStorage.clear();
  mockedListCourses.mockResolvedValue([
    {
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
    },
    {
      goal: "学习 Rust 所有权",
      id: "plan-2",
      lessons: [
        {
          id: "lesson-2",
          mastery_score: 0,
          next_action: "阅读所有权示例",
          objective: "理解 move 与 borrow",
          status: "in_progress",
          title: "所有权入门",
        },
      ],
      status: "paused",
      title: "Rust 所有权课程",
    },
  ]);
  mockedCreateCourse.mockResolvedValue({
    goal: "学习强化学习",
    id: "plan-3",
    lessons: [],
    status: "active",
    title: "机器学习教师计划",
  });
  mockedActivateCourse.mockResolvedValue({
    goal: "学习 Rust 所有权",
    id: "plan-2",
    lessons: [
      {
        id: "lesson-2",
        mastery_score: 0,
        next_action: "阅读所有权示例",
        objective: "理解 move 与 borrow",
        status: "in_progress",
        title: "所有权入门",
      },
    ],
    status: "active",
    title: "Rust 所有权课程",
  });
  mockedFetchCourseTimeline.mockResolvedValue({
    course_id: "plan-1",
    events: [
      {
        created_at: "2026-05-23T00:00:00",
        event_type: "plan_created",
        id: "event-1",
        payload: {},
        summary: "创建课程：机器学习教师计划",
      },
      {
        created_at: "2026-05-23T00:05:00",
        event_type: "runtime_run",
        id: "event-2",
        payload: {},
        summary: "运行记录：sandbox Code preview: print('hello')",
      },
    ],
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
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

test("lists courses with progress summaries and active status", async () => {
  render(<LearningPlanPage />);

  expect(await screen.findByText("课程管理")).toBeInTheDocument();
  expect(screen.getByText("Rust 所有权课程")).toBeInTheDocument();
  expect(screen.getByText("active")).toBeInTheDocument();
  expect(screen.getByText("paused")).toBeInTheDocument();
  expect(screen.getByText("进度 1/1")).toBeInTheDocument();
  expect(screen.getByText("掌握均分 1")).toBeInTheDocument();
  expect(screen.getByText("课程回溯")).toBeInTheDocument();
});

test("creates a new course from the course management page", async () => {
  const user = userEvent.setup();

  render(<LearningPlanPage />);

  await user.type(await screen.findByLabelText("新课程目标"), "学习强化学习");
  await user.click(screen.getByRole("button", { name: "创建课程" }));

  await waitFor(() =>
    expect(mockedCreateCourse).toHaveBeenCalledWith({
      goal: "学习强化学习",
      weekly_hours: 6,
    }),
  );
  await waitFor(() => expect(mockedListCourses).toHaveBeenCalledTimes(2));
});

test("switches the active course and loads its timeline", async () => {
  const user = userEvent.setup();

  render(<LearningPlanPage />);

  await screen.findByText("Rust 所有权课程");
  await user.click(screen.getByRole("button", { name: "激活 Rust 所有权课程" }));

  await waitFor(() => expect(mockedActivateCourse).toHaveBeenCalledWith("plan-2"));
  expect(mockedFetchCourseTimeline).toHaveBeenLastCalledWith("plan-2");
});

test("shows an empty state when no course exists", async () => {
  mockedListCourses.mockResolvedValue([]);

  render(<LearningPlanPage />);

  expect(await screen.findByText("创建学习计划后，这里会展示课程模块。")).toBeInTheDocument();
});

test("shows a helpful error when courses cannot load", async () => {
  mockedListCourses.mockRejectedValue(new Error("读取课程失败"));

  render(<LearningPlanPage />);

  expect(await screen.findByText("读取课程失败")).toBeInTheDocument();
});

test("renders a lightweight course timeline for the active plan", async () => {
  render(<LearningPlanPage />);

  expect(await screen.findByText("课程回溯")).toBeInTheDocument();
  expect(screen.getAllByText("创建课程：机器学习教师计划").length).toBeGreaterThan(0);
  expect(
    screen.getAllByText("运行记录：sandbox Code preview: print('hello')").length,
  ).toBeGreaterThan(0);
  expect(mockedFetchCourseTimeline).toHaveBeenCalledWith("plan-1");
});
