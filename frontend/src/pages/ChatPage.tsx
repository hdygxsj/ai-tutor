import {
  DeleteOutlined,
  HistoryOutlined,
  PlusOutlined,
  RobotOutlined,
  SendOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  Alert,
  Avatar,
  Button,
  Card,
  Drawer,
  Empty,
  Input,
  List,
  Space,
  Tag,
  Typography,
} from "antd";

import { sendTutorMessage } from "../api/client";
import type { TutorChatMessage, TutorProvider } from "../types/learning";
import "./ChatPage.css";

const { TextArea } = Input;
const CHAT_SESSIONS_STORAGE_KEY = "ai-dream:tutor-chat-sessions";
const LEGACY_CHAT_HISTORY_STORAGE_KEY = "ai-dream:tutor-chat-history";

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

interface ChatSession {
  id: string;
  title: string;
  messages: TutorChatMessage[];
  lastProvider?: TutorProvider;
  updatedAt: number;
}

interface StoredChatState {
  currentSessionId: string;
  sessions: ChatSession[];
}

export function ChatPage() {
  const [chatState, setChatState] = useState<StoredChatState>(loadStoredChatState);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const currentSession = useMemo(
    () =>
      chatState.sessions.find((session) => session.id === chatState.currentSessionId) ??
      chatState.sessions[0],
    [chatState],
  );
  const messages = currentSession.messages;
  const hasConversation = useMemo(
    () => messages.some((message) => message.content !== INITIAL_GREETING),
    [messages],
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, isSending]);

  useEffect(() => {
    window.localStorage.setItem(CHAT_SESSIONS_STORAGE_KEY, JSON.stringify(chatState));
    window.localStorage.removeItem(LEGACY_CHAT_HISTORY_STORAGE_KEY);
  }, [chatState]);

  async function handleSend() {
    const content = input.trim();

    if (!content || isSending) {
      return;
    }

    const history = messages;
    const sendingSessionId = currentSession.id;
    const userMessage: TutorChatMessage = { content, role: "user" };

    updateSessionById(sendingSessionId, (session) => ({
      ...session,
      messages: [...session.messages, userMessage],
    }));
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const response = await sendTutorMessage({ history, message: content });
      updateSessionById(sendingSessionId, (session) => ({
        ...session,
        lastProvider: response.provider,
        messages: [
          ...session.messages,
          { content: response.reply, role: "assistant" },
        ],
      }));
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
    updateSessionById(currentSession.id, (session) => ({
      ...session,
      lastProvider: undefined,
      messages: [...INITIAL_MESSAGES],
      title: "新对话",
    }));
    setInput("");
    setError(null);
    window.localStorage.removeItem(LEGACY_CHAT_HISTORY_STORAGE_KEY);
  }

  function createNewConversation() {
    const session = createChatSession();

    setChatState((current) => ({
      currentSessionId: session.id,
      sessions: [session, ...current.sessions],
    }));
    setInput("");
    setError(null);
  }

  function selectSession(sessionId: string) {
    setChatState((current) => ({
      ...current,
      currentSessionId: sessionId,
    }));
    setInput("");
    setError(null);
    setHistoryOpen(false);
  }

  function updateSessionById(
    sessionId: string,
    updater: (session: ChatSession) => ChatSession,
  ) {
    setChatState((current) => {
      const sessions = current.sessions.map((session) => {
        if (session.id !== sessionId) {
          return session;
        }

        const nextSession = updater(session);
        return {
          ...nextSession,
          title: deriveSessionTitle(nextSession.messages),
          updatedAt: Date.now(),
        };
      });

      return { ...current, sessions };
    });
  }

  return (
    <Space className="chat-page" direction="vertical" size={24}>
      <Card className="chat-hero" variant="borderless">
        <div className="chat-hero__content">
          <Typography.Text className="chat-hero__eyebrow">
            AI 导师
          </Typography.Text>
          <Typography.Title className="chat-hero__title" level={1}>
            引导式学习对话
          </Typography.Title>
          <Typography.Paragraph className="chat-hero__description">
            M2.1 使用 Settings 里的导师 provider，学习计划/评分仍保持确定性。
            对话历史会保存在本机浏览器，刷新页面后仍可继续。
          </Typography.Paragraph>
        </div>
        <Space wrap>
          <Button
            aria-label="历史记录"
            className="chat-hero__button"
            icon={<HistoryOutlined />}
            onClick={() => setHistoryOpen(true)}
          >
            历史记录
          </Button>
          <Button
            aria-label="新对话"
            className="chat-hero__button"
            icon={<PlusOutlined />}
            onClick={createNewConversation}
          >
            新对话
          </Button>
        </Space>
      </Card>

      <Card
        className="chat-shell"
        styles={{ body: { padding: 0 } }}
        variant="borderless"
      >
        <div className="chat-toolbar">
          <Space>
            <Avatar
              icon={<RobotOutlined />}
              className="chat-toolbar__avatar"
            />
            <div>
              <Typography.Text strong>AI Dream 导师</Typography.Text>
              <br />
              <Typography.Text type="secondary">
                {currentSession.lastProvider
                  ? `最近回复：${providerLabels[currentSession.lastProvider]}`
                  : "等待你的问题"}
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
            清空当前对话
          </Button>
        </div>

        <div
          aria-label="导师对话历史"
          className="chat-stream"
        >
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            {messages.map((message, index) => (
              <ChatBubble
                key={`${message.role}-${index}-${message.content}`}
                message={message}
              />
            ))}

            {isSending ? <TypingIndicator /> : null}
            <div ref={bottomRef} />
          </Space>
        </div>

        <div className="chat-composer-panel">
          {error ? (
            <Alert
              message={error}
              showIcon
              style={{ marginBottom: 12 }}
              type="error"
            />
          ) : null}

          <div className="chat-composer">
            <TextArea
              aria-label="输入给导师的消息"
              autoSize={{ maxRows: 5, minRows: 1 }}
              className="chat-composer__input"
              disabled={isSending}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void handleSend();
                }
              }}
              placeholder="输入问题，Enter 发送，Shift + Enter 换行"
              value={input}
            />
            <Button
              aria-label="发送"
              className="chat-composer__send"
              disabled={isSending || input.trim().length === 0}
              icon={<SendOutlined />}
              loading={isSending}
              onClick={() => void handleSend()}
              type="primary"
            />
          </div>
        </div>
      </Card>

      <HistoryDrawer
        currentSessionId={currentSession.id}
        onClose={() => setHistoryOpen(false)}
        onSelect={selectSession}
        open={historyOpen}
        sessions={chatState.sessions}
      />
    </Space>
  );
}

