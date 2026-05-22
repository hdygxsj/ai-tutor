import type {
  DashboardSummary,
  AgentSessionSummary,
  AssignmentReviewSummary,
  CourseTimelineResponse,
  CourseSummary,
  LearningPlanSummary,
  ExperimentRunResult,
  TutorChatRequest,
  TutorChatResponse,
  TutorConnectionTestResult,
  TutorSettings,
  TutorSettingsUpdate,
} from "../types/learning";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

export interface IntakePayload {
  goal: string;
  background?: string;
  weekly_hours?: number;
}

export interface CoursePayload {
  goal: string;
  background?: string;
  weekly_hours?: number;
}

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });
  } catch {
    throw new Error("无法连接到学习服务，请确认后端已启动。");
  }

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<T>;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string | unknown[] };

    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Fall through to the generic localized message.
  }

  return `请求失败，请稍后重试。（状态码 ${response.status}）`;
}

export function startIntake(payload: IntakePayload): Promise<LearningPlanSummary> {
  return requestJson<LearningPlanSummary>("/agent/intake", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function sendTutorMessage(
  payload: TutorChatRequest,
): Promise<TutorChatResponse> {
  return requestJson<TutorChatResponse>("/agent/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchDashboard(): Promise<DashboardSummary> {
  return requestJson<DashboardSummary>("/learning/dashboard");
}

export function fetchActivePlan(): Promise<LearningPlanSummary | null> {
  return requestJson<LearningPlanSummary | null>("/learning/active-plan");
}

export function listCourses(): Promise<CourseSummary[]> {
  return requestJson<CourseSummary[]>("/courses");
}

export function createCourse(payload: CoursePayload): Promise<CourseSummary> {
  return requestJson<CourseSummary>("/courses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function activateCourse(courseId: string): Promise<CourseSummary> {
  return requestJson<CourseSummary>(`/courses/${courseId}/activate`, {
    method: "POST",
  });
}

export function fetchCourseTimeline(courseId: string): Promise<CourseTimelineResponse> {
  return requestJson<CourseTimelineResponse>(`/courses/${courseId}/timeline`);
}

export function listAgentSessions(courseId: string): Promise<AgentSessionSummary[]> {
  return requestJson<AgentSessionSummary[]>(`/courses/${courseId}/sessions`);
}

export function createAgentSession(
  courseId: string,
  title = "新的 Agent 会话",
): Promise<AgentSessionSummary> {
  return requestJson<AgentSessionSummary>(`/courses/${courseId}/sessions`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export function submitAssignment(
  assignmentId: string,
  content: string,
): Promise<AssignmentReviewSummary> {
  return requestJson<AssignmentReviewSummary>(`/assignments/${assignmentId}/submit`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function fetchTutorSettings(): Promise<TutorSettings> {
  return requestJson<TutorSettings>("/settings/tutor");
}

export function saveTutorSettings(
  payload: TutorSettingsUpdate,
): Promise<TutorSettings> {
  return requestJson<TutorSettings>("/settings/tutor", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function testTutorSettings(
  payload: TutorSettingsUpdate,
): Promise<TutorConnectionTestResult> {
  return requestJson<TutorConnectionTestResult>("/settings/tutor/test", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function runMinimalExperiment(): Promise<ExperimentRunResult> {
  return requestJson<ExperimentRunResult>("/experiments/minimal", {
    method: "POST",
  });
}
