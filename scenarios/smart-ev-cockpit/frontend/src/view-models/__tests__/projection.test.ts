import { describe, expect, it } from "vitest";

import { buildProjectionScene } from "../projection";
import type { ScenarioResponse } from "../../types/api";

const step = {
  day: "Day 1",
  act: "Act 1",
  actKey: "Act 1",
  utterance: "I usually set 26C and seat heat level 2 when I get in during winter.",
  actorId: "driver_primary" as const,
  seatPosition: "front_left" as const,
};

describe("buildProjectionScene", () => {
  it("builds an idle projection from scenario metadata", () => {
    const projection = buildProjectionScene({
      step,
      response: null,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "en",
    });

    expect(projection.status).toBe("idle");
    expect(projection.title).toBe("Preference capture");
    expect(projection.subtitle).toContain("Store structured cabin preferences");
    expect(projection.scoreLabel).toBe("Ready");
    expect(projection.chips).toEqual([
      { label: "Actor", value: "Driver" },
      { label: "Scene", value: "Act 1" },
      { label: "Source", value: "Scenario" },
    ]);
  });

  it("maps low-battery scenario metadata into battery state", () => {
    const projection = buildProjectionScene({
      step: {
        ...step,
        day: "Day 56",
        act: "Act 9",
        actKey: "Act 9",
        utterance: "Trigger low-battery proactive care.",
      },
      response: null,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "en",
    });

    expect(projection.batteryState).toEqual({
      percent: 18,
      rangeKm: 76,
      status: "low",
      isLive: false,
    });
  });
});

const liveResponse: ScenarioResponse = {
  assistant_reply: "Warming cabin from live memory.",
  trace_id: "trace_live_123",
  live_backend: "powercontext_builtin",
  powercontext_connected: true,
  operations: [{ type: "search", hit_count: 1 }],
  memory_hits: [
    {
      memory_id: "mem_live",
      content: "driver_primary prefers 26C and seat heat level 2 in winter.",
      memory_kind: "cabin_control_preference",
      score: 0.87,
    },
  ],
  vehicle_state: {
    hvac: { front_left_target_temp: 26 },
    seat_heat: { front_left: 2 },
  },
  vehicle_state_diff: [
    {
      field: "hvac",
      before: { front_left_target_temp: 22 },
      after: { front_left_target_temp: 26 },
    },
    {
      field: "seat_heat",
      before: { front_left: 0, front_right: 0 },
      after: { front_left: 2 },
    },
  ],
  privacy_report: { redaction_count: 0 },
  recommendations: [{ label: "Warm cabin" }],
  evidence: {},
};

it("uses live PowerContext response data when available", () => {
  const projection = buildProjectionScene({
    step,
    response: liveResponse,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "en",
  });

  expect(projection.status).toBe("ready");
  expect(projection.title).toBe("Cabin linked");
  expect(projection.subtitle).toBe(
    "Intent understood, memory recalled, climate action applied.",
  );
  expect(projection.scoreLabel).toBe("Linked");
  expect(projection.chips).toEqual([
    { label: "Intent", value: "Driver feels cold" },
    { label: "Memory", value: "Winter comfort preference" },
    { label: "Action", value: "Driver zone 22°C -> 26°C, seat heat 0 -> 2" },
  ]);
  expect(projection.routeReadout).toBe("Driver zone 22°C -> 26°C");
  expect(projection.storySteps).toEqual([
    {
      label: "Intent",
      value: "Driver feels cold",
      detail: "The utterance is treated as a cabin comfort control request.",
    },
    {
      label: "Memory",
      value: "Winter comfort preference",
      detail: "driver_primary prefers 26C and seat heat level 2 in winter.",
    },
    {
      label: "Action",
      value: "Driver zone 22°C -> 26°C, seat heat 0 -> 2",
      detail: "PowerContext restores the remembered comfort setup on the vehicle.",
    },
  ]);
  expect(projection.climateAction).toEqual({
    zoneLabel: "Driver zone",
    temperatureLabel: "Temperature",
    beforeTemp: "22°C",
    afterTemp: "26°C",
    temperatureReadout: "22°C -> 26°C",
    seatHeatLabel: "Seat heat",
    beforeSeatHeat: "0",
    afterSeatHeat: "2",
    seatHeatReadout: "0 -> 2",
  });
});

