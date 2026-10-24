// anyplot.ai
// funnel-basic: Basic Funnel Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "funnel-basic · javascript · muix · anyplot.ai";
const TOTAL_SHARE_SUFFIX = "of initial stage";

const TITLE_HEIGHT = 82;
const MARGIN = { top: 20, right: 60, bottom: 28, left: 20 };
const Y_AXIS_WIDTH = 210;

// Columns: set these to your data's column names
const STAGE = "Stage"; // role: stage
const SHOPPERS = "Shoppers"; // role: value

// Data: replace this block with your own records
const data: Record<string, string | number>[] = [
  { [STAGE]: "Product Views", [SHOPPERS]: 50000 },
  { [STAGE]: "Added to Cart", [SHOPPERS]: 30000 },
  { [STAGE]: "Checkout Started", [SHOPPERS]: 16000 },
  { [STAGE]: "Payment Submitted", [SHOPPERS]: 9000 },
  { [STAGE]: "Order Completed", [SHOPPERS]: 5500 },
];

// Plot: reads only data and the constants above
const maxVal = Math.max(...data.map((r) => Number(r[SHOPPERS])));
const firstVal = Number(data[0][SHOPPERS]);
const lastVal = Number(data[data.length - 1][SHOPPERS]);
const overallConversionPct = ((lastVal / firstVal) * 100).toFixed(1);

const stages = data.map((row, i) => {
  const name = String(row[STAGE]);
  const value = Number(row[SHOPPERS]);
  const nextVal = i < data.length - 1 ? Number(data[i + 1][SHOPPERS]) : value;
  const color = t.palette[i];
  const r = parseInt(color.slice(1, 3), 16);
  const g = parseInt(color.slice(3, 5), 16);
  const b = parseInt(color.slice(5, 7), 16);
  const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
  const labelColor = luminance > 135 ? "#1A1A17" : "#FAF8F1";
  const pct = Math.round((value / firstVal) * 100);
  return { name, value, nextVal, color, labelColor, pct };
});

const stageNames = stages.map((s) => s.name);

function FunnelPlot() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as unknown as ((v: string) => number) & { bandwidth: () => number };
  const drawingArea = useDrawingArea();

  const x0 = xScale(0);
  const cx = drawingArea.left + drawingArea.width / 2;
  const bandwidth = yScale.bandwidth();

  return (
    <g>
      {stages.map((stage) => {
        const y0 = yScale(stage.name);
        const y1 = y0 + bandwidth;
        const topW = xScale(stage.value) - x0;
        const bottomW = xScale(stage.nextVal) - x0;

        const points = [
          `${cx - topW / 2},${y0}`,
          `${cx + topW / 2},${y0}`,
          `${cx + bottomW / 2},${y1}`,
          `${cx - bottomW / 2},${y1}`,
        ].join(" ");

        return (
          <g key={stage.name}>
            <polygon points={points} fill={stage.color} stroke={t.pageBg} strokeWidth={1.5} />
            <text
              x={cx}
              y={y0 + bandwidth / 2 - 11}
              fill={stage.labelColor}
              fontSize={18}
              fontWeight={600}
              textAnchor="middle"
              fontFamily="sans-serif"
            >
              {stage.value.toLocaleString()}
            </text>
            <text
              x={cx}
              y={y0 + bandwidth / 2 + 15}
              fill={stage.labelColor}
              fontSize={14}
              fontWeight={500}
              textAnchor="middle"
              fontFamily="sans-serif"
            >
              {`${stage.pct}% ${TOTAL_SHARE_SUFFIX}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const chartWidth = window.ANYPLOT_SIZE.width;
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;
  const subtitle = `${stages.length} ${STAGE}s · ${SHOPPERS} from ${firstVal.toLocaleString()} to ${lastVal.toLocaleString()} (${overallConversionPct}% end-to-end conversion)`;

  return (
    <Box
      sx={{
        width: chartWidth,
        height: window.ANYPLOT_SIZE.height,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: TITLE_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 15, mt: "2px" }}>
          {subtitle}
        </Typography>
      </Box>

      <ChartsContainer
        skipAnimation
        width={chartWidth}
        height={chartHeight}
        margin={MARGIN}
        series={[
          {
            type: "bar",
            data: stages.map((s) => s.value),
            layout: "horizontal",
          },
        ]}
        xAxis={[{ scaleType: "linear", min: 0, max: maxVal, position: "none" }]}
        yAxis={[
          {
            scaleType: "band",
            data: stageNames,
            width: Y_AXIS_WIDTH,
            categoryGapRatio: 0.3,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fill: t.inkSoft, fontWeight: 500 },
          },
        ]}
      >
        <FunnelPlot />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
