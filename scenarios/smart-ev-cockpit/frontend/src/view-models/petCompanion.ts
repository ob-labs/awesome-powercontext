import type { ActorId, ActKey, ScenarioRecommendation, ScenarioResponse } from "../types/api";
import type { ProjectionScene, ScenarioStep } from "./projection";
import type { Locale } from "../i18n";

export type PetMood =
  | "curious"
  | "focused"
  | "delighted"
  | "protective"
  | "calm"
  | "urgent"
  | "alert"
  | "sorting";

export type PetAction =
  | "capture_preference"
  | "identify_actor"
  | "chain_routine"
  | "guard_boundary"
  | "mask_location"
  | "soften_media"
  | "surface_reminder"
  | "nudge_drive_mode"
  | "watch_battery"
  | "sort_lifecycle"
  | "standby"
  | "report_error";

export type PetTarget =
  | "climate"
  | "seat"
  | "routine"
  | "boundary"
  | "navigation"
  | "media"
  | "relationship"
  | "drive"
  | "battery"
  | "lifecycle"
  | "memory"
  | "error";

export type PetAnchor =
  | "driver"
  | "passenger"
  | "child"
  | "chat_driver"
  | "chat_passenger"
  | "chat_child"
  | "climate"
  | "media"
  | "navigation"
  | "drive"
  | "battery"
  | "lifecycle"
  | "routine"
  | "boundary"
  | "memory"
  | "error";

export interface PetCompanionState {
  name: string;
  mood: PetMood;
  action: PetAction;
  target: PetTarget;
  originAnchor: PetAnchor;
  anchor: PetAnchor;
  travelLabel: string;
  speech: string;
  cueLabel: string;
  memoryOrbLabel: string;
}

interface BuildPetCompanionStateArgs {
  step: ScenarioStep;
  response: ScenarioResponse | null;
  projection: ProjectionScene;
  liveError: string | null;
  selectedActorId: ActorId;
  locale: Locale;
}

type PetCompanionCopy = Omit<
  PetCompanionState,
  "name" | "originAnchor" | "anchor" | "travelLabel"
>;

const ZH_ACT_COPY: Record<string, PetCompanionCopy> = {
  "Act 1": {
    mood: "curious",
    action: "capture_preference",
    target: "climate",
    speech: "我把这组座舱温度和座椅设置记成可复用偏好。",
    cueLabel: "空调和座椅偏好",
    memoryOrbLabel: "偏好记忆",
  },
  "Act 2": {
    mood: "focused",
    action: "identify_actor",
    target: "seat",
    speech: "我先确认是谁在说话，再联动对应座位。",
    cueLabel: "乘员身份",
    memoryOrbLabel: "乘员记忆",
  },
  "Act 3": {
    mood: "delighted",
    action: "chain_routine",
    target: "routine",
    speech: "空调、座椅和驾驶模式已经串成一条例程。",
    cueLabel: "组合例程",
    memoryOrbLabel: "例程记忆",
  },
  "Act 4": {
    mood: "protective",
    action: "guard_boundary",
    target: "boundary",
    speech: "我先核对车辆能力边界，再回答这个请求。",
    cueLabel: "能力边界",
    memoryOrbLabel: "车辆档案",
  },
  "Act 5": {
    mood: "protective",
    action: "mask_location",
    target: "navigation",
    speech: "我只圈出区域级目的地，不暴露精确地址。",
    cueLabel: "隐私导航",
    memoryOrbLabel: "脱敏地点",
  },
  "Act 6": {
    mood: "calm",
    action: "soften_media",
    target: "media",
    speech: "我把内容切到儿童助眠风格，并控制音量。",
    cueLabel: "儿童媒体",
    memoryOrbLabel: "媒体偏好",
  },
  "Act 7": {
    mood: "delighted",
    action: "surface_reminder",
    target: "relationship",
    speech: "我找到重要日子记忆，只给建议，不自动行动。",
    cueLabel: "关系提醒",
    memoryOrbLabel: "纪念日记忆",
  },
  "Act 8": {
    mood: "focused",
    action: "nudge_drive_mode",
    target: "drive",
    speech: "我正在把驾驶模式拨到更合适的位置。",
    cueLabel: "驾驶模式",
    memoryOrbLabel: "驾驶偏好",
  },
  "Act 9": {
    mood: "urgent",
    action: "watch_battery",
    target: "battery",
    speech: "低电量提醒已亮起，我准备了充电安全建议。",
    cueLabel: "低电量关怀",
    memoryOrbLabel: "充电偏好",
  },
  "Act 10": {
    mood: "sorting",
    action: "sort_lifecycle",
    target: "lifecycle",
    speech: "我正在分拣记忆：保留、归档或删除。",
    cueLabel: "生命周期",
    memoryOrbLabel: "记忆分拣",
  },
};

