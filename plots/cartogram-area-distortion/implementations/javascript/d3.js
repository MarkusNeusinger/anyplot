// anyplot.ai
// cartogram-area-distortion: Cartogram with Area Distortion by Data Value
// Library: d3 7.9.0 | JavaScript 22.23.4
// Quality: 82/100 | Updated: 2026-11-08

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 130, right: 250, bottom: 50, left: 30 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// Columns: set these to your data's column names
const REGION = "State";  // role: region
const LABEL = "Abbreviation";  // role: label
const LON = "Longitude";  // role: x (centroid)
const LAT = "Latitude";  // role: y (centroid)
const VALUE = "Population (millions)";  // role: value (area)
const SECONDARY = "GDP per capita (USD)";  // role: color

// Data: replace this block with your own records, one object per row
// US states + D.C.: centroid, population 2023, GDP per capita 2022
const data = [
  { [REGION]: "Alabama",        [LABEL]: "AL", [LON]: -86.7,  [LAT]: 32.8, [VALUE]: 5.1,  [SECONDARY]: 53100  },
  { [REGION]: "Alaska",         [LABEL]: "AK", [LON]: -153.0, [LAT]: 64.2, [VALUE]: 0.74, [SECONDARY]: 82400  },
  { [REGION]: "Arizona",        [LABEL]: "AZ", [LON]: -111.7, [LAT]: 34.3, [VALUE]: 7.4,  [SECONDARY]: 65900  },
  { [REGION]: "Arkansas",       [LABEL]: "AR", [LON]: -92.4,  [LAT]: 34.9, [VALUE]: 3.1,  [SECONDARY]: 50000  },
  { [REGION]: "California",     [LABEL]: "CA", [LON]: -119.7, [LAT]: 37.2, [VALUE]: 39.0, [SECONDARY]: 99700  },
  { [REGION]: "Colorado",       [LABEL]: "CO", [LON]: -105.5, [LAT]: 39.0, [VALUE]: 5.9,  [SECONDARY]: 84400  },
  { [REGION]: "Connecticut",    [LABEL]: "CT", [LON]: -72.7,  [LAT]: 41.6, [VALUE]: 3.6,  [SECONDARY]: 91900  },
  { [REGION]: "Delaware",       [LABEL]: "DE", [LON]: -75.5,  [LAT]: 39.0, [VALUE]: 1.0,  [SECONDARY]: 91000  },
  { [REGION]: "Florida",        [LABEL]: "FL", [LON]: -81.5,  [LAT]: 27.8, [VALUE]: 22.6, [SECONDARY]: 64600  },
  { [REGION]: "Georgia",        [LABEL]: "GA", [LON]: -83.4,  [LAT]: 32.7, [VALUE]: 11.0, [SECONDARY]: 67500  },
  { [REGION]: "Hawaii",         [LABEL]: "HI", [LON]: -157.5, [LAT]: 20.3, [VALUE]: 1.44, [SECONDARY]: 66700  },
  { [REGION]: "Idaho",          [LABEL]: "ID", [LON]: -114.5, [LAT]: 44.4, [VALUE]: 2.0,  [SECONDARY]: 55000  },
  { [REGION]: "Illinois",       [LABEL]: "IL", [LON]: -89.2,  [LAT]: 40.1, [VALUE]: 12.6, [SECONDARY]: 81200  },
  { [REGION]: "Indiana",        [LABEL]: "IN", [LON]: -86.3,  [LAT]: 40.0, [VALUE]: 6.9,  [SECONDARY]: 62600  },
  { [REGION]: "Iowa",           [LABEL]: "IA", [LON]: -93.5,  [LAT]: 42.1, [VALUE]: 3.2,  [SECONDARY]: 71600  },
  { [REGION]: "Kansas",         [LABEL]: "KS", [LON]: -98.4,  [LAT]: 38.5, [VALUE]: 2.9,  [SECONDARY]: 71400  },
  { [REGION]: "Kentucky",       [LABEL]: "KY", [LON]: -84.3,  [LAT]: 37.5, [VALUE]: 4.5,  [SECONDARY]: 58400  },
  { [REGION]: "Louisiana",      [LABEL]: "LA", [LON]: -91.8,  [LAT]: 31.2, [VALUE]: 4.6,  [SECONDARY]: 60700  },
  { [REGION]: "Maine",          [LABEL]: "ME", [LON]: -69.2,  [LAT]: 45.4, [VALUE]: 1.4,  [SECONDARY]: 56400  },
  { [REGION]: "Maryland",       [LABEL]: "MD", [LON]: -76.8,  [LAT]: 39.1, [VALUE]: 6.2,  [SECONDARY]: 82400  },
  { [REGION]: "Massachusetts",  [LABEL]: "MA", [LON]: -71.8,  [LAT]: 42.3, [VALUE]: 7.1,  [SECONDARY]: 99900  },
  { [REGION]: "Michigan",       [LABEL]: "MI", [LON]: -84.5,  [LAT]: 44.3, [VALUE]: 10.0, [SECONDARY]: 63400  },
  { [REGION]: "Minnesota",      [LABEL]: "MN", [LON]: -94.3,  [LAT]: 46.4, [VALUE]: 5.7,  [SECONDARY]: 87900  },
  { [REGION]: "Mississippi",    [LABEL]: "MS", [LON]: -89.7,  [LAT]: 32.7, [VALUE]: 3.0,  [SECONDARY]: 46300  },
  { [REGION]: "Missouri",       [LABEL]: "MO", [LON]: -92.6,  [LAT]: 38.4, [VALUE]: 6.2,  [SECONDARY]: 63700  },
  { [REGION]: "Montana",        [LABEL]: "MT", [LON]: -109.6, [LAT]: 47.0, [VALUE]: 1.1,  [SECONDARY]: 61800  },
  { [REGION]: "Nebraska",       [LABEL]: "NE", [LON]: -99.9,  [LAT]: 41.5, [VALUE]: 2.0,  [SECONDARY]: 81500  },
  { [REGION]: "Nevada",         [LABEL]: "NV", [LON]: -116.7, [LAT]: 39.5, [VALUE]: 3.2,  [SECONDARY]: 76300  },
  { [REGION]: "New Hampshire",  [LABEL]: "NH", [LON]: -71.6,  [LAT]: 43.7, [VALUE]: 1.4,  [SECONDARY]: 77900  },
  { [REGION]: "New Jersey",     [LABEL]: "NJ", [LON]: -74.5,  [LAT]: 40.1, [VALUE]: 9.3,  [SECONDARY]: 80400  },
  { [REGION]: "New Mexico",     [LABEL]: "NM", [LON]: -106.1, [LAT]: 34.5, [VALUE]: 2.1,  [SECONDARY]: 62400  },
  { [REGION]: "New York",       [LABEL]: "NY", [LON]: -75.5,  [LAT]: 42.9, [VALUE]: 19.8, [SECONDARY]: 103700 },
  { [REGION]: "North Carolina", [LABEL]: "NC", [LON]: -79.4,  [LAT]: 35.6, [VALUE]: 10.7, [SECONDARY]: 66700  },
  { [REGION]: "North Dakota",   [LABEL]: "ND", [LON]: -100.5, [LAT]: 47.5, [VALUE]: 0.78, [SECONDARY]: 91000  },
  { [REGION]: "Ohio",           [LABEL]: "OH", [LON]: -82.8,  [LAT]: 40.4, [VALUE]: 11.8, [SECONDARY]: 71000  },
  { [REGION]: "Oklahoma",       [LABEL]: "OK", [LON]: -97.5,  [LAT]: 35.5, [VALUE]: 4.0,  [SECONDARY]: 59800  },
  { [REGION]: "Oregon",         [LABEL]: "OR", [LON]: -120.5, [LAT]: 43.9, [VALUE]: 4.3,  [SECONDARY]: 80700  },
  { [REGION]: "Pennsylvania",   [LABEL]: "PA", [LON]: -77.2,  [LAT]: 40.6, [VALUE]: 13.1, [SECONDARY]: 69700  },
  { [REGION]: "Rhode Island",   [LABEL]: "RI", [LON]: -71.5,  [LAT]: 41.7, [VALUE]: 1.1,  [SECONDARY]: 71800  },
  { [REGION]: "South Carolina", [LABEL]: "SC", [LON]: -80.9,  [LAT]: 33.8, [VALUE]: 5.3,  [SECONDARY]: 53000  },
  { [REGION]: "South Dakota",   [LABEL]: "SD", [LON]: -100.3, [LAT]: 44.4, [VALUE]: 0.91, [SECONDARY]: 78000  },
  { [REGION]: "Tennessee",      [LABEL]: "TN", [LON]: -86.3,  [LAT]: 35.9, [VALUE]: 7.1,  [SECONDARY]: 67700  },
  { [REGION]: "Texas",          [LABEL]: "TX", [LON]: -99.3,  [LAT]: 31.5, [VALUE]: 30.1, [SECONDARY]: 78200  },
  { [REGION]: "Utah",           [LABEL]: "UT", [LON]: -111.1, [LAT]: 39.3, [VALUE]: 3.4,  [SECONDARY]: 79400  },
  { [REGION]: "Vermont",        [LABEL]: "VT", [LON]: -72.7,  [LAT]: 44.0, [VALUE]: 0.65, [SECONDARY]: 61500  },
  { [REGION]: "Virginia",       [LABEL]: "VA", [LON]: -79.4,  [LAT]: 37.5, [VALUE]: 8.7,  [SECONDARY]: 80900  },
  { [REGION]: "Washington",     [LABEL]: "WA", [LON]: -120.5, [LAT]: 47.4, [VALUE]: 7.9,  [SECONDARY]: 99400  },
  { [REGION]: "West Virginia",  [LABEL]: "WV", [LON]: -80.6,  [LAT]: 38.6, [VALUE]: 1.8,  [SECONDARY]: 49400  },
  { [REGION]: "Wisconsin",      [LABEL]: "WI", [LON]: -90.0,  [LAT]: 44.6, [VALUE]: 5.9,  [SECONDARY]: 73400  },
  { [REGION]: "Wyoming",        [LABEL]: "WY", [LON]: -107.6, [LAT]: 43.0, [VALUE]: 0.58, [SECONDARY]: 79300  },
  { [REGION]: "D.C.",           [LABEL]: "DC", [LON]: -77.0,  [LAT]: 38.9, [VALUE]: 0.69, [SECONDARY]: 234800 },
];

