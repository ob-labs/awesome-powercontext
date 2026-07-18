import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Download,
  Presentation,
  RotateCcw,
  StepForward,
  Undo2,
  X,
} from "lucide-react";

import {
  clearAllTestData,
  executeScenarioStep,
  exportTrace,
  generateTestData,
  getChatHistory,
  getUserIdentities,
  getUserProfile,
  getTestDataStatus,
  importTestData,
  isNavigationConfirmationText,
  updateUserIdentity,
} from "./api/smartEvCockpit";
import { AppShell } from "./components/AppShell";
import { CockpitStatusBand } from "./components/CockpitStatusBand";
import { CockpitStage } from "./components/CockpitStage";
import { DeveloperEvidenceDrawer } from "./components/DeveloperEvidenceDrawer";
import { DialoguePanel, type DialogueMessage } from "./components/DialoguePanel";
import {
  InteriorTrimSelector,
  type InteriorTheme,
} from "./components/InteriorTrimSelector";
import { LifecyclePanel } from "./components/LifecyclePanel";
import { MemoryCard } from "./components/MemoryCard";
import { MemoryFlowPanel } from "./components/MemoryFlowPanel";
import { MemoryGraph } from "./components/MemoryGraph";
import { PrivacyStrip } from "./components/PrivacyStrip";
import { RecommendationPanel } from "./components/RecommendationPanel";
import { ScenarioTimeline } from "./components/ScenarioTimeline";
import { SeatOccupantSelector } from "./components/SeatOccupantSelector";
import { TestDataPanel } from "./components/TestDataPanel";
import { UserIdentityPanel } from "./components/UserIdentityPanel";
import { VehicleStatePanel } from "./components/VehicleStatePanel";
import {
  APP_COPY,
  DEFAULT_LOCALE,
  SCENARIO_STEPS_BY_LOCALE,
  type Locale,
} from "./i18n";
import { describeChatSource } from "./view-models/chatSource";
import { buildPetCompanionState } from "./view-models/petCompanion";
import type {
  ActorId,
  ChatHistoryMessage,
  ScenarioResponse,
  SeatPosition,
  TestDataStatus,
  UserIdentity,
  UserProfileSummary,
} from "./types/api";
import { buildProjectionScene } from "./view-models/projection";

const DEFAULT_SCENARIO_INDEX = 0;
const DEFAULT_SCENARIO_STEPS = SCENARIO_STEPS_BY_LOCALE[DEFAULT_LOCALE];
const DEMO_SESSION_ID = "demo_session_001";
const PPT_DECK_SRC = "/powermem-smart-ev-cockpit-deck.html";
const EMPTY_UTTERANCE_DRAFTS: Record<ActorId, string> = {
  driver_primary: "",
  passenger_front: "",
  child_rear_left: "",
};

