// anyplot.ai
// histogram-epidemic: Epidemic Curve (Epi Curve)
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-08-26

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, sans-serif";

// Constants
const ONSET_DATE_COL = "onset_date";
const CASE_TYPE_COL = "case_type";
const CASE_COUNT_COL = "case_count";
const EVENT_LABEL_COL = "event_label";

const Y_HEADROOM_RATIO = 0.14;

// Data
type EpiRow = {
  [ONSET_DATE_COL]: string;
  [CASE_TYPE_COL]: string;
  [CASE_COUNT_COL]: number;
  [EVENT_LABEL_COL]: string;
};

const DATA: EpiRow[] = [];
let seed = 42;
const dayCount = 63;
const startDate = new Date(2024, 0, 1);
const eventByDayIndex: Record<number, string> = {
  20: "Lockdown start",
  45: "Vaccination campaign",
};

const rawDailyTotals: number[] = [];
for (let day = 0; day < dayCount; day++) {
  const z1 = (day - 14) / 5;
  const wave1 = 46 * Math.exp(-0.5 * z1 * z1);
  const z2 = (day - 39) / 8;
  const wave2 = 30 * Math.exp(-0.5 * z2 * z2);
  seed = (seed * 1103515245 + 12345) % 2147483648;
  const noise = (seed / 2147483648 - 0.5) * 6;
  rawDailyTotals.push(Math.max(0, Math.round(wave1 + wave2 + noise)));
}

const rawConfirmed: number[] = [];
for (let day = 0; day < dayCount; day++) {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  const frac = 0.55 + (seed / 2147483648) * 0.1;
  rawConfirmed.push(Math.round(rawDailyTotals[day] * frac));
}

const rawProbable: number[] = [];
for (let day = 0; day < dayCount; day++) {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  const frac = 0.55 + (seed / 2147483648) * 0.1;
  rawProbable.push(
    Math.round((rawDailyTotals[day] - rawConfirmed[day]) * frac),
  );
}

for (let day = 0; day < dayCount; day++) {
  const d = new Date(startDate);
  d.setDate(d.getDate() + day);
  const dateLabel = d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  const ev = eventByDayIndex[day] ?? "";
  const conf = rawConfirmed[day];
  const prob = rawProbable[day];
  const susp = Math.max(0, rawDailyTotals[day] - conf - prob);

  DATA.push(
    {
      [ONSET_DATE_COL]: dateLabel,
      [CASE_TYPE_COL]: "Confirmed",
      [CASE_COUNT_COL]: conf,
      [EVENT_LABEL_COL]: ev,
    },
    {
      [ONSET_DATE_COL]: dateLabel,
      [CASE_TYPE_COL]: "Probable",
      [CASE_COUNT_COL]: prob,
      [EVENT_LABEL_COL]: ev,
    },
    {
      [ONSET_DATE_COL]: dateLabel,
      [CASE_TYPE_COL]: "Suspect",
      [CASE_COUNT_COL]: susp,
      [EVENT_LABEL_COL]: ev,
    },
  );
}

const onsetDates: string[] = [];
const caseTypes: string[] = [];
const eventsByDate = new Map<string, string>();

for (const row of DATA) {
  const dt = row[ONSET_DATE_COL];
  const ct = row[CASE_TYPE_COL];
  if (!onsetDates.includes(dt)) onsetDates.push(dt);
  if (!caseTypes.includes(ct)) caseTypes.push(ct);
  if (row[EVENT_LABEL_COL] && !eventsByDate.has(dt)) {
    eventsByDate.set(dt, row[EVENT_LABEL_COL]);
  }
}

const countLookup = new Map<string, number>();
for (const row of DATA) {
  const key = `${row[ONSET_DATE_COL]}__${row[CASE_TYPE_COL]}`;
  countLookup.set(key, (countLookup.get(key) ?? 0) + row[CASE_COUNT_COL]);
}

const dailyTotals = onsetDates.map((dt) =>
  caseTypes.reduce(
    (sum, ct) => sum + (countLookup.get(`${dt}__${ct}`) ?? 0),
    0,
  ),
);

const cumulativeCases: number[] = [];
for (const tot of dailyTotals) {
  cumulativeCases.push(
    (cumulativeCases.length ? cumulativeCases[cumulativeCases.length - 1] : 0) +
      tot,
  );
}

const maxDaily = Math.ceil(Math.max(...dailyTotals) * (1 + Y_HEADROOM_RATIO));
const maxCumulative = Math.ceil(
  (cumulativeCases[cumulativeCases.length - 1] ?? 1) * (1 + Y_HEADROOM_RATIO * 0.5),
);

