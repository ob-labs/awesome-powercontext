import { describe, expect, it } from "vitest";

import { getScenarioStepsForDate, seasonForDate } from "../i18n";

describe("seasonal scenario copy", () => {
  it("maps calendar dates to demo seasons", () => {
    expect(seasonForDate(new Date(2026, 2, 1))).toBe("spring");
    expect(seasonForDate(new Date(2026, 6, 12))).toBe("summer");
    expect(seasonForDate(new Date(2026, 8, 1))).toBe("autumn");
    expect(seasonForDate(new Date(2026, 11, 1))).toBe("winter");
  });

  it("uses a summer cabin preference for the July demo date", () => {
    const zhSteps = getScenarioStepsForDate("zh", new Date(2026, 6, 12));
    const enSteps = getScenarioStepsForDate("en", new Date(2026, 6, 12));

    expect(zhSteps[0].utterance).toBe(
      "我夏天上车一般 23C，座椅加热 0 档。",
    );
    expect(enSteps[0].utterance).toBe(
      "I usually set 23C and seat heat level 0 when I get in during summer.",
    );
    expect(zhSteps[1]).toMatchObject({
      utterance: "车里有点热。",
      initialHvacTargetTempC: 28.5,
    });
    expect(enSteps[1]).toMatchObject({
      utterance: "It feels a bit warm in here.",
      initialHvacTargetTempC: 28.5,
    });
  });

  it("keeps the warmer winter cabin preference in winter", () => {
    const zhSteps = getScenarioStepsForDate("zh", new Date(2026, 0, 12));
    const enSteps = getScenarioStepsForDate("en", new Date(2026, 0, 12));

    expect(zhSteps[0].utterance).toBe(
      "我冬天上车一般 26C，座椅加热 2 档。",
    );
    expect(enSteps[0].utterance).toBe(
      "I usually set 26C and seat heat level 2 when I get in during winter.",
    );
    expect(zhSteps[1]).toMatchObject({
      utterance: "有点冷。",
      initialHvacTargetTempC: 18,
    });
    expect(enSteps[1]).toMatchObject({
      utterance: "I feel a bit cold.",
      initialHvacTargetTempC: 18,
    });
  });
});
