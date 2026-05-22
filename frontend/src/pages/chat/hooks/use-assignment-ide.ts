import { useState } from "react";

import { submitAssignment } from "../../../api/client";
import type { TutorChatMessage } from "../../../types/learning";

export interface ActiveIdeAssignment {
  id: string;
  prompt: string;
  title: string;
}

export function useAssignmentIde() {
  const [activeIdeAssignment, setActiveIdeAssignment] =
    useState<ActiveIdeAssignment | null>(null);
  const [codeDraft, setCodeDraft] = useState("");
  const [debugLayoutEnabled, setDebugLayoutEnabled] = useState(false);
  const [reviewFeedback, setReviewFeedback] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [isSubmittingAssignment, setIsSubmittingAssignment] = useState(false);

  const isCodingMode = debugLayoutEnabled || activeIdeAssignment !== null;

  function toggleDebugLayout() {
    setDebugLayoutEnabled((current) => !current);
  }

  function openIdeFromAction(action: NonNullable<TutorChatMessage["actions"]>[number]) {
    const assignmentId = action.payload.assignment_id;
    if (typeof assignmentId !== "string") {
      return;
    }

    setActiveIdeAssignment({
      id: assignmentId,
      prompt:
        typeof action.payload.prompt === "string"
          ? action.payload.prompt
          : "完成 Agent 布置的代码任务。",
      title:
        typeof action.payload.title === "string"
          ? action.payload.title
          : action.label,
    });
    setCodeDraft("");
    setReviewFeedback(null);
    setReviewError(null);
  }

  function closeIdePanel() {
    setActiveIdeAssignment(null);
    setDebugLayoutEnabled(false);
  }

  async function submitCurrentAssignment() {
    if (!activeIdeAssignment || isSubmittingAssignment) {
      return;
    }

    setIsSubmittingAssignment(true);
    try {
      const review = await submitAssignment(activeIdeAssignment.id, codeDraft);
      setReviewFeedback(review.feedback);
      setReviewError(null);
    } catch (caughtError) {
      setReviewFeedback(null);
      setReviewError(
        caughtError instanceof Error ? caughtError.message : "提交失败，请稍后重试。",
      );
    } finally {
      setIsSubmittingAssignment(false);
    }
  }

  return {
    activeIdeAssignment,
    closeIdePanel,
    codeDraft,
    isCodingMode,
    isSubmittingAssignment,
    openIdeFromAction,
    reviewError,
    reviewFeedback,
    setCodeDraft,
    submitCurrentAssignment,
    toggleDebugLayout,
  };
}
