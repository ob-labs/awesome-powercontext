import type { ActKey, ActorId, SeatPosition, TestDataState } from "./types/api";

export type Locale = "en" | "zh";
export type InteriorThemeId = "black" | "orange" | "red" | "ivory" | "cognac";

export interface LocalizedScenarioStep {
  day: string;
  act: string;
  actKey: ActKey;
  utterance: string;
  actorId: ActorId;
  seatPosition: SeatPosition;
  initialHvacTargetTempC?: number;
}

export type ActorLabels = Record<ActorId, string>;

export interface TestDataPanelLabels {
  controlsLabel: string;
  countAria: string;
  generateAria: (count: number) => string;
  generate: string;
  clearAria: string;
  clear: string;
  noDataset: string;
  stateLabels: Record<TestDataState, string>;
  generated: (count: number) => string;
  importing: (imported: number, total: number) => string;
  imported: (count: number) => string;
  skipped: (count: number) => string;
  deleted: (count: number) => string;
  failed: (count: number) => string;
}

export interface DialogueLabels {
  title: string;
  utterance: string;
  send: string;
  sending: string;
  empty: string;
  floatingLabel: string;
  recentLabel: string;
  assistantName: string;
  userName: string;
}

export interface SeatOccupantLabels {
  selectorLabel: string;
  settingsLabel: (actor: string) => string;
  actors: ActorLabels;
}

export interface UserIdentityPanelLabels {
  dialogLabel: string;
  title: string;
  subtitle: string;
  seat: string;
  displayName: string;
  userId: string;
  profileNote: string;
  profileSummary: string;
  memoryKinds: string;
  recentMemories: string;
  noProfile: string;
  noMemoryKinds: string;
  close: string;
  save: string;
  saving: string;
  saved: (displayName: string, userId: string) => string;
  saveError: string;
}

export interface InteriorTrimLabels {
  selectorLabel: string;
  themes: Record<InteriorThemeId, string>;
}

export interface MediaPreferenceLabels {
  title: string;
  subtitle: string;
  sourceLabel: string;
  volumeLabel: string;
  volume: string;
}

export interface InfotainmentDisplayLabels {
  displayLabel: string;
  driverClusterLabel: string;
  centerTouchscreenLabel: string;
  passengerScreenLabel: string;
  sceneRailLabel: string;
  previousSceneLabel: string;
  nextSceneLabel: string;
  batteryCardLabel: string;
  batteryCardTitle: string;
  batteryLiveLabel: string;
  batteryRangeLabel: string;
  batteryHealthLabel: string;
  batteryHealthValue: string;
  batteryStatusLabels: {
    normal: string;
    low: string;
    critical: string;
  };
  climateCardLabel: string;
  musicCardLabel: string;
  bluetoothMusic: string;
  decreaseVolumeLabel: string;
  increaseVolumeLabel: string;
  musicConnectedLabel: string;
  musicPlayingLabel: string;
  musicPausedLabel: string;
  musicOffLabel: string;
  playMusicLabel: string;
  pauseMusicLabel: string;
  previousTrackLabel: string;
  nextTrackLabel: string;
  turnMusicOnLabel: string;
  turnMusicOffLabel: string;
  playbackProgressLabel: string;
  projectionSummaryLabel: string;
  navigationMapModeLabel: string;
  navigationStatusLabel: string;
  navigationDestinationLabel: string;
  navigationPrivacyLabel: string;
  navigationInstruction: string;
  navigationInstructionDetail: (destination: string) => string;
  navigationEtaLabel: string;
  navigationEtaValue: string;
  navigationDistanceLabel: string;
  navigationDistanceValue: string;
  navigationTrafficLabel: string;
  navigationAreaOnlyLabel: string;
  navigationScaleLabel: string;
  navigationCityLabel: string;
  navigationMapLabels: {
    huangpuRiver: string;
    innerRing: string;
    middleRing: string;
    centuryAvenue: string;
    lujiazui: string;
    centuryPark: string;
    zhangjiang: string;
    xujiahui: string;
  };
  powerMemDrive: string;
  sceneProjector: string;
  needsAttention: string;
  passenger: string;
  comfort: string;
  cabinReadout: string;
  defaultClimateZone: string;
  defaultClimateTemp: string;
  defaultClimateReadout: string;
  defaultSeatHeatLabel: string;
  defaultSeatHeatLevel: string;
  defaultSeatHeatReadout: string;
  defaultMediaPreference: MediaPreferenceLabels;
}

export interface CockpitStageLabels {
  stageLabel: string;
  imageAlt: string;
  sceneFocus: string;
  projectionLabel: string;
  infotainment: InfotainmentDisplayLabels;
}

