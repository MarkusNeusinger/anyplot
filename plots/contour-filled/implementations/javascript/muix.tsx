// anyplot.ai
// contour-filled: Filled Contour Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Updated: 2026-09-05

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;

// Constants
const TITLE = "contour-filled · javascript · muix · anyplot.ai";
const FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
const NUM_BANDS = 10;

// Columns: set these to your data's column names
const X = "Zonal offset (°)"; // role: x
const Y = "Meridional offset (°)"; // role: y
const Z = "Temperature anomaly (°C)"; // role: z

// Data: replace this block with your own records
const data = (() => {
  const sampleGrid = 36;
  const sampleSpan = 6;
  const rows: Record<string, number>[] = [];
  for (let j = 0; j < sampleGrid; j += 1) {
    const y = -sampleSpan / 2 + (j / (sampleGrid - 1)) * sampleSpan;
    for (let i = 0; i < sampleGrid; i += 1) {
      const x = -sampleSpan / 2 + (i / (sampleGrid - 1)) * sampleSpan;
      const warm = 2.0 * Math.exp(-((x - 1.3) * (x - 1.3) + (y - 0.9) * (y - 0.9)) * 0.55);
      const cool = -1.6 * Math.exp(-((x + 1.4) * (x + 1.4) + (y + 1.0) * (y + 1.0)) * 0.65);
      rows.push({ [X]: x, [Y]: y, [Z]: warm + cool });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const xs = Array.from(new Set(data.map((d) => Number(d[X])))).sort((a, b) => a - b);
const ys = Array.from(new Set(data.map((d) => Number(d[Y])))).sort((a, b) => a - b);
const nX = xs.length;
const nY = ys.length;
const xMin = xs[0];
const xMax = xs[nX - 1];
const yMin = ys[0];
const yMax = ys[nY - 1];

const zGrid = Array.from({ length: nY }, () => new Array(nX).fill(NaN));
const xIndex = new Map(xs.map((v, i) => [v, i]));
const yIndex = new Map(ys.map((v, j) => [v, j]));
for (const row of data) {
  const val = Number(row[Z]);
  if (Number.isFinite(val)) {
    zGrid[yIndex.get(Number(row[Y]))!][xIndex.get(Number(row[X]))!] = val;
  }
}

const validZ = data.map((d) => Number(d[Z])).filter((v) => Number.isFinite(v));
const zMin = Math.min(...validZ);
const zMax = Math.max(...validZ);
const vAbs = Math.max(Math.abs(zMin), Math.abs(zMax));
const SUBTITLE = `${Z} across ${nX}×${nY} grid · ${NUM_BANDS} filled contour bands`;

const divStops = [t.div[2], t.div[1], t.div[0]].map((hex) => {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
});

const levels = Array.from({ length: NUM_BANDS }, (_, k) => -vAbs + (k * 2 * vAbs) / NUM_BANDS);
const levelEdges = Array.from(
  { length: NUM_BANDS + 1 },
  (_, k) => -vAbs + (k * 2 * vAbs) / NUM_BANDS,
);

const bandColors = Array.from({ length: NUM_BANDS }, (_, k) => {
  const pos = k / (NUM_BANDS - 1);
  const [start, end, ratio] =
    pos < 0.5
      ? [divStops[0], divStops[1], pos / 0.5]
      : [divStops[1], divStops[2], (pos - 0.5) / 0.5];
  const r = Math.round(start[0] + (end[0] - start[0]) * ratio);
  const g = Math.round(start[1] + (end[1] - start[1]) * ratio);
  const b = Math.round(start[2] + (end[2] - start[2]) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
});

const triangles: { x: number; y: number; z: number }[][] = [];
for (let j = 0; j < nY - 1; j += 1) {
  for (let i = 0; i < nX - 1; i += 1) {
    const sw = { x: xs[i], y: ys[j], z: zGrid[j][i] };
    const se = { x: xs[i + 1], y: ys[j], z: zGrid[j][i + 1] };
    const ne = { x: xs[i + 1], y: ys[j + 1], z: zGrid[j + 1][i + 1] };
    const nw = { x: xs[i], y: ys[j + 1], z: zGrid[j + 1][i] };
    const center = {
      x: (sw.x + se.x) / 2,
      y: (sw.y + nw.y) / 2,
      z: (sw.z + se.z + ne.z + nw.z) / 4,
    };
    triangles.push([sw, se, center], [se, ne, center], [ne, nw, center], [nw, sw, center]);
  }
}

const validTriangles = triangles.filter(
  ([a, b, c]) => !Number.isNaN(a.z) && !Number.isNaN(b.z) && !Number.isNaN(c.z),
);

const bandGeometry: { x: number; y: number }[][][] = [];
const isolineGeometry: { x: number; y: number }[][][] = [];
for (let k = 1; k < NUM_BANDS; k += 1) {
  const threshold = levels[k];
  const polys: { x: number; y: number }[][] = [];
  const segments: { x: number; y: number }[][] = [];
  for (const [a, b, c] of validTriangles) {
    const inA = a.z >= threshold;
    const inB = b.z >= threshold;
    const inC = c.z >= threshold;
    const nIn = (inA ? 1 : 0) + (inB ? 1 : 0) + (inC ? 1 : 0);
    if (nIn === 0) continue;
    if (nIn === 3) {
      polys.push([a, b, c]);
      continue;
    }
    const rAB = b.z !== a.z ? (threshold - a.z) / (b.z - a.z) : 0.5;
    const ab = { x: a.x + rAB * (b.x - a.x), y: a.y + rAB * (b.y - a.y) };
    const rBC = c.z !== b.z ? (threshold - b.z) / (c.z - b.z) : 0.5;
    const bc = { x: b.x + rBC * (c.x - b.x), y: b.y + rBC * (c.y - b.y) };
    const rCA = a.z !== c.z ? (threshold - c.z) / (a.z - c.z) : 0.5;
    const ca = { x: c.x + rCA * (a.x - c.x), y: c.y + rCA * (a.y - c.y) };

    if (nIn === 1) {
      if (inA) {
        polys.push([a, ab, ca]);
        segments.push([ab, ca]);
      } else if (inB) {
        polys.push([b, bc, ab]);
        segments.push([bc, ab]);
      } else {
        polys.push([c, ca, bc]);
        segments.push([ca, bc]);
      }
    } else if (!inC) {
      polys.push([a, b, bc, ca]);
      segments.push([ca, bc]);
    } else if (!inA) {
      polys.push([b, c, ca, ab]);
      segments.push([ab, ca]);
    } else {
      polys.push([c, a, ab, bc]);
      segments.push([bc, ab]);
    }
  }
  bandGeometry.push(polys);
  isolineGeometry.push(segments);
}

function FilledContourLayer() {
  const xScale = useXScale("x") as any;
  const yScale = useYScale("y") as any;
  const { left, top, width, height } = useDrawingArea();

  const basePath = validTriangles
    .map(
      (tri) =>
        tri
          .map((p, k) => `${k === 0 ? "M" : "L"} ${xScale(p.x).toFixed(1)},${yScale(p.y).toFixed(1)}`)
          .join(" ") + " Z",
    )
    .join(" ");

  const barX = left + width + 36;
  const barW = 22;
  const barH = height * 0.78;
  const barTop = top + (height - barH) / 2;
  const stepH = barH / NUM_BANDS;

  return (
    <g fontFamily={FONT}>
      <path d={basePath} fill={bandColors[0]} stroke={bandColors[0]} strokeWidth={0.75} />
      {bandGeometry.map((polys, idx) => {
        const dPath = polys
          .map(
            (poly) =>
              poly
                .map((p, k) => {
                  const px = xScale(p.x).toFixed(1);
                  const py = yScale(p.y).toFixed(1);
                  return `${k === 0 ? "M" : "L"} ${px},${py}`;
                })
                .join(" ") + " Z",
          )
          .join(" ");
        return (
          <path
            key={`band-${idx}`}
            d={dPath}
            fill={bandColors[idx + 1]}
            stroke={bandColors[idx + 1]}
            strokeWidth={0.75}
          />
        );
      })}
      {isolineGeometry.map((segments, idx) => {
        const dPath = segments
          .map(([p0, p1]) => {
            const x0 = xScale(p0.x).toFixed(1);
            const y0 = yScale(p0.y).toFixed(1);
            const x1 = xScale(p1.x).toFixed(1);
            const y1 = yScale(p1.y).toFixed(1);
            return `M ${x0},${y0} L ${x1},${y1}`;
          })
          .join(" ");
        return (
          <path
            key={`iso-${idx}`}
            d={dPath}
            stroke={t.ink}
            strokeOpacity={0.28}
            strokeWidth={1}
            fill="none"
          />
        );
      })}

      {/* Discrete contour-band colorbar */}
      {bandColors.map((col, k) => {
        const y = barTop + (NUM_BANDS - 1 - k) * stepH;
        return (
          <rect
            key={`cb-${k}`}
            x={barX}
            y={y}
            width={barW}
            height={stepH + 0.5}
            fill={col}
          />
        );
      })}
      <rect
        x={barX}
        y={barTop}
        width={barW}
        height={barH}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={1.2}
      />
      {levelEdges.map((val, k) => {
        if (k % 2 !== 0) return null;
        const y = barTop + (NUM_BANDS - k) * stepH;
        return (
          <g key={`cbt-${k}`}>
            <line
              x1={barX + barW}
              y1={y}
              x2={barX + barW + 6}
              y2={y}
              stroke={t.inkSoft}
              strokeWidth={1.2}
            />
            <text
              x={barX + barW + 10}
              y={y}
              dominantBaseline="central"
              fontSize={14}
              fill={t.inkSoft}
            >
              {val >= 0 ? `+${val.toFixed(1)}` : val.toFixed(1)}
            </text>
          </g>
        );
      })}
      <text
        x={barX + barW + 68}
        y={barTop + barH / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={15}
        fontWeight={500}
        fill={t.ink}
        transform={`rotate(-90, ${barX + barW + 68}, ${barTop + barH / 2})`}
      >
        {Z}
      </text>
    </g>
  );
}

export default function Chart() {
  const chartW = SIZE.width - 48;
  const chartH = SIZE.height - 110;

  return (
    <Box
      sx={{
        width: SIZE.width,
        height: SIZE.height,
        bgcolor: t.pageBg,
        color: t.ink,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        pt: "18px",
        px: "24px",
        boxSizing: "border-box",
      }}
    >
      <Typography
        sx={{
          fontSize: 22,
          fontWeight: 700,
          color: t.ink,
          fontFamily: FONT,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        {TITLE}
      </Typography>
      <Typography
        sx={{
          fontSize: 15,
          color: t.inkSoft,
          fontFamily: FONT,
          textAlign: "center",
          mt: "4px",
          mb: "4px",
        }}
      >
        {SUBTITLE}
      </Typography>

      <ChartsContainer
        width={chartW}
        height={chartH}
        series={[]}
        margin={{ top: 20, right: 160, bottom: 20, left: 20 }}
        skipAnimation
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: 60,
            label: X,
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: yMin,
            max: yMax,
            width: 84,
            label: Y,
            labelStyle: { fontSize: 15, fill: t.ink, fontFamily: FONT },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft, fontFamily: FONT },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <FilledContourLayer />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>
    </Box>
  );
}
