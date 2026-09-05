// anyplot.ai
// scatter-color-mapped: Color-Mapped Scatter Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 82/100 | Created: 2026-09-05
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsText } from "@mui/x-charts/ChartsText";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Ocean buoy network: sea-surface temperature sampled across a survey grid.
// A warm-core current near (0°E, 40°N) fades outward, so temperature (color)
// traces a spatial pattern rather than pure noise.
let seed = 42;
const nextRandom = () => {
  seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
};

const STATION_COUNT = 160;
const buoys = [];
for (let i = 0; i < STATION_COUNT; i += 1) {
  const longitude = -14 + nextRandom() * 26;
  const latitude = 30 + nextRandom() * 22;
  const distanceFromCore = Math.hypot(longitude - 0, latitude - 40);
  const temperature = 23 - 0.42 * distanceFromCore + (nextRandom() - 0.5) * 2.4;
  buoys.push({
    id: i,
    x: Number(longitude.toFixed(2)),
    y: Number(latitude.toFixed(2)),
    z: Number(temperature.toFixed(2)),
  });
}

const temperatures = buoys.map((buoy) => buoy.z);
const tempMin = Math.min(...temperatures);
const tempMax = Math.max(...temperatures);

// --- Title (fontsize scales with title length, see plot-generator.md) -------
const TITLE = "scatter-color-mapped · javascript · muix · anyplot.ai";
const TITLE_FONTSIZE = Math.round(22 * (TITLE.length > 67 ? 67 / TITLE.length : 1));

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  return (
    <ScatterChart
      width={width}
      height={height}
      skipAnimation
      legend={{ hidden: true }}
      grid={{ vertical: true, horizontal: true }}
      margin={{ top: 90, right: 190, bottom: 110, left: 110 }}
      xAxis={[
        {
          id: "longitude",
          label: "Longitude (°E)",
          labelStyle: { fontSize: 18 },
          tickLabelStyle: { fontSize: 14 },
          valueFormatter: (value: number) => `${value}°`,
        },
      ]}
      yAxis={[
        {
          id: "latitude",
          label: "Latitude (°N)",
          labelStyle: { fontSize: 18 },
          tickLabelStyle: { fontSize: 14 },
          valueFormatter: (value: number) => `${value}°`,
        },
      ]}
      zAxis={[
        {
          id: "temperature",
          min: tempMin,
          max: tempMax,
          colorMap: {
            type: "continuous",
            min: tempMin,
            max: tempMax,
            color: [t.seq[0], t.seq[1]],
          },
        },
      ]}
      series={[
        {
          id: "buoys",
          label: "Ocean buoys",
          data: buoys,
          markerSize: 14,
          color: t.palette[0],
        },
      ]}
    >
      <ChartsText
        text={TITLE}
        x={width / 2}
        y={40}
        style={{
          fontSize: TITLE_FONTSIZE,
          fontWeight: 600,
          fill: t.ink,
          textAnchor: "middle",
          dominantBaseline: "hanging",
        }}
      />
      <ChartsText
        text="Sea-surface temp (°C)"
        x={width - 95}
        y={64}
        style={{
          fontSize: 14,
          fill: t.inkSoft,
          textAnchor: "middle",
          dominantBaseline: "hanging",
        }}
      />
      <ContinuousColorLegend
        axisDirection="z"
        direction="column"
        position={{ horizontal: "right", vertical: "middle" }}
        length="62%"
        thickness={22}
        spacing={10}
        align="middle"
        minLabel={({ value }) => `${Number(value).toFixed(1)}°C`}
        maxLabel={({ value }) => `${Number(value).toFixed(1)}°C`}
        labelStyle={{ fontSize: 16, fill: t.inkSoft }}
      />
    </ScatterChart>
  );
}
