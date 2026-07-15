import type {
  ActorId,
  ScenarioMemoryHit,
  ScenarioResponse,
  SeatPosition,
} from "../types/api";
import {
  APP_COPY,
  DEFAULT_LOCALE,
  type Locale,
  type MediaPreferenceLabels,
  type ProjectionLabels,
} from "../i18n";

export interface ScenarioStep {
  day: string;
  act: string;
  actKey?: string;
  utterance: string;
  actorId: ActorId;
  seatPosition: SeatPosition;
  initialHvacTargetTempC?: number;
}

export interface ProjectionChip {
  label: string;
  value: string;
}

export interface ProjectionStoryStep {
  label: string;
  value: string;
  detail: string;
}

export interface ProjectionClimateAction {
  zoneLabel: string;
  temperatureLabel: string;
  beforeTemp: string;
  afterTemp: string;
  temperatureReadout: string;
  seatHeatLabel: string;
  beforeSeatHeat: string;
  afterSeatHeat: string;
  seatHeatReadout: string;
}

export type ProjectionMediaPreference = MediaPreferenceLabels;

export type ProjectionMode =
  | "scenario"
  | "action"
  | "chat"
  | "navigation"
  | "recommendation"
  | "battery-care"
  | "error";

export type ProjectionBatteryStatus = "normal" | "low" | "critical";

export interface ProjectionBatteryState {
  percent: number;
  rangeKm: number;
  status: ProjectionBatteryStatus;
  isLive: boolean;
}

export interface ProjectionNavigation {
  destinationLabel: string;
  statusLabel: string;
  routeLabel: string;
}

export interface ProjectionRecommendation {
  title: string;
  summary: string;
  policyLabel: string;
  regionLabel: string;
  privacyLabel: string;
}

export interface ProjectionBatteryCare {
  title: string;
  summary: string;
  destinationLabel: string;
  memoryLabel: string;
  actionLabel: string;
}

export interface ProjectionScene {
  id: string;
  mode: ProjectionMode;
  title: string;
  subtitle: string;
  scoreLabel: string;
  dockLabel: string;
  chips: ProjectionChip[];
  storySteps?: ProjectionStoryStep[];
  climateAction?: ProjectionClimateAction;
  navigation?: ProjectionNavigation;
  recommendation?: ProjectionRecommendation;
  batteryCare?: ProjectionBatteryCare;
  mediaPreference?: ProjectionMediaPreference;
  batteryState?: ProjectionBatteryState;
  routeReadout: string;
  mapLabel?: string;
  showMap: boolean;
  privacyLabel: string;
  status: "idle" | "ready" | "error";
}

interface BuildProjectionSceneArgs {
  step: ScenarioStep;
  response: ScenarioResponse | null;
  liveError: string | null;
  selectedActorId: ActorId;
  selectedSeatPosition?: SeatPosition;
  locale?: Locale;
}

