// anyplot.ai
// bar-3d-categorical: 3D Bar Chart for Categorical Comparison
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-04
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const ISO_DX = 20;
const ISO_DY = -14;
const STAGGER_DX = ISO_DX * 1.35;
const STAGGER_DY = ISO_DY * 1.35;
const Y_PAD_SHARE = 0.08;
const VALUE_LABEL_H = 22; // px a value label needs above a bar's top face
const LABEL_CHAR_PX = 8.5; // px advance of one 14 px label character
const ROW_LABEL_GAP = 12;
const EDGE_PAD = 16;

// Columns: set these to your data's column names
const X_CATEGORY = "Alloy"; // role: x_category
const Y_CATEGORY = "Heat treatment"; // role: y_category
const VALUE = "Tensile strength (MPa)"; // role: value

// Data: replace this block with your own records, one object per row
const data = [
  { [X_CATEGORY]: "Al 6061", [Y_CATEGORY]: "Annealed", [VALUE]: 124 },
  { [X_CATEGORY]: "Ti-6Al-4V", [Y_CATEGORY]: "Annealed", [VALUE]: 830 },
  { [X_CATEGORY]: "Steel 4140", [Y_CATEGORY]: "Annealed", [VALUE]: 655 },
  { [X_CATEGORY]: "Inconel 718", [Y_CATEGORY]: "Annealed", [VALUE]: 965 },
  { [X_CATEGORY]: "Mg AZ31", [Y_CATEGORY]: "Annealed", [VALUE]: 145 },
  { [X_CATEGORY]: "Al 6061", [Y_CATEGORY]: "Tempered", [VALUE]: 200 },
  { [X_CATEGORY]: "Ti-6Al-4V", [Y_CATEGORY]: "Tempered", [VALUE]: 950 },
  { [X_CATEGORY]: "Steel 4140", [Y_CATEGORY]: "Tempered", [VALUE]: 780 },
  { [X_CATEGORY]: "Inconel 718", [Y_CATEGORY]: "Tempered", [VALUE]: 1100 },
  { [X_CATEGORY]: "Mg AZ31", [Y_CATEGORY]: "Tempered", [VALUE]: 200 },
  { [X_CATEGORY]: "Al 6061", [Y_CATEGORY]: "Quenched", [VALUE]: 275 },
  { [X_CATEGORY]: "Ti-6Al-4V", [Y_CATEGORY]: "Quenched", [VALUE]: 1100 },
  { [X_CATEGORY]: "Steel 4140", [Y_CATEGORY]: "Quenched", [VALUE]: 900 },
  { [X_CATEGORY]: "Inconel 718", [Y_CATEGORY]: "Quenched", [VALUE]: 1250 },
  { [X_CATEGORY]: "Mg AZ31", [Y_CATEGORY]: "Quenched", [VALUE]: 240 },
  { [X_CATEGORY]: "Al 6061", [Y_CATEGORY]: "Aged", [VALUE]: 310 },
  { [X_CATEGORY]: "Ti-6Al-4V", [Y_CATEGORY]: "Aged", [VALUE]: 1170 },
  { [X_CATEGORY]: "Steel 4140", [Y_CATEGORY]: "Aged", [VALUE]: 1080 },
  { [X_CATEGORY]: "Inconel 718", [Y_CATEGORY]: "Aged", [VALUE]: 1400 },
  { [X_CATEGORY]: "Mg AZ31", [Y_CATEGORY]: "Aged", [VALUE]: 290 },
];

// Plot: reads only data and the constants above
const alloys = [...new Set(data.map((d) => d[X_CATEGORY]))];
const treatments = [...new Set(data.map((d) => d[Y_CATEGORY]))];
const values = data.map((d) => d[VALUE]);
const maxVal = Math.max(...values);
const minVal = Math.min(...values);
const yMax = maxVal * (1 + Y_PAD_SHARE);
const formatValue = (v: number) => v.toLocaleString("en-US");
const marginTop =
  (treatments.length - 1) * Math.abs(STAGGER_DY) + Math.abs(ISO_DY) + VALUE_LABEL_H;
const rowLabelW = Math.max(...treatments.map((tr) => tr.length)) * LABEL_CHAR_PX;
const marginRight =
  (treatments.length - 1) * STAGGER_DX + ISO_DX + ROW_LABEL_GAP + rowLabelW + EDGE_PAD;

const rowColors = treatments.map((_, i) => t.palette[i]);
const topColors = rowColors.map((hex) => {
  const num = parseInt(hex.slice(1), 16);
  const r = Math.round(((num >> 16) & 255) + (255 - ((num >> 16) & 255)) * 0.34);
  const g = Math.round(((num >> 8) & 255) + (255 - ((num >> 8) & 255)) * 0.34);
  const b = Math.round((num & 255) + (255 - (num & 255)) * 0.34);
  return `rgb(${r}, ${g}, ${b})`;
});
const sideColors = rowColors.map((hex) => {
  const num = parseInt(hex.slice(1), 16);
  const r = Math.round(((num >> 16) & 255) * 0.7);
  const g = Math.round(((num >> 8) & 255) * 0.7);
  const b = Math.round((num & 255) * 0.7);
  return `rgb(${r}, ${g}, ${b})`;
});

const paintOrder = [...treatments.keys()].sort((a, b) => b - a);

