import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, beforeEach, expect, test, vi } from "vitest";

import {
  createAgentSession,
  createCourse,
  listAgentSessions,
  listCourses,
  runAssignment,
  sendTutorMessage,
  startIntake,
  submitAssignment,
} from "../api/client";
import { ChatPage } from "../pages/ChatPage";

vi.mock("../api/client", () => ({
  sendTutorMessage: vi.fn(),
  startIntake: vi.fn(),
  submitAssignment: vi.fn(),
  runAssignment: vi.fn(),
  listCourses: vi.fn(),
  createCourse: vi.fn(),
  listAgentSessions: vi.fn(),
  createAgentSession: vi.fn(),
}));

const mockedSendTutorMessage = vi.mocked(sendTutorMessage);
const mockedStartIntake = vi.mocked(startIntake);
const mockedSubmitAssignment = vi.mocked(submitAssignment);
const mockedRunAssignment = vi.mocked(runAssignment);
const mockedListCourses = vi.mocked(listCourses);
const mockedCreateCourse = vi.mocked(createCourse);
const mockedListAgentSessions = vi.mocked(listAgentSessions);
const mockedCreateAgentSession = vi.mocked(createAgentSession);
const initialGreeting =
  "你好，我是 AI Dream 导师。你可以告诉我今天想学习什么，我会用当前 Settings 中配置的导师 provider 帮你拆解下一步。";

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
      goal: "学习线性回归",
      id: "course-1",
      lessons: [],
      status: "active",
      title: "线性回归课程",
    },
  ]);
  mockedCreateCourse.mockResolvedValue({
    goal: "自由探索",
    id: "course-new",
    lessons: [],
    status: "active",
    title: "自由探索课程",
  });
  mockedListAgentSessions.mockResolvedValue([]);
  mockedCreateAgentSession.mockResolvedValue({
    course_id: "course-1",
    id: "session-1",
    messages: [],
    status: "active",
    title: "新的 Agent 会话",
    token_usage: { total_tokens: 0 },
  });
  mockedSendTutorMessage.mockResolvedValue({
    provider: "fake",
    reply: "可以先从监督学习的训练流程开始。",
    usage: {
      completion_tokens: 12,
      model: "fake",
      prompt_tokens: 18,
      provider: "fake",
      source: "estimated",
      total_tokens: 30,
    },
    actions: [],
    course_id: null,
    session_id: null,
  });
  mockedStartIntake.mockResolvedValue({
    goal: "我想学习线性回归",
    id: "plan-chat-1",
    lessons: [
      {
        id: "lesson-chat-1",
        mastery_score: 1,
        next_action: "完成 autograd 概念作业",
        objective: "解释梯度下降和损失函数",
        status: "assignment_ready",
        title: "线性回归入门",
      },
    ],
    status: "active",
    title: "机器学习教师计划",
  });
  mockedSubmitAssignment.mockResolvedValue({
    feedback: "代码覆盖了 requires_grad 与 backward。",
    id: "review-1",
    score: 90,
    status: "passed",
  });
  mockedRunAssignment.mockResolvedValue({
    artifacts: [],
    assignment_id: "assignment-1",
    backend: "sandbox",
    course_id: "course-1",
    id: "run-1",
    logs: [
      "Sandbox prepared run with image python:3.12-slim.",
      "Code preview: print('hello runtime')",
    ],
    metadata: { execution: "preview_only", image: "python:3.12-slim" },
    status: "completed",
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test("renders initial tutor greeting and composer", () => {
  render(<ChatPage />);

  expect(screen.getByRole("heading", { name: "引导式学习对话" })).toBeInTheDocument();
  expect(screen.getByText(initialGreeting)).toBeInTheDocument();
  expect(screen.getByLabelText("输入给导师的消息")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "发送" })).toBeInTheDocument();
});

test("starts with a centered chat workspace and no coding panel", () => {
  const { container } = render(<ChatPage />);

  const workspace = container.querySelector(".chat-workspace");

  expect(workspace).toBeInTheDocument();
  expect(workspace).not.toHaveClass("chat-workspace--coding");
  expect(screen.queryByLabelText("在线 IDE / 调试工作区")).not.toBeInTheDocument();
});

