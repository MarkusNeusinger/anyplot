import { useEffect, useRef } from 'react';

import Box from '@mui/material/Box';

import { oklchToRgb, starPoints } from 'src/sections/palette/paletteHelpers';
import type { WheelDot } from 'src/sections/palette/types';

const MAX_WHEEL_CHROMA = 0.28; // clamp for radial position normalisation across palettes
const WHEEL_RING_L = 0.72; // fixed OKLCH lightness for the hue-ring disk

export function ChromaWheel({
  size = 320,
  imprintDots,
  overlay,
  compact = false,
}: {
  size?: number;
  imprintDots: WheelDot[];
  overlay?: WheelDot[];
  /** Compact preview: hide angle ticks/labels, scale dots down, use more disk. */
  compact?: boolean;
}) {
  const cx = size / 2;
  const cy = size / 2;
  // The coloured disk runs to outerR; only a thin margin is left (just enough
  // for the angle labels in full mode). No second border ring beyond it.
  const outerR = size / 2 - (compact ? 4 : 22);
  const dotR = Math.min(7.5, Math.max(3, size * 0.024)); // scale with size so the small wheel stays clean
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const lastPaintRef = useRef<string>(''); // skip redundant repaints (StrictMode double-invoke / same-size re-render)

  // Project (hue°, chroma) → (x, y). Hue 0° at right (3 o'clock), increasing
  // counter-clockwise — matching the per-pixel disk painted below.
  const project = (H: number, C: number): { x: number; y: number } => {
    const rad = (H * Math.PI) / 180;
    const r = Math.min(C / MAX_WHEEL_CHROMA, 1) * outerR;
    return { x: cx + Math.cos(rad) * r, y: cy - Math.sin(rad) * r };
  };

  // Paint the hue ring per-pixel into a canvas: every pixel at (r, θ) is
  // oklch(WHEEL_RING_L, (r/outerR)·MAX_CHROMA, θ). Continuous → no facets, and
  // the chroma genuinely fades to neutral grey at the centre (matches the
  // matplotlib reference wheel rather than faking the fade with a bg overlay).
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    // The per-pixel disk is the same for a given (size, outerR); skip the
    // O(n²) trig repaint when nothing that affects it changed.
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    // Key includes dpr so a zoom / display change repaints at the right resolution.
    const paintKey = `${size}|${outerR}|${dpr}`;
    if (lastPaintRef.current === paintKey) return;
    const px = Math.round(size * dpr);
    canvas.width = px;
    canvas.height = px;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const img = ctx.createImageData(px, px);
    const data = img.data;
    const r0 = outerR * dpr;
    const cxp = cx * dpr;
    const cyp = cy * dpr;
    for (let y = 0; y < px; y++) {
      for (let x = 0; x < px; x++) {
        const dx = x - cxp;
        const dy = y - cyp;
        const r = Math.hypot(dx, dy);
        const idx = (y * px + x) * 4;
        if (r > r0) continue; // leave fully transparent outside the disk
        let theta = (Math.atan2(-dy, dx) * 180) / Math.PI;
        if (theta < 0) theta += 360;
        const c = Math.min(r / r0, 1) * MAX_WHEEL_CHROMA;
        const [rr, gg, bb] = oklchToRgb(WHEEL_RING_L, c, theta);
        data[idx] = rr;
        data[idx + 1] = gg;
        data[idx + 2] = bb;
        data[idx + 3] = r > r0 - dpr ? Math.round((255 * (r0 - r)) / dpr) : 255; // 1px AA edge
      }
    }
    ctx.putImageData(img, 0, 0);
    lastPaintRef.current = paintKey;
  }, [size, outerR, cx, cy]);

  // Chroma envelope — the band all imprint hues fall inside (low-chroma corridor).
  const cs = imprintDots.map(d => d.C);
  const rInner = (Math.min(...cs) / MAX_WHEEL_CHROMA) * outerR;
  const rOuter = (Math.max(...cs) / MAX_WHEEL_CHROMA) * outerR;
  const rMid = (rInner + rOuter) / 2;
  const ticks = compact ? [] : [0, 90, 180, 270];

  return (
    <Box sx={{ position: 'relative', width: size, height: size }}>
      <Box
        component="canvas"
        ref={canvasRef}
        sx={{
          position: 'absolute',
          inset: 0,
          width: size,
          height: size,
          borderRadius: '50%',
        }}
      />
      <Box
        component="svg"
        viewBox={`0 0 ${size} ${size}`}
        sx={{ position: 'absolute', inset: 0, overflow: 'visible' }}
      >
        {/* Crisp ring exactly at the coloured-disk edge — no outer moat / second rim */}
        <circle cx={cx} cy={cy} r={outerR} fill="none" stroke="var(--rule)" strokeWidth={1} />

        {/* Low-chroma corridor: shaded annulus + dashed edges */}
        <circle
          cx={cx}
          cy={cy}
          r={rMid}
          fill="none"
          stroke="var(--ink)"
          strokeOpacity={0.1}
          strokeWidth={Math.max(0, rOuter - rInner)}
        />
        <circle
          cx={cx}
          cy={cy}
          r={rInner}
          fill="none"
          stroke="var(--ink)"
          strokeOpacity={0.28}
          strokeWidth={1}
          strokeDasharray="2 3"
        />
        <circle
          cx={cx}
          cy={cy}
          r={rOuter}
          fill="none"
          stroke="var(--ink)"
          strokeOpacity={0.28}
          strokeWidth={1}
          strokeDasharray="2 3"
        />

        {/* Angle ticks + labels (0° = 3 o'clock, CCW) */}
        {ticks.map(deg => {
          const rad = (deg * Math.PI) / 180;
          const x1 = cx + Math.cos(rad) * outerR;
          const y1 = cy - Math.sin(rad) * outerR;
          const x2 = cx + Math.cos(rad) * (outerR + 5);
          const y2 = cy - Math.sin(rad) * (outerR + 5);
          const lx = cx + Math.cos(rad) * (outerR + 15);
          const ly = cy - Math.sin(rad) * (outerR + 15);
          return (
            <g key={deg}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--ink-muted)" strokeWidth={1} />
              <text
                x={lx}
                y={ly}
                fontSize={11}
                fontWeight={600}
                fill="var(--ink-soft)"
                textAnchor="middle"
                dominantBaseline="middle"
                style={{ fontFamily: 'monospace' }}
              >
                {deg}°
              </text>
            </g>
          );
        })}

        {/* Overlay palette (hollow rings) — below imprint dots so imprint stays dominant */}
        {overlay &&
          overlay.map((d, i) => {
            const { x, y } = project(d.H, d.C);
            return (
              <g key={`o-${i}`}>
                <title>{d.hex}</title>
                <circle
                  cx={x}
                  cy={y}
                  r={dotR - 1}
                  fill="none"
                  stroke="var(--bg-page)"
                  strokeWidth={3}
                  opacity={0.9}
                />
                <circle
                  cx={x}
                  cy={y}
                  r={dotR - 1}
                  fill="none"
                  stroke={d.hex}
                  strokeWidth={2.25}
                  opacity={0.95}
                />
              </g>
            );
          })}

        {/* Imprint dots — white halo + filled dot; slot 0 (brand) drawn as a star */}
        {imprintDots.map((d, i) => {
          const { x, y } = project(d.H, d.C);
          const label = d.name ? `${d.name} · ${d.hex}` : d.hex;
          if (i === 0) {
            return (
              <g key={i} style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.55))' }}>
                <title>{`★ ${label}`}</title>
                <polygon
                  points={starPoints(x, y, dotR + 2.5, (dotR + 2.5) / 2.3)}
                  fill={d.hex}
                  stroke="var(--ink)"
                  strokeWidth={1.5}
                  strokeLinejoin="round"
                  style={{ cursor: 'pointer' }}
                />
              </g>
            );
          }
          return (
            <g key={i} style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.55))' }}>
              <title>{label}</title>
              <circle cx={x} cy={y} r={dotR + 1} fill="var(--bg-page)" />
              <circle
                cx={x}
                cy={y}
                r={dotR}
                fill={d.hex}
                stroke="var(--bg-page)"
                strokeWidth={1}
                style={{ cursor: 'pointer' }}
              />
            </g>
          );
        })}
      </Box>
    </Box>
  );
}