export function buildProjectionScene({
  step,
  response,
  liveError,
  selectedActorId,
  selectedSeatPosition,
  locale = DEFAULT_LOCALE,
}: BuildProjectionSceneArgs): ProjectionScene {
  const copy = APP_COPY[locale].projection;
  const actKey = step.actKey ?? step.act;
  const seatPosition = selectedSeatPosition ?? step.seatPosition;
  const mediaPreference = buildMediaPreference(response, selectedActorId, copy);
  const batteryState = buildBatteryState(step, response);

  if (liveError) {
    return {
      id: `${step.day}-${step.act}-error`,
      mode: "error",
      title: copy.liveMemoryUnavailable,
      subtitle: liveError,
      scoreLabel: copy.error,
      dockLabel: copy.liveModeNeedsAttention,
      chips: [
        { label: copy.backend, value: "PowerMem" },
        { label: copy.state, value: copy.error },
        { label: copy.action, value: copy.checkService },
      ],
      routeReadout: copy.noProjectionUpdate,
      showMap: false,
      mediaPreference,
      batteryState,
      privacyLabel: copy.noFakeFallback,
      status: "error",
    };
  }

  if (response) {
    if (isOrdinaryChat(response)) {
      const primaryMemory = response.memory_hits[0];
      return {
        id: response.trace_id,
        mode: "chat",
        title: copy.assistant,
        subtitle: response.assistant_reply,
        scoreLabel: copy.live,
        dockLabel: response.powermem_connected ? copy.llmChat : copy.disconnected,
        chips: [
          {
            label: copy.trace,
            value: response.powermem_connected ? copy.synced : copy.disconnected,
          },
          { label: copy.memory, value: primaryMemory?.memory_kind ?? copy.noHit },
          {
            label: copy.privacy,
            value: String(response.privacy_report.redaction_count ?? 0),
          },
        ],
        routeReadout: copy.llmChat,
        showMap: false,
        mediaPreference,
        batteryState,
        privacyLabel: copy.evidenceVisible,
        status: "ready",
      };
    }

    const batteryCareProjection = buildBatteryCareProjection(
      response,
      copy,
      mediaPreference,
      batteryState,
    );
    if (batteryCareProjection) {
      return batteryCareProjection;
    }

    const relationshipProjection = buildRelationshipProjection(
      response,
      copy,
      mediaPreference,
      batteryState,
    );
    if (relationshipProjection) {
      return relationshipProjection;
    }

    const navigationProjection = buildNavigationProjection(
      response,
      copy,
      mediaPreference,
      batteryState,
    );
    if (navigationProjection) {
      return navigationProjection;
    }

    const primaryMemory = response.memory_hits[0];
    const climateAction = buildClimateAction(response, seatPosition, copy);
    const actionValue = formatActionValue(climateAction, copy);
    const memoryDetail = primaryMemory?.content?.trim() || copy.noMemoryDetail;
    return {
      id: response.trace_id,
      mode: "action",
      title: copy.cabinLinked,
      subtitle: copy.cabinLinkedSubtitle,
      scoreLabel: copy.linked,
      dockLabel: response.powermem_connected
        ? copy.livePowerMemTrace
        : copy.disconnected,
      chips: [
        { label: copy.intent, value: copy.coldIntentByActor[selectedActorId] },
        { label: copy.memory, value: copy.rememberedPreference },
        { label: copy.action, value: actionValue },
      ],
      storySteps: [
        {
          label: copy.intent,
          value: copy.coldIntentByActor[selectedActorId],
          detail: copy.comfortControlRequest,
        },
        {
          label: copy.memory,
          value: copy.rememberedPreference,
          detail: memoryDetail,
        },
        {
          label: copy.action,
          value: actionValue,
          detail: copy.vehicleActionApplied,
        },
      ],
      climateAction,
      mediaPreference,
      batteryState,
      routeReadout: climateAction
        ? copy.routeReadout(climateAction.zoneLabel, climateAction.temperatureReadout)
        : copy.vehicleActionApplied,
      mapLabel: copy.actionTrace,
      showMap: false,
      privacyLabel: copy.evidenceVisible,
      status: "ready",
    };
  }

  return {
    id: `${step.day}-${step.act}`,
    mode: "scenario",
    title: copy.actTitles[actKey] ?? step.act,
    subtitle: copy.actSubtitles[actKey] ?? step.utterance,
    scoreLabel: copy.ready,
    dockLabel: step.day,
    chips: [
      { label: copy.actor, value: copy.actors[selectedActorId] },
      { label: copy.scene, value: step.act },
      { label: copy.source, value: copy.scenario },
    ],
    routeReadout: copy.actRouteReadouts[actKey] ?? step.utterance,
    mapLabel: copy.scenarioTrace,
    showMap: true,
    mediaPreference,
    batteryState,
    privacyLabel: copy.syntheticDataOnly,
    status: "idle",
  };
}

