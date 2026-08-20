// anyplot.ai
// pie-basic: Basic Pie Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-20
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const companies = ["Nimbus Cloud", "Vertex Systems", "Halcyon Labs", "Ferro Dynamics", "Quinta Networks", "Others"];
const marketShare = [31.4, 22.8, 18.5, 12.9, 8.7, 5.7];

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
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "pie-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Cloud infrastructure market share by vendor",
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
      borderWidth: 2,
      borderColor: t.pageBg,
      slicedOffset: 24,
      dataLabels: {
        enabled: true,
        format: "{point.percentage:.1f}%",
        distance: 20,
        style: {
          color: t.ink,
          fontSize: "15px",
          fontWeight: "600",
          textOutline: "none",
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
