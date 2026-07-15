import { useEffect, useState } from "react";
import {
  BatteryMedium,
  BatteryWarning,
  Bluetooth,
  Minus,
  Pause,
  Play,
  Plus,
  Power,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
} from "lucide-react";

import { APP_COPY, type InfotainmentDisplayLabels } from "../i18n";
import type { PetTarget } from "../view-models/petCompanion";
import { buildScenarioBatteryState } from "../view-models/projection";
import type {
  ProjectionClimateAction,
  ProjectionMediaPreference,
  ProjectionScene,
  ScenarioStep,
} from "../view-models/projection";

interface InfotainmentDisplayProps {
  steps: ScenarioStep[];
  activeIndex: number;
  projection: ProjectionScene;
  petFocusTarget?: PetTarget;
  labels?: InfotainmentDisplayLabels;
  onSelectScenario: (index: number) => void;
}

const MIN_MEDIA_VOLUME = 0;
const MAX_MEDIA_VOLUME = 40;
const DEFAULT_MEDIA_VOLUME = 22;
const MEDIA_PROGRESS_PERCENT = 38;
const MEDIA_ELAPSED_TIME = "01:18";
const MEDIA_TOTAL_TIME = "03:42";

function formatClockTime(date = new Date()): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function getPreviousScenarioIndex(activeIndex: number, totalSteps: number): number {
  if (totalSteps <= 0) {
    return 0;
  }
  return (activeIndex - 1 + totalSteps) % totalSteps;
}

function getNextScenarioIndex(activeIndex: number, totalSteps: number): number {
  if (totalSteps <= 0) {
    return 0;
  }
  return (activeIndex + 1) % totalSteps;
}

function clampMediaVolume(volume: number): number {
  return Math.min(MAX_MEDIA_VOLUME, Math.max(MIN_MEDIA_VOLUME, volume));
}

function parseMediaVolume(volume: string): number {
  const parsed = Number.parseInt(volume, 10);
  if (Number.isNaN(parsed)) {
    return DEFAULT_MEDIA_VOLUME;
  }
  return clampMediaVolume(parsed);
}

function formatTemperature(value: number | undefined, fallback: string): string {
  return typeof value === "number" ? `${value}°C` : fallback;
}

