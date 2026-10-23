// anyplot.ai
// horizon-basic: Horizon Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-20
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { AreaPlot } from "@mui/x-charts/LineChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// Constants
const OUTER_PAD = 32;
const LABEL_COL_WIDTH = 180;
const RIGHT_PAD = 16;
const CHART_WIDTH = SIZE.width - OUTER_PAD * 2 - LABEL_COL_WIDTH - RIGHT_PAD;
const ROW_HEIGHT = 70;
const HALF_HEIGHT = ROW_HEIGHT / 2;
const ROW_GAP = 10;
const BAND_COUNT = 3;
const ZERO_MARGIN = { top: 0, right: 0, bottom: 0, left: 0 };

// Columns: set these to your data's column names
const DATE = "Time"; // role: date
const VALUE = "Deviation from 24h rolling baseline, in percentage points (pp)"; // role: value
const SERIES = "Service"; // role: series

// Data: replace this block with your own records, one object per row
const data = (() => {
  const pointCount = 168;
  const maxDev = 45;
  const mulberry32 = (seed) => {
    let s = seed;
    return () => {
      s = (s + 0x6d2b79f5) | 0;
      let v = Math.imul(s ^ (s >>> 15), 1 | s);
      v = (v + Math.imul(v ^ (v >>> 7), 61 | v)) ^ v;
      return ((v ^ (v >>> 14)) >>> 0) / 4294967296;
    };
  };
  const servers = [
    { name: "api-gateway", amplitude: 22, phase: 0.0, walkScale: 6, seed: 1013 },
    { name: "auth-service", amplitude: 18, phase: 1.1, walkScale: 5, seed: 1069 },
    { name: "orders-db", amplitude: 30, phase: 2.4, walkScale: 9, seed: 1151 },
    { name: "inventory-db", amplitude: 26, phase: 0.6, walkScale: 8, seed: 1223 },
    { name: "redis-cache", amplitude: 15, phase: 3.0, walkScale: 4, seed: 1291 },
    { name: "search-index", amplitude: 20, phase: 1.8, walkScale: 6, seed: 1373 },
    { name: "payment-worker", amplitude: 35, phase: 0.3, walkScale: 10, seed: 1447 },
    { name: "email-worker", amplitude: 12, phase: 2.1, walkScale: 3, seed: 1523 },
  ];
  const rows = [];
  servers.forEach((server) => {
    const rand = mulberry32(server.seed);
    let walk = 0;
    for (let i = 0; i < pointCount; i += 1) {
      walk += (rand() - 0.5) * server.walkScale * 0.6 - walk * 0.15;
      const daily = server.amplitude * Math.sin((2 * Math.PI * i) / 24 + server.phase);
      const val = Math.max(-maxDev, Math.min(maxDev, daily + walk));
      const day = Math.floor(i / 24) + 1;
      const hour = i % 24;
      rows.push({
        [DATE]: `Day ${day} · ${String(hour).padStart(2, "0")}:00`,
        [SERIES]: server.name,
        [VALUE]: val,
      });
    }
  });
  return rows;
})();

// Plot: reads only data and the constants above
const seriesNames = [...new Set(data.map((d) => d[SERIES]))];
const dates = [...new Set(data.map((d) => d[DATE]))];
const pointCount = dates.length;
const xIndex = Array.from({ length: pointCount }, (_, i) => i);
const maxDeviation =
  Math.ceil(Math.max(...data.map((d) => Math.abs(d[VALUE]))) / 15) * 15 || 45;
const bandThresholds = Array.from({ length: BAND_COUNT }, (_, k) =>
  Math.round((maxDeviation * (k + 1)) / BAND_COUNT),
);

const seriesData = seriesNames.map((name) => {
  const values = data.filter((d) => d[SERIES] === name).map((d) => d[VALUE]);
  return {
    name,
    positive: values.map((v) => Math.max(v, 0)),
    negative: values.map((v) => Math.max(-v, 0)),
  };
});

const TITLE = "horizon-basic · javascript · muix · anyplot.ai";
const TITLE_FONT_SIZE = Math.round(22 * (TITLE.length > 67 ? 67 / TITLE.length : 1));

function mixHex(hexA, hexB, ratio) {
  const a = parseInt(hexA.slice(1), 16);
  const b = parseInt(hexB.slice(1), 16);
  const channel = (shift) => {
    const va = (a >> shift) & 255;
    const vb = (b >> shift) & 255;
    return Math.round(va + (vb - va) * ratio);
  };
  const [r, g, bl] = [16, 8, 0].map(channel);
  return `#${[r, g, bl].map((c) => c.toString(16).padStart(2, "0")).join("")}`;
}

function bandColors(pole) {
  return Array.from({ length: BAND_COUNT }, (_, k) => {
    const strength = 0.45 + 0.55 * ((k + 1) / BAND_COUNT);
    return mixHex(t.div[1], pole, strength);
  });
}

const POS_BAND_COLORS = bandColors(t.div[2]);
const NEG_BAND_COLORS = bandColors(t.div[0]);

