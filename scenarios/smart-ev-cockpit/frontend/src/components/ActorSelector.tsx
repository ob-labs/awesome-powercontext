import type { ActorId, SeatPosition } from "../types/api";

const ACTORS: Array<{
  label: string;
  actorId: ActorId;
  seatPosition: SeatPosition;
}> = [
  { label: "Driver", actorId: "driver_primary", seatPosition: "front_left" },
  { label: "Passenger", actorId: "passenger_front", seatPosition: "front_right" },
  { label: "Child", actorId: "child_rear_left", seatPosition: "rear_left" },
];

interface ActorSelectorProps {
  selectedActorId: ActorId;
  onSelect: (actorId: ActorId, seatPosition: SeatPosition) => void;
}

export function ActorSelector({ selectedActorId, onSelect }: ActorSelectorProps) {
  return (
    <div className="actor-selector" aria-label="Actor selector">
      {ACTORS.map((actor) => (
        <button
          type="button"
          key={actor.actorId}
          aria-pressed={actor.actorId === selectedActorId}
          onClick={() => onSelect(actor.actorId, actor.seatPosition)}
        >
          {actor.label}
        </button>
      ))}
    </div>
  );
}
