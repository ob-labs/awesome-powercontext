export interface TraceOperation {
  type: string;
  query?: string;
  filters?: Record<string, unknown>;
  hit_count?: number;
}
