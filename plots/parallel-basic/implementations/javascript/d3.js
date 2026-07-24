// anyplot.ai
// parallel-basic: Basic Parallel Coordinates Plot
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: pending | Created: 2026-07-24

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 150, right: 230, bottom: 60, left: 70 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Cloud compute instance specs by family — vCPU/memory/storage grow together
// within a family, while price and network throughput separate the families.
// Each axis is scaled to its own min/max (not a shared scale), which is the
// standard normalization for parallel coordinates: every dimension has its
// own units, so a fixed 0-1 range per axis is what makes them comparable.
const dimensions = [
  { key: "vcpu", label: "vCPUs", format: d3.format("d") },
  { key: "memory", label: "Memory (GB)", format: d3.format(",d") },
  { key: "storage", label: "Storage (GB)", format: d3.format(",d") },
  { key: "price", label: "Price ($/hr)", format: (d) => `$${d3.format(".2f")(d)}` },
  { key: "network", label: "Network (Gbps)", format: d3.format(",d") },
];

const data = [
  // General Purpose
  { category: "General Purpose", vcpu: 2, memory: 8, storage: 80, price: 0.08, network: 5 },
  { category: "General Purpose", vcpu: 4, memory: 16, storage: 160, price: 0.16, network: 10 },
  { category: "General Purpose", vcpu: 8, memory: 32, storage: 320, price: 0.32, network: 10 },
  { category: "General Purpose", vcpu: 16, memory: 64, storage: 640, price: 0.64, network: 15 },
  { category: "General Purpose", vcpu: 32, memory: 128, storage: 1280, price: 1.28, network: 20 },
  { category: "General Purpose", vcpu: 48, memory: 192, storage: 1920, price: 1.92, network: 25 },
  // Compute Optimized
  { category: "Compute Optimized", vcpu: 4, memory: 8, storage: 50, price: 0.14, network: 10 },
  { category: "Compute Optimized", vcpu: 8, memory: 16, storage: 100, price: 0.28, network: 15 },
  { category: "Compute Optimized", vcpu: 16, memory: 32, storage: 200, price: 0.56, network: 20 },
  { category: "Compute Optimized", vcpu: 32, memory: 64, storage: 400, price: 1.12, network: 25 },
  { category: "Compute Optimized", vcpu: 48, memory: 96, storage: 600, price: 1.68, network: 30 },
  { category: "Compute Optimized", vcpu: 64, memory: 128, storage: 800, price: 2.24, network: 40 },
  // Memory Optimized
  { category: "Memory Optimized", vcpu: 2, memory: 16, storage: 100, price: 0.13, network: 10 },
  { category: "Memory Optimized", vcpu: 4, memory: 32, storage: 200, price: 0.26, network: 10 },
  { category: "Memory Optimized", vcpu: 8, memory: 64, storage: 400, price: 0.52, network: 15 },
  { category: "Memory Optimized", vcpu: 16, memory: 128, storage: 800, price: 1.04, network: 20 },
  { category: "Memory Optimized", vcpu: 32, memory: 256, storage: 1600, price: 2.08, network: 25 },
  { category: "Memory Optimized", vcpu: 48, memory: 384, storage: 2400, price: 3.12, network: 30 },
  // GPU Accelerated
  { category: "GPU Accelerated", vcpu: 8, memory: 32, storage: 200, price: 0.9, network: 25 },
  { category: "GPU Accelerated", vcpu: 16, memory: 64, storage: 400, price: 1.8, network: 50 },
  { category: "GPU Accelerated", vcpu: 32, memory: 128, storage: 800, price: 3.6, network: 100 },
  { category: "GPU Accelerated", vcpu: 64, memory: 256, storage: 1600, price: 7.2, network: 100 },
  { category: "GPU Accelerated", vcpu: 96, memory: 384, storage: 2400, price: 10.8, network: 200 },
  { category: "GPU Accelerated", vcpu: 128, memory: 512, storage: 3200, price: 14.4, network: 200 },
];

const categories = ["General Purpose", "Compute Optimized", "Memory Optimized", "GPU Accelerated"];

// SVG mount
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Scales — one shared x position per dimension, one independent y scale per dimension
const xScale = d3.scalePoint().domain(dimensions.map((d) => d.key)).range([0, iw]);
const yScales = Object.fromEntries(
  dimensions.map((d) => [
    d.key,
    d3.scaleLinear().domain(d3.extent(data, (row) => row[d.key])).nice().range([ih, 0]),
  ]),
);
const colorScale = d3.scaleOrdinal().domain(categories).range(t.palette.slice(0, categories.length));

// Data lines — one path per observation, transparent enough to read overlaps
const lineGen = d3.line();
g.selectAll(".instance-line")
  .data(data)
  .join("path")
  .attr("class", "instance-line")
  .attr("d", (row) => lineGen(dimensions.map((d) => [xScale(d.key), yScales[d.key](row[d.key])])))
  .attr("fill", "none")
  .attr("stroke", (row) => colorScale(row.category))
  .attr("stroke-width", 2.25)
  .attr("stroke-opacity", 0.62);

// Axes — one vertical d3.axisLeft per dimension, plus the dimension label above it
dimensions.forEach((dim) => {
  const axisG = g.append("g")
    .attr("transform", `translate(${xScale(dim.key)},0)`)
    .call(d3.axisLeft(yScales[dim.key]).ticks(5).tickFormat(dim.format));
  axisG.selectAll("text").attr("fill", t.inkSoft).style("font-size", "13px");
  axisG.selectAll("line").attr("stroke", t.grid);
  axisG.select(".domain").attr("stroke", t.inkSoft).attr("stroke-width", 1.5);

  g.append("text")
    .attr("x", xScale(dim.key)).attr("y", -22)
    .attr("text-anchor", "middle")
    .attr("fill", t.ink).style("font-size", "16px").style("font-weight", "600")
    .text(dim.label);
});

// Legend — instance family swatches in the right margin
const legend = svg.append("g").attr("transform", `translate(${margin.left + iw + 44},${margin.top + 12})`);
legend.append("text")
  .attr("fill", t.inkSoft).style("font-size", "13px").style("font-weight", "600")
  .text("Instance Family");
categories.forEach((cat, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${30 + i * 32})`);
  row.append("rect")
    .attr("width", 16).attr("height", 16).attr("rx", 3)
    .attr("fill", colorScale(cat));
  row.append("text")
    .attr("x", 24).attr("y", 13)
    .attr("fill", t.ink).style("font-size", "14px")
    .text(cat);
});

// Title
const title = "Cloud Instance Specs · parallel-basic · javascript · d3 · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(24 * 67 / title.length));
svg.append("text")
  .attr("x", width / 2).attr("y", 56)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);
