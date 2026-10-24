// anyplot.ai
// histogram-epidemic: Epidemic Curve (Epi Curve)
// Library: muix 7.29.1 | JavaScript 22.23.2
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

// Constants
const FONT = "system-ui, -apple-system, sans-serif";
const TITLE = "histogram-epidemic · javascript · muix · anyplot.ai";
const Y_HEADROOM_RATIO = 0.14;
const MONTH_ABBR = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

// Columns: set these to your data's column names
const ONSET_DATE = "Symptom Onset Date"; // role: onset_date
const CASE_TYPE = "Case Classification"; // role: case_type
const DAILY_CASES = "Daily New Cases"; // role: case_count
const EVENT_LABEL = "Intervention Event"; // role: events

// Data: replace this block with your own records
type EpiRow = {
  [ONSET_DATE]: string;
  [CASE_TYPE]: string;
  [DAILY_CASES]: number;
  [EVENT_LABEL]: string;
};

const data: EpiRow[] = [];
let seed = 42;
const dayCount = 63;
const startMs = Date.UTC(2024, 0, 1);
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
  const isoDate = new Date(startMs + day * 86400000).toISOString().slice(0, 10);
  const ev = eventByDayIndex[day] ?? "";
  const conf = rawConfirmed[day];
  const prob = rawProbable[day];
  const susp = Math.max(0, rawDailyTotals[day] - conf - prob);

  data.push(
    {
      [ONSET_DATE]: isoDate,
      [CASE_TYPE]: "Confirmed",
      [DAILY_CASES]: conf,
      [EVENT_LABEL]: ev,
    },
    {
      [ONSET_DATE]: isoDate,
      [CASE_TYPE]: "Probable",
      [DAILY_CASES]: prob,
      [EVENT_LABEL]: ev,
    },
    {
      [ONSET_DATE]: isoDate,
      [CASE_TYPE]: "Suspect",
      [DAILY_CASES]: susp,
      [EVENT_LABEL]: ev,
    },
  );
}

// Plot: reads only data and the constants above
const onsetDates = Array.from(new Set(data.map((r) => r[ONSET_DATE]))).sort();
const caseTypes: string[] = [];
const eventsByDate = new Map<string, string>();

for (const row of data) {
  const dt = row[ONSET_DATE];
  const ct = row[CASE_TYPE];
  if (!caseTypes.includes(ct)) caseTypes.push(ct);
  if (row[EVENT_LABEL] && !eventsByDate.has(dt)) {
    eventsByDate.set(dt, row[EVENT_LABEL]);
  }
}

const countLookup = new Map<string, number>();
for (const row of data) {
  const key = `${row[ONSET_DATE]}__${row[CASE_TYPE]}`;
  countLookup.set(key, (countLookup.get(key) ?? 0) + row[DAILY_CASES]);
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

const maxDaily = Math.max(...dailyTotals) * (1 + Y_HEADROOM_RATIO);
const maxCumulative =
  cumulativeCases[cumulativeCases.length - 1] * (1 + Y_HEADROOM_RATIO * 0.5);

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

const totalOutbreakCases = cumulativeCases[cumulativeCases.length - 1];
const peakDaily = Math.max(...dailyTotals);
const peakDate = onsetDates[dailyTotals.indexOf(peakDaily)];

const fmtDate = (iso: string) => {
  const parts = iso.split("-").map(Number);
  return `${MONTH_ABBR[parts[1] - 1]} ${parts[2]}`;
};

const SUBTITLE = `${onsetDates.length} days (${fmtDate(onsetDates[0])}–${fmtDate(onsetDates[onsetDates.length - 1])}) · Total ${totalOutbreakCases.toLocaleString("en-US")} cases, peak ${peakDaily}/day on ${fmtDate(peakDate)}`;

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
            label: ONSET_DATE,
            valueFormatter: fmtDate,
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
            label: DAILY_CASES,
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