test("debug layout toggle shows the right coding workspace", async () => {
  const user = userEvent.setup();
  const { container } = render(<ChatPage />);

  await user.click(screen.getByRole("button", { name: "调试布局" }));

  expect(container.querySelector(".chat-workspace")).toHaveClass("chat-workspace--coding");
  expect(screen.getByLabelText("在线 IDE / 调试工作区")).toBeInTheDocument();
  expect(screen.getByText("调试模式")).toBeInTheDocument();
});

test("debug layout uses the compact chat card without the large hero", async () => {
  const user = userEvent.setup();
  render(<ChatPage />);

  expect(screen.getByRole("heading", { name: "引导式学习对话" })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "调试布局" }));

  expect(screen.queryByRole("heading", { name: "引导式学习对话" })).not.toBeInTheDocument();
});

test("chat header keeps the tutor title separate from wrapping meta", () => {
  const { container } = render(<ChatPage />);

  const title = screen.getByText("AI Dream 导师");

  expect(title).toHaveClass("chat-toolbar__title");
  expect(title).toHaveTextContent(/^AI Dream 导师$/);
  expect(container.querySelector(".chat-toolbar__meta")).toHaveTextContent("等待你的问题");
  expect(container.querySelector(".chat-toolbar__meta")).toHaveTextContent("等待导师回复");
  expect(container.querySelector(".chat-toolbar__meta")).toHaveTextContent("本会话 0 tokens");
});

test("message bubbles do not repeat role titles above the text", async () => {
  const user = userEvent.setup();
  const { container } = render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "解释一下 autograd");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();
  expect(container.querySelector(".chat-bubble__speaker")).not.toBeInTheDocument();
});

test("sent and received messages show lightweight timestamps", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "时间戳测试");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();
  expect(screen.getAllByText(/\d{1,2}:\d{2}/).length).toBeGreaterThanOrEqual(2);
});

test("sending a message calls sendTutorMessage with message and history", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "我想学习线性回归");
  await screen.findByText(/线性回归课程/);
  await user.click(screen.getByRole("button", { name: "发送" }));

  await waitFor(() =>
    expect(mockedSendTutorMessage).toHaveBeenCalledWith({
      course_id: "course-1",
      history: [expect.objectContaining({ content: initialGreeting, role: "assistant" })],
      message: "我想学习线性回归",
      session_id: "session-1",
    }),
  );
});

test("returned assistant reply appears in the thread", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "下一步做什么？");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();
});

test("hides the hero and shows token usage after the session starts", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "我想学习线性回归");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "引导式学习对话" })).not.toBeInTheDocument();
  expect(screen.getByText("本次 30 tokens")).toBeInTheDocument();
  expect(screen.getByText("本会话 30 tokens")).toBeInTheDocument();
});

test("renders Agent action cards returned by the tutor", async () => {
  const user = userEvent.setup();
  mockedSendTutorMessage.mockResolvedValueOnce({
    actions: [
      {
        label: "代码作业已准备",
        payload: { title: "实现线性回归训练循环" },
        type: "assignment_ready",
      },
    ],
    course_id: "course-1",
    provider: "fake",
    reply: "我给你准备了一个代码练习。",
    session_id: "session-1",
    usage: {
      completion_tokens: 8,
      model: "fake",
      prompt_tokens: 12,
      provider: "fake",
      source: "estimated",
      total_tokens: 20,
    },
  });

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "给我一个代码练习");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("代码作业已准备")).toBeInTheDocument();
  expect(screen.getByText("实现线性回归训练循环")).toBeInTheDocument();
});

test("automatically opens the IDE when an assignment action arrives", async () => {
  const user = userEvent.setup();
  mockedSendTutorMessage.mockResolvedValueOnce({
    actions: [
      {
        label: "代码作业已准备",
        payload: {
          assignment_id: "assignment-1",
          prompt: "实现一个最小 autograd 示例",
          title: "实现线性回归训练循环",
        },
        type: "assignment_ready",
      },
    ],
    course_id: "course-1",
    provider: "fake",
    reply:
      "知识点：先理解计算图和梯度传播。\n\n下一步：任务会在右侧工作区打开。",
    session_id: "session-1",
    usage: {
      completion_tokens: 18,
      model: "fake",
      prompt_tokens: 12,
      provider: "fake",
      source: "estimated",
      total_tokens: 30,
    },
  });

  const { container } = render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "给我代码题");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText(/知识点：先理解计算图和梯度传播/)).toBeInTheDocument();
  expect(container.querySelector(".chat-workspace")).toHaveClass("chat-workspace--coding");
  expect(screen.getByLabelText("在线 IDE / 调试工作区")).toBeInTheDocument();
  expect(screen.getByText("任务已在右侧打开")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "打开在线 IDE" })).not.toBeInTheDocument();
});

