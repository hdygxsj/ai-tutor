import { useEffect, useMemo, useState } from "react";

import type {
  LearningPlanSummary,
  TutorChatMessage,
  TutorProvider,
} from "../../../types/learning";

const CHAT_SESSIONS_STORAGE_KEY = "ai-dream:tutor-chat-sessions";
const LEGACY_CHAT_HISTORY_STORAGE_KEY = "ai-dream:tutor-chat-history";

export const INITIAL_GREETING =
  "你好，我是 AI Dream 导师。你可以告诉我今天想学习什么，我会用当前 Settings 中配置的导师 provider 帮你拆解下一步。";

export function createTutorMessage(
  message: Omit<TutorChatMessage, "createdAt"> & { createdAt?: string },
): TutorChatMessage {
  return {
    ...message,
    createdAt: message.createdAt ?? new Date().toISOString(),
  };
}

function createInitialMessages(): TutorChatMessage[] {
  return [createTutorMessage({ content: INITIAL_GREETING, role: "assistant" })];
}

export interface ChatSession {
  createdPlan?: LearningPlanSummary;
  id: string;
  planError?: string;
  title: string;
  messages: TutorChatMessage[];
  lastProvider?: TutorProvider;
  updatedAt: number;
}

interface StoredChatState {
  currentSessionId: string;
  sessions: ChatSession[];
}

export function useChatSessions() {
  const [chatState, setChatState] = useState<StoredChatState>(loadStoredChatState);
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
  const sessionTokenTotal = useMemo(
    () =>
      messages.reduce(
        (total, message) => total + (message.usage?.total_tokens ?? 0),
        0,
      ),
    [messages],
  );

  useEffect(() => {
    window.localStorage.setItem(CHAT_SESSIONS_STORAGE_KEY, JSON.stringify(chatState));
    window.localStorage.removeItem(LEGACY_CHAT_HISTORY_STORAGE_KEY);
  }, [chatState]);

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

  function clearCurrentSession() {
    updateSessionById(currentSession.id, (session) => ({
      ...session,
      createdPlan: undefined,
      lastProvider: undefined,
      messages: createInitialMessages(),
      planError: undefined,
      title: "新对话",
    }));
    window.localStorage.removeItem(LEGACY_CHAT_HISTORY_STORAGE_KEY);
  }

  function createNewConversation() {
    const session = createChatSession();

    setChatState((current) => ({
      currentSessionId: session.id,
      sessions: [session, ...current.sessions],
    }));
  }

  function selectSession(sessionId: string) {
    setChatState((current) => ({
      ...current,
      currentSessionId: sessionId,
    }));
  }

  return {
    chatState,
    clearCurrentSession,
    createNewConversation,
    currentSession,
    hasConversation,
    messages,
    selectSession,
    sessionTokenTotal,
    updateSessionById,
  };
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

    const sessions = parsed.sessions.filter(isStoredChatSession).map((session) => ({
      ...session,
      messages: normalizeMessages(session.messages),
    }));
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

    return parsed.length > 0 ? normalizeMessages(parsed) : null;
  } catch {
    return null;
  }
}

function createChatSession(messages?: TutorChatMessage[]): ChatSession {
  const normalizedMessages = normalizeMessages(messages ?? createInitialMessages());

  return {
    createdPlan: undefined,
    id: createSessionId(),
    messages: normalizedMessages,
    planError: undefined,
    title: deriveSessionTitle(normalizedMessages),
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
    (maybeSession.createdPlan === undefined || isStoredLearningPlan(maybeSession.createdPlan)) &&
    (maybeSession.planError === undefined || typeof maybeSession.planError === "string") &&
    typeof maybeSession.title === "string" &&
    typeof maybeSession.updatedAt === "number"
  );
}

function normalizeMessages(messages: TutorChatMessage[]): TutorChatMessage[] {
  return messages.map((message) => createTutorMessage(message));
}

function isStoredLearningPlan(value: unknown): value is LearningPlanSummary {
  if (!value || typeof value !== "object") {
    return false;
  }

  const maybePlan = value as Partial<LearningPlanSummary>;
  return (
    typeof maybePlan.id === "string" &&
    typeof maybePlan.title === "string" &&
    typeof maybePlan.goal === "string" &&
    typeof maybePlan.status === "string" &&
    Array.isArray(maybePlan.lessons)
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
