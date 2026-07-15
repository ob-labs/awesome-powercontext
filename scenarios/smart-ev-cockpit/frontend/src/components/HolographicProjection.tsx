import type { ProjectionScene } from "../view-models/projection";
import { ProjectionMap } from "./ProjectionMap";
import { APP_COPY } from "../i18n";

interface HolographicProjectionProps {
  projection: ProjectionScene;
  ariaLabel?: string;
}

export function HolographicProjection({
  projection,
  ariaLabel = APP_COPY.en.cockpit.projectionLabel,
}: HolographicProjectionProps) {
  return (
    <section
      key={projection.id}
      className={`holographic-projection holographic-projection--${projection.status} holographic-projection--${projection.mode}`}
      data-projection-mode={projection.mode}
      aria-label={ariaLabel}
      aria-live="polite"
    >
      <div className="holographic-projection__beam" aria-hidden="true" />
      <div className="holographic-projection__panel">
        <div className="holographic-projection__content">
          <div className="holographic-projection__copy">
            <span className="holographic-projection__kicker">
              {projection.dockLabel}
            </span>
            <h2>{projection.title}</h2>
            <p
              className={
                projection.mode === "chat"
                  ? "holographic-projection__reply"
                  : undefined
              }
            >
              {projection.subtitle}
            </p>
            <div className="holographic-projection__chips">
              {projection.chips.map((chip) => (
                <span key={`${chip.label}-${chip.value}`}>
                  <strong>{chip.label}</strong>
                  {chip.value}
                </span>
              ))}
            </div>
          </div>
          {projection.storySteps?.length ? (
            <div
              className="holographic-projection__story"
              aria-label={projection.routeReadout}
            >
              {projection.storySteps.map((step) => (
                <article key={`${step.label}-${step.value}`}>
                  <span>{step.label}</span>
                  <strong>{step.value}</strong>
                  <p>{step.detail}</p>
                </article>
              ))}
            </div>
          ) : projection.showMap ? (
            <ProjectionMap
              label={projection.mapLabel}
              readout={projection.routeReadout}
              status={projection.status}
            />
          ) : (
            <div
              className="holographic-projection__assistant-status"
              aria-label={projection.routeReadout}
            >
              <span>{projection.routeReadout}</span>
              <strong>{projection.scoreLabel}</strong>
              <i aria-hidden="true" />
              <i aria-hidden="true" />
              <i aria-hidden="true" />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
