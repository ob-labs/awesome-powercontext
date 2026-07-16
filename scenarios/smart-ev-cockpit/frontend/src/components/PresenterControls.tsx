import { Download, RotateCcw, StepForward, Undo2 } from "lucide-react";

import type { TestDataStatus } from "../types/api";
import { TestDataPanel } from "./TestDataPanel";

interface PresenterControlsProps {
  canReplay: boolean;
  isExportingTrace: boolean;
  presenterStatus: string | null;
  onResetDemo: () => void;
  onReplayDemo: () => void;
  onNextScenario: () => void;
  onExportTrace: () => void;
  testDataStatus: TestDataStatus | null;
  testDataBusy: boolean;
  testDataError: string | null;
  onGenerateTestData: (count: number) => void;
  onClearTestData: () => void;
}

export function PresenterControls({
  canReplay,
  isExportingTrace,
  presenterStatus,
  onResetDemo,
  onReplayDemo,
  onNextScenario,
  onExportTrace,
  testDataStatus,
  testDataBusy,
  testDataError,
  onGenerateTestData,
  onClearTestData,
}: PresenterControlsProps) {
  return (
    <div className="presenter-stack">
      <div className="presenter-controls" aria-label="Presenter controls">
        <button type="button" onClick={onResetDemo}>
          <RotateCcw aria-hidden="true" strokeWidth={1.8} />
          Reset
        </button>
        <button type="button" onClick={onReplayDemo} disabled={!canReplay}>
          <Undo2 aria-hidden="true" strokeWidth={1.8} />
          Replay
        </button>
        <button type="button" onClick={onNextScenario}>
          <StepForward aria-hidden="true" strokeWidth={1.8} />
          Next
        </button>
        <button type="button" onClick={onExportTrace} disabled={isExportingTrace}>
          <Download aria-hidden="true" strokeWidth={1.8} />
          {isExportingTrace ? "Exporting" : "Export"}
        </button>
      </div>
      {presenterStatus ? (
        <p className="presenter-controls__status" aria-live="polite">
          {presenterStatus}
        </p>
      ) : null}
      <TestDataPanel
        status={testDataStatus}
        isBusy={testDataBusy}
        error={testDataError}
        onGenerate={onGenerateTestData}
        onClear={onClearTestData}
      />
    </div>
  );
}