const barSeries = caseTypes.map((ct, idx) => ({
  type: "bar" as const,
  id: `bar-${ct}`,
  xAxisId: "onset",
  yAxisId: "daily",
  stack: "cases",
  data: onsetDates.map((dt) => countLookup.get(`${dt}__${ct}`) ?? 0),
  label: ct,
  color: t.palette[idx],
}));

const series = [
  ...barSeries,
  {
    type: "line" as const,
    id: "cumulative-line",
    xAxisId: "onset",
    yAxisId: "cumulative",
    data: cumulativeCases,
    label: "Cumulative cases",
    color: t.ink,
    curve: "monotoneX" as const,
    showMark: false,
  },
];

const totalOutbreakCases = cumulativeCases[cumulativeCases.length - 1] ?? 0;
const peakDaily = Math.max(...dailyTotals);
const peakDate = onsetDates[dailyTotals.indexOf(peakDaily)] ?? "";

const TITLE = "histogram-epidemic · javascript · muix · anyplot.ai";
const SUBTITLE = `${onsetDates.length}-day propagated outbreak (${onsetDates[0]}–${onsetDates[onsetDates.length - 1]}) · Total ${totalOutbreakCases.toLocaleString("en-US")} cases, peak ${peakDaily}/day on ${peakDate}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const HEADER_H = 112;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <Box sx={{ pt: "14px", px: "40px", textAlign: "center" }}>
        <Typography
          sx={{
            fontSize: 22,
            fontWeight: 600,
            color: t.ink,
            lineHeight: 1.2,
            fontFamily: FONT,
          }}
        >
          {TITLE}
        </Typography>
        <Typography
          sx={{
            fontSize: 15,
            fontWeight: 400,
            color: t.inkSoft,
            mt: "4px",
            lineHeight: 1.2,
            fontFamily: FONT,
          }}
        >
          {SUBTITLE}
        </Typography>
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: "28px",
            mt: "10px",
          }}
        >
          {caseTypes.map((ct, idx) => (
            <Box
              key={ct}
              sx={{ display: "flex", alignItems: "center", gap: "8px" }}
            >
              <Box
                sx={{
                  width: 16,
                  height: 14,
                  borderRadius: "2px",
                  bgcolor: t.palette[idx],
                }}
              />
              <Typography
                sx={{
                  fontSize: 14,
                  fontWeight: 600,
                  color: t.ink,
                  fontFamily: FONT,
                }}
              >
                {ct}
              </Typography>
            </Box>
          ))}
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box sx={{ width: 22, height: 3, bgcolor: t.ink }} />
            <Typography
              sx={{
                fontSize: 14,
                fontWeight: 600,
                color: t.ink,
                fontFamily: FONT,
              }}
            >
              Cumulative cases (right axis)
            </Typography>
          </Box>
        </Box>
      </Box>

      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        series={series}
        xAxis={[
          {
            id: "onset",
            scaleType: "band",
            data: onsetDates,
            categoryGapRatio: 0.04,
            height: 60,
            label: "Symptom Onset Date",
            tickLabelInterval: (_value: string, index: number) =>
              index % 7 === 0,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "daily",
            position: "left",
            min: 0,
            max: maxDaily,
            width: 80,
            label: "Daily New Cases",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
          {
            id: "cumulative",
            position: "right",
            min: 0,
            max: maxCumulative,
            width: 92,
            label: "Cumulative Cases",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
          },
        ]}
        margin={{ top: 20, right: 24, bottom: 20, left: 24 }}
        skipAnimation
      >
        <ChartsGrid
          horizontal
          sx={{ "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 } }}
        />
        <BarPlot skipAnimation />
        <LinePlot
          skipAnimation
          slotProps={{ line: { sx: { strokeWidth: 3 } } }}
        />
        <ChartsXAxis
          axisId="onset"
          sx={{ "& .MuiChartsAxis-line": { stroke: t.inkSoft } }}
        />
        <ChartsYAxis
          axisId="daily"
          sx={{ "& .MuiChartsAxis-line": { stroke: t.inkSoft } }}
        />
        <ChartsYAxis
          axisId="cumulative"
          sx={{ "& .MuiChartsAxis-line": { stroke: t.inkSoft } }}
        />
        {Array.from(eventsByDate.entries()).map(([evDate, evLabel]) => (
          <ChartsReferenceLine
            key={evDate}
            x={evDate}
            axisId="onset"
            label={evLabel}
            labelAlign="start"
            labelStyle={{
              fontSize: 14,
              fontWeight: 600,
              fill: t.ink,
              fontFamily: FONT,
            }}
            lineStyle={{
              stroke: t.amber,
              strokeDasharray: "6 4",
              strokeWidth: 2.5,
            }}
          />
        ))}
      </ChartsContainer>
    </Box>
  );
}
