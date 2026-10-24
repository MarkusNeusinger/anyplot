// anyplot.ai
// heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-25
//# anyplot-orientation: square

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Constants
const X_MIN_COL = "x_min";
const X_MAX_COL = "x_max";
const Y_MIN_COL = "y_min";
const Y_MAX_COL = "y_max";
const MAX_ITER_COL = "max_iterations";

const ESCAPE_RADIUS_SQ = 4;
const COLOR_GAMMA = 0.42;
const INTERIOR_HEX = "#1A1A17";
const LUT_SIZE = 512;
const GRADIENT_STOPS = [0, 0.25, 0.5, 0.75, 1];

// Data
const DATA = [
  {
    [X_MIN_COL]: -2.05,
    [X_MAX_COL]: 0.45,
    [Y_MIN_COL]: -1.25,
    [Y_MAX_COL]: 1.25,
    [MAX_ITER_COL]: 100,
  },
];

const config = DATA[0];
const xMin = config[X_MIN_COL];
const xMax = config[X_MAX_COL];
const yMin = config[Y_MIN_COL];
const yMax = config[Y_MAX_COL];
const maxIterations = config[MAX_ITER_COL];

const seqLowNum = parseInt(t.seq[0].slice(1), 16);
const seqHighNum = parseInt(t.seq[1].slice(1), 16);
const lowR = (seqLowNum >> 16) & 255;
const lowG = (seqLowNum >> 8) & 255;
const lowB = seqLowNum & 255;
const highR = (seqHighNum >> 16) & 255;
const highG = (seqHighNum >> 8) & 255;
const highB = seqHighNum & 255;

const interiorNum = parseInt(INTERIOR_HEX.slice(1), 16);
const interiorR = (interiorNum >> 16) & 255;
const interiorG = (interiorNum >> 8) & 255;
const interiorB = interiorNum & 255;

const COLOR_LUT: Array<[number, number, number]> = [];
for (let i = 0; i < LUT_SIZE; i++) {
  const frac = i / (LUT_SIZE - 1);
  const gFrac = Math.pow(frac, COLOR_GAMMA);
  COLOR_LUT.push([
    Math.round(lowR + (highR - lowR) * gFrac),
    Math.round(lowG + (highG - lowG) * gFrac),
    Math.round(lowB + (highB - lowB) * gFrac),
  ]);
}

const stopColors = GRADIENT_STOPS.map((stop) => {
  const idx = Math.round(stop * (LUT_SIZE - 1));
  const [r, g, b] = COLOR_LUT[idx];
  return { offset: `${stop * 100}%`, color: `rgb(${r},${g},${b})` };
});

const TITLE = "heatmap-mandelbrot · javascript · muix · anyplot.ai";
const SUBTITLE = `z(n+1) = z(n)² + c · Re(c) ∈ [${xMin.toFixed(2)}, ${xMax.toFixed(2)}], Im(c) ∈ [${yMin.toFixed(2)}, ${yMax.toFixed(2)}] · max ${maxIterations} iterations`;

