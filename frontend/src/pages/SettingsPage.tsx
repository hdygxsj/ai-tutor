import {
  Alert,
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  Select,
  Space,
  Typography,
  message,
} from "antd";
import { useEffect, useState } from "react";

import {
  fetchTutorSettings,
  saveTutorSettings,
  testTutorSettings,
} from "../api/client";
import type {
  TutorConnectionTestResult,
  TutorProvider,
  TutorSettingsUpdate,
} from "../types/learning";

interface TutorSettingsFormValues {
  provider: TutorProvider;
  base_url?: string;
  model_name?: string;
  api_key?: string;
}

const DEFAULT_FORM_VALUES: TutorSettingsFormValues = {
  provider: "fake",
  base_url: "",
  model_name: "",
  api_key: "",
};

const PROVIDER_OPTIONS = [
  { label: "Fake", value: "fake" },
  { label: "Ollama", value: "ollama" },
  { label: "OpenAI-compatible", value: "openai_compatible" },
];

export function SettingsPage() {
  const [form] = Form.useForm<TutorSettingsFormValues>();
  const [messageApi, contextHolder] = message.useMessage();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [hasSavedApiKey, setHasSavedApiKey] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<"success" | "error" | null>(null);
  const [testResult, setTestResult] =
    useState<TutorConnectionTestResult | null>(null);

  useEffect(() => {
    let active = true;

    async function loadSettings() {
      setLoading(true);
      setLoadError(null);

      try {
        const settings = await fetchTutorSettings();

        if (!active) {
          return;
        }

        form.setFieldsValue({
          provider: settings.provider,
          base_url: settings.base_url ?? "",
          model_name: settings.model_name ?? "",
          api_key: "",
        });
        setHasSavedApiKey(settings.has_api_key);
      } catch (error) {
        if (!active) {
          return;
        }

        setLoadError(errorMessage(error));
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadSettings();

    return () => {
      active = false;
    };
  }, [form]);

  const saveSettings = async () => {
    setSaving(true);
    setSaveStatus(null);

    try {
      const savedSettings = await saveTutorSettings(payloadFromForm());

      setHasSavedApiKey(savedSettings.has_api_key);
      form.setFieldsValue({ api_key: "" });
      setSaveStatus("success");
      void messageApi.success("导师配置已保存");
    } catch (error) {
      setSaveStatus("error");
      void messageApi.error(errorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await testTutorSettings(payloadFromForm());

      setTestResult(result);
      void messageApi.open({
        content: result.message,
        type: result.ok ? "success" : "warning",
      });
    } catch (error) {
      const messageText = errorMessage(error);

      setTestResult({ message: messageText, ok: false });
      void messageApi.error(messageText);
    } finally {
      setTesting(false);
    }
  };

  const payloadFromForm = (): TutorSettingsUpdate => {
    const values = form.getFieldsValue();

    return omitEmptyFields({
      provider: values.provider,
      base_url: values.base_url,
      model_name: values.model_name,
      api_key: values.api_key,
    });
  };

  return (
    <Space direction="vertical" size={24} style={{ width: "100%" }}>
      {contextHolder}
      <div>
        <Typography.Text type="secondary">设置</Typography.Text>
        <Typography.Title level={1} style={{ marginBottom: 8 }}>
          学习者偏好
        </Typography.Title>
        <Typography.Paragraph style={{ color: "#64748b", fontSize: 16 }}>
          管理本地学习偏好、学习节奏和工作区配置。
        </Typography.Paragraph>
      </div>

      <Alert
        description="M1.1 仍使用默认 tenant 与默认 workspace；这里仅配置本地 AI 导师 provider，不改变确定性的 M1 教师闭环。"
        message="默认工作区"
        showIcon
        type="info"
      />

      <Card loading={loading} title="AI 导师配置">
        {loadError ? (
          <Alert
            description={loadError}
            message="导师配置加载失败"
            showIcon
            style={{ marginBottom: 16 }}
            type="error"
          />
        ) : null}

        {saveStatus === "success" ? (
          <Alert
            message="导师配置已保存"
            showIcon
            style={{ marginBottom: 16 }}
            type="success"
          />
        ) : saveStatus === "error" ? (
          <Alert
            message="导师配置保存失败"
            showIcon
            style={{ marginBottom: 16 }}
            type="error"
          />
        ) : null}

        {testResult ? (
          <Alert
            message={testResult.message}
            showIcon
            style={{ marginBottom: 16 }}
            type={testResult.ok ? "success" : "error"}
          />
        ) : null}

        <Descriptions column={1} size="small" style={{ marginBottom: 24 }}>
          <Descriptions.Item label="Tenant">default</Descriptions.Item>
          <Descriptions.Item label="Workspace">default</Descriptions.Item>
          <Descriptions.Item label="说明">
            配置只影响导师连接参数；API Key 只会保存到后端，不会在读取时回填。
          </Descriptions.Item>
        </Descriptions>

        <Form
          form={form}
          initialValues={DEFAULT_FORM_VALUES}
          layout="vertical"
          onFinish={() => void saveSettings()}
        >
          <Form.Item label="Provider" name="provider">
            <Select aria-label="Provider" options={PROVIDER_OPTIONS} />
          </Form.Item>

          <Form.Item label="Base URL" name="base_url">
            <Input aria-label="Base URL" placeholder="http://localhost:11434" />
          </Form.Item>

          <Form.Item label="Model Name" name="model_name">
            <Input aria-label="Model Name" placeholder="llama3.1" />
          </Form.Item>

          <Form.Item
            extra={hasSavedApiKey ? "已保存 API Key" : undefined}
            label="API Key"
            name="api_key"
          >
            <Input.Password
              aria-label="API Key"
              autoComplete="new-password"
              placeholder="留空表示不更新已保存的 API Key"
            />
          </Form.Item>

          <Space wrap>
            <Button htmlType="submit" loading={saving} type="primary">
              保存配置
            </Button>
            <Button loading={testing} onClick={() => void testConnection()}>
              测试连接
            </Button>
          </Space>
        </Form>
      </Card>
    </Space>
  );
}

function omitEmptyFields(payload: TutorSettingsUpdate): TutorSettingsUpdate {
  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== ""),
  ) as TutorSettingsUpdate;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "请求失败，请稍后重试。";
}
