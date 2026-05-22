import { Button, Drawer, Empty, List } from "antd";

import type { ChatSession } from "../hooks/use-chat-sessions";

interface HistoryDrawerProps {
  currentSessionId: string;
  onClose: () => void;
  onSelect: (sessionId: string) => void;
  open: boolean;
  sessions: ChatSession[];
}

export function HistoryDrawer({
  currentSessionId,
  onClose,
  onSelect,
  open,
  sessions,
}: HistoryDrawerProps) {
  const sortedSessions = [...sessions].sort((left, right) => right.updatedAt - left.updatedAt);

  return (
    <Drawer
      getContainer={false}
      onClose={onClose}
      open={open}
      title="历史记录"
      width={380}
    >
      {sortedSessions.length === 0 ? (
        <Empty description="还没有对话历史" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={sortedSessions}
          renderItem={(session) => (
            <List.Item>
              <Button
                block
                className="chat-history-item"
                onClick={() => onSelect(session.id)}
                type={session.id === currentSessionId ? "primary" : "default"}
              >
                <span className="chat-history-item__title">{session.title}</span>
                <span className="chat-history-item__meta">
                  {new Date(session.updatedAt).toLocaleString()}
                </span>
              </Button>
            </List.Item>
          )}
        />
      )}
    </Drawer>
  );
}