// Plot: reads only data and the constants above
const regions = data.filter((d) => d[VALUE] != null);

// AlbersUSA composite projection places AK + HI in their conventional insets
const geoFeatures = {
  type: "FeatureCollection",
  features: regions.map((d) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [d[LON], d[LAT]] },
  })),
};

const projection = d3.geoAlbersUsa().fitExtent([[0, 12], [iw, ih]], geoFeatures);

const nodes = regions.map((d) => {
  const p = projection([d[LON], d[LAT]]) ?? [iw / 2, ih / 2];
  return { d, x: p[0], y: p[1], x0: p[0], y0: p[1] };
});

// Area ∝ value: radius on a square-root scale
const maxR = 70;
const rScale = d3.scaleSqrt().domain([0, d3.max(regions, (d) => d[VALUE])]).range([0, maxR]);

// Dorling layout: pull circles to their centroids, collide to remove overlaps
const sim = d3.forceSimulation(nodes)
  .force("attract-x", d3.forceX((n) => n.x0).strength(0.65))
  .force("attract-y", d3.forceY((n) => n.y0).strength(0.65))
  .force("collide", d3.forceCollide((n) => rScale(n.d[VALUE]) + 2).strength(1.0))
  .stop();
for (let i = 0; i < 350; i++) sim.tick();

