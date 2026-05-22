import { Alert, Button, Card, Descriptions, List, Space, Typography } from "antd";
import { useState } from "react";

import { runMinimalExperiment } from "../api/client";
import { MetricCard } from "../components/MetricCard";
import type { ExperimentRunResult } from "../types/learning";

export function ExperimentsPage() {
  const [result, setResult] = useState<ExperimentRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const runExperiment = async () => {
    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const nextResult = await runMinimalExperiment();

      setResult(nextResult);
    } catch (runError) {
      setError(errorMessage(runError));
    } finally {
      setRunning(false);
    }
  };

  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Text type="secondary">M2.2 Experiment Runner</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          实验运行
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          M2.2 运行最小 deterministic 实验，验证从前端触发实验、读取指标、日志和产物的闭环；后续会接 Docker/PyTorch 执行。
        </Typography.Paragraph>
      </div>

      <Card>
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Typography.Paragraph style={{ margin: 0 }}>
            当前最小实验使用确定性的轻量 runner，先固定接口和展示形态，方便下一步替换为隔离的训练环境。
          </Typography.Paragraph>
          <Button
            disabled={running}
            loading={running}
            onClick={() => void runExperiment()}
            type="primary"
          >
            运行最小实验
          </Button>
        </Space>
      </Card>

      {error ? (
        <Alert
          description={error}
          message="实验运行失败"
          showIcon
          type="error"
        />
      ) : null}

      {result ? (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Card title="运行结果">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="run_id">{result.run_id}</Descriptions.Item>
              <Descriptions.Item label="status">{result.status}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Space wrap size={16} style={{ width: "100%" }}>
            <MetricCard
              helperText="实验开始时的 loss"
              title="initial_loss"
              value={result.metrics.initial_loss}
            />
            <MetricCard
              helperText="实验结束时的 loss"
              title="final_loss"
              value={result.metrics.final_loss}
            />
            <MetricCard
              helperText="initial_loss 与 final_loss 的差值"
              title="improvement"
              value={result.metrics.improvement}
            />
          </Space>

          <Card title="Logs">
            <pre
              style={{
                background: "#0f172a",
                borderRadius: 8,
                color: "#e2e8f0",
                margin: 0,
                overflowX: "auto",
                padding: 16,
              }}
            >
              {result.logs.split("\n").map((line) => (
                <div key={line}>{line}</div>
              ))}
            </pre>
          </Card>

          <Card title="Artifacts">
            <List
              dataSource={result.artifacts}
              renderItem={(artifact) => (
                <List.Item>
                  <List.Item.Meta
                    description={`${artifact.content_type} · ${artifact.path}`}
                    title={artifact.name}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Space>
      ) : null}
    </Space>
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "实验运行失败，请稍后重试。";
}
