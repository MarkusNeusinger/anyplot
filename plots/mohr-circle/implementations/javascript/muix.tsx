// anyplot.ai
// mohr-circle: Mohr's Circle for Stress Analysis
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 87/100 | Updated: 2026-10-24
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "mohr-circle · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 64;
const X_AXIS_HEIGHT = 60;
const Y_AXIS_WIDTH = 90;
const PAD_RATIO = 0.68;
const ARC_RADIUS_RATIO = 0.32;
const ARC_STEPS = 32;
const X_AXIS_PREFIX = "Normal Stress σ";
const Y_AXIS_PREFIX = "Shear Stress τ";

// Columns: set these to your data's column names
const SIGMA_X = "Normal Stress σx (MPa)"; // role: sigma_x
const SIGMA_Y = "Normal Stress σy (MPa)"; // role: sigma_y
const TAU_XY = "Shear Stress τxy (MPa)"; // role: tau_xy

// Data: replace this block with your own records
const data: Array<Record<string, number>> = [
  {
    [SIGMA_X]: 80,
    [SIGMA_Y]: 20,
    [TAU_XY]: 30,
  },
];

// Plot: reads only data and the constants above
const unitMatch = /\(([^)]+)\)/.exec(SIGMA_X);
const unit = unitMatch ? unitMatch[1] : "";
const unitSuffix = unit ? ` ${unit}` : "";
const xAxisLabel = unit ? `${X_AXIS_PREFIX} (${unit})` : X_AXIS_PREFIX;
const yAxisLabel = unit ? `${Y_AXIS_PREFIX} (${unit})` : Y_AXIS_PREFIX;

const stateRow = data[0];
const sigmaX = Number(stateRow[SIGMA_X]);
const sigmaY = Number(stateRow[SIGMA_Y]);
const tauXY = Number(stateRow[TAU_XY]);

const center = (sigmaX + sigmaY) / 2;
const radius = Math.sqrt(((sigmaX - sigmaY) / 2) ** 2 + tauXY ** 2);
const sigma1 = center + radius;
const sigma2 = center - radius;
const tauMax = radius;
const twoThetaPRad = Math.atan2(tauXY, (sigmaX - sigmaY) / 2);
const twoThetaPDeg = (twoThetaPRad * 180) / Math.PI;

const pad = radius * PAD_RATIO;
const xAxisMin = center - radius - pad;
const xAxisMax = center + radius + pad;
const yAxisMin = -radius - pad;
const yAxisMax = radius + pad;

