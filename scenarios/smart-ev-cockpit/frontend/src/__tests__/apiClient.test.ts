import { describe, expect, it, vi } from "vitest";
import {
  clearAllTestData,
  createUtterance,
  createVehicleEvent,
  executeScenarioStep,
  exportTrace,
  generateTestData,
  getChatHistory,
  getUserIdentities,
  getUserProfile,
  getTestDataStatus,
  importTestData,
  runLifecycle,
  updateUserIdentity,
} from "../api/smartEvCockpit";

describe("smart EV cockpit API client", () => {
  it("posts utterance payloads to the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        assistant_reply: "Live response",
        trace_id: "trace_001",
        live_backend: "powercontext_builtin",
        powercontext_connected: true,
        operations: [],
        memory_hits: [],
        vehicle_state: {},
        vehicle_state_diff: [],
        privacy_report: {},
        recommendations: [],
        evidence: {},
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await createUtterance({
      actor_id: "driver_primary",
      seat_position: "front_left",
      text: "I feel cold.",
      session_id: "demo_session_001",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/scenarios/smart-ev-cockpit/utter",
      expect.objectContaining({ method: "POST" }),
    );
    expect(result.trace_id).toBe("trace_001");
  });

  it("routes Act 9 through the vehicle event endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        assistant_reply: "Low SOC proactive care",
        trace_id: "trace_act9",
        live_backend: "powercontext_builtin",
        powercontext_connected: true,
        operations: [],
        memory_hits: [],
        vehicle_state: {},
        vehicle_state_diff: [],
        privacy_report: {},
        recommendations: [],
        evidence: {},
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await executeScenarioStep({
      act_key: "Act 9",
      actor_id: "driver_primary",
      seat_position: "front_left",
      text: "Trigger low-battery proactive care.",
      session_id: "demo_session_001",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/scenarios/smart-ev-cockpit/events/vehicle",
      expect.objectContaining({ method: "POST" }),
    );
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      soc: 9,
      range_km: 42,
      text: "Trigger low-battery proactive care.",
    });
    expect(result.trace_id).toBe("trace_act9");
  });

  it("marks an Act 9 navigation confirmation as a charging event confirmation", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        assistant_reply: "Charging navigation confirmed",
        trace_id: "trace_act9_confirmed",
        live_backend: "powercontext_builtin",
        powercontext_connected: true,
        operations: [],
        memory_hits: [],
        vehicle_state: {},
        vehicle_state_diff: [],
        privacy_report: {},
        recommendations: [],
        evidence: {},
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await executeScenarioStep({
      act_key: "Act 9",
      actor_id: "driver_primary",
      seat_position: "front_left",
      text: "确认导航",
      session_id: "demo_session_001",
    });

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      soc: 9,
      range_km: 42,
      text: "确认导航",
      confirm_navigation: true,
    });
  });

  it("routes Act 10 through the lifecycle endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        assistant_reply: "Lifecycle review complete",
        trace_id: "trace_act10",
        live_backend: "powercontext_builtin",
        powercontext_connected: true,
        operations: [{ type: "UPDATE" }],
        memory_hits: [],
        vehicle_state: {},
        vehicle_state_diff: [],
        privacy_report: {},
        recommendations: [],
        lifecycle: { completed_operations: [{ type: "UPDATE", result: "ok" }] },
        evidence: {},
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await executeScenarioStep({
      act_key: "Act 10",
      actor_id: "driver_primary",
      seat_position: "front_left",
      text: "执行第 90 天生命周期回顾。",
      session_id: "demo_session_001",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/scenarios/smart-ev-cockpit/lifecycle/run",
      expect.objectContaining({ method: "POST" }),
    );
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      current_day: 90,
      text: "执行第 90 天生命周期回顾。",
    });
    expect(result.trace_id).toBe("trace_act10");
  });

  it("posts vehicle events and lifecycle runs directly", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        assistant_reply: "ok",
        trace_id: "trace_direct",
        live_backend: "powercontext_builtin",
        powercontext_connected: true,
        operations: [],
        memory_hits: [],
        vehicle_state: {},
        vehicle_state_diff: [],
        privacy_report: {},
        recommendations: [],
        evidence: {},
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await createVehicleEvent({ soc: 9, range_km: 42 });
    await runLifecycle({ current_day: 90 });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/scenarios/smart-ev-cockpit/events/vehicle",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/scenarios/smart-ev-cockpit/lifecycle/run",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("loads actor-scoped chat history from the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        messages: [
          {
            id: "chat_001",
            session_id: "demo_session_001",
            actor_id: "driver_primary",
            seat_position: "front_left",
            role: "user",
            text: "I feel cold.",
            trace_id: "trace_001",
            created_at: "2026-07-09T10:00:00Z",
          },
        ],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getChatHistory({
      session_id: "demo_session_001",
      actor_id: "driver_primary",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/scenarios/smart-ev-cockpit/chat-history?session_id=demo_session_001&actor_id=driver_primary",
    );
    expect(result.messages[0].text).toBe("I feel cold.");
  });

  it("exports live trace evidence from the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        scenario_id: "smart_ev_cockpit",
        traces: [{ trace_id: "trace_001" }],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await exportTrace();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/scenarios/smart-ev-cockpit/export",
    );
    expect(result.traces).toEqual([{ trace_id: "trace_001" }]);
  });

  it("manages test data through backend endpoints", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        state: "generated",
        dataset_id: "dataset_001",
        generated_count: 1200,
        imported_count: 0,
        deleted_count: 0,
        skipped_count: 0,
        failed_count: 0,
        last_error: null,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await generateTestData({ count: 1200, seed: 42, locale: "zh" });
    await importTestData({ dataset_id: "dataset_001", apply: true });
    await getTestDataStatus();
    await clearAllTestData({ apply: true });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/scenarios/smart-ev-cockpit/test-data/generate",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/scenarios/smart-ev-cockpit/test-data/import",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/scenarios/smart-ev-cockpit/test-data/status",
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      "/api/scenarios/smart-ev-cockpit/test-data/all",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("loads user-scoped chat history from the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ messages: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getChatHistory({
      session_id: "demo_session_001",
      actor_id: "driver_primary",
      user_id: "guest_alex",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/scenarios/smart-ev-cockpit/chat-history?session_id=demo_session_001&actor_id=driver_primary&user_id=guest_alex",
    );
  });

  it("calls identity and profile endpoints", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        identities: [],
        identity: {
          actor_id: "driver_primary",
          seat_position: "front_left",
          user_id: "guest_alex",
          display_name: "Alex",
          profile_note: "",
          updated_at: "2026-07-10T00:00:00Z",
        },
        profile: {
          identity: {
            actor_id: "driver_primary",
            seat_position: "front_left",
            user_id: "guest_alex",
            display_name: "Alex",
            profile_note: "",
            updated_at: "2026-07-10T00:00:00Z",
          },
          primary_memory: null,
          memory_kind_counts: {},
          memories: [],
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getUserIdentities();
    await updateUserIdentity("driver_primary", {
      user_id: "guest_alex",
      display_name: "Alex",
      profile_note: "",
    });
    await getUserProfile("driver_primary");

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/scenarios/smart-ev-cockpit/identities",
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/scenarios/smart-ev-cockpit/identities/driver_primary",
      expect.objectContaining({ method: "PUT" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/scenarios/smart-ev-cockpit/profiles/driver_primary",
    );
  });
});
