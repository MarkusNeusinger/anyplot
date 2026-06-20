// anyplot.ai
// heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-20
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;

// --- Cell color: Imprint semantic anchors green → amber → ochre → red -------
function cellColor(score) {
  const stops = [
    { s: 1,  r: 0,   g: 158, b: 115, a: 0.75 }, // #009E73 low risk
    { s: 5,  r: 221, g: 204, b: 119, a: 0.80 }, // #DDCC77 medium risk
    { s: 10, r: 189, g: 130, b: 51,  a: 0.85 }, // #BD8233 high risk
    { s: 17, r: 174, g: 48,  b: 48,  a: 0.90 }, // #AE3030 critical risk
    { s: 25, r: 140, g: 20,  b: 20,  a: 0.95 },
  ];
  let lo = stops[0], hi = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {
    if (score >= stops[i].s && score <= stops[i + 1].s) {
      lo = stops[i]; hi = stops[i + 1]; break;
    }
  }
  const f = lo.s === hi.s ? 0 : (score - lo.s) / (hi.s - lo.s);
  const a = +(lo.a + (hi.a - lo.a) * f).toFixed(2);
  return `rgba(${Math.round(lo.r + (hi.r - lo.r) * f)},${Math.round(lo.g + (hi.g - lo.g) * f)},${Math.round(lo.b + (hi.b - lo.b) * f)},${a})`;
}

// --- Data: IT security risk register ----------------------------------------
// 12 risks, all in unique cells — no jitter needed
const risks = [
  { name: "Data Breach",      likelihood: 4, impact: 5, cat: 0 },
  { name: "Ransomware",       likelihood: 3, impact: 5, cat: 0 },
  { name: "Integration Fail", likelihood: 2, impact: 5, cat: 0 },
  { name: "Phishing Attack",  likelihood: 5, impact: 3, cat: 0 },
  { name: "Network Outage",   likelihood: 4, impact: 3, cat: 0 },
  { name: "Vendor Failure",   likelihood: 2, impact: 4, cat: 1 },
  { name: "Regulatory Fine",  likelihood: 2, impact: 3, cat: 1 },
  { name: "Budget Overrun",   likelihood: 4, impact: 2, cat: 1 },
  { name: "System Downtime",  likelihood: 3, impact: 4, cat: 2 },
  { name: "Key Staff Loss",   likelihood: 3, impact: 3, cat: 2 },
  { name: "Scope Creep",      likelihood: 5, impact: 2, cat: 2 },
  { name: "Hardware Failure", likelihood: 2, impact: 2, cat: 2 },
];

const catConfig = [
  { label: "Technical",   color: t.palette[0] }, // #009E73
  { label: "Financial",   color: t.palette[1] }, // #C475FD
  { label: "Operational", color: t.palette[2] }, // #4467A3
];

const datasets = catConfig.map((cat, ci) => ({
  label: cat.label,
  data: risks
    .filter(r => r.cat === ci)
    .map(r => ({ x: r.impact, y: r.likelihood, name: r.name })),
  backgroundColor: cat.color,
  borderColor: THEME === "light" ? "rgba(250,248,241,0.85)" : "rgba(26,26,23,0.85)",
  borderWidth: 2.5,
  pointRadius: 12,
  pointHoverRadius: 14,
}));

// --- Plugin: draw 5×5 colored risk matrix background -----------------------
const matrixBg = {
  id: "matrixBg",
  beforeDraw(chart) {
    const { ctx, scales: { x, y }, chartArea: ca } = chart;
    ctx.save();
    ctx.beginPath();
    ctx.rect(ca.left, ca.top, ca.right - ca.left, ca.bottom - ca.top);
    ctx.clip();

    for (let imp = 1; imp <= 5; imp++) {
      for (let lik = 1; lik <= 5; lik++) {
        const score = imp * lik;
        const x0 = x.getPixelForValue(imp - 0.5);
        const x1 = x.getPixelForValue(imp + 0.5);
        const y0 = y.getPixelForValue(lik + 0.5);
        const y1 = y.getPixelForValue(lik - 0.5);
        const w = x1 - x0, h = y1 - y0;

        // Colored fill
        ctx.fillStyle = cellColor(score);
        ctx.fillRect(x0, y0, w, h);

        // Cell grid border
        ctx.strokeStyle = THEME === "light" ? "rgba(255,255,255,0.45)" : "rgba(0,0,0,0.35)";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(x0, y0, w, h);

        // Risk score in bottom-right corner
        ctx.font = "bold 12px sans-serif";
        ctx.fillStyle = THEME === "light" ? "rgba(255,255,255,0.70)" : "rgba(0,0,0,0.50)";
        ctx.textAlign = "right";
        ctx.textBaseline = "bottom";
        ctx.fillText(String(score), x1 - 7, y1 - 5);
      }
    }

    // Zone labels in free cells representative of each zone
    const zones = [
      { label: "LOW",      imp: 1, lik: 1 }, // score 1
      { label: "MEDIUM",   imp: 2, lik: 3 }, // score 6
      { label: "HIGH",     imp: 4, lik: 4 }, // score 16
      { label: "CRITICAL", imp: 5, lik: 5 }, // score 25
    ];
    zones.forEach(({ label, imp, lik }) => {
      const cx = (x.getPixelForValue(imp - 0.5) + x.getPixelForValue(imp + 0.5)) / 2;
      const cy = (y.getPixelForValue(lik + 0.5) + y.getPixelForValue(lik - 0.5)) / 2;
      ctx.font = "bold 13px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = THEME === "light" ? "rgba(255,255,255,0.90)" : "rgba(0,0,0,0.60)";
      ctx.fillText(label, cx, cy);
    });

    ctx.restore();
  },
};