function Bars3D() {
  const xScale = useXScale() as any;
  const yScale = useYScale() as any;
  const { left, width } = useDrawingArea();
  const bandwidth = xScale.bandwidth();
  const barWidth = bandwidth * 0.52;
  const baseline = yScale(0);

  return (
    <g data-drawing-container>
      <g>
        {treatments.map((treatment, row) => {
          const dx = row * STAGGER_DX;
          const dy = row * STAGGER_DY;
          return (
            <g key={`floor-row-${treatment}`}>
              <line
                x1={left + dx}
                y1={baseline + dy}
                x2={left + width + dx}
                y2={baseline + dy}
                stroke={t.inkSoft}
                strokeWidth={1.5}
                opacity={0.35}
              />
              <text
                x={left + width + dx + ISO_DX + ROW_LABEL_GAP}
                y={baseline + dy + 4}
                fontSize={14}
                fontWeight={500}
                fill={t.inkSoft}
              >
                {treatment}
              </text>
            </g>
          );
        })}
        {alloys.map((alloy) => {
          const cx = xScale(alloy) + bandwidth / 2;
          const points = treatments
            .map(
              (_, row) =>
                `${cx + row * STAGGER_DX},${baseline + row * STAGGER_DY}`,
            )
            .join(" ");
          return (
            <polyline
              key={`floor-col-${alloy}`}
              points={points}
              fill="none"
              stroke={t.inkSoft}
              strokeWidth={1.5}
              opacity={0.35}
            />
          );
        })}
      </g>
      {paintOrder.map((row) => {
        const treatment = treatments[row];
        const dx = row * STAGGER_DX;
        const dy = row * STAGGER_DY;
        const color = rowColors[row];
        const topColor = topColors[row];
        const sideColor = sideColors[row];
        return (
          <g key={treatment} transform={`translate(${dx}, ${dy})`}>
            {alloys.map((alloy) => {
              const rowObj = data.find(
                (d) => d[X_CATEGORY] === alloy && d[Y_CATEGORY] === treatment,
              );
              if (!rowObj || rowObj[VALUE] === null) return null;
              const value = rowObj[VALUE];
              const x = xScale(alloy) + (bandwidth - barWidth) / 2;
              const y = yScale(value);
              const barHeight = baseline - y;
              const topFace = [
                `${x},${y}`,
                `${x + barWidth},${y}`,
                `${x + barWidth + ISO_DX},${y + ISO_DY}`,
                `${x + ISO_DX},${y + ISO_DY}`,
              ].join(" ");
              const sideFace = [
                `${x + barWidth},${y}`,
                `${x + barWidth},${y + barHeight}`,
                `${x + barWidth + ISO_DX},${y + barHeight + ISO_DY}`,
                `${x + barWidth + ISO_DX},${y + ISO_DY}`,
              ].join(" ");
              const labelCx = x + barWidth / 2 + ISO_DX / 2;
              const labelCy = y + ISO_DY - 7;
              const labelStr = formatValue(value);
              const pillW = labelStr.length * LABEL_CHAR_PX + 10;
              return (
                <g key={alloy}>
                  <rect
                    x={x}
                    y={y}
                    width={barWidth}
                    height={barHeight}
                    fill={color}
                  />
                  <polygon points={sideFace} fill={sideColor} />
                  <polygon points={topFace} fill={topColor} />
                  {row < treatments.length - 1 && (
                    <rect
                      x={labelCx - pillW / 2}
                      y={labelCy - 14}
                      width={pillW}
                      height={18}
                      rx={3}
                      fill={t.pageBg}
                      fillOpacity={0.85}
                    />
                  )}
                  <text
                    x={labelCx}
                    y={labelCy}
                    textAnchor="middle"
                    fontSize={14}
                    fontWeight={600}
                    fill={t.ink}
                  >
                    {labelStr}
                  </text>
                </g>
              );
            })}
          </g>
        );
      })}
    </g>
  );
}

const TITLE = "bar-3d-categorical · javascript · muix · anyplot.ai";
const SUBTITLE = `${X_CATEGORY}: ${alloys.length} · ${Y_CATEGORY}: ${treatments.length} · ${VALUE}: ${formatValue(minVal)}–${formatValue(maxVal)}`;
const HEADER_H = 104;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      }}
    >
      <div
        style={{
          height: HEADER_H,
          padding: "14px 48px 0 48px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            fontSize: 22,
            fontWeight: 600,
            color: t.ink,
            lineHeight: 1.25,
          }}
        >
          {TITLE}
        </div>
        <div
          style={{
            fontSize: 15,
            color: t.inkSoft,
            marginTop: 4,
          }}
        >
          {SUBTITLE}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            marginTop: 6,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          <span style={{ fontWeight: 600, color: t.ink }}>{Y_CATEGORY}:</span>
          {treatments.map((tr, i) => (
            <span
              key={tr}
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 3,
                  backgroundColor: rowColors[i],
                  display: "inline-block",
                }}
              />
              <span>{tr}</span>
            </span>
          ))}
        </div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_H}
        margin={{ top: marginTop, right: marginRight, bottom: 24, left: 40 }}
        skipAnimation
        series={[]}
        xAxis={[
          {
            scaleType: "band",
            data: alloys,
            label: X_CATEGORY,
            height: 68,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: 0,
            max: yMax,
            valueFormatter: formatValue,
            label: VALUE,
            width: 96,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsGrid horizontal />
        <Bars3D />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
