import { motion } from "framer-motion";

import type { PetAnchor, PetCompanionState } from "../view-models/petCompanion";

interface PetCompanionProps {
  state: PetCompanionState;
}

interface AnchorPoint {
  left: string;
  top: string;
  scale: number;
}

const ANCHOR_POINTS: Record<PetAnchor, AnchorPoint> = {
  driver: { left: "23%", top: "67%", scale: 0.76 },
  passenger: { left: "77%", top: "67%", scale: 0.76 },
  child: { left: "50%", top: "79%", scale: 0.72 },
  chat_driver: { left: "27.5%", top: "29%", scale: 0.66 },
  chat_passenger: { left: "94.5%", top: "29%", scale: 0.66 },
  chat_child: { left: "27.5%", top: "32%", scale: 0.64 },
  climate: { left: "57%", top: "56%", scale: 0.7 },
  media: { left: "88%", top: "55%", scale: 0.68 },
  navigation: { left: "88%", top: "36%", scale: 0.68 },
  drive: { left: "62%", top: "67%", scale: 0.7 },
  battery: { left: "43%", top: "63%", scale: 0.72 },
  lifecycle: { left: "60%", top: "27%", scale: 0.66 },
  routine: { left: "56%", top: "48%", scale: 0.7 },
  boundary: { left: "47%", top: "35%", scale: 0.68 },
  memory: { left: "40%", top: "32%", scale: 0.66 },
  error: { left: "52%", top: "28%", scale: 0.68 },
};

