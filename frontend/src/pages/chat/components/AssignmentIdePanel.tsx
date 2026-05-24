import { CloseOutlined } from "@ant-design/icons";
import Editor from "@monaco-editor/react";
import { Alert, Button, Card, Input, Space, Tag, Typography } from "antd";

import type { ActiveIdeAssignment } from "../hooks/use-assignment-ide";
import type { RuntimeRunResponse } from "../../../types/learning";

const { TextArea } = Input;

interface AssignmentIdePanelProps {
  activeAssignment: ActiveIdeAssignment | null;
  codeDraft: string;
  fileName: string;
  language: string;
  isRunning: boolean;
  isSubmitting: boolean;
  onChangeCodeDraft: (value: string) => void;
  onChangeFileName: (value: string) => void;
  onChangeLanguage: (value: string) => void;
  onClose: () => void;
  onRun: () => void;
  onSubmit: () => void;
  reviewError: string | null;
  reviewFeedback: string | null;
  runError: string | null;
  runResult: RuntimeRunResponse | null;
}

export function AssignmentIdePanel({
  activeAssignment,
  codeDraft,
  fileName,
  language,
  isRunning,
  isSubmitting,
  onChangeCodeDraft,
  onChangeFileName,
  onChangeLanguage,
  onClose,
  onRun,
  onSubmit,
  reviewError,
  reviewFeedback,
  runError,
  runResult,
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
          <Space direction="vertical" size={4}>
            {activeAssignment.testCommand ? (
              <Typography.Text type="secondary">
                测试命令：{activeAssignment.testCommand}
              </Typography.Text>
            ) : null}
            {activeAssignment.datasetNotes ? (
              <Typography.Text type="secondary">
                数据说明：{activeAssignment.datasetNotes}
              </Typography.Text>
            ) : null}
            {activeAssignment.tests?.length ? (
              <Typography.Text type="secondary">
                测试要求：{activeAssignment.tests.join("；")}
              </Typography.Text>
            ) : null}
          </Space>
          <Space wrap>
            <div className="assignment-ide-panel__field">
              <Typography.Text aria-hidden="true" type="secondary">文件名</Typography.Text>
              <Input
                aria-label="文件名"
                onChange={(event) => onChangeFileName(event.target.value)}
                value={fileName}
              />
            </div>
            <div className="assignment-ide-panel__field">
              <Typography.Text aria-hidden="true" type="secondary">语言</Typography.Text>
              <select
                aria-label="语言"
                className="assignment-ide-panel__select"
                onChange={(event) => onChangeLanguage(event.target.value)}
                style={{ minWidth: 160, minHeight: 32 }}
                value={language}
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
              </select>
            </div>
          </Space>
          <CodeEditor language={language} onChange={onChangeCodeDraft} value={codeDraft} />
          <Space wrap>
            <Button loading={isRunning} onClick={onRun}>
              运行代码
            </Button>
            <Button loading={isSubmitting} onClick={onSubmit} type="primary">
              提交给 Agent 审阅
            </Button>
          </Space>
          <RuntimeRunPanel error={runError} result={runResult} />
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

function CodeEditor({
  language,
  onChange,
  value,
}: {
  language: string;
  onChange: (value: string) => void;
  value: string;
}) {
  if (import.meta.env.MODE === "test") {
    return (
      <TextArea
        aria-label="代码编辑器"
        className="assignment-ide-panel__editor"
        onChange={(event) => onChange(event.target.value)}
        placeholder="在这里编写代码或答案，提交后由 Agent 老师审阅"
        rows={14}
        value={value}
      />
    );
  }

  return (
    <div aria-label="代码编辑器" className="assignment-ide-panel__monaco">
      <Editor
        defaultLanguage="python"
        height="360px"
        language={language}
        onChange={(nextValue) => onChange(nextValue ?? "")}
        options={{
          fontSize: 14,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: "on",
        }}
        theme="vs-dark"
        value={value}
      />
    </div>
  );
}

function RuntimeRunPanel({
  error,
  result,
}: {
  error: string | null;
  result: RuntimeRunResponse | null;
}) {
  if (error) {
    return <Alert message="运行失败" description={error} showIcon type="error" />;
  }

  if (!result) {
    return (
      <Card className="assignment-ide-panel__runtime" size="small" title="运行结果">
        <Typography.Text type="secondary">
          点击运行后会显示 sandbox/K8s 状态、日志和 run id。
        </Typography.Text>
      </Card>
    );
  }

  const isPreparedKubernetes =
    result.backend === "kubernetes" && result.metadata.execution === "prepared_only";

  return (
    <Card className="assignment-ide-panel__runtime" size="small" title="运行结果">
      <Space direction="vertical" size={10} style={{ width: "100%" }}>
        <Space wrap>
          <Tag color="blue">{result.backend}</Tag>
          <Tag color={result.status === "completed" ? "green" : "gold"}>{result.status}</Tag>
          <Typography.Text copyable>{result.id}</Typography.Text>
        </Space>
        {isPreparedKubernetes ? (
          <Alert message="已准备 K8s Job / 等待执行" showIcon type="warning" />
        ) : null}
        <div className="assignment-ide-panel__logs">
          {result.logs.map((line, index) => (
            <Typography.Text key={`${line}-${index}`}>{line}</Typography.Text>
          ))}
        </div>
      </Space>
    </Card>
  );
}