function ChatBubble({ message }: { message: TutorChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`chat-message ${isUser ? "chat-message--user" : ""}`}>
      {!isUser ? (
        <Avatar
          icon={<RobotOutlined />}
          className="chat-message__avatar chat-message__avatar--assistant"
        />
      ) : null}
      <div className={`chat-bubble ${isUser ? "chat-bubble--user" : ""}`}>
        <Typography.Text className="chat-bubble__speaker" strong>
          {isUser ? "你" : "AI 导师"}
        </Typography.Text>
        <Typography.Paragraph className="chat-bubble__content">
          {message.content}
        </Typography.Paragraph>
      </div>
      {isUser ? (
        <Avatar
          icon={<UserOutlined />}
          className="chat-message__avatar chat-message__avatar--user"
        />
      ) : null}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div aria-label="AI 导师正在思考" className="chat-message">
      <Avatar
        icon={<RobotOutlined />}
        className="chat-message__avatar chat-message__avatar--assistant"
      />
      <div className="chat-bubble chat-bubble--typing">
        <span>正在组织回答</span>
        <span className="typing-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </div>
    </div>
  );
}

function HistoryDrawer({
  currentSessionId,
  onClose,
  onSelect,
  open,
  sessions,
}: {
  currentSessionId: string;
  onClose: () => void;
  onSelect: (sessionId: string) => void;
  open: boolean;
  sessions: ChatSession[];
}) {
  const sortedSessions = [...sessions].sort((left, right) => right.updatedAt - left.updatedAt);

  return (
    <Drawer
      getContainer={false}
      onClose={onClose}
      open={open}
      title="历史记录"
      width={380}
    >
      {sortedSessions.length === 0 ? (
        <Empty description="还没有对话历史" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={sortedSessions}
          renderItem={(session) => (
            <List.Item>
              <Button
                block
                className="chat-history-item"
                onClick={() => onSelect(session.id)}
                type={session.id === currentSessionId ? "primary" : "default"}
              >
                <span className="chat-history-item__title">{session.title}</span>
                <span className="chat-history-item__meta">
                  {new Date(session.updatedAt).toLocaleString()}
                </span>
              </Button>
            </List.Item>
          )}
        />
      )}
    </Drawer>
  );
}

