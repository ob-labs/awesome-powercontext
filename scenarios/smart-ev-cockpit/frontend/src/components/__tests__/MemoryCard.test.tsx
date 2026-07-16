import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MemoryCard } from "../MemoryCard";

describe("MemoryCard", () => {
  it("shows live evidence fields required by the workshop", () => {
    render(
      <MemoryCard
        memory={{
          memory_id: "mem_winter",
          content: "driver winter preference",
          memory_kind: "cabin_control_preference",
          visibility: "public_demo",
          lifecycle_status: "active",
          score: 0.91,
        }}
      />,
    );

    expect(screen.getByText("mem_winter")).toBeInTheDocument();
    expect(screen.getByText("cabin_control_preference")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("0.91")).toBeInTheDocument();
  });
});
