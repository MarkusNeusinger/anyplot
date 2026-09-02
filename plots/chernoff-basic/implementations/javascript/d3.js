// anyplot.ai
// chernoff-basic: Chernoff Faces for Multivariate Data
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data: 12 companies x 8 financial/operational metrics, 3 industries ----
// Each metric is later normalized to [0, 1] (via d3.extent) before being
// mapped onto a facial feature's pixel range, per the spec's 0-1 rule.
const companies = [
  { name: "Nova Robotics", industry: "Tech", revenueGrowth: 24, profitMargin: 15, liquidityRatio: 2.1, rdInvestment: 19, debtRatio: 0.28, marketShare: 9, customerSat: 86, opEfficiency: 78 },
  { name: "PixelForge Software", industry: "Tech", revenueGrowth: 31, profitMargin: 8, liquidityRatio: 1.6, rdInvestment: 22, debtRatio: 0.35, marketShare: 6, customerSat: 79, opEfficiency: 71 },
  { name: "CloudSpring Systems", industry: "Tech", revenueGrowth: 12, profitMargin: 22, liquidityRatio: 2.8, rdInvestment: 14, debtRatio: 0.18, marketShare: 13, customerSat: 91, opEfficiency: 88 },
  { name: "ByteHarbor Data", industry: "Tech", revenueGrowth: 6, profitMargin: 5, liquidityRatio: 1.1, rdInvestment: 9, debtRatio: 0.52, marketShare: 4, customerSat: 63, opEfficiency: 58 },
  { name: "Trailhead Retail", industry: "Retail", revenueGrowth: 9, profitMargin: 6, liquidityRatio: 1.4, rdInvestment: 3, debtRatio: 0.41, marketShare: 11, customerSat: 74, opEfficiency: 69 },
  { name: "UrbanCart", industry: "Retail", revenueGrowth: 15, profitMargin: 9, liquidityRatio: 1.7, rdInvestment: 4, debtRatio: 0.33, marketShare: 15, customerSat: 81, opEfficiency: 75 },
  { name: "Meadow Market", industry: "Retail", revenueGrowth: 3, profitMargin: 4, liquidityRatio: 0.9, rdInvestment: 2, debtRatio: 0.61, marketShare: 7, customerSat: 58, opEfficiency: 52 },
  { name: "Northwind Goods", industry: "Retail", revenueGrowth: 11, profitMargin: 12, liquidityRatio: 2.0, rdInvestment: 5, debtRatio: 0.24, marketShare: 19, customerSat: 84, opEfficiency: 80 },
  { name: "Ironclad Manufacturing", industry: "Manufacturing", revenueGrowth: 7, profitMargin: 14, liquidityRatio: 1.9, rdInvestment: 8, debtRatio: 0.3, marketShare: 22, customerSat: 77, opEfficiency: 83 },
  { name: "Summit Steel Works", industry: "Manufacturing", revenueGrowth: 4, profitMargin: 10, liquidityRatio: 1.5, rdInvestment: 6, debtRatio: 0.44, marketShare: 17, customerSat: 70, opEfficiency: 76 },
  { name: "Cascade Motors", industry: "Manufacturing", revenueGrowth: 13, profitMargin: 17, liquidityRatio: 2.3, rdInvestment: 11, debtRatio: 0.2, marketShare: 24, customerSat: 89, opEfficiency: 85 },
  { name: "Anchor Industries", industry: "Manufacturing", revenueGrowth: 1, profitMargin: 2, liquidityRatio: 0.8, rdInvestment: 3, debtRatio: 0.58, marketShare: 10, customerSat: 55, opEfficiency: 48 },
];

const industries = ["Tech", "Retail", "Manufacturing"];
const industryColor = d3.scaleOrdinal().domain(industries).range(t.palette.slice(0, 3));

// --- Feature scales: metric extent -> facial-feature pixel range ------------
const faceWidthScale = d3.scaleLinear().domain(d3.extent(companies, (d) => d.revenueGrowth)).range([55, 85]);
const faceHeightScale = d3.scaleLinear().domain(d3.extent(companies, (d) => d.profitMargin)).range([65, 95]);
const eyeSizeScale = d3.scaleLinear().domain(d3.extent(companies, (d) => d.liquidityRatio)).range([5, 11]);
const eyeSpacingScale = d3.scaleLinear().domain(d3.extent(companies, (d) => d.rdInvestment)).range([16, 30]);
const browSlantScale = d3.scaleLinear().domain(d3.extent(companies, (d) => d.debtRatio)).range([-8, 24]);
const noseLengthScale = d3.scaleLinear().domain(d3.extent(companies, (d) => d.marketShare)).range([10, 24]);
const mouthCurveScale = d3.scaleLinear().domain(d3.extent(companies, (d) => d.customerSat)).range([-10, 22]);
const mouthWidthScale = d3.scaleLinear().domain(d3.extent(companies, (d) => d.opEfficiency)).range([20, 40]);

