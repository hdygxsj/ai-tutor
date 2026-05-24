export type LearningStatus =
  | "not_started"
  | "in_progress"
  | "assignment_ready"
  | "submitted"
  | "needs_revision"
  | "mastered"
  | "review_scheduled";

export interface LessonSummary {
  id: string;
  title: string;
  objective: string;
  status: LearningStatus;
  mastery_score: number;
  next_action: string;
  assignment?: {
    id: string;
    lesson_id: string;
    title: string;
    kind: string;
    prompt: string;
    status: string;
    starter_code?: string;
    test_command?: string;
    tests?: string[];
    dataset_notes?: string;
  } | null;
}

export interface LearningPlanSummary {
  id: string;
  title: string;
  goal: string;
  status: string;
  lessons: LessonSummary[];
}

export type CourseSummary = LearningPlanSummary;

export interface CourseTimelineEvent {
  id: string;
  event_type: string;
  summary: string;
  created_at: string;
  payload: Record<string, unknown>;
}

export interface CourseTimelineResponse {
  course_id: string;
  events: CourseTimelineEvent[];
}

export interface AgentSessionSummary {
  id: string;
  course_id: string;
  title: string;
  status: string;
  messages: Array<Record<string, unknown>>;
  token_usage: Record<string, number>;
}

export interface DashboardSummary {
  active_plan_title: string;
  next_action: string;
  assigned_count: number;
  mastery_average: number;
}

export type TutorProvider = "fake" | "ollama" | "openai_compatible";

export interface TutorSettings {
  provider: TutorProvider;
  base_url?: string | null;
  model_name?: string | null;
  has_api_key: boolean;
}

export interface TutorSettingsUpdate {
  provider: TutorProvider;
  base_url?: string;
  model_name?: string;
  api_key?: string;
}

export interface TutorConnectionTestResult {
  ok: boolean;
  message: string;
}

export type ChatRole = "system" | "user" | "assistant";

export interface TutorChatMessage {
  role: ChatRole;
  content: string;
  createdAt?: string;
  usage?: TokenUsage;
  actions?: AgentAction[];
}

export interface TutorChatRequest {
  message: string;
  history?: TutorChatMessage[];
  course_id?: string;
  session_id?: string;
}

export interface TutorChatResponse {
  reply: string;
  provider: TutorProvider;
  usage: TokenUsage;
  actions: AgentAction[];
  course_id?: string | null;
  session_id?: string | null;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  provider: TutorProvider | string;
  model?: string | null;
  source: "provider" | "estimated" | "unknown" | string;
}

export interface AgentAction {
  type: string;
  label: string;
  payload: Record<string, unknown>;
}

export interface AssignmentReviewSummary {
  id: string;
  status: string;
  score: number;
  feedback: string;
}

export interface RuntimeRunResponse {
  id: string;
  course_id: string;
  assignment_id: string;
  backend: "sandbox" | "kubernetes";
  status: string;
  stdout: string;
  stderr: string;
  exit_code: number | null;
  test_results: Record<string, unknown>;
  logs: string[];
  artifacts: Array<Record<string, unknown>>;
  metadata: Record<string, unknown>;
}

export interface ExperimentArtifact {
  name: string;
  path: string;
  content_type: string;
}

export interface ExperimentRunResult {
  run_id: string;
  status: string;
  metrics: {
    initial_loss: number;
    final_loss: number;
    improvement: number;
  };
  logs: string;
  artifacts: ExperimentArtifact[];
}
