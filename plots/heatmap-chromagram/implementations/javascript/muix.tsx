// anyplot.ai
// heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-24

// MUI X community has no native heatmap; rendered as SVG within a React
// component using the harness-injected theme tokens (Imprint seq colormap).

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// Pitch classes (index 0=C … 11=B)
const PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const N_FRAMES = 80;
const SEC_PER_FRAME = 0.05;

// Four-chord progression: C maj → G maj → A min → F maj
const CHORDS = [
  { label: "C major", pcs: [0, 4, 7],  start: 0,  end: 20 },
  { label: "G major", pcs: [7, 11, 2], start: 20, end: 40 },
  { label: "A minor", pcs: [9, 0, 4],  start: 40, end: 60 },
  { label: "F major", pcs: [5, 9, 0],  start: 60, end: 80 },
];

// Deterministic LCG seeded at 42
function makeLCG(seed) {
  let s = seed >>> 0;
  return () => { s = (((s * 1664525) >>> 0) + 1013904223) >>> 0; return s / 0x100000000; };
}
const rand = makeLCG(42);

// Build 12 × 80 chroma matrix; chord tones get high energy, others low
const chroma = Array.from({ length: 12 }, (_, pc) =>
  Array.from({ length: N_FRAMES }, (_, f) => {
    const chord = CHORDS.find(c => f >= c.start && f < c.end);
    const active   = chord ? chord.pcs.includes(pc) : false;
    const overtone = chord ? chord.pcs.map(p => (p + 7) % 12).includes(pc) : false;
    const base = active   ? 0.65 + rand() * 0.30
               : overtone ? 0.22 + rand() * 0.18
               :             rand() * 0.16;
    return Math.min(1.0, base);
  })
);

// Imprint sequential colormap: seq[0]=#009E73 → seq[1]=#4467A3
function hexRgb(h) {
  return [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)];
}
function seqColor(v) {
  const [r1,g1,b1] = hexRgb(t.seq[0]);
  const [r2,g2,b2] = hexRgb(t.seq[1]);
  return `rgb(${Math.round(r1+(r2-r1)*v)},${Math.round(g1+(g2-g1)*v)},${Math.round(b1+(b2-b1)*v)})`;
}

export default function Chart() {
  // Layout margins (CSS px in 1600×900 mount)
  const ML = 68, MR = 88, MT = 74, MB = 70;
  const gW = width - ML - MR;
  const gH = height - MT - MB;
  const cW = gW / N_FRAMES;
  const cH = gH / 12;

  // Colorbar
  const cbX = width - MR + 20;
  const cbW = 22;

  const xTicks = [0, 10, 20, 30, 40, 50, 60, 70, 80];

  return (
    <svg
      width={width}
      height={height}
      style={{ background: t.pageBg, fontFamily: "Inter, system-ui, sans-serif" }}
    >
      {/* Title */}
      <text
        x={width / 2} y={MT - 42}
        textAnchor="middle" fontSize={22} fontWeight="500" fill={t.ink}
      >
        heatmap-chromagram · javascript · muix · anyplot.ai
      </text>

      {/* Chord labels above grid */}
      {CHORDS.map(c => (
        <text
          key={c.label}
          x={ML + (c.start + (c.end - c.start) / 2) * cW}
          y={MT - 14}
          textAnchor="middle" fontSize={13} fill={t.inkSoft}
        >
          {c.label}
        </text>
      ))}

      <g transform={`translate(${ML},${MT})`}>
        {/* Heatmap cells — pc 0 (C) at bottom → display row = 11 − pc */}
        {chroma.map((row, pc) =>
          row.map((val, f) => (
            <rect
              key={`${pc}-${f}`}
              x={f * cW}
              y={(11 - pc) * cH}
              width={cW + 0.5}
              height={cH + 0.5}
              fill={seqColor(val)}
            />
          ))
        )}

        {/* Chord-change dividers */}
        {[20, 40, 60].map(f => (
          <line
            key={f}
            x1={f * cW} y1={0} x2={f * cW} y2={gH}
            stroke={t.pageBg} strokeWidth={2.5}
          />
        ))}

        {/* Y-axis pitch class labels (C at bottom, B at top) */}
        {PITCH_CLASSES.map((pc, i) => (
          <text
            key={pc}
            x={-10}
            y={(11 - i) * cH + cH / 2}
            textAnchor="end" dominantBaseline="middle"
            fontSize={13} fill={t.inkSoft}
          >
            {pc}
          </text>
        ))}

        {/* X-axis tick labels */}
        {xTicks.filter(f => f <= N_FRAMES).map(f => (
          <text
            key={f}
            x={f * cW} y={gH + 20}
            textAnchor="middle" fontSize={12} fill={t.inkSoft}
          >
            {(f * SEC_PER_FRAME).toFixed(1)}s
          </text>
        ))}

        {/* Axis labels */}
        <text x={gW / 2} y={gH + 52} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
          Time (seconds)
        </text>
        <text
          x={-46} y={gH / 2}
          textAnchor="middle" fontSize={14} fill={t.inkSoft}
          transform={`rotate(-90, -46, ${gH / 2})`}
        >
          Pitch Class
        </text>
      </g>

      {/* Colorbar gradient */}
      <defs>
        <linearGradient id="cbGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <rect x={cbX} y={MT} width={cbW} height={gH} fill="url(#cbGrad)" />
      <text x={cbX + cbW/2} y={MT - 6}    textAnchor="middle" fontSize={11} fill={t.inkSoft}>1.0</text>
      <text x={cbX + cbW/2} y={MT + gH + 14} textAnchor="middle" fontSize={11} fill={t.inkSoft}>0.0</text>
      <text
        x={cbX + cbW + 16} y={MT + gH / 2}
        textAnchor="middle" fontSize={12} fill={t.inkSoft}
        transform={`rotate(90, ${cbX + cbW + 16}, ${MT + gH / 2})`}
      >
        Energy
      </text>
    </svg>
  );
}
