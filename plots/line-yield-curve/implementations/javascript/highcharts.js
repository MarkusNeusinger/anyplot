// anyplot.ai
// line-yield-curve: Yield Curve (Interest Rate Term Structure)
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-10

//# anyplot-orientation: landscape

const theme = window.ANYPLOT_THEME;
const t = window.ANYPLOT_TOKENS;

// U.S. Treasury yield curve snapshots (maturity years → annualized yield %)
const matValues = [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30];
const matLabels  = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"];

// Log-transform x-positions for proper time spacing on a linear axis
// (equivalent to a log axis, but avoids Highcharts' auto label-culling on log axes)
const logX = matValues.map((v) => Math.log10(v) * 10);
// logX ≈ [-10.8, -6.0, -3.0, 0.0, 3.0, 4.8, 7.0, 8.5, 10.0, 13.0, 14.8]

// Three historical U.S. Treasury snapshots showing different curve shapes
const jan2021 = [0.05, 0.04, 0.05, 0.07, 0.13, 0.21, 0.46, 0.73, 1.07, 1.63, 1.83]; // Normal
const nov2022 = [3.42, 4.32, 4.60, 4.75, 4.57, 4.43, 4.13, 4.01, 3.96, 4.13, 3.93]; // Inverted
const jun2024 = [5.27, 5.37, 5.38, 5.10, 4.73, 4.48, 4.31, 4.30, 4.28, 4.52, 4.41]; // Flat

const toPoints = (yields) => logX.map((lx, i) => ({ x: lx, y: yields[i] }));

// Title length = 84 chars → fontSize = round(22 * 67 / 84) = 18px
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" }
  },
  credits: { enabled: false },
  colors: t.palette,

  title: {
    text: "U.S. Treasury Yield Curves · line-yield-curve · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "18px", fontWeight: "600" }
  },

  xAxis: {
    tickPositions: logX,
    labels: {
      formatter: function () {
        // Map log-transformed tick back to maturity label
        const idx = logX.reduce(
          (best, v, i) => Math.abs(v - this.value) < Math.abs(logX[best] - this.value) ? i : best,
          0
        );
        return matLabels[idx];
      },
      style: { color: t.inkSoft, fontSize: "13px" }
    },
    title: {
      text: "Maturity",
      style: { color: t.inkSoft, fontSize: "16px" }
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: "transparent",
    plotBands: [
      {
        // Shade the short-to-medium term zone where Nov 2022 was deeply inverted
        from: logX[0],
        to: logX[4],  // 1M to 2Y
        color: theme === "light" ? "rgba(174,48,48,0.07)" : "rgba(174,48,48,0.15)",
        label: {
          text: "Inversion zone",
          style: { color: t.inkSoft, fontSize: "11px", fontStyle: "italic" },
          align: "center",
          verticalAlign: "top",
          y: 18
        }
      }
    ]
  },

  yAxis: {
    title: {
      text: "Yield (%)",
      style: { color: t.inkSoft, fontSize: "16px" }
    },
    labels: {
      formatter: function () { return this.value.toFixed(1) + "%"; },
      style: { color: t.inkSoft, fontSize: "14px" }
    },
    gridLineColor: t.grid,
    min: 0
  },

  legend: {
    enabled: true,
    layout: "horizontal",
    align: "right",
    verticalAlign: "top",
    itemStyle: { color: t.inkSoft, fontSize: "14px", fontWeight: "normal" },
    itemHoverStyle: { color: t.ink },
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    borderRadius: 4,
    borderWidth: 1
  },

  plotOptions: {
    series: {
      animation: false,
      lineWidth: 2.5,
      marker: {
        enabled: true,
        radius: 5,
        symbol: "circle",
        lineWidth: 1,
        lineColor: "transparent"
      }
    }
  },

  series: [
    { name: "Jan 2021 — Normal",   data: toPoints(jan2021) },
    { name: "Nov 2022 — Inverted", data: toPoints(nov2022) },
    { name: "Jun 2024 — Flat",     data: toPoints(jun2024) }
  ],

  tooltip: {
    formatter: function () {
      const idx = logX.reduce(
        (best, v, i) => Math.abs(v - this.x) < Math.abs(logX[best] - this.x) ? i : best, 0
      );
      return "<b>" + this.series.name + "</b><br/>" +
             "Maturity: " + matLabels[idx] + "<br/>" +
             "Yield: " + Highcharts.numberFormat(this.y, 2) + "%";
    }
  }
});
