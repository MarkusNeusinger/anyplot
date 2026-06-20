// anyplot.ai
// line-retention-cohort: User Retention Curve by Cohort
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-20
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Monthly signup cohorts tracked weekly — 4 cohorts, 13 weeks (week 0 through 12)
// Shows improving retention as product onboarding was refined over Q1 2025
const cohortData = [
  {
    label: "Jan 2025",
    n: 1245,
    color: t.palette[0],
    opacity: 0.55,
    lineWidth: 1.5,
    data: [100, 62, 43, 32, 26, 22, 19, 17, 16, 15, 14, 14, 13],
  },
  {
    label: "Feb 2025",
    n: 1387,
    color: t.palette[1],
    opacity: 0.70,
    lineWidth: 2.0,
    data: [100, 65, 47, 36, 30, 25, 22, 20, 18, 17, 16, 16, 15],
  },
  {
    label: "Mar 2025",
    n: 1523,
    color: t.palette[2],
    opacity: 0.85,
    lineWidth: 2.5,
    data: [100, 70, 53, 42, 35, 31, 28, 26, 24, 23, 22, 22, 21],
  },
  {
    label: "Apr 2025",
    n: 1641,
    color: t.palette[3],
    opacity: 1.0,
    lineWidth: 3.0,
    data: [100, 74, 58, 48, 41, 37, 34, 32, 30, 29, 28, 28, 27],
  },
];

Highcharts.chart("container", {
  chart: {
    type: "spline",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    marginRight: 30,
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "line-retention-cohort · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: {
      text: "Weeks Since Signup",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    tickInterval: 1,
    min: 0,
    max: 12,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    gridLineColor: "transparent",
  },
  yAxis: {
    title: {
      text: "Retention Rate (%)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    min: 0,
    max: 100,
    tickInterval: 20,
    gridLineColor: t.grid,
    labels: {
      style: { color: t.inkSoft, fontSize: "14px" },
      format: "{value}%",
    },
    plotLines: [
      {
        value: 20,
        color: t.inkSoft,
        dashStyle: "Dash",
        width: 1.5,
        label: {
          text: "20% target",
          style: { color: t.inkSoft, fontSize: "12px" },
          align: "right",
          x: -6,
        },
        zIndex: 3,
      },
    ],
  },
  legend: {
    enabled: true,
    layout: "horizontal",
    align: "center",
    verticalAlign: "bottom",
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    spline: {
      marker: {
        enabled: true,
        symbol: "circle",
      },
    },
  },
  series: cohortData.map((c) => ({
    name: `${c.label} (n=${c.n.toLocaleString("en-US")})`,
    data: c.data,
    color: c.color,
    opacity: c.opacity,
    lineWidth: c.lineWidth,
    marker: {
      fillColor: c.color,
      radius: c.lineWidth >= 3.0 ? 4 : 3,
    },
  })),
});