function BandStack({ values, colors }) {
  return (
    <>
      {colors.map((color, bandIndex) => (
        <Box
          key={bandIndex}
          sx={{
            position: "absolute",
            left: 0,
            bottom: 0,
            width: CHART_WIDTH,
            height: HALF_HEIGHT * BAND_COUNT,
            transform: `translateY(${bandIndex * HALF_HEIGHT}px)`,
          }}
        >
          <ChartsContainer
            width={CHART_WIDTH}
            height={HALF_HEIGHT * BAND_COUNT}
            margin={ZERO_MARGIN}
            disableAxisListener
            skipAnimation
            series={[
              {
                type: "line",
                data: values,
                area: true,
                baseline: 0,
                curve: "monotoneX",
                color,
              },
            ]}
            xAxis={[
              {
                scaleType: "linear",
                data: xIndex,
                min: 0,
                max: pointCount - 1,
                domainLimit: "strict",
                position: "none",
              },
            ]}
            yAxis={[
              {
                scaleType: "linear",
                min: 0,
                max: maxDeviation,
                domainLimit: "strict",
                position: "none",
              },
            ]}
            sx={{ "& .MuiLineChart-area": { fill: color, fillOpacity: 1 } }}
          >
            <AreaPlot
              skipAnimation
              slotProps={{ area: { style: { fill: color, fillOpacity: 1 } } }}
            />
          </ChartsContainer>
        </Box>
      ))}
    </>
  );
}

function HorizonRow({ name, positive, negative }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", height: ROW_HEIGHT }}>
      <Box sx={{ width: LABEL_COL_WIDTH, pr: "14px", boxSizing: "border-box", textAlign: "right" }}>
        <Typography
          sx={{
            m: 0,
            fontSize: 17,
            fontWeight: 500,
            color: t.ink,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {name}
        </Typography>
      </Box>
      <Box sx={{ position: "relative", width: CHART_WIDTH, height: ROW_HEIGHT }}>
        <Box sx={{ position: "absolute", top: 0, left: 0, width: CHART_WIDTH, height: HALF_HEIGHT, overflow: "hidden" }}>
          <BandStack values={positive} colors={POS_BAND_COLORS} />
        </Box>
        <Box
          sx={{
            position: "absolute",
            top: HALF_HEIGHT,
            left: 0,
            width: CHART_WIDTH,
            height: HALF_HEIGHT,
            overflow: "hidden",
            transform: "scaleY(-1)",
          }}
        >
          <BandStack values={negative} colors={NEG_BAND_COLORS} />
        </Box>
        <Box sx={{ position: "absolute", top: HALF_HEIGHT, left: 0, width: CHART_WIDTH, height: "1px", bgcolor: t.grid }} />
      </Box>
    </Box>
  );
}

function LegendSwatches({ colors, thresholds, label, align }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: "6px", flexDirection: align === "left" ? "row-reverse" : "row" }}>
      <Typography sx={{ m: 0, fontSize: 13, color: t.inkSoft, whiteSpace: "nowrap" }}>{label}</Typography>
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "2px" }}>
        <Box sx={{ display: "flex", gap: "3px" }}>
          {colors.map((color, i) => (
            <Box key={i} sx={{ width: 14, height: 14, borderRadius: "3px", bgcolor: color }} />
          ))}
        </Box>
        <Box sx={{ display: "flex", gap: "3px" }}>
          {thresholds.map((th, i) => (
            <Typography key={i} sx={{ m: 0, fontSize: 11, color: t.inkSoft, width: 14, textAlign: "center", whiteSpace: "nowrap" }}>
              {th}
            </Typography>
          ))}
        </Box>
      </Box>
    </Box>
  );
}

const TICKS = [
  0,
  Math.round((pointCount - 1) / 4),
  Math.round((pointCount - 1) / 2),
  Math.round((3 * (pointCount - 1)) / 4),
  pointCount - 1,
];

export default function Chart() {
  return (
    <Box
      sx={{
        width: SIZE.width,
        height: SIZE.height,
        boxSizing: "border-box",
        p: `${OUTER_PAD}px`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
      }}
    >
      <Typography sx={{ m: 0, fontSize: TITLE_FONT_SIZE, fontWeight: 600, color: t.ink }}>{TITLE}</Typography>
      <Typography sx={{ m: 0, mb: "14px", fontSize: 14, color: t.inkSoft }}>
        {VALUE}
      </Typography>

      <Box sx={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "18px", mb: "20px" }}>
        <LegendSwatches
          label="Below baseline"
          colors={[...NEG_BAND_COLORS].reverse()}
          thresholds={[...bandThresholds].reverse()}
          align="left"
        />
        <Box sx={{ width: "1px", height: "16px", bgcolor: t.grid }} />
        <LegendSwatches label="Above baseline" colors={POS_BAND_COLORS} thresholds={bandThresholds} align="right" />
      </Box>

      <Box>
        {seriesData.map((series, i) => (
          <Box key={series.name} sx={{ mb: i === seriesData.length - 1 ? 0 : `${ROW_GAP}px` }}>
            <HorizonRow name={series.name} positive={series.positive} negative={series.negative} />
          </Box>
        ))}
      </Box>

      <Box sx={{ display: "flex", mt: "14px" }}>
        <Box sx={{ width: LABEL_COL_WIDTH, flexShrink: 0 }} />
        <Box sx={{ position: "relative", width: CHART_WIDTH, height: "18px" }}>
          {TICKS.map((index) => (
            <Typography
              key={index}
              component="span"
              sx={{
                m: 0,
                position: "absolute",
                left: `${(index / (pointCount - 1)) * 100}%`,
                transform: index === 0 ? "none" : index === pointCount - 1 ? "translateX(-100%)" : "translateX(-50%)",
                fontSize: 14,
                color: t.inkSoft,
                whiteSpace: "nowrap",
              }}
            >
              {dates[index]}
            </Typography>
          ))}
        </Box>
      </Box>
    </Box>
  );
}
