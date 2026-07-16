import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SeatOccupantSelector } from "../SeatOccupantSelector";
import type { UserIdentity } from "../../types/api";

const identities: UserIdentity[] = [
  {
    actor_id: "driver_primary",
    seat_position: "front_left",
    user_id: "guest_alex",
    display_name: "Alex",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
  {
    actor_id: "passenger_front",
    seat_position: "front_right",
    user_id: "passenger_front",
    display_name: "Passenger",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
  {
    actor_id: "child_rear_left",
    seat_position: "rear_left",
    user_id: "child_rear_left",
    display_name: "Child",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
];

describe("SeatOccupantSelector", () => {
  it("renders a settings control for each occupant without replacing selection", async () => {
    const onSelect = vi.fn();
    const onOpenSettings = vi.fn();
    const user = userEvent.setup();
    render(
      <SeatOccupantSelector
        selectedActorId="driver_primary"
        identities={identities}
        onSelect={onSelect}
        onOpenSettings={onOpenSettings}
      />,
    );

    const selector = screen.getByLabelText("Seat occupant selector");
    expect(within(selector).getByRole("button", { name: "Driver" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    await user.click(
      within(selector).getByRole("button", {
        name: "Configure Driver profile",
      }),
    );

    expect(onOpenSettings).toHaveBeenCalledWith("driver_primary", "front_left");
    expect(onSelect).not.toHaveBeenCalled();
    expect(within(selector).getByText("guest_alex")).toBeInTheDocument();
  });
});
