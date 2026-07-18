import { describe, expect, it } from "vitest";

import { describeChatSource } from "../chatSource";

describe("describeChatSource", () => {
  it.each([
    [[{ type: "CHAT" }, { type: "ADD" }, { type: "SEARCH" }], "PowerMem ADD + LLM"],
    [[{ type: "CHAT" }, { type: "UPDATE" }], "PowerMem UPDATE + LLM"],
    [[{ type: "CHAT" }, { type: "DELETE" }], "PowerMem DELETE + LLM"],
    [[{ type: "CHAT" }, { type: "SEARCH" }], "PowerMem SEARCH + LLM"],
    [[{ type: "CHAT" }], "LLM"],
    [[], "LLM"],
  ])("maps %o to %s", (operations, expected) => {
    expect(describeChatSource(operations)).toBe(expected);
  });

  it("prioritizes a mutation over search evidence", () => {
    expect(describeChatSource([{ type: "SEARCH" }, { type: "UPDATE" }])).toBe(
      "PowerMem UPDATE + LLM",
    );
  });
});
