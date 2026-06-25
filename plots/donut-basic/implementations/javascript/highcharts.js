// anyplot.ai
// donut-basic: Basic Donut Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.0
// Quality: 88/100 | Created: 2026-06-25
//# anyplot-orientation: square
// anyplot.ai
// donut-basic: Basic Donut Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-25

const t = window.ANYPLOT_TOKENS;

// Annual budget allocation by department ($K)
const departments = [
  { name: "R&D",        y: 420 },
  { name: "Sales",      y: 310 },
  { name: "Operations", y: 260 },
  { name: "Marketing",  y: 180 },
  { name: "IT",         y: 145 },
  { name: "HR",         y:  85 },
];

const totalBudget = departments.reduce((s, d) => s + d.y, 0);

Highcharts.chart("container", {
  chart: {
    type: "pie",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    events: {
      render() {
        const s = this.series[0];
        if (!s || !s.center) return;
        const cx = this.plotLeft + s.center[0];
        const cy = this.plotTop  + s.center[1];

        if (this._cv) this._cv.destroy();
        if (this._ct) this._ct.destroy();

        this._cv = this.renderer
          .text(`$${(totalBudget / 1000).toFixed(1)}M`, cx, cy - 6)
          .attr({ align: "center", zIndex: 5 })
          .css({ color: t.ink, fontSize: "38px", fontWeight: "700" })
          .add();

        this._ct = this.renderer
          .text("Total Budget", cx, cy + 26)
          .attr({ align: "center", zIndex: 5 })
          .css({ color: t.inkSoft, fontSize: "15px" })
          .add();
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "donut-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  plotOptions: {
    series: { animation: false },
    pie: {
      innerSize: "55%",
      center: ["50%", "52%"],
      dataLabels: {
        enabled: true,
        format: "<b>{point.name}</b><br>{point.percentage:.1f}%",
        style: {
          color: t.ink,
          fontSize: "13px",
          fontWeight: "normal",
          textOutline: "none",
        },
        connectorColor: t.inkSoft,
        connectorWidth: 1,
        distance: 28,
      },
      borderWidth: 0,
    },
  },
  legend: { enabled: false },
  series: [
    {
      name: "Budget",
      colorByPoint: true,
      data: departments,
    },
  ],
});