export function InfotainmentDisplay({
  steps,
  activeIndex,
  projection,
  petFocusTarget,
  labels = APP_COPY.en.cockpit.infotainment,
  onSelectScenario,
}: InfotainmentDisplayProps) {
  const activeStep = steps[activeIndex] ?? steps[0];
  const initialHvacTargetTemp = formatTemperature(
    activeStep?.initialHvacTargetTempC,
    labels.defaultClimateTemp,
  );
  const climateAction: ProjectionClimateAction =
    projection.climateAction ?? {
      zoneLabel: labels.defaultClimateZone,
      temperatureLabel: labels.defaultClimateZone,
      beforeTemp: initialHvacTargetTemp,
      afterTemp: initialHvacTargetTemp,
      temperatureReadout: labels.defaultClimateReadout,
      seatHeatLabel: labels.defaultSeatHeatLabel,
      beforeSeatHeat: labels.defaultSeatHeatLevel,
      afterSeatHeat: labels.defaultSeatHeatLevel,
      seatHeatReadout: labels.defaultSeatHeatReadout,
    };
  const mediaPreference: ProjectionMediaPreference =
    projection.mediaPreference ?? labels.defaultMediaPreference;
  const [clockTime, setClockTime] = useState(() => formatClockTime());
  const [mediaVolume, setMediaVolume] = useState(() =>
    parseMediaVolume(mediaPreference.volume),
  );
  const [mediaEnabled, setMediaEnabled] = useState(true);
  const [mediaPlaying, setMediaPlaying] = useState(true);
  const batteryState = projection.batteryState ?? buildScenarioBatteryState(activeStep);
  const batteryStatusLabel = labels.batteryStatusLabels[batteryState.status];
  const BatteryIcon =
    batteryState.status === "critical" ? BatteryWarning : BatteryMedium;
  const previousIndex = getPreviousScenarioIndex(activeIndex, steps.length);
  const nextIndex = getNextScenarioIndex(activeIndex, steps.length);
  const sceneNavigationDisabled = steps.length === 0;
  const climateFocused =
    petFocusTarget === "climate" ||
    petFocusTarget === "seat" ||
    petFocusTarget === "routine";
  const mediaFocused = petFocusTarget === "media";
  const navigationFocused = petFocusTarget === "navigation";
  const batteryFocused = petFocusTarget === "battery";
  const sceneFocused =
    petFocusTarget === "boundary" ||
    petFocusTarget === "relationship" ||
    petFocusTarget === "memory" ||
    petFocusTarget === "drive" ||
    petFocusTarget === "lifecycle";

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setClockTime(formatClockTime());
    }, 60_000);
    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    setMediaVolume(parseMediaVolume(mediaPreference.volume));
  }, [mediaPreference.volume]);

  const mediaState = !mediaEnabled ? "off" : mediaPlaying ? "playing" : "paused";
  const mediaStatusLabel = !mediaEnabled
    ? labels.musicOffLabel
    : mediaPlaying
      ? labels.musicPlayingLabel
      : labels.musicPausedLabel;
  const mediaProgress = mediaEnabled ? MEDIA_PROGRESS_PERCENT : 0;
  const mediaElapsedTime = mediaEnabled ? MEDIA_ELAPSED_TIME : "--:--";
  const mediaTotalTime = mediaEnabled ? MEDIA_TOTAL_TIME : "--:--";
  const playPauseLabel = mediaPlaying ? labels.pauseMusicLabel : labels.playMusicLabel;

  const handleMediaPowerToggle = () => {
    if (mediaEnabled) {
      setMediaEnabled(false);
      setMediaPlaying(false);
      return;
    }

    setMediaEnabled(true);
    setMediaPlaying(true);
  };

  return (
    <div
      className="infotainment-display"
      aria-label={labels.displayLabel}
      data-display-mode="automotive-glass"
      data-screen-placement="center-touchscreen"
      data-frame-source="background-image"
    >
      <div className="infotainment-display__hardware" aria-hidden="true" />
      <section
        className="infotainment-display__center"
        aria-label={labels.centerTouchscreenLabel}
      >
        <div className="infotainment-display__topbar">
          <span>{labels.bluetoothMusic}</span>
          <time>{clockTime}</time>
        </div>

        {projection.mode === "navigation" && projection.navigation ? (
          <div className="infotainment-display__dashboard infotainment-display__dashboard--map">
            <section
              className="infotainment-display__navigation-map"
              aria-label={labels.navigationMapModeLabel}
              data-pet-focus={navigationFocused ? "true" : undefined}
            >
              <svg
                className="infotainment-display__city-map"
                viewBox="0 0 900 420"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <path
                  className="city-map__water"
                  d="M392 -20 C360 54 423 91 381 154 C342 212 285 249 322 324 C346 374 322 405 306 440 L420 440 C452 362 405 334 453 262 C494 199 555 160 516 92 C487 42 529 13 552 -20 Z"
                />
                <path className="city-map__minor" d="M18 52 H378" />
                <path className="city-map__minor" d="M546 52 H884" />
                <path className="city-map__minor" d="M28 112 H352" />
                <path className="city-map__minor" d="M535 118 H872" />
                <path className="city-map__minor" d="M10 178 H326" />
                <path className="city-map__minor" d="M505 184 H890" />
                <path className="city-map__minor" d="M42 252 H308" />
                <path className="city-map__minor" d="M468 252 H852" />
                <path className="city-map__minor" d="M22 330 H338" />
                <path className="city-map__minor" d="M438 326 H888" />
                <path className="city-map__minor" d="M92 6 V398" />
                <path className="city-map__minor" d="M190 0 V412" />
                <path className="city-map__minor" d="M294 0 V412" />
                <path className="city-map__minor" d="M612 0 V412" />
                <path className="city-map__minor" d="M724 0 V412" />
                <path className="city-map__minor" d="M820 0 V412" />
                <path
                  className="city-map__major"
                  d="M34 354 C128 286 210 292 306 240 C380 198 408 154 505 136 C612 116 706 88 872 44"
                />
                <path
                  className="city-map__major"
                  d="M16 92 C122 150 208 160 296 144 C358 132 394 124 472 138 C572 158 694 146 886 110"
                />
                <path
                  className="city-map__secondary"
                  d="M86 18 C156 92 174 162 246 206 C312 246 340 304 362 414"
                />
                <path
                  className="city-map__secondary"
                  d="M828 0 C750 76 698 145 676 222 C656 292 616 342 540 420"
                />
                <path
                  className="city-map__ring"
                  d="M160 86 C250 24 386 42 470 104 C548 162 548 268 472 326 C390 388 260 380 178 320 C96 260 78 146 160 86"
                />
                <path
                  className="city-map__ring city-map__ring--outer"
                  d="M62 74 C210 -25 470 -8 620 98 C760 197 742 320 604 389 C456 463 190 430 72 320 C-42 214 -54 144 62 74"
                />
                <path
                  className="city-map__century"
                  d="M430 238 C496 212 558 196 650 178 C720 164 786 142 858 120"
                />
                <path
                  className="city-map__route-shadow"
                  d="M174 306 C254 260 316 272 386 238 C462 202 526 205 592 190 C658 175 704 142 774 116"
                />
                <path
                  className="city-map__route"
                  d="M174 306 C254 260 316 272 386 238 C462 202 526 205 592 190 C658 175 704 142 774 116"
                />
                <path
                  className="city-map__route-progress"
                  d="M174 306 C254 260 316 272 386 238 C462 202 526 205 592 190"
                />
                <circle className="city-map__poi" cx="276" cy="212" r="4" />
                <circle className="city-map__poi" cx="474" cy="150" r="4" />
                <circle className="city-map__poi" cx="594" cy="232" r="4" />
                <circle className="city-map__poi" cx="728" cy="154" r="4" />
                <circle className="city-map__vehicle-halo" cx="174" cy="306" r="18" />
                <circle className="city-map__vehicle" cx="174" cy="306" r="7" />
                <circle className="city-map__destination-halo" cx="774" cy="116" r="19" />
                <circle className="city-map__destination" cx="774" cy="116" r="8" />
              </svg>

              <span className="infotainment-display__map-label infotainment-display__map-label--river">
                {labels.navigationMapLabels.huangpuRiver}
              </span>
              <span className="infotainment-display__map-label infotainment-display__map-label--inner-ring">
                {labels.navigationMapLabels.innerRing}
              </span>
              <span className="infotainment-display__map-label infotainment-display__map-label--middle-ring">
                {labels.navigationMapLabels.middleRing}
              </span>
              <span className="infotainment-display__map-label infotainment-display__map-label--century">
                {labels.navigationMapLabels.centuryAvenue}
              </span>
              <span className="infotainment-display__map-poi infotainment-display__map-poi--xujiahui">
                {labels.navigationMapLabels.xujiahui}
              </span>
              <span className="infotainment-display__map-poi infotainment-display__map-poi--lujiazui">
                {labels.navigationMapLabels.lujiazui}
              </span>
              <span className="infotainment-display__map-poi infotainment-display__map-poi--park">
                {labels.navigationMapLabels.centuryPark}
              </span>
              <span className="infotainment-display__map-poi infotainment-display__map-poi--zhangjiang">
                {labels.navigationMapLabels.zhangjiang}
              </span>

              <div className="infotainment-display__map-compass" aria-hidden="true">
                <b>N</b>
                <span>{labels.navigationCityLabel}</span>
              </div>
              <div className="infotainment-display__map-scale" aria-hidden="true">
                <i />
                <span>{labels.navigationScaleLabel}</span>
              </div>

              <div className="infotainment-display__nav-turn">
                <span>{labels.navigationInstruction}</span>
                <strong>{labels.navigationInstructionDetail(projection.navigation.destinationLabel)}</strong>
                <small>{projection.navigation.routeLabel}</small>
              </div>

              <aside className="infotainment-display__nav-summary">
                <span>{labels.navigationDestinationLabel}</span>
                <strong>{projection.navigation.destinationLabel}</strong>
                <div className="infotainment-display__nav-metrics">
                  <div>
                    <small>{labels.navigationEtaLabel}</small>
                    <b>{labels.navigationEtaValue}</b>
                  </div>
                  <div>
                    <small>{labels.navigationDistanceLabel}</small>
                    <b>{labels.navigationDistanceValue}</b>
                  </div>
                </div>
              </aside>

              <div className="infotainment-display__nav-bottom">
                <span>{projection.navigation.statusLabel}</span>
                <strong>{labels.navigationTrafficLabel}</strong>
                <small>{projection.chips.at(2)?.value ?? labels.navigationAreaOnlyLabel}</small>
              </div>
            </section>
          </div>
        ) : (
          <div className="infotainment-display__dashboard">
          <section
            className="infotainment-display__scene-card"
            aria-label={labels.projectionSummaryLabel}
            data-pet-focus={sceneFocused ? "true" : undefined}
          >
            <div className="infotainment-display__scene-layout">
              <div className="infotainment-display__scene-copy">
                <div className="infotainment-display__scene-kicker">
                  <span>{activeStep ? activeStep.day : projection.dockLabel}</span>
                  <strong>{activeStep ? activeStep.act : projection.title}</strong>
                </div>
                <h2>{projection.title}</h2>
                <p>{projection.subtitle}</p>
                <div className="infotainment-display__scene-readout">
                  <b>{projection.routeReadout}</b>
                </div>
              </div>
            </div>
            <div className="infotainment-display__scene-arrows">
              <button
                type="button"
                aria-label={labels.previousSceneLabel}
                disabled={sceneNavigationDisabled}
                onClick={() => onSelectScenario(previousIndex)}
              >
                <span aria-hidden="true">‹</span>
              </button>
              <button
                type="button"
                aria-label={labels.nextSceneLabel}
                disabled={sceneNavigationDisabled}
                onClick={() => onSelectScenario(nextIndex)}
              >
                <span aria-hidden="true">›</span>
              </button>
            </div>
          </section>

          <div className="infotainment-display__center-stack">
            <section
              className="infotainment-display__battery-card"
              aria-label={labels.batteryCardLabel}
              data-battery-state={batteryState.status}
              data-battery-source={batteryState.isLive ? "live" : "scenario"}
              data-pet-focus={batteryFocused ? "true" : undefined}
            >
              <div className="infotainment-display__battery-header">
                <span>{labels.batteryCardTitle}</span>
                <b>
                  <BatteryIcon aria-hidden="true" size={13} strokeWidth={2.5} />
                  {labels.batteryLiveLabel}
                </b>
              </div>
              <div className="infotainment-display__battery-main">
                <div className="infotainment-display__battery-shell" aria-hidden="true">
                  <i
                    className="infotainment-display__battery-fill"
                    style={{ width: `${batteryState.percent}%` }}
                  />
                  <span />
                  <span />
                  <span />
                </div>
                <strong>{batteryState.percent}%</strong>
              </div>
              <div className="infotainment-display__battery-meta">
                <span>{labels.batteryRangeLabel}</span>
                <b>{batteryState.rangeKm} km</b>
              </div>
              <div className="infotainment-display__battery-footer">
                <span>{batteryStatusLabel}</span>
                <small>
                  {labels.batteryHealthLabel} {labels.batteryHealthValue}
                </small>
              </div>
            </section>

            {projection.mode === "battery-care" && projection.batteryCare ? (
              <section
                className="infotainment-display__climate-card infotainment-display__battery-care-card"
                aria-label={projection.batteryCare.title}
              >
                <span>{projection.batteryCare.title}</span>
                <strong>{projection.batteryCare.destinationLabel}</strong>
                <small>{projection.batteryCare.memoryLabel}</small>
                <div className="infotainment-display__battery-care-action">
                  <BatteryWarning aria-hidden="true" size={13} strokeWidth={2.5} />
                  <b>{projection.batteryCare.actionLabel}</b>
                </div>
              </section>
            ) : projection.mode === "recommendation" && projection.recommendation ? (
              <section
                className="infotainment-display__climate-card infotainment-display__recommendation-card"
                aria-label={projection.recommendation.title}
              >
                <span>{projection.recommendation.policyLabel}</span>
                <strong>{projection.recommendation.regionLabel}</strong>
                <small>{projection.recommendation.privacyLabel}</small>
              </section>
            ) : (
              <section
                className="infotainment-display__climate-card"
                aria-label={labels.climateCardLabel}
                data-pet-focus={climateFocused ? "true" : undefined}
              >
                <span>{climateAction.zoneLabel}</span>
                <strong>{climateAction.afterTemp}</strong>
                <small>{climateAction.temperatureReadout}</small>
                <div className="infotainment-display__seat-heat">
                  <span>{climateAction.seatHeatLabel}</span>
                  <b>{climateAction.afterSeatHeat}</b>
                  <small>{climateAction.seatHeatReadout}</small>
                </div>
              </section>
            )}
          </div>

          <section
            className="infotainment-display__music-card"
            aria-label={labels.musicCardLabel}
            data-media-state={mediaState}
            data-pet-focus={mediaFocused ? "true" : undefined}
          >
            <div className="infotainment-display__music-header">
              <span>{labels.bluetoothMusic}</span>
              <div className="infotainment-display__music-status" aria-live="polite">
                <Bluetooth aria-hidden="true" size={13} strokeWidth={2.4} />
                <small>{labels.musicConnectedLabel}</small>
                <b>{mediaStatusLabel}</b>
              </div>
            </div>
            <div className="infotainment-display__music-meta">
              <small>{mediaPreference.sourceLabel}</small>
              <strong>{mediaPreference.title}</strong>
              <em>{mediaPreference.subtitle}</em>
            </div>
            <div
              className="infotainment-display__music-equalizer"
              aria-hidden="true"
              data-state={mediaState}
            >
              <i />
              <i />
              <i />
              <i />
              <i />
            </div>
            <div className="infotainment-display__music-controls">
              <button type="button" aria-label={labels.previousTrackLabel}>
                <SkipBack aria-hidden="true" size={15} strokeWidth={2.5} />
              </button>
              <button
                type="button"
                className="infotainment-display__music-play"
                aria-label={playPauseLabel}
                disabled={!mediaEnabled}
                onClick={() => setMediaPlaying((playing) => !playing)}
              >
                {mediaPlaying ? (
                  <Pause aria-hidden="true" size={18} strokeWidth={2.8} />
                ) : (
                  <Play aria-hidden="true" size={18} strokeWidth={2.8} />
                )}
              </button>
              <button type="button" aria-label={labels.nextTrackLabel}>
                <SkipForward aria-hidden="true" size={15} strokeWidth={2.5} />
              </button>
              <button
                type="button"
                className="infotainment-display__music-power"
                aria-label={
                  mediaEnabled ? labels.turnMusicOffLabel : labels.turnMusicOnLabel
                }
                aria-pressed={!mediaEnabled}
                onClick={handleMediaPowerToggle}
              >
                <Power aria-hidden="true" size={14} strokeWidth={2.6} />
              </button>
            </div>
            <div className="infotainment-display__music-progress">
              <span>{mediaElapsedTime}</span>
              <div
                aria-label={labels.playbackProgressLabel}
                aria-valuemax={100}
                aria-valuemin={0}
                aria-valuenow={mediaProgress}
                role="progressbar"
              >
                <i style={{ width: `${mediaProgress}%` }} />
              </div>
              <span>{mediaTotalTime}</span>
            </div>
            <div className="infotainment-display__music-volume" aria-live="polite">
              <button
                type="button"
                aria-label={labels.decreaseVolumeLabel}
                disabled={!mediaEnabled}
                onClick={() =>
                  setMediaVolume((currentVolume) =>
                    clampMediaVolume(currentVolume - 1),
                  )
                }
              >
                <Minus aria-hidden="true" size={14} strokeWidth={2.7} />
              </button>
              <div>
                {mediaEnabled ? (
                  <Volume2 aria-hidden="true" size={13} strokeWidth={2.4} />
                ) : (
                  <VolumeX aria-hidden="true" size={13} strokeWidth={2.4} />
                )}
                <span>{mediaPreference.volumeLabel}</span>
                <strong>{mediaVolume}</strong>
              </div>
              <button
                type="button"
                aria-label={labels.increaseVolumeLabel}
                disabled={!mediaEnabled}
                onClick={() =>
                  setMediaVolume((currentVolume) =>
                    clampMediaVolume(currentVolume + 1),
                  )
                }
              >
                <Plus aria-hidden="true" size={14} strokeWidth={2.7} />
              </button>
            </div>
          </section>
          </div>
        )}
      </section>
    </div>
  );
}
