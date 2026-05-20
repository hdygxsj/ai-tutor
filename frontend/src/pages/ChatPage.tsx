import { useState } from "react";

import { Alert, Button, Card, Input, Space, Tag, Typography } from "antd";

import { sendTutorMessage } from "../api/client";
import type { TutorChatMessage, TutorProvider } from "../types/learning";

const { TextArea } = Input;

const INITIAL_GREETING =
  "你好，我是 AI Dream 导师。你可以告诉我今天想学习什么，我会用当前 Settings 中配置的导师 provider 帮你拆解下一步。";

const providerLabels: Record<TutorProvider, string> = {
  fake: "Fake",
  ollama: "Ollama",
  openai_compatible: "OpenAI-compatible",
};

export function ChatPage() {
  const [messages, setMessages] = useState<TutorChatMessage[]>([
    { content: INITIAL_GREETING, role: "assistant" },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastProvider, setLastProvider] = useState<TutorProvider | null>(null);

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

  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Text type="secondary">AI 导师</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          引导式学习对话
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          M2.1 使用 Settings 里的导师 provider，学习计划/评分仍保持确定性。
        </Typography.Paragraph>
      </div>

      <Card>
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          {error ? <Alert message={error} type="error" showIcon /> : null}

          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}-${message.content}`}
                style={{
                  display: "flex",
                  justifyContent:
                    message.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    background:
                      message.role === "user" ? "#e6f4ff" : "#f8fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: 12,
                    maxWidth: "78%",
                    padding: "12px 14px",
                  }}
                >
                  <Typography.Text
                    strong
                    style={{
                      color: message.role === "user" ? "#0958d9" : "#475569",
                      display: "block",
                      marginBottom: 4,
                    }}
                  >
                    {message.role === "user" ? "你" : "AI 导师"}
                  </Typography.Text>
                  <Typography.Paragraph style={{ marginBottom: 0 }}>
                    {message.content}
                  </Typography.Paragraph>
                </div>
              </div>
            ))}
          </Space>

          {lastProvider ? (
            <Typography.Text type="secondary">
              本次回复 provider：<Tag>{providerLabels[lastProvider]}</Tag>
            </Typography.Text>
          ) : null}

          <Space.Compact style={{ width: "100%" }}>
            <TextArea
              aria-label="输入给导师的消息"
              autoSize={{ maxRows: 5, minRows: 2 }}
              disabled={isSending}
              onChange={(event) => setInput(event.target.value)}
              placeholder="告诉导师你想理解的问题或下一步学习目标"
              value={input}
            />
            <Button
              aria-label="发送"
              disabled={isSending || input.trim().length === 0}
              loading={isSending}
              onClick={handleSend}
              type="primary"
            >
              发送
            </Button>
          </Space.Compact>
        </Space>
      </Card>
    </Space>
  );
}
