// anyplot.ai
// horizon-basic: Horizon Chart
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 82/100 | Updated: 2026-10-23
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
const SWATCH_WIDTH = 24;

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
  const bump = (i, center, width) => Math.exp(-(((i - center) / width) ** 2));
  const daily = (i, phase) => Math.sin((2 * Math.PI * i) / 24 + phase);
  // Each service has its own load profile: i = hour since start, d = day index (0-6)
  const servers = [
    // Business-hours traffic, quieter at the weekend
    { name: "api-gateway", noise: 5, seed: 1013, shape: (i, d) => (d >= 5 ? 9 : 20) * daily(i, -1.9) },
    // Quiet all week until a login storm on Day 3 morning
    { name: "auth-service", noise: 3, seed: 1069, shape: (i) => 4 * daily(i, -1.9) + 40 * bump(i, 57, 2.5) },
    // Evening order peaks that grow toward the weekend
    { name: "orders-db", noise: 6, seed: 1151, shape: (i, d) => (14 + 4 * d) * daily(i, -2.8) },
    // Slow drift across the week plus a nightly 02:00 batch job
    {
      name: "inventory-db",
      noise: 4,
      seed: 1223,
      shape: (i, d) => -22 + (44 * i) / 167 + 16 * bump(i % 24, 2, 1.2) * (d < 5 ? 1 : 0.4),
    },
    // Flat, then a cache flush on Day 5 that drops the hit rate
    { name: "redis-cache", noise: 2.5, seed: 1291, shape: (i) => -42 * bump(i, 106, 3) * (i >= 103 ? 1 : 0.4) },
    // Nightly re-index bursts, slightly under baseline during the day
    { name: "search-index", noise: 3, seed: 1373, shape: (i) => -7 + 34 * bump(i % 24, 4, 1.4) },
    // Strong daily cycle, an outage on Day 4 afternoon and the backlog surge after it
    {
      name: "payment-worker",
      noise: 5,
      seed: 1447,
      shape: (i) => 18 * daily(i, -2.2) - 60 * bump(i, 87, 2) + 52 * bump(i, 93, 2.5),
    },
    // Near idle except two newsletter sends at 09:00
    { name: "email-worker", noise: 2, seed: 1523, shape: (i) => -3 + 30 * bump(i, 33, 1.5) + 36 * bump(i, 129, 1.5) },
  ];
  const rows = [];
  servers.forEach((server) => {
    const rand = mulberry32(server.seed);
    let walk = 0;
    for (let i = 0; i < pointCount; i += 1) {
      const day = Math.floor(i / 24);
      walk += (rand() - 0.5) * server.noise - walk * 0.3;
      const val = Math.max(-maxDev, Math.min(maxDev, server.shape(i, day) + walk));
      rows.push({
        [DATE]: `Day ${day + 1} · ${String(i % 24).padStart(2, "0")}:00`,
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

// Band colors: each step mixes the theme-adaptive diverging midpoint toward a pole
const mid = parseInt(t.div[1].slice(1), 16);
const [POS_BAND_COLORS, NEG_BAND_COLORS] = [t.div[2], t.div[0]].map((poleHex) => {
  const pole = parseInt(poleHex.slice(1), 16);
  return Array.from({ length: BAND_COUNT }, (_, k) => {
    const strength = 0.45 + 0.55 * ((k + 1) / BAND_COUNT);
    const rgb = [16, 8, 0].map((shift) => {
      const from = (mid >> shift) & 255;
      const to = (pole >> shift) & 255;
      return Math.round(from + (to - from) * strength);
    });
    return `#${rgb.map((c) => c.toString(16).padStart(2, "0")).join("")}`;
  });
});

// Top half folds positive values upward; bottom half mirrors negatives downward
const HALVES = [
  { key: "positive", colors: POS_BAND_COLORS, top: 0, transform: "none" },
  { key: "negative", colors: NEG_BAND_COLORS, top: HALF_HEIGHT, transform: "scaleY(-1)" },
];

const LEGEND = [
  {
    label: "Below baseline",
    colors: [...NEG_BAND_COLORS].reverse(),
    thresholds: [...bandThresholds].reverse(),
    direction: "row-reverse",
  },
  { label: "Above baseline", colors: POS_BAND_COLORS, thresholds: bandThresholds, direction: "row" },
];

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
      <Typography sx={{ m: 0, mb: "10px", fontSize: 14, color: t.inkSoft }}>
        {VALUE}
      </Typography>

      <Box sx={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "20px", mb: "14px" }}>
        {LEGEND.map((entry, entryIndex) => (
          <Box key={entry.label} sx={{ display: "flex", alignItems: "center", gap: "20px" }}>
            {entryIndex > 0 && <Box sx={{ width: "1px", height: "20px", bgcolor: t.grid }} />}
            <Box sx={{ display: "flex", alignItems: "center", gap: "8px", flexDirection: entry.direction }}>
              <Typography sx={{ m: 0, fontSize: 15, color: t.inkSoft, whiteSpace: "nowrap" }}>{entry.label}</Typography>
              <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "2px" }}>
                <Box sx={{ display: "flex", gap: "3px" }}>
                  {entry.colors.map((color) => (
                    <Box key={color} sx={{ width: SWATCH_WIDTH, height: 14, borderRadius: "3px", bgcolor: color }} />
                  ))}
                </Box>
                <Box sx={{ display: "flex", gap: "3px" }}>
                  {entry.thresholds.map((threshold) => (
                    <Typography
                      key={threshold}
                      sx={{ m: 0, fontSize: 14, color: t.inkSoft, width: SWATCH_WIDTH, textAlign: "center", whiteSpace: "nowrap" }}
                    >
                      {threshold}
                    </Typography>
                  ))}
                </Box>
              </Box>
            </Box>
          </Box>
        ))}
      </Box>

      <Box>
        {seriesData.map((series, rowIndex) => (
          <Box
            key={series.name}
            sx={{
              display: "flex",
              alignItems: "center",
              height: ROW_HEIGHT,
              mb: rowIndex === seriesData.length - 1 ? 0 : `${ROW_GAP}px`,
            }}
          >
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
                {series.name}
              </Typography>
            </Box>
            <Box sx={{ position: "relative", width: CHART_WIDTH, height: ROW_HEIGHT }}>
              {HALVES.map((half) => (
                <Box
                  key={half.key}
                  sx={{
                    position: "absolute",
                    top: half.top,
                    left: 0,
                    width: CHART_WIDTH,
                    height: HALF_HEIGHT,
                    overflow: "hidden",
                    transform: half.transform,
                  }}
                >
                  {/* Each band shares the 0–max domain, shifted down one band height and clipped */}
                  {half.colors.map((color, bandIndex) => (
                    <Box
                      key={color}
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
                            data: series[half.key],
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
                        <AreaPlot skipAnimation slotProps={{ area: { style: { fill: color, fillOpacity: 1 } } }} />
                      </ChartsContainer>
                    </Box>
                  ))}
                </Box>
              ))}
              <Box sx={{ position: "absolute", top: HALF_HEIGHT, left: 0, width: CHART_WIDTH, height: "1px", bgcolor: t.grid }} />
            </Box>
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
