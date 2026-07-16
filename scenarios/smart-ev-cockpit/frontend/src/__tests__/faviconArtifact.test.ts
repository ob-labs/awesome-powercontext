import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("frontend favicon artifact", () => {
  it("uses the OceanBase PNG as the browser tab favicon", () => {
    const faviconPath = resolve(process.cwd(), "public/oceanbase.png");
    const htmlPath = resolve(process.cwd(), "index.html");

    expect(existsSync(faviconPath)).toBe(true);
    expect(readFileSync(htmlPath, "utf8")).toContain(
      '<link rel="icon" type="image/png" href="/oceanbase.png" />',
    );
  });
});
