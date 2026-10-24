// anyplot.ai
// heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-25
//# anyplot-orientation: square
import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const { width, height } = window.ANYPLOT_SIZE;
const TITLE = "heatmap-mandelbrot · javascript · muix · anyplot.ai";
const ESCAPE_RADIUS_SQ = 4;
const COLOR_GAMMA = 0.42;
const INTERIOR_HEX = "#1A1A17";
const LUT_SIZE = 512;
const GRADIENT_STOPS = [0, 0.25, 0.5, 0.75, 1];

const BASE_TOP = 96;
const BASE_BOTTOM = 164;
const BASE_LEFT = 80;
const BASE_RIGHT = 160;
const X_AXIS_H = 60;
const Y_AXIS_W = 80;

// Data: replace this block with your own parameters
const X_MIN = -2.0; // role: x_min
const X_MAX = 0.5; // role: x_max
const Y_MIN = -1.25; // role: y_min
const Y_MAX = 1.25; // role: y_max
const MAX_ITERATIONS = 100; // role: max_iterations

// Plot: reads only data and the constants above
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

const SUBTITLE = `z(n+1) = z(n)² + c · Re(c) ∈ [${X_MIN.toFixed(2)}, ${X_MAX.toFixed(2)}], Im(c) ∈ [${Y_MIN.toFixed(2)}, ${Y_MAX.toFixed(2)}] · max ${MAX_ITERATIONS} iterations`;

const maxAreaW = width - BASE_LEFT - BASE_RIGHT - Y_AXIS_W;
const maxAreaH = height - BASE_TOP - BASE_BOTTOM - X_AXIS_H;
const complexAspect = (X_MAX - X_MIN) / (Y_MAX - Y_MIN);
const targetAreaW = complexAspect >= 1 ? maxAreaW : Math.round(maxAreaH * complexAspect);
const targetAreaH = complexAspect >= 1 ? Math.round(maxAreaW / complexAspect) : maxAreaH;
const extraW = maxAreaW - targetAreaW;
const extraH = maxAreaH - targetAreaH;
const margin = {
  top: BASE_TOP + Math.floor(extraH / 2),
  bottom: BASE_BOTTOM + Math.ceil(extraH / 2),
  left: BASE_LEFT + Math.floor(extraW / 2),
  right: BASE_RIGHT + Math.ceil(extraW / 2),
};

function MandelbrotLayer() {
  const { left, top, width: areaW, height: areaH } = useDrawingArea();
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);

  React.useLayoutEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const pxW = Math.round(areaW * dpr);
    const pxH = Math.round(areaH * dpr);
    canvas.width = pxW;
    canvas.height = pxH;
    const ctx = canvas.getContext("2d")!;
    const image = ctx.createImageData(pxW, pxH);
    const pixels = image.data;

    for (let py = 0; py < pxH; py++) {
      const im0 = Y_MAX - (py / (pxH - 1)) * (Y_MAX - Y_MIN);
      for (let px = 0; px < pxW; px++) {
        const re0 = X_MIN + (px / (pxW - 1)) * (X_MAX - X_MIN);

        let zr = 0;
        let zi = 0;
        let n = 0;
        while (n < MAX_ITERATIONS && zr * zr + zi * zi <= ESCAPE_RADIUS_SQ) {
          const zr2 = zr * zr - zi * zi + re0;
          zi = 2 * zr * zi + im0;
          zr = zr2;
          n++;
        }

        const idx = (py * pxW + px) * 4;
        if (n >= MAX_ITERATIONS) {
          pixels[idx] = interiorR;
          pixels[idx + 1] = interiorG;
          pixels[idx + 2] = interiorB;
        } else {
          const magSq = zr * zr + zi * zi;
          const smoothN =
            n + 1 - Math.log(Math.log(Math.sqrt(magSq))) / Math.LN2;
          const frac = Math.max(0, Math.min(1, smoothN / MAX_ITERATIONS));
          const lutIdx = Math.round(frac * (LUT_SIZE - 1));
          const [r, g, b] = COLOR_LUT[lutIdx];
          pixels[idx] = r;
          pixels[idx + 1] = g;
          pixels[idx + 2] = b;
        }
        pixels[idx + 3] = 255;
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
        Smooth escape-time scale (1–{MAX_ITERATIONS} iterations)
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
        Slow escape ({MAX_ITERATIONS})
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

export default function Chart() {
  return (
    <ChartsContainer
      width={width}
      height={height}
      series={[]}
      skipAnimation
      margin={margin}
      xAxis={[
        {
          id: "real-axis",
          scaleType: "linear",
          min: X_MIN,
          max: X_MAX,
          height: X_AXIS_H,
          label: "Real Part Re(c)",
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 15, fill: t.ink },
        },
      ]}
      yAxis={[
        {
          id: "imag-axis",
          scaleType: "linear",
          min: Y_MIN,
          max: Y_MAX,
          width: Y_AXIS_W,
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
