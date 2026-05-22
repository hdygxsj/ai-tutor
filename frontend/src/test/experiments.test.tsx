import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, beforeEach, expect, test, vi } from "vitest";

import { runMinimalExperiment } from "../api/client";
import { ExperimentsPage } from "../pages/ExperimentsPage";

vi.mock("../api/client", () => ({
  runMinimalExperiment: vi.fn(),
}));

const mockedRunMinimalExperiment = vi.mocked(runMinimalExperiment);

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
  mockedRunMinimalExperiment.mockReset();
});

afterEach(() => {
  cleanup();
});

test("renders the experiments page and explains the M2.2 minimal runner", () => {
  render(<ExperimentsPage />);

  expect(screen.getByRole("heading", { name: "实验运行" })).toBeInTheDocument();
  expect(
    screen.getByText(/M2\.2 运行最小 deterministic 实验/),
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "运行最小实验" })).toBeEnabled();
});

test("runs the minimal experiment when clicking the run button", async () => {
  const user = userEvent.setup();

  mockedRunMinimalExperiment.mockResolvedValue(sampleResult());

  render(<ExperimentsPage />);
  await user.click(screen.getByRole("button", { name: "运行最小实验" }));

  expect(mockedRunMinimalExperiment).toHaveBeenCalledTimes(1);
  expect(await screen.findByText("run-m2-001")).toBeInTheDocument();
});

test("renders returned metrics logs and artifacts", async () => {
  const user = userEvent.setup();

  mockedRunMinimalExperiment.mockResolvedValue(sampleResult());

  render(<ExperimentsPage />);
  await user.click(screen.getByRole("button", { name: "运行最小实验" }));

  expect(await screen.findByText("run-m2-001")).toBeInTheDocument();
  expect(screen.getByText("passed")).toBeInTheDocument();
  expect(metricCard("initial_loss")).toHaveTextContent("1.25");
  expect(metricCard("final_loss")).toHaveTextContent("0.42");
  expect(metricCard("improvement")).toHaveTextContent("0.83");
  expect(screen.getByText("epoch 1 loss=1.25")).toBeInTheDocument();
  expect(screen.getByText("epoch 2 loss=0.42")).toBeInTheDocument();
  expect(screen.getByText("metrics.json")).toBeInTheDocument();
  expect(screen.getByText("log.txt")).toBeInTheDocument();
});

test("shows a visible error after API failure and allows retry", async () => {
  const user = userEvent.setup();

  mockedRunMinimalExperiment
    .mockRejectedValueOnce(new Error("runner unavailable"))
    .mockResolvedValueOnce(sampleResult());

  render(<ExperimentsPage />);

  const runButton = screen.getByRole("button", { name: "运行最小实验" });

  await user.click(runButton);

  expect(await screen.findByText("实验运行失败")).toBeInTheDocument();
  expect(screen.getByText("runner unavailable")).toBeInTheDocument();
  expect(runButton).toBeEnabled();

  await user.click(runButton);

  await waitFor(() => expect(mockedRunMinimalExperiment).toHaveBeenCalledTimes(2));
  expect(await screen.findByText("run-m2-001")).toBeInTheDocument();
});

test("clears the previous result when a later run fails", async () => {
  const user = userEvent.setup();

  mockedRunMinimalExperiment
    .mockResolvedValueOnce(sampleResult())
    .mockRejectedValueOnce(new Error("runner unavailable"));

  render(<ExperimentsPage />);

  const runButton = screen.getByRole("button", { name: "运行最小实验" });

  await user.click(runButton);

  expect(await screen.findByText("run-m2-001")).toBeInTheDocument();
  expect(metricCard("initial_loss")).toHaveTextContent("1.25");

  await user.click(runButton);

  expect(await screen.findByText("实验运行失败")).toBeInTheDocument();
  expect(screen.getByText("runner unavailable")).toBeInTheDocument();
  expect(screen.queryByText("run-m2-001")).not.toBeInTheDocument();
  expect(screen.queryByText("initial_loss")).not.toBeInTheDocument();
  expect(screen.queryByText("metrics.json")).not.toBeInTheDocument();
});

function metricCard(title: string): HTMLElement {
  const titleElement = screen.getByText(title);
  const card = titleElement.closest(".ant-card");

  expect(card).not.toBeNull();

  return card as HTMLElement;
}

function sampleResult() {
  return {
    artifacts: [
      {
        content_type: "application/json",
        name: "metrics.json",
        path: "artifacts/experiments/run-m2-001/metrics.json",
      },
      {
        content_type: "text/plain",
        name: "log.txt",
        path: "artifacts/experiments/run-m2-001/log.txt",
      },
    ],
    logs: "epoch 1 loss=1.25\nepoch 2 loss=0.42",
    metrics: {
      final_loss: 0.42,
      improvement: 0.83,
      initial_loss: 1.25,
    },
    run_id: "run-m2-001",
    status: "passed",
  };
}
