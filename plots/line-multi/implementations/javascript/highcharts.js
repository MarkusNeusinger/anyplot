// anyplot.ai
// line-multi: Multi-Line Comparison Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Average monthly temperature (°C) across four US cities
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const newYork    = [-1, 0, 5, 11, 17, 22, 25, 24, 20, 14, 8, 2];
const losAngeles = [14, 15, 15, 16, 18, 20, 23, 24, 23, 20, 17, 14];
const chicago    = [-4, -2, 4, 10, 16, 22, 24, 23, 19, 12, 4, -2];
const miami      = [20, 21, 23, 25, 27, 29, 30, 30, 29, 27, 24, 21];

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: { type: "line", backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  colors: t.palette,
  title: { text: "line-multi · javascript · highcharts · anyplot.ai",
           style: { color: t.ink, fontSize: "22px", fontWeight: "600" } },
  xAxis: { categories: months,
           lineColor: t.inkSoft, tickColor: t.inkSoft,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } },
           title:  { text: "Month", style: { color: t.inkSoft, fontSize: "16px" } } },
  yAxis: { title: { text: "Average Temperature (°C)",
                     style: { color: t.inkSoft, fontSize: "16px" } },
           gridLineColor: t.grid,
           labels: { style: { color: t.inkSoft, fontSize: "14px" } } },
  legend: { itemStyle: { color: t.inkSoft, fontSize: "14px" },
            itemHoverStyle: { color: t.ink } },
  plotOptions: { series: { animation: false, lineWidth: 3,
                            marker: { enabled: true, radius: 5 } } },
  series: [
    { name: "New York", data: newYork },
    { name: "Los Angeles", data: losAngeles },
    { name: "Chicago", data: chicago },
    { name: "Miami", data: miami },
  ],
});
