// anyplot.ai
// line-win-probability: Win Probability Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const EVEN = 0.5; // even odds: the reference line and the boundary between the two team fills
const PROB_TICKS = [0, 0.25, 0.5, 0.75, 1]; // the full probability domain
const PERIOD_LENGTH = 45; // minutes per half of a football match; a marker is drawn at every period end inside the game
const PERIOD_LABEL = "Half time";

// Columns: set these to your data's column names
const MINUTE = "Match time (min)"; // role: game_time
const WIN_PROB = "Home win probability"; // role: win_probability
const EVENT = "Event"; // role: event
const HOME = "Harwick Town"; // role: extra
const AWAY = "Millbrook Rovers"; // role: extra

// Data: replace this block with your own records, one object per row
// Minute-by-minute model probability of a home win in a 90-minute match, with the running score
// of each team: the away side scores early, the home side equalises and wins it late.
const data = (() => {
  let s = 42;
  const rand = () => {
    s = (Math.imul(1664525, s) + 1013904223) | 0;
    return (s >>> 0) / 0x100000000;
  };
  const fullTime = 90;
  const goals = {
    19: { side: "away", wp: 0.26, scorer: "Lindqvist" },
    58: { side: "home", wp: 0.54, scorer: "Okafor" },
    84: { side: "home", wp: 0.88, scorer: "Mensah" },
  };
  // The range the model moves in at each score (home-away)
  const bands = { "0-0": [0.05, 0.95], "0-1": [0.11, 0.5], "1-1": [0.42, 0.67], "2-1": [0.81, 0.97] };
  let wp = 0.5;
  let home = 0;
  let away = 0;
  return Array.from({ length: fullTime + 1 }, (_, minute) => {
    const goal = goals[minute];
    const left = fullTime - minute;
    if (goal) {
      if (goal.side === "home") home += 1;
      else away += 1;
      wp = goal.wp;
    } else if (left === 0) {
      wp = home > away ? 1 : 0; // the final whistle settles it: a draw is not a home win
    } else if (minute > 0) {
      // Swings and the pull towards even odds shrink with the time left, and a lead firms up towards its result
      const [lo, hi] = bands[`${home}-${away}`];
      const share = left / fullTime;
      const lead = Math.sign(home - away);
      const firming = lead === 0 ? 0 : ((lead > 0 ? 1 : 0) - wp) / (left + 1);
      const next = wp + (rand() - 0.5) * 0.055 * Math.sqrt(share) + (0.5 - wp) * 0.018 * share + firming;
      wp = Math.max(lead < 0 ? 0 : lo, Math.min(lead > 0 ? 1 : hi, next));
    }
    return {
      [MINUTE]: minute,
      [WIN_PROB]: Math.round(wp * 1000) / 1000,
      [EVENT]: goal ? `Goal · ${goal.scorer}` : null,
      [HOME]: home,
      [AWAY]: away,
    };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[MINUTE] - b[MINUTE]);
const last = rows[rows.length - 1];
const xMin = rows[0][MINUTE];
const xMax = last[MINUTE];

// Where the line crosses even odds, a point at exactly EVEN is inserted, so each team's fill ends at the crossing
const points = [];
rows.forEach((d, i) => {
  const prev = rows[i - 1];
  if (prev && prev[WIN_PROB] != null && d[WIN_PROB] != null) {
    const da = prev[WIN_PROB] - EVEN;
    const db = d[WIN_PROB] - EVEN;
    if (da * db < 0) points.push({ x: prev[MINUTE] + (da / (da - db)) * (d[MINUTE] - prev[MINUTE]), p: EVEN });
  }
  points.push({ x: d[MINUTE], p: d[WIN_PROB] });
});
const xs = points.map((p) => p.x);
const homeAhead = points.map((p) => (p.p != null && p.p >= EVEN ? p.p : null));
const awayAhead = points.map((p) => (p.p != null && p.p <= EVEN ? p.p : null));

const HOME_COLOR = t.palette[0];
const AWAY_COLOR = t.palette[1];

// An event takes the colour of the team whose score rose on its row; its label sits left of the swing,
// at the new level, where the line arrives from the level before the event
const events = rows
  .map((d, i) => ({ d, prev: rows[i - 1] ?? d }))
  .filter(({ d }) => d[EVENT] != null && d[WIN_PROB] != null)
  .map(({ d, prev }) => ({
    x: d[MINUTE],
    p: d[WIN_PROB],
    color: d[HOME] > prev[HOME] ? HOME_COLOR : d[AWAY] > prev[AWAY] ? AWAY_COLOR : t.inkSoft,
    text: `${d[MINUTE]}' ${d[EVENT]} (${d[HOME]}–${d[AWAY]})`,
  }));
const periodEnds = Array.from({ length: Math.ceil(xMax / PERIOD_LENGTH) }, (_, k) => (k + 1) * PERIOD_LENGTH).filter(
  (m) => m > xMin && m < xMax,
);

const TITLE = "line-win-probability · javascript · muix · anyplot.ai";
const SUBTITLE = `Final score: ${HOME} ${last[HOME]} – ${last[AWAY]} ${AWAY} · ${rows.length} model updates over ${xMax - xMin} minutes`;
const HEADER_H = 80;
const LEGEND_H = 44;

function EventMarks() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {events.map((e) => (
        <g key={e.text}>
          <circle cx={xScale(e.x)} cy={yScale(e.p)} r={7} fill={e.color} stroke={t.pageBg} strokeWidth={2.5} />
          <text
            x={xScale(e.x) - 16}
            y={yScale(e.p)}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize={15}
            fontWeight={600}
            fill={t.ink}
          >
            {e.text}
          </text>
        </g>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 112px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: xs,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            tickNumber: 7,
            valueFormatter: (v: number) => `${Math.round(v)}'`,
            label: MINUTE,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: PROB_TICKS[0],
            max: PROB_TICKS[PROB_TICKS.length - 1],
            tickInterval: PROB_TICKS,
            valueFormatter: (v: number) => `${Math.round(v * 100)}%`,
            label: WIN_PROB,
            width: 84,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "home",
            data: homeAhead,
            label: `${HOME} (home) ahead`,
            color: HOME_COLOR,
            area: true,
            baseline: EVEN,
            curve: "linear",
            showMark: false,
            valueFormatter: (v: number | null) => (v == null ? "" : `${(v * 100).toFixed(1)}%`),
          },
          {
            id: "away",
            data: awayAhead,
            label: `${AWAY} (away) ahead`,
            color: AWAY_COLOR,
            area: true,
            baseline: EVEN,
            curve: "linear",
            showMark: false,
            valueFormatter: (v: number | null) => (v == null ? "" : `${(v * 100).toFixed(1)}%`),
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 16, color: t.ink, columnGap: 3, pr: 5 },
          },
        }}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.32 },
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        {periodEnds.map((m) => (
          <ChartsReferenceLine
            key={m}
            x={m}
            label={PERIOD_LABEL}
            labelAlign="start"
            spacing={{ x: 8, y: 8 }}
            labelStyle={{ fontSize: 15, fill: t.inkSoft }}
            lineStyle={{ stroke: t.inkSoft, strokeDasharray: "4 4", strokeWidth: 1.5 }}
          />
        ))}
        <ChartsReferenceLine y={EVEN} lineStyle={{ stroke: t.inkSoft, strokeWidth: 2.5 }} />
        <EventMarks />
      </LineChart>
    </div>
  );
}