test("opens the IDE panel from an assignment action and submits for Agent review", async () => {
  const user = userEvent.setup();
  mockedSendTutorMessage.mockResolvedValueOnce({
    actions: [
      {
        label: "代码作业已准备",
        payload: {
          assignment_id: "assignment-1",
          prompt: "实现一个最小 autograd 示例",
          title: "实现线性回归训练循环",
        },
        type: "assignment_ready",
      },
    ],
    course_id: "course-1",
    provider: "fake",
    reply: "打开右侧 IDE 完成这道题。",
    session_id: "session-1",
    usage: {
      completion_tokens: 8,
      model: "fake",
      prompt_tokens: 12,
      provider: "fake",
      source: "estimated",
      total_tokens: 20,
    },
  });

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "给我代码题");
  await user.click(screen.getByRole("button", { name: "发送" }));
  await screen.findByLabelText("在线 IDE / 调试工作区");
  await user.type(screen.getByLabelText("代码编辑器"), "loss.backward()");
  await user.click(screen.getByRole("button", { name: "提交给 Agent 审阅" }));

  await waitFor(() =>
    expect(mockedSubmitAssignment).toHaveBeenCalledWith(
      "assignment-1",
      expect.stringContaining("loss.backward()"),
    ),
  );
  expect(await screen.findByText("Agent 审阅完成")).toBeInTheDocument();
  expect(screen.getByText("代码覆盖了 requires_grad 与 backward。")).toBeInTheDocument();
});

test("runs assignment code through the runtime API and shows status logs", async () => {
  const user = userEvent.setup();
  mockedSendTutorMessage.mockResolvedValueOnce({
    actions: [
      {
        label: "代码作业已准备",
        payload: {
          assignment_id: "assignment-1",
          prompt: "实现一个最小 autograd 示例",
          title: "实现线性回归训练循环",
        },
        type: "assignment_ready",
      },
    ],
    course_id: "course-1",
    provider: "fake",
    reply: "打开右侧 IDE 完成这道题。",
    session_id: "session-1",
    usage: {
      completion_tokens: 8,
      model: "fake",
      prompt_tokens: 12,
      provider: "fake",
      source: "estimated",
      total_tokens: 20,
    },
  });

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "给我代码题");
  await user.click(screen.getByRole("button", { name: "发送" }));
  await screen.findByLabelText("在线 IDE / 调试工作区");
  expect(screen.getByLabelText("文件名")).toHaveValue("solution.py");
  expect(screen.getByLabelText("语言")).toHaveTextContent("Python");

  await user.type(screen.getByLabelText("代码编辑器"), "print('hello runtime')");
  await user.click(screen.getByRole("button", { name: "运行代码" }));

  await waitFor(() =>
    expect(mockedRunAssignment).toHaveBeenCalledWith("assignment-1", {
      code: expect.stringContaining("print('hello runtime')"),
      session_id: "session-1",
    }),
  );
  expect(await screen.findByText("运行结果")).toBeInTheDocument();
  expect(screen.getByText("run-1")).toBeInTheDocument();
  expect(screen.getByText("sandbox")).toBeInTheDocument();
  expect(screen.getByText("completed")).toBeInTheDocument();
  expect(screen.getByText("Code preview: print('hello runtime')")).toBeInTheDocument();
});

