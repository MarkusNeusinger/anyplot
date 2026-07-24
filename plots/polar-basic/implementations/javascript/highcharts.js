// anyplot.ai
// polar-basic: Basic Polar Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-07-24
//# anyplot-orientation: square

// Only the core `highcharts` bundle is loaded (no highcharts-more), so the
// native polar chart type isn't available. We project each (hour, visits)
// polar coordinate to Cartesian ourselves and draw the grid rings, spokes,
// labels, and data curve with the core SVG renderer — same technique the
// radar-basic implementation uses for its polygon overlay.
const t = window.ANYPLOT_TOKENS;

// --- Data (average website visits by hour of day, 24-hour cycle) -----------
const HOURS = Array.from({ length: 24 }, (_, i) => i);
const VISITS = [
  850, 620, 480, 390, 350, 420, 680, 1200, 1900, 2400, 2650, 2800, 2900, 2950,
  2850, 2700, 2600, 2750, 3100, 3600, 3950, 3700, 2900, 1800,
];
const MAX_VALUE = 4000;
const RING_LEVELS = [1000, 2000, 3000, 4000];
const SPOKE_HOURS = [0, 3, 6, 9, 12, 15, 18, 21];
const SPOKE_LABELS = ["12 AM", "3 AM", "6 AM", "9 AM", "12 PM", "3 PM", "6 PM", "9 PM"];

const formatHour = (hour) => {
  const period = hour < 12 ? "AM" : "PM";
  const h12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${h12}:00 ${period}`;
};

const TITLE = "polar-basic · javascript · highcharts · anyplot.ai";
const titleFs = Math.round(22 * Math.min(1, 67 / TITLE.length)) + "px";

// --- Chart (empty core chart used as a canvas for the renderer overlay) ----
const chart = Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    margin: [150, 90, 90, 90],
  },
  credits: { enabled: false },
  title: {
    text: TITLE,
    style: { color: t.ink, fontSize: titleFs, fontWeight: "600" },
  },
  subtitle: {
    text: "Average hourly visits over a 24-hour cycle",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: { visible: false, gridLineWidth: 0, lineWidth: 0, tickLength: 0 },
  yAxis: { visible: false, gridLineWidth: 0, lineWidth: 0, tickLength: 0 },
  legend: { enabled: false },
  tooltip: {
    enabled: true,
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    style: { color: t.ink },
    formatter() {
      return `<b>${this.point.name}</b><br/>${this.point.custom.actualValue.toLocaleString()} visits`;
    },
  },
  plotOptions: { series: { animation: false } },
  series: [],
});

// Fix the (visible: false) axes to a known pixel-space extent so a real
// scatter series can be data-bound at the same polar-projected coordinates
// the renderer overlay uses below — this keeps the PNG output identical
// while giving the interactive HTML genuine Highcharts series/tooltip usage.
chart.xAxis[0].setExtremes(0, chart.plotWidth, false);
chart.yAxis[0].setExtremes(0, chart.plotHeight, false);

// --- Geometry ----------------------------------------------------------------
const cx = chart.plotLeft + chart.plotWidth / 2;
const cy = chart.plotTop + chart.plotHeight / 2;
const outerR = Math.min(chart.plotWidth, chart.plotHeight) / 2 - 70;

// hour 0 points straight up (midnight); hours proceed clockwise like a clock face
const angleOf = (hour) => -Math.PI / 2 + (hour / 24) * (2 * Math.PI);
const pointAt = (hour, radiusFrac) => {
  const angle = angleOf(hour);
  return [cx + outerR * radiusFrac * Math.cos(angle), cy + outerR * radiusFrac * Math.sin(angle)];
};

// --- Radial grid rings ---------------------------------------------------------
RING_LEVELS.forEach((level) => {
  chart.renderer
    .circle(cx, cy, outerR * (level / MAX_VALUE))
    .attr({ stroke: t.grid, "stroke-width": 1, fill: "none", zIndex: 1 })
    .add();
});

// --- Angular spokes + hour labels ----------------------------------------------
SPOKE_HOURS.forEach((hour, i) => {
  const [ox, oy] = pointAt(hour, 1);
  chart.renderer
    .path(["M", cx, cy, "L", ox, oy])
    .attr({ stroke: t.inkSoft, "stroke-width": 1, zIndex: 1 })
    .add();

  const angle = angleOf(hour);
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const [lx, ly] = pointAt(hour, 1 + 30 / outerR);
  const align = cos > 0.3 ? "left" : cos < -0.3 ? "right" : "center";
  chart.renderer
    .text(SPOKE_LABELS[i], lx, ly + sin * 6 + 5)
    .attr({ align, zIndex: 5 })
    .css({ fontSize: "15px", fontWeight: "600", color: t.ink, fontFamily: "inherit" })
    .add();
});

// --- Ring scale labels (along the top spoke) -----------------------------------
RING_LEVELS.forEach((level) => {
  const [, ly] = pointAt(0, level / MAX_VALUE);
  chart.renderer
    .text(level.toLocaleString(), cx + 8, ly + 4)
    .attr({ align: "left", zIndex: 4 })
    .css({ fontSize: "12px", color: t.inkSoft, fontFamily: "inherit" })
    .add();
});

// --- Data curve (closed loop — hour 23 wraps back to hour 0) -------------------
const vertices = HOURS.map((hour) => pointAt(hour, VISITS[hour] / MAX_VALUE));
const path = ["M"];
vertices.forEach(([x, y], i) => path.push(...(i === 0 ? [x, y] : ["L", x, y])));
path.push("Z");

chart.renderer
  .path(path)
  .attr({
    fill: t.palette[0],
    "fill-opacity": 0.2,
    stroke: t.palette[0],
    "stroke-width": 3,
    "stroke-linejoin": "round",
    zIndex: 3,
  })
  .add();

vertices.forEach(([x, y]) => {
  chart.renderer
    .circle(x, y, 5)
    .attr({ fill: t.palette[0], stroke: t.pageBg, "stroke-width": 1.5, zIndex: 4 })
    .add();
});

// Real Highcharts scatter series at the same vertex pixels (mapped through
// the fixed-extent axes above) — markers stay hidden so the PNG is
// untouched, but each point is genuinely data-bound and hoverable in the
// interactive HTML, with the tooltip reporting the actual hour and visits.
chart.addSeries(
  {
    type: "scatter",
    name: "Hourly visits",
    color: t.palette[0],
    enableMouseTracking: true,
    stickyTracking: false,
    animation: false,
    marker: {
      enabled: false,
      radius: 6,
      states: { hover: { enabled: true, radius: 6, lineWidth: 1.5, lineColor: t.pageBg } },
    },
    data: vertices.map(([x, y], i) => ({
      x: x - chart.plotLeft,
      y: chart.plotTop + chart.plotHeight - y,
      name: formatHour(HOURS[i]),
      custom: { actualValue: VISITS[i] },
    })),
  },
  false
);
chart.redraw();
