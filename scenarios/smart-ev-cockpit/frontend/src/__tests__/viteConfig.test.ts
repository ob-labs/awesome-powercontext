import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("Vite development API proxy", () => {
  it("proxies same-origin API requests to the local backend", async () => {
    const config = await readFile(resolve(process.cwd(), "vite.config.ts"), "utf8");

    expect(config).toContain("server:");
    expect(config).toContain("proxy:");
    expect(config).toContain('"/api"');
    expect(config).toContain('target: "http://127.0.0.1:8000"');
    expect(config).toContain("changeOrigin: true");
  });
});