// --- Plugin: draw risk item name labels near each marker --------------------
const riskLabels = {
  id: "riskLabels",
  afterDraw(chart) {
    const { ctx, scales: { x, y } } = chart;
    ctx.save();

    chart.data.datasets.forEach(ds => {
      ds.data.forEach(pt => {
        const px = x.getPixelForValue(pt.x);
        const py = y.getPixelForValue(pt.y);
        const label = pt.name;
        const above = pt.y <= 3; // high likelihood → point near top → label below

        ctx.font = "600 11px sans-serif";
        const tw = ctx.measureText(label).width;
        const th = 13, pad = 4;
        const bw = tw + pad * 2, bh = th + pad;
        const bx = px - bw / 2;
        const by = above ? py - 18 - bh : py + 18;

        // Background pill for legibility
        ctx.fillStyle = THEME === "light" ? "rgba(250,248,241,0.92)" : "rgba(26,26,23,0.92)";
        ctx.beginPath();
        ctx.roundRect(bx, by, bw, bh, 3);
        ctx.fill();

        ctx.fillStyle = THEME === "light" ? "#1A1A17" : "#F0EFE8";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(label, px, by + bh / 2);
      });
    });

    ctx.restore();
  },
};

// --- Plugin: zone severity legend box ---------------------------------------
const zoneLegend = {
  id: "zoneLegend",
  afterDraw(chart) {
    const { ctx, chartArea: ca } = chart;
    ctx.save();

    const entries = [
      { label: "Low (1–4)",      score: 2  },
      { label: "Medium (5–9)",   score: 7  },
      { label: "High (10–16)",   score: 13 },
      { label: "Critical (17–25)", score: 22 },
    ];

    ctx.font = "12px sans-serif";
    const maxW = Math.max(...entries.map(e => ctx.measureText(e.label).width));
    const swW = 14, swH = 12, gap = 6, lineH = 22, pad = 10;
    const boxW = pad * 2 + swW + gap + maxW + 4;
    const boxH = pad * 2 + entries.length * lineH - (lineH - swH);

    const bx = ca.right - boxW - 10;
    const by = ca.bottom - boxH - 10;

    // Legend box background
    ctx.fillStyle = THEME === "light" ? "#FFFDF6" : "#242420";
    ctx.strokeStyle = THEME === "light" ? "rgba(26,26,23,0.15)" : "rgba(240,239,232,0.15)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(bx, by, boxW, boxH, 5);
    ctx.fill();
    ctx.stroke();

    entries.forEach((entry, i) => {
      const rowY = by + pad + i * lineH;
      // Color swatch
      ctx.fillStyle = cellColor(entry.score);
      ctx.beginPath();
      ctx.roundRect(bx + pad, rowY + (lineH - swH) / 2, swW, swH, 2);
      ctx.fill();
      // Zone label text
      ctx.font = "12px sans-serif";
      ctx.fillStyle = THEME === "light" ? "#4A4A44" : "#B8B7B0";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(entry.label, bx + pad + swW + gap, rowY + lineH / 2);
    });

    ctx.restore();
  },
};

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ------------------------------------------------------------------
const IMPACT_LABELS = ["", "Negligible", "Minor", "Moderate", "Major", "Catastrophic"];
const LIKELIHOOD_LABELS = ["", "Rare", "Unlikely", "Possible", "Likely", "Almost Certain"];

new Chart(canvas, {
  type: "scatter",
  data: { datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "heatmap-risk-matrix · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "600" },
        padding: { top: 16, bottom: 10 },
      },
      legend: {
        display: true,
        position: "bottom",
        labels: {
          color: t.ink,
          font: { size: 15 },
          padding: 20,
          usePointStyle: true,
          pointStyle: "circle",
        },
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: 0.5,
        max: 5.5,
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          stepSize: 1,
          callback(val) {
            const v = Math.round(val);
            return v >= 1 && v <= 5 ? IMPACT_LABELS[v] : "";
          },
          maxRotation: 0,
        },
        grid: { display: false },
        border: { color: t.inkSoft, width: 1.5 },
        title: {
          display: true,
          text: "Impact",
          color: t.ink,
          font: { size: 15, weight: "600" },
          padding: { top: 8 },
        },
      },
      y: {
        type: "linear",
        min: 0.5,
        max: 5.5,
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          stepSize: 1,
          callback(val) {
            const v = Math.round(val);
            return v >= 1 && v <= 5 ? LIKELIHOOD_LABELS[v] : "";
          },
        },
        grid: { display: false },
        border: { color: t.inkSoft, width: 1.5 },
        title: {
          display: true,
          text: "Likelihood",
          color: t.ink,
          font: { size: 15, weight: "600" },
          padding: { bottom: 8 },
        },
      },
    },
    layout: {
      padding: { top: 8, right: 16, bottom: 8, left: 8 },
    },
  },
  plugins: [matrixBg, riskLabels, zoneLegend],
});
