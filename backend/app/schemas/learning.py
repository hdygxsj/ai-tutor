from pydantic import BaseModel, Field


class IntakeRequest(BaseModel):
    goal: str = Field(min_length=3)
    background: str = ""
    weekly_hours: int = Field(default=5, ge=1, le=80)


class LessonSummary(BaseModel):
    id: str
    title: str
    objective: str
    status: str
    mastery_score: int = Field(strict=True)
    next_action: str


class LearningPlanSummary(BaseModel):
    id: str
    title: str
    goal: str
    status: str
    lessons: list[LessonSummary]


class DashboardSummary(BaseModel):
    active_plan_title: str
    next_action: str
    assigned_count: int
    mastery_average: int = Field(strict=True)


class AssignmentSummary(BaseModel):
    id: str
    lesson_id: str
    title: str
    kind: str
    prompt: str
    status: str


class AssignmentSubmissionRequest(BaseModel):
    content: str = Field(min_length=1)


class AssignmentReviewSummary(BaseModel):
    id: str
    status: str
    score: int
    feedback: str
