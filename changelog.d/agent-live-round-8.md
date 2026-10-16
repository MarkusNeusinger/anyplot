### Fixed

- **The assistant sees every category of a short column.** The dataset profile now lists every value
  of a text column with at most 12 distinct ones (else its five most frequent), so a six-source
  energy mix no longer hides its sixth source, `Übrige`, which the reply had called a row the plot
  added. The dataset judge reads the same values, and a profile over its size cap first drops the
  values past the five most frequent. (#12206)
- **Adapted heatmaps derive their color scale from the data.** The readiness scan now names literal
  color-scale limits, centers and colorbar ticks (`vmin=0, vmax=100, center=50`) and a colorbar at
  literal figure coordinates (`cbar_pos`) as hints for the adapter, so a heatmap of values from 32 to
  93 no longer keeps a 0 to 100 scale and a stray top-left colorbar. (#12206)

### Changed

- **`.to_long()` names the new columns in the session language.** The names column says what the
  melted headers are (`Wochentag`, `Monat`, `Jahr`) or `Kategorie`, and the values column is `Wert`,
  instead of the roles' names `y` and `value`, which became the plot's text. The new columns stay
  bound to the roles they were made for whatever their names, and the summary offers a rename when
  the notes or the file name say what the values measure. (#12206)
