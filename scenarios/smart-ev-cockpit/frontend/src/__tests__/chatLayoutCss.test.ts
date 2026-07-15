import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const css = readFileSync(resolve(process.cwd(), "src/styles/app.css"), "utf8");

function extractRule(selector: string) {
  const escapedSelector = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`${escapedSelector}\\s*\\{(?<body>[\\s\\S]*?)\\n\\}`));
  return match?.groups?.body ?? "";
}

describe("floating chat layout CSS", () => {
  it("keeps the desktop chat window compact and above occupant anchors", () => {
    const driverRule = extractRule(".voice-command-panel");
    const childRule = extractRule('.voice-command-panel[data-anchor-actor="child_rear_left"]');
    const driverOccupantRule = extractRule(".seat-occupant--driver");
    const childOccupantRule = extractRule(".seat-occupant--child");

    expect(driverRule).toContain("top: 31%;");
    expect(driverRule).toContain("width: min(27vw, 430px);");
    expect(childRule).toContain("left: 18%;");
    expect(childRule).toContain("top: 34%;");
    expect(childRule).toContain("width: min(24vw, 380px);");
    expect(childRule).not.toContain("left: 50%;");
    expect(driverOccupantRule).toContain("top: 75%;");
    expect(childOccupantRule).toContain("top: 86.5%;");
  });

  it("uses normal vertical flow for scrollable chat history", () => {
    const messageRule = extractRule(".dialogue-panel__messages");
    const userMessageRule = extractRule(".dialogue-message--user");
    const assistantMessageRule = extractRule(".dialogue-message--assistant");

    expect(messageRule).toContain("overflow-y: scroll;");
    expect(messageRule).toContain("display: flex;");
    expect(messageRule).toContain("flex-direction: column;");
    expect(messageRule).not.toContain("align-content: end;");
    expect(userMessageRule).toContain("margin-left: auto;");
    expect(assistantMessageRule).toContain("margin-right: auto;");
  });

  it("uses transparent glass for the chat window while keeping readable message bubbles", () => {
    const panelRule = extractRule(".voice-command-panel .dialogue-panel");
    const messageRule = extractRule(".dialogue-panel__messages");
    const userBubbleRule = extractRule(".dialogue-message--user p");
    const assistantBubbleRule = extractRule(".dialogue-message--assistant p,\n.dialogue-panel__empty");

    expect(panelRule).toContain("background: transparent;");
    expect(panelRule).toContain("backdrop-filter: blur(22px) saturate(1.35) contrast(1.06);");
    expect(panelRule).not.toContain("rgb(7 15 17 / 94%)");
    expect(messageRule).toContain("background: transparent;");
    expect(messageRule).toContain("backdrop-filter: blur(22px) saturate(1.35) contrast(1.06);");
    expect(messageRule).not.toContain("rgb(6 18 20 / 46%)");
    expect(messageRule).not.toContain("rgb(255 255 255 / 86%)");
    expect(messageRule).not.toContain("rgb(221 231 227 / 92%)");
    expect(userBubbleRule).toContain("background:");
    expect(assistantBubbleRule).toContain("background:");
  });

  it("keeps the child chat compact so cockpit controls remain reachable", () => {
    const childPanelRule = extractRule(
      '.voice-command-panel[data-anchor-actor="child_rear_left"] .dialogue-panel',
    );

    expect(childPanelRule).toContain("height: clamp(280px, 32dvh, 380px);");
  });

  it("places manual cockpit buttons lower on the screen while left of right-side text", () => {
    const manualKeysRule = extractRule(".manual-cockpit-keys");
    const buttonsRule = extractRule(".manual-cockpit-keys__buttons");

    expect(manualKeysRule).toContain("left: 44%;");
    expect(manualKeysRule).toContain("top: 31.2%;");
    expect(manualKeysRule).toContain("width: min(38vw, 560px);");
    expect(manualKeysRule).toContain("min-width: 0;");
    expect(manualKeysRule).toContain("display: flex;");
    expect(manualKeysRule).toContain("align-items: center;");
    expect(manualKeysRule).toContain("transform: translate(-50%, -2px) scale(0.92);");
    expect(manualKeysRule).toContain("transform-origin: top center;");
    expect(manualKeysRule).not.toContain("bottom:");
    expect(buttonsRule).toContain("flex: 0 0 auto;");
    expect(css).not.toContain(".manual-cockpit-keys__day");
  });

  it("keeps manual cockpit keys on a fixed leather palette instead of following interior themes", () => {
    const buttonsRule = extractRule(".manual-cockpit-keys__buttons");
    const buttonRule = extractRule(".manual-cockpit-keys button");
    const hoverRule = extractRule(".manual-cockpit-keys button:hover:not(:disabled)");
    const statusRule = extractRule(".manual-cockpit-keys__status");

    expect(buttonRule).toContain("rgb(235 232 222 / 88%)");
    expect(`${buttonsRule}${buttonRule}${hoverRule}${statusRule}`).not.toContain(
      "--interior-",
    );
  });

  it("removes the visible lower support frame and keeps smaller metallic buttons on the leather area", () => {
    const buttonsRule = extractRule(".manual-cockpit-keys__buttons");
    const buttonRule = extractRule(".manual-cockpit-keys button");
    const iconRule = extractRule(".manual-cockpit-keys button svg");
    const statusRule = extractRule(".manual-cockpit-keys__status");

    expect(statusRule).toContain("position: absolute;");
    expect(statusRule).toContain("clip-path: inset(50%);");
    expect(buttonsRule).toContain("max-width: 100%;");
    expect(buttonsRule).toContain("overflow: visible;");
    expect(buttonsRule).toContain("border: 0;");
    expect(buttonsRule).toContain("background: transparent;");
    expect(buttonsRule).toContain("box-shadow: none;");
    expect(buttonsRule).toContain("padding: 0;");
    expect(buttonRule).toContain("min-height: 36px;");
    expect(buttonRule).toContain("padding: 0 13px;");
    expect(buttonRule).toContain("linear-gradient(180deg, rgb(98 103 99 / 88%)");
    expect(iconRule).toContain("width: 14px;");
    expect(iconRule).toContain("height: 14px;");
  });
});
