// anyplot.ai
// map-tile-background: Map with Tile Background
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const light = t.theme === "light";

// --- Data: Barcelona Bicing bike-share stations, daily rides ---------------
// The runtime is offline (no fetch/CDN), so the "tile background" below is a
// deterministic, procedurally generated street-grid basemap rather than a
// fetched OSM/CartoDB raster — see the block-hash generator further down.
const stations = [
  { label: "Plaça Catalunya", lat: 41.387, lon: 2.1701, rides: 1450 },
  { label: "Passeig de Gràcia", lat: 41.3917, lon: 2.1649, rides: 1280 },
  { label: "Rambla Catalunya", lat: 41.39, lon: 2.162, rides: 990 },
  { label: "Sagrada Família", lat: 41.4036, lon: 2.1744, rides: 980 },
  { label: "Barceloneta Beach", lat: 41.3784, lon: 2.1925, rides: 1120 },
  { label: "Gòtic · Pl. Sant Jaume", lat: 41.3825, lon: 2.1769, rides: 860 },
  { label: "Park Güell", lat: 41.4145, lon: 2.1527, rides: 640 },
  { label: "El Born", lat: 41.385, lon: 2.1815, rides: 790 },
  { label: "Montjuïc · Fundació Miró", lat: 41.369, lon: 2.159, rides: 420 },
  { label: "Poble Sec", lat: 41.3735, lon: 2.162, rides: 560 },
  { label: "Vila de Gràcia", lat: 41.402, lon: 2.156, rides: 710 },
  { label: "Diagonal Mar", lat: 41.409, lon: 2.214, rides: 480 },
  { label: "Port Vell", lat: 41.3755, lon: 2.183, rides: 870 },
  { label: "Sant Antoni Market", lat: 41.3757, lon: 2.1636, rides: 730 },
];

// --- Layout ------------------------------------------------------------
const margin = { top: 96, right: 40, bottom: 40, left: 40 };
const mapX0 = margin.left;
const mapY0 = margin.top;
const mapX1 = width - margin.right;
const mapY1 = height - margin.bottom;
const mapW = mapX1 - mapX0;
const mapH = mapY1 - mapY0;

// --- Fit-bounds projection (equirectangular, latitude-corrected) -----------
// Auto-fits the initial view to the padded data extent, the way a real tile
// map's fitBounds() call would before picking a zoom level.
const lats = stations.map((d) => d.lat);
const lons = stations.map((d) => d.lon);
let latMin = d3.min(lats);
let latMax = d3.max(lats);
let lonMin = d3.min(lons);
let lonMax = d3.max(lons);
const latPad = Math.max((latMax - latMin) * 0.28, 0.008);
const lonPad = Math.max((lonMax - lonMin) * 0.28, 0.008);
latMin -= latPad;
latMax += latPad;
lonMin -= lonPad;
lonMax += lonPad;

const cosLat = Math.cos(((latMin + latMax) / 2) * (Math.PI / 180));
const geoW = (lonMax - lonMin) * cosLat;
const geoH = latMax - latMin;
const fitScale = Math.min(mapW / geoW, mapH / geoH);
const projW = geoW * fitScale;
const projH = geoH * fitScale;
const offX = mapX0 + (mapW - projW) / 2;
const offY = mapY0 + (mapH - projH) / 2;

const projX = (lon) => offX + (lon - lonMin) * cosLat * fitScale;
const projY = (lat) => offY + (latMax - lat) * fitScale;

const zoomLevel = Math.max(10, Math.min(18, Math.round(Math.log2((360 * mapW) / (256 * (lonMax - lonMin))))));

// --- Basemap tones (theme-adaptive, decorative — not data colors) ----------
const landFill = light ? "#F1ECDD" : "#211E17";
const blockFill = light ? "#E7DFC9" : "#282318";
const parkFill = light ? "#D9E5C9" : "#1E2A1C";
const waterFill = light ? "#CDE0EC" : "#1A2530";
const streetStroke = light ? "rgba(26,26,23,0.3)" : "rgba(240,239,232,0.28)";

// --- SVG mount ---------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

svg
  .append("clipPath")
  .attr("id", "map-viewport")
  .append("rect")
  .attr("x", mapX0)
  .attr("y", mapY0)
  .attr("width", mapW)
  .attr("height", mapH)
  .attr("rx", 18);

const mapG = svg.append("g").attr("clip-path", "url(#map-viewport)");

mapG.append("rect").attr("x", mapX0).attr("y", mapY0).attr("width", mapW).attr("height", mapH).attr("fill", landFill);

