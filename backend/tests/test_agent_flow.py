from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_session
from app.db.base import Base
from app.main import app
from app.schemas.learning import LessonSummary


def test_agent_intake_creates_plan_and_dashboard_reflects_assignment() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    original_override = app.dependency_overrides.get(get_session)
    app.dependency_overrides[get_session] = override_get_session
    try:
        client = TestClient(app)
        intake_response = client.post(
            "/api/agent/intake",
            json={
                "goal": "掌握机器学习基础并完成第一个 PyTorch 作业",
                "background": "会一点 Python，还没有系统学过机器学习",
                "weekly_hours": 6,
            },
        )

        assert intake_response.status_code == 200
        intake = intake_response.json()
        assert intake["title"] == "机器学习教师计划"
        assert intake["goal"] == "掌握机器学习基础并完成第一个 PyTorch 作业"
        assert len(intake["lessons"]) >= 1
        assert intake["lessons"][0]["status"] == "assignment_ready"
        assert intake["lessons"][0]["mastery_score"] == 1
        assert intake["lessons"][0]["next_action"] == "完成 autograd 概念作业"

        dashboard_response = client.get("/api/learning/dashboard")

        assert dashboard_response.status_code == 200
        dashboard = dashboard_response.json()
        assert dashboard["assigned_count"] == 1
        assert dashboard["active_plan_title"] == intake["title"]

        plan_response = client.get("/api/learning/active-plan")

        assert plan_response.status_code == 200
        active_plan = plan_response.json()
        assert active_plan["id"] == intake["id"]
        assert active_plan["title"] == "机器学习教师计划"
        assert active_plan["goal"] == "掌握机器学习基础并完成第一个 PyTorch 作业"
        assert active_plan["lessons"][0]["title"] == "张量和 autograd 入门"
        assert active_plan["lessons"][0]["next_action"] == "完成 autograd 概念作业"
    finally:
        if original_override is None:
            app.dependency_overrides.pop(get_session, None)
        else:
            app.dependency_overrides[get_session] = original_override


def test_lesson_summary_accepts_status_strings() -> None:
    summary = LessonSummary(
        id="lesson-1",
        title="Autograd",
        objective="理解自动求导",
        status="ready_for_review",
        mastery_score=0,
        next_action="开始学习",
    )

    assert summary.status == "ready_for_review"


def test_courses_api_creates_switchable_courses_and_agent_sessions() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    original_override = app.dependency_overrides.get(get_session)
    app.dependency_overrides[get_session] = override_get_session
    try:
        client = TestClient(app)

        first = client.post("/api/courses", json={"goal": "学习 PyTorch autograd"})
        second = client.post("/api/courses", json={"goal": "学习 Rust 所有权"})

        assert first.status_code == 200
        assert second.status_code == 200
        courses = client.get("/api/courses")

        assert courses.status_code == 200
        course_items = courses.json()
        assert [course["goal"] for course in course_items] == [
            "学习 Rust 所有权",
            "学习 PyTorch autograd",
        ]
        assert course_items[0]["status"] == "active"
        assert course_items[1]["status"] == "paused"

        session_a = client.post(
            f"/api/courses/{second.json()['id']}/sessions",
            json={"title": "第一次老师窗口"},
        )
        session_b = client.post(
            f"/api/courses/{second.json()['id']}/sessions",
            json={"title": "复习窗口"},
        )

        assert session_a.status_code == 200
        assert session_b.status_code == 200
        assert session_a.json()["course_id"] == second.json()["id"]
        assert session_a.json()["messages"] == []

        sessions = client.get(f"/api/courses/{second.json()['id']}/sessions")

        assert sessions.status_code == 200
        assert [session["title"] for session in sessions.json()] == [
            "复习窗口",
            "第一次老师窗口",
        ]

        activate_first = client.post(f"/api/courses/{first.json()['id']}/activate")
        assert activate_first.status_code == 200
        assert activate_first.json()["status"] == "active"
        assert client.get("/api/learning/dashboard").json()["active_plan_title"] == first.json()[
            "title"
        ]
    finally:
        if original_override is None:
            app.dependency_overrides.pop(get_session, None)
        else:
            app.dependency_overrides[get_session] = original_override


def test_assignment_submit_api_returns_agent_review() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    original_override = app.dependency_overrides.get(get_session)
    app.dependency_overrides[get_session] = override_get_session
    try:
        client = TestClient(app)
        course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
        assignment_id = course["lessons"][0]["assignment"]["id"]

        response = client.post(
            f"/api/assignments/{assignment_id}/submit",
            json={"content": "requires_grad 会追踪计算图，backward 会计算梯度。"},
        )

        assert response.status_code == 200
        review = response.json()
        assert review["status"] == "passed"
        assert review["score"] == 90
        assert review["feedback"] == "回答覆盖 requires_grad 与 backward。"
    finally:
        if original_override is None:
            app.dependency_overrides.pop(get_session, None)
        else:
            app.dependency_overrides[get_session] = original_override


def test_course_timeline_returns_chat_review_and_runtime_events() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    original_override = app.dependency_overrides.get(get_session)
    app.dependency_overrides[get_session] = override_get_session
    try:
        client = TestClient(app)
        course = client.post("/api/courses", json={"goal": "学习 autograd"}).json()
        session = client.post(
            f"/api/courses/{course['id']}/sessions",
            json={"title": "回溯测试"},
        ).json()
        assignment_id = course["lessons"][0]["assignment"]["id"]

        chat_response = client.post(
            "/api/agent/chat",
            json={
                "course_id": course["id"],
                "session_id": session["id"],
                "message": "我先学什么？",
            },
        )
        run_response = client.post(
            f"/api/assignments/{assignment_id}/run",
            json={"code": "print('hello autograd')"},
        )
        review_response = client.post(
            f"/api/assignments/{assignment_id}/submit",
            json={"content": "requires_grad 会追踪计算图，backward 会计算梯度。"},
        )
        timeline_response = client.get(f"/api/courses/{course['id']}/timeline")

        assert chat_response.status_code == 200
        assert run_response.status_code == 200
        assert review_response.status_code == 200
        assert timeline_response.status_code == 200
        timeline = timeline_response.json()
        event_types = [event["event_type"] for event in timeline["events"]]
        assert "plan_created" in event_types
        assert "agent_session_message" in event_types
        assert "runtime_run" in event_types
        assert "assignment_graded" in event_types
        assert any(event["summary"] == "学习者提问：我先学什么？" for event in timeline["events"])
        assert any("hello autograd" in event["summary"] for event in timeline["events"])
        assert any("90" in event["summary"] for event in timeline["events"])
    finally:
        if original_override is None:
            app.dependency_overrides.pop(get_session, None)
        else:
            app.dependency_overrides[get_session] = original_override
