// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-20

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;
const TITLE = "feynman-basic · javascript · muix · anyplot.ai";
const SUBTITLE = "Electron–positron annihilation → virtual photon → muon pair (QED)";
const FOOTER_NOTE =
  "Vertex dots mark interaction points · arrows show particle (forward) vs antiparticle (backward) flow in time";
const TIME_AXIS_LABEL = "time";

const FONT =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

// Constants
const VERTEX_ID = "vertexId";
const VERTEX_X = "vertexX";
const VERTEX_Y = "vertexY";
const VERTEX_INTERACTION = "isInteraction";

const PARTICLE_ID = "particleId";
const PARTICLE_TYPE = "particleType";
const PARTICLE_LABEL = "particleLabel";
const PARTICLE_ANTI = "isAntiparticle";

const FROM_VERTEX = "fromVertex";
const TO_VERTEX = "toVertex";

const STYLE_KIND = "styleKind";
const STYLE_LABEL = "styleLabel";

const X_PAD_SHARE = 0.095;
const Y_TOP_PAD_SHARE = 0.67;
const Y_BOTTOM_PAD_SHARE = 0.83;
const TIME_AXIS_DROP_SHARE = 0.25;
const STYLE_KEY_DROP_SHARE = 0.54;
const PHOTON_WAVES = 6;
const PHOTON_AMP_PX = 12;
const KEY_SWATCH_W_PX = 60;
const KEY_WAVES = 2.5;
const KEY_AMP_PX = 8;

// Data: vertices, particles, propagators, and standard Feynman line-style key
const vertexData = [
  { [VERTEX_ID]: "eIn", [VERTEX_X]: 8, [VERTEX_Y]: 24, [VERTEX_INTERACTION]: 0 },
  { [VERTEX_ID]: "posIn", [VERTEX_X]: 8, [VERTEX_Y]: 0, [VERTEX_INTERACTION]: 0 },
  { [VERTEX_ID]: "v1", [VERTEX_X]: 34, [VERTEX_Y]: 12, [VERTEX_INTERACTION]: 1 },
  { [VERTEX_ID]: "v2", [VERTEX_X]: 66, [VERTEX_Y]: 12, [VERTEX_INTERACTION]: 1 },
  { [VERTEX_ID]: "muOut", [VERTEX_X]: 92, [VERTEX_Y]: 24, [VERTEX_INTERACTION]: 0 },
  { [VERTEX_ID]: "antiMuOut", [VERTEX_X]: 92, [VERTEX_Y]: 0, [VERTEX_INTERACTION]: 0 },
];

const particleData = [
  { [PARTICLE_ID]: "e-", [PARTICLE_TYPE]: "fermion", [PARTICLE_LABEL]: "e⁻", [PARTICLE_ANTI]: 0 },
  { [PARTICLE_ID]: "e+", [PARTICLE_TYPE]: "fermion", [PARTICLE_LABEL]: "e⁺", [PARTICLE_ANTI]: 1 },
  { [PARTICLE_ID]: "gamma", [PARTICLE_TYPE]: "photon", [PARTICLE_LABEL]: "γ*", [PARTICLE_ANTI]: 0 },
  { [PARTICLE_ID]: "mu-", [PARTICLE_TYPE]: "fermion", [PARTICLE_LABEL]: "μ⁻", [PARTICLE_ANTI]: 0 },
  { [PARTICLE_ID]: "mu+", [PARTICLE_TYPE]: "fermion", [PARTICLE_LABEL]: "μ⁺", [PARTICLE_ANTI]: 1 },
];

const propagatorData = [
  { [FROM_VERTEX]: "eIn", [TO_VERTEX]: "v1", [PARTICLE_ID]: "e-" },
  { [FROM_VERTEX]: "posIn", [TO_VERTEX]: "v1", [PARTICLE_ID]: "e+" },
  { [FROM_VERTEX]: "v1", [TO_VERTEX]: "v2", [PARTICLE_ID]: "gamma" },
  { [FROM_VERTEX]: "v2", [TO_VERTEX]: "muOut", [PARTICLE_ID]: "mu-" },
  { [FROM_VERTEX]: "v2", [TO_VERTEX]: "antiMuOut", [PARTICLE_ID]: "mu+" },
];

const styleKeyData = [
  { [STYLE_KIND]: "fermion", [STYLE_LABEL]: "Fermion (e⁻, q, …)" },
  { [STYLE_KIND]: "photon", [STYLE_LABEL]: "Photon (γ)" },
  { [STYLE_KIND]: "gluon", [STYLE_LABEL]: "Gluon (g)" },
  { [STYLE_KIND]: "boson", [STYLE_LABEL]: "Scalar boson (H)" },
];

// Derived lookup maps and coordinate bounds from data
const vertexMap = new Map(
  vertexData.map((v) => [
    v[VERTEX_ID],
    { x: v[VERTEX_X], y: v[VERTEX_Y], isInteraction: v[VERTEX_INTERACTION] === 1 },
  ])
);