test("shows prepared Kubernetes runtime status without pretending execution happened", async () => {
  const user = userEvent.setup();
  mockedRunAssignment.mockResolvedValueOnce({
    artifacts: [],
    assignment_id: "assignment-1",
    backend: "kubernetes",
    course_id: "course-1",
    id: "run-k8s-1",
    logs: [
      "Kubernetes run prepared in namespace ai-dream-runs.",
      "No Job was created by this local preview runner.",
    ],
    metadata: { execution: "prepared_only", namespace: "ai-dream-runs" },
    status: "queued",
  });
  mockedSendTutorMessage.mockResolvedValueOnce({
    actions: [
      {
        label: "代码作业已准备",
        payload: {
          assignment_id: "assignment-1",
          prompt: "实现一个最小 autograd 示例",
          title: "实现线性回归训练循环",
        },
        type: "assignment_ready",
      },
    ],
    course_id: "course-1",
    provider: "fake",
    reply: "打开右侧 IDE 完成这道题。",
    session_id: "session-1",
    usage: {
      completion_tokens: 8,
      model: "fake",
      prompt_tokens: 12,
      provider: "fake",
      source: "estimated",
      total_tokens: 20,
    },
  });

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "给我代码题");
  await user.click(screen.getByRole("button", { name: "发送" }));
  await screen.findByLabelText("在线 IDE / 调试工作区");
  await user.type(screen.getByLabelText("代码编辑器"), "print('queued only')");
  await user.click(screen.getByRole("button", { name: "运行代码" }));

  expect(await screen.findByText("已准备 K8s Job / 等待执行")).toBeInTheDocument();
  expect(screen.getByText("No Job was created by this local preview runner.")).toBeInTheDocument();
});

test("shows IDE submission failures as errors instead of completed reviews", async () => {
  const user = userEvent.setup();
  mockedSubmitAssignment.mockRejectedValueOnce(new Error("沙箱运行失败"));
  mockedSendTutorMessage.mockResolvedValueOnce({
    actions: [
      {
        label: "代码作业已准备",
        payload: {
          assignment_id: "assignment-1",
          prompt: "实现一个最小 autograd 示例",
          title: "实现线性回归训练循环",
        },
        type: "assignment_ready",
      },
    ],
    course_id: "course-1",
    provider: "fake",
    reply: "打开右侧 IDE 完成这道题。",
    session_id: "session-1",
    usage: {
      completion_tokens: 8,
      model: "fake",
      prompt_tokens: 12,
      provider: "fake",
      source: "estimated",
      total_tokens: 20,
    },
  });

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "给我代码题");
  await user.click(screen.getByRole("button", { name: "发送" }));
  await screen.findByLabelText("在线 IDE / 调试工作区");
  await user.type(screen.getByLabelText("代码编辑器"), "raise RuntimeError()");
  await user.click(screen.getByRole("button", { name: "提交给 Agent 审阅" }));

  expect(await screen.findByText("提交失败")).toBeInTheDocument();
  expect(screen.getByText("沙箱运行失败")).toBeInTheDocument();
  expect(screen.queryByText("Agent 审阅完成")).not.toBeInTheDocument();
});

test("persists chat history across remounts", async () => {
  const user = userEvent.setup();
  const { unmount } = render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "我想复习 autograd");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();

  unmount();
  render(<ChatPage />);

  expect(screen.getByText("我想复习 autograd")).toBeInTheDocument();
  expect(screen.getByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();
});

test("clears persisted history and restores the initial greeting", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "清空前的问题");
  await user.click(screen.getByRole("button", { name: "发送" }));
  expect(await screen.findByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "清空对话" }));

  expect(screen.queryByText("清空前的问题")).not.toBeInTheDocument();
  expect(screen.getByText(initialGreeting)).toBeInTheDocument();
  expect(window.localStorage.getItem("ai-dream:tutor-chat-history")).toBeNull();
});

test("pressing Enter sends the current message", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "用回车发送{Enter}");

  await waitFor(() =>
    expect(mockedSendTutorMessage).toHaveBeenCalledWith({
      course_id: "course-1",
      history: [expect.objectContaining({ content: initialGreeting, role: "assistant" })],
      message: "用回车发送",
      session_id: "session-1",
    }),
  );
});

test("shows an animated thinking indicator while waiting for the tutor", async () => {
  const user = userEvent.setup();
  let resolveReply: (() => void) | undefined;
  mockedSendTutorMessage.mockReturnValue(
    new Promise((resolve) => {
      resolveReply = () =>
        resolve({
          actions: [],
          course_id: null,
          session_id: null,
          provider: "fake",
          reply: "这一步可以从损失函数开始。",
          usage: {
            completion_tokens: 10,
            model: "fake",
            prompt_tokens: 20,
            provider: "fake",
            source: "estimated",
            total_tokens: 30,
          },
        });
    }),
  );

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "讲讲损失函数");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByLabelText("AI 导师正在思考")).toBeInTheDocument();
  expect(screen.getByText("正在组织回答")).toBeInTheDocument();

  resolveReply?.();
  expect(await screen.findByText("这一步可以从损失函数开始。")).toBeInTheDocument();
});

