import { APP_COPY } from "../i18n";

interface CockpitStatusBandProps {
  labels?: typeof APP_COPY.en.evidencePanels.cockpitStatus;
}

export function CockpitStatusBand({
  labels = APP_COPY.en.evidencePanels.cockpitStatus,
}: CockpitStatusBandProps) {
  return (
    <section className="cockpit-band" aria-label={labels.ariaLabel}>
      <strong>{labels.live}</strong>
      <span className="status-chip">powercontext_builtin</span>
      <span className="status-chip">{labels.vehicle}</span>
      <span className="status-chip">{labels.soc}</span>
      <span className="status-chip">{labels.inside}</span>
      <span className="status-chip">{labels.comfort}</span>
    </section>
  );
}