it("uses live SOC and range values for the battery state", () => {
  const batteryResponse: ScenarioResponse = {
    ...liveResponse,
    trace_id: "trace_low_soc",
    act_key: "Act 9",
    memory_hits: [],
    vehicle_state: { soc: 9, range_km: 42 },
    vehicle_state_diff: [
      { field: "soc", before: 62, after: 9 },
      { field: "range_km", before: 305, after: 42 },
    ],
    recommendations: [
      {
        title: "Battery safety recommendation",
        action_policy: "confirm",
        metadata: { soc: 9, range_km: 42 },
      },
    ],
  };

  const projection = buildProjectionScene({
    step: { ...step, act: "Act 9", actKey: "Act 9" },
    response: batteryResponse,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "en",
  });

  expect(projection.batteryState).toEqual({
    percent: 9,
    rangeKm: 42,
    status: "critical",
    isLive: true,
  });
});

it("renders Act 9 as a confirmation-gated battery care flow", () => {
  const batteryCareResponse: ScenarioResponse = {
    ...liveResponse,
    trace_id: "trace_battery_care",
    act_key: "Act 9",
    assistant_reply:
      "当前电量 9%，剩余续航 42 公里。请立即导航到最近可用的充电站，请确认是否开始导航。",
    memory_hits: [
      {
        memory_id: "charging_used",
        content: "Masked charging_preference memory",
        memory_kind: "charging_preference",
      },
    ],
    selected_memory_ids: ["charging_used"],
    vehicle_state: { soc: 9, range_km: 42 },
    vehicle_state_diff: [
      { field: "soc", before: 62, after: 9 },
      { field: "range_km", before: 305, after: 42 },
    ],
    recommendations: [
      {
        type: "charging_safety",
        title: "电池安全建议",
        summary: "请立即导航到最近可用的充电站。",
        action_policy: "confirm",
        reason_codes: ["critical_soc"],
        metadata: {
          soc: 9,
          range_km: 42,
          charging_strategy: "nearest_available",
        },
      },
    ],
  };

  const projection = buildProjectionScene({
    step: {
      ...step,
      day: "第 70 天",
      act: "场景 9",
      actKey: "Act 9",
      utterance: "触发低电量主动关怀。",
    },
    response: batteryCareResponse,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "zh",
  });

  expect(projection.mode).toBe("battery-care");
  expect(projection.title).toBe("低电量主动关怀");
  expect(projection.subtitle).toBe("检测到 SOC 9%，剩余续航 42 km。");
  expect(projection.routeReadout).toBe(
    "低电量事件 · 偏好命中 · 充电建议 · 等待确认",
  );
  expect(projection.batteryCare).toEqual({
    title: "电池安全建议",
    summary: "请立即导航到最近可用的充电站。",
    destinationLabel: "最近可用的充电站",
    memoryLabel: "已命中充电偏好",
    actionLabel: "等待驾驶员确认",
  });
  expect(projection.climateAction).toBeUndefined();

  const policyOnlyProjection = buildProjectionScene({
    step: {
      ...step,
      day: "第 70 天",
      act: "场景 9",
      actKey: "Act 9",
      utterance: "触发低电量主动关怀。",
    },
    response: {
      ...batteryCareResponse,
      memory_hits: [],
      selected_memory_ids: [],
      recommendations: [
        {
          ...batteryCareResponse.recommendations[0],
          metadata: { soc: 9, range_km: 42 },
        },
      ],
    },
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "zh",
  });

  expect(policyOnlyProjection.routeReadout).toBe(
    "低电量事件 · 安全策略 · 充电建议 · 等待确认",
  );
  expect(policyOnlyProjection.batteryCare?.memoryLabel).toBe("电池安全策略已启用");
});

it("ignores stale battery snapshot values when Act 1 only changes the cabin", () => {
  const cabinResponseWithStaleBattery: ScenarioResponse = {
    ...liveResponse,
    trace_id: "trace_act_1_after_low_soc",
    act_key: "Act 1",
    vehicle_state: {
      soc: 9,
      range_km: 42,
      hvac: { front_left_target_temp: 23 },
      seat_heat: { front_left: 0 },
    },
    vehicle_state_diff: [
      {
        field: "hvac.front_left_target_temp",
        before: 22,
        after: 23,
      },
    ],
    recommendations: [],
  };

  const projection = buildProjectionScene({
    step,
    response: cabinResponseWithStaleBattery,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "en",
  });

  expect(projection.batteryState).toEqual({
    percent: 74,
    rangeKm: 382,
    status: "normal",
    isLive: false,
  });
});

