import { RobotOutlined, UserOutlined } from "@ant-design/icons";
import { Avatar, Button, Space, Typography } from "antd";

import type { TutorChatMessage } from "../../../types/learning";

interface ChatBubbleProps {
  message: TutorChatMessage;
  onOpenIde: (action: NonNullable<TutorChatMessage["actions"]>[number]) => void;
}

export function ChatBubble({ message, onOpenIde }: ChatBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`chat-message ${isUser ? "chat-message--user" : ""}`}>
      {!isUser ? (
        <Avatar
          icon={<RobotOutlined />}
          className="chat-message__avatar chat-message__avatar--assistant"
        />
      ) : null}
      <div className={`chat-bubble ${isUser ? "chat-bubble--user" : ""}`}>
        <Typography.Paragraph className="chat-bubble__content">
          {message.content}
        </Typography.Paragraph>
        <div className="chat-bubble__meta">
          {message.createdAt ? (
            <Typography.Text type="secondary">{formatMessageTime(message.createdAt)}</Typography.Text>
          ) : null}
          {!isUser && message.usage ? (
            <Typography.Text type="secondary">本次 {message.usage.total_tokens} tokens</Typography.Text>
          ) : null}
        </div>
        {!isUser && message.actions?.length ? (
          <Space className="chat-action-list" direction="vertical" size={8}>
            {message.actions.map((action, index) => (
              <AgentActionCard
                action={action}
                key={`${action.type}-${index}`}
                onOpenIde={onOpenIde}
              />
            ))}
          </Space>
        ) : null}
      </div>
      {isUser ? (
        <Avatar
          icon={<UserOutlined />}
          className="chat-message__avatar chat-message__avatar--user"
        />
      ) : null}
    </div>
  );
}

function formatMessageTime(createdAt: string): string {
  const date = new Date(createdAt);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function AgentActionCard({
  action,
  onOpenIde,
}: {
  action: NonNullable<TutorChatMessage["actions"]>[number];
  onOpenIde: (action: NonNullable<TutorChatMessage["actions"]>[number]) => void;
}) {
  const title =
    typeof action.payload.title === "string" ? action.payload.title : "等待 Agent 安排下一步";
  const canOpenIde = typeof action.payload.assignment_id === "string";

  return (
    <div className="chat-action-card">
      <Typography.Text strong>{action.label}</Typography.Text>
      <Typography.Text type="secondary">{title}</Typography.Text>
      {canOpenIde ? (
        <Button size="small" onClick={() => onOpenIde(action)}>
          打开在线 IDE
        </Button>
      ) : null}
    </div>
  );
}
