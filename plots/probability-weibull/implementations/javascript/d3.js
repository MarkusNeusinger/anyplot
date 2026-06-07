// anyplot.ai
// probability-weibull: Weibull Probability Plot for Reliability Analysis
// Library: d3 7.9.0 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-07

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 80, right: 100, bottom: 120, left: 130 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Turbine blade fatigue-life data: 17 failures + 3 right-censored suspensions
// Times approximate Weibull(β≈2, η≈4000 h) — sorted by time
const rawData = [
  { time: 750,  failed: true  },
  { time: 1180, failed: true  },
  { time: 1500, failed: true  },
  { time: 1790, failed: true  },
  { time: 1850, failed: false },
  { time: 2050, failed: true  },
  { time: 2290, failed: true  },
  { time: 2520, failed: true  },
  { time: 2750, failed: true  },
  { time: 2980, failed: true  },
  { time: 3100, failed: false },
  { time: 3210, failed: true  },
  { time: 3450, failed: true  },
  { time: 3690, failed: true  },
  { time: 3750, failed: false },
  { time: 3950, failed: true  },
  { time: 4220, failed: true  },
  { time: 4520, failed: true  },
  { time: 4850, failed: true  },
  { time: 5230, failed: true  },
];

const n = rawData.length; // 20 total observations
const weibullY = (F) => Math.log(-Math.log(1 - F));

// Bernard's median rank: (i − 0.3) / (n + 0.4)
let failRank = 0;
const plotData = rawData.map((d) => {
  if (d.failed) {
    failRank++;
    const F = (failRank - 0.3) / (n + 0.4);
    return { time: d.time, failed: true, F, yw: weibullY(F) };
  }
  return { time: d.time, failed: false, F: null, yw: null };
});

const failures = plotData.filter((d) => d.failed);
const censored = plotData.filter((d) => !d.failed);

// OLS regression in Weibull coordinates: yw = β·ln(t) + b
const lnT  = (d) => Math.log(d.time);
const nF   = failures.length;
const sx   = d3.sum(failures, lnT);
const sy   = d3.sum(failures, (d) => d.yw);
const sxy  = d3.sum(failures, (d) => lnT(d) * d.yw);
const sxx  = d3.sum(failures, (d) => lnT(d) * lnT(d));
const beta       = (nF * sxy - sx * sy) / (nF * sxx - sx * sx);
const bIntercept = (sy - beta * sx) / nF;
const eta        = Math.round(Math.exp(-bIntercept / beta));

// Probability axis: map F → ln(−ln(1−F))
const probTicks = [0.01, 0.05, 0.1, 0.2, 0.5, 0.632, 0.9, 0.99];
const yMin = weibullY(0.01);  // ≈ −4.60
const yMax = weibullY(0.99);  // ≈  1.53

// SVG
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

// Clip path — keeps fitted line and points within axes
svg.append("defs").append("clipPath").attr("id", "plot-clip")
  .append("rect").attr("width", iw).attr("height", ih);

const g    = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
const plotG = g.append("g").attr("clip-path", "url(#plot-clip)");

// Scales
const x = d3.scaleLog().domain([400, 8000]).range([0, iw]);
const y = d3.scaleLinear().domain([yMin, yMax]).range([ih, 0]);

// Horizontal grid at each probability tick
probTicks.forEach((F) => {
  plotG.append("line")
    .attr("x1", 0).attr("x2", iw)
    .attr("y1", y(weibullY(F))).attr("y2", y(weibullY(F)))
    .attr("stroke", t.grid).attr("stroke-width", 1);
});
// Vertical grid at log-decade ticks
[500, 1000, 2000, 4000, 8000].forEach((v) => {
  plotG.append("line")
    .attr("x1", x(v)).attr("x2", x(v))
    .attr("y1", 0).attr("y2", ih)
    .attr("stroke", t.grid).attr("stroke-width", 1);
});

// Reference line at 63.2% characteristic life (amber dashed)
const y632 = y(weibullY(0.632));
plotG.append("line")
  .attr("x1", 0).attr("x2", iw)
  .attr("y1", y632).attr("y2", y632)
  .attr("stroke", t.amber).attr("stroke-width", 2)
  .attr("stroke-dasharray", "8 4");

// Vertical eta marker (characteristic life read-off line)
if (eta >= 400 && eta <= 8000) {
  plotG.append("line")
    .attr("x1", x(eta)).attr("x2", x(eta))
    .attr("y1", y632).attr("y2", ih)
    .attr("stroke", t.amber).attr("stroke-width", 1.5)
    .attr("stroke-dasharray", "5 3");
}

// Fitted Weibull straight line
plotG.append("line")
  .attr("x1", x(400)).attr("x2", x(8000))
  .attr("y1", y(beta * Math.log(400) + bIntercept))
  .attr("y2", y(beta * Math.log(8000) + bIntercept))
  .attr("stroke", t.palette[2])
  .attr("stroke-width", 2.5);

// Failure points — filled green circles
plotG.selectAll(".fail")
  .data(failures).join("circle").attr("class", "fail")
  .attr("cx", (d) => x(d.time))
  .attr("cy", (d) => y(d.yw))
  .attr("r", 7)
  .attr("fill", t.palette[0])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// Y-axis spine + custom Weibull probability ticks
g.append("line").attr("x1", 0).attr("x2", 0).attr("y1", 0).attr("y2", ih)
  .attr("stroke", t.inkSoft).attr("stroke-width", 1.5);
