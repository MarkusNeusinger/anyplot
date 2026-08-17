// anyplot.ai
// area-stacked: Stacked Area Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-17

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly website traffic by source, Jan 2023 - Dec 2024 (24 months).
// Series ordered largest-to-smallest so the biggest source anchors the bottom
// of the stack (spec note: "order series by size, largest at bottom").
let seed = 42;
const lcg = () => {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
};
const noise = (scale) => (lcg() - 0.5) * scale;

const monthNames = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];
const labels = [2023, 2024].flatMap((year) =>
  monthNames.map((m) => `${m} '${String(year).slice(2)}`),
);

const direct = [];
const organicSearch = [];
const referral = [];
const social = [];
labels.forEach((_, i) => {
  const holidayBump = i % 12 >= 10 ? 200 : 0;
  direct.push(Math.round(1300 + i * 8 + holidayBump + noise(60)));
  organicSearch.push(Math.round(700 + i * 22 + noise(50)));
  referral.push(Math.round(380 + i * 3 + noise(30)));
  social.push(Math.round(180 + i * 14 + noise(25)));
});

const hexToRgba = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const series = [
  { label: "Direct", data: direct, color: t.palette[0] },
  { label: "Organic Search", data: organicSearch, color: t.palette[1] },
  { label: "Referral", data: referral, color: t.palette[2] },
  { label: "Social", data: social, color: t.palette[3] },
];

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels,
    datasets: series.map((s, i) => ({
      label: s.label,
      data: s.data,
      borderColor: s.color,
      backgroundColor: hexToRgba(s.color, 0.75),
      borderWidth: 2,
      pointRadius: 0,
      tension: 0,
      fill: i === 0 ? "origin" : "-1",
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      title: {
        display: true,
        text: "area-stacked · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: {
        position: "top",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 24, padding: 20 },
      },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 12,
        },
        grid: { display: false },
        title: {
          display: true,
          text: "Month",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        stacked: true,
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Website Visits (thousands)",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
