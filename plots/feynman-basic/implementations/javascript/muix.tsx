// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-24

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SIZE = window.ANYPLOT_SIZE;
const TITLE = "feynman-basic · javascript · muix · anyplot.ai";
const FOOTER_NOTE =
  "Vertex dots mark interaction points · arrows show particle (forward) vs antiparticle (backward) flow in time";
const TIME_AXIS_LABEL = "time";

const FONT =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

const X_PAD_SHARE = 0.095;
const Y_TOP_PAD_SHARE = 0.67;
const Y_BOTTOM_PAD_SHARE = 0.83;
const TIME_AXIS_DROP_SHARE = 0.25;
const STYLE_KEY_DROP_SHARE = 0.54;
const PHOTON_WAVES = 6;
const PHOTON_AMP_PX = 12;
const GLUON_LOOPS = 8;
const GLUON_R_PX = 9;
const KEY_SWATCH_W_PX = 60;
const KEY_WAVES = 2.5;
const KEY_AMP_PX = 8;

const STYLE_KEY: { kind: "fermion" | "photon" | "gluon" | "boson"; label: string }[] = [
  { kind: "fermion", label: "Fermion (e⁻, q, …)" },
  { kind: "photon", label: "Photon (γ)" },
  { kind: "gluon", label: "Gluon (g)" },
  { kind: "boson", label: "Scalar boson (H)" },
];

// Data: replace this block with your own parameters
const VERTICES = [ // role: vertices
  { id: "eIn", x: 8, y: 24, isInteraction: false },
  { id: "posIn", x: 8, y: 0, isInteraction: false },
  { id: "v1", x: 34, y: 12, isInteraction: true },
  { id: "v2", x: 66, y: 12, isInteraction: true },
  { id: "muOut", x: 92, y: 24, isInteraction: false },
  { id: "antiMuOut", x: 92, y: 0, isInteraction: false },
];

const PARTICLES: {
  id: string;
  type: "fermion" | "photon" | "gluon" | "boson";
  label: string;
  anti: boolean;
}[] = [ // role: particles
  { id: "e-", type: "fermion", label: "e⁻", anti: false },
  { id: "e+", type: "fermion", label: "e⁺", anti: true },
  { id: "gamma", type: "photon", label: "γ*", anti: false },
  { id: "mu-", type: "fermion", label: "μ⁻", anti: false },
  { id: "mu+", type: "fermion", label: "μ⁺", anti: true },
];

const PROPAGATORS = [ // role: propagators
  { fromVertex: "eIn", toVertex: "v1", particleId: "e-" },
  { fromVertex: "posIn", toVertex: "v1", particleId: "e+" },
  { fromVertex: "v1", toVertex: "v2", particleId: "gamma" },
  { fromVertex: "v2", toVertex: "muOut", particleId: "mu-" },
  { fromVertex: "v2", toVertex: "antiMuOut", particleId: "mu+" },
];

// Plot: reads only data and the constants above
const vertexMap = new Map(VERTICES.map((v) => [v.id, v]));
const particleMap = new Map(PARTICLES.map((p) => [p.id, p]));

const typeColorMap = new Map<string, string>();
STYLE_KEY.forEach((entry, idx) => {
  typeColorMap.set(entry.kind, t.palette[idx]);
});

const vxValues = VERTICES.map((v) => v.x);
const vyValues = VERTICES.map((v) => v.y);
const minVx = Math.min(...vxValues);
const maxVx = Math.max(...vxValues);
const minVy = Math.min(...vyValues);
const maxVy = Math.max(...vyValues);
const vxSpan = maxVx - minVx;
const vySpan = maxVy - minVy;
const midVx = (minVx + maxVx) / 2;

const xDomainMin = minVx - vxSpan * X_PAD_SHARE;
const xDomainMax = maxVx + vxSpan * X_PAD_SHARE;
const yDomainMin = minVy - vySpan * Y_BOTTOM_PAD_SHARE;
const yDomainMax = maxVy + vySpan * Y_TOP_PAD_SHARE;

const timeAxisY = minVy - vySpan * TIME_AXIS_DROP_SHARE;
const styleKeyY = minVy - vySpan * STYLE_KEY_DROP_SHARE;

const interactionVertices = VERTICES.filter((v) => v.isInteraction);

