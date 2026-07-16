import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DialoguePanel } from "../DialoguePanel";
import type { DialogueMessage } from "../DialoguePanel";

const longHistory: DialogueMessage[] = Array.from({ length: 12 }, (_, index) => ({
  id: `message-${index}`,
  role: index % 2 === 0 ? "user" : "assistant",
  text: `历史回复 ${index + 1}`,
}));

describe("DialoguePanel", () => {
  it("renders a persistent in-panel scrollbar for chat history", () => {
    const { container } = render(
      <DialoguePanel
        utterance=""
        messages={longHistory}
        onUtteranceChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    const chatLog = screen.getByRole("log", { name: "Recent conversation" });
    const scrollbar = container.querySelector(".dialogue-panel__scrollbar");
    const thumb = container.querySelector(".dialogue-panel__scrollbar-thumb");

    expect(chatLog).toHaveAttribute("data-custom-scrollbar", "true");
    expect(scrollbar).toHaveAttribute("data-scrollbar-track", "visible");
    expect(scrollbar).toHaveAttribute("aria-hidden", "true");
    expect(thumb).toBeInTheDocument();
  });

  it("lets the visible scrollbar control the message scroll position", () => {
    const { container } = render(
      <DialoguePanel
        utterance=""
        messages={longHistory}
        onUtteranceChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    const chatLog = screen.getByRole("log", { name: "Recent conversation" });
    const scrollbar = container.querySelector(".dialogue-panel__scrollbar");
    expect(scrollbar).not.toBeNull();
    Object.defineProperty(chatLog, "clientHeight", { value: 100, configurable: true });
    Object.defineProperty(chatLog, "scrollHeight", { value: 300, configurable: true });
    Object.defineProperty(chatLog, "scrollTop", {
      value: 0,
      writable: true,
      configurable: true,
    });
    vi.spyOn(scrollbar as Element, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      bottom: 100,
      right: 8,
      width: 8,
      height: 100,
      toJSON: () => ({}),
    });

    fireEvent(scrollbar as Element, new MouseEvent("pointerdown", {
      bubbles: true,
      clientY: 75,
    }));

    expect(chatLog.scrollTop).toBe(150);
  });

  it("scrolls to the latest message when the conversation grows", () => {
    const firstMessages = longHistory.slice(0, 3);
    const nextMessages = [
      ...firstMessages,
      {
        id: "assistant-new",
        role: "assistant" as const,
        text: "新的 PowerMem 回复",
      },
    ];
    const { rerender } = render(
      <DialoguePanel
        utterance=""
        messages={firstMessages}
        onUtteranceChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    const chatLog = screen.getByRole("log", { name: "Recent conversation" });
    Object.defineProperty(chatLog, "clientHeight", { value: 100, configurable: true });
    Object.defineProperty(chatLog, "scrollHeight", { value: 360, configurable: true });
    Object.defineProperty(chatLog, "scrollTop", {
      value: 0,
      writable: true,
      configurable: true,
    });

    rerender(
      <DialoguePanel
        utterance=""
        messages={nextMessages}
        onUtteranceChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(chatLog.scrollTop).toBe(260);
  });

  it("submits the current utterance when Enter is pressed", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <DialoguePanel
        utterance="放点适合孩子睡觉的内容。"
        messages={[]}
        onUtteranceChange={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    fireEvent.keyDown(screen.getByRole("textbox", { name: "Utterance" }), {
      key: "Enter",
      code: "Enter",
    });

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith("放点适合孩子睡觉的内容。");
    });
  });

  it("keeps Shift+Enter available for multiline input", () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <DialoguePanel
        utterance="第一行"
        messages={[]}
        onUtteranceChange={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    fireEvent.keyDown(screen.getByRole("textbox", { name: "Utterance" }), {
      key: "Enter",
      code: "Enter",
      shiftKey: true,
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("does not send duplicate requests while an Enter submission is pending", async () => {
    let resolveSubmit: () => void = () => {};
    const onSubmit = vi.fn(
      () => new Promise<void>((resolve) => {
        resolveSubmit = resolve;
      }),
    );
    render(
      <DialoguePanel
        utterance="有点冷。"
        messages={[]}
        onUtteranceChange={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    const textbox = screen.getByRole("textbox", { name: "Utterance" });
    fireEvent.keyDown(textbox, { key: "Enter", code: "Enter" });
    fireEvent.keyDown(textbox, { key: "Enter", code: "Enter" });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    resolveSubmit();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Send" })).not.toBeDisabled();
    });
  });
});