export interface ProjectionLabels {
  actTitles: Record<string, string>;
  actSubtitles: Record<string, string>;
  actRouteReadouts: Record<string, string>;
  actors: ActorLabels;
  liveMemoryUnavailable: string;
  error: string;
  liveModeNeedsAttention: string;
  backend: string;
  state: string;
  action: string;
  checkService: string;
  noProjectionUpdate: string;
  noFakeFallback: string;
  livePowerMemTrace: string;
  assistant: string;
  llmChat: string;
  actionTrace: string;
  scenarioTrace: string;
  disconnected: string;
  trace: string;
  synced: string;
  memory: string;
  noHit: string;
  privacy: string;
  evidenceVisible: string;
  ready: string;
  actor: string;
  scene: string;
  source: string;
  scenario: string;
  syntheticDataOnly: string;
  live: string;
  linked: string;
  cabinLinked: string;
  cabinLinkedSubtitle: string;
  intent: string;
  rememberedPreference: string;
  navigationTitle: string;
  navigationSubtitle: string;
  navigationDock: string;
  navigationIntent: string;
  navigationStatusActive: string;
  navigationMapLabel: string;
  destination: string;
  regionOnly: string;
  suggestionOnly: string;
  anniversaryDateMasked: string;
  regionLevelDestination: string;
  navigationRouteReadout: (destination: string) => string;
  batteryCareTitle: string;
  batteryCareSubtitle: (soc: number, rangeKm: number) => string;
  batteryCareFlow: string;
  batteryCarePolicyFlow: string;
  batteryCareMemoryMatched: string;
  batteryCareSafetyPolicy: string;
  batteryCareAwaitingConfirmation: string;
  batteryCareGuidanceReady: string;
  nearestAvailableChargingStation: string;
  reachableChargingStation: string;
  vehicleActionApplied: string;
  comfortControlRequest: string;
  noMemoryDetail: string;
  zoneLabels: Record<SeatPosition, string>;
  coldIntentByActor: ActorLabels;
  temperature: string;
  seatHeat: string;
  temperatureReadout: (beforeTemp: string, afterTemp: string) => string;
  seatHeatReadout: (beforeHeat: string, afterHeat: string) => string;
  actionSummary: (
    zone: string,
    temperatureReadout: string,
    seatHeatReadout: string,
  ) => string;
  routeReadout: (zone: string, temperatureReadout: string) => string;
  mediaPreferenceByActor: Record<ActorId, MediaPreferenceLabels>;
  mediaMemorySubtitle: string;
}

export interface EvidencePanelLabels {
  cockpitStatus: {
    ariaLabel: string;
    live: string;
    vehicle: string;
    soc: string;
    inside: string;
    comfort: string;
  };
  scenarioTimeline: {
    ariaLabel: string;
  };
  memoryFlow: {
    title: string;
    empty: string;
  };
  privacy: {
    ariaLabel: string;
    text: string;
  };
  vehicleState: {
    title: string;
    summaryLabel: string;
    empty: string;
  };
  recommendations: {
    title: string;
    empty: string;
  };
  memoryGraph: {
    title: string;
    groupLabel: string;
    empty: string;
    nodes: string[];
  };
  lifecycle: {
    ariaLabel: string;
    empty: string;
    stages: string[];
  };
  developerEvidence: {
    drawerLabel: string;
    title: string;
    exportTrace: string;
    backendStatusLabel: string;
    live: string;
    disconnected: string;
    noEvidence: string;
    steps: Array<[string, string]>;
  };
}

export interface AppCopy {
  topDataBarLabel: string;
  language: {
    label: string;
    english: string;
    chinese: string;
  };
  status: {
    loaded: (day: string) => string;
    actorSet: (actor: string) => string;
    reset: string;
    exportedTrace: string;
    traceExportFailed: string;
    liveFallbackError: string;
    testDataFallbackError: string;
  };
  evidence: {
    entry: string;
    openAria: string;
    dialogAria: string;
    title: string;
    subtitle: string;
    close: string;
  };
  manual: {
    ariaLabel: string;
    reset: string;
    replay: string;
    next: string;
    export: string;
    exporting: string;
  };
  testData: TestDataPanelLabels;
  dialogue: DialogueLabels;
  seats: SeatOccupantLabels;
  identity: UserIdentityPanelLabels;
  interior: InteriorTrimLabels;
  cockpit: CockpitStageLabels;
  projection: ProjectionLabels;
  evidencePanels: EvidencePanelLabels;
}

export const DEFAULT_LOCALE: Locale = "zh";

export type DemoSeason = "spring" | "summer" | "autumn" | "winter";

const ACT_2_INITIAL_HVAC_TARGET_TEMP_C: Record<DemoSeason, number> = {
  spring: 20,
  summer: 28.5,
  autumn: 20,
  winter: 18,
};

const SEASONAL_UTTERANCES_BY_LOCALE: Record<
  Locale,
  Record<DemoSeason, Partial<Record<ActKey, string>>>
> = {
  en: {
    spring: {
      "Act 1": "I usually set 24C and seat heat level 0 when I get in during spring.",
      "Act 2": "It feels a little cool in here.",
    },
    summer: {
      "Act 1": "I usually set 23C and seat heat level 0 when I get in during summer.",
      "Act 2": "It feels a bit warm in here.",
    },
    autumn: {
      "Act 1": "I usually set 24C and seat heat level 1 when I get in during autumn.",
      "Act 2": "It feels a little cool in here.",
    },
    winter: {
      "Act 1": "I usually set 26C and seat heat level 2 when I get in during winter.",
      "Act 2": "I feel a bit cold.",
    },
  },
  zh: {
    spring: {
      "Act 1": "我春天上车一般 24C，座椅加热 0 档。",
      "Act 2": "车里有点凉。",
    },
    summer: {
      "Act 1": "我夏天上车一般 23C，座椅加热 0 档。",
      "Act 2": "车里有点热。",
    },
    autumn: {
      "Act 1": "我秋天上车一般 24C，座椅加热 1 档。",
      "Act 2": "车里有点凉。",
    },
    winter: {
      "Act 1": "我冬天上车一般 26C，座椅加热 2 档。",
      "Act 2": "有点冷。",
    },
  },
};

export function seasonForDate(date: Date = new Date()): DemoSeason {
  const month = date.getMonth() + 1;
  if (month >= 3 && month <= 5) {
    return "spring";
  }
  if (month >= 6 && month <= 8) {
    return "summer";
  }
  if (month >= 9 && month <= 11) {
    return "autumn";
  }
  return "winter";
}

export function getScenarioStepsForDate(
  locale: Locale,
  date: Date = new Date(),
): LocalizedScenarioStep[] {
  const season = seasonForDate(date);
  const seasonalUtterances = SEASONAL_UTTERANCES_BY_LOCALE[locale][season];
  return SCENARIO_STEPS_BASE_BY_LOCALE[locale].map((step) => ({
    ...step,
    utterance: seasonalUtterances[step.actKey] ?? step.utterance,
    ...(step.actKey === "Act 2"
      ? { initialHvacTargetTempC: ACT_2_INITIAL_HVAC_TARGET_TEMP_C[season] }
      : {}),
  }));
}

