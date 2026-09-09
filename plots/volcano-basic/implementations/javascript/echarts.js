// anyplot.ai
// volcano-basic: Volcano Plot for Statistical Significance
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-09

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const inkMuted = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data: simulated RNA-seq differential expression (deterministic LCG) ----
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}
function randNormal() {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const GENE_STEMS = ["TP53", "BRCA1", "EGFR", "MYC", "KRAS", "PTEN", "AKT1", "PIK3CA", "STAT3", "NFKB1", "VEGFA", "CDKN2A"];
const FC_THRESHOLD = 1; // log2 fold change cutoff (2-fold)
const P_THRESHOLD = 1.3; // -log10(0.05)

const notSignificant = [];
const upRegulated = [];
const downRegulated = [];

for (let i = 0; i < 650; i += 1) {
  const log2FoldChange = randNormal() * 1.7;
  const negLog10Pvalue = Math.max(0, Math.abs(log2FoldChange) * 1.5 + randNormal() * 1.2 + rand() * 0.3);
  const gene = `${GENE_STEMS[i % GENE_STEMS.length]}${Math.floor(i / GENE_STEMS.length) + 1}`;
  const point = { name: gene, value: [log2FoldChange, negLog10Pvalue] };

  if (negLog10Pvalue < P_THRESHOLD || Math.abs(log2FoldChange) < FC_THRESHOLD) {
    notSignificant.push(point);
  } else if (log2FoldChange > 0) {
    upRegulated.push(point);
  } else {
    downRegulated.push(point);
  }
}

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "volcano-basic · javascript · echarts · anyplot.ai",
    left: "center",
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    top: 56,
    data: ["Not significant", "Up-regulated", "Down-regulated"],
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemWidth: 14,
    itemHeight: 14,
  },
  tooltip: {
    trigger: "item",
    formatter: (p) => `${p.data.name}<br/>log2FC: ${p.data.value[0].toFixed(2)}<br/>-log10(p): ${p.data.value[1].toFixed(2)}`,
  },
  grid: { left: 90, right: 70, top: 150, bottom: 90 },
  xAxis: {
    type: "value",
    name: "log2(Fold Change)",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "-log10(p-value)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Not significant",
      type: "scatter",
      data: notSignificant,
      symbolSize: 8,
      itemStyle: { color: inkMuted, opacity: 0.5, borderColor: t.pageBg, borderWidth: 0.5 },
      markLine: {
        silent: true,
        symbol: "none",
        label: { show: false },
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5, opacity: 0.6 },
        data: [{ yAxis: P_THRESHOLD }, { xAxis: -FC_THRESHOLD }, { xAxis: FC_THRESHOLD }],
      },
    },
    {
      name: "Down-regulated",
      type: "scatter",
      data: downRegulated,
      symbolSize: 9,
      itemStyle: { color: t.palette[2], opacity: 0.75, borderColor: t.pageBg, borderWidth: 0.5 },
    },
    {
      name: "Up-regulated",
      type: "scatter",
      data: upRegulated,
      symbolSize: 9,
      itemStyle: { color: t.palette[4], opacity: 0.75, borderColor: t.pageBg, borderWidth: 0.5 },
    },
  ],
});
