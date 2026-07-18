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
  it("ships a self-contained 16-slide HTML PPT in the frontend folder", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const slideCount = (html.match(/<section class="slide/g) ?? []).length;

    expect(slideCount).toBe(16);
    expect(html).toContain("PowerMem");
    expect(html).toContain("Smart EV Cockpit");
    expect(html).toContain("AI 应用为什么需要记忆");
    expect(html).toContain("智能座舱记忆的五个卖点");
    expect(html).toContain("LOCOMO：可量化的记忆优势");
    expect(html).toContain("data-total=\"16\"");
    expect(html).toContain("KeyboardEvent");
    expect(html).toContain("ArrowRight");
    expect(html).toContain("smart-ev-cockpit-bg.png");
    expect(html).toContain("vehicle-cockpit-background");
    expect(html).not.toMatch(/https?:\/\//);
  });

  it("keeps the deck aligned to the requested narrative order", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const productStart = html.indexOf("PowerMem 核心特性");
    const cockpitStart = html.indexOf("座舱记忆模型");
    const valueStart = html.indexOf("智能座舱记忆的五个卖点");

    expect(productStart).toBeGreaterThan(-1);
    expect(cockpitStart).toBeGreaterThan(productStart);
    expect(valueStart).toBeGreaterThan(cockpitStart);
  });

  it("uses one Hermes Cyber cockpit-dark visual system across the whole deck", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");

    expect(html).toContain(
      '<body data-total="16" data-theme="hermes-cyber">',
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
      "基于艾宾浩斯遗忘曲线的记忆遗忘管理",
      "智能记忆提取",
      "经验/skills 蒸馏",
      "混合检索/多路召回",
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

    expect(html).toContain("font-size: clamp(22px, 2.6vw, 42px);");
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

    expect(h1Rule).toContain("font-size: clamp(28px, 4.2vw, 64px);");
    expect(h2Rule).toContain("font-size: clamp(22px, 2.6vw, 42px);");
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
      "20 minutes = 58.2%",
      "31 days = 21.1%",
      "ScopeController",
      "PermissionController",
      "CollaborationCoordinator",
      "PrivacyProtector",
      "SOA vehicle state diff",
      "智能座舱记忆的五个卖点",
      "端云协同记忆：快、稳、可同步",
      "GIS 联动：位置感和路线感",
    ];

    for (const term of requiredTerms) {
      expect(html).toContain(term);
    }
  });

  it("keeps the architecture redesign scoped to the approved slide set", () => {
    expect(existsSync(deckPath)).toBe(true);

    const html = readFileSync(deckPath, "utf8");
    const architectureSlides = [
      'data-slide="6"',
      'data-slide="8"',
      'data-slide="10"',
      'data-slide="11"',
      'data-slide="12"',
      'data-slide="15"',
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

    expect((html.match(/<section class="slide/g) ?? []).length).toBe(16);
    expect(html).not.toMatch(/TODO|TBD|PLACEHOLDER/);
  });
});
