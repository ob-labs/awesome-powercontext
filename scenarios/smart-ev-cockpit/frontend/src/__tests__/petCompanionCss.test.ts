import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(process.cwd(), "src/styles/app.css"), "utf8");

function extractRule(selector: string) {
  const escapedSelector = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`${escapedSelector}\\s*\\{(?<body>[\\s\\S]*?)\\n\\}`));
  return match?.groups?.body ?? "";
}

describe("pet companion motion CSS", () => {
  it("renders the companion as a free stage sprite instead of a framed card", () => {
    const rootRule = extractRule(".pet-companion");
    const spriteRule = extractRule(".pet-companion__sprite");
    const bubbleRule = extractRule(".pet-companion__speech-bubble");
    const compactCopyRule = extractRule(
      ".pet-companion__speech-bubble p,\n.pet-companion__speech-bubble b",
    );

    expect(rootRule).toContain("position: absolute;");
    expect(rootRule).toContain("z-index: 60;");
    expect(rootRule).toContain("pointer-events: none;");
    expect(rootRule).toContain("transform: translate(-50%, -50%);");
    expect(rootRule).toContain("width: clamp(116px, 9.75vw, 173px);");
    expect(css).toContain("width: clamp(105px, 16.2vw, 155px);");
    expect(css).toContain("width: 105px;");
    expect(css).toContain("width: 105px;\n    z-index: 60;");
    expect(rootRule).not.toContain("border:");
    expect(spriteRule).toContain("animation: pet-sprite-idle");
    expect(bubbleRule).toContain("position: absolute;");
    expect(bubbleRule).toContain("max-width: 128px;");
    expect(compactCopyRule).toContain("clip-path: inset(50%);");
  });

  it("lets chat-corner pet anchors appear above the chat panel without taking input", () => {
    const chatAnchorRule = extractRule(
      '.pet-companion[data-anchor="chat_driver"],\n.pet-companion[data-anchor="chat_passenger"],\n.pet-companion[data-anchor="chat_child"]',
    );

    expect(chatAnchorRule).toContain("z-index: 61;");
    expect(chatAnchorRule).not.toContain("pointer-events: auto;");
  });

  it("uses SVG transform boxes so tail, ears, eyelids, and chip animation is visible", () => {
    const animatedSvgRule = extractRule(
      ".pet-companion__tail,\n.pet-companion__ears,\n.pet-companion__eye-lids,\n.pet-companion__memory-chip",
    );

    expect(animatedSvgRule).toContain("transform-box: fill-box;");
    expect(animatedSvgRule).toContain("transform-origin: center;");
    expect(css).toContain("@keyframes pet-eye-blink");
    expect(css).toContain("@keyframes pet-tail-signal");
  });

  it("adds articulated body motion instead of moving the whole sprite as one icon", () => {
    const headRule = extractRule(".pet-companion__head-group");
    const pawRule = extractRule(".pet-companion__forepaws");
    const groundRule = extractRule(".pet-companion__ground");

    expect(headRule).toContain("animation: pet-head-bob");
    expect(pawRule).toContain("animation: pet-paw-step");
    expect(groundRule).toContain("animation: pet-ground-shadow");
    expect(css).toContain("@keyframes pet-head-bob");
    expect(css).toContain("@keyframes pet-paw-step");
    expect(css).toContain("@keyframes pet-ground-shadow");
  });

  it("adds realistic SVG material treatment for fur, eyes, nose, and paws", () => {
    const furRule = extractRule(".pet-companion__fur-strands");
    const eyeDepthRule = extractRule(".pet-companion__eye-depth");
    const noseGlossRule = extractRule(".pet-companion__nose-gloss");
    const pawPadRule = extractRule(".pet-companion__paw-pads ellipse");

    expect(furRule).toContain("animation: pet-fur-shimmer");
    expect(eyeDepthRule).toContain("fill: url(\"#memofox-eye-depth\")");
    expect(noseGlossRule).toContain("fill: url(\"#memofox-nose-gloss\")");
    expect(pawPadRule).toContain("fill: rgb(3 28 31 / 72%);");
    expect(css).toContain("@keyframes pet-fur-shimmer");
  });

  it("does not keep Rive canvas styles in the pet sprite", () => {
    expect(css).not.toContain("pet-companion__rive");
    expect(css).not.toContain("mix-blend-mode: multiply;");
  });

  it("highlights cockpit targets when the pet travels to them", () => {
    const driverRule = extractRule(
      '.cockpit-stage[data-pet-origin-anchor="driver"] .seat-occupant--driver .seat-occupant',
    );
    const climateRule = extractRule('.infotainment-display__climate-card[data-pet-focus="true"]');

    expect(driverRule).toContain("box-shadow:");
    expect(climateRule).toContain("animation: pet-target-pulse");
  });
});
