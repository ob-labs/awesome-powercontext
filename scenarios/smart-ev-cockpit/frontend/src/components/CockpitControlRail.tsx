import type { ReactNode } from "react";

interface CockpitControlRailProps {
  title: string;
  meta: string;
  presenter: ReactNode;
  dialogue: ReactNode;
}

export function CockpitControlRail({
  title,
  meta,
  presenter,
  dialogue,
}: CockpitControlRailProps) {
  return (
    <section className="cockpit-control-rail" aria-label="Cockpit controls">
      <div className="cockpit-control-rail__header">
        <div>
          <h1>{title}</h1>
          <span>{meta}</span>
        </div>
        {presenter}
      </div>
      <div className="cockpit-control-rail__dialogue">{dialogue}</div>
    </section>
  );
}
