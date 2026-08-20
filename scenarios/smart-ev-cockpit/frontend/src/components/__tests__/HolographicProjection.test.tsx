import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HolographicProjection } from "../HolographicProjection";
import type { ProjectionScene } from "../../view-models/projection";

const baseProjection: ProjectionScene = {
  id: "projection-test",
  mode: "chat",
  title: "Voice assistant",
  subtitle: "The weather reply should read as a cabin assistant response.",
  scoreLabel: "Live",
  dockLabel: "LLM chat",
  chips: [
    { label: "Trace", value: "Synced" },
    { label: "Memory", value: "No hit" },
    { label: "Privacy", value: "0" },
  ],
  routeReadout: "LLM chat",
  showMap: false,
  privacyLabel: "Evidence visible",
  status: "ready",
};

describe("HolographicProjection", () => {
  it("renders ordinary chat without the action trajectory map", () => {
    const { container } = render(
      <HolographicProjection projection={baseProjection} />,
    );

    expect(container.querySelector(".holographic-projection--chat")).not.toBeNull();
    expect(container.querySelector(".projection-map")).toBeNull();
    expect(screen.getByText("The weather reply should read as a cabin assistant response.")).toBeInTheDocument();
  });

  it("renders action projections as intent, memory, and action story steps", () => {
    const actionProjection: ProjectionScene = {
      ...baseProjection,
      id: "projection-action",
      mode: "action",
      title: "Cabin linked",
      subtitle: "Intent understood, memory recalled, climate action applied.",
      routeReadout: "Driver zone 22°C -> 26°C",
      showMap: false,
      storySteps: [
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
      ],
    };

    const { container } = render(
      <HolographicProjection projection={actionProjection} />,
    );

    expect(container.querySelector(".projection-map")).toBeNull();
    expect(screen.getByText("Intent")).toBeInTheDocument();
    expect(screen.getByText("Driver feels cold")).toBeInTheDocument();
    expect(
      screen.getByText("driver_primary prefers 26C and seat heat level 2 in winter."),
    ).toBeInTheDocument();
    expect(screen.getByText("Driver zone 22°C -> 26°C, seat heat 0 -> 2")).toBeInTheDocument();
  });
});
