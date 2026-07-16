import { APP_COPY } from "../i18n";

interface PrivacyStripProps {
  labels?: typeof APP_COPY.en.evidencePanels.privacy;
}

export function PrivacyStrip({
  labels = APP_COPY.en.evidencePanels.privacy,
}: PrivacyStripProps) {
  return (
    <section className="privacy-strip" aria-label={labels.ariaLabel}>
      {labels.text}
    </section>
  );
}
