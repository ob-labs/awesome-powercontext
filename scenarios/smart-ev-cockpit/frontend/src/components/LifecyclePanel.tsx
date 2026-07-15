import type { ScenarioLifecycle, TraceOperation } from "../types/api";
import { APP_COPY } from "../i18n";

interface LifecyclePanelProps {
  lifecycle?: ScenarioLifecycle | null;
  operations?: TraceOperation[];
  labels?: typeof APP_COPY.en.evidencePanels.lifecycle;
}

function lifecycleRows(
  lifecycle?: ScenarioLifecycle | null,
  operations: TraceOperation[] = [],
): TraceOperation[] {
  if (lifecycle?.completed_operations?.length) {
    return lifecycle.completed_operations;
  }
  if (lifecycle?.audit?.length) {
    return lifecycle.audit;
  }
  return operations.filter((operation) =>
    ["UPDATE", "DELETE"].includes(operation.type.toUpperCase()),
  );
}

export function LifecyclePanel({
  lifecycle,
  operations = [],
  labels = APP_COPY.en.evidencePanels.lifecycle,
}: LifecyclePanelProps) {
  const rows = lifecycleRows(lifecycle, operations);

  return (
    <section className="lifecycle-strip" aria-label={labels.ariaLabel}>
      {rows.length === 0 ? (
        <span className="lifecycle-stage">{labels.empty}</span>
      ) : (
        rows.map((row) => (
          <span className="lifecycle-stage" key={`${row.type}-${row.memory_ids?.[0]}`}>
            {row.type}
            {row.after_status ? `: ${row.after_status}` : ""}
            {row.result ? ` (${row.result})` : ""}
          </span>
        ))
      )}
    </section>
  );
}