const inLabels: string[] = [];
const internalLabels: string[] = [];
const outLabels: string[] = [];
for (const prop of PROPAGATORS) {
  const fromV = vertexMap.get(prop.fromVertex)!;
  const toV = vertexMap.get(prop.toVertex)!;
  const p = particleMap.get(prop.particleId)!;
  if (!fromV.isInteraction) inLabels.push(p.label);
  else if (!toV.isInteraction) outLabels.push(p.label);
  else internalLabels.push(p.label);
}
const subtitle = `${inLabels.join(" + ")} → ${internalLabels.join(" + ")} → ${outLabels.join(" + ")} · ${interactionVertices.length} interaction vertices, ${PROPAGATORS.length} propagators`;

function FeynmanCanvas() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;

  const fermionColor = typeColorMap.get("fermion")!;

  return (
    <g fontFamily={FONT}>
      <defs>
        <marker
          id="arrow-fermion"
          markerWidth="11"
          markerHeight="11"
          refX="8"
          refY="5.5"
          orient="auto"
          markerUnits="userSpaceOnUse"
        >
          <path d="M0,0 L11,5.5 L0,11 Z" fill={fermionColor} />
        </marker>
        <marker
          id="arrow-axis"
          markerWidth="9"
          markerHeight="9"
          refX="7"
          refY="4.5"
          orient="auto"
          markerUnits="userSpaceOnUse"
        >
          <path d="M0,0 L9,4.5 L0,9 Z" fill={t.inkSoft} />
        </marker>
      </defs>

      {/* Propagator lines and particle symbol labels */}
      {PROPAGATORS.map((prop, i) => {
        const fromV = vertexMap.get(prop.fromVertex)!;
        const toV = vertexMap.get(prop.toVertex)!;
        const particle = particleMap.get(prop.particleId)!;
        const color = typeColorMap.get(particle.type)!;

        const x1 = xs(fromV.x);
        const y1 = ys(fromV.y);
        const x2 = xs(toV.x);
        const y2 = ys(toV.y);
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2;

        let labelX = mx;
        let labelY = my - 22;
        let labelAnchor: "start" | "middle" | "end" = "middle";
        if (!fromV.isInteraction) {
          labelX = x1 - 14;
          labelY = y1 + (fromV.y > toV.y ? -10 : 24);
          labelAnchor = "end";
        } else if (!toV.isInteraction) {
          labelX = x2 + 14;
          labelY = y2 + (toV.y > fromV.y ? -10 : 24);
          labelAnchor = "start";
        }

        const dx = x2 - x1;
        const dy = y2 - y1;
        const len = Math.hypot(dx, dy);
        const ux = dx / len;
        const uy = dy / len;
        const px = -uy;
        const py = ux;

        let lineEl: React.ReactNode;
        if (particle.type === "photon") {
          const steps = Math.round(PHOTON_WAVES * 22);
          let d = "";
          for (let s = 0; s <= steps; s++) {
            const u = s / steps;
            const offset = PHOTON_AMP_PX * Math.sin(u * PHOTON_WAVES * 2 * Math.PI);
            const wx = x1 + ux * u * len + px * offset;
            const wy = y1 + uy * u * len + py * offset;
            d += `${s === 0 ? "M" : "L"} ${wx.toFixed(1)} ${wy.toFixed(1)} `;
          }
          lineEl = <path d={d} stroke={color} strokeWidth={4.5} fill="none" />;
        } else if (particle.type === "gluon") {
          const steps = Math.round(GLUON_LOOPS * 24);
          let d = "";
          for (let s = 0; s <= steps; s++) {
            const u = s / steps;
            const theta = u * GLUON_LOOPS * 2 * Math.PI;
            const along = u * len + GLUON_R_PX * 0.72 * Math.sin(theta);
            const perp = -GLUON_R_PX * Math.cos(theta);
            const gx = x1 + ux * along + px * perp;
            const gy = y1 + uy * along + py * perp;
            d += `${s === 0 ? "M" : "L"} ${gx.toFixed(1)} ${gy.toFixed(1)} `;
          }
          lineEl = <path d={d} stroke={color} strokeWidth={3.6} fill="none" />;
        } else if (particle.type === "boson") {
          lineEl = (
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={color}
              strokeWidth={4.5}
              strokeDasharray="12,7"
              strokeLinecap="round"
            />
          );
        } else {
          const marked = particle.anti
            ? { ax: x2, ay: y2, bx: x1, by: y1 }
            : { ax: x1, ay: y1, bx: x2, by: y2 };
          lineEl = (
            <g stroke={color} strokeWidth={4.5} strokeLinecap="round">
              <line x1={marked.ax} y1={marked.ay} x2={mx} y2={my} markerEnd="url(#arrow-fermion)" />
              <line x1={marked.bx} y1={marked.by} x2={mx} y2={my} />
            </g>
          );
        }

        return (
          <g key={i}>
            {lineEl}
            <text
              x={labelX}
              y={labelY}
              textAnchor={labelAnchor}
              fontSize={24}
              fontWeight={700}
              fill={color}
            >
              {particle.label}
            </text>
          </g>
        );
      })}

      {/* Interaction vertex dots */}
      {interactionVertices.map((v) => (
        <circle
          key={v.id}
          cx={xs(v.x)}
          cy={ys(v.y)}
          r={9}
          fill={t.ink}
        />
      ))}

      {/* Time direction axis */}
      <line
        x1={xs(minVx)}
        y1={ys(timeAxisY)}
        x2={xs(maxVx)}
        y2={ys(timeAxisY)}
        stroke={t.inkSoft}
        strokeWidth={1.5}
        markerEnd="url(#arrow-axis)"
      />
      <text x={xs(maxVx) + 14} y={ys(timeAxisY) + 5} fontSize={16} fill={t.inkSoft}>
        {TIME_AXIS_LABEL}
      </text>

      {/* Four-type Feynman propagator style key */}
      {STYLE_KEY.map((item, idx) => {
        const { kind, label } = item;
        const color = typeColorMap.get(kind)!;
        const xFrac = minVx + vxSpan * 0.02 + (vxSpan * 0.86 * idx) / (STYLE_KEY.length - 1);
        const px = xs(xFrac);
        const py = ys(styleKeyY);
        const x2 = px + KEY_SWATCH_W_PX;

        let swatchEl: React.ReactNode;
        if (kind === "fermion") {
          swatchEl = (
            <line
              x1={px}
              y1={py}
              x2={x2}
              y2={py}
              stroke={color}
              strokeWidth={4}
              markerEnd="url(#arrow-fermion)"
            />
          );
        } else if (kind === "photon") {
          const steps = Math.round(KEY_WAVES * 22);
          let d = "";
          for (let s = 0; s <= steps; s++) {
            const u = s / steps;
            const wx = px + u * KEY_SWATCH_W_PX;
            const wy = py + KEY_AMP_PX * Math.sin(u * KEY_WAVES * 2 * Math.PI);
            d += `${s === 0 ? "M" : "L"} ${wx.toFixed(1)} ${wy.toFixed(1)} `;
          }
          swatchEl = <path d={d} stroke={color} strokeWidth={4} fill="none" />;
        } else if (kind === "gluon") {
          const loops = 4;
          const steps = 96;
          const rLoop = 7.5;
          let d = "";
          for (let s = 0; s <= steps; s++) {
            const u = s / steps;
            const theta = u * loops * 2 * Math.PI;
            const gx = px + u * KEY_SWATCH_W_PX + rLoop * 0.72 * Math.sin(theta);
            const gy = py - rLoop * Math.cos(theta);
            d += `${s === 0 ? "M" : "L"} ${gx.toFixed(1)} ${gy.toFixed(1)} `;
          }
          swatchEl = <path d={d} stroke={color} strokeWidth={3.2} fill="none" />;
        } else {
          swatchEl = (
            <line
              x1={px}
              y1={py}
              x2={x2}
              y2={py}
              stroke={color}
              strokeWidth={4}
              strokeDasharray="12,7"
            />
          );
        }

        return (
          <g key={kind}>
            {swatchEl}
            <text x={px} y={py + 26} fontSize={15} fill={t.inkSoft}>
              {label}
            </text>
          </g>
        );
      })}

      {/* Header and footer text */}
      <text
        x={xs(midVx)}
        y={ys(maxVy + vySpan * 0.5)}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>
      <text
        x={xs(midVx)}
        y={ys(maxVy + vySpan * 0.31)}
        textAnchor="middle"
        fontSize={16}
        fill={t.inkSoft}
      >
        {subtitle}
      </text>
      <text
        x={xs(midVx)}
        y={ys(minVy - vySpan * 0.75)}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
      >
        {FOOTER_NOTE}
      </text>
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: SIZE.width, height: SIZE.height, backgroundColor: t.pageBg }}>
      <ChartsContainer
        width={SIZE.width}
        height={SIZE.height}
        margin={{ top: 12, right: 12, bottom: 12, left: 12 }}
        series={[]}
        xAxis={[{ id: "x", scaleType: "linear", min: xDomainMin, max: xDomainMax, position: "none" }]}
        yAxis={[{ id: "y", scaleType: "linear", min: yDomainMin, max: yDomainMax, position: "none" }]}
        skipAnimation
      >
        <FeynmanCanvas />
      </ChartsContainer>
    </div>
  );
}