// --- Synthetic tile texture: deterministic street-grid basemap -------------
// Fixed-hash pseudo-noise (no Math.random) so the "tiles" are reproducible.
// Evokes Barcelona's Eixample grid blocks, with a coastline band toward the
// bottom-right standing in for the Mediterranean.
function blockHash(i, j) {
  const s = Math.sin(i * 12.9898 + j * 78.233) * 43758.5453;
  return s - Math.floor(s);
}

const cell = 42;
const gap = 3;
const cols = Math.ceil(mapW / cell) + 1;
const rows = Math.ceil(mapH / cell) + 1;

const blocks = [];
for (let j = 0; j < rows; j += 1) {
  for (let i = 0; i < cols; i += 1) {
    const u = i / cols;
    const v = j / rows;
    const isWater = u * 0.32 + v > 0.9;
    const h = blockHash(i, j);
    let fill = null;
    if (isWater) fill = waterFill;
    else if (h > 0.94) fill = parkFill;
    else if (h > 0.2) fill = blockFill;
    if (fill) blocks.push({ x: mapX0 + i * cell, y: mapY0 + j * cell, fill, isWater });
  }
}

mapG
  .selectAll("rect.block")
  .data(blocks)
  .join("rect")
  .attr("class", "block")
  .attr("x", (d) => d.x + (d.isWater ? 0 : gap / 2))
  .attr("y", (d) => d.y + (d.isWater ? 0 : gap / 2))
  .attr("width", (d) => cell - (d.isWater ? 0 : gap))
  .attr("height", (d) => cell - (d.isWater ? 0 : gap))
  .attr("rx", (d) => (d.isWater ? 0 : 7))
  .attr("fill", (d) => d.fill);

const streetLines = [];
for (let i = 0; i <= cols; i += 1) {
  streetLines.push({ x1: mapX0 + i * cell, y1: mapY0, x2: mapX0 + i * cell, y2: mapY1 });
}
for (let j = 0; j <= rows; j += 1) {
  streetLines.push({ x1: mapX0, y1: mapY0 + j * cell, x2: mapX1, y2: mapY0 + j * cell });
}

mapG
  .selectAll("line.street")
  .data(streetLines)
  .join("line")
  .attr("class", "street")
  .attr("x1", (d) => d.x1)
  .attr("y1", (d) => d.y1)
  .attr("x2", (d) => d.x2)
  .attr("y2", (d) => d.y2)
  .attr("stroke", streetStroke)
  .attr("stroke-width", 1);

// Map viewport frame
svg
  .append("rect")
  .attr("x", mapX0)
  .attr("y", mapY0)
  .attr("width", mapW)
  .attr("height", mapH)
  .attr("rx", 18)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1.5);

// --- Station markers: color-encode daily rides via imprint_seq -------------
const rideExtent = d3.extent(stations, (d) => d.rides);
const colorScale = d3.scaleSequential(d3.interpolateRgbBasis(t.seq)).domain(rideExtent);
const markerR = 14;

mapG
  .selectAll("circle.station")
  .data(stations)
  .join("circle")
  .attr("class", "station")
  .attr("cx", (d) => projX(d.lon))
  .attr("cy", (d) => projY(d.lat))
  .attr("r", markerR)
  .attr("fill", (d) => colorScale(d.rides))
  .attr("stroke", t.ink)
  .attr("stroke-width", 2)
  .attr("fill-opacity", 0.92);

// --- Station labels: radial placement + measured halo for legibility -------
// A handful of stations sit under 300m apart (real Barcelona geography), so
// the generic radial push alone still stacks their labels; these four get an
// explicit directional override, the same manual-offset technique the
// python/matplotlib sibling implementation uses for its own dense cluster.
const manualOffsets = {
  "El Born": [46, -30],
  "Gòtic · Pl. Sant Jaume": [-52, 22],
  "Sant Antoni Market": [-52, -6],
  "Poble Sec": [48, 22],
};

const centerX = mapX0 + mapW / 2;
const centerY = mapY0 + mapH / 2;
const labelG = svg.append("g");

for (const d of stations) {
  const px = projX(d.lon);
  const py = projY(d.lat);
  let lx;
  let ly;
  let anchor;
  if (manualOffsets[d.label]) {
    const [ox, oy] = manualOffsets[d.label];
    lx = px + ox;
    ly = py + oy;
    anchor = ox >= 0 ? "start" : "end";
  } else {
    const dx = px - centerX;
    const dy = py - centerY;
    const norm = Math.hypot(dx, dy) || 1;
    lx = px + (dx / norm) * 42;
    ly = py + (dy / norm) * 26;
    anchor = dx >= 0 ? "start" : "end";
  }

  const grp = labelG.append("g");
  const text = grp
    .append("text")
    .attr("x", lx)
    .attr("y", ly)
    .attr("text-anchor", anchor)
    .attr("dominant-baseline", "middle")
    .style("font-size", "13px")
    .style("font-weight", "500")
    .attr("fill", t.ink)
    .text(d.label);

  const bbox = text.node().getBBox();
  grp
    .insert("rect", "text")
    .attr("x", bbox.x - 5)
    .attr("y", bbox.y - 3)
    .attr("width", bbox.width + 10)
    .attr("height", bbox.height + 6)
    .attr("rx", 4)
    .attr("fill", t.elevatedBg)
    .attr("fill-opacity", 0.88);
}