it("turns missing previous vehicle values into customer-facing target readouts", () => {
  const responseWithoutBefore: ScenarioResponse = {
    ...liveResponse,
    vehicle_state_diff: [
      {
        field: "hvac",
        before: {},
        after: { front_left_target_temp: 26 },
      },
      {
        field: "seat_heat",
        before: {},
        after: { front_left: 2 },
      },
    ],
  };

  const projection = buildProjectionScene({
    step,
    response: responseWithoutBefore,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "en",
  });

  expect(projection.chips.at(2)).toEqual({
    label: "Action",
    value: "Driver zone target 26°C, seat heat level 2",
  });
  expect(projection.routeReadout).toBe("Driver zone target 26°C");
  expect(projection.climateAction).toMatchObject({
    beforeTemp: "--",
    afterTemp: "26°C",
    temperatureReadout: "Target 26°C",
    beforeSeatHeat: "--",
    afterSeatHeat: "2",
    seatHeatReadout: "Level 2",
  });
});

it("links Act 1 leaf-level vehicle diffs to the climate readout", () => {
  const preferenceResponse: ScenarioResponse = {
    ...liveResponse,
    act_key: "Act 1",
    assistant_reply: "已保存并应用你的座舱偏好。",
    vehicle_state: {
      hvac: { front_left_target_temp: 23 },
      seat_heat: { front_left: 0 },
    },
    vehicle_state_diff: [
      {
        field: "hvac.front_left_target_temp",
        before: 22,
        after: 23,
      },
    ],
  };

  const projection = buildProjectionScene({
    step,
    response: preferenceResponse,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "zh",
  });

  expect(projection.climateAction).toMatchObject({
    beforeTemp: "22°C",
    afterTemp: "23°C",
    temperatureReadout: "22°C -> 23°C",
    afterSeatHeat: "0",
  });
  expect(projection.routeReadout).toBe("驾驶员温区 22°C -> 23°C");
});

it("switches to navigation projection when vehicle state enters map mode", () => {
  const navigationResponse: ScenarioResponse = {
    assistant_reply: "已切换到地图模式，开始导航到张江科学城。",
    trace_id: "trace_navigation_confirmed",
    live_backend: "powercontext_builtin",
    powercontext_connected: true,
    operations: [{ type: "search", hit_count: 1 }],
    memory_hits: [
      {
        memory_id: "location_used",
        content: "Masked location_episode memory",
        memory_kind: "location_episode",
        score: 0.91,
      },
    ],
    vehicle_state: {
      navigation: {
        mode: "map",
        status: "active",
        destination: {
          area_scope: "region",
          region: "张江科学城",
        },
        destination_label: "张江科学城",
      },
    },
    vehicle_state_diff: [
      {
        field: "navigation.mode",
        before: undefined,
        after: "map",
      },
    ],
    privacy_report: { redaction_count: 0 },
    recommendations: [
      {
        type: "navigation",
        title: "区域级导航",
        action_policy: "execute",
        metadata: { area_scope: "region", region: "张江科学城" },
      },
    ],
    evidence: {},
  };

  const projection = buildProjectionScene({
    step: { ...step, act: "Act 5", actKey: "Act 5" },
    response: navigationResponse,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "zh",
  });

  expect(projection.mode).toBe("navigation");
  expect(projection.showMap).toBe(true);
  expect(projection.title).toBe("地图导航");
  expect(projection.routeReadout).toBe("区域级路线已加载：张江科学城");
  expect(projection.navigation).toEqual({
    destinationLabel: "张江科学城",
    statusLabel: "导航中",
    routeLabel: "区域级路线已加载：张江科学城",
  });
});

it("shows charging-station navigation after confirming Act 9", () => {
  const chargingNavigationResponse: ScenarioResponse = {
    ...liveResponse,
    act_key: "Act 9",
    assistant_reply: "已确认，开始导航到最近可用的充电站。",
    trace_id: "trace_charging_navigation_confirmed",
    memory_hits: [],
    vehicle_state: {
      soc: 9,
      range_km: 42,
      navigation: {
        mode: "map",
        status: "active",
        destination: {
          area_scope: "category",
          destination_type: "charging_station",
          selection_strategy: "nearest_available",
        },
        destination_label: "最近可用的充电站",
      },
    },
    vehicle_state_diff: [
      {
        field: "navigation.mode",
        before: undefined,
        after: "map",
      },
    ],
    recommendations: [
      {
        type: "charging_navigation",
        title: "充电站导航",
        action_policy: "execute",
        reason_codes: ["critical_soc", "charging_navigation_confirmed"],
      },
    ],
  };

  const projection = buildProjectionScene({
    step: { ...step, act: "场景 9", actKey: "Act 9" },
    response: chargingNavigationResponse,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "zh",
  });

  expect(projection.mode).toBe("navigation");
  expect(projection.navigation?.destinationLabel).toBe("最近可用的充电站");
  expect(projection.routeReadout).toContain("最近可用的充电站");
  expect(JSON.stringify(projection)).not.toContain("张江科学城");
});