const EN_ACT_COPY: Record<string, PetCompanionCopy> = {
  "Act 1": {
    mood: "curious",
    action: "capture_preference",
    target: "climate",
    speech: "I saved this cabin temperature and seat setup as a reusable preference.",
    cueLabel: "Climate and seat preference",
    memoryOrbLabel: "Preference memory",
  },
  "Act 2": {
    mood: "focused",
    action: "identify_actor",
    target: "seat",
    speech: "I check who is speaking before adjusting the right seat.",
    cueLabel: "Occupant identity",
    memoryOrbLabel: "Occupant memory",
  },
  "Act 3": {
    mood: "delighted",
    action: "chain_routine",
    target: "routine",
    speech: "Climate, seat, and drive mode are linked into one routine.",
    cueLabel: "Combined routine",
    memoryOrbLabel: "Routine memory",
  },
  "Act 4": {
    mood: "protective",
    action: "guard_boundary",
    target: "boundary",
    speech: "I check the vehicle capability boundary before answering.",
    cueLabel: "Capability boundary",
    memoryOrbLabel: "Vehicle profile",
  },
  "Act 5": {
    mood: "protective",
    action: "mask_location",
    target: "navigation",
    speech: "I show the region only and keep the exact address hidden.",
    cueLabel: "Private navigation",
    memoryOrbLabel: "Masked location",
  },
  "Act 6": {
    mood: "calm",
    action: "soften_media",
    target: "media",
    speech: "I switch to child sleep media and keep the volume low.",
    cueLabel: "Child media",
    memoryOrbLabel: "Media preference",
  },
  "Act 7": {
    mood: "delighted",
    action: "surface_reminder",
    target: "relationship",
    speech: "I found an important date and only suggest the next step.",
    cueLabel: "Relationship reminder",
    memoryOrbLabel: "Anniversary memory",
  },
  "Act 8": {
    mood: "focused",
    action: "nudge_drive_mode",
    target: "drive",
    speech: "I am nudging the drive mode to the better setting.",
    cueLabel: "Drive mode",
    memoryOrbLabel: "Driving preference",
  },
  "Act 9": {
    mood: "urgent",
    action: "watch_battery",
    target: "battery",
    speech: "The low-battery signal is on, and I prepared charging care.",
    cueLabel: "Low-battery care",
    memoryOrbLabel: "Charging preference",
  },
  "Act 10": {
    mood: "sorting",
    action: "sort_lifecycle",
    target: "lifecycle",
    speech: "I am sorting memories into keep, archive, or delete.",
    cueLabel: "Lifecycle",
    memoryOrbLabel: "Memory sorting",
  },
};

export function buildPetCompanionState({
  step,
  response,
  projection,
  liveError,
  selectedActorId,
  locale,
}: BuildPetCompanionStateArgs): PetCompanionState {
  const name = locale === "zh" ? "忆灵" : "MemoFox";
  const originAnchor = actorAnchor(selectedActorId);
  if (liveError || projection.status === "error") {
    return withAnchors({
      name,
      mood: "alert",
      action: "report_error",
      target: "error",
      speech:
        locale === "zh"
          ? `PowerContext 链路需要检查：${liveError ?? projection.subtitle}`
          : `PowerContext needs attention: ${liveError ?? projection.subtitle}`,
      cueLabel: locale === "zh" ? "链路检查" : "Link check",
      memoryOrbLabel: locale === "zh" ? "异常信号" : "Error signal",
    }, originAnchor, "error");
  }

  const actKey = response?.act_key ?? step.actKey ?? step.act;
  const base = (locale === "zh" ? ZH_ACT_COPY : EN_ACT_COPY)[actKey];

  if (!base) {
    return withAnchors({
      name,
      mood: "curious",
      action: "standby",
      target: "memory",
      speech:
        locale === "zh"
          ? "我在旁边观察这次座舱记忆请求。"
          : "I am watching this cockpit memory request.",
      cueLabel: locale === "zh" ? actorLabel(selectedActorId, locale) : "Memory",
      memoryOrbLabel: locale === "zh" ? "相关记忆" : "Relevant memory",
    }, originAnchor, chatAnchor(selectedActorId));
  }

  const anchor = response
    ? anchorForTarget(base.target, selectedActorId)
    : chatAnchor(selectedActorId);
  const state: PetCompanionState = withAnchors(
    { name, ...base },
    originAnchor,
    anchor,
  );
  if (actKey === "Act 2") {
    state.cueLabel =
      locale === "zh"
        ? `当前乘员：${actorLabel(selectedActorId, locale)}`
        : `Current occupant: ${actorLabel(selectedActorId, locale)}`;
  }
  if (actKey === "Act 8") {
    return withDriveMode(state, response, locale);
  }
  if (actKey === "Act 9") {
    return withBatteryCare(state, response, locale);
  }
  if (actKey === "Act 10") {
    return withLifecycleCount(state, response, locale);
  }
  return state;
}

