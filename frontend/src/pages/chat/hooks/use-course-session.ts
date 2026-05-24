import { useEffect, useState } from "react";

import {
  createAgentSession,
  createCourse,
  listAgentSessions,
  listCourses,
} from "../../../api/client";
import type { AgentSessionSummary, CourseSummary } from "../../../types/learning";

const ACTIVE_COURSE_STORAGE_KEY = "ai-dream:active-course-id";

export function useCourseSession() {
  const [currentCourse, setCurrentCourse] = useState<CourseSummary | null>(null);
  const [currentAgentSession, setCurrentAgentSession] =
    useState<AgentSessionSummary | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadCourseSession() {
      try {
        const courses = await listCourses();
        const storedCourseId = window.localStorage.getItem(ACTIVE_COURSE_STORAGE_KEY);
        const course =
          courses.find((item) => item.id === storedCourseId) ??
          courses.find((item) => item.status === "active") ??
          courses[0] ??
          (await createCourse({ goal: "自由探索 AI 课程", weekly_hours: 6 }));
        window.localStorage.setItem(ACTIVE_COURSE_STORAGE_KEY, course.id);
        const sessions = await listAgentSessions(course.id);
        const agentSession =
          sessions[0] ?? (await createAgentSession(course.id, "新的 Agent 会话"));

        if (isMounted) {
          setCurrentCourse(course);
          setCurrentAgentSession(agentSession);
        }
      } catch {
        // The local chat still works if the course/session bootstrap API is unavailable.
      }
    }

    void loadCourseSession();

    return () => {
      isMounted = false;
    };
  }, []);

  async function adoptServerCourseSession(
    courseId?: string | null,
    sessionId?: string | null,
  ) {
    if (!courseId) {
      return;
    }

    window.localStorage.setItem(ACTIVE_COURSE_STORAGE_KEY, courseId);

    try {
      const [courses, sessions] = await Promise.all([
        listCourses(),
        listAgentSessions(courseId),
      ]);
      const serverCourse = courses.find((course) => course.id === courseId);
      const serverSession = sessionId
        ? sessions.find((session) => session.id === sessionId)
        : sessions[0];

      if (serverCourse) {
        setCurrentCourse(serverCourse);
      }
      if (serverSession) {
        setCurrentAgentSession(serverSession);
      }
    } catch {
      // Keep the chat responsive; the next bootstrap can reconcile server state.
    }
  }

  return { adoptServerCourseSession, currentAgentSession, currentCourse };
}
