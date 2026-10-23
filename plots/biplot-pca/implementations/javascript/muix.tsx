// anyplot.ai
// biplot-pca: PCA Biplot with Scores and Loading Vectors
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-01
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// Constants
const LOADING_SCALE_SHARE = 0.85;
const AXIS_PAD_SHARE = 0.16;
const UNIT_CIRCLE_STEPS = 72;
const MIN_LABEL_GAP = 30;
const JACOBI_MAX_SWEEPS = 100;
const JACOBI_TOL = 1e-12;

// Columns: set these to your data's column names
const LABELS = "Production facility"; // role: labels
const FEATURES = [
  "Temperature (°C)",
  "Pressure (kPa)",
  "Vibration (mm/s)",
  "Throughput (units/min)",
]; // role: features

// Data: replace this block with your own records, one object per row
const data = (() => {
  let state = 42;
  const facilities = ["Munich Assembly", "Stuttgart Press", "Dresden Optics"];
  const batchOffsets = [-1.4, 0, 1.4];
  const obsPerFacility = 20;
  const rows: { [key: string]: string | number }[] = [];

  for (let fIdx = 0; fIdx < facilities.length; fIdx += 1) {
    const facility = facilities[fIdx];
    for (let i = 0; i < obsPerFacility; i += 1) {
      const normals: number[] = [];
      for (let g = 0; g < 6; g += 1) {
        state = (state * 16807) % 2147483647;
        const u1 = Math.max((state - 1) / 2147483646, 1e-9);
        state = (state * 16807) % 2147483647;
        const u2 = (state - 1) / 2147483646;
        normals.push(Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2));
      }
      const processIntensity = batchOffsets[fIdx] + normals[0] * 0.5;
      const calibrationDrift = normals[1];
      rows.push({
        [LABELS]: facility,
        [FEATURES[0]]: Number(
          (68 + 4.2 * processIntensity + 1.0 * calibrationDrift + normals[2] * 1.4).toFixed(2),
        ),
        [FEATURES[1]]: Number(
          (120 + 5.5 * processIntensity - 2.4 * calibrationDrift + normals[3] * 1.8).toFixed(2),
        ),
        [FEATURES[2]]: Number(
          (3.2 - 1.2 * processIntensity + 2.6 * calibrationDrift + normals[4] * 0.35).toFixed(2),
        ),
        [FEATURES[3]]: Number(
          (480 + 6.0 * processIntensity + 0.6 * calibrationDrift + normals[5] * 4.5).toFixed(2),
        ),
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const sampleCount = data.length;
const featureCount = FEATURES.length;

const groups: string[] = [];
for (const row of data) {
  const g = String(row[LABELS]);
  if (!groups.includes(g)) groups.push(g);
}

const featureMeans = FEATURES.map(
  (col) => data.reduce((sum, row) => sum + Number(row[col]), 0) / sampleCount,
);
const featureStds = FEATURES.map((col, j) =>
  Math.sqrt(
    data.reduce((sum, row) => sum + (Number(row[col]) - featureMeans[j]) ** 2, 0) /
      sampleCount,
  ) || 1,
);
const standardized = data.map((row) =>
  FEATURES.map((col, j) => (Number(row[col]) - featureMeans[j]) / featureStds[j]),
);

const correlationMatrix = Array.from({ length: featureCount }, (_, rowIdx) =>
  Array.from({ length: featureCount }, (_, colIdx) => {
    let sum = 0;
    for (let obs = 0; obs < sampleCount; obs += 1) {
      sum += standardized[obs][rowIdx] * standardized[obs][colIdx];
    }
    return sum / sampleCount;
  }),
);

const workingMatrix = correlationMatrix.map((row) => row.slice());
const eigenvectors = Array.from({ length: featureCount }, (_, rowIdx) =>
  Array.from({ length: featureCount }, (_, colIdx) => (rowIdx === colIdx ? 1 : 0)),
);

for (let sweep = 0; sweep < JACOBI_MAX_SWEEPS; sweep += 1) {
  let offDiagonalMagnitude = 0;
  for (let rowIdx = 0; rowIdx < featureCount; rowIdx += 1) {
    for (let colIdx = rowIdx + 1; colIdx < featureCount; colIdx += 1) {
      offDiagonalMagnitude += workingMatrix[rowIdx][colIdx] ** 2;
    }
  }
  if (offDiagonalMagnitude < JACOBI_TOL) break;

  for (let p = 0; p < featureCount; p += 1) {
    for (let q = p + 1; q < featureCount; q += 1) {
      if (Math.abs(workingMatrix[p][q]) < JACOBI_TOL) continue;
      const theta =
        (workingMatrix[q][q] - workingMatrix[p][p]) / (2 * workingMatrix[p][q]);
      const tan =
        Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
      const cos = 1 / Math.sqrt(tan * tan + 1);
      const sin = tan * cos;
      const app = workingMatrix[p][p];
      const aqq = workingMatrix[q][q];
      const apq = workingMatrix[p][q];
      workingMatrix[p][p] = cos * cos * app - 2 * sin * cos * apq + sin * sin * aqq;
      workingMatrix[q][q] = sin * sin * app + 2 * sin * cos * apq + cos * cos * aqq;
      workingMatrix[p][q] = 0;
      workingMatrix[q][p] = 0;
      for (let k = 0; k < featureCount; k += 1) {
        if (k !== p && k !== q) {
          const akp = workingMatrix[k][p];
          const akq = workingMatrix[k][q];
          workingMatrix[k][p] = cos * akp - sin * akq;
          workingMatrix[p][k] = workingMatrix[k][p];
          workingMatrix[k][q] = sin * akp + cos * akq;
          workingMatrix[q][k] = workingMatrix[k][q];
        }
      }
      for (let k = 0; k < featureCount; k += 1) {
        const vkp = eigenvectors[k][p];
        const vkq = eigenvectors[k][q];
        eigenvectors[k][p] = cos * vkp - sin * vkq;
        eigenvectors[k][q] = sin * vkp + cos * vkq;
      }
    }
  }
}

const eigenvalues = workingMatrix.map((row, i) => row[i]);
const componentOrder = eigenvalues
  .map((value, index) => ({ value, index }))
  .sort((a, b) => b.value - a.value);
const pc1Index = componentOrder[0].index;
const pc2Index = componentOrder[1].index;
const totalVariance = eigenvalues.reduce((sum, value) => sum + value, 0);
const pc1VarianceShare = (eigenvalues[pc1Index] / totalVariance) * 100;
const pc2VarianceShare = (eigenvalues[pc2Index] / totalVariance) * 100;

const scores = standardized.map((row) => ({
  x: row.reduce((sum, value, j) => sum + value * eigenvectors[j][pc1Index], 0),
  y: row.reduce((sum, value, j) => sum + value * eigenvectors[j][pc2Index], 0),
}));

// PC2's eigenvalue rounds to a tiny negative number when all features are collinear
const rawLoadings = FEATURES.map((_, j) => ({
  x: eigenvectors[j][pc1Index] * Math.sqrt(eigenvalues[pc1Index]),
  y: eigenvectors[j][pc2Index] * Math.sqrt(Math.max(0, eigenvalues[pc2Index])),
}));

const maxScoreExtent = Math.max(
  ...scores.map((s) => Math.max(Math.abs(s.x), Math.abs(s.y))),
);
const maxLoadingExtent = Math.max(
  ...rawLoadings.map((l) => Math.max(Math.abs(l.x), Math.abs(l.y))),
);
const loadingDisplayScale = (maxScoreExtent * LOADING_SCALE_SHARE) / maxLoadingExtent;
const loadingVectors = rawLoadings.map((loading, j) => ({
  variable: FEATURES[j],
  x: loading.x * loadingDisplayScale,
  y: loading.y * loadingDisplayScale,
}));

const HEADER_H = 104;
const MARGIN = { top: 16, right: 200, bottom: 20, left: 200 };
const X_AXIS_H = 64;
const Y_AXIS_W = 84;
const drawW = size.width - MARGIN.left - MARGIN.right - Y_AXIS_W;
const drawH = size.height - HEADER_H - MARGIN.top - MARGIN.bottom - X_AXIS_H;
const aspectRatio = drawW / drawH;

const maxAbsX = Math.max(...scores.map((s) => Math.abs(s.x)), loadingDisplayScale);
const maxAbsY = Math.max(...scores.map((s) => Math.abs(s.y)), loadingDisplayScale);
const yBound = Math.max(maxAbsY * (1 + AXIS_PAD_SHARE), (maxAbsX * (1 + AXIS_PAD_SHARE)) / aspectRatio);
const yMax = yBound;
const yMin = -yBound;
const xMax = yBound * aspectRatio;
const xMin = -xMax;

const series = groups.map((group, groupIdx) => ({
  type: "scatter" as const,
  id: group,
  label: group,
  color: t.palette[groupIdx],
  markerSize: 7,
  xAxisId: "pc1",
  yAxisId: "pc2",
  data: data
    .map((row, i) => ({ row, i }))
    .filter(({ row }) => String(row[LABELS]) === group)
    .map(({ i }) => ({ x: scores[i].x, y: scores[i].y, id: `${group}-${i}` })),
}));

const unitCirclePoints = Array.from({ length: UNIT_CIRCLE_STEPS + 1 }, (_, i) => {
  const angle = (i / UNIT_CIRCLE_STEPS) * 2 * Math.PI;
  return {
    x: Math.cos(angle) * loadingDisplayScale,
    y: Math.sin(angle) * loadingDisplayScale,
  };
});

const TITLE = "biplot-pca · javascript · muix · anyplot.ai";
const SUBTITLE = `${sampleCount} observations · ${LABELS}: ${groups.length} · ${featureCount} standardized features · PC1 + PC2 explain ${(pc1VarianceShare + pc2VarianceShare).toFixed(1)}% variance`;

function LoadingArrows() {
  const xScale = useXScale("pc1");
  const yScale = useYScale("pc2");
  const originX = xScale(0);
  const originY = yScale(0);

  const rawItems = loadingVectors.map((loading) => ({
    variable: loading.variable,
    tipX: xScale(loading.x),
    tipY: yScale(loading.y),
    labelY: yScale(loading.y),
    pointsRight: loading.x >= 0,
  }));

  const sides = [true, false].map((pointsRight) =>
    rawItems
      .filter((item) => item.pointsRight === pointsRight)
      .sort((a, b) => a.tipY - b.tipY),
  );
  for (const side of sides) {
    for (let i = 0; i < side.length; i += 1) {
      const minY = i === 0 ? -Infinity : side[i - 1].labelY + MIN_LABEL_GAP;
      side[i].labelY = Math.max(side[i].tipY, minY);
    }
  }
  const items = sides.flat();

  return (
    <g>
      <defs>
        <marker
          id="biplot-arrowhead"
          markerWidth={8}
          markerHeight={8}
          refX={6}
          refY={4}
          orient="auto"
        >
          <path d="M0,0 L8,4 L0,8 Z" fill={t.ink} />
        </marker>
      </defs>
      <polyline
        points={unitCirclePoints
          .map((p) => `${xScale(p.x)},${yScale(p.y)}`)
          .join(" ")}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={1.25}
        strokeDasharray="5 4"
        opacity={0.65}
      />
      <line
        x1={xScale(xMin)}
        x2={xScale(xMax)}
        y1={originY}
        y2={originY}
        stroke={t.inkSoft}
        strokeWidth={1}
        strokeOpacity={0.45}
      />
      <line
        x1={originX}
        x2={originX}
        y1={yScale(yMin)}
        y2={yScale(yMax)}
        stroke={t.inkSoft}
        strokeWidth={1}
        strokeOpacity={0.45}
      />
      {items.map((loading) => {
        const textX = loading.tipX + (loading.pointsRight ? 12 : -12);
        const pillW = loading.variable.length * 8.2 + 12;
        const pillX = loading.pointsRight ? textX - 5 : textX - pillW + 5;
        return (
          <g key={loading.variable}>
            <line
              x1={originX}
              y1={originY}
              x2={loading.tipX}
              y2={loading.tipY}
              stroke={t.ink}
              strokeWidth={2.5}
              markerEnd="url(#biplot-arrowhead)"
            />
            <rect
              x={pillX}
              y={loading.labelY - 12}
              width={pillW}
              height={24}
              rx={4}
              fill={t.pageBg}
              fillOpacity={0.86}
            />
            <text
              x={textX}
              y={loading.labelY}
              fill={t.ink}
              fontSize={14}
              fontWeight={600}
              fontFamily="Inter, system-ui, sans-serif"
              textAnchor={loading.pointsRight ? "start" : "end"}
              dominantBaseline="middle"
            >
              {loading.variable}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  return (
    <div
      style={{
        width: size.width,
        height: size.height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          {groups.map((group, idx) => (
            <div
              key={group}
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  background: t.palette[idx],
                  display: "inline-block",
                }}
              />
              <span style={{ fontSize: 14, color: t.inkSoft }}>{group}</span>
            </div>
          ))}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 18,
                height: 0,
                borderTop: `1.5px dashed ${t.inkSoft}`,
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 14, color: t.inkSoft }}>
              Correlation unit circle
            </span>
          </div>
        </div>
      </div>

      <ChartsContainer
        width={size.width}
        height={size.height - HEADER_H}
        series={series}
        xAxis={[
          {
            id: "pc1",
            scaleType: "linear",
            min: xMin,
            max: xMax,
            tickNumber: 11,
            height: X_AXIS_H,
            label: `PC1 (${pc1VarianceShare.toFixed(1)}% variance)`,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "pc2",
            scaleType: "linear",
            min: yMin,
            max: yMax,
            tickNumber: 9,
            width: Y_AXIS_W,
            label: `PC2 (${pc2VarianceShare.toFixed(1)}% variance)`,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        margin={MARGIN}
        skipAnimation
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal vertical />
        <ScatterPlot />
        <LoadingArrows />
        <ChartsXAxis axisId="pc1" />
        <ChartsYAxis axisId="pc2" />
        <ChartsTooltip trigger="item" />
      </ChartsContainer>
    </div>
  );
}
