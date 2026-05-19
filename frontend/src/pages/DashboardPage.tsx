import { Alert, Button, Card, Empty, Space, Typography } from "antd";
import { useCallback, useEffect, useRef, useState } from "react";

import { fetchDashboard, startIntake } from "../api/client";
import { MetricCard } from "../components/MetricCard";
import type { DashboardSummary } from "../types/learning";

const SAMPLE_INTAKE = {
  goal: "完成 M1 机器学习入门学习计划",
  background: "已有基础 Python 经验，希望建立机器学习核心概念和练习闭环。",
  weekly_hours: 6,
};

export function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [creatingPlan, setCreatingPlan] = useState(false);
  const [dashboardError, setDashboardError] = useState(false);
  const [createPlanError, setCreatePlanError] = useState(false);
  const dashboardRequestId = useRef(0);

  const loadDashboard = useCallback(async () => {
    const requestId = dashboardRequestId.current + 1;

    dashboardRequestId.current = requestId;
    setLoadingDashboard(true);
    setDashboardError(false);

    try {
      const nextDashboard = await fetchDashboard();

      if (requestId !== dashboardRequestId.current) {
        return;
      }

      setDashboard(nextDashboard);
      setDashboardError(false);
    } catch {
      if (requestId !== dashboardRequestId.current) {
        return;
      }

      setDashboard(null);
      setDashboardError(true);
    } finally {
      if (requestId === dashboardRequestId.current) {
        setLoadingDashboard(false);
      }
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const createPlan = async () => {
    setCreatingPlan(true);
    setCreatePlanError(false);

    try {
      await startIntake(SAMPLE_INTAKE);
      await loadDashboard();
    } catch {
      setCreatePlanError(true);
    } finally {
      setCreatingPlan(false);
    }
  };

  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Text type="secondary">M1 学习闭环</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          今日学习面板
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          跟踪当前课程、待完成作业和下一步学习建议。
        </Typography.Paragraph>
      </div>

      <Space wrap size={16} style={{ width: "100%" }}>
        <MetricCard
          helperText="当前计划中待提交或待修订的练习"
          title="待完成作业"
          value={dashboard?.assigned_count ?? 0}
        />
        <MetricCard
          helperText="基于已完成课时的掌握度估算"
          suffix="/ 5"
          title="平均掌握度"
          value={dashboard?.mastery_average ?? 0}
        />
        <MetricCard
          helperText="正在推进的学习计划"
          title="当前课程"
          value={dashboard?.active_plan_title ?? "暂无课程"}
        />
      </Space>

      {dashboardError ? (
        <Alert
          action={
            <Button
              aria-label="重试"
              onClick={() => void loadDashboard()}
              size="small"
            >
              重试
            </Button>
          }
          description="请检查后端服务是否已启动，或稍后重试。"
          message="学习面板加载失败"
          showIcon
          type="error"
        />
      ) : dashboard ? (
        <Alert
          description={dashboard.next_action}
          message="下一步建议"
          showIcon
          type="info"
        />
      ) : (
        <Card loading={loadingDashboard}>
          {!loadingDashboard ? (
            <Empty
              description="暂未加载到学习面板数据，可以创建 M1 示例学习计划开始。"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : null}
        </Card>
      )}

      {createPlanError ? (
        <Alert
          description="请检查后端服务状态，或稍后重试创建学习计划。"
          message="创建学习计划失败"
          showIcon
          type="error"
        />
      ) : null}

      <Button loading={creatingPlan} onClick={createPlan} type="primary">
        创建 M1 示例学习计划
      </Button>
    </Space>
  );
}
