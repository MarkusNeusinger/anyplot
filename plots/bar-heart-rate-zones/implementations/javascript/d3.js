// anyplot.ai
// bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-14
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const THEME = window.ANYPLOT_THEME;

// Semantic zone colors — conventional fitness-zone hues mapped to Imprint palette
const muted = THEME === "light" ? "#6B6A63" : "#A8A79F";
const zoneColors = [
  muted,      // Z1 Recovery  — grey  (Imprint muted anchor)
  "#4467A3",  // Z2 Endurance — blue  (Imprint pos 3)
  "#009E73",  // Z3 Aerobic   — green (Imprint pos 1 / brand)
  "#BD8233",  // Z4 Threshold — ochre (Imprint pos 4)
  "#AE3030",  // Z5 Maximum   — matte red (Imprint pos 5)
];

// Data — 60-minute tempo run
const zones = [
  { id: "Z1", name: "Recovery",  minutes: 8,  hrRange: "< 50% max HR"  },
  { id: "Z2", name: "Endurance", minutes: 22, hrRange: "50–60% max HR" },
  { id: "Z3", name: "Aerobic",   minutes: 15, hrRange: "60–70% max HR" },
  { id: "Z4", name: "Threshold", minutes: 12, hrRange: "70–80% max HR" },
  { id: "Z5", name: "Maximum",   minutes: 3,  hrRange: "80%+ max HR"   },
];

const margin = { top: 90, right: 60, bottom: 130, left: 100 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// Scales
const x = d3.scaleBand()
  .domain(zones.map(d => d.id))
  .range([0, iw])
  .padding(0.32);

const y = d3.scaleLinear()
  .domain([0, 30])
  .range([ih, 0]);

// Horizontal gridlines (y-axis only)
g.append("g")
  .call(d3.axisLeft(y).tickValues([5, 10, 15, 20, 25, 30]).tickSize(-iw).tickFormat(""))
  .call(ag => ag.select(".domain").remove())
  .selectAll("line")
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// Y axis with labels
g.append("g")
  .call(
    d3.axisLeft(y)
      .tickValues([0, 5, 10, 15, 20, 25, 30])
      .tickFormat(d => d === 0 ? "" : `${d} min`)
  )
  .call(ag => {
    ag.select(".domain").attr("stroke", t.inkSoft);
    ag.selectAll(".tick text").attr("fill", t.inkSoft).style("font-size", "14px");
    ag.selectAll(".tick line").remove();
  });

// X axis baseline
g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).tickSize(0).tickFormat(""))
  .call(ag => ag.select(".domain").attr("stroke", t.inkSoft));

// Bars
g.selectAll(".bar")
  .data(zones)
  .join("rect")
  .attr("x", d => x(d.id))
  .attr("y", d => y(d.minutes))
  .attr("width", x.bandwidth())
  .attr("height", d => ih - y(d.minutes))
  .attr("fill", (d, i) => zoneColors[i])
  .attr("rx", 4);

// Duration labels above each bar
g.selectAll(".dur-label")
  .data(zones)
  .join("text")
  .attr("x", d => x(d.id) + x.bandwidth() / 2)
  .attr("y", d => y(d.minutes) - 12)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .style("font-weight", "700")
  .text(d => {
    const m = Math.floor(d.minutes);
    const s = Math.round((d.minutes - m) * 60);
    return `${m}:${String(s).padStart(2, "0")}`;
  });

// X-axis zone label groups: ID + name + HR range
const xLabels = g.selectAll(".zone-label")
  .data(zones)
  .join("g")
  .attr("transform", d => `translate(${x(d.id) + x.bandwidth() / 2},${ih})`);

xLabels.append("text")
  .attr("y", 30)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "17px")
  .style("font-weight", "700")
  .text(d => d.id);

xLabels.append("text")
  .attr("y", 54)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text(d => d.name);

xLabels.append("text")
  .attr("y", 76)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "12px")
  .text(d => d.hrRange);

// Y-axis label (rotated)
g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -(ih / 2))
  .attr("y", -72)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Time (minutes)");

// Title
const titleText = "60-min Tempo Run · bar-heart-rate-zones · javascript · d3 · anyplot.ai";
const titleSize = Math.max(16, Math.round(22 * Math.min(1, 67 / titleText.length)));

svg.append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleSize}px`)
  .style("font-weight", "600")
  .text(titleText);
