// anyplot.ai
// titration-curve: Acid-Base Titration Curve
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const PH_MIN = 0; // the full pH scale the y axis spans
const PH_MAX = 14;
const DERIV_HEADROOM = 0.25; // share of the derivative peak left free above it on the right axis
const TITLE = "titration-curve · javascript · muix · anyplot.ai";
const TITLE_H = 76;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const VOLUME = "Volume of NaOH added (mL)"; // role: volume_ml
const PH = "pH"; // role: ph

// Data: replace this block with your own records, one object per row
// 25 mL of 0.1 M HCl titrated with 0.1 M NaOH, 201 readings from 0 to 50 mL.
// pH from the exact charge balance [H+] - [OH-] = excess acid, with Kw = 1e-14.
const data = (() => {
  const acidVolume = 25;
  const acidMolarity = 0.1;
  const baseMolarity = 0.1;
  const readings = 201;
  const maxVolume = 50;
  const kw = 1e-14;
  return Array.from({ length: readings }, (_, i) => {
    const volume = (i / (readings - 1)) * maxVolume;
    const excess = (acidMolarity * acidVolume - baseMolarity * volume) / (acidVolume + volume);
    const root = Math.sqrt(excess * excess + 4 * kw);
    const hydrogen = excess >= 0 ? (excess + root) / 2 : kw / ((root - excess) / 2);
    return {
      [VOLUME]: Math.round(volume * 100) / 100,
      [PH]: Math.round(-Math.log10(hydrogen) * 1000) / 1000,
    };
  });
})();

// Plot: reads only data and the constants above
const rows = data
  .filter((d) => d[VOLUME] != null && d[PH] != null)
  .sort((a, b) => a[VOLUME] - b[VOLUME]);
const volumes = rows.map((d) => d[VOLUME]);
const phValues = rows.map((d) => d[PH]);

// dpH/dV by central differences, one-sided at the two ends
const derivative = rows.map((_, i) => {
  const lo = Math.max(0, i - 1);
  const hi = Math.min(rows.length - 1, i + 1);
  const dv = volumes[hi] - volumes[lo];
  return dv === 0 ? null : (phValues[hi] - phValues[lo]) / dv;
});

// Equivalence point: the reading where the derivative peaks
const eqIndex = derivative.reduce(
  (best, v, i) => (v != null && v > (derivative[best] ?? -Infinity) ? i : best),
  0,
);
const eqVolume = volumes[eqIndex];
const eqPh = phValues[eqIndex];
const derivPeak = derivative[eqIndex];

const VOLUME_UNIT = VOLUME.match(/\(([^)]+)\)\s*$/)?.[1] ?? "";
const DERIV_NAME = `d${PH}/dV`;
const DERIV_LABEL = `${DERIV_NAME}${VOLUME_UNIT ? ` (per ${VOLUME_UNIT})` : ""}`;
const EQ_LABEL = `Equivalence point · ${eqVolume.toFixed(2)} ${VOLUME_UNIT}, ${PH} ${eqPh.toFixed(2)}`;
const SUBTITLE = `${rows.length} readings, ${volumes[0]}–${volumes[volumes.length - 1]} ${VOLUME_UNIT} of titrant · equivalence at the ${DERIV_NAME} maximum`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, px: "40px", pt: "16px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>

      <LineChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        colors={t.palette}
        grid={{ horizontal: true }}
        xAxis={[
          {
            id: "volume",
            data: volumes,
            scaleType: "linear",
            domainLimit: "nice",
            tickNumber: 10,
            label: VOLUME,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "ph",
            min: PH_MIN,
            max: PH_MAX,
            tickNumber: 8,
            label: PH,
            width: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
          {
            id: "deriv",
            position: "right",
            min: 0,
            max: derivPeak * (1 + DERIV_HEADROOM),
            label: DERIV_LABEL,
            width: 80,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "ph",
            data: phValues,
            label: PH,
            yAxisId: "ph",
            showMark: false,
            curve: "monotoneX",
          },
          {
            id: "deriv",
            data: derivative,
            label: DERIV_LABEL,
            yAxisId: "deriv",
            showMark: false,
            curve: "linear",
            area: true,
          },
        ]}
        margin={{ top: 16, right: 24, bottom: 12, left: 24 }}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 16, color: t.ink },
          },
        }}
        sx={{
          '& .MuiLineChart-line[data-series="ph"]': { strokeWidth: 3.5 },
          '& .MuiLineChart-line[data-series="deriv"]': { strokeWidth: 2 },
          '& .MuiLineChart-area[data-series="deriv"]': { fillOpacity: 0.15 },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsReferenceLine
          x={eqVolume}
          axisId="volume"
          label={EQ_LABEL}
          labelAlign="start"
          spacing={{ x: 10, y: 10 }}
          lineStyle={{ strokeDasharray: "8 5", stroke: t.inkSoft, strokeWidth: 1.5 }}
          labelStyle={{ fontSize: 15, fill: t.ink, fontWeight: 500 }}
        />
      </LineChart>
    </Box>
  );
}
