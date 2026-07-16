interface ProjectionMapProps {
  label?: string;
  readout: string;
  status: "idle" | "ready" | "error";
}

export function ProjectionMap({ label, readout, status }: ProjectionMapProps) {
  const path =
    status === "error"
      ? "M24,84 C70,82 82,38 126,48 C170,58 178,118 221,111 C248,107 268,78 286,80"
      : "M22,132 C58,92 91,128 128,86 C166,43 202,68 235,38 C256,20 273,24 288,39";

  return (
    <div className="projection-map" aria-label={readout}>
      {label ? <strong className="projection-map__label">{label}</strong> : null}
      <svg viewBox="0 0 300 170" preserveAspectRatio="none" aria-hidden="true">
        <path d={path} className="projection-map__glow" />
        <path d={path} className="projection-map__line" />
        <circle cx="235" cy="38" r="6" />
      </svg>
      <span>
        <i className="projection-map__pulse" aria-hidden="true" />
        {readout}
      </span>
    </div>
  );
}