function MohrAnnotations() {
  const xScale = useXScale();
  const yScale = useYScale();

  const cx = Number(xScale(center));
  const cy = Number(yScale(0));
  const ax = Number(xScale(sigmaX));
  const ay = Number(yScale(tauXY));
  const bx = Number(xScale(sigmaY));
  const by = Number(yScale(-tauXY));
  const s1x = Number(xScale(sigma1));
  const s1y = Number(yScale(0));
  const s2x = Number(xScale(sigma2));
  const s2y = Number(yScale(0));
  const tmaxX = Number(xScale(center));
  const tmaxY = Number(yScale(tauMax));
  const tminX = Number(xScale(center));
  const tminY = Number(yScale(-tauMax));

  const circleRadiusPx = Math.abs(s1x - cx);
  const arcRadius = radius * ARC_RADIUS_RATIO;

  let arcPath = "";
  for (let i = 0; i <= ARC_STEPS; i++) {
    const angle = (twoThetaPRad * i) / ARC_STEPS;
    const px = Number(xScale(center + arcRadius * Math.cos(angle)));
    const py = Number(yScale(arcRadius * Math.sin(angle)));
    arcPath += `${i === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)} `;
  }

  const angleLabelX = Number(xScale(center + arcRadius * 1.65 * Math.cos(twoThetaPRad / 2)));
  const angleLabelY = Number(yScale(arcRadius * 1.65 * Math.sin(twoThetaPRad / 2)));

  const stateColor = t.palette[1];
  const circleColor = t.palette[0];
  const landmarkColor = t.ink;

  const principalPoints = [
    { x: s1x, y: s1y },
    { x: s2x, y: s2y },
    { x: tmaxX, y: tmaxY },
    { x: tminX, y: tminY },
  ];
  const statePoints = [
    { x: ax, y: ay },
    { x: bx, y: by },
  ];

  return (
    <g>
      <circle
        cx={cx}
        cy={cy}
        r={circleRadiusPx}
        fill={circleColor}
        fillOpacity={0.07}
        stroke={circleColor}
        strokeWidth={3.5}
      />

      <line
        x1={s2x}
        y1={s2y}
        x2={s1x}
        y2={s1y}
        stroke={landmarkColor}
        strokeWidth={4}
        strokeLinecap="round"
      />

      <line
        x1={ax}
        y1={ay}
        x2={bx}
        y2={by}
        stroke={t.ink}
        strokeWidth={2}
        strokeDasharray="7 6"
      />

      <path d={arcPath.trim()} fill="none" stroke={t.inkSoft} strokeWidth={2} />

      <circle cx={cx} cy={cy} r={6} fill={landmarkColor} />

      {principalPoints.map((p, i) => (
        <circle
          key={`p-${i}`}
          cx={p.x}
          cy={p.y}
          r={10}
          fill={landmarkColor}
          stroke={t.pageBg}
          strokeWidth={2.5}
        />
      ))}

      {statePoints.map((p, i) => (
        <circle
          key={`s-${i}`}
          cx={p.x}
          cy={p.y}
          r={10}
          fill={stateColor}
          stroke={t.pageBg}
          strokeWidth={2.5}
        />
      ))}

      <ChartsText
        x={ax + 18}
        y={ay - 16}
        text={`A(${sigmaX}, ${tauXY})`}
        style={{ fontSize: 16, fontWeight: 600, fill: t.ink, dominantBaseline: "central" }}
      />
      <ChartsText
        x={bx - 18}
        y={by + 18}
        text={`B(${sigmaY}, ${-tauXY})`}
        style={{
          fontSize: 16,
          fontWeight: 600,
          fill: t.ink,
          textAnchor: "end",
          dominantBaseline: "central",
        }}
      />
      <ChartsText
        x={s1x + 14}
        y={s1y + 28}
        text={`σ₁ = ${sigma1.toFixed(1)}${unitSuffix}`}
        style={{ fontSize: 17, fontWeight: 700, fill: t.ink, dominantBaseline: "central" }}
      />
      <ChartsText
        x={s2x - 14}
        y={s2y + 28}
        text={`σ₂ = ${sigma2.toFixed(1)}${unitSuffix}`}
        style={{
          fontSize: 17,
          fontWeight: 700,
          fill: t.ink,
          textAnchor: "end",
          dominantBaseline: "central",
        }}
      />
      <ChartsText
        x={tmaxX + 16}
        y={tmaxY - 14}
        text={`τ_max = ${tauMax.toFixed(1)}${unitSuffix}`}
        style={{ fontSize: 17, fontWeight: 700, fill: t.ink, dominantBaseline: "central" }}
      />
      <ChartsText
        x={tminX + 16}
        y={tminY + 14}
        text={`−τ_max = ${(-tauMax).toFixed(1)}${unitSuffix}`}
        style={{ fontSize: 17, fontWeight: 700, fill: t.ink, dominantBaseline: "central" }}
      />
      <ChartsText
        x={cx - 14}
        y={cy - 18}
        text={`C(${center.toFixed(0)}, 0)`}
        style={{
          fontSize: 15,
          fill: t.inkSoft,
          textAnchor: "end",
          dominantBaseline: "central",
        }}
      />
      <ChartsText
        x={angleLabelX + 8}
        y={angleLabelY - 6}
        text={`2θp = ${twoThetaPDeg.toFixed(0)}°`}
        style={{ fontSize: 15, fontWeight: 600, fill: t.inkSoft, dominantBaseline: "central" }}
      />
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartH = height - TITLE_HEIGHT;
  const targetDrawSize = Math.min(width - Y_AXIS_WIDTH - 64, chartH - X_AXIS_HEIGHT - 44);
  const marginLeft = Math.floor((width - Y_AXIS_WIDTH - targetDrawSize) / 2);
  const marginRight = width - Y_AXIS_WIDTH - targetDrawSize - marginLeft;
  const marginTop = Math.floor((chartH - X_AXIS_HEIGHT - targetDrawSize) / 2);
  const marginBottom = chartH - X_AXIS_HEIGHT - targetDrawSize - marginTop;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={width}
        height={chartH}
        margin={{
          top: marginTop,
          right: marginRight,
          bottom: marginBottom,
          left: marginLeft,
        }}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "sigma",
            scaleType: "linear",
            min: xAxisMin,
            max: xAxisMax,
            height: X_AXIS_HEIGHT,
            label: xAxisLabel,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            stroke: t.inkSoft,
          },
        ]}
        yAxis={[
          {
            id: "tau",
            scaleType: "linear",
            min: yAxisMin,
            max: yAxisMax,
            width: Y_AXIS_WIDTH,
            label: yAxisLabel,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            stroke: t.inkSoft,
          },
        ]}
      >
        <ChartsGrid horizontal vertical />
        <ChartsReferenceLine y={0} lineStyle={{ stroke: t.grid, strokeWidth: 2 }} />
        <ChartsReferenceLine x={center} lineStyle={{ stroke: t.grid, strokeWidth: 2 }} />
        <MohrAnnotations />
        <ChartsXAxis axisId="sigma" />
        <ChartsYAxis axisId="tau" />
      </ChartsContainer>
    </div>
  );
}
