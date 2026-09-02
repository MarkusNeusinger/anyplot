// anyplot.ai
// choropleth-basic: Choropleth Map with Regional Coloring
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 79/100 | Created: 2026-09-02

// Chart.js has no built-in geographic/shape geometry (that lives only in the
// chartjs-chart-geo plugin, which is not installed in this runtime — see
// prompts/library/chartjs.md "No Workarounds"). This renders the same
// region -> value story as a tile map: one square per region, positioned by
// its real-world longitude/latitude, colored on the Imprint sequential scale.
// Region "boundaries" are the square's stroke; missing data renders as a
// muted gray tile, per the specification's data-handling note.
const t = window.ANYPLOT_TOKENS;
const MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ----------------------------------------
// Renewable share of electricity generation (%) by country, with approximate
// centroid coordinates. Two countries carry no reading to demonstrate the
// missing-data handling the spec calls for.
const countries = [
  { code: "CA", lon: -106.3, lat: 56.1, value: 68 },
  { code: "US", lon: -95.7, lat: 37.1, value: 21 },
  { code: "MX", lon: -102.6, lat: 23.6, value: 24 },
  { code: "BR", lon: -51.9, lat: -14.2, value: 84 },
  { code: "AR", lon: -63.6, lat: -38.4, value: 33 },
  { code: "CO", lon: -74.1, lat: 4.6, value: 70 },
  { code: "PE", lon: -75.2, lat: -9.2, value: 60 },
  { code: "CL", lon: -71.5, lat: -35.7, value: 46 },
  { code: "GB", lon: -3.4, lat: 55.4, value: 43 },
  { code: "FR", lon: 2.2, lat: 46.6, value: 27 },
  { code: "DE", lon: 10.5, lat: 51.2, value: 46 },
  { code: "ES", lon: -3.7, lat: 40.5, value: 50 },
  { code: "IT", lon: 12.6, lat: 41.9, value: 41 },
  { code: "NO", lon: 8.5, lat: 60.5, value: 98 },
  { code: "SE", lon: 18.6, lat: 60.1, value: 68 },
  { code: "PL", lon: 19.1, lat: 51.9, value: 17 },
  { code: "RU", lon: 105.3, lat: 61.5, value: 20 },
  { code: "TR", lon: 35.2, lat: 38.9, value: 44 },
  { code: "EG", lon: 30.8, lat: 26.8, value: 12 },
  { code: "NG", lon: 8.7, lat: 9.1, value: null },
  { code: "ZA", lon: 22.9, lat: -30.6, value: 9 },
  { code: "KE", lon: 37.9, lat: -0.0, value: 90 },
  { code: "MA", lon: -7.1, lat: 31.8, value: 20 },
  { code: "SA", lon: 45.1, lat: 23.9, value: 1 },
  { code: "IN", lon: 78.9, lat: 20.6, value: 23 },
  { code: "CN", lon: 104.1, lat: 35.9, value: 31 },
  { code: "JP", lon: 138.3, lat: 36.2, value: 22 },
  { code: "KR", lon: 127.8, lat: 35.9, value: 9 },
  { code: "ID", lon: 113.9, lat: -0.8, value: null },
  { code: "TH", lon: 100.9, lat: 15.9, value: 18 },
  { code: "VN", lon: 108.8, lat: 14.1, value: 40 },
  { code: "AU", lon: 133.8, lat: -25.3, value: 32 },
  { code: "NZ", lon: 174.9, lat: -40.9, value: 87 },
];

