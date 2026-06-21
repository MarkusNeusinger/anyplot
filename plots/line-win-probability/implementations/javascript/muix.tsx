//# anyplot-orientation: landscape
// anyplot.ai
// line-win-probability: Win Probability Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-21

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG for reproducible match simulation
function lcg(seed: number): () => number {
  let s = seed | 0;
  return () => {
    s = (Math.imul(1664525, s) + 1013904223) | 0;
    return (s >>> 0) / 0x100000000;
  };
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

const rand = lcg(42);
const TOTAL_MINUTES = 90;

// Key event times
const AWAY_GOAL = 19;
const HALF_TIME = 45;
const HOME_GOAL_EQ = 58;
const HOME_GOAL_WIN = 84;

// Generate match win probability: Forest Green FC (home) vs City Blue FC (away)
// Scenario: Away scores early, home fights back with two second-half goals
const minutes: number[] = Array.from({ length: TOTAL_MINUTES + 1 }, (_, i) => i);

let wp = 0.50;
const winProb: number[] = [0.50];

for (let i = 1; i <= TOTAL_MINUTES; i++) {
  if (i === AWAY_GOAL) {
    wp = 0.26; // sharp drop — away goal
  } else if (i === HOME_GOAL_EQ) {
    wp = 0.54; // equaliser — back to level
  } else if (i === HOME_GOAL_WIN) {
    wp = 0.88; // winner — home dominant
  } else {
    const noise = (rand() - 0.5) * 0.055;
    const revert = (0.5 - wp) * 0.018;
    wp = clamp(wp + noise + revert, 0.05, 0.95);
    // Phase-specific range constraints
    if (i > AWAY_GOAL && i < HOME_GOAL_EQ) {
      wp = clamp(wp, 0.11, 0.50); // away leading phase
    } else if (i > HOME_GOAL_EQ && i < HOME_GOAL_WIN) {
      wp = clamp(wp, 0.42, 0.67); // closely contested phase
    } else if (i > HOME_GOAL_WIN) {
      wp = clamp(wp, 0.81, 0.97); // home sealing the win
    }
  }
  winProb.push(Math.round(wp * 1000) / 1000);
}

// Away win probability is the complement — stacked together they sum to 1
const awayProb: number[] = winProb.map(v => Math.round((1 - v) * 1000) / 1000);

// Imprint palette — first series is always #009E73 (home/brand green)
const HOME_COLOR = t.palette[0]; // #009E73
const AWAY_COLOR = t.palette[2]; // #4467A3

const TITLE = "line-win-probability · javascript · muix · anyplot.ai";
const SUBTITLE = "Forest Green FC 2 – 1 City Blue FC · 90 minutes";

const TITLE_HEIGHT = 68; // CSS px reserved for title + subtitle

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT;

  return (
    <Box
      sx={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        bgcolor: t.pageBg,
      }}
    >
      {/* Title block */}
      <Box sx={{ textAlign: "center", pt: 1.5 }}>
        <Typography
          sx={{ fontSize: 18, fontWeight: 500, color: t.ink, lineHeight: 1.3 }}
        >
          {TITLE}
        </Typography>
        <Typography sx={{ fontSize: 13, color: t.inkSoft, mt: 0.25 }}>
          {SUBTITLE}
        </Typography>
      </Box>

      {/* Stacked area chart: home probability (bottom) + away probability (top) */}
      <LineChart
        width={width}
        height={chartHeight}
        skipAnimation
        xAxis={[
          {
            data: minutes,
            label: "Match Time (minutes)",
            min: 0,
            max: 90,
            tickNumber: 7,
            valueFormatter: (v: number) => `${v}'`,
            labelStyle: { fontSize: 14, fill: t.inkSoft },
            tickLabelStyle: { fontSize: 12, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: 1,
            tickNumber: 5,
            valueFormatter: (v: number) => `${Math.round(v * 100)}%`,
            label: "Home Win Probability",
            labelStyle: { fontSize: 14, fill: t.inkSoft },
            tickLabelStyle: { fontSize: 12, fill: t.inkSoft },
          },
        ]}
        series={[
          {
            id: "home",
            data: winProb,
            label: "Home Win — Forest Green FC",
            area: true,
            stack: "prob",
            showMark: false,
            color: HOME_COLOR,
          },
          {
            id: "away",
            data: awayProb,
            label: "Away Win — City Blue FC",
            area: true,
            stack: "prob",
            showMark: false,
            color: AWAY_COLOR,
          },
        ]}
        margin={{ top: 16, bottom: 64, left: 96, right: 48 }}
        sx={{
          bgcolor: "transparent",
          // Hide the constant y=1 line that sits at the top of the stacked away series
          "& .MuiLineElement-series-away": { display: "none" },
          "& .MuiAreaElement-series-home": { fillOpacity: 0.82 },
          "& .MuiAreaElement-series-away": { fillOpacity: 0.82 },
          // Win-probability boundary line (series-home) — make it prominent
          "& .MuiLineElement-series-home": { strokeWidth: 2.5 },
        }}
        slotProps={{
          legend: {
            position: { vertical: "top", horizontal: "right" },
            padding: { top: 8, right: 12 },
            itemMarkWidth: 14,
            itemMarkHeight: 14,
            labelStyle: { fontSize: 12, fill: t.inkSoft },
          },
        }}
      >
        {/* 50% neutral baseline — marks "even odds" */}
        <ChartsReferenceLine
          y={0.5}
          label="50% — even odds"
          labelAlign="end"
          lineStyle={{
            stroke: t.ink,
            strokeWidth: 1.5,
            strokeDasharray: "8 4",
            opacity: 0.45,
          }}
          labelStyle={{ fontSize: 11, fill: t.inkSoft }}
        />

        {/* Away goal — probability falls */}
        <ChartsReferenceLine
          x={AWAY_GOAL}
          label={`Goal (Away) ${AWAY_GOAL}'`}
          labelAlign="start"
          lineStyle={{
            stroke: AWAY_COLOR,
            strokeWidth: 1.5,
            strokeDasharray: "5 3",
            opacity: 0.75,
          }}
          labelStyle={{ fontSize: 10, fill: t.inkSoft }}
        />

        {/* Half time marker */}
        <ChartsReferenceLine
          x={HALF_TIME}
          label="Half Time"
          labelAlign="start"
          lineStyle={{
            stroke: t.ink,
            strokeWidth: 1,
            strokeDasharray: "4 3",
            opacity: 0.3,
          }}
          labelStyle={{ fontSize: 10, fill: t.inkSoft }}
        />

        {/* Home equaliser */}
        <ChartsReferenceLine
          x={HOME_GOAL_EQ}
          label={`Goal (Home) ${HOME_GOAL_EQ}'`}
          labelAlign="start"
          lineStyle={{
            stroke: HOME_COLOR,
            strokeWidth: 1.5,
            strokeDasharray: "5 3",
            opacity: 0.75,
          }}
          labelStyle={{ fontSize: 10, fill: t.inkSoft }}
        />

        {/* Home winner */}
        <ChartsReferenceLine
          x={HOME_GOAL_WIN}
          label={`Goal (Home) ${HOME_GOAL_WIN}'`}
          labelAlign="end"
          lineStyle={{
            stroke: HOME_COLOR,
            strokeWidth: 1.5,
            strokeDasharray: "5 3",
            opacity: 0.75,
          }}
          labelStyle={{ fontSize: 10, fill: t.inkSoft }}
        />
      </LineChart>
    </Box>
  );
}
