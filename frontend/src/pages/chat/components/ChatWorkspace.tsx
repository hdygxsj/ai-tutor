import type { RefObject } from "react";

import type {
  CourseSummary,
  LearningPlanSummary,
  TutorChatMessage,
  TutorProvider,
} from "../../../types/learning";
import type { ActiveIdeAssignment } from "../hooks/use-assignment-ide";
import { AssignmentIdePanel } from "./AssignmentIdePanel";
import { ChatPanel } from "./ChatPanel";

interface ChatWorkspaceProps {
  activeIdeAssignment: ActiveIdeAssignment | null;
  bottomRef: RefObject<HTMLDivElement>;
  codeDraft: string;
  createdPlan?: LearningPlanSummary;
  currentCourse: CourseSummary | null;
  error: string | null;
  hasConversation: boolean;
  input: string;
  isCodingMode: boolean;
  isCreatingPlan: boolean;
  isSending: boolean;
  isSubmittingAssignment: boolean;
  lastProvider?: TutorProvider;
  messages: TutorChatMessage[];
  onChangeCodeDraft: (value: string) => void;
  onChangeInput: (value: string) => void;
  onClearHistory: () => void;
  onCloseIdePanel: () => void;
  onCreateConversation: () => void;
  onOpenHistory: () => void;
  onOpenIde: (action: NonNullable<TutorChatMessage["actions"]>[number]) => void;
  onSend: () => void;
  onSubmitAssignment: () => void;
  onToggleDebugLayout: () => void;
  planError?: string;
  reviewError: string | null;
  reviewFeedback: string | null;
  sessionTokenTotal: number;
}

export function ChatWorkspace({
  activeIdeAssignment,
  bottomRef,
  codeDraft,
  createdPlan,
  currentCourse,
  error,
  hasConversation,
  input,
  isCodingMode,
  isCreatingPlan,
  isSending,
  isSubmittingAssignment,
  lastProvider,
  messages,
  onChangeCodeDraft,
  onChangeInput,
  onClearHistory,
  onCloseIdePanel,
  onCreateConversation,
  onOpenHistory,
  onOpenIde,
  onSend,
  onSubmitAssignment,
  onToggleDebugLayout,
  planError,
  reviewError,
  reviewFeedback,
  sessionTokenTotal,
}: ChatWorkspaceProps) {
  return (
    <div className={`chat-workspace ${isCodingMode ? "chat-workspace--coding" : ""}`}>
      <ChatPanel
        bottomRef={bottomRef}
        codeLayoutActive={isCodingMode}
        currentCourse={currentCourse}
        createdPlan={createdPlan}
        error={error}
        hasConversation={hasConversation}
        input={input}
        isCreatingPlan={isCreatingPlan}
        isSending={isSending}
        lastProvider={lastProvider}
        messages={messages}
        onChangeInput={onChangeInput}
        onClearHistory={onClearHistory}
        onCreateConversation={onCreateConversation}
        onOpenHistory={onOpenHistory}
        onOpenIde={onOpenIde}
        onSend={onSend}
        onToggleDebugLayout={onToggleDebugLayout}
        planError={planError}
        sessionTokenTotal={sessionTokenTotal}
      />
      {isCodingMode ? (
        <AssignmentIdePanel
          activeAssignment={activeIdeAssignment}
          codeDraft={codeDraft}
          isSubmitting={isSubmittingAssignment}
          onChangeCodeDraft={onChangeCodeDraft}
          onClose={onCloseIdePanel}
          onSubmit={onSubmitAssignment}
          reviewError={reviewError}
          reviewFeedback={reviewFeedback}
        />
      ) : null}
    </div>
  );
}
