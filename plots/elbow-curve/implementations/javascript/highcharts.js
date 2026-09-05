// anyplot.ai
// elbow-curve: Elbow Curve for K-Means Clustering
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 95/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Customer segmentation: K-means clustering on annual spend + visit frequency,
// inertia (within-cluster sum of squares) across candidate cluster counts.
const kValues = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
const inertia = [8420, 4180, 2350, 1580, 1310, 1120, 980, 870, 790, 730];
const elbowK = 4;

const seriesData = kValues.map((k, i) =>
  k === elbowK
    ? { x: k, y: inertia[i], marker: { radius: 11, lineWidth: 3, lineColor: t.ink } }
    : [k, inertia[i]]
);

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: { type: "areaspline", backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "elbow-curve · javascript · highcharts · anyplot.ai",
           style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  xAxis: { title: { text: "Number of Clusters (k)",
                     style: { color: t.inkSoft, fontSize: "16px" } },
           min: 1, max: 10, tickInterval: 1,
           lineColor: t.inkSoft, tickColor: t.inkSoft, gridLineColor: t.grid,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } },
           plotLines: [{
             value: elbowK, color: t.inkSoft, dashStyle: "Dash", width: 1.5, zIndex: 3,
             label: { text: `Optimal k = ${elbowK}`, style: { color: t.inkSoft, fontSize: "14px" },
                      align: "left", x: 8, y: 16 },
           }] },
  yAxis: { title: { text: "Inertia (within-cluster sum of squares)",
                     style: { color: t.inkSoft, fontSize: "16px" } },
           gridLineColor: t.grid,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } } },
  legend: { enabled: false },
  tooltip: { enabled: true, backgroundColor: t.elevatedBg, borderColor: t.grid,
             style: { color: t.ink, fontSize: "13px" },
             formatter() {
               return `k = ${this.x}<br/>Inertia: ${this.y.toLocaleString()}`;
             } },
  plotOptions: { series: { animation: false, lineWidth: 3,
                            fillOpacity: 0.12,
                            marker: { radius: 7, fillColor: t.palette[0], lineWidth: 0 } } },
  series: [{ name: "Inertia", data: seriesData, color: t.palette[0] }],
});