const DEFAULT_USER_IDENTITIES: UserIdentity[] = [
  {
    actor_id: "driver_primary",
    seat_position: "front_left",
    user_id: "driver_primary",
    display_name: "Driver",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
  {
    actor_id: "passenger_front",
    seat_position: "front_right",
    user_id: "passenger_front",
    display_name: "Passenger",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
  {
    actor_id: "child_rear_left",
    seat_position: "rear_left",
    user_id: "child_rear_left",
    display_name: "Child",
    profile_note: "",
    updated_at: "2026-07-10T00:00:00Z",
  },
];

function createUtteranceDrafts(actorId: ActorId, utterance: string): Record<ActorId, string> {
  return {
    ...EMPTY_UTTERANCE_DRAFTS,
    [actorId]: utterance,
  };
}

export default function App() {
  const [locale, setLocale] = useState<Locale>(DEFAULT_LOCALE);
  const [response, setResponse] = useState<ScenarioResponse | null>(null);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [selectedScenarioIndex, setSelectedScenarioIndex] =
    useState(DEFAULT_SCENARIO_INDEX);
  const [utteranceDrafts, setUtteranceDrafts] = useState<Record<ActorId, string>>(
    () =>
      createUtteranceDrafts(
        DEFAULT_SCENARIO_STEPS[DEFAULT_SCENARIO_INDEX].actorId,
        DEFAULT_SCENARIO_STEPS[DEFAULT_SCENARIO_INDEX].utterance,
      ),
  );
  const [selectedActorId, setSelectedActorId] = useState<ActorId>(
    DEFAULT_SCENARIO_STEPS[DEFAULT_SCENARIO_INDEX].actorId,
  );
  const [selectedSeatPosition, setSelectedSeatPosition] = useState<SeatPosition>(
    DEFAULT_SCENARIO_STEPS[DEFAULT_SCENARIO_INDEX].seatPosition,
  );
  const [lastSubmittedUtterance, setLastSubmittedUtterance] = useState<string | null>(
    null,
  );
  const [presenterStatus, setPresenterStatus] = useState<string | null>(null);
  const [isExportingTrace, setIsExportingTrace] = useState(false);
  const [testDataStatus, setTestDataStatus] = useState<TestDataStatus | null>(null);
  const [testDataBusy, setTestDataBusy] = useState(false);
  const [testDataError, setTestDataError] = useState<string | null>(null);
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);
  const [isDeckOpen, setIsDeckOpen] = useState(false);
  const [interiorTheme, setInteriorTheme] = useState<InteriorTheme>("ivory");
  const [chatMessages, setChatMessages] = useState<DialogueMessage[]>([]);
  const [userIdentities, setUserIdentities] = useState<UserIdentity[]>(
    DEFAULT_USER_IDENTITIES,
  );
  const [selectedUserProfile, setSelectedUserProfile] =
    useState<UserProfileSummary | null>(null);
  const [identityPanelActorId, setIdentityPanelActorId] = useState<ActorId | null>(
    null,
  );
  const [identitySaveBusy, setIdentitySaveBusy] = useState(false);
  const [identitySaveError, setIdentitySaveError] = useState<string | null>(null);
  const selectedActorRef = useRef(selectedActorId);
  const copy = APP_COPY[locale];
  const pptCopy =
    locale === "zh"
      ? {
          entry: "PowerMem PPT",
          openAria: "打开 PowerMem PPT",
          dialogAria: "PowerMem(汽车智能座舱记忆方案)",
          title: "PowerMem(汽车智能座舱记忆方案)",
          subtitle: "16 页 HTML PPT：PowerMem 能力、智能座舱价值与 demo 项目总览。",
          openInNew: "新窗口打开",
          close: "关闭",
        }
      : {
          entry: "PowerMem PPT",
          openAria: "Open PowerMem PPT",
          dialogAria: "PowerMem smart EV cockpit PPT",
          title: "PowerMem Smart EV Cockpit PPT",
          subtitle:
            "A 16-slide HTML deck covering PowerMem, cockpit capabilities, and this demo.",
          openInNew: "Open in new tab",
          close: "Close",
        };
  const scenarioSteps = SCENARIO_STEPS_BY_LOCALE[locale];
  const utteranceText = utteranceDrafts[selectedActorId] ?? "";
  const selectedIdentity =
    userIdentities.find((identity) => identity.actor_id === selectedActorId) ??
    DEFAULT_USER_IDENTITIES.find((identity) => identity.actor_id === selectedActorId) ??
    DEFAULT_USER_IDENTITIES[0];
  const selectedUserId = selectedIdentity.user_id;
  const identityPanelIdentity = identityPanelActorId
    ? userIdentities.find((identity) => identity.actor_id === identityPanelActorId) ??
      DEFAULT_USER_IDENTITIES.find(
        (identity) => identity.actor_id === identityPanelActorId,
      ) ??
      null
    : null;
  selectedActorRef.current = selectedActorId;

  useEffect(() => {
    void refreshTestDataStatus();
    void refreshUserIdentities();
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  }, [locale]);

  useEffect(() => {
    let isCancelled = false;
    const actorId = selectedActorId;
    const userId = selectedUserId;
    setChatMessages([]);
    void loadChatHistory(actorId, userId, (messages) => {
      if (!isCancelled && selectedActorRef.current === actorId) {
        setChatMessages(messages);
      }
    });
    void refreshUserProfile(actorId);
    return () => {
      isCancelled = true;
    };
  }, [selectedActorId, selectedUserId]);

  const testDataOperationActive =
    testDataStatus?.state === "importing" || testDataStatus?.state === "deleting";

  useEffect(() => {
    if (!testDataOperationActive) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void refreshTestDataStatus();
    }, 1000);
    return () => window.clearInterval(intervalId);
  }, [testDataOperationActive]);

  async function handleSubmit(text: string) {
    const submittedText = text.trim();
    if (!submittedText) {
      return;
    }

    setLiveError(null);
    setPresenterStatus(null);
    setLastSubmittedUtterance(submittedText);
    const submittedActorId = selectedActorId;
    const submittedUserId = selectedUserId;
    const submittedSeatPosition = selectedSeatPosition;
    setActorUtteranceDraft(submittedActorId, "");
    setChatMessages((current) =>
      appendChatMessages(current, {
        id: createChatMessageId("user", current.length),
        role: "user",
        text: submittedText,
        meta: copy.seats.actors[submittedActorId],
      }),
    );
    try {
      const currentStep = scenarioSteps[selectedScenarioIndex];
      const scriptedActKey = currentStep.actKey ?? currentStep.act;
      const isScriptedUtterance =
        submittedText === currentStep.utterance.trim();
      const isPendingAct9Confirmation =
        scriptedActKey === "Act 9" &&
        response?.act_key === "Act 9" &&
        response.recommendations.some(
          (recommendation) =>
            recommendation.type === "charging_safety" &&
            recommendation.action_policy === "confirm",
        ) &&
        isNavigationConfirmationText(submittedText);
      const result = normalizeScenarioResponse(await executeScenarioStep({
        ...(isScriptedUtterance || isPendingAct9Confirmation
          ? { act_key: scriptedActKey }
          : {}),
        ...(isScriptedUtterance && currentStep.initialHvacTargetTempC !== undefined
          ? {
              vehicle_context: {
                hvac_target_temp_c: currentStep.initialHvacTargetTempC,
              },
            }
          : {}),
        actor_id: submittedActorId,
        user_id: submittedUserId,
        seat_position: submittedSeatPosition,
        text: submittedText,
        session_id: DEMO_SESSION_ID,
      }));
      if (selectedActorRef.current !== submittedActorId) {
        return;
      }
      const chatSource = describeChatSource(result.operations);
      setResponse(result);
      setChatMessages((current) =>
        appendChatMessages(current, {
          id: result.trace_id
            ? `assistant-${result.trace_id}-${current.length}`
            : createChatMessageId("assistant", current.length),
          role: "assistant",
          text: result.assistant_reply,
          meta: chatSource,
        }),
      );
      await loadChatHistory(submittedActorId, submittedUserId, (messages) => {
        if (
          selectedActorRef.current === submittedActorId &&
          messages.length > 0 &&
          messages.some((message) => message.traceId === result.trace_id)
        ) {
          const messagesWithSource = messages.map((message) =>
            message.role === "assistant" && message.traceId === result.trace_id
              ? { ...message, meta: chatSource }
              : message,
          );
          setChatMessages(messagesWithSource);
        }
      });
      void refreshUserProfile(submittedActorId);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : copy.status.liveFallbackError;
      setResponse(null);
      setLiveError(errorMessage);
      setChatMessages((current) =>
        appendChatMessages(current, {
          id: createChatMessageId("assistant-error", current.length),
          role: "assistant",
          text: errorMessage,
          meta: copy.dialogue.assistantName,
        }),
      );
    }
  }

  function selectScenario(index: number, statusMessage?: string) {
    const nextStep = scenarioSteps[index];
    setSelectedScenarioIndex(index);
    setUtteranceDrafts(createUtteranceDrafts(nextStep.actorId, nextStep.utterance));
    setChatMessages([]);
    setSelectedActorId(nextStep.actorId);
    setSelectedSeatPosition(nextStep.seatPosition);
    setIdentityPanelActorId(null);
    setIdentitySaveError(null);
    setResponse(null);
    setLiveError(null);
    setPresenterStatus(statusMessage ?? copy.status.loaded(nextStep.day));
  }

  function selectActor(actorId: ActorId, seatPosition: SeatPosition) {
    setChatMessages([]);
    setSelectedActorId(actorId);
    setSelectedSeatPosition(seatPosition);
    setIdentityPanelActorId(null);
    setIdentitySaveError(null);
    setPresenterStatus(copy.status.actorSet(copy.seats.actors[actorId]));
  }

  function handleOpenIdentitySettings(actorId: ActorId, seatPosition: SeatPosition) {
    selectActor(actorId, seatPosition);
    setIdentityPanelActorId(actorId);
    setIdentitySaveError(null);
  }

  async function handleSaveIdentity(payload: {
    user_id: string;
    display_name?: string;
    profile_note?: string;
  }) {
    if (!identityPanelIdentity) {
      return;
    }

    setIdentitySaveBusy(true);
    setIdentitySaveError(null);
    try {
      const result = await updateUserIdentity(identityPanelIdentity.actor_id, payload);
      setUserIdentities((current) =>
        current.map((identity) =>
          identity.actor_id === result.identity.actor_id ? result.identity : identity,
        ),
      );
      setPresenterStatus(
        copy.identity.saved(result.identity.display_name, result.identity.user_id),
      );
      await refreshUserProfile(result.identity.actor_id);
    } catch (error) {
      setIdentitySaveError(
        error instanceof Error ? error.message : copy.identity.saveError,
      );
    } finally {
      setIdentitySaveBusy(false);
    }
  }

  function handleResetDemo() {
    setResponse(null);
    setLiveError(null);
    setLastSubmittedUtterance(null);
    selectScenario(DEFAULT_SCENARIO_INDEX, copy.status.reset);
  }

  function handleReplayDemo() {
    if (!lastSubmittedUtterance) {
      return;
    }
    setActorUtteranceDraft(selectedActorId, lastSubmittedUtterance);
    void handleSubmit(lastSubmittedUtterance);
  }

  function handleNextScenario() {
    const nextIndex = (selectedScenarioIndex + 1) % scenarioSteps.length;
    selectScenario(nextIndex);
  }

  async function handleExportTrace() {
    setIsExportingTrace(true);
    setPresenterStatus(null);
    try {
      const traceData = await exportTrace();
      downloadJson(traceData, "smart-ev-cockpit-trace.json");
      setPresenterStatus(copy.status.exportedTrace);
    } catch (error) {
      setPresenterStatus(
        error instanceof Error ? error.message : copy.status.traceExportFailed,
      );
    } finally {
      setIsExportingTrace(false);
    }
  }

  async function refreshTestDataStatus() {
    try {
      const status = await getTestDataStatus();
      setTestDataStatus(status);
    } catch {
      setTestDataStatus(null);
    }
  }

  async function refreshUserIdentities() {
    try {
      const result = await getUserIdentities();
      setUserIdentities(result.identities);
    } catch {
      setUserIdentities(DEFAULT_USER_IDENTITIES);
    }
  }

  async function refreshUserProfile(actorId: ActorId) {
    try {
      const result = await getUserProfile(actorId);
      if (selectedActorRef.current === actorId) {
        setSelectedUserProfile(result.profile);
      }
    } catch {
      if (selectedActorRef.current === actorId) {
        setSelectedUserProfile(null);
      }
    }
  }

  async function runTestDataAction(action: () => Promise<TestDataStatus>) {
    setTestDataBusy(true);
    setTestDataError(null);
    try {
      const status = await action();
      setTestDataStatus(status);
    } catch (error) {
      setTestDataError(
        error instanceof Error ? error.message : copy.status.testDataFallbackError,
      );
    } finally {
      setTestDataBusy(false);
    }
  }

  function handleGenerateTestData(count: number) {
    void runTestDataAction(async () => {
      const generatedStatus = await generateTestData({ count, seed: 42, locale });
      setTestDataStatus(generatedStatus);
      const datasetId = generatedStatus.dataset_id;
      if (!datasetId) {
        throw new Error(copy.status.testDataFallbackError);
      }
      return importTestData({
        dataset_id: datasetId,
        apply: true,
        max_workers: 3,
      });
    });
  }

  function handleClearTestData() {
    void runTestDataAction(() => clearAllTestData({ apply: true }));
  }

  function handleLocaleChange(nextLocale: Locale) {
    if (nextLocale === locale) {
      return;
    }

    const nextSteps = SCENARIO_STEPS_BY_LOCALE[nextLocale];
    const nextStep = nextSteps[selectedScenarioIndex] ?? nextSteps[DEFAULT_SCENARIO_INDEX];
    setLocale(nextLocale);
    setUtteranceDrafts(createUtteranceDrafts(nextStep.actorId, nextStep.utterance));
    setSelectedActorId(nextStep.actorId);
    setSelectedSeatPosition(nextStep.seatPosition);
    setIdentityPanelActorId(null);
    setIdentitySaveError(null);
    setResponse(null);
    setLiveError(null);
    setLastSubmittedUtterance(null);
    setPresenterStatus(null);
  }

  function setActorUtteranceDraft(actorId: ActorId, text: string) {
    setUtteranceDrafts((current) => ({
      ...current,
      [actorId]: text,
    }));
  }

  const activeStep = scenarioSteps[selectedScenarioIndex];
  const projection = useMemo(
    () =>
      buildProjectionScene({
        step: activeStep,
        response,
        liveError,
        selectedActorId,
        selectedSeatPosition,
        locale,
      }),
    [activeStep, response, liveError, selectedActorId, selectedSeatPosition, locale],
  );
  const petState = useMemo(
    () =>
      buildPetCompanionState({
        step: activeStep,
        response,
        projection,
        liveError,
        selectedActorId,
        locale,
      }),
    [activeStep, response, projection, liveError, selectedActorId, locale],
  );

  return (
    <AppShell>
      <header className="top-data-bar" aria-label={copy.topDataBarLabel}>
        <TestDataPanel
          status={testDataStatus}
          isBusy={testDataBusy || testDataOperationActive}
          error={testDataError}
          labels={copy.testData}
          onGenerate={handleGenerateTestData}
          onClear={handleClearTestData}
        />
        <div className="top-data-bar__utility">
          <div className="language-switcher" aria-label={copy.language.label}>
            <button
              type="button"
              aria-pressed={locale === "en"}
              onClick={() => handleLocaleChange("en")}
            >
              {copy.language.english}
            </button>
            <button
              type="button"
              aria-pressed={locale === "zh"}
              onClick={() => handleLocaleChange("zh")}
            >
              {copy.language.chinese}
            </button>
          </div>
          <button
            type="button"
            className="evidence-entry__button evidence-entry__button--quiet"
            aria-label={copy.evidence.openAria}
            aria-haspopup="dialog"
            aria-expanded={isEvidenceOpen}
            onClick={() => setIsEvidenceOpen(true)}
          >
            <Activity aria-hidden="true" strokeWidth={1.8} />
            {copy.evidence.entry}
          </button>
          <button
            type="button"
            className="ppt-entry__button"
            aria-label={pptCopy.openAria}
            aria-haspopup="dialog"
            aria-expanded={isDeckOpen}
            onClick={() => {
              setIsEvidenceOpen(false);
              setIsDeckOpen(true);
            }}
          >
            <Presentation aria-hidden="true" strokeWidth={1.8} />
            {pptCopy.entry}
          </button>
        </div>
      </header>
      <CockpitStage
        steps={scenarioSteps}
        activeIndex={selectedScenarioIndex}
        projection={projection}
        petState={petState}
        onSelectScenario={selectScenario}
        interiorTheme={interiorTheme}
        labels={copy.cockpit}
      >
        <SeatOccupantSelector
          selectedActorId={selectedActorId}
          identities={userIdentities}
          labels={copy.seats}
          onSelect={selectActor}
          onOpenSettings={handleOpenIdentitySettings}
        />
        {identityPanelIdentity ? (
          <UserIdentityPanel
            identity={identityPanelIdentity}
            profile={selectedUserProfile}
            actorLabel={copy.seats.actors[identityPanelIdentity.actor_id]}
            labels={copy.identity}
            isSaving={identitySaveBusy}
            error={identitySaveError}
            onClose={() => {
              setIdentityPanelActorId(null);
              setIdentitySaveError(null);
            }}
            onSave={handleSaveIdentity}
          />
        ) : null}
        <InteriorTrimSelector
          selectedTheme={interiorTheme}
          labels={copy.interior}
          onSelect={setInteriorTheme}
        />
        <section className="manual-cockpit-keys" aria-label={copy.manual.ariaLabel}>
          <div className="manual-cockpit-keys__buttons">
            <button type="button" onClick={handleResetDemo}>
              <RotateCcw aria-hidden="true" strokeWidth={1.8} />
              {copy.manual.reset}
            </button>
            <button
              type="button"
              onClick={handleReplayDemo}
              disabled={!lastSubmittedUtterance}
            >
              <Undo2 aria-hidden="true" strokeWidth={1.8} />
              {copy.manual.replay}
            </button>
            <button type="button" onClick={handleNextScenario}>
              <StepForward aria-hidden="true" strokeWidth={1.8} />
              {copy.manual.next}
            </button>
            <button
              type="button"
              onClick={handleExportTrace}
              disabled={isExportingTrace}
            >
              <Download aria-hidden="true" strokeWidth={1.8} />
              {isExportingTrace ? copy.manual.exporting : copy.manual.export}
            </button>
          </div>
          {presenterStatus ? (
            <p className="manual-cockpit-keys__status" aria-live="polite">
              {presenterStatus}
            </p>
          ) : null}
        </section>
        <div className="voice-command-panel" data-anchor-actor={selectedActorId}>
          <DialoguePanel
            utterance={utteranceText}
            messages={chatMessages}
            anchorActorId={selectedActorId}
            labels={copy.dialogue}
            onUtteranceChange={(text) => setActorUtteranceDraft(selectedActorId, text)}
            onSubmit={handleSubmit}
          />
        </div>
      </CockpitStage>
      {isDeckOpen ? (
        <section
          className="ppt-modal"
          role="dialog"
          aria-modal="true"
          aria-label={pptCopy.dialogAria}
        >
          <div
            className="ppt-modal__backdrop"
            aria-hidden="true"
            onClick={() => setIsDeckOpen(false)}
          />
          <div className="ppt-modal__panel">
            <header className="ppt-modal__header">
              <div>
                <h2>{pptCopy.title}</h2>
                <p>{pptCopy.subtitle}</p>
              </div>
              <div className="ppt-modal__actions">
                <a
                  className="ppt-modal__open-link"
                  href={PPT_DECK_SRC}
                  target="_blank"
                  rel="noreferrer"
                >
                  {pptCopy.openInNew}
                </a>
                <button
                  type="button"
                  className="icon-command ppt-modal__close"
                  onClick={() => setIsDeckOpen(false)}
                >
                  <X aria-hidden="true" strokeWidth={1.8} />
                  {pptCopy.close}
                </button>
              </div>
            </header>
            <iframe
              className="ppt-modal__frame"
              title="PowerMem smart EV cockpit PPT"
              src={PPT_DECK_SRC}
              loading="lazy"
              referrerPolicy="no-referrer"
              sandbox="allow-scripts allow-same-origin"
              allowFullScreen
            />
          </div>
        </section>
      ) : null}
      {isEvidenceOpen ? (
        <section
          className="evidence-modal"
          role="dialog"
          aria-modal="true"
          aria-label={copy.evidence.dialogAria}
        >
          <div
            className="evidence-modal__backdrop"
            aria-hidden="true"
            onClick={() => setIsEvidenceOpen(false)}
          />
          <div className="evidence-modal__panel">
            <header className="evidence-modal__header">
              <div>
                <h2>{copy.evidence.title}</h2>
                <p>{copy.evidence.subtitle}</p>
              </div>
              <button
                type="button"
                className="icon-command evidence-modal__close"
                onClick={() => setIsEvidenceOpen(false)}
              >
                <X aria-hidden="true" strokeWidth={1.8} />
                {copy.evidence.close}
              </button>
            </header>
            <CockpitStatusBand labels={copy.evidencePanels.cockpitStatus} />
            {liveError ? (
              <section className="panel live-error" role="alert">
                {liveError}
              </section>
            ) : null}
            <ScenarioTimeline
              steps={scenarioSteps}
              activeIndex={selectedScenarioIndex}
              labels={copy.evidencePanels.scenarioTimeline}
              onSelect={selectScenario}
            />
            <main className="workspace-grid">
              <MemoryFlowPanel
                isEmpty={!response || response.memory_hits.length === 0}
                labels={copy.evidencePanels.memoryFlow}
              >
                <PrivacyStrip labels={copy.evidencePanels.privacy} />
                {response?.memory_hits.map((memory) => (
                  <MemoryCard memory={memory} key={memory.memory_id} />
                ))}
              </MemoryFlowPanel>
              <VehicleStatePanel
                diff={response?.vehicle_state_diff}
                state={response?.vehicle_state}
                labels={copy.evidencePanels.vehicleState}
              />
              <div className="support-stack">
                <RecommendationPanel
                  labels={copy.evidencePanels.recommendations}
                  recommendations={response?.recommendations}
                />
                <MemoryGraph
                  labels={copy.evidencePanels.memoryGraph}
                  selectedMemoryIds={response?.selected_memory_ids}
                  memoryHits={response?.memory_hits}
                />
              </div>
            </main>
            <section className="secondary-grid" aria-label="Developer and lifecycle evidence">
              {response ? (
                <DeveloperEvidenceDrawer
                  response={response}
                  labels={copy.evidencePanels.developerEvidence}
                  onExportTrace={handleExportTrace}
                />
              ) : null}
            </section>
            <LifecyclePanel
              labels={copy.evidencePanels.lifecycle}
              lifecycle={response?.lifecycle}
              operations={response?.operations}
            />
          </div>
        </section>
      ) : null}
    </AppShell>
  );
}

