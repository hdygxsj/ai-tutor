import { useEffect, useRef, useState } from "react";

import { sendTutorMessage, startIntake } from "../api/client";
import type { TutorChatMessage } from "../types/learning";
import { ChatWorkspace } from "./chat/components/ChatWorkspace";
import { HistoryDrawer } from "./chat/components/HistoryDrawer";
import { useAssignmentIde } from "./chat/hooks/use-assignment-ide";
import { useCourseSession } from "./chat/hooks/use-course-session";
import {
  INITIAL_GREETING,
  createTutorMessage,
  useChatSessions,
} from "./chat/hooks/use-chat-sessions";
import "./ChatPage.css";

export function ChatPage() {
  const {
    chatState,
    clearCurrentSession,
    createNewConversation,
    currentSession,
    hasConversation,
    messages,
    selectSession,
    sessionTokenTotal,
    updateSessionById,
  } = useChatSessions();
  const { adoptServerCourseSession, currentAgentSession, currentCourse } =
    useCourseSession();
  const assignmentIde = useAssignmentIde();
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [creatingPlanSessionId, setCreatingPlanSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const isCreatingPlan = creatingPlanSessionId === currentSession.id;

  useEffect(() => {
    const bottom = bottomRef.current;
    const stream = bottom?.closest<HTMLElement>(".chat-stream");

    if (!stream) {
      return;
    }

    if (typeof stream.scrollTo === "function") {
      stream.scrollTo({
        top: stream.scrollHeight,
        behavior: "smooth",
      });
      return;
    }

    stream.scrollTop = stream.scrollHeight;
  }, [messages, isSending]);

  async function handleSend() {
    const content = input.trim();

    if (!content || isSending || isCreatingPlan) {
      return;
    }

    const history = messages;
    const sendingSessionId = currentSession.id;
    const userMessage = createTutorMessage({ content, role: "user" });

    updateSessionById(sendingSessionId, (session) => ({
      ...session,
      messages: [...session.messages, userMessage],
    }));
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const response = await sendTutorMessage({
        course_id: currentCourse?.id,
        history,
        message: content,
        session_id: currentAgentSession?.id,
      });
      const assistantMessage = createTutorMessage({
        actions: response.actions,
        content: response.reply,
        role: "assistant",
        usage: response.usage,
      });
      const assignmentAction = response.actions.find(
        (action) =>
          action.type === "assignment_ready" &&
          typeof action.payload.assignment_id === "string",
      );
      if (assignmentAction) {
        assignmentIde.openIdeFromAction(assignmentAction);
      }
      updateSessionById(sendingSessionId, (session) => ({
        ...session,
        lastProvider: response.provider,
        messages: [...session.messages, assistantMessage],
      }));
      await adoptServerCourseSession(response.course_id, response.session_id);
      setIsSending(false);
      if (!currentCourse && !response.course_id) {
        await createPlanForConversation({
          goal: content,
          messages: [...history, userMessage, assistantMessage],
          sessionId: sendingSessionId,
        });
      }
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
    clearCurrentSession();
    setInput("");
    setError(null);
  }

  function createNewChat() {
    createNewConversation();
    setInput("");
    setError(null);
  }

  function selectChatSession(sessionId: string) {
    selectSession(sessionId);
    setInput("");
    setError(null);
    setHistoryOpen(false);
  }

  async function createPlanForConversation({
    goal,
    messages: planMessages,
    sessionId,
  }: {
    goal: string;
    messages: TutorChatMessage[];
    sessionId: string;
  }) {
    setCreatingPlanSessionId(sessionId);
    updateSessionById(sessionId, (session) => ({
      ...session,
      createdPlan: undefined,
      planError: undefined,
    }));

    try {
      const plan = await startIntake({
        background: buildConversationBackground(planMessages, goal),
        goal,
        weekly_hours: 6,
      });
      updateSessionById(sessionId, (session) => ({
        ...session,
        createdPlan: plan,
        planError: undefined,
      }));
    } catch (caughtError) {
      updateSessionById(sessionId, (session) => ({
        ...session,
        createdPlan: undefined,
        planError:
          caughtError instanceof Error
            ? caughtError.message
            : "创建学习计划失败，请稍后重试。",
      }));
    } finally {
      setCreatingPlanSessionId((currentSessionId) =>
        currentSessionId === sessionId ? null : currentSessionId,
      );
    }
  }

  return (
    <div className="chat-page">
      <ChatWorkspace
        activeIdeAssignment={assignmentIde.activeIdeAssignment}
        bottomRef={bottomRef}
        codeDraft={assignmentIde.codeDraft}
        createdPlan={currentSession.createdPlan}
        currentCourse={currentCourse}
        error={error}
        fileName={assignmentIde.fileName}
        hasConversation={hasConversation}
        input={input}
        isCodingMode={assignmentIde.isCodingMode}
        isCreatingPlan={isCreatingPlan}
        isRunningAssignment={assignmentIde.isRunningAssignment}
        isSending={isSending}
        isSubmittingAssignment={assignmentIde.isSubmittingAssignment}
        language={assignmentIde.language}
        lastProvider={currentSession.lastProvider}
        messages={messages}
        onChangeCodeDraft={assignmentIde.setCodeDraft}
        onChangeFileName={assignmentIde.setFileName}
        onChangeInput={setInput}
        onChangeLanguage={assignmentIde.setLanguage}
        onClearHistory={clearHistory}
        onCloseIdePanel={assignmentIde.closeIdePanel}
        onCreateConversation={createNewChat}
        onOpenHistory={() => setHistoryOpen(true)}
        onOpenIde={assignmentIde.openIdeFromAction}
        onRunAssignment={() =>
          void assignmentIde.runCurrentAssignment(currentAgentSession?.id)
        }
        onSend={() => void handleSend()}
        onSubmitAssignment={() => void assignmentIde.submitCurrentAssignment()}
        onToggleDebugLayout={assignmentIde.toggleDebugLayout}
        planError={currentSession.planError}
        reviewError={assignmentIde.reviewError}
        reviewFeedback={assignmentIde.reviewFeedback}
        runError={assignmentIde.runError}
        runResult={assignmentIde.runResult}
        sessionTokenTotal={sessionTokenTotal}
      />

      <HistoryDrawer
        currentSessionId={currentSession.id}
        onClose={() => setHistoryOpen(false)}
        onSelect={selectChatSession}
        open={historyOpen}
        sessions={chatState.sessions}
      />
    </div>
  );
}

function buildConversationBackground(
  messages: TutorChatMessage[],
  pendingGoal: string,
): string {
  const recentMessages = messages
    .filter((message) => message.content !== INITIAL_GREETING)
    .slice(-6)
    .map((message) => `${message.role === "user" ? "学习者" : "导师"}：${message.content}`);

  if (!recentMessages.some((message) => message.includes(pendingGoal))) {
    recentMessages.push(`学习者：${pendingGoal}`);
  }

  return recentMessages.join("\n");
}
