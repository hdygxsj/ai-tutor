import { useState } from "react";

import { runAssignment, submitAssignment } from "../../../api/client";
import type { RuntimeRunResponse, TutorChatMessage } from "../../../types/learning";

export interface ActiveIdeAssignment {
  datasetNotes?: string;
  id: string;
  fileName: string;
  language: string;
  prompt: string;
  starterCode?: string;
  testCommand?: string;
  tests?: string[];
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
  const [isRunningAssignment, setIsRunningAssignment] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<RuntimeRunResponse | null>(null);
  const [fileName, setFileName] = useState("solution.py");
  const [language, setLanguage] = useState("python");

  const isCodingMode = debugLayoutEnabled || activeIdeAssignment !== null;

  function toggleDebugLayout() {
    setDebugLayoutEnabled((current) => !current);
  }

  function openIdeFromAction(action: NonNullable<TutorChatMessage["actions"]>[number]) {
    const assignmentId = action.payload.assignment_id;
    if (typeof assignmentId !== "string") {
      return;
    }

    const starterCode =
      typeof action.payload.starter_code === "string" ? action.payload.starter_code : "";
    setActiveIdeAssignment({
      datasetNotes:
        typeof action.payload.dataset_notes === "string"
          ? action.payload.dataset_notes
          : undefined,
      fileName:
        typeof action.payload.file_name === "string"
          ? action.payload.file_name
          : "solution.py",
      id: assignmentId,
      language:
        typeof action.payload.language === "string" ? action.payload.language : "python",
      prompt:
        typeof action.payload.prompt === "string"
          ? action.payload.prompt
          : "完成 Agent 布置的代码任务。",
      starterCode,
      testCommand:
        typeof action.payload.test_command === "string"
          ? action.payload.test_command
          : undefined,
      tests: Array.isArray(action.payload.tests)
        ? action.payload.tests.filter((item): item is string => typeof item === "string")
        : undefined,
      title:
        typeof action.payload.title === "string"
          ? action.payload.title
          : action.label,
    });
    setFileName(
      typeof action.payload.file_name === "string" ? action.payload.file_name : "solution.py",
    );
    setLanguage(typeof action.payload.language === "string" ? action.payload.language : "python");
    setCodeDraft(starterCode);
    setReviewFeedback(null);
    setReviewError(null);
    setRunError(null);
    setRunResult(null);
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
      const review = runResult
        ? await submitAssignment(activeIdeAssignment.id, codeDraft, runResult.id)
        : await submitAssignment(activeIdeAssignment.id, codeDraft);
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

  async function runCurrentAssignment(sessionId?: string | null) {
    if (!activeIdeAssignment || isRunningAssignment) {
      return;
    }

    setIsRunningAssignment(true);
    try {
      const result = await runAssignment(activeIdeAssignment.id, {
        code: codeDraft,
        session_id: sessionId,
      });
      setRunResult(result);
      setRunError(null);
    } catch (caughtError) {
      setRunResult(null);
      setRunError(caughtError instanceof Error ? caughtError.message : "运行失败，请稍后重试。");
    } finally {
      setIsRunningAssignment(false);
    }
  }

  return {
    activeIdeAssignment,
    closeIdePanel,
    codeDraft,
    fileName,
    language,
    isCodingMode,
    isRunningAssignment,
    isSubmittingAssignment,
    openIdeFromAction,
    reviewError,
    reviewFeedback,
    runError,
    runResult,
    setCodeDraft,
    setFileName,
    setLanguage,
    runCurrentAssignment,
    submitCurrentAssignment,
    toggleDebugLayout,
  };
}
