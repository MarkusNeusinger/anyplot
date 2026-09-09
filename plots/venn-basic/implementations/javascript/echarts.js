// anyplot.ai
// venn-basic: Venn Diagram
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-09
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Primary programming languages reported by software engineers in a skills
// survey. Each set is the total engineers who know that language; the
// overlap counts are the engineers who know two or all three.
const SET_A = { name: "Python", total: 120, color: t.palette[0] };
const SET_B = { name: "JavaScript", total: 100, color: t.palette[1] };
const SET_C = { name: "SQL", total: 90, color: t.palette[2] };

const REGIONS = {
  aOnly: 55,
  bOnly: 40,
  cOnly: 40,
  abOnly: 30,
  acOnly: 20,
  bcOnly: 15,
  abc: 15,
};

// --- Geometry -----------------------------------------------------------
// Classic symmetric 3-circle layout: equal-radius circles whose centers sit
// on a small circle around the canvas center, 120 degrees apart. Region
// labels are placed along the same radial directions at hand-tuned radii
// so they land inside the intended lens/petal without touching neighbors.
const cx = width / 2;
const cy = height / 2;
const r = Math.min(width, height) * 0.22;
const centerOffset = r * 0.62;

const polar = (angleDeg, radius) => ({
  x: cx + radius * Math.cos((angleDeg * Math.PI) / 180),
  y: cy - radius * Math.sin((angleDeg * Math.PI) / 180),
});

const ANGLE_A = 150;
const ANGLE_B = 30;
const ANGLE_C = 270;
const ANGLE_AB = 90;
const ANGLE_AC = 210;
const ANGLE_BC = 330;

const CIRCLE_A = polar(ANGLE_A, centerOffset);
const CIRCLE_B = polar(ANGLE_B, centerOffset);
const CIRCLE_C = polar(ANGLE_C, centerOffset);

const setLabelRadius = r * 1.55;
const onlyLabelRadius = centerOffset + r * 0.45;
const pairLabelRadius = r * 0.75;

const hexToRgba = (hex, alpha) => {
  const n = parseInt(hex.slice(1), 16);
  const red = (n >> 16) & 255;
  const green = (n >> 8) & 255;
  const blue = n & 255;
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
};

// --- Title --------------------------------------------------------------
const TITLE = "venn-basic · javascript · echarts · anyplot.ai";
const titleFontSize = TITLE.length > 67 ? Math.round(22 * (67 / TITLE.length)) : 22;

// --- Graphic elements -----------------------------------------------------
const circles = [SET_A, SET_B, SET_C].map((set, i) => {
  const centerPoint = [CIRCLE_A, CIRCLE_B, CIRCLE_C][i];
  return {
    type: "circle",
    shape: { cx: centerPoint.x, cy: centerPoint.y, r },
    style: {
      fill: hexToRgba(set.color, 0.5),
      stroke: t.pageBg,
      lineWidth: 4,
    },
    z: 2,
  };
});

const setLabels = [SET_A, SET_B, SET_C].map((set, i) => {
  const angle = [ANGLE_A, ANGLE_B, ANGLE_C][i];
  const pos = polar(angle, setLabelRadius);
  return {
    type: "text",
    left: pos.x,
    top: pos.y,
    style: {
      text: `${set.name}\n${set.total}`,
      fill: t.ink,
      font: "bold 28px sans-serif",
      textAlign: "center",
      textVerticalAlign: "middle",
      lineHeight: 32,
    },
    z: 5,
  };
});

const regionLabelSpecs = [
  { count: REGIONS.aOnly, pos: polar(ANGLE_A, onlyLabelRadius) },
  { count: REGIONS.bOnly, pos: polar(ANGLE_B, onlyLabelRadius) },
  { count: REGIONS.cOnly, pos: polar(ANGLE_C, onlyLabelRadius) },
  { count: REGIONS.abOnly, pos: polar(ANGLE_AB, pairLabelRadius) },
  { count: REGIONS.acOnly, pos: polar(ANGLE_AC, pairLabelRadius) },
  { count: REGIONS.bcOnly, pos: polar(ANGLE_BC, pairLabelRadius) },
  { count: REGIONS.abc, pos: { x: cx, y: cy } },
];

const regionLabels = regionLabelSpecs.map((region) => ({
  type: "text",
  left: region.pos.x,
  top: region.pos.y,
  style: {
    text: String(region.count),
    fill: t.ink,
    stroke: t.pageBg,
    lineWidth: 3,
    font: "bold 26px sans-serif",
    textAlign: "center",
    textVerticalAlign: "middle",
  },
  z: 5,
}));

// --- Init + option ------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: TITLE,
    left: "center",
    top: height * 0.04,
    textStyle: { color: t.ink, fontSize: titleFontSize },
  },
  graphic: {
    elements: [...circles, ...setLabels, ...regionLabels],
  },
});
