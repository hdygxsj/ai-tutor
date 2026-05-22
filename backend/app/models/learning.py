from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TenantMixin:
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class LearningBase(Base, TenantMixin, TimestampMixin):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)


class LearnerProfile(LearningBase):
    __tablename__ = "learner_profiles"

    display_name: Mapped[str] = mapped_column(String(255), default="本地学习者", nullable=False)
    goals: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    background: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class LearningPlan(LearningBase):
    __tablename__ = "learning_plans"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)

    modules: Mapped[list["LearningModule"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="LearningModule.position",
    )
    agent_sessions: Mapped[list["AgentSession"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="AgentSession.updated_at.desc()",
    )


class AgentSession(LearningBase):
    __tablename__ = "agent_sessions"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("learning_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), default="新的 Agent 会话", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    messages: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    token_usage: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        nullable=False,
    )

    course: Mapped[LearningPlan] = relationship(back_populates="agent_sessions")


class LearningModule(LearningBase):
    __tablename__ = "learning_modules"

    plan_id: Mapped[str] = mapped_column(
        ForeignKey("learning_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    position: Mapped[int] = mapped_column(default=0, nullable=False)

    plan: Mapped[LearningPlan] = relationship(back_populates="modules")
    lessons: Mapped[list["LearningLesson"]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="LearningLesson.position",
    )


class LearningLesson(LearningBase):
    __tablename__ = "learning_lessons"

    module_id: Mapped[str] = mapped_column(
        ForeignKey("learning_modules.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(default=0, nullable=False)

    module: Mapped[LearningModule] = relationship(back_populates="lessons")
    progress_records: Mapped[list["LessonProgress"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
    )


class LessonProgress(LearningBase):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "workspace_id",
            "lesson_id",
            name="uq_lesson_progress_tenant_workspace_lesson",
        ),
    )

    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("learning_lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), default="not_started", nullable=False)
    mastery_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_action: Mapped[str] = mapped_column(String(255), default="开始学习", nullable=False)

    lesson: Mapped[LearningLesson] = relationship(back_populates="progress_records")


class Assignment(LearningBase):
    __tablename__ = "assignments"

    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("learning_lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    rubric: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="assigned", nullable=False)

    lesson: Mapped[LearningLesson] = relationship(back_populates="assignments")
    submissions: Mapped[list["AssignmentSubmission"]] = relationship(
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class AssignmentSubmission(LearningBase):
    __tablename__ = "assignment_submissions"

    assignment_id: Mapped[str] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    assignment: Mapped[Assignment] = relationship(back_populates="submissions")
    reviews: Mapped[list["AssignmentReview"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
    )


class AssignmentReview(LearningBase):
    __tablename__ = "assignment_reviews"

    submission_id: Mapped[str] = mapped_column(
        ForeignKey("assignment_submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[int] = mapped_column(default=0, nullable=False)
    deterministic_results: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    llm_review: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)

    submission: Mapped[AssignmentSubmission] = relationship(back_populates="reviews")


class MasteryRecord(LearningBase):
    __tablename__ = "mastery_records"

    knowledge_point: Mapped[str] = mapped_column(String(255), nullable=False)
    mastery_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class LearningEvent(LearningBase):
    __tablename__ = "learning_events"

    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class AgentObservation(LearningBase):
    __tablename__ = "agent_observations"

    observation_type: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
