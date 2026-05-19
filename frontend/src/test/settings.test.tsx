import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, beforeEach, expect, test, vi } from "vitest";

import {
  fetchTutorSettings,
  saveTutorSettings,
  testTutorSettings,
} from "../api/client";
import { SettingsPage } from "../pages/SettingsPage";

vi.mock("../api/client", () => ({
  fetchTutorSettings: vi.fn(),
  saveTutorSettings: vi.fn(),
  testTutorSettings: vi.fn(),
}));

const mockedFetchTutorSettings = vi.mocked(fetchTutorSettings);
const mockedSaveTutorSettings = vi.mocked(saveTutorSettings);
const mockedTestTutorSettings = vi.mocked(testTutorSettings);

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    value: vi.fn().mockImplementation((query: string) => ({
      addEventListener: vi.fn(),
      addListener: vi.fn(),
      dispatchEvent: vi.fn(),
      matches: false,
      media: query,
      onchange: null,
      removeEventListener: vi.fn(),
      removeListener: vi.fn(),
    })),
    writable: true,
  });
});

beforeEach(() => {
  mockedFetchTutorSettings.mockResolvedValue({
    base_url: "http://localhost:11434",
    has_api_key: true,
    model_name: "llama3.1",
    provider: "ollama",
  });
  mockedSaveTutorSettings.mockResolvedValue({
    base_url: "https://api.example.test/v1",
    has_api_key: true,
    model_name: "gpt-4o-mini",
    provider: "openai_compatible",
  });
  mockedTestTutorSettings.mockResolvedValue({
    message: "连接成功",
    ok: true,
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test("loads and displays existing tutor settings", async () => {
  render(<SettingsPage />);

  expect(await screen.findByText("AI 导师配置")).toBeInTheDocument();
  expect(await screen.findByText("Ollama")).toBeInTheDocument();
  expect(screen.getByDisplayValue("http://localhost:11434")).toBeInTheDocument();
  expect(screen.getByDisplayValue("llama3.1")).toBeInTheDocument();
  expect(screen.getByText("已保存 API Key")).toBeInTheDocument();
  expect(screen.getByLabelText("API Key")).toHaveValue("");
});

test("saves changed tutor settings with the entered API key", async () => {
  const user = userEvent.setup();

  render(<SettingsPage />);
  await screen.findByDisplayValue("http://localhost:11434");

  await selectProvider(user, "OpenAI-compatible");
  await user.clear(screen.getByLabelText("Base URL"));
  await user.type(screen.getByLabelText("Base URL"), "https://api.example.test/v1");
  await user.clear(screen.getByLabelText("Model Name"));
  await user.type(screen.getByLabelText("Model Name"), "gpt-4o-mini");
  await user.type(screen.getByLabelText("API Key"), "sk-test-key");
  await user.click(screen.getByRole("button", { name: "保存配置" }));

  expect(mockedSaveTutorSettings).toHaveBeenCalledWith({
    api_key: "sk-test-key",
    base_url: "https://api.example.test/v1",
    model_name: "gpt-4o-mini",
    provider: "openai_compatible",
  });
  expect(await screen.findAllByText("导师配置已保存")).not.toHaveLength(0);
});

test("keeps saved API key when saving without entering a new key", async () => {
  const user = userEvent.setup();

  mockedFetchTutorSettings.mockResolvedValue({
    base_url: "https://api.example.test/v1",
    has_api_key: true,
    model_name: "gpt-4o-mini",
    provider: "openai_compatible",
  });
  mockedSaveTutorSettings.mockResolvedValue({
    base_url: "https://api.example.test/v1",
    has_api_key: true,
    model_name: "gpt-4o-mini",
    provider: "openai_compatible",
  });

  render(<SettingsPage />);
  await screen.findByDisplayValue("https://api.example.test/v1");

  expect(screen.getByText("已保存 API Key")).toBeInTheDocument();
  expect(screen.getByLabelText("API Key")).toHaveValue("");
  expect(
    screen.getByPlaceholderText("留空表示不更新已保存的 API Key"),
  ).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "保存配置" }));

  expect(mockedSaveTutorSettings).toHaveBeenCalledWith({
    base_url: "https://api.example.test/v1",
    model_name: "gpt-4o-mini",
    provider: "openai_compatible",
  });
  expect(await screen.findAllByText("导师配置已保存")).not.toHaveLength(0);
  expect(screen.getByText("已保存 API Key")).toBeInTheDocument();
});

test("tests tutor connection and shows the result", async () => {
  const user = userEvent.setup();

  render(<SettingsPage />);
  await screen.findByDisplayValue("http://localhost:11434");

  await user.click(screen.getByRole("button", { name: "测试连接" }));

  await waitFor(() =>
    expect(mockedTestTutorSettings).toHaveBeenCalledWith({
      base_url: "http://localhost:11434",
      model_name: "llama3.1",
      provider: "ollama",
    }),
  );
  expect(await screen.findAllByText("连接成功")).not.toHaveLength(0);
});

async function selectProvider(
  user: ReturnType<typeof userEvent.setup>,
  optionName: string,
) {
  await user.click(screen.getByRole("combobox", { name: "Provider" }));
  await user.click(await screen.findByTitle(optionName));
}