// --- Grid layout --------------------------------------------------------------
const margin = { top: 130, right: 40, bottom: 20, left: 40 };
const cols = 4;
const rows = 3;
const cellW = (width - margin.left - margin.right) / cols;
const cellH = (height - margin.top - margin.bottom) / rows;

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Title ----------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("chernoff-basic · javascript · d3 · anyplot.ai");

// --- Industry legend --------------------------------------------------------
const legendItemW = 190;
const legend = svg
  .append("g")
  .attr("transform", `translate(${width / 2 - ((industries.length - 1) * legendItemW) / 2}, 92)`);

const legendItems = legend
  .selectAll("g.legend-item")
  .data(industries)
  .join("g")
  .attr("class", "legend-item")
  .attr("transform", (d, i) => `translate(${i * legendItemW}, 0)`);

legendItems.append("circle").attr("r", 7).attr("fill", (d) => industryColor(d));
legendItems
  .append("text")
  .attr("x", 16)
  .attr("y", 5)
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text((d) => d);

// --- Faces: one <g> per company, positioned by grid index -------------------
const faceG = svg
  .selectAll("g.face")
  .data(companies)
  .join("g")
  .attr("class", "face")
  .attr("transform", (d, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const cx = margin.left + col * cellW + cellW / 2;
    const cy = margin.top + row * cellH + cellH * 0.4;
    return `translate(${cx},${cy})`;
  });

faceG.each(function (d) {
  const g = d3.select(this);
  const color = industryColor(d.industry);

  const faceW = faceWidthScale(d.revenueGrowth);
  const faceH = faceHeightScale(d.profitMargin);
  const eyeSize = eyeSizeScale(d.liquidityRatio);
  const eyeSpacing = eyeSpacingScale(d.rdInvestment);
  const browSlant = browSlantScale(d.debtRatio);
  const noseLen = noseLengthScale(d.marketShare);
  const mouthCurve = mouthCurveScale(d.customerSat);
  const mouthWidth = mouthWidthScale(d.opEfficiency);

  const eyeY = -faceH * 0.12;
  const noseTopY = -faceH * 0.05;
  const mouthY = faceH * 0.42;

  // face outline — industry color carries the group encoding
  g.append("ellipse")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("rx", faceW)
    .attr("ry", faceH)
    .attr("fill", t.elevatedBg)
    .attr("stroke", color)
    .attr("stroke-width", 3.5);

  // eyes: white + pupil, mirrored around center
  for (const side of [-1, 1]) {
    const ex = side * eyeSpacing;
    g.append("ellipse").attr("cx", ex).attr("cy", eyeY).attr("rx", eyeSize).attr("ry", eyeSize * 0.8).attr("fill", t.pageBg).attr("stroke", t.ink).attr("stroke-width", 1.5);
    g.append("circle").attr("cx", ex).attr("cy", eyeY).attr("r", eyeSize * 0.4).attr("fill", t.ink);

    // eyebrow, rotated by debt-driven slant (mirrored across the two sides)
    const browY = eyeY - eyeSize - 10;
    g.append("line")
      .attr("x1", ex - 13)
      .attr("x2", ex + 13)
      .attr("y1", browY)
      .attr("y2", browY)
      .attr("stroke", t.ink)
      .attr("stroke-width", 3)
      .attr("stroke-linecap", "round")
      .attr("transform", `rotate(${side * browSlant} ${ex} ${browY})`);
  }

  // nose
  g.append("path")
    .attr("d", `M0,${noseTopY} L0,${noseTopY + noseLen} L5,${noseTopY + noseLen}`)
    .attr("fill", "none")
    .attr("stroke", t.ink)
    .attr("stroke-width", 2.5)
    .attr("stroke-linecap", "round");

  // mouth: quadratic curve, control point below/above the corners for smile/frown
  g.append("path")
    .attr("d", `M${-mouthWidth / 2},${mouthY} Q0,${mouthY + mouthCurve} ${mouthWidth / 2},${mouthY}`)
    .attr("fill", "none")
    .attr("stroke", t.ink)
    .attr("stroke-width", 3)
    .attr("stroke-linecap", "round");

  // company label
  g.append("text")
    .attr("x", 0)
    .attr("y", cellH * 0.46)
    .attr("text-anchor", "middle")
    .attr("fill", t.inkSoft)
    .style("font-size", "14px")
    .text(d.name);
});