test("opens history drawer and restores an earlier conversation", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "第一段历史问题");
  await user.click(screen.getByRole("button", { name: "发送" }));
  expect(await screen.findByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "新对话" }));
  await user.type(screen.getByLabelText("输入给导师的消息"), "第二段问题");

  expect(screen.queryByText("第一段历史问题")).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "历史记录" }));
  expect(await screen.findByRole("dialog", { name: "历史记录" })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: /第一段历史问题/ }));

  expect(screen.getAllByText("第一段历史问题").length).toBeGreaterThan(0);
  expect(screen.queryByText("第二段问题")).not.toBeInTheDocument();
});

test("appends delayed tutor replies to the session that sent the message", async () => {
  const user = userEvent.setup();
  let resolveReply: (() => void) | undefined;
  mockedSendTutorMessage.mockReturnValue(
    new Promise((resolve) => {
      resolveReply = () =>
        resolve({
          actions: [],
          course_id: null,
          session_id: null,
          provider: "fake",
          reply: "这是第一段对话的延迟回复。",
          usage: {
            completion_tokens: 10,
            model: "fake",
            prompt_tokens: 20,
            provider: "fake",
            source: "estimated",
            total_tokens: 30,
          },
        });
    }),
  );

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "第一段延迟问题");
  await user.click(screen.getByRole("button", { name: "发送" }));
  await user.click(screen.getByRole("button", { name: "新对话" }));

  resolveReply?.();
  await waitFor(() => expect(mockedSendTutorMessage).toHaveBeenCalledTimes(1));

  expect(screen.queryByText("这是第一段对话的延迟回复。")).not.toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "历史记录" }));
  await user.click(screen.getByRole("button", { name: /第一段延迟问题/ }));

  expect(await screen.findByText("这是第一段对话的延迟回复。")).toBeInTheDocument();
});

test("uses the active backend course instead of auto-starting intake after replies", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await screen.findByText(/线性回归课程/);
  await user.type(screen.getByLabelText("输入给导师的消息"), "我想学习线性回归");
  await user.click(screen.getByRole("button", { name: "发送" }));

  await screen.findByText("可以先从监督学习的训练流程开始。");
  expect(mockedStartIntake).not.toHaveBeenCalled();
});

test("creates a backend course and session when no course exists", async () => {
  const user = userEvent.setup();
  mockedListCourses.mockResolvedValueOnce([]);
  mockedCreateCourse.mockResolvedValueOnce({
    goal: "自由探索 AI 课程",
    id: "course-new",
    lessons: [],
    status: "active",
    title: "自由探索课程",
  });
  mockedCreateAgentSession.mockResolvedValueOnce({
    course_id: "course-new",
    id: "session-new",
    messages: [],
    status: "active",
    title: "新的 Agent 会话",
    token_usage: { total_tokens: 0 },
  });

  render(<ChatPage />);

  await screen.findByText(/自由探索课程/);
  await user.type(screen.getByLabelText("输入给导师的消息"), "第一段计划问题");
  await user.click(screen.getByRole("button", { name: "发送" }));

  await waitFor(() =>
    expect(mockedSendTutorMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        course_id: "course-new",
        session_id: "session-new",
      }),
    ),
  );
});

test("keeps chat usable when backend course bootstrap fails", async () => {
  const user = userEvent.setup();
  mockedListCourses.mockRejectedValueOnce(new Error("课程服务不可用"));

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "我想系统学习 PyTorch");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("可以先从监督学习的训练流程开始。")).toBeInTheDocument();
  expect(screen.getByText("我想系统学习 PyTorch")).toBeInTheDocument();
});

test("API failure shows visible error and preserves conversation", async () => {
  const user = userEvent.setup();
  mockedSendTutorMessage.mockRejectedValue(new Error("导师暂时不可用"));

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "请解释梯度下降");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("导师暂时不可用")).toBeInTheDocument();
  expect(screen.getByText(initialGreeting)).toBeInTheDocument();
  expect(screen.getByText("请解释梯度下降")).toBeInTheDocument();
});