// --- Imprint sequential scale (green -> blue), binned for a readable legend
const hexToRgb = (hex) => ({
  r: parseInt(hex.slice(1, 3), 16),
  g: parseInt(hex.slice(3, 5), 16),
  b: parseInt(hex.slice(5, 7), 16),
});
const lerp = (a, b, f) => Math.round(a + (b - a) * f);
const seqRgb = (frac) => {
  const c0 = hexToRgb(t.seq[0]);
  const c1 = hexToRgb(t.seq[1]);
  return { r: lerp(c0.r, c1.r, frac), g: lerp(c0.g, c1.g, frac), b: lerp(c0.b, c1.b, frac) };
};
const toCss = ({ r, g, b }) => `rgb(${r}, ${g}, ${b})`;
// WCAG-ish relative luminance so a code label always reads against its own tile,
// regardless of theme (tile fill colors are identical across themes).
const luminance = ({ r, g, b }) => 0.299 * r + 0.587 * g + 0.114 * b;
const LABEL_LIGHT = "#FFFDF6";
const LABEL_DARK = "#1A1A17";

const bins = [
  { label: "< 10%", max: 10 },
  { label: "10–25%", max: 25 },
  { label: "25–40%", max: 40 },
  { label: "40–65%", max: 65 },
  { label: "≥ 65%", max: Infinity },
].map((bin, i, arr) => {
  const rgb = seqRgb(i / (arr.length - 1));
  return { ...bin, color: toCss(rgb), textColor: luminance(rgb) > 140 ? LABEL_DARK : LABEL_LIGHT };
});

const binIndex = (value) => bins.findIndex((bin) => value <= bin.max);
const mutedTextColor = luminance(hexToRgb(MUTED)) > 140 ? LABEL_DARK : LABEL_LIGHT;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// A tile-map has no room for chartjs-chart-geo's boundary shapes (not
// installed — see prompts/library/chartjs.md), so region codes are drawn
// directly onto each square with a plain Chart.js plugin (native canvas
// access, no external package) instead.
const regionLabelPlugin = {
  id: "regionLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    chart.data.datasets.forEach((dataset, dsIndex) => {
      const meta = chart.getDatasetMeta(dsIndex);
      meta.data.forEach((point, i) => {
        const raw = dataset.data[i];
        ctx.save();
        ctx.font = "600 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
        ctx.fillStyle = dataset.textColor;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(raw.code, point.x, point.y);
        ctx.restore();
      });
    });
  },
};

// --- Chart ---------------------------------------------------------------
const datasets = bins.map((bin, i) => ({
  label: `${bin.label} renewable`,
  data: countries.filter((c) => c.value !== null && binIndex(c.value) === i),
  backgroundColor: bin.color,
  textColor: bin.textColor,
  borderColor: t.ink,
  borderWidth: 1.5,
  pointStyle: "rect",
  pointRadius: 20,
  pointHoverRadius: 22,
}));
datasets.push({
  label: "No data",
  data: countries.filter((c) => c.value === null),
  backgroundColor: MUTED,
  textColor: mutedTextColor,
  borderColor: t.ink,
  borderWidth: 1.5,
  pointStyle: "rect",
  pointRadius: 20,
  pointHoverRadius: 22,
});

const title = "Renewable Electricity Share · choropleth-basic · javascript · chartjs · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));

new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: datasets.map((d) => ({
      ...d,
      data: d.data.map((c) => ({ x: c.lon, y: c.lat, code: c.code, value: c.value })),
    })),
  },
  plugins: [regionLabelPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, bottom: 8, left: 16, right: 16 } },
    plugins: {
      title: { display: true, text: title, color: t.ink, font: { size: titleFontSize, weight: "500" } },
      legend: {
        position: "bottom",
        labels: { color: t.inkSoft, font: { size: 16 }, boxWidth: 22, boxHeight: 22, padding: 18 },
      },
      tooltip: {
        callbacks: {
          title: () => "",
          label: (ctx) =>
            ctx.raw.value === null || ctx.raw.value === undefined
              ? `${ctx.raw.code}: no data`
              : `${ctx.raw.code}: ${ctx.raw.value}% renewable`,
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: -170,
        max: 179,
        display: true,
        border: { display: false },
        ticks: { display: false },
        grid: { color: t.grid },
      },
      y: {
        type: "linear",
        min: -58,
        max: 82,
        display: true,
        border: { display: false },
        ticks: { display: false },
        grid: { color: t.grid },
      },
    },
  },
});
