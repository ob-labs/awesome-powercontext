import { APP_COPY } from "../i18n";

interface ScenarioTimelineStep {
  day: string;
  act: string;
}

interface ScenarioTimelineProps {
  steps: ScenarioTimelineStep[];
  activeIndex: number;
  labels?: typeof APP_COPY.en.evidencePanels.scenarioTimeline;
  onSelect: (index: number) => void;
}

export function ScenarioTimeline({
  steps,
  activeIndex,
  labels = APP_COPY.en.evidencePanels.scenarioTimeline,
  onSelect,
}: ScenarioTimelineProps) {
  return (
    <nav className="scenario-timeline" aria-label={labels.ariaLabel}>
      {steps.map((step, index) => (
        <button
          type="button"
          key={step.day}
          aria-current={index === activeIndex ? "step" : undefined}
          onClick={() => onSelect(index)}
        >
          {step.day}
        </button>
      ))}
    </nav>
  );
}
