// anyplot.ai
// point-basic: Point Estimate Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Estimated effect of study interventions on exam score, points gained/lost
// vs. a no-intervention baseline, with 95% confidence intervals.
const categories = [
  "Tutoring",
  "Study Group",
  "Practice Tests",
  "Flashcards",
  "Online Course",
  "Peer Review",
  "Sleep Coaching",
];
const estimate = [6.8, 4.1, 5.6, 2.3, 3.4, 1.2, -0.6];
const marginOfError = [1.4, 1.9, 1.1, 1.6, 1.3, 1.8, 1.5];
const lowerBound = estimate.map((v, i) => v - marginOfError[i]);
const upperBound = estimate.map((v, i) => v + marginOfError[i]);

// Highcharts core has no errorbar/columnrange series (those live in the
// unloaded highcharts-more module) — draw the CI whiskers natively with the
// SVGRenderer once the axes are laid out, keyed off the same pixel space the
// scatter points use.
const intervalColor = Highcharts.color(t.palette[0]).setOpacity(0.55).get();
const capHalfPx = 9;

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    inverted: true,
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      load() {
        const chart = this;
        const xAxis = chart.xAxis[0];
        const yAxis = chart.yAxis[0];
        categories.forEach((_, i) => {
          const rowPixel = xAxis.toPixels(i);
          const lowPixel = yAxis.toPixels(lowerBound[i]);
          const highPixel = yAxis.toPixels(upperBound[i]);
          chart.renderer
            .path(["M", lowPixel, rowPixel, "L", highPixel, rowPixel])
            .attr({ "stroke-width": 3, stroke: intervalColor, zIndex: 4 })
            .add();
          [lowPixel, highPixel].forEach((xPixel) => {
            chart.renderer
              .path([
                "M",
                xPixel,
                rowPixel - capHalfPx,
                "L",
                xPixel,
                rowPixel + capHalfPx,
              ])
              .attr({ "stroke-width": 3, stroke: intervalColor, zIndex: 4 })
              .add();
          });
        });
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "point-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories,
    minPadding: 0.08,
    maxPadding: 0.08,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Effect on Exam Score (points)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    minPadding: 0.06,
    maxPadding: 0.06,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: 0,
        color: t.inkSoft,
        width: 1.5,
        dashStyle: "ShortDash",
        zIndex: 3,
      },
    ],
  },
  legend: { enabled: false },
  tooltip: {
    formatter() {
      const i = this.point.x;
      return (
        `<b>${categories[i]}</b><br/>` +
        `Estimate: ${estimate[i].toFixed(1)}<br/>` +
        `95% CI: [${lowerBound[i].toFixed(1)}, ${upperBound[i].toFixed(1)}]`
      );
    },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: { radius: 8, symbol: "circle", lineWidth: 0 },
    },
  },
  series: [
    {
      name: "Estimate",
      data: estimate.map((v, i) => [i, v]),
      zIndex: 5,
    },
    {
      // Invisible — only extends the value axis to cover the CI whiskers,
      // which are custom-drawn (see chart.events.load) and outside any
      // series Highcharts would otherwise use for axis-extent calculation.
      name: "CI bounds",
      data: [...lowerBound, ...upperBound].map((v, j) => [
        j % categories.length,
        v,
      ]),
      marker: { enabled: false },
      lineWidth: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
  ],
});