function buildBatteryCareProjection(
  response: ScenarioResponse,
  copy: ProjectionLabels,
  mediaPreference: ProjectionMediaPreference,
  batteryState: ProjectionBatteryState,
): ProjectionScene | undefined {
  const recommendation = response.recommendations.find(
    (candidate) => candidate.type === "charging_safety",
  );
  if (response.act_key !== "Act 9" || !recommendation) {
    return undefined;
  }

  const selectedMemoryIds = new Set(response.selected_memory_ids ?? []);
  const hasChargingPreference = response.memory_hits.some(
    (hit) =>
      hit.memory_kind === "charging_preference" && selectedMemoryIds.has(hit.memory_id),
  );
  const chargingStrategy = recommendation.metadata?.charging_strategy;
  const destinationLabel =
    chargingStrategy === "nearest_available"
      ? copy.nearestAvailableChargingStation
      : copy.reachableChargingStation;
  const memoryLabel = hasChargingPreference
    ? copy.batteryCareMemoryMatched
    : copy.batteryCareSafetyPolicy;
  const actionLabel =
    recommendation.action_policy === "confirm"
      ? copy.batteryCareAwaitingConfirmation
      : copy.batteryCareGuidanceReady;
  const title = recommendation.title ?? copy.batteryCareTitle;
  const summary = recommendation.summary ?? response.assistant_reply;

  return {
    id: response.trace_id,
    mode: "battery-care",
    title: copy.batteryCareTitle,
    subtitle: copy.batteryCareSubtitle(batteryState.percent, batteryState.rangeKm),
    scoreLabel: copy.linked,
    dockLabel: response.powermem_connected
      ? copy.livePowerMemTrace
      : copy.disconnected,
    chips: [
      {
        label: copy.state,
        value: `SOC ${batteryState.percent}% · ${batteryState.rangeKm} km`,
      },
      { label: copy.memory, value: memoryLabel },
      { label: copy.action, value: actionLabel },
    ],
    storySteps: [
      {
        label: copy.state,
        value: `SOC ${batteryState.percent}% · ${batteryState.rangeKm} km`,
        detail: copy.batteryCareSubtitle(batteryState.percent, batteryState.rangeKm),
      },
      {
        label: copy.memory,
        value: memoryLabel,
        detail: destinationLabel,
      },
      {
        label: copy.action,
        value: actionLabel,
        detail: summary,
      },
    ],
    batteryCare: {
      title,
      summary,
      destinationLabel,
      memoryLabel,
      actionLabel,
    },
    mediaPreference,
    batteryState,
    routeReadout: hasChargingPreference
      ? copy.batteryCareFlow
      : copy.batteryCarePolicyFlow,
    showMap: false,
    privacyLabel: copy.evidenceVisible,
    status: "ready",
  };
}

function buildRelationshipProjection(
  response: ScenarioResponse,
  copy: ProjectionLabels,
  mediaPreference: ProjectionMediaPreference,
  batteryState: ProjectionBatteryState,
): ProjectionScene | undefined {
  const recommendation = response.recommendations.find(
    (candidate) => candidate.type === "relationship",
  );
  if (!recommendation) {
    return undefined;
  }

  const title = recommendation.title ?? copy.actTitles["Act 7"];
  const summary = recommendation.summary ?? response.assistant_reply;
  const region = recommendation.metadata?.region;
  const regionLabel =
    typeof region === "string" && region.trim()
      ? `${region} · ${copy.regionOnly}`
      : copy.regionOnly;
  const routeReadout = `${copy.suggestionOnly} · ${copy.anniversaryDateMasked}`;

  return {
    id: response.trace_id,
    mode: "recommendation",
    title,
    subtitle: summary,
    scoreLabel: copy.linked,
    dockLabel: response.powermem_connected
      ? copy.livePowerMemTrace
      : copy.disconnected,
    chips: [
      { label: copy.destination, value: regionLabel },
      { label: copy.action, value: copy.suggestionOnly },
      { label: copy.privacy, value: copy.anniversaryDateMasked },
    ],
    recommendation: {
      title,
      summary,
      policyLabel: copy.suggestionOnly,
      regionLabel,
      privacyLabel: copy.anniversaryDateMasked,
    },
    mediaPreference,
    batteryState,
    routeReadout,
    showMap: false,
    privacyLabel: copy.anniversaryDateMasked,
    status: "ready",
  };
}

