//# anyplot-orientation: square
// anyplot.ai
// heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;

// IT security risk register — 12 items distributed across the 5×5 matrix
const risks = [
  { name: "Data Breach",    likelihood: 3, impact: 5 },
  { name: "Ransomware",     likelihood: 4, impact: 5 },
  { name: "DDoS Attack",    likelihood: 4, impact: 3 },
  { name: "Supply Chain",   likelihood: 2, impact: 4 },
  { name: "Insider Threat", likelihood: 2, impact: 5 },
  { name: "API Failure",    likelihood: 3, impact: 3 },
  { name: "Key Staff Loss", likelihood: 3, impact: 4 },
  { name: "Budget Cut",     likelihood: 4, impact: 2 },
  { name: "Compliance",     likelihood: 2, impact: 3 },
  { name: "Cloud Outage",   likelihood: 2, impact: 4 },
  { name: "Phishing",       likelihood: 5, impact: 2 },
  { name: "HW Failure",     likelihood: 1, impact: 3 },
];

// Zone colour coding — semantic Imprint palette anchors
function zoneColor(lh: number, imp: number): string {
  const score = lh * imp;
  if (score <= 4)  return "#009E73"; // Low — Imprint brand green
  if (score <= 9)  return "#DDCC77"; // Medium — Imprint amber
  if (score <= 16) return "#BD8233"; // High — Imprint ochre
  return "#AE3030";                  // Critical — Imprint matte red
}

const LIKELIHOOD_LABELS = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"];
const IMPACT_LABELS     = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"];

const ZONE_LEGEND = [
  { label: "Low (1–4)",        color: "#009E73" },
  { label: "Medium (5–9)",     color: "#DDCC77" },
  { label: "High (10–16)",     color: "#BD8233" },
  { label: "Critical (20–25)", color: "#AE3030" },
];

// Count co-occupants per cell, then assign ordinal index for jitter
const _cnt: Record<string, number> = {};
risks.forEach(r => {
  const k = `${r.likelihood}-${r.impact}`;
  _cnt[k] = (_cnt[k] ?? 0) + 1;
});
const _itr: Record<string, number> = {};
const risksPlaced = risks.map(r => {
  const k = `${r.likelihood}-${r.impact}`;
  const idx = _itr[k] ?? 0;
  _itr[k] = idx + 1;
  return { ...r, idx, siblings: _cnt[k] };
});

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;  // 1200 CSS px (square)
  const H = window.ANYPLOT_SIZE.height; // 1200 CSS px (square)

  // Layout margins (CSS px)
  const ML = 162, MT = 66, MR = 52, MB = 182;
  const GW = W - ML - MR; // grid width
  const GH = H - MT - MB; // grid height
  const cW = GW / 5;
  const cH = GH / 5;

  // SVG coords inside the grid group:
  //   impact 1 → left (x=0), 5 → right (x=GW)
  //   likelihood 1 → bottom (y=GH), 5 → top (y=0)
  function markerXY(r: typeof risksPlaced[0]): [number, number] {
    const cx = (r.impact - 0.5) * cW;
    const cy = (5.5 - r.likelihood) * cH;
    if (r.siblings === 1) return [cx, cy];
    const angle = (2 * Math.PI * r.idx) / r.siblings - Math.PI / 2;
    return [
      cx + cW * 0.22 * Math.cos(angle),
      cy + cH * 0.22 * Math.sin(angle),
    ];
  }

  const FONT  = "system-ui, -apple-system, sans-serif";
  const TITLE = "heatmap-risk-matrix · javascript · muix · anyplot.ai";

  return (
    <svg width={W} height={H} fontFamily={FONT}>

      {/* Title */}
      <text x={W / 2} y={44}
        textAnchor="middle" fontSize={20} fontWeight="500" fill={t.ink}>
        {TITLE}
      </text>

      <g transform={`translate(${ML},${MT})`}>

        {/* Background risk-zone cells */}
        {[1, 2, 3, 4, 5].flatMap(lh =>
          [1, 2, 3, 4, 5].map(imp => (
            <rect key={`cell-${lh}-${imp}`}
              x={(imp - 1) * cW} y={(5 - lh) * cH}
              width={cW} height={cH}
              fill={zoneColor(lh, imp)} fillOpacity={0.38}
              stroke={t.ink} strokeOpacity={0.18} strokeWidth={1} />
          ))
        )}

        {/* Risk score (L×I) label inside each cell */}
        {[1, 2, 3, 4, 5].flatMap(lh =>
          [1, 2, 3, 4, 5].map(imp => (
            <text key={`score-${lh}-${imp}`}
              x={(imp - 0.5) * cW} y={(5.5 - lh) * cH}
              textAnchor="middle" dominantBaseline="middle"
              fontSize={16} fill={t.ink} fillOpacity={0.32}>
              {lh * imp}
            </text>
          ))
        )}

        {/* Y-axis: Likelihood tick labels */}
        {LIKELIHOOD_LABELS.map((label, i) => {
          const cy = (4.5 - i) * cH;
          if (label === "Almost Certain") {
            return (
              <text key={`yl-${i}`} x={-14} textAnchor="end"
                fill={t.inkSoft} fontSize={13}>
                <tspan x={-14} y={cy - 9}>Almost</tspan>
                <tspan x={-14} y={cy + 9}>Certain</tspan>
              </text>
            );
          }
          return (
            <text key={`yl-${i}`} x={-14} y={cy}
              textAnchor="end" dominantBaseline="middle"
              fill={t.inkSoft} fontSize={13}>
              {label}
            </text>
          );
        })}

        {/* Y-axis title */}
        <text
          transform={`translate(-126,${GH / 2}) rotate(-90)`}
          textAnchor="middle"
          fontSize={15} fontWeight="500" fill={t.ink}>
          Likelihood
        </text>

        {/* X-axis: Impact tick labels */}
        {IMPACT_LABELS.map((label, i) => (
          <text key={`xl-${i}`}
            x={(i + 0.5) * cW} y={GH + 16}
            textAnchor="middle" dominantBaseline="hanging"
            fill={t.inkSoft} fontSize={13}>
            {label}
          </text>
        ))}

        {/* X-axis title */}
        <text x={GW / 2} y={GH + 56}
          textAnchor="middle"
          fontSize={15} fontWeight="500" fill={t.ink}>
          Impact
        </text>

        {/* Risk item markers with labels */}
        {risksPlaced.map((r, i) => {
          const [mx, my] = markerXY(r);
          return (
            <g key={`risk-${i}`}>
              <circle cx={mx} cy={my} r={10}
                fill={t.elevatedBg} stroke={t.ink} strokeWidth={1.5} />
              <text x={mx} y={my - 14}
                textAnchor="middle"
                fontSize={11} fontWeight="500" fill={t.ink}>
                {r.name}
              </text>
            </g>
          );
        })}

        {/* Risk zone legend */}
        {ZONE_LEGEND.map((z, i) => {
          const lx = i * (GW / 4) + GW / 8;
          const ly = GH + 116;
          return (
            <g key={`leg-${i}`}>
              <rect x={lx - 50} y={ly - 9}
                width={18} height={18}
                fill={z.color} fillOpacity={0.65} rx={2} />
              <text x={lx - 28} y={ly}
                dominantBaseline="middle"
                fontSize={12} fill={t.ink}>
                {z.label}
              </text>
            </g>
          );
        })}

      </g>
    </svg>
  );
}
