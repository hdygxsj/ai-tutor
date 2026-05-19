import {
  BookOutlined,
  CheckSquareOutlined,
  DashboardOutlined,
  MessageOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Layout, Menu, Typography } from "antd";
import type { MenuProps } from "antd";
import type { ReactNode } from "react";

const { Header, Sider, Content } = Layout;

export type AppMenuKey =
  | "dashboard"
  | "chat"
  | "learning"
  | "assignments"
  | "settings";

const menuItems: MenuProps["items"] = [
  {
    key: "dashboard",
    icon: <DashboardOutlined />,
    label: "Dashboard",
  },
  {
    key: "chat",
    icon: <MessageOutlined />,
    label: "AI 导师",
  },
  {
    key: "learning",
    icon: <BookOutlined />,
    label: "学习计划",
  },
  {
    key: "assignments",
    icon: <CheckSquareOutlined />,
    label: "作业反馈",
  },
  {
    key: "settings",
    icon: <SettingOutlined />,
    label: "设置",
  },
];

interface AppShellProps {
  activeKey: AppMenuKey;
  children: ReactNode;
  onSelect: (key: AppMenuKey) => void;
}

export function AppShell({ activeKey, children, onSelect }: AppShellProps) {
  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f7fb" }}>
      <Sider
        breakpoint="lg"
        collapsedWidth="0"
        style={{
          background: "#0f172a",
          boxShadow: "8px 0 24px rgba(15, 23, 42, 0.08)",
        }}
        width={248}
      >
        <div style={{ padding: 24 }}>
          <Typography.Title
            level={3}
            style={{ color: "#fff", margin: 0, letterSpacing: 0.2 }}
          >
            AI Dream
          </Typography.Title>
          <Typography.Text style={{ color: "rgba(255, 255, 255, 0.62)" }}>
            个人学习闭环
          </Typography.Text>
        </div>
        <Menu
          items={menuItems}
          mode="inline"
          onClick={({ key }) => onSelect(key as AppMenuKey)}
          selectedKeys={[activeKey]}
          style={{ background: "transparent", borderInlineEnd: 0 }}
          theme="dark"
        />
      </Sider>
      <Layout>
        <Header
          style={{
            alignItems: "center",
            background: "#fff",
            borderBottom: "1px solid #edf0f5",
            display: "flex",
            height: 72,
            paddingInline: 32,
          }}
        >
          <Typography.Text strong style={{ color: "#334155", fontSize: 16 }}>
            机器学习教师 Agent
          </Typography.Text>
        </Header>
        <Content style={{ padding: 32 }}>
          <div style={{ margin: "0 auto", maxWidth: 1120 }}>{children}</div>
        </Content>
      </Layout>
    </Layout>
  );
}
