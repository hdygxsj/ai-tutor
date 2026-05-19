import { Card, Descriptions, Empty, Space, Typography } from "antd";

export function ChatPage() {
  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Text type="secondary">AI 导师</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          引导式学习对话
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          M1 阶段先保留对话入口，后续任务会接入 intake 和 tutor loop。
        </Typography.Paragraph>
      </div>

      <Card>
        <Descriptions column={1} title="当前能力范围">
          <Descriptions.Item label="目标">
            围绕学习目标收集背景信息并推荐下一步行动。
          </Descriptions.Item>
          <Descriptions.Item label="状态">等待任务接入对话流。</Descriptions.Item>
        </Descriptions>
        <Empty
          description="AI 导师对话将在后续任务中启用。"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    </Space>
  );
}
