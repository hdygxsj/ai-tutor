import type {
  DashboardSummary,
  LearningPlanSummary,
  TutorChatRequest,
  TutorChatResponse,
  TutorConnectionTestResult,
  TutorSettings,
  TutorSettingsUpdate,
} from "../types/learning";

export const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export interface IntakePayload {
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
