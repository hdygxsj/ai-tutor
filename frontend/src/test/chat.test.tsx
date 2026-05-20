import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, beforeEach, expect, test, vi } from "vitest";

import { sendTutorMessage } from "../api/client";
import { ChatPage } from "../pages/ChatPage";

vi.mock("../api/client", () => ({
  sendTutorMessage: vi.fn(),
}));

const mockedSendTutorMessage = vi.mocked(sendTutorMessage);
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
  mockedSendTutorMessage.mockResolvedValue({
    provider: "fake",
    reply: "可以先从监督学习的训练流程开始。",
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

test("sending a message calls sendTutorMessage with message and history", async () => {
  const user = userEvent.setup();

  render(<ChatPage />);

  await user.type(screen.getByLabelText("输入给导师的消息"), "我想学习线性回归");
  await user.click(screen.getByRole("button", { name: "发送" }));

  await waitFor(() =>
    expect(mockedSendTutorMessage).toHaveBeenCalledWith({
      history: [{ content: initialGreeting, role: "assistant" }],
      message: "我想学习线性回归",
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
      history: [{ content: initialGreeting, role: "assistant" }],
      message: "用回车发送",
    }),
  );
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
