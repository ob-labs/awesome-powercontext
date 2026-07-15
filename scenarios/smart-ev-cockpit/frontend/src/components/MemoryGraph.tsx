import type { ScenarioMemoryHit } from "../types/api";
import { APP_COPY } from "../i18n";

interface MemoryGraphProps {
  selectedMemoryIds?: string[];
  memoryHits?: ScenarioMemoryHit[];
  labels?: typeof APP_COPY.en.evidencePanels.memoryGraph;
}

export function MemoryGraph({
  selectedMemoryIds = [],
  memoryHits = [],
  labels = APP_COPY.en.evidencePanels.memoryGraph,
}: MemoryGraphProps) {
  const nodes = selectedMemoryIds.map((memoryId) => {
    const hit = memoryHits.find((item) => item.memory_id === memoryId);
    const kind = hit?.memory_kind ?? "memory";
    return `${kind}:${memoryId}`;
  });

  return (
    <section className="panel compact-panel">
      <h2>{labels.title}</h2>
      {nodes.length === 0 ? (
        <p>{labels.empty}</p>
      ) : (
        <div className="node-grid" aria-label={labels.groupLabel}>
          {nodes.map((node) => (
            <span className="node-chip" key={node}>
              {node}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
