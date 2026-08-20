export type ActorId = "driver_primary" | "passenger_front" | "child_rear_left";
export type SeatPosition = "front_left" | "front_right" | "rear_left";

export type ActKey =
  | "Act 1"
  | "Act 2"
  | "Act 3"
  | "Act 4"
  | "Act 5"
  | "Act 6"
  | "Act 7"
  | "Act 8"
  | "Act 9"
  | "Act 10"
  | "Chat";

export interface TraceOperation {
  type: string;
  query?: string;
  filters?: Record<string, unknown>;
  hit_count?: number;
  memory_ids?: string[];
  result?: string;
  before_status?: string;
  after_status?: string;
}

export interface ScenarioMemoryHit {
  memory_id: string;
  content?: string;
  memory_kind?: string;
  visibility?: string;
  lifecycle_status?: string;
  actor_id?: string;
  source_event_ids?: string[];
  hidden_fields?: string[];
  score?: number;
  [key: string]: unknown;
}

export interface ScenarioRecommendation {
  type?: string;
  title?: string;
  summary?: string;
  action_policy?: string;
  label?: string;
  reason_code?: string;
  reason_codes?: string[];
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface VehicleStateDiff {
  field: string;
  before: unknown;
  after: unknown;
}

export interface UtteranceRequest {
  act_key?: ActKey;
  actor_id: ActorId;
  user_id?: string;
  seat_position: SeatPosition;
  text: string;
  session_id: string;
  vehicle_context?: {
    hvac_target_temp_c: number;
  };
}

export interface VehicleEventRequest {
  soc: number;
  range_km: number;
  text?: string;
  confirm_navigation?: boolean;
}

export interface LifecycleRequest {
  current_day: number;
  text?: string;
}

export interface ChatHistoryRequest {
  session_id: string;
  actor_id?: ActorId;
  user_id?: string;
  limit?: number;
}

export interface ChatHistoryMessage {
  id: string;
  session_id: string;
  actor_id: ActorId;
  user_id: string;
  seat_position: SeatPosition;
  role: "user" | "assistant";
  text: string;
  trace_id?: string | null;
  created_at: string;
}

export interface ChatHistoryResponse {
  messages: ChatHistoryMessage[];
}

export interface ScenarioLifecycle {
  current_day?: number;
  plan?: TraceOperation[];
  completed_operations?: TraceOperation[];
  failed_operation?: TraceOperation | null;
  audit?: TraceOperation[];
  trace_id?: string;
}

export interface ScenarioResponse {
  act_key?: ActKey;
  assistant_reply: string;
  trace_id: string;
  live_backend: string;
  powercontext_connected: boolean;
  data_source?: string;
  operations: TraceOperation[];
  memory_hits: ScenarioMemoryHit[];
  selected_memory_ids?: string[];
  vehicle_state: Record<string, unknown>;
  vehicle_state_diff: VehicleStateDiff[];
  privacy_report: Record<string, unknown>;
  recommendations: ScenarioRecommendation[];
  evidence: Record<string, unknown>;
  lifecycle?: ScenarioLifecycle;
  redacted_input?: string;
}

export type TestDataState =
  | "idle"
  | "generated"
  | "importing"
  | "imported"
  | "deleting"
  | "deleted"
  | "failed";

export interface TestDataStatus {
  state: TestDataState;
  dataset_id: string | null;
  dataset_path?: string | null;
  locale: "en" | "zh";
  generated_count: number;
  imported_count: number;
  deleted_count: number;
  skipped_count: number;
  failed_count: number;
  last_error: string | null;
}

export interface GenerateTestDataRequest {
  count?: number;
  seed?: number;
  locale?: "en" | "zh";
}

export interface ImportTestDataRequest {
  dataset_id: string;
  apply: boolean;
  limit?: number | null;
  max_workers?: number;
}

export interface DeleteTestDataRequest {
  apply: boolean;
}

export interface UserIdentity {
  actor_id: ActorId;
  seat_position: SeatPosition;
  user_id: string;
  display_name: string;
  profile_note: string;
  updated_at: string;
}

export interface UserIdentitiesResponse {
  identities: UserIdentity[];
}

export interface UpdateUserIdentityRequest {
  user_id: string;
  display_name?: string;
  profile_note?: string;
}

export interface UserProfileMemory {
  memory_id: string;
  content: string;
  metadata: {
    actor_id?: string | null;
    seat_position?: string | null;
    memory_kind: string;
    memory_dimension?: string[];
    [key: string]: unknown;
  };
}

export interface UserProfileSummary {
  identity: UserIdentity;
  primary_memory: string | null;
  memory_kind_counts: Record<string, number>;
  memories: UserProfileMemory[];
}

export interface UserProfileResponse {
  profile: UserProfileSummary;
}
