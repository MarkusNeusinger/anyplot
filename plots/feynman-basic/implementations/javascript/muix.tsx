// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-08-20
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;
const TITLE = "feynman-basic · javascript · muix · anyplot.ai";
const SUBTITLE = "Electron–positron annihilation → virtual photon → muon pair (QED)";

const FONT =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

// Imprint palette — data colors identical across themes; first series is
// always brand green.
const FERMION = t.palette[0]; // #009E73 — every fermion leg (e-, e+, mu-, mu+)
const PHOTON = t.palette[1]; // #C475FD — photon propagator
const GLUON = t.palette[2]; // #4467A3 — gluon (shown in the style key only)
const BOSON = t.palette[3]; // #BD8233 — scalar boson, e.g. Higgs (style key only)

// Data-space domain. x runs left→right as the time axis; y is plain vertical
// space. 100×60 roughly matches the 1600×900 CSS mount aspect ratio so pixel
// shapes (computed after scaling) aren't stretched.
const X = [0, 100];
const Y = [-20, 40];

// --- Data model: particles / vertices / propagators (per specification.md) --
const vertices = {
  v1: [34, 12], // e- + e+ annihilate here
  v2: [66, 12], // gamma* pair-produces mu- + mu+ here
  eIn: [8, 24], // incoming e-
  posIn: [8, 0], // incoming e+
  muOut: [92, 24], // outgoing mu-
  antiMuOut: [92, 0], // outgoing mu+
};

const particles = [
  { id: "e-", type: "fermion", label: "e⁻", anti: false },
  { id: "e+", type: "fermion", label: "e⁺", anti: true },
  { id: "gamma", type: "photon", label: "γ*", anti: false },
  { id: "mu-", type: "fermion", label: "μ⁻", anti: false },
  { id: "mu+", type: "fermion", label: "μ⁺", anti: true },
];
const particleById = Object.fromEntries(particles.map((p) => [p.id, p]));

const propagators = [
  { from_vertex: "eIn", to_vertex: "v1", particle_id: "e-" },
  { from_vertex: "posIn", to_vertex: "v1", particle_id: "e+" },
  { from_vertex: "v1", to_vertex: "v2", particle_id: "gamma" },
  { from_vertex: "v2", to_vertex: "muOut", particle_id: "mu-" },
  { from_vertex: "v2", to_vertex: "antiMuOut", particle_id: "mu+" },
];

// --- Geometry helpers (pixel space, after scaling) --------------------------
function wavyPath(x1, y1, x2, y2, waves, amp) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  const ux = dx / len;
  const uy = dy / len;
  const px = -uy;
  const py = ux;
  const steps = Math.max(24, Math.round(waves * 22));
  let d = "";
  for (let i = 0; i <= steps; i++) {
    const u = i / steps;
    const offset = amp * Math.sin(u * waves * 2 * Math.PI);
    const x = x1 + ux * u * len + px * offset;
    const y = y1 + uy * u * len + py * offset;
    d += `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)} `;
  }
  return d;
}

