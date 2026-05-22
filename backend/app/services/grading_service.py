from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.models.learning import (
    AgentObservation,
    Assignment,
    AssignmentReview,
    AssignmentSubmission,
    LearningEvent,
    LessonProgress,
    MasteryRecord,
)


class GradingService:
    def __init__(self, db: Session, tenant: TenantContext) -> None:
        self.db = db
        self.tenant = tenant

    def submit_and_grade(self, assignment_id: str, content: str) -> AssignmentReview:
        assignment = self.db.scalar(
            select(Assignment).where(
                Assignment.id == assignment_id,
                Assignment.tenant_id == self.tenant.tenant_id,
                Assignment.workspace_id == self.tenant.workspace_id,
            )
        )
        if assignment is None:
            raise ValueError("Assignment not found")
        course_id = assignment.lesson.module.plan_id

        required_concepts = assignment.rubric.get("required_concepts", [])
        content_lower = content.lower()
        matched_concepts = [
            concept for concept in required_concepts if concept.lower() in content_lower
        ]
        missing_concepts = [
            concept for concept in required_concepts if concept not in matched_concepts
        ]
        passed = not missing_concepts
        status = "passed" if passed else "needs_revision"
        score = 90 if passed else 45

        deterministic_results = {
            "required_concepts": required_concepts,
            "matched_concepts": matched_concepts,
            "missing_concepts": missing_concepts,
        }
        llm_review = {
            "verdict": status,
            "summary": (
                "回答覆盖 requires_grad 与 backward。"
                if passed
                else "回答缺少关键 autograd 概念。"
            ),
        }
        progress = self.db.scalar(
            select(LessonProgress).where(
                LessonProgress.lesson_id == assignment.lesson_id,
                LessonProgress.tenant_id == self.tenant.tenant_id,
                LessonProgress.workspace_id == self.tenant.workspace_id,
            )
        )

        submission = AssignmentSubmission(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            assignment=assignment,
            content=content,
            evidence={"source": "service", "required_concepts": required_concepts},
        )
        review = AssignmentReview(
            tenant_id=self.tenant.tenant_id,
            workspace_id=self.tenant.workspace_id,
            submission=submission,
            status=status,
            score=score,
            deterministic_results=deterministic_results,
            llm_review=llm_review,
            feedback=llm_review["summary"],
        )
        assignment.status = "completed" if passed else "needs_revision"
        if progress is not None:
            progress.status = "mastered" if passed else "needs_revision"
            progress.mastery_score = 5 if passed else 2
            progress.next_action = (
                "进入下一课，或复盘 autograd 关键概念"
                if passed
                else "重做作业，并复习 autograd 的 requires_grad 与 backward"
            )

        self.db.add_all(
            [
                submission,
                review,
                MasteryRecord(
                    tenant_id=self.tenant.tenant_id,
                    workspace_id=self.tenant.workspace_id,
                    knowledge_point="autograd",
                    mastery_score=5 if passed else 2,
                    evidence={
                        "assignment_id": assignment.id,
                        "status": status,
                        "score": score,
                    },
                ),
                AgentObservation(
                    tenant_id=self.tenant.tenant_id,
                    workspace_id=self.tenant.workspace_id,
                    observation_type="assignment_review",
                    summary=llm_review["summary"],
                    evidence={
                        "assignment_id": assignment.id,
                        "status": status,
                        "missing_concepts": missing_concepts,
                    },
                ),
                LearningEvent(
                    tenant_id=self.tenant.tenant_id,
                    workspace_id=self.tenant.workspace_id,
                    event_type="assignment_graded",
                    payload={
                        "course_id": course_id,
                        "assignment_id": assignment.id,
                        "status": status,
                        "score": score,
                    },
                ),
            ]
        )
        self.db.commit()
        self.db.refresh(review)
        return review
