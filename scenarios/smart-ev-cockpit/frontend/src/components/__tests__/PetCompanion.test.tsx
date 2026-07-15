import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PetCompanion } from "../PetCompanion";
import type { PetCompanionState } from "../../view-models/petCompanion";

const state: PetCompanionState = {
  name: "忆灵",
  mood: "urgent",
  action: "watch_battery",
  target: "battery",
  originAnchor: "driver",
  anchor: "battery",
  travelLabel: "driver-to-battery",
  speech: "电量 9%：低电量提醒已亮起，我准备了充电建议。",
  cueLabel: "SOC 9%",
  memoryOrbLabel: "充电偏好",
};

describe("PetCompanion", () => {
  it("renders the companion status with speech and target metadata", () => {
    render(<PetCompanion state={state} />);

    const companion = screen.getByLabelText("忆灵：电量 9%：低电量提醒已亮起，我准备了充电建议。");

    expect(companion).toHaveAttribute("data-mood", "urgent");
    expect(companion).toHaveAttribute("data-action", "watch_battery");
    expect(companion).toHaveAttribute("data-target", "battery");
    expect(companion).toHaveAttribute("data-anchor", "battery");
    expect(companion).toHaveAttribute("data-origin-anchor", "driver");
    expect(companion).toHaveAttribute("data-travel", "driver-to-battery");
    expect(within(companion).getByText("忆灵")).toBeInTheDocument();
    expect(within(companion).getByText(state.speech)).toBeInTheDocument();
    expect(within(companion).getByText("SOC 9%")).toBeInTheDocument();
    expect(within(companion).getByText("充电偏好")).toBeInTheDocument();
  });

  it("renders as a free stage sprite instead of a fixed information card", () => {
    render(<PetCompanion state={state} />);

    const companion = screen.getByLabelText("忆灵：电量 9%：低电量提醒已亮起，我准备了充电建议。");

    expect(companion).toHaveClass("pet-companion--free");
    expect(within(companion).getByTestId("pet-companion-sprite")).toBeInTheDocument();
    expect(within(companion).getByTestId("pet-companion-speech-bubble")).toHaveTextContent(
      state.cueLabel,
    );
    expect(companion.querySelector(".pet-companion__body")).toBeNull();
  });

  it("places chat anchors on the top-right corner of their dialogue panel", () => {
    const expectedPositions = [
      ["chat_driver", "27.5%", "29%"],
      ["chat_passenger", "94.5%", "29%"],
      ["chat_child", "27.5%", "32%"],
    ] as const;

    for (const [anchor, left, top] of expectedPositions) {
      const { unmount } = render(
        <PetCompanion
          state={{
            ...state,
            originAnchor: anchor,
            anchor,
            travelLabel: `${anchor}-to-${anchor}`,
          }}
        />,
      );

      expect(
        screen.getByLabelText("忆灵：电量 9%：低电量提醒已亮起，我准备了充电建议。"),
      ).toHaveStyle({ left, top });
      unmount();
    }
  });

  it("keeps the drawn fox decorative and exposes real text outside the svg", () => {
    render(<PetCompanion state={state} />);

    const companion = screen.getByLabelText("忆灵：电量 9%：低电量提醒已亮起，我准备了充电建议。");
    const fox = within(companion).getByTestId("memofox-figure");

    expect(fox).toHaveAttribute("aria-hidden", "true");
    expect(fox.tagName.toLowerCase()).toBe("svg");
    expect(companion.querySelector(".pet-companion__rive-layer")).toBeNull();
    expect(companion.querySelector("canvas")).toBeNull();
    expect(within(companion).getByText(state.speech).tagName.toLowerCase()).toBe("p");
  });

  it("renders a layered pet body instead of a flat icon", () => {
    render(<PetCompanion state={state} />);

    const companion = screen.getByLabelText("忆灵：电量 9%：低电量提醒已亮起，我准备了充电建议。");

    expect(within(companion).getByTestId("pet-companion-body-shell")).toBeInTheDocument();
    expect(within(companion).getByTestId("pet-companion-muzzle")).toBeInTheDocument();
    expect(within(companion).getByTestId("pet-companion-forepaws")).toBeInTheDocument();
    expect(within(companion).getByTestId("pet-companion-eye-lids")).toBeInTheDocument();
  });

  it("renders material details that make the SVG pet feel less flat", () => {
    render(<PetCompanion state={state} />);

    const companion = screen.getByLabelText("忆灵：电量 9%：低电量提醒已亮起，我准备了充电建议。");

    expect(within(companion).getByTestId("pet-companion-fur-strands")).toBeInTheDocument();
    expect(within(companion).getByTestId("pet-companion-eye-depth")).toBeInTheDocument();
    expect(within(companion).getByTestId("pet-companion-nose-gloss")).toBeInTheDocument();
    expect(within(companion).getByTestId("pet-companion-paw-pads")).toBeInTheDocument();
  });

  it("marks the pet parts that should visibly animate", () => {
    render(<PetCompanion state={state} />);

    const companion = screen.getByLabelText("忆灵：电量 9%：低电量提醒已亮起，我准备了充电建议。");

    expect(companion).toHaveAttribute("data-motion", "active");
    expect(within(companion).getByTestId("pet-companion-tail")).toHaveAttribute(
      "data-motion-part",
      "tail",
    );
    expect(within(companion).getByTestId("pet-companion-eye-lids")).toHaveAttribute(
      "data-motion-part",
      "blink",
    );
    expect(within(companion).getByTestId("pet-companion-memory-chip")).toHaveAttribute(
      "data-motion-part",
      "memory",
    );
  });
});
