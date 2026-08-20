import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";
import {
  clearAllTestData,
  executeScenarioStep,
  exportTrace,
  generateTestData,
  getChatHistory,
  getUserIdentities,
  getUserProfile,
  getTestDataStatus,
  importTestData,
  isNavigationConfirmationText,
  updateUserIdentity,
} from "../api/smartEvCockpit";
import type {
  ActorId,
  ScenarioResponse,
  SeatPosition,
  TestDataStatus,
  UserIdentity,
  UserProfileResponse,
} from "../types/api";

vi.mock("../api/smartEvCockpit", () => ({
  executeScenarioStep: vi.fn(),
  clearAllTestData: vi.fn(),
  exportTrace: vi.fn(),
  generateTestData: vi.fn(),
  getChatHistory: vi.fn(),
  getUserIdentities: vi.fn(),
  getUserProfile: vi.fn(),
  getTestDataStatus: vi.fn(),
  importTestData: vi.fn(),
  isNavigationConfirmationText: vi.fn(),
  updateUserIdentity: vi.fn(),
}));

const liveResponse: ScenarioResponse = {
  assistant_reply: "Warming cabin from live memory.",
  trace_id: "trace_live_123",
  live_backend: "powercontext_builtin",
  powercontext_connected: true,
  operations: [],
  memory_hits: [
    {
      memory_id: "mem_live",
      content: "driver prefers a warmer cabin on cold mornings",
      memory_kind: "cabin_control_preference",
      visibility: "public_demo",
      lifecycle_status: "active",
      hidden_fields: [],
      score: 0.87,
    },
  ],
  vehicle_state: { cabin_temp_c: 24 },
  vehicle_state_diff: [{ field: "cabin_temp_c", before: 22, after: 24 }],
  privacy_report: { redaction_count: 0 },
  recommendations: [{ label: "Warm cabin", reason_code: "cold_cabin_preference" }],
  evidence: {
    request: { actor_id: "driver_primary" },
    privacy: { redaction_count: 0 },
    data_source: "powercontext_builtin",
    operations: [
      {
        type: "SEARCH",
        query: "cold cabin",
        filters: { actor_id: "driver_primary" },
        hit_count: 1,
      },
    ],
    memory_hits: [{ memory_id: "mem_live", score: 0.87 }],
    decision: { selected_memory_ids: ["mem_live"] },
    vehicle_action: { diff: [{ field: "cabin_temp_c", before: 22, after: 24 }] },
    latency_ms: 184,
  },
};

const idleTestDataStatus: TestDataStatus = {
  state: "idle",
  dataset_id: null,
  dataset_path: null,
  locale: "zh",
  generated_count: 0,
  imported_count: 0,
  deleted_count: 0,
  skipped_count: 0,
  failed_count: 0,
  last_error: null,
};

const generatedTestDataStatus: TestDataStatus = {
  state: "generated",
  dataset_id: "smart_ev_cockpit_20260708_1200_seed42",
  dataset_path: "/tmp/generated.jsonl",
  locale: "en",
  generated_count: 1200,
  imported_count: 0,
  deleted_count: 0,
  skipped_count: 0,
  failed_count: 0,
  last_error: null,
};

function chatMessage(
  id: string,
  actorId: ActorId,
  seatPosition: SeatPosition,
  role: "user" | "assistant",
  text: string,
  userId = actorId,
) {
  return {
    id,
    session_id: "demo_session_001",
    actor_id: actorId,
    user_id: userId,
    seat_position: seatPosition,
    role,
    text,
    trace_id: `trace_${id}`,
    created_at: "2026-07-09T10:00:00Z",
  };
}

const importingTestDataStatus: TestDataStatus = {
  ...generatedTestDataStatus,
  state: "importing",
  imported_count: 0,
};

const importedTestDataStatus: TestDataStatus = {
  ...generatedTestDataStatus,
  state: "imported",
  imported_count: 1200,
};

const defaultIdentities: UserIdentity[] = [
  {
    actor_id: "driver_primary",
    seat_position: "front_left",
    user_id: "driver_primary",
    display_name: "驾驶员",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
  {
    actor_id: "passenger_front",
    seat_position: "front_right",
    user_id: "passenger_front",
    display_name: "前排乘客",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
  {
    actor_id: "child_rear_left",
    seat_position: "rear_left",
    user_id: "child_rear_left",
    display_name: "儿童",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
];

const emptyProfile: UserProfileResponse = {
  profile: {
    identity: defaultIdentities[0],
    primary_memory: null,
    memory_kind_counts: {},
    memories: [],
  },
};

async function switchToEnglish(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "EN" }));
}