// Color domain ends at the 95th percentile so a single outlier (D.C.) does not
// flatten the ramp for every other region; values above it clamp to the top stop
const secValues = regions.map((d) => d[SECONDARY]).filter((v) => v != null);
const secLo = d3.min(secValues);
const secHi = d3.quantile(secValues, 0.95);
const colorScale = d3.scaleSequential(d3.interpolateRgbBasis(t.seq))
  .domain([secLo, secHi])
  .clamp(true);
const fmtK = (v) => `$${Math.round(v / 1000)}k`;

const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// Larger circles first so smaller neighbours stay on top
const sorted = [...nodes].sort((a, b) => b.d[VALUE] - a.d[VALUE]);

g.selectAll("circle.region")
  .data(sorted)
  .join("circle")
  .attr("class", "region")
  .attr("cx", (n) => n.x)
  .attr("cy", (n) => n.y)
  .attr("r", (n) => rScale(n.d[VALUE]))
  .attr("fill", (n) => (n.d[SECONDARY] == null ? t.grid : colorScale(n.d[SECONDARY])))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// Two letters at 11 px need a radius of about 11 px; smaller circles stay unlabeled
const minLabelR = 11;
g.selectAll("text.abbr")
  .data(sorted.filter((n) => rScale(n.d[VALUE]) >= minLabelR))
  .join("text")
  .attr("class", "abbr")
  .attr("x", (n) => n.x)
  .attr("y", (n) => n.y)
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "central")
  .attr("fill", t.pageBg)
  .style("font-size", (n) => `${Math.max(11, Math.min(18, rScale(n.d[VALUE]) * 0.46))}px`)
  .style("font-weight", "700")
  .style("pointer-events", "none")
  .text((n) => n.d[LABEL]);

