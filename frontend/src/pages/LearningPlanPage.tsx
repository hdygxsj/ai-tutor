import { Card, Descriptions, Empty, Space, Typography } from "antd";

export function LearningPlanPage() {
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

      <Card>
        <Descriptions column={1} title="M1 页面范围">
          <Descriptions.Item label="课程结构">
            后续会展示 lesson 列表、状态和掌握度。
          </Descriptions.Item>
          <Descriptions.Item label="当前版本">
            仅提供导航目标和空状态。
          </Descriptions.Item>
        </Descriptions>
        <Empty
          description="创建学习计划后，这里会展示课程模块。"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    </Space>
  );
}
