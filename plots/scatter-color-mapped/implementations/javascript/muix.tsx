// anyplot.ai
// scatter-color-mapped: Color-Mapped Scatter Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 82/100 | Updated: 2026-10-23

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const X = "Longitude (°E)"; // role: x
const Y = "Latitude (°N)"; // role: y
const COLOR = "Sea-surface temperature (°C)"; // role: color

// Data: replace this block with your own records, one object per row
// Ocean buoy network: sea-surface temperature sampled across a survey grid.
// A warm-core current near (0°E, 40°N) fades outward.
const data = (() => {
  let seed = 42;
  const nextRandom = () => {
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };

  const stationCount = 160;
  const rows: { [X]: number; [Y]: number; [COLOR]: number }[] = [];
  for (let i = 0; i < stationCount; i += 1) {
    const longitude = -14 + nextRandom() * 26;
    const latitude = 30 + nextRandom() * 22;
    const distanceFromCore = Math.hypot(longitude - 0, latitude - 40);
    const temperature = 23 - 0.42 * distanceFromCore + (nextRandom() - 0.5) * 2.4;
    rows.push({
      [X]: Number(longitude.toFixed(2)),
      [Y]: Number(latitude.toFixed(2)),
      [COLOR]: Number(temperature.toFixed(2)),
    });
  }
  return rows;
})();

// Plot: reads only data and the constants above
const buoys = data.map((row, i) => ({
  id: i,
  x: row[X],
  y: row[Y],
  z: row[COLOR],
}));

const temperatures = buoys.map((buoy) => buoy.z);
const tempMin = Number(Math.min(...temperatures).toFixed(1));
const tempMax = Number(Math.max(...temperatures).toFixed(1));

const withAlpha = (hex: string, alpha: number) => {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
const MARKER_ALPHA = 0.88;

const TITLE = "scatter-color-mapped · javascript · muix · anyplot.ai";

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const titleHeight = 64;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Typography
        sx={{
          color: t.ink,
          fontSize: 22,
          fontWeight: 600,
          textAlign: "center",
          lineHeight: 1.2,
          pt: "18px",
          height: titleHeight,
          fontFamily: "inherit",
        }}
      >
        {TITLE}
      </Typography>
      <Box sx={{ flex: 1, display: "flex", alignItems: "center", pr: "32px" }}>
        <ScatterChart
          width={width - 140}
          height={height - titleHeight}
          skipAnimation
          disableHitArea
          grid={{ horizontal: true, vertical: true }}
          margin={{ top: 24, right: 24, bottom: 24, left: 40 }}
          xAxis={[
            {
              id: "longitude",
              height: 68,
              label: X,
              labelStyle: { fontSize: 18, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              valueFormatter: (value: number) => `${value}°`,
            },
          ]}
          yAxis={[
            {
              id: "latitude",
              width: 84,
              label: Y,
              labelStyle: { fontSize: 18, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              valueFormatter: (value: number) => `${value}°`,
            },
          ]}
          zAxis={[
            {
              id: "temperature",
              min: tempMin,
              max: tempMax,
              valueFormatter: (v: number) => `${Number(v).toFixed(1)}°C`,
              colorMap: {
                type: "continuous",
                min: tempMin,
                max: tempMax,
                color: [withAlpha(t.seq[0], MARKER_ALPHA), withAlpha(t.seq[1], MARKER_ALPHA)],
              },
            },
          ]}
          series={[
            {
              id: "buoys",
              label: "Ocean buoys",
              data: buoys,
              markerSize: 9,
              zAxisId: "temperature",
              color: t.palette[0],
            },
          ]}
          slots={{ legend: ContinuousColorLegend }}
          slotProps={{
            legend: {
              axisId: "temperature",
              axisDirection: "z",
              direction: "vertical",
              position: { vertical: "middle", horizontal: "end" },
              thickness: 18,
              sx: {
                height: "65%",
                color: t.inkSoft,
                fontSize: 15,
                fontFamily: "inherit",
              },
            } as any,
          }}
          sx={{
            "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          }}
        />
        <Typography
          sx={{
            writingMode: "vertical-rl",
            transform: "rotate(180deg)",
            color: t.ink,
            fontSize: 16,
            fontWeight: 500,
            ml: "8px",
            fontFamily: "inherit",
          }}
        >
          {COLOR}
        </Typography>
      </Box>
    </Box>
  );
}
