import type { ScenarioRecommendation } from "../types/api";
import { APP_COPY } from "../i18n";

interface RecommendationPanelProps {
  recommendations?: ScenarioRecommendation[];
  labels?: typeof APP_COPY.en.evidencePanels.recommendations;
}

export function RecommendationPanel({
  recommendations = [],
  labels = APP_COPY.en.evidencePanels.recommendations,
}: RecommendationPanelProps) {
  return (
    <section className="panel compact-panel">
      <h2>{labels.title}</h2>
      {recommendations.length === 0 ? (
        <p>{labels.empty}</p>
      ) : (
        <ul className="recommendation-list">
          {recommendations.map((item, index) => (
            <li key={`${item.title ?? item.label ?? "rec"}-${index}`}>
              <strong>{item.title ?? item.label}</strong>
              {item.summary ? <p>{item.summary}</p> : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
