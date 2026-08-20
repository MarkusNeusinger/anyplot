// anyplot.ai
// pie-basic: Basic Pie Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 95/100 | Created: 2026-08-20
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const companies = ["Nimbus Cloud", "Vertex Systems", "Halcyon Labs", "Ferro Dynamics", "Quinta Networks", "Others"];
const marketShare = [31.4, 22.8, 18.5, 12.9, 8.7, 5.7];
const leader = { name: companies[0], share: marketShare[0] };

// Slightly explode the largest slice for emphasis
const sliceData = companies.map((name, i) => ({
  name,
  y: marketShare[i],
  sliced: i === 0,
  selected: i === 0,
}));

// --- Chart -----------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "pie",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    // Highcharts-distinctive touch: draw a center label into the donut hole
    // via the SVG renderer, reinforcing the "market leader" story.
    events: {
      render() {
        if (this.centerLabel) this.centerLabel.destroy();
        this.centerLabel = this.renderer
          .text(
            `<div style="text-align:center;line-height:1.35">` +
              `<div style="font-size:12px;letter-spacing:0.05em;text-transform:uppercase;color:${t.inkSoft}">Market leader</div>` +
              `<div style="font-size:17px;font-weight:700;color:${t.ink}">${leader.name}</div>` +
              `<div style="font-size:24px;font-weight:700;color:${t.palette[0]}">${leader.share.toFixed(1)}%</div>` +
              `</div>`,
            0,
            0,
            true,
          )
          .add();
        const box = this.centerLabel.getBBox();
        this.centerLabel.attr({
          x: this.plotLeft + this.plotWidth / 2 - box.width / 2,
          y: this.plotTop + this.plotHeight / 2 - box.height / 2,
        });
      },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "pie-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: `Cloud infrastructure market share by vendor — ${leader.name} leads at ${leader.share.toFixed(1)}%`,
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  tooltip: {
    pointFormat: "{series.name}: <b>{point.percentage:.1f}%</b>",
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    pie: {
      allowPointSelect: false,
      showInLegend: true,
      innerSize: "55%",
      borderWidth: 2,
      borderColor: t.pageBg,
      slicedOffset: 24,
      dataLabels: {
        enabled: true,
        distance: 20,
        useHTML: true,
        // Highcharts-distinctive connector shape (not a generic default) plus
        // a bolder, name-carrying label on the leading slice only.
        connectorShape: "crookedLine",
        crookDistance: "70%",
        style: {
          color: t.ink,
          fontSize: "15px",
          fontWeight: "600",
          textOutline: "none",
        },
        formatter() {
          if (this.point.index === 0) {
            return `<b>${this.point.name}</b><br/>${this.point.percentage.toFixed(1)}%`;
          }
          return `${this.point.percentage.toFixed(1)}%`;
        },
      },
    },
  },
  series: [
    {
      name: "Market share",
      colorByPoint: true,
      data: sliceData,
    },
  ],
});
