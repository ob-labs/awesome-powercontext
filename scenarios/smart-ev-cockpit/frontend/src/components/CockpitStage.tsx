import type { ReactNode } from "react";

import cockpitImage from "../assets/smart-ev-cockpit-bg.png";
import { APP_COPY, type CockpitStageLabels } from "../i18n";
import type { PetCompanionState } from "../view-models/petCompanion";
import type { ProjectionScene, ScenarioStep } from "../view-models/projection";
import type { InteriorTheme } from "./InteriorTrimSelector";
import { InfotainmentDisplay } from "./InfotainmentDisplay";
import { PetCompanion } from "./PetCompanion";

interface CockpitStageProps {
  steps: ScenarioStep[];
  activeIndex: number;
  projection: ProjectionScene;
  petState?: PetCompanionState;
  onSelectScenario: (index: number) => void;
  interiorTheme?: InteriorTheme;
  labels?: CockpitStageLabels;
  children?: ReactNode;
}

export function CockpitStage({
  steps,
  activeIndex,
  projection,
  petState,
  onSelectScenario,
  interiorTheme = "ivory",
  labels = APP_COPY.en.cockpit,
  children,
}: CockpitStageProps) {
  const activeStep = steps[activeIndex];

  return (
    <section
      className="cockpit-stage"
      aria-label={labels.stageLabel}
      data-interior={interiorTheme}
      data-pet-anchor={petState?.anchor}
      data-pet-origin-anchor={petState?.originAnchor}
      data-pet-target={petState?.target}
    >
      <img
        className="cockpit-stage__image"
        src={cockpitImage}
        alt={labels.imageAlt}
        data-interior-filter={interiorTheme}
      />
      <div
        className="cockpit-stage__material-tint"
        data-interior={interiorTheme}
        data-testid="cockpit-material-tint"
        aria-hidden="true"
      />
      <div className="cockpit-stage__floor-shadow" aria-hidden="true" />
      <div className="cockpit-stage__scene-hint" aria-hidden="true">
        <i />
        <span>
          {activeStep ? `${activeStep.day} / ${activeStep.act}` : labels.sceneFocus}
        </span>
      </div>
      <InfotainmentDisplay
        steps={steps}
        activeIndex={activeIndex}
        projection={projection}
        petFocusTarget={petState?.target}
        labels={labels.infotainment}
        onSelectScenario={onSelectScenario}
      />
      {petState ? <PetCompanion state={petState} /> : null}
      {children ? <div className="cockpit-stage__controls">{children}</div> : null}
    </section>
  );
}
