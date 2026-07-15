import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(process.cwd(), "src/styles/app.css"), "utf8");

function extractRule(selector: string) {
  const escapedSelector = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`${escapedSelector}\\s*\\{(?<body>[\\s\\S]*?)\\n\\}`));
  return match?.groups?.body ?? "";
}

describe("infotainment scene card CSS", () => {
  it("keeps scene titles on one line without ellipsis truncation", () => {
    const copyRule = extractRule(".infotainment-display__scene-copy");
    const titleRule = extractRule(".infotainment-display__scene-copy h2");

    expect(copyRule).toContain("max-width: min(82%, 390px);");
    expect(titleRule).toContain("max-width: 100%;");
    expect(titleRule).toContain("font-size: clamp(13px, 1.04vw, 22px);");
    expect(titleRule).toContain("white-space: nowrap;");
    expect(titleRule).not.toContain("text-overflow: ellipsis;");
    expect(titleRule).not.toContain("overflow: hidden;");
    expect(titleRule).not.toContain("max-width: 13ch;");
  });
});
