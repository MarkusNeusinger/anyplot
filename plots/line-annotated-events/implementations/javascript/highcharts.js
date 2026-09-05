// anyplot.ai
// line-annotated-events: Annotated Line Plot with Event Markers
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 83/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Tiny fixed-seed LCG — the browser has no seeded RNG.
let lcgState = 42;
function lcgRandom() {
  lcgState = (lcgState * 1103515245 + 12345) & 0x7fffffff;
  return lcgState / 0x7fffffff;
}

const dayMs = 24 * 60 * 60 * 1000;
const startDate = Date.UTC(2024, 0, 1);
const numDays = 180;

// Milestones that shift the daily-active-users trajectory.
const events = [
  { day: 18, label: "v2.0 Launch", stepGain: 55 },
  { day: 52, label: "Referral Program", stepGain: 35 },
  { day: 88, label: "Server Outage", stepGain: -70 },
  { day: 124, label: "Marketing Campaign", stepGain: 60 },
  { day: 158, label: "Holiday Surge", stepGain: 40 },
];

const dailyActiveUsers = [];
let growthRate = 20;
let level = 9800;
for (let day = 0; day < numDays; day++) {
  const milestone = events.find((e) => e.day === day);
  if (milestone) growthRate += milestone.stepGain > 0 ? 6 : -4;

  const weeklySeasonality = Math.sin((day / 7) * 2 * Math.PI) * 220;
  const noise = (lcgRandom() - 0.5) * 260;
  level += growthRate + (lcgRandom() - 0.5) * 8;
  if (milestone) level += milestone.stepGain;

  const value = Math.round(level + weeklySeasonality + noise);
  dailyActiveUsers.push([startDate + day * dayMs, value]);
}

// Positive milestones stay brand-lavender; the one negative event (the outage)
// gets the Imprint semantic-red anchor so color reinforces the up/down story.
const eventColor = (e) => (e.stepGain < 0 ? t.palette[4] : t.palette[1]);

const eventPoints = events.map((e) => ({
  x: startDate + e.day * dayMs,
  y: dailyActiveUsers[e.day][1],
  color: eventColor(e),
}));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "spline",
    backgroundColor: "transparent",
    animation: false,
    spacingTop: 4,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "line-annotated-events · javascript · highcharts · anyplot.ai",
    margin: 10,
    style: { color: t.ink, fontSize: "27px", fontWeight: "600" },
  },
  xAxis: {
    type: "datetime",
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: { text: "Date", style: { color: t.inkSoft, fontSize: "16px" } },
    plotLines: events.map((e, i) => ({
      value: startDate + e.day * dayMs,
      color: eventColor(e),
      dashStyle: "Dash",
      width: 1.5,
      zIndex: 1,
      label: {
        text: e.label,
        rotation: 0,
        align: "left",
        x: 6,
        y: i % 2 === 0 ? 22 : 42,
        style: { color: t.inkSoft, fontSize: "12px" },
      },
    })),
  },
  yAxis: {
    title: {
      text: "Daily Active Users",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    maxPadding: 0.04,
    endOnTick: false,
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    spline: { lineWidth: 3, marker: { enabled: false } },
  },
  series: [
    {
      name: "Daily Active Users",
      data: dailyActiveUsers,
      color: t.palette[0],
      zIndex: 1,
    },
    {
      type: "scatter",
      name: "Milestones",
      data: eventPoints,
      color: t.palette[1],
      marker: { radius: 7, symbol: "circle", lineWidth: 1.5, lineColor: t.pageBg },
      zIndex: 10,
      // legend swatch stays lavender for the series as a whole; the one
      // negative event (Server Outage) overrides its own marker color above.
    },
  ],
});
