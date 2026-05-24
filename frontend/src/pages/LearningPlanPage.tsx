import { useEffect, useState } from "react";

import { Alert, Button, Card, Empty, Input, List, Space, Tag, Typography } from "antd";

import {
  activateCourse,
  createCourse,
  fetchCourseTimeline,
  listCourses,
} from "../api/client";
import type { CourseSummary, CourseTimelineEvent } from "../types/learning";

const ACTIVE_COURSE_STORAGE_KEY = "ai-dream:active-course-id";

export function LearningPlanPage() {
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [activeCourse, setActiveCourse] = useState<CourseSummary | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<CourseTimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [switchingCourseId, setSwitchingCourseId] = useState<string | null>(null);
  const [newCourseGoal, setNewCourseGoal] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;

    async function loadCourseManagement() {
      setIsLoading(true);
      setError(null);

      try {
        const courseItems = await listCourses();
        const selectedCourse = selectPreferredCourse(courseItems);

        if (!isCurrent) {
          return;
        }

        setCourses(courseItems);
        setActiveCourse(selectedCourse);
        rememberActiveCourse(selectedCourse);

        if (selectedCourse) {
          const timeline = await fetchCourseTimeline(selectedCourse.id);
          if (isCurrent) {
            setTimelineEvents(timeline.events);
          }
        } else if (isCurrent) {
          setTimelineEvents([]);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "读取课程失败，请稍后重试。",
          );
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false);
        }
      }
    }

    void loadCourseManagement();

    return () => {
      isCurrent = false;
    };
  }, []);

  async function reloadCourses(preferredCourseId?: string) {
    const courseItems = await listCourses();
    const selectedCourse = selectPreferredCourse(courseItems, preferredCourseId);

    setCourses(courseItems);
    setActiveCourse(selectedCourse);
    rememberActiveCourse(selectedCourse);

    if (selectedCourse) {
      const timeline = await fetchCourseTimeline(selectedCourse.id);
      setTimelineEvents(timeline.events);
    } else {
      setTimelineEvents([]);
    }
  }

  async function handleCreateCourse() {
    const goal = newCourseGoal.trim();
    if (!goal || isCreating) {
      return;
    }

    setIsCreating(true);
    setError(null);
    try {
      const course = await createCourse({ goal, weekly_hours: 6 });
      setNewCourseGoal("");
      await reloadCourses(course.id);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "创建课程失败，请稍后重试。");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleActivateCourse(course: CourseSummary) {
    if (course.status === "active" || switchingCourseId) {
      return;
    }

    setSwitchingCourseId(course.id);
    setError(null);
    try {
      const activatedCourse = await activateCourse(course.id);
      rememberActiveCourse(activatedCourse);
      setCourses((currentCourses) =>
        currentCourses.map((item) =>
          item.id === activatedCourse.id
            ? activatedCourse
            : { ...item, status: item.status === "active" ? "paused" : item.status },
        ),
      );
      setActiveCourse(activatedCourse);
      const timeline = await fetchCourseTimeline(activatedCourse.id);
      setTimelineEvents(timeline.events);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "切换课程失败，请稍后重试。");
    } finally {
      setSwitchingCourseId(null);
    }
  }

  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Text type="secondary">Learning</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          课程管理
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          创建课程、切换当前课程，并回溯对话、运行和作业审阅记录。
        </Typography.Paragraph>
      </div>

      {error ? <Alert message={error} showIcon type="error" /> : null}

      <Card title="新建课程">
        <Space.Compact style={{ width: "100%" }}>
          <Input
            aria-label="新课程目标"
            onChange={(event) => setNewCourseGoal(event.target.value)}
            onPressEnter={() => void handleCreateCourse()}
            placeholder="例如：学习强化学习"
            value={newCourseGoal}
          />
          <Button
            disabled={!newCourseGoal.trim()}
            loading={isCreating}
            onClick={() => void handleCreateCourse()}
            type="primary"
          >
            创建课程
          </Button>
        </Space.Compact>
      </Card>

      <Card loading={isLoading} title="课程列表">
        {activeCourse ? (
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            <div>
              <Space align="center" wrap>
                <Typography.Title level={3} style={{ margin: 0 }}>
                  {activeCourse.title}
                </Typography.Title>
                <Tag color={activeCourse.status === "active" ? "green" : "default"}>
                  {activeCourse.status}
                </Tag>
              </Space>
              <Typography.Paragraph style={{ color: "#64748b", marginTop: 8 }}>
                {activeCourse.goal}
              </Typography.Paragraph>
              <Space wrap>
                <Tag color="blue">{courseProgressLabel(activeCourse)}</Tag>
                <Tag color="purple">{masteryAverageLabel(activeCourse)}</Tag>
                <Typography.Text type="secondary">
                  当前课程上下文会用于 AI 导师新消息。
                </Typography.Text>
              </Space>
            </div>

            <List
              dataSource={activeCourse.lessons}
              renderItem={(lesson) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space wrap>
                        <Typography.Text strong>{lesson.title}</Typography.Text>
                        <Tag color="blue">掌握度 {lesson.mastery_score}/5</Tag>
                        <Tag>{lesson.status}</Tag>
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={4}>
                        <Typography.Text>{lesson.objective}</Typography.Text>
                        <Typography.Text type="secondary">
                          {lesson.next_action}
                        </Typography.Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
            <List
              dataSource={courses.filter((course) => course.id !== activeCourse.id)}
              renderItem={(course) => (
                <List.Item
                  actions={[
                    course.status === "active" ? (
                      <Tag color="green" key="active">
                        当前课程
                      </Tag>
                    ) : (
                      <Button
                        aria-label={`激活 ${course.title}`}
                        key="activate"
                        loading={switchingCourseId === course.id}
                        onClick={() => void handleActivateCourse(course)}
                      >
                        激活
                      </Button>
                    ),
                  ]}
                >
                  <List.Item.Meta
                    description={
                      <Space direction="vertical" size={4}>
                        <Typography.Text type="secondary">{course.goal}</Typography.Text>
                        <Space wrap>
                          <Tag color={course.status === "active" ? "green" : "default"}>
                            {course.status}
                          </Tag>
                          <Tag>课程{courseProgressLabel(course)}</Tag>
                          <Tag>课程{masteryAverageLabel(course)}</Tag>
                        </Space>
                      </Space>
                    }
                    title={<Typography.Text strong>{course.title}</Typography.Text>}
                  />
                </List.Item>
              )}
            />
          </Space>
        ) : (
          <Empty
            description="创建学习计划后，这里会展示课程模块。"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>

      {activeCourse ? (
        <Card title="课程回溯">
          {timelineEvents.length ? (
            <List
              dataSource={timelineEvents}
              renderItem={(event) => (
                <List.Item>
                  <List.Item.Meta
                    description={
                      <Typography.Text type="secondary">
                        {formatTimelineTime(event.created_at)} · {event.event_type}
                      </Typography.Text>
                    }
                    title={<Typography.Text>{event.summary}</Typography.Text>}
                  />
                </List.Item>
              )}
            />
          ) : (
            <Empty
              description="还没有可回溯的学习记录。"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>
      ) : null}
    </Space>
  );
}

function courseProgressLabel(course: CourseSummary): string {
  const completedCount = course.lessons.filter(
    (lesson) => lesson.status !== "not_started",
  ).length;

  return `进度 ${completedCount}/${course.lessons.length}`;
}

function masteryAverageLabel(course: CourseSummary): string {
  if (!course.lessons.length) {
    return "掌握均分 0";
  }

  const total = course.lessons.reduce((sum, lesson) => sum + lesson.mastery_score, 0);
  return `掌握均分 ${Math.round(total / course.lessons.length)}`;
}

function formatTimelineTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function selectPreferredCourse(
  courses: CourseSummary[],
  preferredCourseId?: string,
): CourseSummary | null {
  const storedCourseId = window.localStorage.getItem(ACTIVE_COURSE_STORAGE_KEY);
  return (
    (preferredCourseId ? courses.find((course) => course.id === preferredCourseId) : undefined) ??
    (storedCourseId ? courses.find((course) => course.id === storedCourseId) : undefined) ??
    courses.find((course) => course.status === "active") ??
    courses[0] ??
    null
  );
}

function rememberActiveCourse(course: CourseSummary | null) {
  if (course) {
    window.localStorage.setItem(ACTIVE_COURSE_STORAGE_KEY, course.id);
  }
}
