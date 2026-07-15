import { deleteJson, getJson, postJson, putJson } from "./client";
import type {
  ChatHistoryRequest,
  ChatHistoryResponse,
  DeleteTestDataRequest,
  GenerateTestDataRequest,
  ImportTestDataRequest,
  LifecycleRequest,
  ScenarioResponse,
  TestDataStatus,
  UpdateUserIdentityRequest,
  UtteranceRequest,
  UserIdentitiesResponse,
  UserProfileResponse,
  VehicleEventRequest,
} from "../types/api";

export function createUtterance(payload: UtteranceRequest): Promise<ScenarioResponse> {
  return postJson<UtteranceRequest, ScenarioResponse>(
    "/api/scenarios/smart-ev-cockpit/utter",
    payload,
  );
}

export function createVehicleEvent(
  payload: VehicleEventRequest,
): Promise<ScenarioResponse> {
  return postJson<VehicleEventRequest, ScenarioResponse>(
    "/api/scenarios/smart-ev-cockpit/events/vehicle",
    payload,
  );
}

const NAVIGATION_CONFIRMATION_PHRASES = [
  "确认导航",
  "开始导航",
  "确认路线",
  "confirm navigation",
  "start navigation",
  "confirm route",
];

export function isNavigationConfirmationText(text: string): boolean {
  const normalized = text.toLocaleLowerCase().replace(/\s+/g, " ").trim();
  return NAVIGATION_CONFIRMATION_PHRASES.some((phrase) => normalized.includes(phrase));
}

export function runLifecycle(payload: LifecycleRequest): Promise<ScenarioResponse> {
  return postJson<LifecycleRequest, ScenarioResponse>(
    "/api/scenarios/smart-ev-cockpit/lifecycle/run",
    payload,
  );
}

export async function executeScenarioStep(
  payload: UtteranceRequest,
): Promise<ScenarioResponse> {
  if (payload.act_key === "Act 9") {
    const confirmNavigation = isNavigationConfirmationText(payload.text);
    return createVehicleEvent({
      soc: 9,
      range_km: 42,
      text: payload.text,
      ...(confirmNavigation ? { confirm_navigation: true } : {}),
    });
  }
  if (payload.act_key === "Act 10") {
    return runLifecycle({ current_day: 90, text: payload.text });
  }
  return createUtterance(payload);
}

export function getChatHistory(
  request: ChatHistoryRequest,
): Promise<ChatHistoryResponse> {
  const params = new URLSearchParams({ session_id: request.session_id });
  if (request.actor_id) {
    params.set("actor_id", request.actor_id);
  }
  if (request.user_id) {
    params.set("user_id", request.user_id);
  }
  if (request.limit) {
    params.set("limit", String(request.limit));
  }
  return getJson<ChatHistoryResponse>(
    `/api/scenarios/smart-ev-cockpit/chat-history?${params.toString()}`,
  );
}

export function exportTrace(): Promise<Record<string, unknown>> {
  return getJson<Record<string, unknown>>("/api/scenarios/smart-ev-cockpit/export");
}

export function generateTestData(
  payload: GenerateTestDataRequest,
): Promise<TestDataStatus> {
  return postJson<GenerateTestDataRequest, TestDataStatus>(
    "/api/scenarios/smart-ev-cockpit/test-data/generate",
    payload,
  );
}

export function importTestData(
  payload: ImportTestDataRequest,
): Promise<TestDataStatus> {
  return postJson<ImportTestDataRequest, TestDataStatus>(
    "/api/scenarios/smart-ev-cockpit/test-data/import",
    payload,
  );
}

export function getTestDataStatus(): Promise<TestDataStatus> {
  return getJson<TestDataStatus>("/api/scenarios/smart-ev-cockpit/test-data/status");
}

export function clearAllTestData(
  payload: DeleteTestDataRequest,
): Promise<TestDataStatus> {
  return deleteJson<DeleteTestDataRequest, TestDataStatus>(
    "/api/scenarios/smart-ev-cockpit/test-data/all",
    payload,
  );
}

export function getUserIdentities(): Promise<UserIdentitiesResponse> {
  return getJson<UserIdentitiesResponse>(
    "/api/scenarios/smart-ev-cockpit/identities",
  );
}

export function updateUserIdentity(
  actorId: string,
  payload: UpdateUserIdentityRequest,
): Promise<{ identity: UserIdentitiesResponse["identities"][number] }> {
  return putJson<UpdateUserIdentityRequest, { identity: UserIdentitiesResponse["identities"][number] }>(
    `/api/scenarios/smart-ev-cockpit/identities/${actorId}`,
    payload,
  );
}

export function getUserProfile(actorId: string): Promise<UserProfileResponse> {
  return getJson<UserProfileResponse>(
    `/api/scenarios/smart-ev-cockpit/profiles/${actorId}`,
  );
}

export function deleteTestDataset(
  datasetId: string,
  payload: DeleteTestDataRequest,
): Promise<TestDataStatus> {
  return deleteJson<DeleteTestDataRequest, TestDataStatus>(
    `/api/scenarios/smart-ev-cockpit/test-data/${datasetId}`,
    payload,
  );
}
