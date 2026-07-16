import type { ScenarioMemoryHit } from "../types/api";

interface MemoryCardProps {
  memory: ScenarioMemoryHit;
}

export function MemoryCard({ memory }: MemoryCardProps) {
  const meta = [
    memory.memory_id,
    memory.memory_kind,
    memory.visibility,
    memory.lifecycle_status,
    typeof memory.score === "number" ? memory.score.toFixed(2) : null,
  ].filter(Boolean);

  return (
    <article className="memory-card">
      <div className="memory-card__meta">
        {meta.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
      <p>{memory.content ?? "No content returned"}</p>
    </article>
  );
}
