import {
  APP_COPY,
  type InteriorThemeId,
  type InteriorTrimLabels,
} from "../i18n";

export type InteriorTheme = InteriorThemeId;

const INTERIOR_THEMES: Array<{
  id: InteriorTheme;
}> = [
  { id: "black" },
  { id: "orange" },
  { id: "red" },
  { id: "ivory" },
  { id: "cognac" },
];

interface InteriorTrimSelectorProps {
  selectedTheme: InteriorTheme;
  labels?: InteriorTrimLabels;
  onSelect: (theme: InteriorTheme) => void;
}

export function InteriorTrimSelector({
  selectedTheme,
  labels = APP_COPY.en.interior,
  onSelect,
}: InteriorTrimSelectorProps) {
  const selectId = "interior-trim-select";

  return (
    <section className="interior-trim-selector" aria-label={labels.selectorLabel}>
      <label htmlFor={selectId}>{labels.selectorLabel}</label>
      <div className={`interior-trim-select-shell interior-swatch--${selectedTheme}`}>
        <span aria-hidden="true" />
        <select
          id={selectId}
          value={selectedTheme}
          onChange={(event) => onSelect(event.target.value as InteriorTheme)}
        >
          {INTERIOR_THEMES.map((theme) => (
            <option value={theme.id} key={theme.id}>
              {labels.themes[theme.id]}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}
