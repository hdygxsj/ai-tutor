import { DeleteOutlined, RobotOutlined, SendOutlined, UserOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useRef, useState } from "react";

import { Alert, Avatar, Button, Card, Input, Space, Tag, Typography } from "antd";

import { sendTutorMessage } from "../api/client";
import type { TutorChatMessage, TutorProvider } from "../types/learning";

const { TextArea } = Input;
const CHAT_HISTORY_STORAGE_KEY = "ai-dream:tutor-chat-history";

const INITIAL_GREETING =
  "你好，我是 AI Dream 导师。你可以告诉我今天想学习什么，我会用当前 Settings 中配置的导师 provider 帮你拆解下一步。";
const INITIAL_MESSAGES: TutorChatMessage[] = [
  { content: INITIAL_GREETING, role: "assistant" },
];

const providerLabels: Record<TutorProvider, string> = {
  fake: "Fake",
  ollama: "Ollama",
  openai_compatible: "OpenAI-compatible",
};

export function ChatPage() {
  const [messages, setMessages] = useState<TutorChatMessage[]>(loadStoredMessages);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastProvider, setLastProvider] = useState<TutorProvider | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const hasConversation = useMemo(
    () => messages.some((message) => message.content !== INITIAL_GREETING),
    [messages],
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, isSending]);

  useEffect(() => {
    if (!hasConversation) {
      window.localStorage.removeItem(CHAT_HISTORY_STORAGE_KEY);
      return;
    }

    window.localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(messages));
  }, [hasConversation, messages]);

  async function handleSend() {
    const content = input.trim();

    if (!content || isSending) {
      return;
    }

    const history = messages;
    const userMessage: TutorChatMessage = { content, role: "user" };

    setMessages([...messages, userMessage]);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const response = await sendTutorMessage({ history, message: content });
      setLastProvider(response.provider);
      setMessages((currentMessages) => [
        ...currentMessages,
        { content: response.reply, role: "assistant" },
      ]);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "导师回复失败，请稍后重试。",
      );
    } finally {
      setIsSending(false);
    }
  }

  function clearHistory() {
    setMessages(INITIAL_MESSAGES);
    setInput("");
    setError(null);
    setLastProvider(null);
    window.localStorage.removeItem(CHAT_HISTORY_STORAGE_KEY);
  }

  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <Card
        style={{
          background:
            "linear-gradient(135deg, #111827 0%, #1d4ed8 52%, #7c3aed 100%)",
          borderRadius: 28,
          boxShadow: "0 24px 60px rgba(15, 23, 42, 0.22)",
          overflow: "hidden",
        }}
        variant="borderless"
      >
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Typography.Text style={{ color: "rgba(255,255,255,0.72)" }}>
            AI 导师
          </Typography.Text>
          <Typography.Title level={1} style={{ color: "#fff", margin: 0 }}>
            引导式学习对话
          </Typography.Title>
          <Typography.Paragraph
            style={{ color: "rgba(255,255,255,0.78)", fontSize: 16, margin: 0 }}
          >
            M2.1 使用 Settings 里的导师 provider，学习计划/评分仍保持确定性。
            对话历史会保存在本机浏览器，刷新页面后仍可继续。
          </Typography.Paragraph>
        </Space>
      </Card>

      <Card
        style={{
          borderRadius: 28,
          boxShadow: "0 18px 50px rgba(15, 23, 42, 0.10)",
          overflow: "hidden",
        }}
        styles={{ body: { padding: 0 } }}
        variant="borderless"
      >
        <div
          style={{
            alignItems: "center",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            justifyContent: "space-between",
            padding: "18px 22px",
          }}
        >
          <Space>
            <Avatar
              icon={<RobotOutlined />}
              style={{
                background: "linear-gradient(135deg, #2563eb, #7c3aed)",
              }}
            />
            <div>
              <Typography.Text strong>AI Dream 导师</Typography.Text>
              <br />
              <Typography.Text type="secondary">
                {lastProvider ? `最近回复：${providerLabels[lastProvider]}` : "等待你的问题"}
              </Typography.Text>
            </div>
          </Space>
          <Button
            aria-label="清空对话"
            danger
            disabled={!hasConversation || isSending}
            icon={<DeleteOutlined />}
            onClick={clearHistory}
          >
            清空对话
          </Button>
        </div>

        <div
          aria-label="导师对话历史"
          style={{
            background:
              "radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 28%), #f8fafc",
            maxHeight: 560,
            minHeight: 430,
            overflowY: "auto",
            padding: 24,
          }}
        >
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            {messages.map((message, index) => (
              <ChatBubble
                key={`${message.role}-${index}-${message.content}`}
                message={message}
              />
            ))}

            {isSending ? (
              <ChatBubble
                message={{ content: "正在思考你的问题...", role: "assistant" }}
              />
            ) : null}
            <div ref={bottomRef} />
          </Space>
        </div>

        <div
          style={{
            background: "#fff",
            borderTop: "1px solid #e2e8f0",
            padding: 18,
          }}
        >
          {error ? (
            <Alert
              message={error}
              showIcon
              style={{ marginBottom: 12 }}
              type="error"
            />
          ) : null}

          <Space.Compact style={{ width: "100%" }}>
            <TextArea
              aria-label="输入给导师的消息"
              autoSize={{ maxRows: 6, minRows: 2 }}
              disabled={isSending}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void handleSend();
                }
              }}
              placeholder="输入问题。Enter 发送，Shift + Enter 换行。"
              style={{
                borderRadius: "16px 0 0 16px",
                padding: 14,
                resize: "none",
              }}
              value={input}
            />
            <Button
              aria-label="发送"
              disabled={isSending || input.trim().length === 0}
              icon={<SendOutlined />}
              loading={isSending}
              onClick={() => void handleSend()}
              style={{
                borderRadius: "0 16px 16px 0",
                minWidth: 108,
              }}
              type="primary"
            >
              发送
            </Button>
          </Space.Compact>
        </div>
      </Card>
    </Space>
  );
}

