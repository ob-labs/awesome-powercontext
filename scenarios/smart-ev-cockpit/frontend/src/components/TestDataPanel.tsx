import { useState } from "react";
import { Database, Trash2 } from "lucide-react";

import { APP_COPY, type TestDataPanelLabels } from "../i18n";
import type { TestDataStatus } from "../types/api";

interface TestDataPanelProps {
  status: TestDataStatus | null;
  isBusy: boolean;
  error: string | null;
  labels?: TestDataPanelLabels;
  onGenerate: (count: number) => void;
  onClear: () => void;
}

const DEFAULT_GENERATION_COUNT = 1200;
const MIN_GENERATION_COUNT = 1;
const MAX_GENERATION_COUNT = 10000;

export function TestDataPanel({
  status,
  isBusy,
  error,
  labels = APP_COPY.en.testData,
  onGenerate,
  onClear,
}: TestDataPanelProps) {
  const [generationCountInput, setGenerationCountInput] = useState(
    String(DEFAULT_GENERATION_COUNT),
  );
  const generationCount = resolveGenerationCount(generationCountInput);
  const datasetId = status?.dataset_id ?? null;
  const generatedCount = status?.generated_count ?? 0;
  const importedCount = status?.imported_count ?? 0;
  const deletedCount = status?.deleted_count ?? 0;
  const skippedCount = status?.skipped_count ?? 0;
  const failedCount = status?.failed_count ?? 0;
  const isImporting = status?.state === "importing";
  const operationBusy = isBusy || isImporting || status?.state === "deleting";

  return (
    <section className="test-data-panel" aria-label={labels.controlsLabel}>
      <div className="test-data-panel__actions">
        <input
          type="number"
          className="test-data-panel__count-input"
          aria-label={labels.countAria}
          min={MIN_GENERATION_COUNT}
          max={MAX_GENERATION_COUNT}
          step={1}
          inputMode="numeric"
          value={generationCountInput}
          onChange={(event) => setGenerationCountInput(event.currentTarget.value)}
          onBlur={() => setGenerationCountInput(String(generationCount))}
          disabled={operationBusy}
        />
        <button
          type="button"
          aria-label={labels.generateAria(generationCount)}
          onClick={() => onGenerate(generationCount)}
          disabled={operationBusy}
        >
          <Database aria-hidden="true" strokeWidth={1.8} />
          {labels.generate}
        </button>
        <button
          type="button"
          className="danger-command"
          aria-label={labels.clearAria}
          onClick={onClear}
          disabled={operationBusy}
        >
          <Trash2 aria-hidden="true" strokeWidth={1.8} />
          {labels.clear}
        </button>
      </div>
      <div className="test-data-panel__status" aria-live="polite">
        <span className="status-chip">
          {labels.stateLabels[status?.state ?? "idle"]}
        </span>
        {datasetId ? <code>{datasetId}</code> : <span>{labels.noDataset}</span>}
        {generatedCount > 0 ? <span>{labels.generated(generatedCount)}</span> : null}
        {isImporting && generatedCount > 0 ? (
          <span>{labels.importing(importedCount, generatedCount)}</span>
        ) : null}
        {!isImporting && importedCount > 0 ? (
          <span>{labels.imported(importedCount)}</span>
        ) : null}
        {skippedCount > 0 ? <span>{labels.skipped(skippedCount)}</span> : null}
        {deletedCount > 0 ? <span>{labels.deleted(deletedCount)}</span> : null}
        {failedCount > 0 ? <span>{labels.failed(failedCount)}</span> : null}
      </div>
      {error || status?.last_error ? (
        <p className="test-data-panel__error" role="alert">
          {error ?? status?.last_error}
        </p>
      ) : null}
    </section>
  );
}

function resolveGenerationCount(value: string): number {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) {
    return DEFAULT_GENERATION_COUNT;
  }
  return Math.min(MAX_GENERATION_COUNT, Math.max(MIN_GENERATION_COUNT, parsed));
}