function withAnchors(
  state: Omit<PetCompanionState, "originAnchor" | "anchor" | "travelLabel">,
  originAnchor: PetAnchor,
  anchor: PetAnchor,
): PetCompanionState {
  return {
    ...state,
    originAnchor,
    anchor,
    travelLabel: `${originAnchor}-to-${anchor}`,
  };
}

function actorAnchor(actorId: ActorId): PetAnchor {
  const anchors: Record<ActorId, PetAnchor> = {
    driver_primary: "driver",
    passenger_front: "passenger",
    child_rear_left: "child",
  };
  return anchors[actorId] ?? "driver";
}

function chatAnchor(actorId: ActorId): PetAnchor {
  const anchors: Record<ActorId, PetAnchor> = {
    driver_primary: "chat_driver",
    passenger_front: "chat_passenger",
    child_rear_left: "chat_child",
  };
  return anchors[actorId] ?? "chat_driver";
}

function anchorForTarget(target: PetTarget, actorId: ActorId): PetAnchor {
  if (target === "seat") {
    return actorAnchor(actorId);
  }
  const anchors: Record<PetTarget, PetAnchor> = {
    climate: "climate",
    seat: actorAnchor(actorId),
    routine: "routine",
    boundary: "boundary",
    navigation: "navigation",
    media: "media",
    relationship: "memory",
    drive: "drive",
    battery: "battery",
    lifecycle: "lifecycle",
    memory: "memory",
    error: "error",
  };
  return anchors[target];
}

function withDriveMode(
  state: PetCompanionState,
  response: ScenarioResponse | null,
  locale: Locale,
): PetCompanionState {
  const mode = response?.recommendations
    .map((recommendation) => readString(recommendation.metadata?.drive_mode))
    .find(Boolean);
  if (!mode) {
    return state;
  }

  const modeLabel = localizedDriveMode(mode, locale);
  return {
    ...state,
    speech:
      locale === "zh"
        ? `我已把驾驶模式拨到${modeLabel}。`
        : `I nudged the drive mode to ${mode}.`,
    cueLabel:
      locale === "zh" ? `驾驶模式：${mode}` : `Drive mode: ${mode}`,
  };
}

function withBatteryCare(
  state: PetCompanionState,
  response: ScenarioResponse | null,
  locale: Locale,
): PetCompanionState {
  const soc = readSoc(response?.recommendations ?? []);
  if (soc === undefined) {
    return state;
  }
  const urgent = soc < 10;
  return {
    ...state,
    mood: urgent ? "urgent" : "focused",
    speech:
      locale === "zh"
        ? `电量 ${soc}%：低电量提醒已亮起，我准备了充电建议。`
        : `Battery ${soc}%: low-battery care is active.`,
    cueLabel: locale === "zh" ? `SOC ${soc}%` : `SOC ${soc}%`,
  };
}

function withLifecycleCount(
  state: PetCompanionState,
  response: ScenarioResponse | null,
  locale: Locale,
): PetCompanionState {
  const completed = response?.lifecycle?.completed_operations?.length ?? 0;
  if (completed <= 0) {
    return {
      ...state,
      speech:
        locale === "zh"
          ? "生命周期回顾已完成，当前没有新增分拣动作。"
          : "Lifecycle review is complete with no new sorting actions.",
    };
  }
  return {
    ...state,
    speech:
      locale === "zh"
        ? `我已分拣 ${completed} 条记忆：保留、归档或删除。`
        : `I sorted ${completed} memories into keep, archive, or delete.`,
    cueLabel:
      locale === "zh"
        ? `已完成 ${completed} 项`
        : `${completed} completed`,
  };
}

function readSoc(recommendations: ScenarioRecommendation[]): number | undefined {
  for (const recommendation of recommendations) {
    const value = recommendation.metadata?.soc;
    if (typeof value === "number") {
      return value;
    }
  }
  return undefined;
}

function readString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function localizedDriveMode(mode: string, locale: Locale): string {
  if (locale !== "zh") {
    return mode;
  }
  const labels: Record<string, string> = {
    comfort: "舒适模式",
    eco: "节能模式",
    sport: "运动模式",
  };
  return labels[mode] ?? `${mode}模式`;
}

function actorLabel(actorId: ActorId, locale: Locale): string {
  const zh: Record<ActorId, string> = {
    driver_primary: "驾驶员",
    passenger_front: "前排乘客",
    child_rear_left: "儿童",
  };
  const en: Record<ActorId, string> = {
    driver_primary: "Driver",
    passenger_front: "Passenger",
    child_rear_left: "Child",
  };
  return (locale === "zh" ? zh : en)[actorId];
}