// --- Legend: rides color scale + tile-provider selector ---------------------
const legendX = mapX1 - 158;
const legendBarY = mapY0 + 54;
const legendBarH = 120;
const providers = ["Streets", "Terrain", "Satellite"];
const activeProvider = "Streets";
const legendBoxH = 54 + legendBarH + 20 + providers.length * 22 + 12;

svg
  .append("rect")
  .attr("x", legendX - 16)
  .attr("y", mapY0 + 14)
  .attr("width", 158)
  .attr("height", legendBoxH)
  .attr("rx", 10)
  .attr("fill", t.elevatedBg)
  .attr("fill-opacity", 0.92)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1);

svg
  .append("text")
  .attr("x", legendX)
  .attr("y", mapY0 + 34)
  .style("font-size", "13px")
  .style("font-weight", "600")
  .attr("fill", t.ink)
  .text("Daily Rides");

svg
  .append("defs")
  .append("linearGradient")
  .attr("id", "rides-gradient")
  .attr("x1", "0%")
  .attr("y1", "100%")
  .attr("x2", "0%")
  .attr("y2", "0%")
  .selectAll("stop")
  .data([0, 1])
  .join("stop")
  .attr("offset", (d) => `${d * 100}%`)
  .attr("stop-color", (d) => t.seq[d]);

svg
  .append("rect")
  .attr("x", legendX)
  .attr("y", legendBarY)
  .attr("width", 14)
  .attr("height", legendBarH)
  .attr("rx", 3)
  .attr("fill", "url(#rides-gradient)");

svg
  .append("text")
  .attr("x", legendX + 22)
  .attr("y", legendBarY + 6)
  .style("font-size", "11px")
  .attr("fill", t.inkSoft)
  .text(rideExtent[1]);

svg
  .append("text")
  .attr("x", legendX + 22)
  .attr("y", legendBarY + legendBarH)
  .style("font-size", "11px")
  .attr("fill", t.inkSoft)
  .text(rideExtent[0]);

// Tile-provider swatches — illustrates provider-switching support (the active
// style is the synthetic street basemap rendered above; no live tile fetch).
const providerY0 = legendBarY + legendBarH + 26;
providers.forEach((name, idx) => {
  const py = providerY0 + idx * 22;
  const isActive = name === activeProvider;
  svg
    .append("rect")
    .attr("x", legendX - 2)
    .attr("y", py - 11)
    .attr("width", 13)
    .attr("height", 13)
    .attr("rx", 3)
    .attr("fill", isActive ? t.palette[0] : "none")
    .attr("stroke", isActive ? t.palette[0] : t.inkSoft)
    .attr("stroke-width", 1.5);
  svg
    .append("text")
    .attr("x", legendX + 16)
    .attr("y", py)
    .attr("dominant-baseline", "middle")
    .style("font-size", "12px")
    .style("font-weight", isActive ? "600" : "400")
    .attr("fill", isActive ? t.ink : t.inkSoft)
    .text(name);
});

// --- Auto-fit / attribution footnotes (bottom corners, inside viewport) ----
function footnote(x, anchor, str) {
  const grp = svg.append("g");
  const text = grp
    .append("text")
    .attr("x", x)
    .attr("y", mapY1 - 14)
    .attr("text-anchor", anchor)
    .style("font-size", "11px")
    .attr("fill", t.inkSoft)
    .text(str);
  const bbox = text.node().getBBox();
  grp
    .insert("rect", "text")
    .attr("x", bbox.x - 6)
    .attr("y", bbox.y - 3)
    .attr("width", bbox.width + 12)
    .attr("height", bbox.height + 6)
    .attr("rx", 4)
    .attr("fill", t.elevatedBg)
    .attr("fill-opacity", 0.85);
}
footnote(mapX0 + 14, "start", `Auto-fit to data bounds · zoom ≈ ${zoomLevel}`);
footnote(mapX1 - 14, "end", "Basemap: anyplot synthetic street tiles (offline render)");

// --- Title -------------------------------------------------------------
const title = "Barcelona Bicing Network · map-tile-background · javascript · d3 · anyplot.ai";
const titleFontSize = Math.min(22, Math.round((22 * 67) / title.length));
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleFontSize}px`)
  .style("font-weight", "600")
  .text(title);

svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 72)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "15px")
  .text("Bike-share stations sized on a tile-style basemap, colored by daily rides");
