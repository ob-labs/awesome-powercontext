import { APP_COPY } from "../i18n";
import type { VehicleStateDiff } from "../types/api";

interface VehicleStatePanelProps {
  diff?: VehicleStateDiff[];
  state?: Record<string, unknown>;
  labels?: typeof APP_COPY.en.evidencePanels.vehicleState;
}

function formatValue(value: unknown) {
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return JSON.stringify(value);
}

export function VehicleStatePanel({
  diff = [],
  state,
  labels = APP_COPY.en.evidencePanels.vehicleState,
}: VehicleStatePanelProps) {
  const hasDiff = diff.length > 0;

  return (
    <section className="panel">
      <h2>{labels.title}</h2>
      {state ? (
        <div className="vehicle-state-grid" aria-label={labels.summaryLabel}>
          {Object.entries(state)
            .slice(0, 4)
            .map(([key, value]) => (
              <span className="status-chip" key={key}>
                {key}: {formatValue(value)}
              </span>
            ))}
        </div>
      ) : null}
      {hasDiff ? (
        <div className="vehicle-diff-list">
          {diff.map((item) => (
            <article className="vehicle-diff" key={item.field}>
              <strong>{item.field}</strong>
              <span>{formatValue(item.before)}</span>
              <span>{formatValue(item.after)}</span>
            </article>
          ))}
        </div>
      ) : (
        <p>{labels.empty}</p>
      )}
    </section>
  );
}
