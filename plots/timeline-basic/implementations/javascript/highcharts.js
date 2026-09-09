// anyplot.ai
// timeline-basic: Event Timeline
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Software product roadmap for 2024, grouped by phase category.
const events = [
  { date: Date.UTC(2024, 0, 15), name: "Kickoff", category: "Planning" },
  { date: Date.UTC(2024, 1, 10), name: "Requirements Finalized", category: "Planning" },
  { date: Date.UTC(2024, 2, 5), name: "Design Review", category: "Planning" },
  { date: Date.UTC(2024, 2, 25), name: "Alpha Build", category: "Development" },
  { date: Date.UTC(2024, 3, 20), name: "Core Features Complete", category: "Development" },
  { date: Date.UTC(2024, 4, 15), name: "Beta Release", category: "Development" },
  { date: Date.UTC(2024, 5, 10), name: "User Testing Begins", category: "Development" },
  { date: Date.UTC(2024, 6, 8), name: "Performance Optimization", category: "Development" },
  { date: Date.UTC(2024, 7, 1), name: "Feature Freeze", category: "Development" },
  { date: Date.UTC(2024, 7, 25), name: "Release Candidate", category: "Release" },
  { date: Date.UTC(2024, 8, 15), name: "Marketing Launch", category: "Release" },
  { date: Date.UTC(2024, 9, 1), name: "General Availability", category: "Release" },
  { date: Date.UTC(2024, 10, 5), name: "Post-Launch Review", category: "Release" },
  { date: Date.UTC(2024, 11, 1), name: "Version 1.1 Planning", category: "Planning" },
];

// Alternate label sides in chronological order so neighboring events never
// compete for the same vertical space, regardless of category.
const ABOVE = { y: -18, verticalAlign: "bottom" };
const BELOW = { y: 18, verticalAlign: "top" };
events.forEach((event, index) => {
  event.side = index % 2 === 0 ? ABOVE : BELOW;
});

const categories = ["Planning", "Development", "Release"];
const categoryColors = { Planning: t.palette[0], Development: t.palette[1], Release: t.palette[2] };
const series = categories.map((category) => ({
  name: category,
  type: "scatter",
  color: categoryColors[category],
  marker: { radius: 10, lineColor: t.pageBg, lineWidth: 2 },
  data: events
    .filter((event) => event.category === category)
    .map((event) => ({
      x: event.date,
      y: 0,
      name: event.name,
      dataLabels: { y: event.side.y, verticalAlign: event.side.verticalAlign },
    })),
  dataLabels: {
    enabled: true,
    format: "{point.name}",
    align: "center",
    style: { color: t.ink, fontSize: "14px", fontWeight: "600", textOutline: "none" },
  },
}));

// --- Chart -----------------------------------------------------------------
Highcharts.chart("container", {
  chart: { type: "scatter", backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "timeline-basic · javascript · highcharts · anyplot.ai",
           style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  subtitle: { text: "Software Product Roadmap 2024",
              style: { color: t.inkSoft, fontSize: "14px" } },
  xAxis: {
    type: "datetime",
    min: Date.UTC(2024, 0, 1),
    max: Date.UTC(2024, 11, 31),
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineWidth: 0,
    dateTimeLabelFormats: { month: "%b" },
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    visible: false,
    min: -1.6,
    max: 1.6,
  },
  legend: {
    align: "center",
    verticalAlign: "bottom",
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    formatter() {
      return `<b>${this.point.name}</b><br>${Highcharts.dateFormat("%b %e, %Y", this.point.x)}`;
    },
  },
  plotOptions: { series: { animation: false } },
  series: [
    {
      name: "Timeline",
      type: "line",
      data: [
        [Date.UTC(2024, 0, 1), 0],
        [Date.UTC(2024, 11, 31), 0],
      ],
      color: t.inkSoft,
      lineWidth: 2,
      marker: { enabled: false },
      enableMouseTracking: false,
      showInLegend: false,
      dataLabels: { enabled: false },
    },
    ...series,
  ],
});
