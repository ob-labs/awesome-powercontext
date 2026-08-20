import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CockpitStage } from "../CockpitStage";
import type { PetCompanionState } from "../../view-models/petCompanion";
import type { ProjectionScene, ScenarioStep } from "../../view-models/projection";

const steps: ScenarioStep[] = [
  {
    day: "Day 45",
    act: "Act 6",
    actKey: "Act 6",
    utterance: "I feel cold.",
    actorId: "driver_primary",
    seatPosition: "front_left",
  },
  {
    day: "Day 56",
    act: "Act 9",
    actKey: "Act 9",
    utterance: "Prepare for a long highway trip with low battery.",
    actorId: "driver_primary",
    seatPosition: "front_left",
  },
];

const projection: ProjectionScene = {
  id: "Day 45-Act 6",
  mode: "scenario",
  title: "Cold cabin comfort",
  subtitle: "Driver comfort routine adapts to cold cabin context.",
  scoreLabel: "Ready",
  dockLabel: "Day 45",
  chips: [
    { label: "Actor", value: "Driver" },
    { label: "Scene", value: "Act 6" },
    { label: "Source", value: "Scenario" },
  ],
  routeReadout: "Cabin +2°C, seat heat level 2",
  mapLabel: "Scene trace",
  showMap: true,
  privacyLabel: "Synthetic data only",
  status: "idle",
};

const petState: PetCompanionState = {
  name: "忆灵",
  mood: "curious",
  action: "capture_preference",
  target: "climate",
  originAnchor: "driver",
  anchor: "climate",
  travelLabel: "driver-to-climate",
  speech: "我把这组座舱温度和座椅设置记成可复用偏好。",
  cueLabel: "空调和座椅偏好",
  memoryOrbLabel: "偏好记忆",
};

afterEach(() => {
  vi.useRealTimers();
});

