import { describe, expect, it } from "vitest";

import { describeChatSource } from "../chatSource";

describe("describeChatSource", () => {
  it.each([
    [[{ type: "CHAT" }, { type: "ADD" }, { type: "SEARCH" }], "PowerContext ADD + LLM"],
    [[{ type: "CHAT" }, { type: "UPDATE" }], "PowerContext UPDATE + LLM"],
    [[{ type: "CHAT" }, { type: "DELETE" }], "PowerContext DELETE + LLM"],
    [[{ type: "CHAT" }, { type: "SEARCH" }], "PowerContext SEARCH + LLM"],
    [[{ type: "CHAT" }], "LLM"],
    [[], "LLM"],
  ])("maps %o to %s", (operations, expected) => {
    expect(describeChatSource(operations)).toBe(expected);
  });

  it("prioritizes a mutation over search evidence", () => {
    expect(describeChatSource([{ type: "SEARCH" }, { type: "UPDATE" }])).toBe(
      "PowerContext UPDATE + LLM",
    );
  });
});
