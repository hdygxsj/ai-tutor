import { useEffect, useState } from "react";

import { Alert, Card, Empty, List, Space, Tag, Typography } from "antd";

import { fetchActivePlan } from "../api/client";
import type { LearningPlanSummary } from "../types/learning";

export function LearningPlanPage() {
  const [plan, setPlan] = useState<LearningPlanSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;

    async function loadPlan() {
      setIsLoading(true);
      setError(null);

      try {
        const activePlan = await fetchActivePlan();
        if (isCurrent) {
          setPlan(activePlan);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "读取学习计划失败，请稍后重试。",
          );
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false);
        }
      }
    }

    void loadPlan();

    return () => {
      isCurrent = false;
    };
  }, []);

  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Text type="secondary">Learning Plan</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          学习计划
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          查看课程模块、课时目标和学习进度。
        </Typography.Paragraph>
      </div>

      {error ? <Alert message={error} showIcon type="error" /> : null}

      <Card loading={isLoading}>
        {plan ? (
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            <div>
              <Space align="center" wrap>
                <Typography.Title level={3} style={{ margin: 0 }}>
                  {plan.title}
                </Typography.Title>
                <Tag color={plan.status === "active" ? "green" : "default"}>
                  {plan.status}
                </Tag>
              </Space>
              <Typography.Paragraph style={{ color: "#64748b", marginTop: 8 }}>
                {plan.goal}
              </Typography.Paragraph>
            </div>

            <List
              dataSource={plan.lessons}
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
          </Space>
        ) : (
          <Empty
            description="创建学习计划后，这里会展示课程模块。"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>
    </Space>
  );
}
