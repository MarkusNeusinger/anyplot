// anyplot.ai
// bar-stacked: Stacked Bar Chart
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly software company revenue composition by product line ($K)
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
const components = [
  { name: "Subscriptions", data: [20, 25, 30, 36, 42, 50] },
  { name: "Software", data: [58, 62, 65, 70, 74, 78] },
  { name: "Services", data: [30, 32, 35, 33, 38, 40] },
  { name: "Hardware", data: [42, 45, 40, 48, 44, 50] },
];
const totals = months.map((_, i) =>
  components.reduce((sum, c) => sum + c.data[i], 0)
);
const avgTotal = Math.round(
  totals.reduce((a, b) => a + b, 0) / totals.length
);
const subs = components[0].data;
const subsGrowthPct = Math.round(
  ((subs[subs.length - 1] - subs[0]) / subs[0]) * 100
);

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Title (fontsize scaled to length; see plot-generator.md formula) -------
const titleText =
  "Monthly SaaS Revenue by Product Line · bar-stacked · javascript · echarts · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / titleText.length));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: titleText,
    left: "center",
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  legend: {
    top: 70,
    data: components.map((c) => c.name),
    textStyle: { color: t.ink, fontSize: 16 },
  },
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "shadow" },
    formatter: (params) => {
      const idx = params[0].dataIndex;
      const total = totals[idx];
      const rows = params
        .map(
          (p) =>
            `${p.marker} ${p.seriesName}: $${p.value}K (${Math.round(
              (p.value / total) * 100
            )}%)`
        )
        .join("<br/>");
      return `<strong>${months[idx]}</strong><br/>${rows}<br/><strong>Total: $${total}K</strong>`;
    },
  },
  grid: { left: 90, right: 60, top: 130, bottom: 70 },
  xAxis: {
    type: "category",
    data: months,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Revenue ($K)",
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    ...components.map((c, i) => ({
      name: c.name,
      type: "bar",
      stack: "revenue",
      barWidth: "55%",
      data: c.data,
      // Rounded top corners on the topmost stack segment only, for polish.
      ...(i === components.length - 1 && {
        itemStyle: { borderRadius: [6, 6, 0, 0] },
      }),
      // Emphasize the composition-shift story: Subscriptions is the
      // fastest-growing component (+150% Jan→Jun) — call it out on the
      // final bar.
      ...(i === 0 && {
        label: {
          show: true,
          position: "inside",
          color: "#FFFFFF",
          fontSize: 12,
          fontWeight: 600,
          formatter: (params) =>
            params.dataIndex === months.length - 1
              ? `+${subsGrowthPct}%`
              : "",
        },
      }),
    })),
    {
      name: "Total",
      type: "bar",
      stack: "revenue",
      data: months.map(() => 0),
      itemStyle: { color: "transparent" },
      label: {
        show: true,
        position: "top",
        color: t.ink,
        fontSize: 15,
        fontWeight: 500,
        formatter: (params) => totals[params.dataIndex],
      },
      tooltip: { show: false },
      markLine: {
        silent: true,
        symbol: "none",
        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5 },
        label: {
          color: t.inkSoft,
          fontSize: 12,
          formatter: `Avg total: $${avgTotal}K`,
          position: "insideEndTop",
        },
        data: [{ yAxis: avgTotal }],
      },
    },
  ],
});