export function PetCompanion({ state }: PetCompanionProps) {
  const origin = ANCHOR_POINTS[state.originAnchor] ?? ANCHOR_POINTS.driver;
  const anchor = ANCHOR_POINTS[state.anchor] ?? origin;

  return (
    <motion.aside
      className="pet-companion pet-companion--free"
      aria-label={`${state.name}：${state.speech}`}
      aria-live="polite"
      data-action={state.action}
      data-anchor={state.anchor}
      data-motion="active"
      data-mood={state.mood}
      data-origin-anchor={state.originAnchor}
      data-target={state.target}
      data-travel={state.travelLabel}
      initial={{
        left: origin.left,
        top: origin.top,
        x: "-50%",
        y: "-50%",
        opacity: 0,
        scale: origin.scale * 0.84,
      }}
      animate={{
        left: anchor.left,
        top: anchor.top,
        x: "-50%",
        y: "-50%",
        opacity: 1,
        scale: anchor.scale,
      }}
      transition={{
        type: "spring",
        stiffness: 138,
        damping: 13,
        mass: 0.72,
      }}
    >
      <motion.div
        key={state.travelLabel}
        className="pet-companion__sprite"
        data-testid="pet-companion-sprite"
        initial={{ y: 0, rotate: -6, scaleX: 1.08, scaleY: 0.92 }}
        animate={{
          y: [0, -10, -46, -28, -6, 3, 0],
          rotate: [-6, -2, 7, -3, 2, 0, 0],
          scaleX: [1.08, 0.96, 0.9, 0.98, 1.1, 0.98, 1],
          scaleY: [0.92, 1.04, 1.14, 1.02, 0.9, 1.03, 1],
        }}
        transition={{
          duration: 1.05,
          ease: [0.18, 0.76, 0.26, 1],
          times: [0, 0.12, 0.34, 0.56, 0.78, 0.9, 1],
        }}
      >
        <div className="pet-companion__avatar" aria-hidden="true">
          <svg
            className="pet-companion__figure"
            viewBox="0 0 176 168"
            aria-hidden="true"
            data-testid="memofox-figure"
          >
            <defs>
              <linearGradient id="memofox-fur-main" x1="42" x2="128" y1="34" y2="136">
                <stop offset="0" stopColor="#f6fffb" stopOpacity="0.94" />
                <stop offset="0.48" stopColor="#83fff0" stopOpacity="0.5" />
                <stop offset="1" stopColor="#1ed4c7" stopOpacity="0.38" />
              </linearGradient>
              <linearGradient id="memofox-fur-shadow" x1="48" x2="126" y1="122" y2="42">
                <stop offset="0" stopColor="#052c31" stopOpacity="0.82" />
                <stop offset="1" stopColor="#bafff6" stopOpacity="0.28" />
              </linearGradient>
              <radialGradient id="memofox-face-glow" cx="44%" cy="36%" r="64%">
                <stop offset="0" stopColor="#ffffff" stopOpacity="0.92" />
                <stop offset="0.52" stopColor="#bdfdf4" stopOpacity="0.55" />
                <stop offset="1" stopColor="#22d7cb" stopOpacity="0.14" />
              </radialGradient>
              <radialGradient id="memofox-eye-depth" cx="36%" cy="30%" r="68%">
                <stop offset="0" stopColor="#ffffff" stopOpacity="0.96" />
                <stop offset="0.26" stopColor="#8ffcf0" stopOpacity="0.58" />
                <stop offset="0.62" stopColor="#073a40" stopOpacity="0.92" />
                <stop offset="1" stopColor="#01191c" stopOpacity="1" />
              </radialGradient>
              <radialGradient id="memofox-nose-gloss" cx="42%" cy="24%" r="70%">
                <stop offset="0" stopColor="#ffffff" stopOpacity="0.86" />
                <stop offset="0.42" stopColor="#88fff1" stopOpacity="0.32" />
                <stop offset="1" stopColor="#061c1f" stopOpacity="0" />
              </radialGradient>
              <filter id="memofox-soft-glow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feColorMatrix
                  in="blur"
                  type="matrix"
                  values="0 0 0 0 0.08 0 0 0 0 1 0 0 0 0 0.9 0 0 0 0.65 0"
                  result="glow"
                />
                <feMerge>
                  <feMergeNode in="glow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <ellipse className="pet-companion__ground" cx="85" cy="143" rx="55" ry="13" />
            <g className="pet-companion__motion-layer" data-motion-part="body">
              <g
                className="pet-companion__tail"
                data-testid="pet-companion-tail"
                data-motion-part="tail"
              >
                <path
                  className="pet-companion__tail-core"
                  d="M111 112C145 106 164 78 153 52C143 28 115 35 108 58C103 75 83 82 74 94C62 112 82 126 111 112Z"
                />
                <path
                  className="pet-companion__tail-tip"
                  d="M134 44C148 48 155 61 153 76C141 70 133 59 134 44Z"
                />
                <path
                  className="pet-companion__tail-ridge"
                  d="M115 96C133 88 143 74 145 60"
                />
              </g>
              <g className="pet-companion__ears" data-testid="pet-companion-ears">
                <path className="pet-companion__ear" d="M54 55L42 17L76 42Z" />
                <path className="pet-companion__ear pet-companion__ear--right" d="M101 42L134 17L122 57Z" />
                <path className="pet-companion__inner-ear" d="M56 45L50 27L68 41Z" />
                <path className="pet-companion__inner-ear" d="M111 42L128 28L119 49Z" />
              </g>
              <g
                className="pet-companion__body-shell"
                data-testid="pet-companion-body-shell"
              >
                <path
                  className="pet-companion__torso"
                  d="M50 102C55 80 72 69 92 72C116 76 128 96 122 122C118 140 103 151 82 151C61 151 46 137 50 102Z"
                />
                <path
                  className="pet-companion__chest"
                  d="M61 111C70 100 80 95 88 84C96 96 108 102 115 114C111 134 99 143 84 143C70 143 60 132 61 111Z"
                />
                <path
                  className="pet-companion__fur-layer"
                  d="M64 111L75 119L84 104L94 120L105 111L98 137H72Z"
                />
                <path
                  className="pet-companion__torso-rim"
                  d="M58 101C66 83 80 76 96 79C111 82 119 96 116 116"
                />
              </g>
              <g className="pet-companion__head-group">
                <path
                  className="pet-companion__head"
                  d="M44 61C54 38 84 29 109 43C129 55 133 82 119 101C104 122 69 123 50 104C39 93 37 76 44 61Z"
                  data-testid="pet-companion-head"
                />
                <path
                  className="pet-companion__head-rim"
                  d="M52 62C61 45 84 38 104 47C118 54 125 69 122 84"
                />
                <path
                  className="pet-companion__face-fluff"
                  d="M48 78C58 65 70 64 83 76C96 64 111 66 121 80C116 102 102 113 84 114C65 112 53 100 48 78Z"
                />
                <path
                  className="pet-companion__cheek"
                  d="M50 88C57 92 63 92 69 86C68 98 60 104 51 101Z"
                />
                <path
                  className="pet-companion__cheek pet-companion__cheek--right"
                  d="M116 88C109 92 103 92 97 86C98 98 106 104 115 101Z"
                />
                <g className="pet-companion__muzzle" data-testid="pet-companion-muzzle">
                  <path d="M69 82C76 77 91 77 98 83C98 96 91 103 83 103C75 103 68 95 69 82Z" />
                  <path d="M75 96C80 99 86 99 91 96" />
                </g>
                <g className="pet-companion__eyes">
                  <ellipse
                    className="pet-companion__eye-depth"
                    cx="67"
                    cy="75"
                    data-testid="pet-companion-eye-depth"
                    rx="6.3"
                    ry="7.1"
                  />
                  <ellipse className="pet-companion__eye-depth" cx="100" cy="75" rx="6.3" ry="7.1" />
                  <circle className="pet-companion__eye" cx="67" cy="75" r="5" />
                  <circle className="pet-companion__eye" cx="100" cy="75" r="5" />
                  <circle className="pet-companion__eye-shine" cx="65" cy="73" r="1.5" />
                  <circle className="pet-companion__eye-shine" cx="98" cy="73" r="1.5" />
                </g>
                <g
                  className="pet-companion__eye-lids"
                  data-testid="pet-companion-eye-lids"
                  data-motion-part="blink"
                >
                  <path d="M60 71C64 68 70 68 74 71" />
                  <path d="M93 71C97 68 103 68 107 71" />
                </g>
                <path className="pet-companion__nose" d="M78 87L88 87L83 93Z" />
                <path
                  className="pet-companion__nose-gloss"
                  d="M80 88C82 86.7 84.8 86.7 86.7 88C85.3 88.7 82.1 88.8 80 88Z"
                  data-testid="pet-companion-nose-gloss"
                />
              </g>
              <g
                className="pet-companion__forepaws"
                data-testid="pet-companion-forepaws"
              >
                <path d="M58 128C63 121 72 122 75 131C72 140 59 141 55 135C54 132 55 130 58 128Z" />
                <path d="M94 131C97 122 107 121 112 128C116 134 110 141 100 140C96 138 94 135 94 131Z" />
                <g className="pet-companion__paw-pads" data-testid="pet-companion-paw-pads">
                  <ellipse cx="63" cy="133" rx="3.7" ry="2.3" />
                  <ellipse cx="70" cy="131" rx="2" ry="1.5" />
                  <ellipse cx="101" cy="133" rx="3.7" ry="2.3" />
                  <ellipse cx="108" cy="131" rx="2" ry="1.5" />
                </g>
              </g>
              <g
                className="pet-companion__fur-strands"
                data-testid="pet-companion-fur-strands"
              >
                <path d="M58 70C65 63 76 62 84 69" />
                <path d="M97 68C106 62 116 64 123 72" />
                <path d="M64 114C73 121 92 123 104 116" />
                <path d="M113 100C130 91 141 75 145 58" />
                <path d="M52 91C58 95 65 95 71 90" />
              </g>
              <g
                className="pet-companion__memory-chip"
                data-testid="pet-companion-memory-chip"
                data-motion-part="memory"
              >
                <rect x="21" y="112" width="44" height="27" rx="10" />
                <path d="M31 121H55M31 130H48" />
                <circle cx="57" cy="121" r="2.2" />
              </g>
            </g>
          </svg>
        </div>
      </motion.div>

      <motion.div
        className="pet-companion__speech-bubble"
        data-testid="pet-companion-speech-bubble"
        initial={{ opacity: 0, y: 10, scale: 0.86 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ delay: 0.2, duration: 0.28 }}
      >
        <span className="pet-companion__name">{state.name}</span>
        <strong>{state.cueLabel}</strong>
        <p>{state.speech}</p>
        <b>{state.memoryOrbLabel}</b>
      </motion.div>
    </motion.aside>
  );
}