// Coiled-spring look for a gluon: a chain of overlapping cubic-bezier bumps
// alternating above/below the path.
function curlyPath(x1, y1, x2, y2, loops, radius) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  const ux = dx / len;
  const uy = dy / len;
  const px = -uy;
  const py = ux;
  const loopLen = len / loops;
  let d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} `;
  for (let i = 0; i < loops; i++) {
    const s0 = i * loopLen;
    const c1x = x1 + ux * (s0 + loopLen * 0.15) - px * radius;
    const c1y = y1 + uy * (s0 + loopLen * 0.15) - py * radius;
    const c2x = x1 + ux * (s0 + loopLen * 0.85) + px * radius;
    const c2y = y1 + uy * (s0 + loopLen * 0.85) + py * radius;
    const ex = x1 + ux * (s0 + loopLen);
    const ey = y1 + uy * (s0 + loopLen);
    d += `C ${c1x.toFixed(1)} ${c1y.toFixed(1)}, ${c2x.toFixed(1)} ${c2y.toFixed(1)}, ${ex.toFixed(1)} ${ey.toFixed(1)} `;
  }
  return d;
}

// Auto-oriented SVG markers give a reliable arrowhead: the browser places and
// rotates the triangle exactly at the path's endpoint, unlike a hand-rolled
// polygon overlaid on a full-length line (which reads by which side has the
// longer unbroken run of line, not by the triangle's own geometry).
function ArrowDefs() {
  return (
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
        <path d="M0,0 L11,5.5 L0,11 Z" fill={FERMION} />
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
  );
}

// Fermion propagator drawn as two half-segments so the arrowhead marker sits
// exactly at the path midpoint. Particles flow forward in time (arrow toward
// `to`); antiparticles are drawn flowing backward, so the marker-carrying
// half is the one nearer `from` instead.
function FermionLine({ x1, y1, x2, y2, anti }) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const marked = anti
    ? { ax: x2, ay: y2, bx: x1, by: y1 }
    : { ax: x1, ay: y1, bx: x2, by: y2 };
  return (
    <g stroke={FERMION} strokeWidth={4.5} strokeLinecap="round">
      <line x1={marked.ax} y1={marked.ay} x2={mx} y2={my} markerEnd="url(#arrow-fermion)" />
      <line x1={marked.bx} y1={marked.by} x2={mx} y2={my} />
    </g>
  );
}

// --- Overlay layers -----------------------------------------------------------
function Propagators() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g>
      <ArrowDefs />
      {propagators.map((prop, i) => {
        const particle = particleById[prop.particle_id];
        const [x1d, y1d] = vertices[prop.from_vertex];
        const [x2d, y2d] = vertices[prop.to_vertex];
        const x1 = xs(x1d);
        const y1 = ys(y1d);
        const x2 = xs(x2d);
        const y2 = ys(y2d);
        if (particle.type === "photon") {
          return (
            <path
              key={i}
              d={wavyPath(x1, y1, x2, y2, 6, 12)}
              stroke={PHOTON}
              strokeWidth={4.5}
              fill="none"
            />
          );
        }
        return <FermionLine key={i} x1={x1} y1={y1} x2={x2} y2={y2} anti={particle.anti} />;
      })}
    </g>
  );
}

function VertexDots() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g>
      {["v1", "v2"].map((id) => (
        <circle key={id} cx={xs(vertices[id][0])} cy={ys(vertices[id][1])} r={9} fill={t.ink} />
      ))}
    </g>
  );
}

function Labels() {
  const xs = useXScale();
  const ys = useYScale();
  const entries = [
    { at: vertices.eIn, dx: -14, dy: -10, anchor: "end", particle: "e-" },
    { at: vertices.posIn, dx: -14, dy: 24, anchor: "end", particle: "e+" },
    { at: vertices.muOut, dx: 14, dy: -10, anchor: "start", particle: "mu-" },
    { at: vertices.antiMuOut, dx: 14, dy: 24, anchor: "start", particle: "mu+" },
  ];
  const [mx, my] = [(vertices.v1[0] + vertices.v2[0]) / 2, vertices.v1[1]];
  return (
    <g fontFamily={FONT} fontWeight={700}>
      {entries.map(({ at, dx, dy, anchor, particle }) => (
        <text
          key={particle}
          x={xs(at[0]) + dx}
          y={ys(at[1]) + dy}
          textAnchor={anchor}
          fontSize={24}
          fill={FERMION}
        >
          {particleById[particle].label}
        </text>
      ))}
      <text x={xs(mx)} y={ys(my) - 22} textAnchor="middle" fontSize={24} fill={PHOTON}>
        {particleById.gamma.label}
      </text>
    </g>
  );
}

function TimeAxis() {
  const xs = useXScale();
  const ys = useYScale();
  const y = -6;
  const x1 = xs(vertices.eIn[0]);
  const x2 = xs(92);
  const py = ys(y);
  return (
    <g fontFamily={FONT}>
      <line
        x1={x1}
        y1={py}
        x2={x2}
        y2={py}
        stroke={t.inkSoft}
        strokeWidth={1.5}
        markerEnd="url(#arrow-axis)"
      />
      <text x={x2 + 14} y={py + 5} fontSize={16} fill={t.inkSoft}>
        time
      </text>
    </g>
  );
}

// Style key covering all four line conventions from the spec, independent of
// which types this particular process happens to use.
function StyleKey() {
  const xs = useXScale();
  const ys = useYScale();
  const y = -13;
  const swatchW = 60;
  const items = [
    { x: 10, color: FERMION, kind: "fermion", label: "Fermion (e⁻, q, …)" },
    { x: 34, color: PHOTON, kind: "photon", label: "Photon (γ)" },
    { x: 58, color: GLUON, kind: "gluon", label: "Gluon (g)" },
    { x: 82, color: BOSON, kind: "boson", label: "Scalar boson (H)" },
  ];
  return (
    <g fontFamily={FONT}>
      {items.map(({ x, color, kind, label }) => {
        const px = xs(x);
        const py = ys(y);
        const x2 = px + swatchW;
        return (
          <g key={kind}>
            {kind === "fermion" && (
              <line
                x1={px}
                y1={py}
                x2={x2}
                y2={py}
                stroke={color}
                strokeWidth={4}
                markerEnd="url(#arrow-fermion)"
              />
            )}
            {kind === "photon" && (
              <path d={wavyPath(px, py, x2, py, 2.5, 8)} stroke={color} strokeWidth={4} fill="none" />
            )}
            {kind === "gluon" && (
              <path d={curlyPath(px, py, x2, py, 2.5, 8)} stroke={color} strokeWidth={4} fill="none" />
            )}
            {kind === "boson" && (
              <line
                x1={px}
                y1={py}
                x2={x2}
                y2={py}
                stroke={color}
                strokeWidth={4}
                strokeDasharray="12,7"
              />
            )}
            <text x={px} y={py + 26} fontSize={15} fill={t.inkSoft}>
              {label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

function Frame() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g fontFamily={FONT}>
      <text x={xs(50)} y={ys(36)} textAnchor="middle" fontSize={30} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={xs(50)} y={ys(31)} textAnchor="middle" fontSize={17} fill={t.inkSoft}>
        {SUBTITLE}
      </text>
      <text x={xs(50)} y={ys(-18)} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
        Vertex dots mark interaction points · arrows show particle (forward) vs antiparticle
        (backward) flow in time
      </text>
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <ChartContainer
      width={SIZE.width}
      height={SIZE.height}
      margin={{ top: 12, right: 12, bottom: 12, left: 12 }}
      series={[]}
      xAxis={[{ id: "x", scaleType: "linear", min: X[0], max: X[1] }]}
      yAxis={[{ id: "y", scaleType: "linear", min: Y[0], max: Y[1] }]}
      skipAnimation
    >
      <Propagators />
      <VertexDots />
      <Labels />
      <TimeAxis />
      <StyleKey />
      <Frame />
    </ChartContainer>
  );
}
