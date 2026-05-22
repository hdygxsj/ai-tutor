import { useEffect, useState } from "react";

import {
  createAgentSession,
  createCourse,
  listAgentSessions,
  listCourses,
} from "../../../api/client";
import type { AgentSessionSummary, CourseSummary } from "../../../types/learning";

export function useCourseSession() {
  const [currentCourse, setCurrentCourse] = useState<CourseSummary | null>(null);
  const [currentAgentSession, setCurrentAgentSession] =
    useState<AgentSessionSummary | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadCourseSession() {
      try {
        const courses = await listCourses();
        const course =
          courses.find((item) => item.status === "active") ??
          courses[0] ??
          (await createCourse({ goal: "自由探索 AI 课程", weekly_hours: 6 }));
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

  return { currentAgentSession, currentCourse };
}
