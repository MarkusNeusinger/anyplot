// anyplot.ai
// line-impurity-comparison: Gini Impurity vs Entropy Comparison
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (deterministic, 101 points so p = 0.5 lands exactly on a sample) -
const n = 101;
const probabilities = Array.from({ length: n }, (_, i) => i / (n - 1));
const midIndex = (n - 1) / 2; // p = 0.5, where both criteria peak

function giniImpurity(p) {
  return 2 * p * (1 - p);
}

function entropy(p) {
  if (p === 0 || p === 1) return 0; // edge cases: entropy defined as 0
  return -p * Math.log2(p) - (1 - p) * Math.log2(1 - p);
}

function seriesData(valueFn, markerColor, labelY) {
  return probabilities.map((p, i) => {
    const y = valueFn(p);
    if (i !== midIndex) return [p, y];
    return {
      x: p,
      y,
      marker: { enabled: true, radius: 6, fillColor: markerColor, lineColor: t.pageBg, lineWidth: 2 },
      dataLabels: {
        enabled: true,
        format: "{y:.2f}",
        y: labelY,
        style: { color: t.ink, fontSize: "14px", fontWeight: "600", textOutline: "none" },
      },
    };
  });
}

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: { type: "line", backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "line-impurity-comparison · javascript · highcharts · anyplot.ai",
           style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  xAxis: {
    title: { text: "Probability p", style: { color: t.inkSoft, fontSize: "16px" } },
    min: 0,
    max: 1,
    tickInterval: 0.1,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [{
      value: 0.5,
      color: t.inkSoft,
      dashStyle: "Dash",
      width: 1.5,
      zIndex: 3,
      label: {
        text: "p = 0.5 · maximum impurity",
        rotation: 0,
        align: "center",
        verticalAlign: "bottom",
        y: -8,
        style: { color: t.inkSoft, fontSize: "13px" },
      },
    }],
  },
  yAxis: {
    title: { text: "Impurity Measure (normalized)", style: { color: t.inkSoft, fontSize: "16px" } },
    min: 0,
    max: 1.05,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    align: "center",
    verticalAlign: "bottom",
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    backgroundColor: t.elevatedBg,
    style: { color: t.ink, fontSize: "13px" },
    valueDecimals: 3,
  },
  plotOptions: {
    series: { animation: false, marker: { enabled: false }, lineWidth: 3 },
  },
  series: [
    {
      name: "Gini impurity — 2p(1−p)",
      data: seriesData(giniImpurity, t.palette[0], -16),
      color: t.palette[0],
    },
    {
      name: "Entropy (normalized) — −p·log₂p − (1−p)·log₂(1−p)",
      data: seriesData(entropy, t.palette[1], 22),
      color: t.palette[1],
      dashStyle: "ShortDash",
    },
  ],
});
