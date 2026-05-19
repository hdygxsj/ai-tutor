import { Card, Descriptions, Empty, Space, Typography } from "antd";

export function AssignmentsPage() {
  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      <div>
        <Typography.Text type="secondary">作业反馈</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          作业与修订
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          管理练习提交、自动批改结果和下一轮修订建议。
        </Typography.Paragraph>
      </div>

      <Card>
        <Descriptions column={1} title="反馈闭环">
          <Descriptions.Item label="提交">
            学习者完成练习后提交答案。
          </Descriptions.Item>
          <Descriptions.Item label="反馈">
            Agent 将根据 rubric 给出批改和修订建议。
          </Descriptions.Item>
        </Descriptions>
        <Empty
          description="当前还没有待处理作业。"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    </Space>
  );
}
