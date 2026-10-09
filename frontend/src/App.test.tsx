import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const vehicles = [
  {
    trimId: "model3-rwd-cn-current",
    displayName: "Model 3 后轮驱动版",
    model: "Model 3",
  },
  {
    trimId: "model3-lr-rwd-cn-current",
    displayName: "Model 3 长续航后轮驱动版",
    model: "Model 3",
  },
];

const answer = {
  answerId: "answer-1",
  answer: "打开充电端口\n\n车辆处于驻车挡时，可以按下充电电缆按钮。",
  boundaryResult: null,
  citations: [
    {
      id: "tesla-model3-charging",
      title: "Tesla 中国 Model 3 车主手册",
      section: "打开充电端口",
      url: "https://www.tesla.cn/ownersmanual/model3/zh_cn/example.html",
      retrievedAt: "2026-10-09",
    },
  ],
  speechText: "车辆处于驻车挡时，可以按下充电电缆按钮。",
  fallbackReason: null,
};

function response(payload: unknown, ok = true): Response {
  return {
    ok,
    json: async () => payload,
  } as Response;
}

function mockSpeech() {
  const speak = vi.fn();
  const cancel = vi.fn();
  const pause = vi.fn();
  const resume = vi.fn();
  class MockUtterance {
    lang = "";
    rate = 1;
    onend: (() => void) | null = null;
    onerror: (() => void) | null = null;

    constructor(public text: string) {}
  }
  vi.stubGlobal("SpeechSynthesisUtterance", MockUtterance);
  Object.defineProperty(window, "speechSynthesis", {
    configurable: true,
    value: { speak, cancel, pause, resume },
  });
  return { speak, cancel, pause, resume };
}

describe("车书 AI", () => {
  beforeEach(() => {
    mockSpeech();
  });

  it("loads trims and completes the charging-port answer flow", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(vehicles))
      .mockResolvedValueOnce(response(answer));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<App />);

    expect(await screen.findByRole("option", { name: "后轮驱动版" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "如何打开充电口？" }));
    await user.click(screen.getByRole("button", { name: "发送问题" }));

    expect(await screen.findByText(/车辆处于驻车挡时，可以按下充电电缆按钮/)).toBeVisible();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/answers",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          question: "如何打开充电口？",
          trimId: "model3-rwd-cn-current",
        }),
      }),
    );
    expect(window.speechSynthesis.speak).toHaveBeenCalledTimes(1);
  });

  it("opens the official citation in a separate responsive panel", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(response(vehicles)).mockResolvedValueOnce(response(answer)),
    );
    const user = userEvent.setup();
    render(<App />);

    await screen.findByRole("option", { name: "后轮驱动版" });
    await user.click(screen.getByRole("button", { name: "如何打开充电口？" }));
    await user.click(screen.getByRole("button", { name: "发送问题" }));
    await user.click(await screen.findByRole("button", { name: /打开充电端口/ }));

    expect(screen.getByRole("complementary", { name: "官方资料来源" })).toBeVisible();
    expect(screen.getByRole("link", { name: /打开完整官方手册/ })).toHaveAttribute(
      "href",
      answer.citations[0].url,
    );
    await user.click(screen.getByRole("button", { name: "关闭来源详情" }));
    expect(screen.queryByRole("complementary", { name: "官方资料来源" })).not.toBeInTheDocument();
  });

  it("records and switches feedback", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(vehicles))
      .mockResolvedValueOnce(response(answer))
      .mockResolvedValueOnce(response({ value: "up" }))
      .mockResolvedValueOnce(response({ value: "down" }));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);

    await screen.findByRole("option", { name: "后轮驱动版" });
    await user.click(screen.getByRole("button", { name: "如何打开充电口？" }));
    await user.click(screen.getByRole("button", { name: "发送问题" }));
    const up = await screen.findByRole("button", { name: "点赞" });
    const down = screen.getByRole("button", { name: "点踩" });

    await user.click(up);
    await waitFor(() => expect(up).toHaveAttribute("aria-pressed", "true"));
    await user.click(down);
    await waitFor(() => expect(down).toHaveAttribute("aria-pressed", "true"));
    expect(up).toHaveAttribute("aria-pressed", "false");
  });

  it("keeps text input usable when microphone recognition is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(vehicles)));
    const user = userEvent.setup();
    render(<App />);

    await screen.findByRole("option", { name: "后轮驱动版" });
    await user.click(screen.getByRole("button", { name: "麦克风提问" }));

    expect(screen.getByText(/语音识别将在后续版本接入/)).toBeVisible();
    expect(screen.getByPlaceholderText(/询问 Model 3/)).toBeEnabled();
  });

  it("shows a recoverable API error", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(response(vehicles))
        .mockResolvedValueOnce(response({ detail: "后端暂时不可用" }, false)),
    );
    const user = userEvent.setup();
    render(<App />);

    await screen.findByRole("option", { name: "后轮驱动版" });
    await user.click(screen.getByRole("button", { name: "如何打开充电口？" }));
    await user.click(screen.getByRole("button", { name: "发送问题" }));

    expect(await screen.findByText("暂时无法连接问答服务")).toBeVisible();
    expect(screen.getByText(/后端暂时不可用/)).toBeVisible();
    expect(screen.getByRole("button", { name: "重试" })).toBeEnabled();
  });
});