describe("CockpitStage", () => {
  it("renders a single active scene card with battery, climate, and media cards", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 6, 10, 11, 26, 0));

    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        onSelectScenario={vi.fn()}
      />,
    );

    expect(
      screen.getByAltText("Premium smart EV cockpit interior"),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Holographic PowerContext evidence projection"),
    ).not.toBeInTheDocument();
    const display = screen.getByLabelText("Panoramic PowerContext display");
    const sceneCard = within(display).getByLabelText(
      "PowerContext projection summary",
    );

    expect(within(sceneCard).getByText("Day 45")).toBeInTheDocument();
    expect(within(sceneCard).getByText("Act 6")).toBeInTheDocument();
    expect(within(sceneCard).getByText("Cold cabin comfort")).toBeInTheDocument();
    expect(
      within(sceneCard).getByText(
        "Driver comfort routine adapts to cold cabin context.",
      ),
    ).toBeInTheDocument();
    expect(
      within(sceneCard).getByText("Cabin +2°C, seat heat level 2"),
    ).toBeInTheDocument();
    expect(within(sceneCard).queryByText("Scene trace")).not.toBeInTheDocument();
    expect(within(sceneCard).queryByText("Synthetic data only")).not.toBeInTheDocument();
    expect(within(sceneCard).queryByText("Actor")).not.toBeInTheDocument();
    expect(within(sceneCard).queryByText("Source")).not.toBeInTheDocument();
    expect(
      within(display).queryByRole("button", { name: /day 90 act 10/i }),
    ).not.toBeInTheDocument();
    expect(within(display).queryByText("PowerContext Drive")).not.toBeInTheDocument();
    expect(display.querySelector(".infotainment-display__topbar")).not.toHaveTextContent(
      "Day 45",
    );
    const batteryCard = within(display).getByLabelText("Battery status");
    expect(batteryCard).toHaveAttribute("data-battery-state", "normal");
    expect(batteryCard).toHaveTextContent("62%");
    expect(batteryCard).toHaveTextContent("305 km");
    expect(batteryCard).toHaveTextContent("Energy stable");
    expect(
      batteryCard.querySelector(".infotainment-display__battery-fill"),
    ).toHaveStyle({ width: "62%" });
    expect(within(display).getByLabelText("Climate temperature")).toHaveTextContent(
      "22.5°C",
    );
    expect(within(display).getByLabelText("Bluetooth music")).toHaveTextContent(
      "Relaxed playlists",
    );
  });

  it("links the battery card to the active low-battery scenario", () => {
    render(
      <CockpitStage
        steps={steps}
        activeIndex={1}
        projection={projection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const batteryCard = within(display).getByLabelText("Battery status");

    expect(batteryCard).toHaveAttribute("data-battery-state", "low");
    expect(batteryCard).toHaveTextContent("18%");
    expect(batteryCard).toHaveTextContent("76 km");
    expect(batteryCard).toHaveTextContent("Charging stop advised");
    expect(
      batteryCard.querySelector(".infotainment-display__battery-fill"),
    ).toHaveStyle({ width: "18%" });
  });

  it("replaces climate controls with the live Act 9 charging recommendation", () => {
    const batteryCareProjection: ProjectionScene = {
      ...projection,
      id: "trace_battery_care",
      mode: "battery-care",
      title: "Low-battery proactive care",
      subtitle: "SOC 9% detected with 42 km remaining.",
      routeReadout: "Low-battery event · Preference match · Charging guidance · Confirm",
      batteryState: {
        percent: 9,
        rangeKm: 42,
        status: "critical",
        isLive: true,
      },
      batteryCare: {
        title: "Battery safety recommendation",
        summary: "Navigate to the nearest available charging station now.",
        destinationLabel: "Nearest available charging station",
        memoryLabel: "Charging preference matched",
        actionLabel: "Awaiting driver confirmation",
      },
    };

    render(
      <CockpitStage
        steps={steps}
        activeIndex={1}
        projection={batteryCareProjection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const careCard = within(display).getByLabelText("Battery safety recommendation");

    expect(careCard).toHaveTextContent("Nearest available charging station");
    expect(careCard).toHaveTextContent("Charging preference matched");
    expect(careCard).toHaveTextContent("Awaiting driver confirmation");
    expect(within(display).queryByLabelText("Climate temperature")).not.toBeInTheDocument();
  });

  it("shows the scripted hot-cabin baseline before Act 2 runs", () => {
    const hotCabinSteps = [
      {
        ...steps[0],
        act: "Act 2",
        actKey: "Act 2",
        utterance: "It feels a bit warm in here.",
        initialHvacTargetTempC: 28.5,
      },
    ] as Array<ScenarioStep & { initialHvacTargetTempC: number }>;

    render(
      <CockpitStage
        steps={hotCabinSteps}
        activeIndex={0}
        projection={projection}
        onSelectScenario={vi.fn()}
      />,
    );

    expect(
      within(screen.getByLabelText("Panoramic PowerContext display")).getByLabelText(
        "Climate temperature",
      ),
    ).toHaveTextContent("28.5°C");
  });

  it("embeds the infotainment content inside the center touchscreen", () => {
    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");

    expect(display).toHaveAttribute("data-display-mode", "automotive-glass");
    expect(display).toHaveAttribute("data-screen-placement", "center-touchscreen");
    expect(display).toHaveAttribute("data-frame-source", "background-image");
    expect(
      within(display).getByLabelText("PowerContext projection summary"),
    ).toBeInTheDocument();
    expect(within(display).getByLabelText("Battery status")).toBeInTheDocument();
    expect(within(display).getByLabelText("Climate temperature")).toBeInTheDocument();
    expect(within(display).getByLabelText("Bluetooth music")).toBeInTheDocument();
    expect(screen.queryByLabelText("Scene shortcut rail")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Main cockpit touchscreen")).toBeInTheDocument();
    expect(screen.queryByLabelText("Driver instrument cluster")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Passenger cockpit screen")).not.toBeInTheDocument();
  });

  it("renders the pet companion inside the cockpit stage", () => {
    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        petState={petState}
        onSelectScenario={vi.fn()}
      />,
    );

    const stage = screen.getByLabelText("Smart EV cockpit scene");
    const display = within(stage).getByLabelText("Panoramic PowerContext display");

    expect(stage).toHaveAttribute("data-pet-anchor", "climate");
    expect(stage).toHaveAttribute("data-pet-origin-anchor", "driver");
    expect(within(display).getByLabelText("Climate temperature")).toHaveAttribute(
      "data-pet-focus",
      "true",
    );
    expect(
      within(stage).getByLabelText("忆灵：我把这组座舱温度和座椅设置记成可复用偏好。"),
    ).toBeInTheDocument();
  });

  it("renders climate linkage on the infotainment display for action projections", () => {
    const actionProjection: ProjectionScene & {
      mediaPreference: {
        title: string;
        subtitle: string;
        volumeLabel: string;
        volume: string;
      };
    } = {
      ...projection,
      id: "trace-climate-action",
      mode: "action",
      title: "Cabin linked",
      subtitle: "Intent understood, memory recalled, climate action applied.",
      scoreLabel: "Linked",
      dockLabel: "Live PowerContext trace",
      routeReadout: "Driver zone 22°C -> 26°C",
      showMap: false,
      climateAction: {
        zoneLabel: "Driver zone",
        temperatureLabel: "Temperature",
        beforeTemp: "22°C",
        afterTemp: "26°C",
        temperatureReadout: "22°C -> 26°C",
        seatHeatLabel: "Seat heat",
        beforeSeatHeat: "0",
        afterSeatHeat: "2",
        seatHeatReadout: "0 -> 2",
      },
      mediaPreference: {
        title: "Relaxed playlists",
        subtitle: "Driver music preference",
        sourceLabel: "PowerContext media",
        volumeLabel: "Volume",
        volume: "22",
      },
    };

    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={actionProjection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const climateCard = within(display).getByLabelText("Climate temperature");
    const musicCard = within(display).getByLabelText("Bluetooth music");

    expect(within(climateCard).getByText("Driver zone")).toBeInTheDocument();
    expect(within(climateCard).getByText("26°C")).toBeInTheDocument();
    expect(within(climateCard).getByText(/22°C\s*->\s*26°C/)).toBeInTheDocument();
    expect(within(climateCard).getByText("Seat heat")).toBeInTheDocument();
    expect(within(climateCard).getByText(/0\s*->\s*2/)).toBeInTheDocument();
    expect(within(musicCard).getByText("Relaxed playlists")).toBeInTheDocument();
    expect(within(musicCard).getByText("Driver music preference")).toBeInTheDocument();
    expect(within(musicCard).getByText("Volume")).toBeInTheDocument();
    expect(within(musicCard).getByText("22")).toBeInTheDocument();
  });

  it("replaces the climate card with relationship recommendation details", () => {
    const recommendationProjection = {
      ...projection,
      id: "trace-relationship-suggestion",
      mode: "recommendation",
      title: "Tonight's suggestion",
      subtitle: "Consider a calm dinner tonight.",
      routeReadout: "Suggestion only · Anniversary date hidden",
      showMap: false,
      recommendation: {
        title: "Tonight's suggestion",
        summary: "Consider a calm dinner tonight.",
        policyLabel: "Suggestion only",
        regionLabel: "Zhangjiang Science City · Region only",
        privacyLabel: "Anniversary date hidden",
      },
      status: "ready",
    } as unknown as ProjectionScene;

    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={recommendationProjection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const recommendationCard = within(display).getByLabelText(
      "Tonight's suggestion",
    );

    expect(recommendationCard).toHaveTextContent("Suggestion only");
    expect(recommendationCard).toHaveTextContent(
      "Zhangjiang Science City · Region only",
    );
    expect(recommendationCard).toHaveTextContent("Anniversary date hidden");
    expect(within(display).queryByLabelText("Climate temperature")).not.toBeInTheDocument();
    expect(within(display).queryByText("23°C")).not.toBeInTheDocument();
  });

  it("switches the infotainment display to map mode for navigation projections", () => {
    const navigationProjection: ProjectionScene = {
      ...projection,
      id: "trace-navigation-confirmed",
      mode: "navigation",
      title: "Map navigation",
      subtitle: "Map mode is active for Zhangjiang Science City.",
      scoreLabel: "Navigating",
      dockLabel: "Navigation",
      routeReadout: "Region route loaded: Zhangjiang Science City",
      mapLabel: "Map route",
      showMap: true,
      navigation: {
        destinationLabel: "Zhangjiang Science City",
        statusLabel: "Navigating",
        routeLabel: "Region route loaded: Zhangjiang Science City",
      },
      status: "ready",
    };

    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={navigationProjection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const mapMode = within(display).getByLabelText("Navigation map mode");

    expect(mapMode).toHaveTextContent("Zhangjiang Science City");
    expect(mapMode).toHaveTextContent("Toward Zhangjiang Science City");
    expect(mapMode).toHaveTextContent("Region route loaded: Zhangjiang Science City");
    expect(mapMode).toHaveTextContent("Huangpu River");
    expect(mapMode).toHaveTextContent("Lujiazui");
    expect(mapMode).toHaveTextContent("Century Ave.");
    expect(mapMode).toHaveTextContent("18 min");
    expect(mapMode).toHaveTextContent("12.4 km");
    expect(mapMode).not.toHaveTextContent("Evidence visible");
    expect(within(display).queryByLabelText("Climate temperature")).not.toBeInTheDocument();
    expect(within(display).queryByLabelText("Bluetooth music")).not.toBeInTheDocument();
  });

  it("does not render a decorative music cover over PowerContext media details", () => {
    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const musicCard = within(display).getByLabelText("Bluetooth music");

    expect(
      musicCard.querySelector(".infotainment-display__music-cover"),
    ).not.toBeInTheDocument();
    expect(within(musicCard).getByText("PowerContext media")).toBeInTheDocument();
    expect(within(musicCard).getByText("Relaxed playlists")).toBeInTheDocument();
    expect(
      within(musicCard).getByText("Driver music preference"),
    ).toBeInTheDocument();
  });

  it("lets drivers adjust music volume from the Bluetooth music card", async () => {
    const user = userEvent.setup();

    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const musicCard = within(display).getByLabelText("Bluetooth music");
    const decreaseVolume = within(musicCard).getByRole("button", {
      name: "Decrease volume",
    });
    const increaseVolume = within(musicCard).getByRole("button", {
      name: "Increase volume",
    });

    expect(within(musicCard).getByText("22")).toBeInTheDocument();

    await user.click(increaseVolume);

    expect(within(musicCard).getByText("23")).toBeInTheDocument();

    await user.click(decreaseVolume);
    await user.click(decreaseVolume);

    expect(within(musicCard).getByText("21")).toBeInTheDocument();
  });

  it("renders a richer Bluetooth player with playback status and progress", () => {
    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const musicCard = within(display).getByLabelText("Bluetooth music");

    expect(within(musicCard).getByText("Bluetooth connected")).toBeInTheDocument();
    expect(within(musicCard).getByText("Now playing")).toBeInTheDocument();
    expect(
      within(musicCard).getByRole("progressbar", {
        name: "Playback progress",
      }),
    ).toHaveAttribute("aria-valuenow", "38");
    expect(
      musicCard.querySelectorAll(".infotainment-display__music-equalizer i"),
    ).toHaveLength(5);
    expect(
      within(musicCard).getByRole("button", { name: "Pause music" }),
    ).toBeInTheDocument();
    expect(
      within(musicCard).getByRole("button", { name: "Turn music off" }),
    ).toBeInTheDocument();
  });

  it("lets drivers pause, resume, turn off, and reopen music", async () => {
    const user = userEvent.setup();

    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        onSelectScenario={vi.fn()}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");
    const musicCard = within(display).getByLabelText("Bluetooth music");

    await user.click(within(musicCard).getByRole("button", { name: "Pause music" }));

    expect(within(musicCard).getByText("Paused")).toBeInTheDocument();
    expect(
      within(musicCard).getByRole("button", { name: "Play music" }),
    ).toBeInTheDocument();

    await user.click(within(musicCard).getByRole("button", { name: "Play music" }));

    expect(within(musicCard).getByText("Now playing")).toBeInTheDocument();

    await user.click(within(musicCard).getByRole("button", { name: "Turn music off" }));

    expect(within(musicCard).getByText("Music off")).toBeInTheDocument();
    expect(
      within(musicCard).getByRole("button", { name: "Turn music on" }),
    ).toBeInTheDocument();
    expect(
      within(musicCard).getByRole("button", { name: "Decrease volume" }),
    ).toBeDisabled();
    expect(
      within(musicCard).getByRole("button", { name: "Increase volume" }),
    ).toBeDisabled();

    await user.click(within(musicCard).getByRole("button", { name: "Turn music on" }));

    expect(within(musicCard).getByText("Now playing")).toBeInTheDocument();
    expect(
      within(musicCard).getByRole("button", { name: "Turn music off" }),
    ).toBeInTheDocument();
    expect(
      within(musicCard).getByRole("button", { name: "Decrease volume" }),
    ).not.toBeDisabled();
    expect(
      within(musicCard).getByRole("button", { name: "Increase volume" }),
    ).not.toBeDisabled();
  });

  it("binds the cockpit photo and material tint to the selected interior theme", () => {
    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        interiorTheme="orange"
        onSelectScenario={vi.fn()}
      />,
    );

    const stage = screen.getByLabelText("Smart EV cockpit scene");
    const image = screen.getByAltText("Premium smart EV cockpit interior");
    const materialTint = screen.getByTestId("cockpit-material-tint");

    expect(stage).toHaveAttribute("data-interior", "orange");
    expect(image).toHaveAttribute("data-interior-filter", "orange");
    expect(materialTint).toHaveAttribute("data-interior", "orange");
  });

  it("calls onSelectScenario with wrapped indices from scene arrow controls", async () => {
    const onSelectScenario = vi.fn();
    const user = userEvent.setup();

    render(
      <CockpitStage
        steps={steps}
        activeIndex={0}
        projection={projection}
        onSelectScenario={onSelectScenario}
      />,
    );

    const display = screen.getByLabelText("Panoramic PowerContext display");

    await user.click(within(display).getByRole("button", { name: "Previous scene" }));
    expect(onSelectScenario).toHaveBeenLastCalledWith(1);

    await user.click(within(display).getByRole("button", { name: "Next scene" }));
    expect(onSelectScenario).toHaveBeenLastCalledWith(1);
  });
});