// Title
const titleStr = "US Population Cartogram · cartogram-area-distortion · javascript · d3 · anyplot.ai";
const titlePx = Math.round(22 * Math.min(1, 67 / titleStr.length));
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titlePx}px`)
  .style("font-weight", "600")
  .text(titleStr);

// Subtitle sits below the title band so it clears the northernmost circles
svg.append("text")
  .attr("x", margin.left)
  .attr("y", 96)
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text(`Circle area ∝ ${VALUE.toLowerCase()} · Color = ${SECONDARY}`);

// Legend column to the right of the map, so no legend element covers a circle
const legX = margin.left + iw + 28;
const colW = width - legX - 16;
const legendTitle = (y, text) =>
  svg.append("text")
    .attr("x", legX)
    .attr("y", y)
    .attr("fill", t.ink)
    .style("font-size", "14px")
    .style("font-weight", "600")
    .text(text);

// Color legend
const legY = margin.top + 10;
const legH = 170;
const legW = 16;

const grad = svg.append("defs").append("linearGradient")
  .attr("id", "cleg-grad")
  .attr("x1", "0%").attr("y1", "100%")
  .attr("x2", "0%").attr("y2", "0%");
d3.range(0, 1.0001, 0.25).forEach((s) => {
  grad.append("stop")
    .attr("offset", `${s * 100}%`)
    .attr("stop-color", colorScale(secLo + s * (secHi - secLo)));
});

svg.append("rect")
  .attr("x", legX)
  .attr("y", legY)
  .attr("width", legW)
  .attr("height", legH)
  .attr("fill", "url(#cleg-grad)")
  .attr("rx", 2);

const cLegScale = d3.scaleLinear().domain([secLo, secHi]).range([legH, 0]);
const cAxisG = svg.append("g")
  .attr("transform", `translate(${legX + legW}, ${legY})`)
  .call(d3.axisRight(cLegScale).ticks(4).tickFormat(fmtK));
cAxisG.selectAll("text").attr("fill", t.inkSoft).style("font-size", "13px");
cAxisG.selectAll("line").attr("stroke", t.inkSoft).attr("stroke-opacity", 0.5);
cAxisG.select(".domain").remove();

legendTitle(legY - 12, "GDP / capita");

const nAbove = secValues.filter((v) => v > secHi).length;
if (nAbove > 0) {
  svg.append("text")
    .attr("x", legX)
    .attr("y", legY + legH + 22)
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .text(`top color = ${fmtK(secHi)} and above`);
}

// Size legend: nested circles at round values of the data range
const szLegY = legY + legH + 72;
legendTitle(szLegY - 12, "Population");

const szMax = d3.max(regions, (d) => d[VALUE]);
const szVals = [1, 10, 30].filter((v) => v <= szMax);
const szR = rScale(d3.max(szVals));
const szCx = legX + szR + 2;
const szBase = szLegY + 2 * szR;
szVals.forEach((v) => {
  const r = rScale(v);
  const cy = szBase - r;
  svg.append("circle")
    .attr("cx", szCx)
    .attr("cy", cy)
    .attr("r", r)
    .attr("fill", "none")
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "3,2");
  svg.append("line")
    .attr("x1", szCx)
    .attr("y1", cy - r)
    .attr("x2", szCx + szR + 8)
    .attr("y2", cy - r)
    .attr("stroke", t.inkSoft)
    .attr("stroke-width", 1);
  svg.append("text")
    .attr("x", szCx + szR + 12)
    .attr("y", cy - r + 4)
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .text(`${v}M`);
});

// Reference inset: equal-size dots at true positions, for comparison with the cartogram
const insetY = szBase + 52;
// AlbersUSA spans roughly 1.6 : 1, so the box follows that aspect within the free column height
const insetH = Math.min(height - margin.bottom - insetY + 20, colW * 0.66);
legendTitle(insetY - 12, "Actual geography");

const inset = svg.append("g").attr("transform", `translate(${legX},${insetY})`);
inset.append("rect")
  .attr("width", colW)
  .attr("height", insetH)
  .attr("fill", t.elevatedBg)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1)
  .attr("rx", 4);

const insetProj = d3.geoAlbersUsa().fitExtent([[8, 8], [colW - 8, insetH - 8]], geoFeatures);
inset.selectAll("circle")
  .data(regions)
  .join("circle")
  .attr("cx", (d) => insetProj([d[LON], d[LAT]])?.[0] ?? -99)
  .attr("cy", (d) => insetProj([d[LON], d[LAT]])?.[1] ?? -99)
  .attr("r", 4)
  .attr("fill", (d) => (d[SECONDARY] == null ? t.grid : colorScale(d[SECONDARY])))
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 0.6);
