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
    RuntimeRun,
)


class GradingService:
    def __init__(self, db: Session, tenant: TenantContext) -> None:
        self.db = db
        self.tenant = tenant

    def submit_and_grade(
        self,
        assignment_id: str,
        content: str,
        run_id: str | None = None,
    ) -> AssignmentReview:
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

        runtime_run = self._resolve_runtime_run(assignment_id, run_id)
        required_concepts = assignment.rubric.get("required_concepts", [])
        content_lower = content.lower()
        matched_concepts = [
            concept for concept in required_concepts if concept.lower() in content_lower
        ]
        missing_concepts = [
            concept for concept in required_concepts if concept not in matched_concepts
        ]
        passed = runtime_run.exit_code == 0 if runtime_run is not None else not missing_concepts
        status = "passed" if passed else "needs_revision"
        score = 90 if passed else 45

        deterministic_results = {
            "required_concepts": required_concepts,
            "matched_concepts": matched_concepts,
            "missing_concepts": missing_concepts,
            "runtime": self._runtime_evidence(runtime_run),
        }
        runtime_feedback = self._runtime_feedback(runtime_run)
        llm_review = {
            "verdict": status,
            "summary": (
                runtime_feedback
                if runtime_run is not None
                else (
                    "回答覆盖 requires_grad 与 backward。"
                    if passed
                    else "回答缺少关键 autograd 概念。"
                )
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
            evidence={
                "source": "service",
                "required_concepts": required_concepts,
                "runtime": self._runtime_evidence(runtime_run),
            },
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
                    event_type="submission_reviewed",
                    payload={
                        "course_id": course_id,
                        "assignment_id": assignment.id,
                        "run_id": runtime_run.id if runtime_run is not None else None,
                        "status": status,
                        "score": score,
                        "feedback": llm_review["summary"],
                    },
                ),
                LearningEvent(
                    tenant_id=self.tenant.tenant_id,
                    workspace_id=self.tenant.workspace_id,
                    event_type="assignment_graded",
                    payload={
                        "course_id": course_id,
                        "assignment_id": assignment.id,
                        "run_id": runtime_run.id if runtime_run is not None else None,
                        "status": status,
                        "score": score,
                    },
                ),
            ]
        )
        self.db.commit()
        self.db.refresh(review)
        return review

    def _resolve_runtime_run(self, assignment_id: str, run_id: str | None) -> RuntimeRun | None:
        query = select(RuntimeRun).where(
            RuntimeRun.assignment_id == assignment_id,
            RuntimeRun.tenant_id == self.tenant.tenant_id,
            RuntimeRun.workspace_id == self.tenant.workspace_id,
        )
        if run_id:
            query = query.where(RuntimeRun.id == run_id)
        else:
            query = query.order_by(RuntimeRun.created_at.desc())
        return self.db.scalar(query)

    def _runtime_evidence(self, runtime_run: RuntimeRun | None) -> dict[str, object]:
        if runtime_run is None:
            return {}
        return {
            "run_id": runtime_run.id,
            "backend": runtime_run.backend,
            "status": runtime_run.status,
            "exit_code": runtime_run.exit_code,
            "stdout": runtime_run.stdout,
            "stderr": runtime_run.stderr,
            "test_results": runtime_run.test_results,
        }

    def _runtime_feedback(self, runtime_run: RuntimeRun | None) -> str:
        if runtime_run is None:
            return ""
        if runtime_run.exit_code == 0:
            return (
                f"代码运行通过，run_id={runtime_run.id}，exit_code=0。"
                "可以进入下一步。"
            )
        return (
            f"代码还需要修改，run_id={runtime_run.id}，"
            f"exit_code={runtime_run.exit_code}。请根据 stderr/test_results 复盘。"
        )
