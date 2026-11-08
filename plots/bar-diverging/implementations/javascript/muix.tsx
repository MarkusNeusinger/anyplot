// anyplot.ai
// bar-diverging: Diverging Bar Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "bar-diverging · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const PAD_SHARE = 0.1; // room beyond the longest bar for its value label
// Direction colours: brand green above zero, the semantic red anchor below
const POS_COLOR = t.palette[0];
const NEG_COLOR = t.palette[4];

// Columns: set these to your data's column names
const STATEMENT = "Survey statement"; // role: category
const NET_SCORE = "Net agreement score (percentage points)"; // role: value

// Data: replace this block with your own records, one object per row
// Employee engagement survey: net agreement = % agree minus % disagree per statement
const data = [
  { [STATEMENT]: "Leadership communicates clearly", [NET_SCORE]: 68 },
  { [STATEMENT]: "I feel valued at work", [NET_SCORE]: 52 },
  { [STATEMENT]: "Team collaboration is strong", [NET_SCORE]: 41 },
  { [STATEMENT]: "My workload is manageable", [NET_SCORE]: 22 },
  { [STATEMENT]: "Growth opportunities are clear", [NET_SCORE]: 9 },
  { [STATEMENT]: "Compensation feels fair", [NET_SCORE]: -8 },
  { [STATEMENT]: "Feedback is timely and useful", [NET_SCORE]: -19 },
  { [STATEMENT]: "Meetings are a good use of time", [NET_SCORE]: -34 },
  { [STATEMENT]: "Tools I use are reliable", [NET_SCORE]: -41 },
  { [STATEMENT]: "Change is managed effectively", [NET_SCORE]: -55 },
];

// Plot: reads only data and the constants above
// Largest value first, so the chart runs from the top positive bar to the most negative
const rows = data.filter((d) => d[NET_SCORE] != null).sort((a, b) => b[NET_SCORE] - a[NET_SCORE]);
const categories = rows.map((d) => d[STATEMENT]);

// One series per direction in a shared stack: each row draws a single bar, coloured
// by its sign, on the side of zero its value points to
const positive = rows.map((d) => (d[NET_SCORE] >= 0 ? d[NET_SCORE] : null));
const negative = rows.map((d) => (d[NET_SCORE] < 0 ? d[NET_SCORE] : null));

// Symmetric value axis around zero, rounded out to a half step of its magnitude
const reach = Math.max(...rows.map((d) => Math.abs(d[NET_SCORE]))) * (1 + PAD_SHARE) || 1;
const halfStep = 10 ** Math.floor(Math.log10(reach)) / 2;
const limit = Math.ceil(reach / halfStep) * halfStep;
const fmtSigned = (v: number) => `${v > 0 ? "+" : ""}${v}`;

const SUBTITLE = `${rows.length} categories, sorted by value · ${positive.filter((v) => v != null).length} above zero, ${negative.filter((v) => v != null).length} below`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, px: "40px", pt: "18px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>
      <BarChart
        width={width}
        height={height - TITLE_H}
        layout="horizontal"
        skipAnimation
        hideLegend
        grid={{ vertical: true }}
        series={[
          {
            id: "pos",
            stack: "score",
            data: positive,
            label: NET_SCORE,
            color: POS_COLOR,
            barLabel: (item: { value: number | null }) => (item.value == null ? null : fmtSigned(item.value)),
            barLabelPlacement: "outside",
            valueFormatter: (v: number | null) => (v == null ? null : fmtSigned(v)),
          },
          {
            id: "neg",
            stack: "score",
            data: negative,
            label: NET_SCORE,
            color: NEG_COLOR,
            barLabel: (item: { value: number | null }) => (item.value == null ? null : fmtSigned(item.value)),
            barLabelPlacement: "outside",
            valueFormatter: (v: number | null) => (v == null ? null : fmtSigned(v)),
          },
        ]}
        xAxis={[
          {
            id: "value",
            min: -limit,
            max: limit,
            label: NET_SCORE,
            height: 64,
            tickNumber: 8,
            valueFormatter: fmtSigned,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            scaleType: "band",
            data: categories,
            width: 280,
            categoryGapRatio: 0.35,
            disableTicks: true,
            tickLabelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        margin={{ top: 16, right: 48, bottom: 8, left: 24 }}
        sx={{
          "& .MuiBarChart-label": { fill: t.ink, fontSize: 15, fontWeight: 600 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsReferenceLine x={0} axisId="value" lineStyle={{ stroke: t.ink, strokeWidth: 2 }} />
      </BarChart>
    </Box>
  );
}
