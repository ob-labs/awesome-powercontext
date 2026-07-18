import type { TraceOperation } from "../types/api";

const MUTATION_TYPES = ["ADD", "UPDATE", "DELETE"] as const;

export function describeChatSource(operations: TraceOperation[]): string {
  const types = new Set(operations.map((operation) => operation.type.toUpperCase()));
  const mutation = MUTATION_TYPES.find((type) => types.has(type));
  if (mutation) {
    return `PowerMem ${mutation} + LLM`;
  }
  if (types.has("SEARCH")) {
    return "PowerMem SEARCH + LLM";
  }
  return "LLM";
}
