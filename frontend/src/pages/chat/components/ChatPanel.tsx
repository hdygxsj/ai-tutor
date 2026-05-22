import {
  BugOutlined,
  DeleteOutlined,
  HistoryOutlined,
  PlusOutlined,
  RobotOutlined,
  SendOutlined,
} from "@ant-design/icons";
import { Alert, Avatar, Button, Card, Input, Space, Typography } from "antd";
import type { RefObject } from "react";

import type {
  CourseSummary,
  LearningPlanSummary,
  TutorChatMessage,
  TutorProvider,
} from "../../../types/learning";
import { ChatBubble } from "./ChatBubble";

const { TextArea } = Input;

const providerLabels: Record<TutorProvider, string> = {
  fake: "Fake",
  ollama: "Ollama",
  openai_compatible: "OpenAI-compatible",
};

interface ChatPanelProps {
  bottomRef: RefObject<HTMLDivElement>;
  codeLayoutActive: boolean;
  currentCourse: CourseSummary | null;
  createdPlan?: LearningPlanSummary;
  error: string | null;
  hasConversation: boolean;
  input: string;
  isCreatingPlan: boolean;
  isSending: boolean;
  lastProvider?: TutorProvider;
  messages: TutorChatMessage[];
  onChangeInput: (value: string) => void;
  onClearHistory: () => void;
  onCreateConversation: () => void;
  onOpenHistory: () => void;
  onOpenIde: (action: NonNullable<TutorChatMessage["actions"]>[number]) => void;
  onSend: () => void;
  onToggleDebugLayout: () => void;
  planError?: string;
  sessionTokenTotal: number;
}

export function ChatPanel({
  bottomRef,
  codeLayoutActive,
  currentCourse,
  createdPlan,
  error,
  hasConversation,
  input,
  isCreatingPlan,
  isSending,
  lastProvider,
  messages,
  onChangeInput,
  onClearHistory,
  onCreateConversation,
  onOpenHistory,
  onOpenIde,
  onSend,
  onToggleDebugLayout,
  planError,
  sessionTokenTotal,
}: ChatPanelProps) {
  return (
    <div className="chat-panel">
      {!hasConversation ? (
        <Card className="chat-hero" variant="borderless">
          <div className="chat-hero__content">
            <Typography.Text className="chat-hero__eyebrow">AI 导师</Typography.Text>
            <Typography.Title className="chat-hero__title" level={1}>
              引导式学习对话
            </Typography.Title>
            <Typography.Paragraph className="chat-hero__description">
              M2.1 使用 Settings 里的导师 provider，学习计划/评分仍保持确定性。
              对话历史会保存在本机浏览器，刷新页面后仍可继续。
            </Typography.Paragraph>
          </div>
        </Card>
      ) : null}

      <Card className="chat-shell" styles={{ body: { padding: 0 } }} variant="borderless">
        <div className="chat-toolbar">
          <Space>
            <Avatar icon={<RobotOutlined />} className="chat-toolbar__avatar" />
            <div className="chat-toolbar__copy">
              <Typography.Text strong>AI Dream 导师</Typography.Text>
              <Typography.Text type="secondary">
                {currentCourse ? `当前课程：${currentCourse.title}` : "等待你的问题"}
              </Typography.Text>
              <Typography.Text type="secondary">
                {lastProvider ? `最近回复：${providerLabels[lastProvider]}` : "等待导师回复"}
              </Typography.Text>
              <Typography.Text type="secondary">
                本会话 {sessionTokenTotal} tokens
              </Typography.Text>
            </div>
          </Space>
          <Space className="chat-toolbar__actions" wrap>
            <Button
              aria-label="调试布局"
              icon={<BugOutlined />}
              onClick={onToggleDebugLayout}
              type={codeLayoutActive ? "primary" : "default"}
            >
              调试布局
            </Button>
            <Button aria-label="历史记录" icon={<HistoryOutlined />} onClick={onOpenHistory}>
              历史记录
            </Button>
            <Button aria-label="新对话" icon={<PlusOutlined />} onClick={onCreateConversation}>
              新对话
            </Button>
            <Button
              aria-label="清空对话"
              danger
              disabled={!hasConversation || isSending || isCreatingPlan}
              icon={<DeleteOutlined />}
              onClick={onClearHistory}
            >
              清空当前对话
            </Button>
          </Space>
        </div>

        <div aria-label="导师对话历史" className="chat-stream">
          <Space direction="vertical" size={18} style={{ width: "100%" }}>
            {messages.map((message, index) => (
              <ChatBubble
                key={`${message.role}-${index}-${message.content}`}
                message={message}
                onOpenIde={onOpenIde}
              />
            ))}
            {isSending ? <TypingIndicator /> : null}
            {isCreatingPlan ? <PlanCreationIndicator /> : null}
            <div ref={bottomRef} />
          </Space>
        </div>

        <div className="chat-composer-panel">
          {error ? (
            <Alert message={error} showIcon style={{ marginBottom: 12 }} type="error" />
          ) : null}
          {planError ? (
            <Alert message={planError} showIcon style={{ marginBottom: 12 }} type="error" />
          ) : null}
          {createdPlan ? <CreatedPlanSummary plan={createdPlan} /> : null}

          <div className="chat-composer">
            <TextArea
              aria-label="输入给导师的消息"
              autoSize={{ maxRows: 5, minRows: 1 }}
              className="chat-composer__input"
              disabled={isSending || isCreatingPlan}
              onChange={(event) => onChangeInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  onSend();
                }
              }}
              placeholder="输入问题，Enter 发送，Shift + Enter 换行"
              value={input}
            />
            <Button
              aria-label="发送"
              className="chat-composer__send"
              disabled={isSending || isCreatingPlan || input.trim().length === 0}
              icon={<SendOutlined />}
              loading={isSending}
              onClick={onSend}
              type="primary"
            />
          </div>
        </div>
      </Card>
    </div>
  );
}

function CreatedPlanSummary({ plan }: { plan: LearningPlanSummary }) {
  const firstLesson = plan.lessons[0];

  return (
    <Alert
      description={
        <Space direction="vertical" size={4}>
          <Typography.Text strong>{plan.title}</Typography.Text>
          {firstLesson ? (
            <>
              <Typography.Text>{firstLesson.title}</Typography.Text>
              <Typography.Text type="secondary">
                下一步：{firstLesson.next_action}
              </Typography.Text>
            </>
          ) : null}
        </Space>
      }
      message="学习计划已创建"
      showIcon
      style={{ marginBottom: 12 }}
      type="success"
    />
  );
}

function TypingIndicator() {
  return (
    <div aria-label="AI 导师正在思考" className="chat-message">
      <Avatar icon={<RobotOutlined />} className="chat-message__avatar chat-message__avatar--assistant" />
      <div className="chat-bubble chat-bubble--typing">
        <span>正在组织回答</span>
        <span className="typing-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </div>
    </div>
  );
}

function PlanCreationIndicator() {
  return (
    <div aria-label="正在生成学习计划" className="chat-message">
      <Avatar icon={<RobotOutlined />} className="chat-message__avatar chat-message__avatar--assistant" />
      <div className="chat-bubble chat-bubble--typing">
        <span>正在根据对话生成学习计划和任务</span>
        <span className="typing-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </div>
    </div>
  );
}
