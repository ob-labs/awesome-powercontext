import { Download } from "lucide-react";

import { APP_COPY } from "../i18n";

interface DeveloperEvidenceDrawerProps {
  response: {
    trace_id: string;
    live_backend: string;
    powermem_connected: boolean;
    evidence: Record<string, unknown>;
  };
  onExportTrace?: () => void;
  labels?: typeof APP_COPY.en.evidencePanels.developerEvidence;
}

function formatEvidence(value: unknown, noEvidence: string) {
  if (value === undefined) {
    return noEvidence;
  }

  return JSON.stringify(value, null, 2);
}

export function DeveloperEvidenceDrawer({
  response,
  onExportTrace,
  labels = APP_COPY.en.evidencePanels.developerEvidence,
}: DeveloperEvidenceDrawerProps) {
  return (
    <aside className="panel evidence-drawer" aria-label={labels.drawerLabel}>
      <header className="panel-header">
        <div>
          <h2>{labels.title}</h2>
          <span className="panel-header__meta">{response.trace_id}</span>
        </div>
        <button
          className="icon-command"
          type="button"
          onClick={onExportTrace}
          disabled={!onExportTrace}
        >
          <Download aria-hidden="true" strokeWidth={1.8} />
          {labels.exportTrace}
        </button>
      </header>
      <div className="evidence-status" aria-label={labels.backendStatusLabel}>
        <span>{response.powermem_connected ? labels.live : labels.disconnected}</span>
        <span>{response.live_backend}</span>
      </div>
      <div className="evidence-steps">
        {labels.steps.map(([key, label]) => (
          <section className="evidence-step" key={key}>
            <h3>{label}</h3>
            <pre>{formatEvidence(response.evidence[key], labels.noEvidence)}</pre>
          </section>
        ))}
      </div>
    </aside>
  );
}
