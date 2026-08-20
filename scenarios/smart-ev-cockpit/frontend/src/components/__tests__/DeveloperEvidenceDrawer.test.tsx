import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DeveloperEvidenceDrawer } from "../DeveloperEvidenceDrawer";

describe("DeveloperEvidenceDrawer", () => {
  it("renders the replayable live evidence chain", () => {
    render(
      <DeveloperEvidenceDrawer
        response={{
          trace_id: "trace_001",
          live_backend: "powercontext_builtin",
          powercontext_connected: true,
          evidence: {
            request: { actor_id: "driver_primary" },
            privacy: { redaction_count: 1 },
            data_source: "powercontext_builtin",
            operations: [
              {
                type: "SEARCH",
                query: "winter cold",
                filters: { actor_id: "driver_primary" },
                hit_count: 1,
              },
            ],
            memory_hits: [{ memory_id: "mem_winter", score: 0.91 }],
            decision: { selected_memory_ids: ["mem_winter"] },
            vehicle_action: { diff: [{ field: "soc", before: 62, after: 18 }] },
            latency_ms: 184,
          },
        }}
      />,
    );

    expect(screen.getByText("trace_001")).toBeInTheDocument();
    expect(screen.getByText("Operations")).toBeInTheDocument();
    expect(screen.getByText(/winter cold/)).toBeInTheDocument();
    expect(screen.getAllByText(/mem_winter/).length).toBeGreaterThan(0);
  });

  it("renders the current backend evidence keys including operations, lifecycle, and audit", () => {
    render(
      <DeveloperEvidenceDrawer
        response={{
          trace_id: "trace_lifecycle_001",
          live_backend: "powercontext_builtin",
          powercontext_connected: true,
          evidence: {
            request: { act_key: "Act 10", actor_id: "driver_primary" },
            privacy: { redaction_count: 0, tags: [] },
            data_source: "powercontext_builtin",
            operations: [
              {
                type: "UPDATE",
                memory_ids: ["temp-001"],
                before_status: "active",
                after_status: "archived",
                result: "ok",
              },
            ],
            memory_hits: [{ memory_id: "temp-001", lifecycle_status: "active" }],
            decision: { selected_memory_ids: [], reason_codes: ["lifecycle_review"] },
            vehicle_action: { patch: {}, diff: [] },
            recommendations: [],
            lifecycle: {
              current_day: 90,
              trace_id: "trace_lifecycle_001",
              completed_operations: [
                {
                  type: "UPDATE",
                  memory_ids: ["temp-001"],
                  before_status: "active",
                  after_status: "archived",
                  result: "ok",
                },
              ],
            },
            audit: [
              {
                type: "UPDATE",
                memory_id: "temp-001",
                before_status: "active",
                after_status: "archived",
                result: "ok",
              },
            ],
            latency_ms: 42,
          },
        }}
      />,
    );

    expect(screen.getByText("Operations")).toBeInTheDocument();
    expect(screen.getByText("Lifecycle")).toBeInTheDocument();
    expect(screen.getByText("Audit")).toBeInTheDocument();
    expect(screen.getByText("Latency")).toBeInTheDocument();
    expect(screen.getAllByText(/temp-001/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/archived/).length).toBeGreaterThan(0);
  });
});
