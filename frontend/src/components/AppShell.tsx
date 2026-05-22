import {
  BookOutlined,
  CheckSquareOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  MessageOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { ConfigProvider, Layout, Menu, Typography } from "antd";
import type { MenuProps } from "antd";
import type { ReactNode } from "react";
import type { AppMenuKey } from "../app-routes";
import "./AppShell.css";

const { Header, Content } = Layout;

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
    key: "experiments",
    icon: <ExperimentOutlined />,
    label: "实验运行",
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
  const isChatPage = activeKey === "chat";

  return (
    <Layout className="app-shell">
      <Header
        className="app-shell__header"
        style={{
          height: "auto",
          lineHeight: "normal",
          minHeight: 72,
          overflow: "visible",
          padding: "14px 28px",
        }}
      >
        <div className="app-shell__brand">
          <Typography.Title className="app-shell__title" level={4}>
            AI Dream
          </Typography.Title>
          <Typography.Text className="app-shell__subtitle" type="secondary">
            Agent 课程工作台
          </Typography.Text>
        </div>
        <ConfigProvider
          theme={{
            components: {
              Menu: {
                activeBarBorderWidth: 0,
                activeBarHeight: 0,
                horizontalItemHoverBg: "#f1f5f9",
                horizontalItemSelectedBg: "#eff6ff",
                horizontalItemSelectedColor: "#2563eb",
              },
            },
          }}
        >
          <Menu
            className="app-shell__menu"
            items={menuItems}
            mode="horizontal"
            onClick={({ key }) => onSelect(key as AppMenuKey)}
            selectedKeys={[activeKey]}
          />
        </ConfigProvider>
      </Header>
      <Content
        className={`app-shell__content ${isChatPage ? "app-shell__content--chat" : ""}`}
      >
        <div
          className={`app-shell__content-inner ${
            isChatPage ? "app-shell__content-inner--chat" : ""
          }`}
        >
          {children}
        </div>
      </Content>
    </Layout>
  );
}