function isOrdinaryChat(response: ScenarioResponse): boolean {
  const hasChatOperation = response.operations.some(
    (operation) => operation.type.toUpperCase() === "CHAT",
  );
  const hasVehicleAction =
    response.vehicle_state_diff.length > 0 || response.recommendations.length > 0;

  return hasChatOperation && !hasVehicleAction;
}

function buildNavigationProjection(
  response: ScenarioResponse,
  copy: ProjectionLabels,
  mediaPreference: ProjectionMediaPreference,
  batteryState: ProjectionBatteryState,
): ProjectionScene | undefined {
  const navigation = readRecord(response.vehicle_state.navigation);
  if (navigation?.mode !== "map") {
    return undefined;
  }

  const hasNavigationSignal =
    response.vehicle_state_diff.some((diff) => diff.field.startsWith("navigation")) ||
    response.recommendations.some(
      (recommendation) =>
        recommendation.type === "navigation" &&
        recommendation.action_policy === "execute",
    );
  if (!hasNavigationSignal) {
    return undefined;
  }

  const destination = readRecord(navigation.destination);
  const region =
    typeof destination?.region === "string" ? destination.region : undefined;
  const destinationLabel =
    typeof navigation.destination_label === "string"
      ? navigation.destination_label
      : region ?? copy.regionLevelDestination;
  const routeLabel = copy.navigationRouteReadout(destinationLabel);

  return {
    id: response.trace_id,
    mode: "navigation",
    title: copy.navigationTitle,
    subtitle: response.assistant_reply || copy.navigationSubtitle,
    scoreLabel: copy.navigationStatusActive,
    dockLabel: copy.navigationDock,
    chips: [
      { label: copy.intent, value: copy.navigationIntent },
      { label: copy.destination, value: destinationLabel },
      { label: copy.privacy, value: copy.regionOnly },
    ],
    routeReadout: routeLabel,
    mapLabel: copy.navigationMapLabel,
    showMap: true,
    navigation: {
      destinationLabel,
      statusLabel: copy.navigationStatusActive,
      routeLabel,
    },
    mediaPreference,
    batteryState,
    privacyLabel: copy.evidenceVisible,
    status: "ready",
  };
}

const DEFAULT_BATTERY_STATE = {
  percent: 62,
  rangeKm: 305,
};

const SCENARIO_BATTERY_STATE_BY_ACT: Record<
  string,
  { percent: number; rangeKm: number }
> = {
  "Act 1": { percent: 74, rangeKm: 382 },
  "Act 2": { percent: 70, rangeKm: 354 },
  "Act 3": { percent: 66, rangeKm: 332 },
  "Act 4": { percent: 63, rangeKm: 318 },
  "Act 5": { percent: 60, rangeKm: 298 },
  "Act 6": DEFAULT_BATTERY_STATE,
  "Act 7": { percent: 58, rangeKm: 286 },
  "Act 8": { percent: 52, rangeKm: 260 },
  "Act 9": { percent: 18, rangeKm: 76 },
  "Act 10": { percent: 41, rangeKm: 210 },
};

export function buildScenarioBatteryState(
  step: ScenarioStep | undefined,
): ProjectionBatteryState {
  return buildScenarioBatteryStateByAct(step?.actKey ?? step?.act);
}