const SCENARIO_STEPS_BASE_BY_LOCALE: Record<Locale, LocalizedScenarioStep[]> = {
  en: [
    {
      day: "Day 1",
      act: "Act 1",
      actKey: "Act 1",
      utterance: "I usually set 26C and seat heat level 2 when I get in during winter.",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "Day 7",
      act: "Act 2",
      actKey: "Act 2",
      utterance: "I feel a bit cold.",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "Day 14",
      act: "Act 3",
      actKey: "Act 3",
      utterance: "Apply my last comfortable setup.",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "Day 21",
      act: "Act 4",
      actKey: "Act 4",
      utterance: "Does this vehicle support rest mode?",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "Day 28",
      act: "Act 5",
      actKey: "Act 5",
      utterance: "Take me to the restaurant from last Friday.",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "Day 35",
      act: "Act 6",
      actKey: "Act 6",
      utterance: "Play something suitable for the child to sleep.",
      actorId: "child_rear_left",
      seatPosition: "rear_left",
    },
    {
      day: "Day 42",
      act: "Act 7",
      actKey: "Act 7",
      utterance: "Any suggestions for tonight?",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "Day 56",
      act: "Act 8",
      actKey: "Act 8",
      utterance: "Suggest a driving mode for this trip.",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "Day 70",
      act: "Act 9",
      actKey: "Act 9",
      utterance: "Trigger low-battery proactive care.",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "Day 90",
      act: "Act 10",
      actKey: "Act 10",
      utterance: "Run lifecycle review at day 90.",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
  ],
  zh: [
    {
      day: "第 1 天",
      act: "场景 1",
      actKey: "Act 1",
      utterance: "我冬天上车一般 26C，座椅加热 2 档。",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "第 7 天",
      act: "场景 2",
      actKey: "Act 2",
      utterance: "有点冷。",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "第 14 天",
      act: "场景 3",
      actKey: "Act 3",
      utterance: "按我上次舒服的设置来。",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "第 21 天",
      act: "场景 4",
      actKey: "Act 4",
      utterance: "这台车支持小憩模式吗？",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "第 28 天",
      act: "场景 5",
      actKey: "Act 5",
      utterance: "带我去上周五那家餐厅。",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "第 35 天",
      act: "场景 6",
      actKey: "Act 6",
      utterance: "放点适合孩子睡觉的内容。",
      actorId: "child_rear_left",
      seatPosition: "rear_left",
    },
    {
      day: "第 42 天",
      act: "场景 7",
      actKey: "Act 7",
      utterance: "今晚有什么安排建议？",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "第 56 天",
      act: "场景 8",
      actKey: "Act 8",
      utterance: "建议这次出行的驾驶模式。",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "第 70 天",
      act: "场景 9",
      actKey: "Act 9",
      utterance: "触发低电量主动关怀。",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
    {
      day: "第 90 天",
      act: "场景 10",
      actKey: "Act 10",
      utterance: "执行第 90 天生命周期回顾。",
      actorId: "driver_primary",
      seatPosition: "front_left",
    },
  ],
};

export const SCENARIO_STEPS_BY_LOCALE: Record<Locale, LocalizedScenarioStep[]> = {
  en: getScenarioStepsForDate("en"),
  zh: getScenarioStepsForDate("zh"),
};

function lowercaseFirst(value: string): string {
  return value ? `${value[0].toLowerCase()}${value.slice(1)}` : value;
}

export const APP_COPY: Record<Locale, AppCopy> = {
  en: {
    topDataBarLabel: "Top data command bar",
    language: {
      label: "Language",
      english: "EN",
      chinese: "中文",
    },
    status: {
      loaded: (day) => `Loaded ${day} sample.`,
      actorSet: (actor) => `Actor set to ${actor}.`,
      reset: "Demo state reset.",
      exportedTrace: "Exported trace evidence JSON.",
      traceExportFailed: "Trace export failed",
      liveFallbackError: "PowerMem live mode failed",
      testDataFallbackError: "Test data operation failed",
    },
    evidence: {
      entry: "Evidence",
      openAria: "Open live evidence",
      dialogAria: "Live evidence console",
      title: "Live Evidence Console",
      subtitle: "PowerMem trace, scenario timeline, vehicle state, and memory graph.",
      close: "Close Evidence",
    },
    manual: {
      ariaLabel: "Manual cockpit keys",
      reset: "Reset",
      replay: "Replay",
      next: "Next",
      export: "Export",
      exporting: "Exporting",
    },
    testData: {
      controlsLabel: "Test data controls",
      countAria: "Memory count",
      generateAria: (count) => `Generate and import ${count} memories`,
      generate: "Generate Data",
      clearAria: "Clear all PowerMem memories",
      clear: "Clear Data",
      noDataset: "No dataset generated",
      stateLabels: {
        idle: "idle",
        generated: "generated",
        importing: "importing",
        imported: "imported",
        deleting: "deleting",
        deleted: "deleted",
        failed: "failed",
      },
      generated: (count) => `${count} generated`,
      importing: (imported, total) => `${imported} / ${total} imported`,
      imported: (count) => `${count} imported`,
      skipped: (count) => `${count} skipped`,
      deleted: (count) => `${count} deleted`,
      failed: (count) => `${count} failed`,
    },
    dialogue: {
      title: "Conversation",
      utterance: "Utterance",
      send: "Send",
      sending: "Sending",
      empty: "Submit an utterance to start a live PowerMem trace.",
      floatingLabel: "Floating voice chat",
      recentLabel: "Recent conversation",
      assistantName: "PowerMem",
      userName: "Voice",
    },
    seats: {
      selectorLabel: "Seat occupant selector",
      settingsLabel: (actor) => `Configure ${actor} profile`,
      actors: {
        driver_primary: "Driver",
        passenger_front: "Passenger",
        child_rear_left: "Child",
      },
    },
    identity: {
      dialogLabel: "User profile settings",
      title: "PowerMem identity binding",
      subtitle: "Bind this seat occupant to a stable PowerMem user_id and review the current profile summary.",
      seat: "Seat",
      displayName: "Display name",
      userId: "PowerMem user_id",
      profileNote: "Profile note",
      profileSummary: "User profile",
      memoryKinds: "Memory kinds",
      recentMemories: "Recent memories",
      noProfile: "No profile memory has been found for this user_id.",
      noMemoryKinds: "No memory kind summary yet.",
      close: "Close",
      save: "Save binding",
      saving: "Saving",
      saved: (displayName, userId) => `Saved ${displayName} as ${userId}.`,
      saveError: "Failed to save user binding",
    },
    interior: {
      selectorLabel: "Interior trim selector",
      themes: {
        black: "Black Interior",
        orange: "Hermes Orange",
        red: "Red Interior",
        ivory: "Porcelain White",
        cognac: "Cognac Brown",
      },
    },
    cockpit: {
      stageLabel: "Smart EV cockpit scene",
      imageAlt: "Premium smart EV cockpit interior",
      sceneFocus: "Scene focus",
      projectionLabel: "Holographic PowerMem evidence projection",
      infotainment: {
        displayLabel: "Panoramic PowerMem display",
        driverClusterLabel: "Driver instrument cluster",
        centerTouchscreenLabel: "Main cockpit touchscreen",
        passengerScreenLabel: "Passenger cockpit screen",
        sceneRailLabel: "Scene shortcut rail",
        previousSceneLabel: "Previous scene",
        nextSceneLabel: "Next scene",
        batteryCardLabel: "Battery status",
        batteryCardTitle: "Battery",
        batteryLiveLabel: "Live SOC",
        batteryRangeLabel: "Range",
        batteryHealthLabel: "Pack health",
        batteryHealthValue: "97% nominal",
        batteryStatusLabels: {
          normal: "Energy stable",
          low: "Charging stop advised",
          critical: "Critical SOC",
        },
        climateCardLabel: "Climate temperature",
        musicCardLabel: "Bluetooth music",
        bluetoothMusic: "Bluetooth music",
        decreaseVolumeLabel: "Decrease volume",
        increaseVolumeLabel: "Increase volume",
        musicConnectedLabel: "Bluetooth connected",
        musicPlayingLabel: "Now playing",
        musicPausedLabel: "Paused",
        musicOffLabel: "Music off",
        playMusicLabel: "Play music",
        pauseMusicLabel: "Pause music",
        previousTrackLabel: "Previous track",
        nextTrackLabel: "Next track",
        turnMusicOnLabel: "Turn music on",
        turnMusicOffLabel: "Turn music off",
        playbackProgressLabel: "Playback progress",
        projectionSummaryLabel: "PowerMem projection summary",
        navigationMapModeLabel: "Navigation map mode",
        navigationStatusLabel: "Status",
        navigationDestinationLabel: "Destination",
        navigationPrivacyLabel: "Privacy",
        navigationInstruction: "Continue on the main route",
        navigationInstructionDetail: (destination) => `Toward ${destination}`,
        navigationEtaLabel: "ETA",
        navigationEtaValue: "18 min",
        navigationDistanceLabel: "Distance",
        navigationDistanceValue: "12.4 km",
        navigationTrafficLabel: "Traffic clear",
        navigationAreaOnlyLabel: "Region only",
        navigationScaleLabel: "2 km",
        navigationCityLabel: "SH",
        navigationMapLabels: {
          huangpuRiver: "Huangpu River",
          innerRing: "Inner Ring",
          middleRing: "Middle Ring",
          centuryAvenue: "Century Ave.",
          lujiazui: "Lujiazui",
          centuryPark: "Century Park",
          zhangjiang: "Zhangjiang",
          xujiahui: "Xujiahui",
        },
        powerMemDrive: "PowerMem Drive",
        sceneProjector: "Scene projector",
        needsAttention: "Needs attention",
        passenger: "Passenger",
        comfort: "Comfort",
        cabinReadout: "Cabin 22.5°C",
        defaultClimateZone: "Cabin climate",
        defaultClimateTemp: "22.5°C",
        defaultClimateReadout: "Auto climate",
        defaultSeatHeatLabel: "Seat heat",
        defaultSeatHeatLevel: "Auto",
        defaultSeatHeatReadout: "Standby",
        defaultMediaPreference: {
          title: "Relaxed playlists",
          subtitle: "Driver music preference",
          sourceLabel: "PowerMem media",
          volumeLabel: "Volume",
          volume: "22",
        },
      },
    },
    projection: {
      actTitles: {
        "Act 1": "Preference capture",
        "Act 2": "Same phrase, different people",
        "Act 3": "Comfort routine",
        "Act 4": "Capability boundary",
        "Act 5": "Location recall",
        "Act 6": "Child media",
        "Act 7": "Relationship suggestion",
        "Act 8": "Driving mode",
        "Act 9": "Proactive care",
        "Act 10": "Lifecycle and privacy",
      },
      actSubtitles: {
        "Act 1": "Store structured cabin preferences without saving raw dialogue.",
        "Act 2": "Apply actor and seat specific comfort and safety boundaries.",
        "Act 3": "Compose cabin and driving preferences into one routine.",
        "Act 4": "Answer capability questions from vehicle profile memory.",
        "Act 5": "Recall a place at region level without exposing exact address.",
        "Act 6": "Combine child media preference with safety policy.",
        "Act 7": "Suggest relationship-aware plans without auto navigation.",
        "Act 8": "Recommend driving mode using SOC and preference memory.",
        "Act 9": "Respond to low-battery vehicle events with proactive care.",
        "Act 10": "Decay, archive, or delete temporary memories on day 90.",
      },
      actRouteReadouts: {
        "Act 1": "Structured preference ADD",
        "Act 2": "Actor-specific cabin patch",
        "Act 3": "Routine HVAC + seat + drive mode",
        "Act 4": "Capability answer, no vehicle command",
        "Act 5": "Region-level navigation suggestion",
        "Act 6": "Low-volume child-safe media",
        "Act 7": "Masked relationship recommendation",
        "Act 8": "Drive mode with SOC context",
        "Act 9": "Low SOC event + charging guidance",
        "Act 10": "Lifecycle UPDATE/DELETE audit",
      },
      actors: {
        driver_primary: "Driver",
        passenger_front: "Passenger",
        child_rear_left: "Child",
      },
      liveMemoryUnavailable: "Live memory unavailable",
      error: "Error",
      liveModeNeedsAttention: "Live mode needs attention",
      backend: "Backend",
      state: "State",
      action: "Action",
      checkService: "Check service",
      noProjectionUpdate: "No projection update",
      noFakeFallback: "No fake fallback",
      livePowerMemTrace: "Live PowerMem trace",
      assistant: "Voice assistant",
      llmChat: "LLM chat",
      actionTrace: "Action trace",
      scenarioTrace: "Scene trace",
      disconnected: "Disconnected",
      trace: "Trace",
      synced: "Synced",
      memory: "Memory",
      noHit: "No hit",
      privacy: "Privacy",
      evidenceVisible: "Evidence visible",
      ready: "Ready",
      actor: "Actor",
      scene: "Scene",
      source: "Source",
      scenario: "Scenario",
      syntheticDataOnly: "Synthetic data only",
      live: "Live",
      linked: "Linked",
      cabinLinked: "Cabin linked",
      cabinLinkedSubtitle:
        "Intent understood, memory recalled, climate action applied.",
      intent: "Intent",
      rememberedPreference: "Winter comfort preference",
      navigationTitle: "Map navigation",
      navigationSubtitle: "Map mode is active with a region-level destination.",
      navigationDock: "Navigation",
      navigationIntent: "Confirmed navigation",
      navigationStatusActive: "Navigating",
      navigationMapLabel: "Map route",
      destination: "Destination",
      regionOnly: "Region only",
      suggestionOnly: "Suggestion only",
      anniversaryDateMasked: "Anniversary date hidden",
      regionLevelDestination: "Region-level destination",
      navigationRouteReadout: (destination) =>
        `Region route loaded: ${destination}`,
      batteryCareTitle: "Low-battery proactive care",
      batteryCareSubtitle: (soc, rangeKm) =>
        `SOC ${soc}% detected with ${rangeKm} km remaining.`,
      batteryCareFlow:
        "Low-battery event · Preference match · Charging guidance · Confirm",
      batteryCarePolicyFlow:
        "Low-battery event · Safety policy · Charging guidance · Confirm",
      batteryCareMemoryMatched: "Charging preference matched",
      batteryCareSafetyPolicy: "Battery safety policy active",
      batteryCareAwaitingConfirmation: "Awaiting driver confirmation",
      batteryCareGuidanceReady: "Charging guidance ready",
      nearestAvailableChargingStation: "Nearest available charging station",
      reachableChargingStation: "Reachable charging station",
      vehicleActionApplied: "PowerMem restores the remembered comfort setup on the vehicle.",
      comfortControlRequest:
        "The utterance is treated as a cabin comfort control request.",
      noMemoryDetail: "Memory content is not available for this hit.",
      zoneLabels: {
        front_left: "Driver zone",
        front_right: "Passenger zone",
        rear_left: "Rear left zone",
      },
      coldIntentByActor: {
        driver_primary: "Driver feels cold",
        passenger_front: "Passenger feels cold",
        child_rear_left: "Child feels cold",
      },
      temperature: "Temperature",
      seatHeat: "Seat heat",
      temperatureReadout: (beforeTemp, afterTemp) =>
        beforeTemp === "--" ? `Target ${afterTemp}` : `${beforeTemp} -> ${afterTemp}`,
      seatHeatReadout: (beforeHeat, afterHeat) =>
        beforeHeat === "--" ? `Level ${afterHeat}` : `${beforeHeat} -> ${afterHeat}`,
      actionSummary: (zone, temperatureReadout, seatHeatReadout) =>
        `${zone} ${lowercaseFirst(temperatureReadout)}, seat heat ${lowercaseFirst(seatHeatReadout)}`,
      routeReadout: (zone, temperatureReadout) =>
        `${zone} ${lowercaseFirst(temperatureReadout)}`,
      mediaPreferenceByActor: {
        driver_primary: {
          title: "Relaxed playlists",
          subtitle: "Driver music preference",
          sourceLabel: "PowerMem media",
          volumeLabel: "Volume",
          volume: "22",
        },
        passenger_front: {
          title: "Weekend relaxed playlists",
          subtitle: "Passenger media preference",
          sourceLabel: "PowerMem media",
          volumeLabel: "Volume",
          volume: "22",
        },
        child_rear_left: {
          title: "Quiet bedtime stories",
          subtitle: "Child media preference",
          sourceLabel: "PowerMem media",
          volumeLabel: "Volume",
          volume: "18",
        },
      },
      mediaMemorySubtitle: "Media preference memory",
    },
    evidencePanels: {
      cockpitStatus: {
        ariaLabel: "Cockpit status",
        live: "LIVE PowerMem",
        vehicle: "Demo Vehicle",
        soc: "SOC 62%",
        inside: "Inside 22°C",
        comfort: "Drive comfort",
      },
      scenarioTimeline: {
        ariaLabel: "Scenario timeline",
      },
      memoryFlow: {
        title: "PowerMem Memory Flow",
        empty: "No live memory hits yet.",
      },
      privacy: {
        ariaLabel: "Privacy status",
        text: "Raw transcript excluded. Masked fields stay hidden.",
      },
      vehicleState: {
        title: "Vehicle Context",
        summaryLabel: "Vehicle state summary",
        empty: "Vehicle state diffs appear after a live backend response.",
      },
      recommendations: {
        title: "Recommendations",
        empty: "Recommendations appear after live PowerMem evidence is returned.",
      },
      memoryGraph: {
        title: "Memory Graph",
        groupLabel: "Memory graph node groups",
        empty: "Selected memory relationships appear after a live response.",
        nodes: ["People", "Vehicle", "Places", "Media", "Controls"],
      },
      lifecycle: {
        ariaLabel: "Memory lifecycle timeline",
        empty: "Lifecycle mutations appear after Act 10 or lifecycle evidence.",
        stages: ["Active", "Reinforced", "Decayed", "Archived", "Deleted"],
      },
      developerEvidence: {
        drawerLabel: "Developer evidence drawer",
        title: "Developer Evidence",
        exportTrace: "Export Trace",
        backendStatusLabel: "PowerMem backend status",
        live: "LIVE PowerMem",
        disconnected: "PowerMem disconnected",
        noEvidence: "No evidence returned",
        steps: [
          ["request", "Request"],
          ["privacy", "Privacy Scrubbed"],
          ["data_source", "Data Source"],
          ["operations", "Operations"],
          ["memory_hits", "Memory Hits"],
          ["decision", "Decision"],
          ["vehicle_action", "Vehicle State Diff"],
          ["recommendations", "Recommendations"],
          ["lifecycle", "Lifecycle"],
          ["audit", "Audit"],
          ["latency_ms", "Latency"],
        ],
      },
    },
  },
  zh: {
    topDataBarLabel: "顶部数据命令栏",
    language: {
      label: "语言",
      english: "EN",
      chinese: "中文",
    },
    status: {
      loaded: (day) => `已载入${day}样例。`,
      actorSet: (actor) => `已切换为${actor}。`,
      reset: "演示状态已重置。",
      exportedTrace: "已导出追踪证据 JSON。",
      traceExportFailed: "追踪导出失败",
      liveFallbackError: "PowerMem 实时模式失败",
      testDataFallbackError: "测试数据操作失败",
    },
    evidence: {
      entry: "证据",
      openAria: "打开实时证据",
      dialogAria: "实时证据控制台",
      title: "实时证据控制台",
      subtitle: "PowerMem 追踪、场景时间线、车辆状态和记忆图谱。",
      close: "关闭证据",
    },
    manual: {
      ariaLabel: "座舱手动按键",
      reset: "重置",
      replay: "重放",
      next: "下一个",
      export: "导出",
      exporting: "导出中",
    },
    testData: {
      controlsLabel: "测试数据控制",
      countAria: "记忆数量",
      generateAria: (count) => `生成并导入 ${count} 条记忆`,
      generate: "数据生成",
      clearAria: "清空 PowerMem 数据库全部记忆",
      clear: "数据清理",
      noDataset: "尚未生成数据集",
      stateLabels: {
        idle: "空闲",
        generated: "已生成",
        importing: "导入中",
        imported: "已导入",
        deleting: "删除中",
        deleted: "已删除",
        failed: "失败",
      },
      generated: (count) => `已生成 ${count} 条`,
      importing: (imported, total) => `已导入 ${imported} / ${total} 条`,
      imported: (count) => `已导入 ${count} 条`,
      skipped: (count) => `跳过 ${count} 条`,
      deleted: (count) => `已删除 ${count} 条`,
      failed: (count) => `失败 ${count} 条`,
    },
    dialogue: {
      title: "对话",
      utterance: "语音指令",
      send: "发送",
      sending: "发送中",
      empty: "提交一句语音指令，启动实时 PowerMem 追踪。",
      floatingLabel: "悬浮语音聊天",
      recentLabel: "最近对话",
      assistantName: "PowerMem",
      userName: "语音",
    },
    seats: {
      selectorLabel: "座位乘员选择",
      settingsLabel: (actor) => `设置${actor}个人信息`,
      actors: {
        driver_primary: "驾驶员",
        passenger_front: "前排乘客",
        child_rear_left: "儿童",
      },
    },
    identity: {
      dialogLabel: "用户个人信息设置",
      title: "PowerMem 身份绑定",
      subtitle: "把当前人物绑定到稳定的 PowerMem user_id，并查看用户画像摘要。",
      seat: "座位",
      displayName: "显示名称",
      userId: "PowerMem user_id",
      profileNote: "个人备注",
      profileSummary: "用户画像",
      memoryKinds: "记忆类型",
      recentMemories: "最近记忆",
      noProfile: "当前 user_id 还没有可展示的画像记忆。",
      noMemoryKinds: "还没有记忆类型统计。",
      close: "关闭",
      save: "保存绑定",
      saving: "保存中",
      saved: (displayName, userId) => `已保存${displayName}到 ${userId}。`,
      saveError: "保存用户绑定失败",
    },
    interior: {
      selectorLabel: "内饰颜色选择",
      themes: {
        black: "黑色内饰",
        orange: "爱马仕橙",
        red: "红色内饰",
        ivory: "瓷白内饰",
        cognac: "干邑棕",
      },
    },
    cockpit: {
      stageLabel: "智能电动车座舱场景",
      imageAlt: "高端智能电动车座舱内饰",
      sceneFocus: "场景聚焦",
      projectionLabel: "PowerMem 全息证据投影",
      infotainment: {
        displayLabel: "PowerMem 全景车机屏幕",
        driverClusterLabel: "驾驶员仪表屏",
        centerTouchscreenLabel: "中控触控屏",
        passengerScreenLabel: "副驾娱乐屏",
        sceneRailLabel: "场景快捷栏",
        previousSceneLabel: "上一个场景",
        nextSceneLabel: "下一个场景",
        batteryCardLabel: "电池电量",
        batteryCardTitle: "电池",
        batteryLiveLabel: "实时 SOC",
        batteryRangeLabel: "续航",
        batteryHealthLabel: "电池健康",
        batteryHealthValue: "97% 正常",
        batteryStatusLabels: {
          normal: "电量稳定",
          low: "建议补能",
          critical: "低电量告警",
        },
        climateCardLabel: "空调温度",
        musicCardLabel: "蓝牙音乐",
        bluetoothMusic: "蓝牙音乐",
        decreaseVolumeLabel: "降低音量",
        increaseVolumeLabel: "提高音量",
        musicConnectedLabel: "蓝牙已连接",
        musicPlayingLabel: "正在播放",
        musicPausedLabel: "已暂停",
        musicOffLabel: "音乐已关闭",
        playMusicLabel: "播放音乐",
        pauseMusicLabel: "暂停音乐",
        previousTrackLabel: "上一首",
        nextTrackLabel: "下一首",
        turnMusicOnLabel: "开启音乐",
        turnMusicOffLabel: "关闭音乐",
        playbackProgressLabel: "播放进度",
        projectionSummaryLabel: "车机屏幕 PowerMem 摘要",
        navigationMapModeLabel: "导航地图模式",
        navigationStatusLabel: "状态",
        navigationDestinationLabel: "目的地",
        navigationPrivacyLabel: "隐私",
        navigationInstruction: "沿主路继续前进",
        navigationInstructionDetail: (destination) => `前往${destination}`,
        navigationEtaLabel: "预计",
        navigationEtaValue: "18 分钟",
        navigationDistanceLabel: "距离",
        navigationDistanceValue: "12.4 km",
        navigationTrafficLabel: "路况顺畅",
        navigationAreaOnlyLabel: "仅区域级",
        navigationScaleLabel: "2 km",
        navigationCityLabel: "上海",
        navigationMapLabels: {
          huangpuRiver: "黄浦江",
          innerRing: "内环高架",
          middleRing: "中环路",
          centuryAvenue: "世纪大道",
          lujiazui: "陆家嘴",
          centuryPark: "世纪公园",
          zhangjiang: "张江",
          xujiahui: "徐家汇",
        },
        powerMemDrive: "PowerMem 智驾",
        sceneProjector: "场景投影",
        needsAttention: "需要处理",
        passenger: "副驾",
        comfort: "舒适",
        cabinReadout: "舱内 22.5°C",
        defaultClimateZone: "座舱空调",
        defaultClimateTemp: "22.5°C",
        defaultClimateReadout: "自动恒温",
        defaultSeatHeatLabel: "座椅加热",
        defaultSeatHeatLevel: "自动",
        defaultSeatHeatReadout: "待命",
        defaultMediaPreference: {
          title: "舒缓歌单",
          subtitle: "驾驶员音乐偏好",
          sourceLabel: "PowerMem 媒体",
          volumeLabel: "音量",
          volume: "22",
        },
      },
    },
    projection: {
      actTitles: {
        "Act 1": "建立偏好",
        "Act 2": "同句不同人",
        "Act 3": "组合例程",
        "Act 4": "能力边界",
        "Act 5": "地点回忆",
        "Act 6": "儿童媒体",
        "Act 7": "纪念日推荐",
        "Act 8": "驾驶模式",
        "Act 9": "主动关怀",
        "Act 10": "生命周期与隐私",
      },
      actSubtitles: {
        "Act 1": "结构化保存座舱偏好，不保存对话原文。",
        "Act 2": "结合乘员和座位应用舒适与安全边界。",
        "Act 3": "把座舱和驾驶偏好组合成一次例程。",
        "Act 4": "基于车辆档案回答能力问题。",
        "Act 5": "只返回区域级地点，不暴露精确地址。",
        "Act 6": "结合儿童媒体偏好与安全策略。",
        "Act 7": "给出关系建议，不自动发起导航。",
        "Act 8": "结合 SOC 和偏好推荐驾驶模式。",
        "Act 9": "低电量车态事件触发主动提醒。",
        "Act 10": "第 90 天衰减、归档或删除短期记忆。",
      },
      actRouteReadouts: {
        "Act 1": "结构化偏好 ADD",
        "Act 2": "按乘员区分的座舱调整",
        "Act 3": "例程 HVAC + 座椅 + 驾驶模式",
        "Act 4": "能力答复，无车控命令",
        "Act 5": "区域级导航建议",
        "Act 6": "低音量儿童安全媒体",
        "Act 7": "脱敏关系推荐",
        "Act 8": "结合 SOC 的驾驶模式",
        "Act 9": "低 SOC 事件 + 充电建议",
        "Act 10": "生命周期 UPDATE/DELETE 审计",
      },
      actors: {
        driver_primary: "驾驶员",
        passenger_front: "前排乘客",
        child_rear_left: "儿童",
      },
      liveMemoryUnavailable: "实时记忆不可用",
      error: "错误",
      liveModeNeedsAttention: "实时模式需要处理",
      backend: "后端",
      state: "状态",
      action: "动作",
      checkService: "检查服务",
      noProjectionUpdate: "没有投影更新",
      noFakeFallback: "没有模拟兜底",
      livePowerMemTrace: "实时 PowerMem 追踪",
      assistant: "语音助手",
      llmChat: "模型对话",
      actionTrace: "动作轨迹",
      scenarioTrace: "场景轨迹",
      disconnected: "未连接",
      trace: "追踪",
      synced: "已同步",
      memory: "记忆",
      noHit: "无命中",
      privacy: "隐私",
      evidenceVisible: "证据可见",
      ready: "就绪",
      actor: "角色",
      scene: "场景",
      source: "来源",
      scenario: "演示场景",
      syntheticDataOnly: "仅使用合成数据",
      live: "实时",
      linked: "已联动",
      cabinLinked: "座舱已联动",
      cabinLinkedSubtitle: "识别意图，调用记忆，完成空调与座椅联动。",
      intent: "意图",
      rememberedPreference: "冬季舒适偏好",
      navigationTitle: "地图导航",
      navigationSubtitle: "已进入地图模式，并加载区域级目的地。",
      navigationDock: "导航中",
      navigationIntent: "确认导航",
      navigationStatusActive: "导航中",
      navigationMapLabel: "地图路线",
      destination: "目的地",
      regionOnly: "仅区域级",
      suggestionOnly: "仅提供建议",
      anniversaryDateMasked: "纪念日日期已隐藏",
      regionLevelDestination: "区域级目的地",
      navigationRouteReadout: (destination) =>
        `区域级路线已加载：${destination}`,
      batteryCareTitle: "低电量主动关怀",
      batteryCareSubtitle: (soc, rangeKm) =>
        `检测到 SOC ${soc}%，剩余续航 ${rangeKm} km。`,
      batteryCareFlow: "低电量事件 · 偏好命中 · 充电建议 · 等待确认",
      batteryCarePolicyFlow: "低电量事件 · 安全策略 · 充电建议 · 等待确认",
      batteryCareMemoryMatched: "已命中充电偏好",
      batteryCareSafetyPolicy: "电池安全策略已启用",
      batteryCareAwaitingConfirmation: "等待驾驶员确认",
      batteryCareGuidanceReady: "充电建议已准备",
      nearestAvailableChargingStation: "最近可用的充电站",
      reachableChargingStation: "可到达的充电站",
      vehicleActionApplied: "PowerMem 已将记忆中的舒适方案恢复到车辆。",
      comfortControlRequest: "这句话被识别为座舱舒适控制请求。",
      noMemoryDetail: "这条命中没有可展示的记忆内容。",
      zoneLabels: {
        front_left: "驾驶员温区",
        front_right: "副驾温区",
        rear_left: "后排左侧温区",
      },
      coldIntentByActor: {
        driver_primary: "驾驶员感觉冷",
        passenger_front: "前排乘客感觉冷",
        child_rear_left: "儿童感觉冷",
      },
      temperature: "温度",
      seatHeat: "座椅加热",
      temperatureReadout: (beforeTemp, afterTemp) =>
        beforeTemp === "--" ? `目标 ${afterTemp}` : `${beforeTemp} -> ${afterTemp}`,
      seatHeatReadout: (beforeHeat, afterHeat) =>
        beforeHeat === "--" ? `${afterHeat} 档` : `${beforeHeat} -> ${afterHeat}`,
      actionSummary: (zone, temperatureReadout, seatHeatReadout) =>
        `${zone} ${temperatureReadout}，座椅加热 ${seatHeatReadout}`,
      routeReadout: (zone, temperatureReadout) =>
        `${zone} ${temperatureReadout}`,
      mediaPreferenceByActor: {
        driver_primary: {
          title: "舒缓歌单",
          subtitle: "驾驶员音乐偏好",
          sourceLabel: "PowerMem 媒体",
          volumeLabel: "音量",
          volume: "22",
        },
        passenger_front: {
          title: "周末舒缓歌单",
          subtitle: "前排乘客媒体偏好",
          sourceLabel: "PowerMem 媒体",
          volumeLabel: "音量",
          volume: "22",
        },
        child_rear_left: {
          title: "安静睡前故事",
          subtitle: "儿童媒体偏好",
          sourceLabel: "PowerMem 媒体",
          volumeLabel: "音量",
          volume: "18",
        },
      },
      mediaMemorySubtitle: "媒体偏好记忆",
    },
    evidencePanels: {
      cockpitStatus: {
        ariaLabel: "座舱状态",
        live: "实时 PowerMem",
        vehicle: "演示车辆",
        soc: "电量 62%",
        inside: "舱内 22°C",
        comfort: "舒适驾驶",
      },
      scenarioTimeline: {
        ariaLabel: "场景时间线",
      },
      memoryFlow: {
        title: "PowerMem 记忆流",
        empty: "还没有实时记忆命中。",
      },
      privacy: {
        ariaLabel: "隐私状态",
        text: "原始转写已排除。脱敏字段保持隐藏。",
      },
      vehicleState: {
        title: "车辆上下文",
        summaryLabel: "车辆状态摘要",
        empty: "实时后端返回后会显示车辆状态差异。",
      },
      recommendations: {
        title: "推荐",
        empty: "实时 PowerMem 证据返回后会显示推荐。",
      },
      memoryGraph: {
        title: "记忆图谱",
        groupLabel: "记忆图谱节点分组",
        empty: "返回实时响应后会显示被选中的记忆关系。",
        nodes: ["人物", "车辆", "地点", "媒体", "控制"],
      },
      lifecycle: {
        ariaLabel: "记忆生命周期时间线",
        empty: "执行第 10 幕或生命周期证据后会显示变更记录。",
        stages: ["活跃", "强化", "衰减", "归档", "删除"],
      },
      developerEvidence: {
        drawerLabel: "开发者证据抽屉",
        title: "开发者证据",
        exportTrace: "导出追踪",
        backendStatusLabel: "PowerMem 后端状态",
        live: "实时 PowerMem",
        disconnected: "PowerMem 未连接",
        noEvidence: "没有返回证据",
        steps: [
          ["request", "请求"],
          ["privacy", "隐私脱敏"],
          ["data_source", "数据来源"],
          ["operations", "操作链路"],
          ["memory_hits", "记忆命中"],
          ["decision", "决策"],
          ["vehicle_action", "车辆状态差异"],
          ["recommendations", "推荐"],
          ["lifecycle", "生命周期"],
          ["audit", "审计"],
          ["latency_ms", "延迟"],
        ],
      },
    },
  },
};