function loadStoredChatState(): StoredChatState {
  const storedSessions = window.localStorage.getItem(CHAT_SESSIONS_STORAGE_KEY);
  const parsedSessions = parseStoredChatState(storedSessions);

  if (parsedSessions) {
    return parsedSessions;
  }

  const legacyMessages = parseStoredMessages(
    window.localStorage.getItem(LEGACY_CHAT_HISTORY_STORAGE_KEY),
  );
  if (legacyMessages) {
    const session = createChatSession(legacyMessages);
    return { currentSessionId: session.id, sessions: [session] };
  }

  const session = createChatSession();
  return { currentSessionId: session.id, sessions: [session] };
}

function parseStoredChatState(stored: string | null): StoredChatState | null {
  if (!stored) {
    return null;
  }

  try {
    const parsed = JSON.parse(stored) as Partial<StoredChatState>;

    if (!Array.isArray(parsed.sessions) || typeof parsed.currentSessionId !== "string") {
      return null;
    }

    const sessions = parsed.sessions.filter(isStoredChatSession);
    if (sessions.length === 0) {
      return null;
    }

    const currentSessionId = sessions.some(
      (session) => session.id === parsed.currentSessionId,
    )
      ? parsed.currentSessionId
      : sessions[0].id;

    return { currentSessionId, sessions };
  } catch {
    return null;
  }
}

function parseStoredMessages(stored: string | null): TutorChatMessage[] | null {
  if (!stored) {
    return null;
  }

  try {
    const parsed = JSON.parse(stored) as unknown;

    if (!Array.isArray(parsed) || !parsed.every(isStoredChatMessage)) {
      return null;
    }

    return parsed.length > 0 ? parsed : null;
  } catch {
    return null;
  }
}

function createChatSession(messages: TutorChatMessage[] = INITIAL_MESSAGES): ChatSession {
  return {
    id: createSessionId(),
    messages: [...messages],
    title: deriveSessionTitle(messages),
    updatedAt: Date.now(),
  };
}

function createSessionId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `session-${Date.now()}`;
}

function deriveSessionTitle(messages: TutorChatMessage[]): string {
  const firstUserMessage = messages.find((message) => message.role === "user");

  if (!firstUserMessage) {
    return "新对话";
  }

  return firstUserMessage.content.length > 24
    ? `${firstUserMessage.content.slice(0, 24)}...`
    : firstUserMessage.content;
}

function isStoredChatSession(value: unknown): value is ChatSession {
  if (!value || typeof value !== "object") {
    return false;
  }

  const maybeSession = value as Partial<ChatSession>;
  return (
    typeof maybeSession.id === "string" &&
    Array.isArray(maybeSession.messages) &&
    maybeSession.messages.every(isStoredChatMessage) &&
    typeof maybeSession.title === "string" &&
    typeof maybeSession.updatedAt === "number"
  );
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
