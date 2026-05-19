import { Card, Descriptions, Empty, Space, Typography } from "antd";

export function SettingsPage() {
  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Text type="secondary">设置</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          学习者偏好
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          管理本地学习偏好、学习节奏和工作区配置。
        </Typography.Paragraph>
      </div>

      <Card>
        <Descriptions column={1} title="配置项">
          <Descriptions.Item label="学习目标">
            后续将支持保存目标和背景信息。
          </Descriptions.Item>
          <Descriptions.Item label="每周投入">
            用于生成更贴近时间预算的学习计划。
          </Descriptions.Item>
        </Descriptions>
        <Empty
          description="设置表单将在后续任务中启用。"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    </Space>
  );
}
