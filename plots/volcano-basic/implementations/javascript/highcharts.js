// anyplot.ai
// volcano-basic: Volcano Plot for Statistical Significance
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;
// ANYPLOT_TOKENS has no "muted" anchor — derive it per default-style-guide.md
// theme-adaptive chrome table (INK_MUTED: #6B6A63 light / #A8A79F dark).
const MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic LCG) ------------------------------------
// Simulated differential gene expression results (RNA-seq treatment vs. control).
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}
const rand = lcg(42);
const randn = () => {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

const FC_THRESHOLD = 1; // log2 fold change cutoff (2-fold)
const P_THRESHOLD = 1.3; // -log10(0.05)

const genePrefixes = ["BRCA", "TP53", "MYC", "EGFR", "KRAS", "PTEN", "AKT", "PIK3", "VEGF", "CDK"];
const geneCount = 600;
const downregulated = [];
const upregulated = [];
const nonsignificant = [];

for (let i = 0; i < geneCount; i++) {
  const logFc = randn() * 1.4;
  const noise = Math.abs(randn()) * 0.9;
  // Genes with larger |fold change| tend to carry more significance (realistic funnel shape).
  const negLog10P = Math.max(0.02, Math.abs(logFc) * 1.6 + noise);
  const label = `${genePrefixes[i % genePrefixes.length]}${i}`;
  const point = { x: Number(logFc.toFixed(3)), y: Number(negLog10P.toFixed(3)), name: label };

  const isSignificant = negLog10P >= P_THRESHOLD && Math.abs(logFc) >= FC_THRESHOLD;
  if (isSignificant && logFc > 0) {
    upregulated.push(point);
  } else if (isSignificant && logFc < 0) {
    downregulated.push(point);
  } else {
    nonsignificant.push(point);
  }
}

// Top significant features by combined score, labeled directly on the chart.
const topLabeled = [...upregulated, ...downregulated]
  .sort((a, b) => Math.abs(b.x) * b.y - Math.abs(a.x) * a.y)
  .slice(0, 6);
const topLabelSet = new Set(topLabeled.map((p) => p.name));

const addDataLabel = (p) => ({
  ...p,
  dataLabels: topLabelSet.has(p.name)
    ? { enabled: true, format: "{point.name}", style: { color: t.ink, fontSize: "12px", fontWeight: "500", textOutline: "none" } }
    : undefined,
});

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: [MUTED, t.palette[2], t.palette[4]],
  title: {
    text: "volcano-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "RNA-seq differential expression: treatment vs. control",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "log2 fold change", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      { value: -FC_THRESHOLD, color: t.inkSoft, dashStyle: "Dash", width: 1.5, zIndex: 3 },
      { value: FC_THRESHOLD, color: t.inkSoft, dashStyle: "Dash", width: 1.5, zIndex: 3 },
    ],
  },
  yAxis: {
    title: { text: "-log10(p-value)", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    plotLines: [{ value: P_THRESHOLD, color: t.inkSoft, dashStyle: "Dash", width: 1.5, zIndex: 3 }],
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false, marker: { radius: 4, symbol: "circle", lineWidth: 0 } },
    scatter: { opacity: 0.65 },
  },
  tooltip: { enabled: false },
  series: [
    { name: "Not significant", data: nonsignificant.map(addDataLabel) },
    { name: "Down-regulated", data: downregulated.map(addDataLabel) },
    { name: "Up-regulated", data: upregulated.map(addDataLabel) },
  ],
});