it("renders Act 7 as a privacy-safe relationship recommendation", () => {
  const relationshipResponse: ScenarioResponse = {
    ...liveResponse,
    act_key: "Act 7",
    assistant_reply:
      "可以考虑今晚安排一次安静的晚餐。相关纪念日日期已保护。",
    trace_id: "trace_relationship_suggestion",
    memory_hits: [
      {
        memory_id: "relationship_used",
        content: "Masked relationship_event memory",
        memory_kind: "relationship_event",
      },
    ],
    vehicle_state: {
      hvac: { front_left_target_temp: 23 },
      seat_heat: { front_left: 0 },
    },
    vehicle_state_diff: [],
    recommendations: [
      {
        type: "relationship",
        title: "今晚建议",
        summary: "可以考虑今晚安排一次安静的晚餐。",
        action_policy: "suggest",
        reason_codes: ["anniversary_date_masked", "navigation_not_started"],
        metadata: {
          date: "anniversary date masked",
          area_scope: "region",
          region: "张江科学城",
        },
      },
    ],
  };

  const projection = buildProjectionScene({
    step: {
      ...step,
      day: "第 42 天",
      act: "场景 7",
      actKey: "Act 7",
      utterance: "今晚有什么安排建议？",
    },
    response: relationshipResponse,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "zh",
  });

  expect(projection.mode).toBe("recommendation");
  expect(projection.title).toBe("今晚建议");
  expect(projection.subtitle).toBe("可以考虑今晚安排一次安静的晚餐。");
  expect(projection.routeReadout).toBe("仅提供建议 · 纪念日日期已隐藏");
  expect(projection.recommendation).toEqual({
    title: "今晚建议",
    summary: "可以考虑今晚安排一次安静的晚餐。",
    policyLabel: "仅提供建议",
    regionLabel: "张江科学城 · 仅区域级",
    privacyLabel: "纪念日日期已隐藏",
  });
  expect(projection.climateAction).toBeUndefined();
});

it("renders ordinary LLM chat as an assistant reply instead of an action projection", () => {
  const chatResponse: ScenarioResponse = {
    assistant_reply:
      "当前车外温度为 6°C，车内温度为 22°C。由于系统不提供实时天气信息，建议您查看手机天气应用或车载导航的天气插件获取详细预报。",
    trace_id: "trace_chat_weather",
    live_backend: "powercontext_builtin+llm",
    powercontext_connected: true,
    operations: [
      { type: "search", hit_count: 0 },
      { type: "chat" },
    ],
    memory_hits: [],
    vehicle_state: {},
    vehicle_state_diff: [],
    privacy_report: { redaction_count: 0 },
    recommendations: [],
    evidence: {},
  };

  const projection = buildProjectionScene({
    step,
    response: chatResponse,
    liveError: null,
    selectedActorId: "driver_primary",
    selectedSeatPosition: "front_left",
    locale: "zh",
  });

  expect(projection.mode).toBe("chat");
  expect(projection.showMap).toBe(false);
  expect(projection.title).toBe("语音助手");
  expect(projection.subtitle).toBe(chatResponse.assistant_reply);
  expect(projection.routeReadout).toBe("模型对话");
  expect(projection.chips).toEqual([
    { label: "追踪", value: "已同步" },
    { label: "记忆", value: "无命中" },
    { label: "隐私", value: "0" },
  ]);
});

it("shows live-mode errors without fake memory content", () => {
  const projection = buildProjectionScene({
    step,
    response: null,
    liveError: "PowerContext is not connected",
    selectedActorId: "driver_primary",
    locale: "en",
  });

  expect(projection.status).toBe("error");
  expect(projection.title).toBe("Live memory unavailable");
  expect(projection.privacyLabel).toBe("No fake fallback");
});
