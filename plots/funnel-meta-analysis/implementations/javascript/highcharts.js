// anyplot.ai
// funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-10

const t = window.ANYPLOT_TOKENS;

// Data: 18 RCTs comparing antidepressant vs placebo, log odds ratios and standard errors
const pooledEffect = 0.40;
const seMax = 0.65;

const studies = [
  [0.45, 0.15], [0.30, 0.22], [0.62, 0.18], [0.20, 0.35],
  [0.55, 0.12], [-0.10, 0.40], [0.35, 0.28], [0.78, 0.55],
  [0.15, 0.45], [0.50, 0.20], [0.25, 0.30], [0.70, 0.14],
  [0.42, 0.38], [0.18, 0.50], [-0.08, 0.60], [0.65, 0.25],
  [0.38, 0.16], [0.52, 0.32]
];

// Pseudo 95% CI funnel: apex at (pooled, SE=0), base at (pooled ± 1.96 * seMax, seMax)
const ci96 = 1.96 * seMax;
const funnelLeft  = [{ x: pooledEffect, y: 0 }, { x: pooledEffect - ci96, y: seMax }];
const funnelRight = [{ x: pooledEffect, y: 0 }, { x: pooledEffect + ci96, y: seMax }];

Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" }
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "funnel-meta-analysis · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" }
  },
  subtitle: {
    text: "Antidepressant vs Placebo · 18 Randomized Controlled Trials",
    style: { color: t.inkSoft, fontSize: "14px" }
  },
  xAxis: {
    title: {
      text: "Log Odds Ratio",
      style: { color: t.inkSoft, fontSize: "16px" }
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    gridLineWidth: 1,
    min: -1.6,
    max: 2.2,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotLines: [
      {
        value: 0,
        dashStyle: "ShortDash",
        color: t.inkSoft,
        width: 2,
        zIndex: 2,
        label: {
          text: "Null (OR = 1)",
          verticalAlign: "top",
          y: -8,
          style: { color: t.inkSoft, fontSize: "12px" }
        }
      },
      {
        value: pooledEffect,
        color: t.ink,
        width: 2,
        zIndex: 2,
        label: {
          text: "Pooled OR = 1.49",
          verticalAlign: "top",
          y: -8,
          style: { color: t.ink, fontSize: "12px" }
        }
      }
    ]
  },
  yAxis: {
    title: {
      text: "Standard Error (SE)",
      style: { color: t.inkSoft, fontSize: "16px" }
    },
    reversed: true,
    min: 0,
    max: 0.70,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } }
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink }
  },
  tooltip: {
    formatter: function () {
      return "<b>Log OR:</b> " + this.x.toFixed(2) + "<br><b>SE:</b> " + this.y.toFixed(2);
    }
  },
  plotOptions: {
    series: { animation: false }
  },
  series: [
    {
      type: "scatter",
      name: "Studies (n = 18)",
      data: studies,
      color: t.palette[0],
      marker: {
        radius: 7,
        symbol: "circle",
        lineColor: t.pageBg,
        lineWidth: 1.5
      }
    },
    {
      type: "line",
      name: "95% CI Limits",
      data: funnelLeft,
      color: t.inkSoft,
      lineWidth: 1.5,
      dashStyle: "Dash",
      marker: { enabled: false },
      enableMouseTracking: false
    },
    {
      type: "line",
      name: "95% CI (right)",
      data: funnelRight,
      color: t.inkSoft,
      lineWidth: 1.5,
      dashStyle: "Dash",
      marker: { enabled: false },
      enableMouseTracking: false,
      showInLegend: false
    }
  ]
});
