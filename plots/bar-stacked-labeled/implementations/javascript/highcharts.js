// anyplot.ai
// bar-stacked-labeled: Stacked Bar Chart with Total Labels
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Quarterly revenue by product line, in $M.
const quarters = ["Q1", "Q2", "Q3", "Q4"];
const hardware = [41, 38, 44, 51];
const software = [27, 32, 35, 39];
const services = [18, 21, 19, 24];
const support = [11, 14, 13, 16];

// The strongest quarter (highest stacked total) anchors the storytelling
// emphasis below — a soft highlight band plus a bolder, brand-green total
// label draw the eye straight to it.
const peakIndex = quarters.length - 1;
const peakBand = Highcharts.color(t.palette[0]).setOpacity(0.08).get();

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "column",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "bar-stacked-labeled · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "27px", fontWeight: "700" },
  },
  subtitle: {
    text:
      "Q" +
      quarters.length +
      " leads at $" +
      hardware[peakIndex] +
      "M in Hardware — total revenue climbs every quarter",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    categories: quarters,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotBands: [
      {
        from: peakIndex - 0.5,
        to: peakIndex + 0.5,
        color: peakBand,
      },
    ],
  },
  yAxis: {
    title: {
      text: "Revenue ($M)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    endOnTick: false,
    maxPadding: 0.14,
    stackLabels: {
      enabled: true,
      useHTML: true,
      style: { textOutline: "none" },
      formatter: function () {
        const isPeak = this.x === peakIndex;
        const color = isPeak ? t.palette[0] : t.ink;
        const fontSize = isPeak ? "19px" : "17px";
        return (
          '<span style="color:' +
          color +
          ";font-size:" +
          fontSize +
          ';font-weight:700;">$' +
          this.total +
          "M</span>"
        );
      },
    },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    column: {
      borderWidth: 0,
      borderRadius: 2,
      stacking: "normal",
      pointPadding: 0.08,
      groupPadding: 0.14,
    },
  },
  series: [
    { name: "Hardware", data: hardware },
    { name: "Software", data: software },
    { name: "Services", data: services },
    { name: "Support", data: support },
  ],
});