const particleMap = new Map(
  particleData.map((p) => [
    p[PARTICLE_ID],
    {
      type: p[PARTICLE_TYPE],
      label: p[PARTICLE_LABEL],
      anti: p[PARTICLE_ANTI] === 1,
    },
  ])
);

const styleKindOrder = styleKeyData.map((s) => s[STYLE_KIND]);
const typeColorMap = new Map<string, string>();
styleKindOrder.forEach((kind, idx) => {
  typeColorMap.set(kind, t.palette[idx]);
});

const vxValues = vertexData.map((v) => v[VERTEX_X]);
const vyValues = vertexData.map((v) => v[VERTEX_Y]);
const minVx = Math.min(...vxValues);
const maxVx = Math.max(...vxValues);
const minVy = Math.min(...vyValues);
const maxVy = Math.max(...vyValues);
const vxSpan = maxVx - minVx || 1;
const vySpan = maxVy - minVy || 1;
const midVx = (minVx + maxVx) / 2;

const xDomainMin = minVx - vxSpan * X_PAD_SHARE;
const xDomainMax = maxVx + vxSpan * X_PAD_SHARE;
const yDomainMin = minVy - vySpan * Y_BOTTOM_PAD_SHARE;
const yDomainMax = maxVy + vySpan * Y_TOP_PAD_SHARE;

const timeAxisY = minVy - vySpan * TIME_AXIS_DROP_SHARE;
const styleKeyY = minVy - vySpan * STYLE_KEY_DROP_SHARE;

const interactionVertices = vertexData.filter((v) => v[VERTEX_INTERACTION] === 1);

function FeynmanCanvas() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;

  const fermionColor = typeColorMap.get("fermion") ?? t.palette[0];

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
      {propagatorData.map((prop, i) => {
        const fromV = vertexMap.get(prop[FROM_VERTEX]) ?? { x: 0, y: 0, isInteraction: false };
        const toV = vertexMap.get(prop[TO_VERTEX]) ?? { x: 0, y: 0, isInteraction: false };
        const particle = particleMap.get(prop[PARTICLE_ID]) ?? {
          type: "fermion",
          label: prop[PARTICLE_ID],
          anti: false,
        };
        const color = typeColorMap.get(particle.type) ?? fermionColor;

        const x1 = xs(fromV.x);
        const y1 = ys(fromV.y);
        const x2 = xs(toV.x);
        const y2 = ys(toV.y);
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2;

        // Label placement derived from vertex roles and coordinates
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

        if (particle.type === "photon") {
          const dx = x2 - x1;
          const dy = y2 - y1;
          const len = Math.hypot(dx, dy) || 1;
          const ux = dx / len;
          const uy = dy / len;
          const px = -uy;
          const py = ux;
          const steps = Math.max(24, Math.round(PHOTON_WAVES * 22));
          let d = "";
          for (let s = 0; s <= steps; s++) {
            const u = s / steps;
            const offset = PHOTON_AMP_PX * Math.sin(u * PHOTON_WAVES * 2 * Math.PI);
            const wx = x1 + ux * u * len + px * offset;
            const wy = y1 + uy * u * len + py * offset;
            d += `${s === 0 ? "M" : "L"} ${wx.toFixed(1)} ${wy.toFixed(1)} `;
          }
          return (
            <g key={i}>
              <path d={d} stroke={color} strokeWidth={4.5} fill="none" />
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
        }

        const marked = particle.anti
          ? { ax: x2, ay: y2, bx: x1, by: y1 }
          : { ax: x1, ay: y1, bx: x2, by: y2 };

        return (
          <g key={i}>
            <g stroke={color} strokeWidth={4.5} strokeLinecap="round">
              <line x1={marked.ax} y1={marked.ay} x2={mx} y2={my} markerEnd="url(#arrow-fermion)" />
              <line x1={marked.bx} y1={marked.by} x2={mx} y2={my} />
            </g>
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
          key={v[VERTEX_ID]}
          cx={xs(v[VERTEX_X])}
          cy={ys(v[VERTEX_Y])}
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
      {styleKeyData.map((item, idx) => {
        const kind = item[STYLE_KIND];
        const label = item[STYLE_LABEL];
        const color = typeColorMap.get(kind) ?? t.inkSoft;
        const xFrac =
          styleKeyData.length > 1
            ? minVx + vxSpan * 0.02 + (vxSpan * 0.86 * idx) / (styleKeyData.length - 1)
            : midVx;
        const px = xs(xFrac);
        const py = ys(styleKeyY);
        const x2 = px + KEY_SWATCH_W_PX;

        let swatchEl: React.ReactNode = null;
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
          const steps = Math.max(24, Math.round(KEY_WAVES * 22));
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
        {SUBTITLE}
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