function MandelbrotLayer() {
  const { left, top, width: areaW, height: areaH } = useDrawingArea();
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);

  React.useLayoutEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || areaW <= 0 || areaH <= 0) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const pxW = Math.max(1, Math.round(areaW * dpr));
    const pxH = Math.max(1, Math.round(areaH * dpr));
    canvas.width = pxW;
    canvas.height = pxH;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const image = ctx.createImageData(pxW, pxH);
    const data = image.data;

    for (let py = 0; py < pxH; py++) {
      const im0 = yMax - (py / Math.max(1, pxH - 1)) * (yMax - yMin);
      for (let px = 0; px < pxW; px++) {
        const re0 = xMin + (px / Math.max(1, pxW - 1)) * (xMax - xMin);

        let zr = 0;
        let zi = 0;
        let n = 0;
        while (n < maxIterations && zr * zr + zi * zi <= ESCAPE_RADIUS_SQ) {
          const zr2 = zr * zr - zi * zi + re0;
          zi = 2 * zr * zi + im0;
          zr = zr2;
          n++;
        }

        const idx = (py * pxW + px) * 4;
        if (n >= maxIterations) {
          data[idx] = interiorR;
          data[idx + 1] = interiorG;
          data[idx + 2] = interiorB;
        } else {
          const magSq = zr * zr + zi * zi;
          const smoothN =
            n + 1 - Math.log(Math.log(Math.sqrt(magSq))) / Math.LN2;
          const frac = Math.max(0, Math.min(1, smoothN / maxIterations));
          const lutIdx = Math.min(
            LUT_SIZE - 1,
            Math.max(0, Math.round(frac * (LUT_SIZE - 1))),
          );
          const [r, g, b] = COLOR_LUT[lutIdx];
          data[idx] = r;
          data[idx + 1] = g;
          data[idx + 2] = b;
        }
        data[idx + 3] = 255;
      }
    }
    ctx.putImageData(image, 0, 0);
  }, [areaW, areaH]);

  const drawingBottom = top + areaH;
  const barX = left;
  const barW = areaW * 0.62;
  const barH = 22;
  const titleY = drawingBottom + 86;
  const barY = titleY + 12;
  const endLabelY = barY + barH + 22;
  const swatchSize = 22;
  const swatchX = left + areaW * 0.72;
  const swatchY = barY;

  return (
    <g>
      <defs>
        <linearGradient id="mandelbrotRamp" x1="0" y1="0" x2="1" y2="0">
          {stopColors.map((s) => (
            <stop key={s.offset} offset={s.offset} stopColor={s.color} />
          ))}
        </linearGradient>
      </defs>

      <text
        x={width / 2}
        y={42}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>
      <text
        x={width / 2}
        y={70}
        textAnchor="middle"
        fontSize={15}
        fill={t.inkSoft}
      >
        {SUBTITLE}
      </text>

      <foreignObject x={left} y={top} width={areaW} height={areaH}>
        <canvas
          ref={canvasRef}
          style={{ width: "100%", height: "100%", display: "block" }}
        />
      </foreignObject>
      <rect
        x={left}
        y={top}
        width={areaW}
        height={areaH}
        fill="none"
        stroke={t.grid}
        strokeWidth={1}
      />

      <text
        x={barX + barW / 2}
        y={titleY}
        textAnchor="middle"
        fontSize={14}
        fontWeight={600}
        fill={t.ink}
      >
        Smooth escape-time scale (1–{maxIterations} iterations)
      </text>
      <rect
        x={barX}
        y={barY}
        width={barW}
        height={barH}
        fill="url(#mandelbrotRamp)"
        stroke={t.grid}
        strokeWidth={1}
        rx={4}
      />
      <text
        x={barX}
        y={endLabelY}
        textAnchor="start"
        fontSize={14}
        fill={t.inkSoft}
      >
        Fast escape (1)
      </text>
      <text
        x={barX + barW}
        y={endLabelY}
        textAnchor="end"
        fontSize={14}
        fill={t.inkSoft}
      >
        Slow escape ({maxIterations})
      </text>

      <rect
        x={swatchX}
        y={swatchY}
        width={swatchSize}
        height={swatchSize}
        fill={INTERIOR_HEX}
        stroke={t.ink}
        strokeWidth={1.5}
        rx={4}
      />
      <text
        x={swatchX + swatchSize + 10}
        y={swatchY + swatchSize / 2 + 5}
        textAnchor="start"
        fontSize={14}
        fontWeight={600}
        fill={t.ink}
      >
        Bounded interior
      </text>
      <text
        x={swatchX + swatchSize + 10}
        y={endLabelY}
        textAnchor="start"
        fontSize={14}
        fill={t.inkSoft}
      >
        Never escapes (|z| ≤ 2)
      </text>
    </g>
  );
}

// Equal 880×880 drawing area so Re(c) and Im(c) share an exact 1:1 scale
export default function Chart() {
  return (
    <ChartsContainer
      width={width}
      height={height}
      series={[]}
      skipAnimation
      margin={{ top: 96, right: 160, bottom: 164, left: 80 }}
      xAxis={[
        {
          id: "real-axis",
          scaleType: "linear",
          min: xMin,
          max: xMax,
          height: 60,
          label: "Real Part Re(c)",
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 15, fill: t.ink },
        },
      ]}
      yAxis={[
        {
          id: "imag-axis",
          scaleType: "linear",
          min: yMin,
          max: yMax,
          width: 80,
          label: "Imaginary Part Im(c)",
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 15, fill: t.ink },
        },
      ]}
    >
      <MandelbrotLayer />
      <ChartsXAxis axisId="real-axis" />
      <ChartsYAxis axisId="imag-axis" />
    </ChartsContainer>
  );
}
