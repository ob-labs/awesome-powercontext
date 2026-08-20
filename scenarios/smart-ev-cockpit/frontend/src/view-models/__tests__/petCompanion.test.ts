import { describe, expect, it } from "vitest";

import { buildPetCompanionState } from "../petCompanion";
import type { ScenarioResponse } from "../../types/api";
import type { ProjectionScene, ScenarioStep } from "../projection";

const projection: ProjectionScene = {
  id: "projection-1",
  mode: "scenario",
  title: "场景",
  subtitle: "演示",
  scoreLabel: "Ready",
  dockLabel: "第 1 天",
  chips: [],
  routeReadout: "演示",
  showMap: true,
  privacyLabel: "Synthetic",
  status: "idle",
};

function step(actKey: string): ScenarioStep {
  return {
    day: "第 1 天",
    act: "场景",
    actKey,
    utterance: "演示指令",
    actorId: "driver_primary",
    seatPosition: "front_left",
  };
}

function response(overrides: Partial<ScenarioResponse> = {}): ScenarioResponse {
  return {
    act_key: "Act 1",
    assistant_reply: "完成",
    trace_id: "trace_pet",
    live_backend: "powercontext_builtin",
    powercontext_connected: true,
    operations: [{ type: "SEARCH", memory_ids: ["mem-1"] }],
    memory_hits: [
      {
        memory_id: "mem-1",
        content: "driver_primary prefers 26C and seat heat level 2.",
        memory_kind: "cabin_control_preference",
      },
    ],
    selected_memory_ids: ["mem-1"],
    vehicle_state: {},
    vehicle_state_diff: [],
    privacy_report: { redaction_count: 0 },
    recommendations: [],
    evidence: {},
    ...overrides,
  };
}

describe("buildPetCompanionState", () => {
  it("introduces MemoFox at the driver chat corner for idle Act 1", () => {
    const pet = buildPetCompanionState({
      step: step("Act 1"),
      response: null,
      projection,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "zh",
    });

    expect(pet.name).toBe("忆灵");
    expect(pet.action).toBe("capture_preference");
    expect(pet.target).toBe("climate");
    expect(pet.originAnchor).toBe("driver");
    expect(pet.anchor).toBe("chat_driver");
    expect(pet.travelLabel).toBe("driver-to-chat_driver");
    expect(pet.speech).toContain("可复用偏好");
    expect(pet.memoryOrbLabel).toBe("偏好记忆");
  });

  it.each([
    ["driver_primary", "driver", "chat_driver"],
    ["passenger_front", "passenger", "chat_passenger"],
    ["child_rear_left", "child", "chat_child"],
  ] as const)(
    "moves to the selected occupant chat corner while idle",
    (selectedActorId, originAnchor, chatAnchor) => {
      const pet = buildPetCompanionState({
        step: step("Act 1"),
        response: null,
        projection,
        liveError: null,
        selectedActorId,
        locale: "zh",
      });

      expect(pet.originAnchor).toBe(originAnchor);
      expect(pet.anchor).toBe(chatAnchor);
      expect(pet.travelLabel).toBe(`${originAnchor}-to-${chatAnchor}`);
    },
  );

  it.each([
    ["Act 1", "capture_preference", "climate", "climate"],
    ["Act 2", "identify_actor", "seat", "driver"],
    ["Act 3", "chain_routine", "routine", "routine"],
    ["Act 4", "guard_boundary", "boundary", "boundary"],
    ["Act 5", "mask_location", "navigation", "navigation"],
    ["Act 6", "soften_media", "media", "media"],
    ["Act 7", "surface_reminder", "relationship", "memory"],
    ["Act 8", "nudge_drive_mode", "drive", "drive"],
    ["Act 9", "watch_battery", "battery", "battery"],
    ["Act 10", "sort_lifecycle", "lifecycle", "lifecycle"],
  ])("maps %s to a distinct companion action", (actKey, action, target, anchor) => {
    const pet = buildPetCompanionState({
      step: step(actKey),
      response: response({ act_key: actKey as ScenarioResponse["act_key"] }),
      projection,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "zh",
    });

    expect(pet.action).toBe(action);
    expect(pet.target).toBe(target);
    expect(pet.originAnchor).toBe("driver");
    expect(pet.anchor).toBe(anchor);
    expect(pet.speech.length).toBeGreaterThan(6);
  });

  it("jumps from the current speaker to the climate target after Act 1 applies an action", () => {
    const pet = buildPetCompanionState({
      step: step("Act 1"),
      response: response({ act_key: "Act 1" }),
      projection,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "zh",
    });

    expect(pet.originAnchor).toBe("driver");
    expect(pet.anchor).toBe("climate");
    expect(pet.travelLabel).toBe("driver-to-climate");
  });

  it("uses a safe memory standby state for ordinary Chat responses", () => {
    const pet = buildPetCompanionState({
      step: step("Act 1"),
      response: response({
        act_key: "Chat",
        operations: [{ type: "CHAT", result: "llm_chat" }],
        memory_hits: [],
      }),
      projection,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "zh",
    });

    expect(pet.action).toBe("standby");
    expect(pet.target).toBe("memory");
    expect(pet.originAnchor).toBe("driver");
    expect(pet.anchor).toBe("chat_driver");
    expect(pet.travelLabel).toBe("driver-to-chat_driver");
  });

  it("uses the recommended drive mode in Act 8 speech", () => {
    const pet = buildPetCompanionState({
      step: step("Act 8"),
      response: response({
        act_key: "Act 8",
        recommendations: [
          {
            type: "drive_mode",
            title: "驾驶模式建议",
            summary: "使用舒适模式。",
            metadata: { drive_mode: "comfort" },
          },
        ],
      }),
      projection,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "zh",
    });

    expect(pet.speech).toContain("舒适");
    expect(pet.cueLabel).toContain("comfort");
  });

  it("switches Act 9 to an urgent low-battery mood when SOC is critical", () => {
    const pet = buildPetCompanionState({
      step: step("Act 9"),
      response: response({
        act_key: "Act 9",
        recommendations: [
          {
            type: "charging_safety",
            title: "电池安全建议",
            summary: "请立即导航到可到达的充电站。",
            metadata: { soc: 9 },
          },
        ],
      }),
      projection,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "zh",
    });

    expect(pet.mood).toBe("urgent");
    expect(pet.speech).toContain("低电量");
  });

  it("summarizes Act 10 lifecycle sorting with completed operation counts", () => {
    const pet = buildPetCompanionState({
      step: step("Act 10"),
      response: response({
        act_key: "Act 10",
        lifecycle: {
          current_day: 90,
          completed_operations: [
            { type: "UPDATE", memory_ids: ["mem-1"], result: "ok" },
            { type: "DELETE", memory_ids: ["mem-2"], result: "ok" },
          ],
        },
      }),
      projection,
      liveError: null,
      selectedActorId: "driver_primary",
      locale: "zh",
    });

    expect(pet.target).toBe("lifecycle");
    expect(pet.speech).toContain("2");
    expect(pet.speech).toContain("分拣");
  });

  it("falls back to an error companion state when the live path fails", () => {
    const pet = buildPetCompanionState({
      step: step("Act 1"),
      response: null,
      projection: { ...projection, status: "error" },
      liveError: "PowerContext unavailable",
      selectedActorId: "driver_primary",
      locale: "en",
    });

    expect(pet.name).toBe("MemoFox");
    expect(pet.mood).toBe("alert");
    expect(pet.target).toBe("error");
    expect(pet.anchor).toBe("error");
    expect(pet.speech).toContain("PowerContext");
  });
});
