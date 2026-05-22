import { CloseOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Input, Space, Tag, Typography } from "antd";

import type { ActiveIdeAssignment } from "../hooks/use-assignment-ide";

const { TextArea } = Input;

interface AssignmentIdePanelProps {
  activeAssignment: ActiveIdeAssignment | null;
  codeDraft: string;
  isSubmitting: boolean;
  onChangeCodeDraft: (value: string) => void;
  onClose: () => void;
  onSubmit: () => void;
  reviewError: string | null;
  reviewFeedback: string | null;
}

export function AssignmentIdePanel({
  activeAssignment,
  codeDraft,
  isSubmitting,
  onChangeCodeDraft,
  onClose,
  onSubmit,
  reviewError,
  reviewFeedback,
}: AssignmentIdePanelProps) {
  return (
    <Card
      aria-label="在线 IDE / 调试工作区"
      className="assignment-ide-panel"
      variant="borderless"
    >
      <div className="assignment-ide-panel__header">
        <div>
          <Tag color={activeAssignment ? "blue" : "purple"}>
            {activeAssignment ? "代码任务" : "调试模式"}
          </Tag>
          <Typography.Title className="assignment-ide-panel__title" level={4}>
            {activeAssignment?.title ?? "代码任务预览"}
          </Typography.Title>
        </div>
        <Button aria-label="关闭调试工作区" icon={<CloseOutlined />} onClick={onClose} />
      </div>

      {activeAssignment ? (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Typography.Paragraph className="assignment-ide-panel__prompt" type="secondary">
            {activeAssignment.prompt}
          </Typography.Paragraph>
          <TextArea
            aria-label="代码编辑器"
            className="assignment-ide-panel__editor"
            onChange={(event) => onChangeCodeDraft(event.target.value)}
            placeholder="在这里编写代码或答案，提交后由 Agent 老师审阅"
            rows={14}
            value={codeDraft}
          />
          <Button loading={isSubmitting} onClick={onSubmit} type="primary">
            提交给 Agent 审阅
          </Button>
          {reviewFeedback ? (
            <Alert
              message="Agent 审阅完成"
              description={reviewFeedback}
              showIcon
              type="success"
            />
          ) : null}
          {reviewError ? (
            <Alert
              message="提交失败"
              description={reviewError}
              showIcon
              type="error"
            />
          ) : null}
        </Space>
      ) : (
        <div className="assignment-ide-panel__debug">
          <Typography.Paragraph>
            调试模式会强制展示编程题布局，用来验证对话区向左收缩、右侧工作区出现的效果。
          </Typography.Paragraph>
          <div className="assignment-ide-panel__placeholder">
            <Typography.Text strong>右侧 IDE / 调试区</Typography.Text>
            <Typography.Text type="secondary">
              之后可以承载代码编辑器、运行结果、测试日志或 Agent 调试信息。
            </Typography.Text>
          </div>
        </div>
      )}
    </Card>
  );
}
