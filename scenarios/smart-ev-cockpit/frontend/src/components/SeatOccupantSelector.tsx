import { Settings } from "lucide-react";

import { APP_COPY, type SeatOccupantLabels } from "../i18n";
import type { ActorId, SeatPosition, UserIdentity } from "../types/api";

const SEAT_OCCUPANTS: Array<{
  actorId: ActorId;
  seatPosition: SeatPosition;
  className: string;
}> = [
  {
    actorId: "driver_primary",
    seatPosition: "front_left",
    className: "seat-occupant--driver",
  },
  {
    actorId: "passenger_front",
    seatPosition: "front_right",
    className: "seat-occupant--passenger",
  },
  {
    actorId: "child_rear_left",
    seatPosition: "rear_left",
    className: "seat-occupant--child",
  },
];

interface SeatOccupantSelectorProps {
  selectedActorId: ActorId;
  identities?: UserIdentity[];
  labels?: SeatOccupantLabels;
  onSelect: (actorId: ActorId, seatPosition: SeatPosition) => void;
  onOpenSettings?: (actorId: ActorId, seatPosition: SeatPosition) => void;
}

export function SeatOccupantSelector({
  selectedActorId,
  identities = [],
  labels = APP_COPY.en.seats,
  onSelect,
  onOpenSettings,
}: SeatOccupantSelectorProps) {
  return (
    <section className="seat-occupant-selector" aria-label={labels.selectorLabel}>
      {SEAT_OCCUPANTS.map((occupant) => {
        const actorLabel = labels.actors[occupant.actorId];
        const identity = identities.find(
          (item) => item.actor_id === occupant.actorId,
        );
        return (
          <div
            className={`seat-occupant-anchor ${occupant.className}`}
            key={occupant.actorId}
          >
            <button
              type="button"
              className="seat-occupant"
              aria-pressed={occupant.actorId === selectedActorId}
              onClick={() => onSelect(occupant.actorId, occupant.seatPosition)}
            >
              <span className="seat-occupant__figure" aria-hidden="true">
                <i />
              </span>
              <span>{actorLabel}</span>
              {identity ? <small aria-hidden="true">{identity.user_id}</small> : null}
            </button>
            {onOpenSettings ? (
              <button
                type="button"
                className="seat-occupant__settings"
                aria-label={labels.settingsLabel(actorLabel)}
                onClick={() => onOpenSettings(occupant.actorId, occupant.seatPosition)}
              >
                <Settings aria-hidden="true" strokeWidth={1.8} />
              </button>
            ) : null}
          </div>
        );
      })}
    </section>
  );
}