function buildBatteryState(
  step: ScenarioStep,
  response: ScenarioResponse | null,
): ProjectionBatteryState {
  const actKey = response?.act_key ?? step.actKey ?? step.act;
  const fallback = buildScenarioBatteryStateByAct(actKey);
  const signaledSoc =
    readDiffAfterNumber(response, "soc") ??
    readRecommendationMetadataNumber(response, "soc");
  const signaledRangeKm =
    readDiffAfterNumber(response, "range_km") ??
    readRecommendationMetadataNumber(response, "range_km");
  const hasBatterySignal =
    signaledSoc !== undefined || signaledRangeKm !== undefined;
  const liveSoc = hasBatterySignal
    ? signaledSoc ?? readVehicleNumber(response?.vehicle_state, "soc")
    : undefined;
  const liveRangeKm = hasBatterySignal
    ? signaledRangeKm ?? readVehicleNumber(response?.vehicle_state, "range_km")
    : undefined;
  const percent = normalizeBatteryPercent(liveSoc ?? fallback.percent);
  const rangeKm = normalizeRangeKm(liveRangeKm ?? fallback.rangeKm);

  return {
    percent,
    rangeKm,
    status: inferBatteryStatus(percent),
    isLive: liveSoc !== undefined || liveRangeKm !== undefined,
  };
}

function buildScenarioBatteryStateByAct(
  actKey: string | undefined,
): ProjectionBatteryState {
  const fallback = actKey
    ? SCENARIO_BATTERY_STATE_BY_ACT[actKey] ?? DEFAULT_BATTERY_STATE
    : DEFAULT_BATTERY_STATE;
  const percent = normalizeBatteryPercent(fallback.percent);

  return {
    percent,
    rangeKm: normalizeRangeKm(fallback.rangeKm),
    status: inferBatteryStatus(percent),
    isLive: false,
  };
}

function inferBatteryStatus(percent: number): ProjectionBatteryStatus {
  if (percent <= 10) {
    return "critical";
  }
  if (percent <= 20) {
    return "low";
  }
  return "normal";
}

function buildClimateAction(
  response: ScenarioResponse,
  seatPosition: SeatPosition,
  copy: ProjectionLabels,
): ProjectionClimateAction | undefined {
  const zoneLabel = copy.zoneLabels[seatPosition];
  const tempKey = `${seatPosition}_target_temp`;
  const hvacDiff = response.vehicle_state_diff.find((diff) => diff.field === "hvac");
  const hvacLeafDiff = response.vehicle_state_diff.find(
    (diff) => diff.field === `hvac.${tempKey}`,
  );
  const seatHeatDiff = response.vehicle_state_diff.find(
    (diff) => diff.field === "seat_heat",
  );
  const seatHeatLeafDiff = response.vehicle_state_diff.find(
    (diff) => diff.field === `seat_heat.${seatPosition}`,
  );
  const beforeTemp =
    readNestedNumber(hvacDiff?.before, tempKey) ?? readNumber(hvacLeafDiff?.before);
  const afterTemp =
    readNestedNumber(hvacDiff?.after, tempKey) ??
    readNumber(hvacLeafDiff?.after) ??
    readNestedNumber(response.vehicle_state.hvac, tempKey);
  const beforeSeatHeat =
    readNestedNumber(seatHeatDiff?.before, seatPosition) ??
    readNumber(seatHeatLeafDiff?.before);
  const afterSeatHeat =
    readNestedNumber(seatHeatDiff?.after, seatPosition) ??
    readNumber(seatHeatLeafDiff?.after) ??
    readNestedNumber(response.vehicle_state.seat_heat, seatPosition);

  if (
    typeof beforeTemp !== "number" &&
    typeof afterTemp !== "number" &&
    typeof beforeSeatHeat !== "number" &&
    typeof afterSeatHeat !== "number"
  ) {
    return undefined;
  }

  const beforeTempLabel = formatTemp(beforeTemp);
  const afterTempLabel = formatTemp(afterTemp);
  const beforeSeatHeatLabel = formatLevel(beforeSeatHeat);
  const afterSeatHeatLabel = formatLevel(afterSeatHeat);

  return {
    zoneLabel,
    temperatureLabel: copy.temperature,
    beforeTemp: beforeTempLabel,
    afterTemp: afterTempLabel,
    temperatureReadout: copy.temperatureReadout(beforeTempLabel, afterTempLabel),
    seatHeatLabel: copy.seatHeat,
    beforeSeatHeat: beforeSeatHeatLabel,
    afterSeatHeat: afterSeatHeatLabel,
    seatHeatReadout: copy.seatHeatReadout(beforeSeatHeatLabel, afterSeatHeatLabel),
  };
}

