import type { ReactNode } from "react";

import { APP_COPY } from "../i18n";

interface MemoryFlowPanelProps {
  children: ReactNode;
  isEmpty?: boolean;
  labels?: typeof APP_COPY.en.evidencePanels.memoryFlow;
}

export function MemoryFlowPanel({
  children,
  isEmpty = false,
  labels = APP_COPY.en.evidencePanels.memoryFlow,
}: MemoryFlowPanelProps) {
  return (
    <section className="panel">
      <h2>{labels.title}</h2>
      <div className="memory-flow-stack">{children}</div>
      {isEmpty ? <p className="empty-state">{labels.empty}</p> : null}
    </section>
  );
}