describe("App live API integration", () => {
  beforeEach(() => {
    vi.mocked(executeScenarioStep).mockReset();
    vi.mocked(clearAllTestData).mockReset();
    vi.mocked(exportTrace).mockReset();
    vi.mocked(generateTestData).mockReset();
    vi.mocked(getChatHistory).mockReset();
    vi.mocked(getUserIdentities).mockReset();
    vi.mocked(getUserProfile).mockReset();
    vi.mocked(getTestDataStatus).mockReset();
    vi.mocked(importTestData).mockReset();
    vi.mocked(isNavigationConfirmationText).mockReset();
    vi.mocked(updateUserIdentity).mockReset();
    vi.mocked(getChatHistory).mockResolvedValue({ messages: [] });
    vi.mocked(getUserIdentities).mockResolvedValue({ identities: defaultIdentities });
    vi.mocked(getUserProfile).mockResolvedValue(emptyProfile);
    vi.mocked(getTestDataStatus).mockResolvedValue(idleTestDataStatus);
    vi.mocked(exportTrace).mockResolvedValue({ recent_operations: [] });
    vi.mocked(generateTestData).mockResolvedValue(generatedTestDataStatus);
    vi.mocked(importTestData).mockResolvedValue(importingTestDataStatus);
    vi.mocked(isNavigationConfirmationText).mockImplementation((text) =>
      text.toLocaleLowerCase().includes("confirm navigation"),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not render fake memory hits before a live backend response", () => {
    render(<App />);

    expect(screen.queryByText("mem_winter")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Developer evidence drawer")).not.toBeInTheDocument();
  });

  it("renders MemoFox as an active cockpit companion on the first demo scene", () => {
    render(<App />);

    expect(
      screen.getByLabelText("忆灵：我把这组座舱温度和座椅设置记成可复用偏好。"),
    ).toBeInTheDocument();
  });

  it("renders test data controls for demo dataset setup", () => {
    render(<App />);

    expect(screen.getByRole("spinbutton", { name: /记忆数量/ })).toHaveValue(1200);
    expect(
      screen.getByRole("button", { name: /生成并导入 1200 条记忆/ }),
    ).toHaveTextContent(
      /^数据生成$/,
    );
    expect(
      screen.getByRole("button", { name: /清空 PowerContext 数据库全部记忆/ }),
    ).toHaveTextContent(/^数据清理$/);
    expect(
      screen.queryByRole("button", { name: /导入到 PowerContext/ }),
    ).not.toBeInTheDocument();
  });

  it("opens the legacy PowerMem PPT from the top-right entry", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /打开旧版 PowerMem PPT/ }));

    expect(
      screen.getByRole("dialog", { name: "旧版 PowerMem 汽车智能座舱记忆方案" }),
    ).toBeInTheDocument();
    expect(screen.getByTitle("Legacy PowerMem smart EV cockpit PPT")).toHaveAttribute(
      "src",
      "/legacy-memory-layer-smart-ev-cockpit-deck.html",
    );
  });

  it("uses the active Chinese locale when generating demo data", async () => {
    vi.mocked(generateTestData).mockResolvedValue({
      ...generatedTestDataStatus,
      dataset_id: "smart_ev_cockpit_20260708_1200_seed42_zh",
      locale: "zh",
    });
    const user = userEvent.setup();
    render(<App />);

    await user.click(
      screen.getByRole("button", { name: /生成并导入 1200 条记忆/ }),
    );

    expect(generateTestData).toHaveBeenCalledWith({
      count: 1200,
      seed: 42,
      locale: "zh",
    });
  });

  it("uses the configured count when generating demo data", async () => {
    vi.mocked(generateTestData).mockResolvedValue({
      ...generatedTestDataStatus,
      dataset_id: "smart_ev_cockpit_20260712_080910_250_seed42_zh_abc123ef",
      generated_count: 250,
      locale: "zh",
    });
    const user = userEvent.setup();
    render(<App />);

    await user.clear(screen.getByRole("spinbutton", { name: /记忆数量/ }));
    await user.type(screen.getByRole("spinbutton", { name: /记忆数量/ }), "250");
    await user.click(
      screen.getByRole("button", { name: /生成并导入 250 条记忆/ }),
    );

    expect(generateTestData).toHaveBeenCalledWith({
      count: 250,
      seed: 42,
      locale: "zh",
    });
  });

  it("generates and imports demo data from one action", async () => {
    vi.mocked(generateTestData).mockResolvedValue({
      ...generatedTestDataStatus,
      locale: "zh",
    });
    const user = userEvent.setup();
    render(<App />);

    await user.click(
      screen.getByRole("button", { name: /生成并导入 1200 条记忆/ }),
    );

    await waitFor(() =>
      expect(importTestData).toHaveBeenCalledWith({
        dataset_id: generatedTestDataStatus.dataset_id,
        apply: true,
        max_workers: 3,
      }),
    );
    expect(generateTestData).toHaveBeenCalledWith({
      count: 1200,
      seed: 42,
      locale: "zh",
    });
    expect(vi.mocked(generateTestData).mock.invocationCallOrder[0]).toBeLessThan(
      vi.mocked(importTestData).mock.invocationCallOrder[0],
    );
  });

  it("keeps generated data clearable when automatic import fails", async () => {
    vi.mocked(generateTestData).mockResolvedValue({
      ...generatedTestDataStatus,
      locale: "zh",
    });
    vi.mocked(importTestData).mockRejectedValue(new Error("Import failed"));
    const user = userEvent.setup();
    render(<App />);

    await user.click(
      screen.getByRole("button", { name: /生成并导入 1200 条记忆/ }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Import failed");
    expect(screen.getByText(generatedTestDataStatus.dataset_id!)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /清空 PowerContext 数据库全部记忆/ }),
    ).toBeEnabled();
  });

  it("clears the entire PowerContext database without a current dataset", async () => {
    vi.mocked(clearAllTestData).mockResolvedValue({
      ...idleTestDataStatus,
      state: "deleted",
      deleted_count: 42,
    });
    const user = userEvent.setup();
    render(<App />);

    const clearButton = await screen.findByRole("button", {
      name: /清空 PowerContext 数据库全部记忆/,
    });
    expect(clearButton).toBeEnabled();
    await user.click(clearButton);

    expect(clearAllTestData).toHaveBeenCalledWith({ apply: true });
  });

  it("renders the cockpit stage and default projection inside the infotainment display", () => {
    render(<App />);

    expect(screen.getByLabelText("智能电动车座舱场景")).toBeInTheDocument();
    expect(
      screen.queryByLabelText("PowerContext 全息证据投影"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByLabelText("车机屏幕 PowerContext 摘要"),
    ).toBeInTheDocument();
    expect(screen.getByText("建立偏好")).toBeInTheDocument();
  });

  it("defaults to Chinese copy with porcelain white interior selected from a dropdown", () => {
    render(<App />);

    expect(document.documentElement.lang).toBe("zh-CN");
    expect(screen.getByRole("button", { name: "中文" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    const interiorSelect = screen.getByRole("combobox", { name: "内饰颜色选择" });
    expect(interiorSelect).toHaveValue("ivory");
    expect(screen.getByLabelText("智能电动车座舱场景")).toHaveAttribute(
      "data-interior",
      "ivory",
    );
  });

  it("switches visible cockpit copy between English and Chinese", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(
      screen.getByRole("button", { name: /生成并导入 1200 条记忆/ }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("智能电动车座舱场景")).toBeInTheDocument();
    expect(screen.getByText("建立偏好")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "语音指令" })).toHaveValue(
      "我夏天上车一般 23C，座椅加热 0 档。",
    );

    const stage = screen.getByLabelText("智能电动车座舱场景");
    const seatSelector = within(stage).getByLabelText("座位乘员选择");
    expect(within(seatSelector).getByRole("button", { name: "驾驶员" })).toBeInTheDocument();
    expect(within(seatSelector).getByRole("button", { name: "前排乘客" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^发送$/ })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /打开实时证据/ }));

    expect(screen.getByRole("dialog", { name: "实时证据控制台" })).toBeInTheDocument();
    expect(screen.getByText("PowerContext 记忆流")).toBeInTheDocument();
    expect(screen.getByText("车辆上下文")).toBeInTheDocument();
    expect(screen.getByText("推荐")).toBeInTheDocument();
    expect(screen.getByLabelText("记忆生命周期时间线")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /关闭证据/ }));

    await user.click(screen.getByRole("button", { name: "EN" }));

    expect(screen.getByLabelText("Smart EV cockpit scene")).toBeInTheDocument();
    expect(screen.getByText("Preference capture")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Utterance" })).toHaveValue(
      "I usually set 23C and seat heat level 0 when I get in during summer.",
    );
  });

  it("hides live evidence sections behind an entry point", async () => {
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    expect(screen.getByRole("button", { name: /open live evidence/i })).toBeInTheDocument();
    expect(screen.queryByLabelText("Cockpit status")).not.toBeInTheDocument();
    expect(screen.queryByText("PowerContext Memory Flow")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Memory lifecycle timeline")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /open live evidence/i }));

    expect(screen.getByRole("dialog", { name: /live evidence console/i })).toBeInTheDocument();
    expect(screen.getByLabelText("Cockpit status")).toBeInTheDocument();
    expect(screen.getByText("PowerContext Memory Flow")).toBeInTheDocument();
    expect(screen.getByLabelText("Memory lifecycle timeline")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /close evidence/i }));

    expect(
      screen.queryByRole("dialog", { name: /live evidence console/i }),
    ).not.toBeInTheDocument();
  });

  it("places commands in the cockpit space instead of crowding the top bar", () => {
    render(<App />);

    const dataBar = screen.getByLabelText("顶部数据命令栏");
    const stage = screen.getByLabelText("智能电动车座舱场景");
    const seatSelector = within(stage).getByLabelText("座位乘员选择");
    const manualKeys = within(stage).getByLabelText("座舱手动按键");

    expect(
      dataBar.compareDocumentPosition(stage) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      within(dataBar).getByRole("button", { name: /生成并导入 1200 条记忆/ }),
    ).toBeInTheDocument();
    expect(
      within(dataBar).getByRole("button", {
        name: /清空 PowerContext 数据库全部记忆/,
      }),
    ).toBeInTheDocument();
    expect(
      within(dataBar).queryByRole("button", { name: /导入到 PowerContext/ }),
    ).not.toBeInTheDocument();
    expect(
      within(dataBar).getByRole("button", { name: /打开实时证据/ }),
    ).toBeInTheDocument();
    expect(within(dataBar).queryByRole("button", { name: /重置/ })).not.toBeInTheDocument();
    expect(within(dataBar).queryByRole("button", { name: "驾驶员" })).not.toBeInTheDocument();

    expect(within(seatSelector).getByRole("button", { name: "驾驶员" })).toBeInTheDocument();
    expect(within(seatSelector).getByRole("button", { name: "前排乘客" })).toBeInTheDocument();
    expect(within(seatSelector).getByRole("button", { name: "儿童" })).toBeInTheDocument();
    expect(within(manualKeys).getByRole("button", { name: /重置/ })).toBeInTheDocument();
    expect(within(manualKeys).getByRole("button", { name: /下一个/ })).toBeInTheDocument();
    expect(manualKeys.querySelector(".manual-cockpit-keys__day")).toBeNull();
    expect(within(manualKeys).queryByText(/场景/)).not.toBeInTheDocument();
    expect(
      within(stage).getByRole("combobox", { name: "内饰颜色选择" }),
    ).toHaveValue("ivory");
    expect(within(stage).getByLabelText("PowerContext 全景车机屏幕")).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", {
      name: /cockpit memory command center/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders voice commands as a floating chat history", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue(liveResponse);
    vi.mocked(getChatHistory)
      .mockResolvedValueOnce({
        messages: [
          chatMessage(
            "chat_driver_1",
            "driver_primary",
            "front_left",
            "user",
            "带我去公司，并保持座舱安静。",
          ),
          chatMessage(
            "chat_driver_2",
            "driver_primary",
            "front_left",
            "user",
            "我觉得有点冷。",
          ),
        ],
      })
      .mockResolvedValueOnce({
        messages: [
          chatMessage(
            "chat_driver_1",
            "driver_primary",
            "front_left",
            "user",
            "带我去公司，并保持座舱安静。",
          ),
          chatMessage(
            "chat_driver_2",
            "driver_primary",
            "front_left",
            "user",
            "我觉得有点冷。",
          ),
          chatMessage(
            "chat_driver_3",
            "driver_primary",
            "front_left",
            "user",
            "今天车里有点冷。",
          ),
          chatMessage(
            "chat_driver_4",
            "driver_primary",
            "front_left",
            "assistant",
            "Warming cabin from live memory.",
          ),
        ],
      });
    const user = userEvent.setup();
    render(<App />);

    const stage = screen.getByLabelText("智能电动车座舱场景");
    const floatingChat = within(stage).getByRole("region", {
      name: "悬浮语音聊天",
    });
    const chatLog = within(floatingChat).getByRole("log", {
      name: "最近对话",
    });

    expect(floatingChat).toHaveAttribute("data-layout", "floating-chat");
    expect(floatingChat).toHaveAttribute("data-anchor-actor", "driver_primary");
    expect(chatLog).toHaveAttribute("data-scrollable", "history");
    expect(chatLog).toHaveAttribute("data-scrollbar", "visible");
    expect(chatLog).toHaveAttribute("tabindex", "0");
    expect(
      await within(chatLog).findByText("带我去公司，并保持座舱安静。"),
    ).toBeInTheDocument();
    expect(within(chatLog).getByText("我觉得有点冷。")).toBeInTheDocument();

    const utterance = within(floatingChat).getByRole("textbox", {
      name: "语音指令",
    });
    await user.clear(utterance);
    await user.type(utterance, "今天车里有点冷。");
    await user.click(within(floatingChat).getByRole("button", { name: /^发送$/ }));

    expect(executeScenarioStep).toHaveBeenCalledWith(
      expect.not.objectContaining({ act_key: expect.any(String) }),
    );
    expect(await within(chatLog).findByText("今天车里有点冷。")).toBeInTheDocument();
    expect(await within(chatLog).findByText("Warming cabin from live memory.")).toBeInTheDocument();
    expect(within(floatingChat).queryByText("提交一句语音指令，启动实时 PowerContext 追踪。")).not.toBeInTheDocument();
  });

  it("labels free-form preference chat from the real PowerContext ADD operation", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue({
      ...liveResponse,
      act_key: "Chat",
      assistant_reply: "已记住你喜欢咖啡。",
      trace_id: "trace_chat_add",
      operations: [
        { type: "CHAT" },
        { type: "ADD", memory_ids: ["mem_coffee"] },
        { type: "SEARCH" },
      ],
    });
    const user = userEvent.setup();
    render(<App />);

    const floatingChat = within(
      screen.getByLabelText("智能电动车座舱场景"),
    ).getByRole("region", { name: "悬浮语音聊天" });
    const utterance = within(floatingChat).getByRole("textbox", {
      name: "语音指令",
    });
    await user.clear(utterance);
    await user.type(utterance, "I like coffee");
    await user.click(within(floatingChat).getByRole("button", { name: /^发送$/ }));

    expect(executeScenarioStep).toHaveBeenCalledWith({
      actor_id: "driver_primary",
      user_id: "driver_primary",
      seat_position: "front_left",
      text: "I like coffee",
      session_id: "demo_session_001",
    });
    expect(await screen.findByText("PowerContext ADD + LLM")).toBeInTheDocument();
  });

  it("keeps the cockpit visible when a random chat response omits evidence arrays", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue({
      act_key: "Chat",
      assistant_reply: "我可以继续作为座舱助手回答这个随机问题。",
      trace_id: "trace_random_chat",
      live_backend: "powercontext_builtin",
      powercontext_connected: true,
      vehicle_state: {},
      evidence: {},
    } as ScenarioResponse);
    const user = userEvent.setup();
    render(<App />);

    const stage = screen.getByLabelText("智能电动车座舱场景");
    const floatingChat = within(stage).getByRole("region", {
      name: "悬浮语音聊天",
    });
    const chatLog = within(floatingChat).getByRole("log", {
      name: "最近对话",
    });
    const utterance = within(floatingChat).getByRole("textbox", {
      name: "语音指令",
    });

    await user.clear(utterance);
    await user.type(utterance, "今天午饭吃什么");
    await user.click(within(floatingChat).getByRole("button", { name: /^发送$/ }));

    expect(await within(chatLog).findByText("今天午饭吃什么")).toBeInTheDocument();
    expect(
      await within(chatLog).findByText("我可以继续作为座舱助手回答这个随机问题。"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("智能电动车座舱场景")).toBeInTheDocument();
    expect(screen.getByLabelText("车机屏幕 PowerContext 摘要")).toBeInTheDocument();
  });

  it("loads separate chat history when the selected occupant changes", async () => {
    vi.mocked(getChatHistory)
      .mockResolvedValueOnce({
        messages: [
          chatMessage(
            "chat_driver",
            "driver_primary",
            "front_left",
            "user",
            "驾驶员历史消息",
          ),
        ],
      })
      .mockResolvedValueOnce({
        messages: [
          chatMessage(
            "chat_passenger",
            "passenger_front",
            "front_right",
            "user",
            "前排乘客历史消息",
          ),
        ],
      });
    const user = userEvent.setup();
    render(<App />);

    const stage = screen.getByLabelText("智能电动车座舱场景");
    const floatingChat = within(stage).getByRole("region", {
      name: "悬浮语音聊天",
    });
    const chatLog = within(floatingChat).getByRole("log", {
      name: "最近对话",
    });

    expect(await within(chatLog).findByText("驾驶员历史消息")).toBeInTheDocument();
    expect(stage).toHaveAttribute("data-pet-anchor", "chat_driver");
    await user.click(
      within(stage).getByRole("button", {
        name: "前排乘客",
      }),
    );

    expect(await within(chatLog).findByText("前排乘客历史消息")).toBeInTheDocument();
    expect(within(chatLog).queryByText("驾驶员历史消息")).not.toBeInTheDocument();
    expect(floatingChat).toHaveAttribute("data-anchor-actor", "passenger_front");
    expect(stage).toHaveAttribute("data-pet-anchor", "chat_passenger");
    expect(getChatHistory).toHaveBeenNthCalledWith(1, {
      session_id: "demo_session_001",
      actor_id: "driver_primary",
      user_id: "driver_primary",
    });
    expect(getChatHistory).toHaveBeenNthCalledWith(2, {
      session_id: "demo_session_001",
      actor_id: "passenger_front",
      user_id: "passenger_front",
    });
  });

  it("keeps utterance drafts scoped to the selected occupant and clears after submit", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue(liveResponse);
    const user = userEvent.setup();
    render(<App />);

    const stage = screen.getByLabelText("智能电动车座舱场景");
    const textbox = screen.getByRole("textbox", { name: "语音指令" });
    await user.clear(textbox);
    await user.type(textbox, "驾驶员自己的问题");

    await user.click(within(stage).getByRole("button", { name: "前排乘客" }));
    expect(screen.getByRole("textbox", { name: "语音指令" })).toHaveValue("");

    await user.type(screen.getByRole("textbox", { name: "语音指令" }), "乘客自己的问题");
    await user.click(within(stage).getByRole("button", { name: "驾驶员" }));
    expect(screen.getByRole("textbox", { name: "语音指令" })).toHaveValue(
      "驾驶员自己的问题",
    );

    await user.click(screen.getByRole("button", { name: /^发送$/ }));
    await waitFor(() =>
      expect(screen.getByRole("textbox", { name: "语音指令" })).toHaveValue(""),
    );
    await user.click(within(stage).getByRole("button", { name: "前排乘客" }));
    expect(screen.getByRole("textbox", { name: "语音指令" })).toHaveValue(
      "乘客自己的问题",
    );
  });

  it("clears stale chat content while loading another occupant history", async () => {
    const pendingPassengerHistory = new Promise<{
      messages: ReturnType<typeof chatMessage>[];
    }>(() => {});
    vi.mocked(getChatHistory)
      .mockResolvedValueOnce({
        messages: [
          chatMessage(
            "chat_driver",
            "driver_primary",
            "front_left",
            "user",
            "驾驶员历史消息",
          ),
        ],
      })
      .mockReturnValueOnce(pendingPassengerHistory);
    const user = userEvent.setup();
    render(<App />);

    const stage = screen.getByLabelText("智能电动车座舱场景");
    const floatingChat = within(stage).getByRole("region", {
      name: "悬浮语音聊天",
    });
    const chatLog = within(floatingChat).getByRole("log", {
      name: "最近对话",
    });

    expect(await within(chatLog).findByText("驾驶员历史消息")).toBeInTheDocument();

    await user.click(
      within(stage).getByRole("button", {
        name: "前排乘客",
      }),
    );

    expect(within(chatLog).queryByText("驾驶员历史消息")).not.toBeInTheDocument();
    expect(
      within(chatLog).getByText("提交一句语音指令，启动实时 PowerContext 追踪。"),
    ).toBeInTheDocument();
  });

  it("does not let a pending submit overwrite the newly selected occupant history", async () => {
    let resolveScenario!: (response: ScenarioResponse) => void;
    vi.mocked(executeScenarioStep).mockReturnValue(
      new Promise<ScenarioResponse>((resolve) => {
        resolveScenario = resolve;
      }),
    );
    vi.mocked(getChatHistory)
      .mockResolvedValueOnce({ messages: [] })
      .mockResolvedValueOnce({
        messages: [
          chatMessage(
            "chat_passenger",
            "passenger_front",
            "front_right",
            "user",
            "前排乘客历史消息",
          ),
        ],
      })
      .mockResolvedValueOnce({
        messages: [
          chatMessage(
            "chat_driver_after_submit",
            "driver_primary",
            "front_left",
            "assistant",
            "驾驶员提交后历史",
          ),
        ],
      });
    const user = userEvent.setup();
    render(<App />);

    const stage = screen.getByLabelText("智能电动车座舱场景");
    const floatingChat = within(stage).getByRole("region", {
      name: "悬浮语音聊天",
    });
    const chatLog = within(floatingChat).getByRole("log", {
      name: "最近对话",
    });

    await waitFor(() =>
      expect(getChatHistory).toHaveBeenCalledWith({
        session_id: "demo_session_001",
        actor_id: "driver_primary",
        user_id: "driver_primary",
      }),
    );
    await user.click(within(floatingChat).getByRole("button", { name: /^发送$/ }));
    await user.click(
      within(stage).getByRole("button", {
        name: "前排乘客",
      }),
    );

    expect(await within(chatLog).findByText("前排乘客历史消息")).toBeInTheDocument();

    await act(async () => {
      resolveScenario(liveResponse);
    });

    await waitFor(() =>
      expect(within(chatLog).getByText("前排乘客历史消息")).toBeInTheDocument(),
    );
    expect(
      within(chatLog).queryByText("Warming cabin from live memory."),
    ).not.toBeInTheDocument();
    expect(within(chatLog).queryByText("驾驶员提交后历史")).not.toBeInTheDocument();
  });

  it("updates the holographic projection when a cockpit scene is selected", async () => {
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    const stage = screen.getByLabelText("Smart EV cockpit scene");
    const display = within(stage).getByLabelText("Panoramic PowerContext display");
    await user.click(within(display).getByRole("button", { name: "Previous scene" }));

    expect(screen.getByText("Lifecycle and privacy")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Manual cockpit keys").querySelector(".manual-cockpit-keys__day"),
    ).toBeNull();
  });

  it("polls test data status while import is running", async () => {
    vi.mocked(getTestDataStatus)
      .mockResolvedValueOnce(idleTestDataStatus)
      .mockResolvedValueOnce(importedTestDataStatus);
    vi.mocked(generateTestData).mockResolvedValue(generatedTestDataStatus);
    vi.mocked(importTestData).mockResolvedValue(importingTestDataStatus);
    const user = userEvent.setup();

    render(<App />);
    await switchToEnglish(user);

    await user.click(
      screen.getByRole("button", { name: /generate and import 1200 memories/i }),
    );

    expect(importTestData).toHaveBeenCalledWith({
      dataset_id: "smart_ev_cockpit_20260708_1200_seed42",
      apply: true,
      max_workers: 3,
    });
    expect(await screen.findByText(/0 \/ 1200 imported/i)).toBeInTheDocument();

    await waitFor(() => expect(getTestDataStatus).toHaveBeenCalledTimes(2), {
      timeout: 2500,
    });
    expect(await screen.findByText(/1200 imported/i)).toBeInTheDocument();
  }, 4000);

  it("submits utterances and renders backend memory evidence", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue(liveResponse);
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    const utterance = screen.getByRole("textbox", { name: /utterance/i });
    await user.clear(utterance);
    await user.type(utterance, "I usually set 23C and seat heat level 0 when I get in during summer.");
    await user.click(screen.getByRole("button", { name: /^send$/i }));

    expect(executeScenarioStep).toHaveBeenCalledWith({
      act_key: "Act 1",
      actor_id: "driver_primary",
      user_id: "driver_primary",
      seat_position: "front_left",
      text: "I usually set 23C and seat heat level 0 when I get in during summer.",
      session_id: "demo_session_001",
    });
    expect(await screen.findByText("Warming cabin from live memory.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /open live evidence/i }));

    expect(screen.getByText("trace_live_123")).toBeInTheDocument();
    expect(screen.getByText("Operations")).toBeInTheDocument();
    expect(screen.getByText(/cold cabin/)).toBeInTheDocument();
    expect(screen.getByText("mem_live")).toBeInTheDocument();
  });

  it("submits the scripted Act 2 hot-cabin context", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue({
      ...liveResponse,
      act_key: "Act 2",
    });
    const user = userEvent.setup();
    render(<App />);

    const display = screen.getByLabelText("PowerContext 全景车机屏幕");
    await user.click(within(display).getByRole("button", { name: "下一个场景" }));
    expect(screen.getByRole("textbox", { name: "语音指令" })).toHaveValue(
      "车里有点热。",
    );
    await user.click(screen.getByRole("button", { name: /^发送$/ }));

    expect(executeScenarioStep).toHaveBeenCalledWith({
      act_key: "Act 2",
      actor_id: "driver_primary",
      user_id: "driver_primary",
      seat_position: "front_left",
      text: "车里有点热。",
      session_id: "demo_session_001",
      vehicle_context: { hvac_target_temp_c: 28.5 },
    });
  });

  it("keeps the Act 9 live response when persisted chat history is stale", async () => {
    const act9Response: ScenarioResponse = {
      ...liveResponse,
      act_key: "Act 9",
      assistant_reply: "Low SOC proactive care.",
      trace_id: "trace_act_9",
      memory_hits: [],
      recommendations: [
        {
          title: "Battery safety recommendation",
          summary: "Navigate to a reachable charging station now.",
          type: "charging_safety",
          action_policy: "confirm",
          reason_codes: ["critical_soc"],
          metadata: { soc: 9, range_km: 42 },
        },
      ],
      vehicle_state: { soc: 9, range_km: 42 },
      vehicle_state_diff: [
        { field: "soc", before: 62, after: 9 },
        { field: "range_km", before: 305, after: 42 },
      ],
    };
    vi.mocked(executeScenarioStep).mockResolvedValue(act9Response);
    vi.mocked(getChatHistory)
      .mockResolvedValueOnce({ messages: [] })
      .mockResolvedValue({
        messages: [
          chatMessage(
            "old-user",
            "driver_primary",
            "front_left",
            "user",
            "Suggest a driving mode for this trip.",
          ),
          chatMessage(
            "old-assistant",
            "driver_primary",
            "front_left",
            "assistant",
            "Use comfort mode for this trip.",
          ),
        ],
      });
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    const stage = screen.getByLabelText("Smart EV cockpit scene");
    const display = within(stage).getByLabelText("Panoramic PowerContext display");
    const nextSceneButton = within(display).getByRole("button", {
      name: "Next scene",
    });
    for (let index = 0; index < 8; index += 1) {
      await user.click(nextSceneButton);
    }

    expect(screen.getByRole("textbox", { name: /utterance/i })).toHaveValue(
      "Trigger low-battery proactive care.",
    );
    await user.click(screen.getByRole("button", { name: /^send$/i }));

    await waitFor(() => {
      expect(vi.mocked(getChatHistory).mock.calls.length).toBeGreaterThanOrEqual(2);
    });
    expect(screen.getByText("Low SOC proactive care.")).toBeInTheDocument();
    const batteryCard = within(display).getByLabelText("Battery status");
    expect(batteryCard).toHaveAttribute("data-battery-state", "critical");
    expect(batteryCard).toHaveTextContent("9%");
    expect(batteryCard).toHaveTextContent("42 km");
    expect(
      screen.queryByText("Use comfort mode for this trip."),
    ).not.toBeInTheDocument();
  });

  it("keeps navigation confirmation scoped to a pending Act 9 recommendation", async () => {
    const act9Response: ScenarioResponse = {
      ...liveResponse,
      act_key: "Act 9",
      assistant_reply: "Charging guidance ready. Confirm navigation?",
      trace_id: "trace_act_9_pending",
      memory_hits: [],
      recommendations: [
        {
          type: "charging_safety",
          title: "Battery safety recommendation",
          summary: "Navigate to a reachable charging station now.",
          action_policy: "confirm",
          metadata: { soc: 9, range_km: 42 },
        },
      ],
      vehicle_state: { soc: 9, range_km: 42 },
      vehicle_state_diff: [
        { field: "soc", before: 62, after: 9 },
        { field: "range_km", before: 305, after: 42 },
      ],
    };
    vi.mocked(executeScenarioStep).mockResolvedValue(act9Response);
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    const display = within(screen.getByLabelText("Smart EV cockpit scene")).getByLabelText(
      "Panoramic PowerContext display",
    );
    const nextSceneButton = within(display).getByRole("button", {
      name: "Next scene",
    });
    for (let index = 0; index < 8; index += 1) {
      await user.click(nextSceneButton);
    }

    await user.click(screen.getByRole("button", { name: /^send$/i }));
    expect(await screen.findByText("Charging guidance ready. Confirm navigation?"))
      .toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /^send$/i })).toBeEnabled(),
    );

    const utterance = screen.getByRole("textbox", { name: /utterance/i });
    await user.type(utterance, "Confirm navigation");
    expect(utterance).toHaveValue("Confirm navigation");
    await user.click(screen.getByRole("button", { name: /^send$/i }));

    await waitFor(() => expect(executeScenarioStep).toHaveBeenCalledTimes(2));
    expect(executeScenarioStep).toHaveBeenLastCalledWith({
      act_key: "Act 9",
      actor_id: "driver_primary",
      user_id: "driver_primary",
      seat_position: "front_left",
      text: "Confirm navigation",
      session_id: "demo_session_001",
    });
  });

  it("uses the selected actor when submitting utterances", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue(liveResponse);
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    const seatSelector = screen.getByLabelText("Seat occupant selector");
    await user.click(within(seatSelector).getByRole("button", { name: "Passenger" }));
    const utterance = screen.getByRole("textbox", { name: /utterance/i });
    await user.type(utterance, "Can you help the passenger?");
    await user.click(screen.getByRole("button", { name: /^send$/i }));

    expect(within(seatSelector).getByRole("button", { name: "Passenger" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(executeScenarioStep).toHaveBeenCalledWith({
      actor_id: "passenger_front",
      user_id: "passenger_front",
      seat_position: "front_right",
      text: "Can you help the passenger?",
      session_id: "demo_session_001",
    });
  });

  it("submits utterances with the selected PowerContext user id binding", async () => {
    vi.mocked(getUserIdentities).mockResolvedValue({
      identities: [
        {
          ...defaultIdentities[0],
          user_id: "guest_alex",
          display_name: "Alex",
        },
        defaultIdentities[1],
        defaultIdentities[2],
      ],
    });
    vi.mocked(executeScenarioStep).mockResolvedValue(liveResponse);
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() =>
      expect(getChatHistory).toHaveBeenCalledWith({
        session_id: "demo_session_001",
        actor_id: "driver_primary",
        user_id: "guest_alex",
      }),
    );

    const utterance = screen.getByRole("textbox", { name: "语音指令" });
    await user.clear(utterance);
    await user.type(utterance, "我夏天上车一般 23C，座椅加热 0 档。");
    await user.click(screen.getByRole("button", { name: /^发送$/ }));

    expect(executeScenarioStep).toHaveBeenCalledWith({
      act_key: "Act 1",
      actor_id: "driver_primary",
      user_id: "guest_alex",
      seat_position: "front_left",
      text: "我夏天上车一般 23C，座椅加热 0 档。",
      session_id: "demo_session_001",
    });
  });

  it("edits the selected occupant PowerContext user binding from the profile panel", async () => {
    const alexIdentity = {
      ...defaultIdentities[0],
      user_id: "guest_alex",
      display_name: "Alex",
    };
    vi.mocked(getUserIdentities).mockResolvedValue({
      identities: [alexIdentity, defaultIdentities[1], defaultIdentities[2]],
    });
    vi.mocked(getUserProfile).mockResolvedValue({
      profile: {
        identity: alexIdentity,
        primary_memory: "guest_alex profile prefers quiet assistant wording.",
        memory_kind_counts: { person_profile: 1, media_preference: 2 },
        memories: [],
      },
    });
    vi.mocked(updateUserIdentity).mockResolvedValue({
      identity: {
        ...alexIdentity,
        user_id: "guest_maya",
        display_name: "Maya",
      },
    });
    const user = userEvent.setup();
    render(<App />);

    const stage = screen.getByLabelText("智能电动车座舱场景");
    await user.click(
      within(stage).getByRole("button", {
        name: "设置驾驶员个人信息",
      }),
    );

    const panel = await screen.findByRole("dialog", {
      name: "用户个人信息设置",
    });
    expect(within(panel).getByText("guest_alex profile prefers quiet assistant wording.")).toBeInTheDocument();
    expect(within(panel).getByText("person_profile 1")).toBeInTheDocument();

    const userIdInput = within(panel).getByRole("textbox", {
      name: "PowerContext user_id",
    });
    const displayNameInput = within(panel).getByRole("textbox", {
      name: "显示名称",
    });
    await user.clear(userIdInput);
    await user.type(userIdInput, "guest_maya");
    await user.clear(displayNameInput);
    await user.type(displayNameInput, "Maya");
    await user.click(within(panel).getByRole("button", { name: "保存绑定" }));

    expect(updateUserIdentity).toHaveBeenCalledWith("driver_primary", {
      user_id: "guest_maya",
      display_name: "Maya",
      profile_note: "",
    });
    expect(await within(stage).findByText("guest_maya")).toBeInTheDocument();
  });

  it("switches cockpit interior trim from the dropdown", async () => {
    const user = userEvent.setup();
    render(<App />);

    const trimSelect = screen.getByRole("combobox", {
      name: "内饰颜色选择",
    });

    expect(trimSelect).toHaveValue("ivory");

    await user.selectOptions(trimSelect, "orange");

    expect(trimSelect).toHaveValue("orange");
    expect(screen.getByLabelText("智能电动车座舱场景")).toHaveAttribute(
      "data-interior",
      "orange",
    );

    await user.selectOptions(trimSelect, "ivory");

    expect(screen.getByLabelText("智能电动车座舱场景")).toHaveAttribute(
      "data-interior",
      "ivory",
    );

    await user.selectOptions(trimSelect, "cognac");

    expect(screen.getByLabelText("智能电动车座舱场景")).toHaveAttribute(
      "data-interior",
      "cognac",
    );
  });

  it("uses timeline controls to update the active demo scene", async () => {
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    expect(
      screen.getByLabelText("Manual cockpit keys").querySelector(".manual-cockpit-keys__day"),
    ).toBeNull();
    expect(screen.getByRole("textbox", { name: /utterance/i })).toHaveValue(
      "I usually set 23C and seat heat level 0 when I get in during summer.",
    );

    const stage = screen.getByLabelText("Smart EV cockpit scene");
    const display = within(stage).getByLabelText("Panoramic PowerContext display");
    const nextSceneButton = within(display).getByRole("button", {
      name: "Next scene",
    });
    for (let index = 0; index < 7; index += 1) {
      await user.click(nextSceneButton);
    }

    expect(
      screen.getByLabelText("Manual cockpit keys").querySelector(".manual-cockpit-keys__day"),
    ).toBeNull();
    expect(
      within(display).getByLabelText("PowerContext projection summary"),
    ).toHaveTextContent("Driving mode");
    expect(
      within(display).queryByRole("button", { name: /day 56 act 8/i }),
    ).not.toBeInTheDocument();
    expect(
      within(display).getByRole("button", { name: "Previous scene" }),
    ).toBeInTheDocument();
    expect(
      within(display).getByRole("button", { name: "Next scene" }),
    ).toBeInTheDocument();
    expect(
      within(display).getByLabelText("Battery status"),
    ).toBeInTheDocument();
    expect(
      within(display).getByLabelText("Climate temperature"),
    ).toBeInTheDocument();
    expect(
      within(display).getByLabelText("Bluetooth music"),
    ).toBeInTheDocument();

    expect(screen.getByRole("textbox", { name: /utterance/i })).toHaveValue(
      "Suggest a driving mode for this trip.",
    );

    await user.click(
      within(screen.getByLabelText("Manual cockpit keys")).getByRole("button", {
        name: /^next$/i,
      }),
    );

    expect(
      screen.getByLabelText("Manual cockpit keys").querySelector(".manual-cockpit-keys__day"),
    ).toBeNull();
    expect(screen.getByRole("textbox", { name: /utterance/i })).toHaveValue(
      "Trigger low-battery proactive care.",
    );
  });

  it("resets and replays the live demo response", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue(liveResponse);
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    expect(screen.getByRole("button", { name: /replay/i })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: /^send$/i }));
    expect(await screen.findByText("Warming cabin from live memory.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /replay/i }));
    expect(executeScenarioStep).toHaveBeenCalledTimes(2);
    expect(executeScenarioStep).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        act_key: "Act 1",
        text: "I usually set 23C and seat heat level 0 when I get in during summer.",
      }),
    );

    await user.click(screen.getByRole("button", { name: /reset/i }));
    expect(screen.getByRole("button", { name: /replay/i })).toBeDisabled();
    expect(
      screen.getByLabelText("Manual cockpit keys").querySelector(".manual-cockpit-keys__day"),
    ).toBeNull();
  });

  it("exports trace evidence from the presenter controls", async () => {
    vi.mocked(exportTrace).mockResolvedValue({
      recent_operations: [{ operation: "utter", trace_id: "trace_live_123" }],
    });
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    await user.click(screen.getByRole("button", { name: /^export$/i }));

    expect(exportTrace).toHaveBeenCalledTimes(1);
    expect(await screen.findByText(/exported trace evidence/i)).toBeInTheDocument();
  });

  it("exports trace evidence from the developer drawer", async () => {
    vi.mocked(executeScenarioStep).mockResolvedValue(liveResponse);
    vi.mocked(exportTrace).mockResolvedValue({
      recent_operations: [{ operation: "utter", trace_id: "trace_live_123" }],
    });
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    await user.click(screen.getByRole("button", { name: /^send$/i }));
    await user.click(screen.getByRole("button", { name: /open live evidence/i }));
    await screen.findByLabelText("Developer evidence drawer");
    await user.click(screen.getByRole("button", { name: /export trace/i }));

    expect(exportTrace).toHaveBeenCalledTimes(1);
    expect(await screen.findByText(/exported trace evidence/i)).toBeInTheDocument();
  });

  it("shows a live error when the backend rejects the utterance", async () => {
    vi.mocked(executeScenarioStep).mockRejectedValue(new Error("PowerContext is not connected"));
    const user = userEvent.setup();
    render(<App />);
    await switchToEnglish(user);

    await user.click(screen.getByRole("button", { name: /^send$/i }));

    await user.click(screen.getByRole("button", { name: /open live evidence/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("PowerContext is not connected");
    expect(screen.queryByLabelText("Developer evidence drawer")).not.toBeInTheDocument();
  });
});
