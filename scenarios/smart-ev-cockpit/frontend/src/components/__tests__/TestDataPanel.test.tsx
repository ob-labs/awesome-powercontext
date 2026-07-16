import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TestDataPanel } from "../TestDataPanel";
import type { TestDataStatus } from "../../types/api";

const generatedStatus: TestDataStatus = {
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

describe("TestDataPanel", () => {
  it("renders only generate-data and clear-data actions", () => {
    render(
      <TestDataPanel
        status={generatedStatus}
        isBusy={false}
        error={null}
        onGenerate={vi.fn()}
        onClear={vi.fn()}
      />,
    );

    expect(screen.getByRole("spinbutton", { name: /memory count/i })).toHaveValue(1200);
    expect(screen.getAllByRole("button")).toHaveLength(2);
    expect(
      screen.getByRole("button", { name: /generate and import 1200 memories/i }),
    ).toHaveTextContent("Generate Data");
    expect(screen.getByRole("button", { name: /clear all powermem memories/i })).toHaveTextContent(
      "Clear Data",
    );
    expect(
      screen.queryByRole("button", { name: /import to powermem/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("smart_ev_cockpit_20260708_1200_seed42")).toBeInTheDocument();
    expect(screen.getByText(/1200 generated/i)).toBeInTheDocument();
  });

  it("keeps full database cleanup available when no dataset exists", () => {
    render(
      <TestDataPanel
        status={null}
        isBusy={false}
        error={null}
        onGenerate={vi.fn()}
        onClear={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: /generate and import 1200 memories/i }),
    ).toBeEnabled();
    expect(
      screen.getByRole("button", { name: /clear all powermem memories/i }),
    ).toBeEnabled();
  });

  it("shows import progress while a dataset is importing", () => {
    render(
      <TestDataPanel
        status={{
          ...generatedStatus,
          state: "importing",
          imported_count: 240,
        }}
        isBusy
        error={null}
        onGenerate={vi.fn()}
        onClear={vi.fn()}
      />,
    );

    expect(screen.getByText(/240 \/ 1200 imported/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /generate and import 1200 memories/i }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /clear all powermem memories/i }),
    ).toBeDisabled();
  });

  it("enables clear after the dataset is imported", () => {
    render(
      <TestDataPanel
        status={{
          ...generatedStatus,
          state: "imported",
          imported_count: 1200,
        }}
        isBusy={false}
        error={null}
        onGenerate={vi.fn()}
        onClear={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: /clear all powermem memories/i }),
    ).toBeEnabled();
    expect(screen.getByText(/1200 imported/i)).toBeInTheDocument();
  });

  it("calls generate and clear handlers", async () => {
    const onGenerate = vi.fn();
    const onClear = vi.fn();
    const user = userEvent.setup();

    render(
      <TestDataPanel
        status={generatedStatus}
        isBusy={false}
        error={null}
        onGenerate={onGenerate}
        onClear={onClear}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: /generate and import 1200 memories/i }),
    );
    await user.click(
      screen.getByRole("button", { name: /clear all powermem memories/i }),
    );

    expect(onGenerate).toHaveBeenCalledWith(1200);
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("calls generate with the configured memory count", async () => {
    const onGenerate = vi.fn();
    const user = userEvent.setup();

    render(
      <TestDataPanel
        status={null}
        isBusy={false}
        error={null}
        onGenerate={onGenerate}
        onClear={vi.fn()}
      />,
    );

    await user.clear(screen.getByRole("spinbutton", { name: /memory count/i }));
    await user.type(screen.getByRole("spinbutton", { name: /memory count/i }), "250");
    await user.click(
      screen.getByRole("button", { name: /generate and import 250 memories/i }),
    );

    expect(onGenerate).toHaveBeenCalledWith(250);
  });

  it("falls back to 1200 memories when the count input is empty", async () => {
    const onGenerate = vi.fn();
    const user = userEvent.setup();

    render(
      <TestDataPanel
        status={null}
        isBusy={false}
        error={null}
        onGenerate={onGenerate}
        onClear={vi.fn()}
      />,
    );

    await user.clear(screen.getByRole("spinbutton", { name: /memory count/i }));
    await user.click(
      screen.getByRole("button", { name: /generate and import 1200 memories/i }),
    );

    expect(onGenerate).toHaveBeenCalledWith(1200);
  });
});