function ChatBubble({ message }: { message: TutorChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        justifyContent: isUser ? "flex-end" : "flex-start",
      }}
    >
      {!isUser ? (
        <Avatar
          icon={<RobotOutlined />}
          style={{ background: "#2563eb", flex: "0 0 auto" }}
        />
      ) : null}
      <div
        style={{
          background: isUser
            ? "linear-gradient(135deg, #2563eb, #1d4ed8)"
            : "#fff",
          border: isUser ? "none" : "1px solid #e2e8f0",
          borderRadius: isUser ? "18px 18px 6px 18px" : "18px 18px 18px 6px",
          boxShadow: isUser
            ? "0 12px 28px rgba(37, 99, 235, 0.24)"
            : "0 10px 30px rgba(15, 23, 42, 0.07)",
          color: isUser ? "#fff" : "#0f172a",
          maxWidth: "min(680px, 76%)",
          padding: "14px 16px",
          whiteSpace: "pre-wrap",
        }}
      >
        <Typography.Text
          strong
          style={{
            color: isUser ? "rgba(255,255,255,0.88)" : "#475569",
            display: "block",
            marginBottom: 6,
          }}
        >
          {isUser ? "你" : "AI 导师"}
        </Typography.Text>
        <Typography.Paragraph
          style={{ color: "inherit", margin: 0, whiteSpace: "pre-wrap" }}
        >
          {message.content}
        </Typography.Paragraph>
      </div>
      {isUser ? (
        <Avatar
          icon={<UserOutlined />}
          style={{ background: "#0f172a", flex: "0 0 auto" }}
        />
      ) : null}
    </div>
  );
}

function loadStoredMessages(): TutorChatMessage[] {
  const fallback = [...INITIAL_MESSAGES];
  const stored = window.localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);

  if (!stored) {
    return fallback;
  }

  try {
    const parsed = JSON.parse(stored) as unknown;

    if (!Array.isArray(parsed) || !parsed.every(isStoredChatMessage)) {
      return fallback;
    }

    return parsed.length > 0 ? parsed : fallback;
  } catch {
    return fallback;
  }
}

function isStoredChatMessage(value: unknown): value is TutorChatMessage {
  if (!value || typeof value !== "object") {
    return false;
  }

  const maybeMessage = value as Partial<TutorChatMessage>;
  return (
    (maybeMessage.role === "assistant" || maybeMessage.role === "user") &&
    typeof maybeMessage.content === "string" &&
    maybeMessage.content.trim().length > 0
  );
}
