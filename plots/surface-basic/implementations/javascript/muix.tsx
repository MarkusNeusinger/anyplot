// anyplot.ai
// surface-basic: Basic 3D Surface Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-10

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEIGHT_SCALE = 3.2;
const ISO_ANGLE = Math.PI / 6;
const COS_ISO = Math.cos(ISO_ANGLE);
const SIN_ISO = Math.sin(ISO_ANGLE);
const Z_TICKS = [-1.0, -0.5, 0.0, 0.5, 1.0];

// Columns: set these to your data's column names
const X_COORD = "x"; // role: x
const Y_COORD = "y"; // role: y
const Z_HEIGHT = "z = sin(x)·cos(y)"; // role: z

// Data: replace this block with your own records
const gridNGen = 30;
const xMinGen = -3;
const xMaxGen = 3;
const yMinGen = -3;
const yMaxGen = 3;

const data: Array<Record<string, number>> = [];
for (let row = 0; row < gridNGen; row += 1) {
  const y = yMinGen + (row / (gridNGen - 1)) * (yMaxGen - yMinGen);
  for (let col = 0; col < gridNGen; col += 1) {
    const x = xMinGen + (col / (gridNGen - 1)) * (xMaxGen - xMinGen);
    const z = Math.sin(x) * Math.cos(y);
    data.push({
      [X_COORD]: Number(x.toFixed(4)),
      [Y_COORD]: Number(y.toFixed(4)),
      [Z_HEIGHT]: Number(z.toFixed(4)),
    });
  }
}

// Plot: reads only data and the constants above
const uniqueXs: number[] = [];
const uniqueYs: number[] = [];
for (const row of data) {
  const xv = Number(row[X_COORD]);
  const yv = Number(row[Y_COORD]);
  if (!uniqueXs.includes(xv)) uniqueXs.push(xv);
  if (!uniqueYs.includes(yv)) uniqueYs.push(yv);
}
uniqueXs.sort((a, b) => a - b);
uniqueYs.sort((a, b) => a - b);

const nx = uniqueXs.length;
const ny = uniqueYs.length;
const xMin = uniqueXs[0];
const xMax = uniqueXs[nx - 1];
const yMin = uniqueYs[0];
const yMax = uniqueYs[ny - 1];

const grid: Array<
  Array<{ x: number; y: number; z: number; px: number; py: number }>
> = Array.from({ length: ny }, () => []);

for (const row of data) {
  const x = Number(row[X_COORD]);
  const y = Number(row[Y_COORD]);
  const z = Number(row[Z_HEIGHT]);
  const rIdx = uniqueYs.indexOf(y);
  const px = (x - y) * COS_ISO;
  const py = z * HEIGHT_SCALE - (x + y) * SIN_ISO;
  grid[rIdx].push({ x, y, z, px, py });
}
for (const line of grid) {
  line.sort((a, b) => a.x - b.x);
}

const allNodes = grid.flat();
const heightValues = allNodes.map((n) => n.z);
const heightMin = Math.min(...heightValues);
const heightMax = Math.max(...heightValues);

const divR0 = parseInt(t.div[0].slice(1, 3), 16);
const divG0 = parseInt(t.div[0].slice(3, 5), 16);
const divB0 = parseInt(t.div[0].slice(5, 7), 16);
const divR1 = parseInt(t.div[1].slice(1, 3), 16);
const divG1 = parseInt(t.div[1].slice(3, 5), 16);
const divB1 = parseInt(t.div[1].slice(5, 7), 16);
const divR2 = parseInt(t.div[2].slice(1, 3), 16);
const divG2 = parseInt(t.div[2].slice(3, 5), 16);
const divB2 = parseInt(t.div[2].slice(5, 7), 16);

const quads: Array<{
  points: Array<{ px: number; py: number }>;
  depthKey: number;
  fill: string;
}> = [];

