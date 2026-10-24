// anyplot.ai
// funnel-basic: Basic Funnel Chart
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-05
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const STAGE_COL = "stage";
const VALUE_COL = "value";

const TITLE = "funnel-basic · javascript · muix · anyplot.ai";
const SUBTITLE_PREFIX = "E-commerce checkout conversion funnel";
const TOTAL_SHARE_SUFFIX = "of initial stage";

const TITLE_HEIGHT = 82;
const MARGIN = { top: 20, right: 60, bottom: 28, left: 20 };
const Y_AXIS_WIDTH = 210;

// Data — e-commerce checkout pipeline from product views through completed orders
const data: Record<string, string | number>[] = [
  { [STAGE_COL]: "Product Views", [VALUE_COL]: 50000 },
  { [STAGE_COL]: "Added to Cart", [VALUE_COL]: 30000 },
  { [STAGE_COL]: "Checkout Started", [VALUE_COL]: 16000 },
  { [STAGE_COL]: "Payment Submitted", [VALUE_COL]: 9000 },
  { [STAGE_COL]: "Order Completed", [VALUE_COL]: 5500 },
];

const maxVal = Math.max(...data.map((r) => Number(r[VALUE_COL])));
const firstVal = Number(data[0][VALUE_COL]) || 1;
const lastVal = Number(data[data.length - 1][VALUE_COL]) || 0;
const overallConversionPct = ((lastVal / firstVal) * 100).toFixed(1);

const stages = data.map((row, i) => {
  const name = String(row[STAGE_COL]);
  const value = Number(row[VALUE_COL]);
  const nextVal = i < data.length - 1 ? Number(data[i + 1][VALUE_COL]) : value;
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
  const xScale = useXScale();
  const yScale = useYScale();
  const drawingArea = useDrawingArea();

  if (!xScale || !yScale || typeof (yScale as any).bandwidth !== "function") return null;

  const x0 = Number(xScale(0));
  const cx = drawingArea.left + drawingArea.width / 2;
  const bandwidth = (yScale as any).bandwidth() as number;

  return (
    <g>
      {stages.map((stage) => {
        const bandTop = yScale(stage.name);
        if (bandTop == null || !isFinite(Number(bandTop))) return null;

        const y0 = Number(bandTop);
        const y1 = y0 + bandwidth;
        const topW = Number(xScale(stage.value)) - x0;
        const bottomW = Number(xScale(stage.nextVal)) - x0;

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
  const subtitle = `${SUBTITLE_PREFIX} · ${stages.length} stages (${overallConversionPct}% end-to-end conversion)`;

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