probTicks.forEach((F) => {
  const yp = y(weibullY(F));
  const label = F === 0.632 ? "63.2%" : `${Math.round(F * 100)}%`;
  g.append("line").attr("x1", -6).attr("x2", 0)
    .attr("y1", yp).attr("y2", yp).attr("stroke", t.inkSoft).attr("stroke-width", 1);
  g.append("text").attr("x", -10).attr("y", yp)
    .attr("text-anchor", "end").attr("dominant-baseline", "middle")
    .attr("fill", t.inkSoft).style("font-size", "14px").text(label);
});

// X-axis spine + log ticks
g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", ih).attr("y2", ih)
  .attr("stroke", t.inkSoft).attr("stroke-width", 1.5);
[500, 1000, 2000, 4000, 8000].forEach((v) => {
  const xp = x(v);
  g.append("line").attr("x1", xp).attr("x2", xp).attr("y1", ih).attr("y2", ih + 6)
    .attr("stroke", t.inkSoft).attr("stroke-width", 1);
  g.append("text").attr("x", xp).attr("y", ih + 12)
    .attr("text-anchor", "middle").attr("dominant-baseline", "hanging")
    .attr("fill", t.inkSoft).style("font-size", "14px")
    .text(v >= 1000 ? `${v / 1000}k` : `${v}`);
});

// Censored suspensions: hollow + crosshair markers below x-axis
censored.forEach((d) => {
  const cx = x(d.time);
  const cy = ih + 38;
  g.append("circle").attr("cx", cx).attr("cy", cy).attr("r", 7)
    .attr("fill", "none").attr("stroke", t.inkSoft).attr("stroke-width", 2);
  g.append("line").attr("x1", cx - 4).attr("x2", cx + 4)
    .attr("y1", cy).attr("y2", cy).attr("stroke", t.inkSoft).attr("stroke-width", 1.5);
  g.append("line").attr("x1", cx).attr("x2", cx)
    .attr("y1", cy - 4).attr("y2", cy + 4).attr("stroke", t.inkSoft).attr("stroke-width", 1.5);
});

// 63.2% annotation on amber line
g.append("text").attr("x", iw - 8).attr("y", y632 - 9)
  .attr("text-anchor", "end").attr("fill", t.amber).style("font-size", "13px")
  .text("63.2% — Characteristic Life");

// Eta annotation on vertical amber line
if (eta >= 400 && eta <= 8000) {
  g.append("text").attr("x", x(eta) + 8).attr("y", ih - 18)
    .attr("fill", t.amber).style("font-size", "13px")
    .text(`η = ${eta.toLocaleString()} h`);
}

// Parameter box (top-left)
const pX = 16, pY = 16;
g.append("rect").attr("x", pX).attr("y", pY).attr("width", 188).attr("height", 68)
  .attr("fill", t.elevatedBg).attr("rx", 4).attr("stroke", t.grid).attr("stroke-width", 1);
g.append("text").attr("x", pX + 12).attr("y", pY + 24)
  .attr("fill", t.ink).style("font-size", "15px").style("font-weight", "600")
  .text(`β = ${beta.toFixed(2)}  (shape)`);
g.append("text").attr("x", pX + 12).attr("y", pY + 50)
  .attr("fill", t.ink).style("font-size", "15px").style("font-weight", "600")
  .text(`η = ${eta.toLocaleString()} h  (scale)`);

// Legend (top-right)
const lx = iw - 158, ly = 16;
g.append("rect").attr("x", lx).attr("y", ly).attr("width", 155).attr("height", 95)
  .attr("fill", t.elevatedBg).attr("rx", 4).attr("stroke", t.grid).attr("stroke-width", 1);
// Failure
g.append("circle").attr("cx", lx + 16).attr("cy", ly + 20).attr("r", 6)
  .attr("fill", t.palette[0]).attr("stroke", t.pageBg).attr("stroke-width", 1.5);
g.append("text").attr("x", lx + 30).attr("y", ly + 20)
  .attr("dominant-baseline", "middle").attr("fill", t.ink).style("font-size", "14px")
  .text("Failure");
// Suspended
g.append("circle").attr("cx", lx + 16).attr("cy", ly + 47).attr("r", 6)
  .attr("fill", "none").attr("stroke", t.inkSoft).attr("stroke-width", 2);
g.append("line").attr("x1", lx + 12).attr("x2", lx + 20).attr("y1", ly + 47).attr("y2", ly + 47)
  .attr("stroke", t.inkSoft).attr("stroke-width", 1.5);
g.append("line").attr("x1", lx + 16).attr("x2", lx + 16).attr("y1", ly + 43).attr("y2", ly + 51)
  .attr("stroke", t.inkSoft).attr("stroke-width", 1.5);
g.append("text").attr("x", lx + 30).attr("y", ly + 47)
  .attr("dominant-baseline", "middle").attr("fill", t.ink).style("font-size", "14px")
  .text("Suspended");
// Weibull fit line
g.append("line").attr("x1", lx + 8).attr("x2", lx + 24).attr("y1", ly + 74).attr("y2", ly + 74)
  .attr("stroke", t.palette[2]).attr("stroke-width", 2.5);
g.append("text").attr("x", lx + 30).attr("y", ly + 74)
  .attr("dominant-baseline", "middle").attr("fill", t.ink).style("font-size", "14px")
  .text("Weibull fit");

// Axis labels
g.append("text").attr("x", iw / 2).attr("y", ih + 80)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "16px").style("font-weight", "500")
  .text("Time to Failure (hours)");

svg.append("text")
  .attr("transform", `translate(32,${margin.top + ih / 2}) rotate(-90)`)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "16px").style("font-weight", "500")
  .text("Cumulative Failure Probability F(t)");

// Title
svg.append("text").attr("x", width / 2).attr("y", 48)
  .attr("text-anchor", "middle").attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .text("probability-weibull · javascript · d3 · anyplot.ai");