for (let r = 0; r < ny - 1; r += 1) {
  for (let c = 0; c < nx - 1; c += 1) {
    const p00 = grid[r][c];
    const p10 = grid[r][c + 1];
    const p11 = grid[r + 1][c + 1];
    const p01 = grid[r + 1][c];
    const avgHeight = (p00.z + p10.z + p11.z + p01.z) / 4;
    const unitT = Math.min(
      1,
      Math.max(0, (avgHeight - heightMin) / (heightMax - heightMin || 1)),
    );
    let rCh = 0;
    let gCh = 0;
    let bCh = 0;
    if (unitT <= 0.5) {
      const f = unitT / 0.5;
      rCh = Math.round(divR0 + (divR1 - divR0) * f);
      gCh = Math.round(divG0 + (divG1 - divG0) * f);
      bCh = Math.round(divB0 + (divB1 - divB0) * f);
    } else {
      const f = (unitT - 0.5) / 0.5;
      rCh = Math.round(divR1 + (divR2 - divR1) * f);
      gCh = Math.round(divG1 + (divG2 - divG1) * f);
      bCh = Math.round(divB1 + (divB2 - divB1) * f);
    }
    quads.push({
      points: [p00, p10, p11, p01],
      depthKey: r + c,
      fill: `rgb(${rCh}, ${gCh}, ${bCh})`,
    });
  }
}
quads.sort((a, b) => a.depthKey - b.depthKey);

const rawPxMin = Math.min(...allNodes.map((n) => n.px));
const rawPxMax = Math.max(...allNodes.map((n) => n.px));
const rawPyMin = Math.min(...allNodes.map((n) => n.py));
const rawPyMax = Math.max(...allNodes.map((n) => n.py));
const padX = (rawPxMax - rawPxMin) * 0.12;
const padY = (rawPyMax - rawPyMin) * 0.1;
const pxMin = rawPxMin - padX;
const pxMax = rawPxMax + padX;
const pyMin = rawPyMin - padY * 1.4;
const pyMax = rawPyMax + padY * 2.6;

const zBotPoint = {
  px: (xMin - yMin) * COS_ISO,
  py: heightMin * HEIGHT_SCALE - (xMin + yMin) * SIN_ISO,
};
const zTopPoint = {
  px: (xMin - yMin) * COS_ISO,
  py: heightMax * HEIGHT_SCALE - (xMin + yMin) * SIN_ISO,
};
const xEndPoint = {
  px: (xMax - yMin) * COS_ISO,
  py: 0 * HEIGHT_SCALE - (xMax + yMin) * SIN_ISO,
};
const yEndPoint = {
  px: (xMin - yMax) * COS_ISO,
  py: 0 * HEIGHT_SCALE - (xMin + yMax) * SIN_ISO,
};
const farCorner = {
  px: (xMax - yMax) * COS_ISO,
  py: 0 * HEIGHT_SCALE - (xMax + yMax) * SIN_ISO,
};

function SurfaceMesh() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;

  return (
    <g>
      {quads.map((quad, i) => (
        <polygon
          key={`quad-${quad.depthKey}-${i}`}
          points={quad.points
            .map((p) => `${xScale(p.px)},${yScale(p.py)}`)
            .join(" ")}
          fill={quad.fill}
          stroke={t.pageBg}
          strokeWidth={0.6}
        />
      ))}
    </g>
  );
}