function buildMediaPreference(
  response: ScenarioResponse | null,
  actorId: ActorId,
  copy: ProjectionLabels,
): ProjectionMediaPreference {
  const defaultPreference = copy.mediaPreferenceByActor[actorId];
  const mediaMemory = response?.memory_hits.find(isMediaMemory);

  if (!mediaMemory?.content) {
    return defaultPreference;
  }

  return {
    ...defaultPreference,
    title: inferMediaTitle(mediaMemory.content, defaultPreference.title),
    subtitle: copy.mediaMemorySubtitle,
    volume: inferVolume(mediaMemory.content) ?? defaultPreference.volume,
  };
}

function isMediaMemory(memory: ScenarioMemoryHit): boolean {
  const kind = memory.memory_kind?.toLowerCase() ?? "";
  const content = memory.content?.toLowerCase() ?? "";
  return (
    kind.includes("media") ||
    content.includes("playlist") ||
    content.includes("music") ||
    content.includes("audio") ||
    content.includes("story")
  );
}

function inferMediaTitle(content: string, fallback: string): string {
  const normalized = content.toLowerCase();
  if (fallback.includes("舒缓") || fallback.includes("安静")) {
    if (normalized.includes("bedtime stor")) {
      return "安静睡前故事";
    }
    if (normalized.includes("calm music")) {
      return "平静音乐";
    }
    if (normalized.includes("relaxed playlist")) {
      return "舒缓歌单";
    }
  }

  if (normalized.includes("bedtime stor")) {
    return "Quiet bedtime stories";
  }
  if (normalized.includes("calm music")) {
    return "Calm music";
  }
  if (normalized.includes("relaxed playlist")) {
    return "Relaxed playlists";
  }
  return fallback;
}

function inferVolume(content: string): string | undefined {
  const match = content.match(/volume\s+(\d+)/i);
  return match?.[1];
}

function formatActionValue(
  climateAction: ProjectionClimateAction | undefined,
  copy: ProjectionLabels,
): string {
  if (!climateAction) {
    return copy.vehicleActionApplied;
  }
  return copy.actionSummary(
    climateAction.zoneLabel,
    climateAction.temperatureReadout,
    climateAction.seatHeatReadout,
  );
}

function readNestedNumber(value: unknown, key: string): number | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }
  const candidate = (value as Record<string, unknown>)[key];
  return readNumber(candidate);
}

function readVehicleNumber(
  vehicleState: Record<string, unknown> | undefined,
  key: string,
): number | undefined {
  return readNumber(vehicleState?.[key]);
}

function readDiffAfterNumber(
  response: ScenarioResponse | null,
  field: string,
): number | undefined {
  const diff = response?.vehicle_state_diff.find((item) => item.field === field);
  return readNumber(diff?.after);
}

function readRecommendationMetadataNumber(
  response: ScenarioResponse | null,
  key: string,
): number | undefined {
  for (const recommendation of response?.recommendations ?? []) {
    const value = readNumber(recommendation.metadata?.[key]);
    if (value !== undefined) {
      return value;
    }
  }
  return undefined;
}

function readNumber(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
}

function normalizeBatteryPercent(value: number): number {
  return Math.min(100, Math.max(0, Math.round(value)));
}

function normalizeRangeKm(value: number): number {
  return Math.max(0, Math.round(value));
}

function readRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : undefined;
}

function formatTemp(value: number | undefined): string {
  return typeof value === "number" ? `${value}°C` : "--";
}

function formatLevel(value: number | undefined): string {
  return typeof value === "number" ? String(value) : "--";
}
