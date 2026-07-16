import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const deckPath = resolve(
  process.cwd(),
  "public/powermem-smart-ev-cockpit-deck.html",
);

function extractCssRule(html: string, selector: string) {
  const escapedSelector = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = html.match(new RegExp(`${escapedSelector}\\s*\\{(?<body>[\\s\\S]*?)\\n\\s*\\}`));
  return match?.groups?.body ?? "";
}

describe("PowerMem smart EV cockpit HTML deck artifact", () => {
  it("ships a self-contained 20-slide HTML PPT in the frontend folder", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const slideCount = (html.match(/<section class="slide/g) ?? []).length;

    expect(slideCount).toBe(20);
    expect(html).toContain("PowerMem");
    expect(html).toContain("Smart EV Cockpit");
    expect(html).toContain("AI 应用为什么需要记忆");
    expect(html).toContain("PowerMem 在智能座舱中的能力");
    expect(html).toContain("smart-ev-cockpit demo 项目");
    expect(html).toContain("powermem 产品介绍.pptx");
    expect(html).toContain("data-total=\"20\"");
    expect(html).toContain("KeyboardEvent");
    expect(html).toContain("ArrowRight");
    expect(html).toContain("smart-ev-cockpit-bg.png");
    expect(html).toContain("vehicle-cockpit-background");
    expect(html).not.toMatch(/https?:\/\//);
  });

  it("keeps the deck aligned to the requested narrative order", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const productStart = html.indexOf("完整介绍 PowerMem 能力");
    const cockpitStart = html.indexOf("PowerMem 在智能座舱中的能力");
    const demoStart = html.indexOf('<section class="slide dark" data-slide="18">');

    expect(productStart).toBeGreaterThan(-1);
    expect(cockpitStart).toBeGreaterThan(productStart);
    expect(demoStart).toBeGreaterThan(cockpitStart);
    expect(html.indexOf("smart-ev-cockpit demo 项目", demoStart)).toBeGreaterThan(
      demoStart,
    );
  });

  it("uses one unified cockpit-dark visual system across the whole deck", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");

    expect(html).toContain(
      '<body data-total="20" data-theme="unified-cockpit-dark">',
    );
    expect(html).toContain('--cockpit-bg: url("smart-ev-cockpit-bg.png");');
    expect(html).not.toContain("--paper:");
    expect(html).not.toContain("color-scheme: light");
    expect(html).not.toMatch(/\.cover\s*\{[^}]*background:/s);
    expect(html).not.toMatch(/\.dark\s*\{[^}]*background:/s);
  });

  it("fully covers PowerMem capabilities with denser title sizing", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const capabilityTerms = [
      "Memory Item 数据模型",
      "提取、归一、去重",
      "ADD / UPDATE / MERGE / DELETE",
      "语义向量 + 全文关键词 + 图关系",
      "Ebbinghaus",
      "多模态记忆",
      "SDK / MCP / HTTP / CLI",
      "Dashboard / Observability",
      "Multi-Agent",
      "权限与隐私治理",
      "存储与模型可插拔",
      "评估指标",
    ];

    for (const term of capabilityTerms) {
      expect(html).toContain(term);
    }

    expect(html).toContain("font-size: clamp(24px, 3vw, 50px);");
    expect(html).not.toContain("font-size: clamp(30px, 3.4vw, 54px);");
    expect(html).not.toContain("font-size: clamp(40px, 4.8vw, 82px);");
  });

  it("keeps large slide titles on one line with responsive sizing", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const h1Rule = extractCssRule(html, "h1");
    const h2Rule = extractCssRule(html, "h2");

    for (const rule of [h1Rule, h2Rule]) {
      expect(rule).toContain("grid-column: 1 / 16;");
      expect(rule).toContain("max-width: none;");
      expect(rule).toContain("white-space: nowrap;");
      expect(rule).toContain("text-wrap: nowrap;");
    }

    expect(h1Rule).toContain("font-size: clamp(34px, 4.7vw, 78px);");
    expect(h2Rule).toContain("font-size: clamp(24px, 3vw, 50px);");
    expect(html).toContain("font-size: clamp(18px, 4.8vw, 26px);");
    expect(html).toContain("font-size: clamp(20px, 5.6vw, 30px);");
    expect(html).not.toContain("font-size: clamp(30px, 10vw, 46px);");
  });

  it("renders source-aligned architecture diagrams from the PowerMem product deck", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const requiredTerms = [
      "deck-architecture",
      "Python SDK",
      "CLI / pmem",
      "智能记忆处理器",
      "Accurate +65.90%",
      "Agile 91.83%",
      "Affordable 96.53%",
      "LLM 判定 Actions",
      "ADD / UPDATE / DELETE / NONE",
      "User Profile",
      "RRF / rerank",
      "final_score = relevance_score × decay_factor",
      "R(t) = e^(-t/S)",
      "ScopeController",
      "PermissionController",
      "CollaborationCoordinator",
      "PrivacyProtector",
      "SOA vehicle state diff",
      "Evidence Trace",
    ];

    for (const term of requiredTerms) {
      expect(html).toContain(term);
    }
  });

  it("keeps the architecture redesign scoped to the approved slide set", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const architectureSlides = [
      'data-slide="5"',
      'data-slide="7"',
      'data-slide="9"',
      'data-slide="10"',
      'data-slide="11"',
      'data-slide="15"',
      'data-slide="18"',
      'data-slide="19"',
    ];

    for (const slideMarker of architectureSlides) {
      const markerIndex = html.indexOf(slideMarker);
      const nextSlideIndex = html.indexOf("<section", markerIndex + 1);
      const slideHtml = html.slice(
        markerIndex,
        nextSlideIndex === -1 ? html.length : nextSlideIndex,
      );

      expect(markerIndex).toBeGreaterThan(-1);
      expect(slideHtml).toMatch(/diagram-|architecture-|flow-|swimlane|business-loop/);
    }

    expect((html.match(/<section class="slide/g) ?? []).length).toBe(20);
    expect(html).not.toMatch(/TODO|TBD|PLACEHOLDER/);
  });
});
