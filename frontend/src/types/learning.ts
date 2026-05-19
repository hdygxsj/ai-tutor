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
}

export interface LearningPlanSummary {
  id: string;
  title: string;
  goal: string;
  status: string;
  lessons: LessonSummary[];
}

export interface DashboardSummary {
  active_plan_title: string;
  next_action: string;
  assigned_count: number;
  mastery_average: number;
}