function appendChatMessages(
  current: DialogueMessage[],
  ...messages: DialogueMessage[]
): DialogueMessage[] {
  return [...current, ...messages];
}

async function loadChatHistory(
  actorId: ActorId,
  userId: string,
  onLoaded: (messages: DialogueMessage[]) => void,
) {
  try {
    const history = await getChatHistory({
      session_id: DEMO_SESSION_ID,
      actor_id: actorId,
      user_id: userId,
    });
    onLoaded(buildDialogueMessagesFromHistory(history.messages));
  } catch {
    onLoaded([]);
  }
}

function buildDialogueMessagesFromHistory(
  messages: ChatHistoryMessage[],
): DialogueMessage[] {
  return messages.map((message) => ({
    id: message.id,
    role: message.role,
    text: message.text,
    meta: message.created_at,
    traceId: message.trace_id,
  }));
}

function createChatMessageId(prefix: string, index: number): string {
  return `${prefix}-${Date.now()}-${index}`;
}

function normalizeScenarioResponse(response: ScenarioResponse): ScenarioResponse {
  const partial = response as Partial<ScenarioResponse>;
  return {
    ...response,
    assistant_reply:
      typeof partial.assistant_reply === "string" ? partial.assistant_reply : "",
    trace_id:
      typeof partial.trace_id === "string" && partial.trace_id
        ? partial.trace_id
        : createChatMessageId("trace", 0),
    live_backend:
      typeof partial.live_backend === "string" ? partial.live_backend : "unknown",
    powermem_connected: Boolean(partial.powermem_connected),
    operations: arrayOrEmpty(partial.operations),
    memory_hits: arrayOrEmpty(partial.memory_hits),
    selected_memory_ids: arrayOrEmpty(partial.selected_memory_ids),
    vehicle_state: recordOrEmpty(partial.vehicle_state),
    vehicle_state_diff: arrayOrEmpty(partial.vehicle_state_diff),
    privacy_report: recordOrEmpty(partial.privacy_report),
    recommendations: arrayOrEmpty(partial.recommendations),
    evidence: recordOrEmpty(partial.evidence),
  };
}

function arrayOrEmpty<T>(value: T[] | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function recordOrEmpty(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }
  return value as Record<string, unknown>;
}

function downloadJson(data: unknown, filename: string) {
  if (
    typeof document === "undefined" ||
    typeof Blob === "undefined" ||
    typeof URL === "undefined" ||
    typeof URL.createObjectURL !== "function"
  ) {
    return;
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
}