function IsoFrame() {
  const { width, height } = window.ANYPLOT_SIZE;
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;

  const zBot = { x: xScale(zBotPoint.px), y: yScale(zBotPoint.py) };
  const zTop = { x: xScale(zTopPoint.px), y: yScale(zTopPoint.py) };
  const xEnd = { x: xScale(xEndPoint.px), y: yScale(xEndPoint.py) };
  const yEnd = { x: xScale(yEndPoint.px), y: yScale(yEndPoint.py) };
  const far = { x: xScale(farCorner.px), y: yScale(farCorner.py) };

  const cbW = 360;
  const cbH = 14;
  const cbX = (width - cbW) / 2;
  const cbY = height - 48;

  return (
    <g>
      <line
        x1={xEnd.x}
        y1={xEnd.y}
        x2={far.x}
        y2={far.y}
        stroke={t.grid}
        strokeWidth={1.5}
        strokeDasharray="6 5"
      />
      <line
        x1={yEnd.x}
        y1={yEnd.y}
        x2={far.x}
        y2={far.y}
        stroke={t.grid}
        strokeWidth={1.5}
        strokeDasharray="6 5"
      />
      <line
        x1={zBot.x}
        y1={zBot.y}
        x2={zTop.x}
        y2={zTop.y}
        stroke={t.inkSoft}
        strokeWidth={2}
      />
      {Z_TICKS.map((zt) => {
        const ty = yScale(zt * HEIGHT_SCALE - (xMin + yMin) * SIN_ISO);
        return (
          <g key={zt}>
            <line
              x1={zBot.x - 6}
              y1={ty}
              x2={zBot.x}
              y2={ty}
              stroke={t.inkSoft}
              strokeWidth={1.5}
            />
            <text
              x={zBot.x - 10}
              y={ty}
              fill={t.inkSoft}
              fontSize={14}
              textAnchor="end"
              dominantBaseline="middle"
            >
              {zt.toFixed(1)}
            </text>
          </g>
        );
      })}
      <text
        x={xEnd.x + 36}
        y={xEnd.y + 10}
        fill={t.ink}
        fontSize={16}
        fontWeight={600}
        textAnchor="middle"
      >
        {`${X_COORD} · [${xMin}, ${xMax}]`}
      </text>
      <text
        x={yEnd.x - 36}
        y={yEnd.y + 10}
        fill={t.ink}
        fontSize={16}
        fontWeight={600}
        textAnchor="middle"
      >
        {`${Y_COORD} · [${yMin}, ${yMax}]`}
      </text>
      <text
        x={zTop.x}
        y={zTop.y - 22}
        fill={t.ink}
        fontSize={16}
        fontWeight={600}
        textAnchor="middle"
      >
        {Z_HEIGHT}
      </text>

      <defs>
        <linearGradient id="surfHeightGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={t.div[0]} />
          <stop offset="50%" stopColor={t.div[1]} />
          <stop offset="100%" stopColor={t.div[2]} />
        </linearGradient>
      </defs>
      <rect
        x={cbX}
        y={cbY}
        width={cbW}
        height={cbH}
        rx={3}
        fill="url(#surfHeightGrad)"
      />
      <text
        x={cbX - 10}
        y={cbY + cbH / 2}
        fill={t.inkSoft}
        fontSize={15}
        textAnchor="end"
        dominantBaseline="middle"
      >
        {`${heightMin.toFixed(2)} (valley)`}
      </text>
      <text
        x={cbX + cbW + 10}
        y={cbY + cbH / 2}
        fill={t.inkSoft}
        fontSize={15}
        textAnchor="start"
        dominantBaseline="middle"
      >
        {`${heightMax.toFixed(2)} (peak)`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg }}>
      <ChartsContainer
        width={width}
        height={height}
        series={[]}
        xAxis={[
          {
            id: "iso-x",
            scaleType: "linear",
            min: pxMin,
            max: pxMax,
            position: "none",
          },
        ]}
        yAxis={[
          {
            id: "iso-y",
            scaleType: "linear",
            min: pyMin,
            max: pyMax,
            position: "none",
          },
        ]}
        margin={{ top: 70, right: 70, bottom: 90, left: 70 }}
      >
        <text
          x={width / 2}
          y={38}
          textAnchor="middle"
          fontSize={22}
          fontWeight={600}
          fill={t.ink}
        >
          Response Surface z = sin(x)·cos(y) · surface-basic · javascript · muix · anyplot.ai
        </text>
        <SurfaceMesh />
        <IsoFrame />
      </ChartsContainer>
    </div>
  );
}
