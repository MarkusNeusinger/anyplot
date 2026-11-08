// anyplot.ai
// sunburst-basic: Basic Sunburst Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { PieChart } from "@mui/x-charts/PieChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const HOLE_SHARE = 0.26; // empty centre as a share of the outer radius
const RING_GAP = 10; // px between two rings
const RING_TINT = [0, 0.3, 0.52]; // per ring depth: share of the branch hue mixed toward the light tint
const TINT_RGB = [250, 248, 241]; // the light tint the outer rings mix toward (#FAF8F1)
const LABEL_MIN_ANGLE = [0, 10, 10]; // per ring depth: smallest segment angle (degrees) that carries a label
const LABEL_SIZE = [18, 15, 14]; // per ring depth: label font size (px)
const INK_ON_LIGHT = "#1A1A17"; // label on a light segment
const INK_ON_DARK = "#FAF8F1"; // label on a dark segment
const LUMINANCE_SPLIT = 0.19; // above this relative luminance a segment takes the dark ink
const HEADER_H = 92;
const PAD = 16;

// Columns: set these to your data's column names
const DEPARTMENT = "Department"; // role: level_1
const TEAM = "Team"; // role: level_2
const PROJECT = "Project"; // role: level_3
const BUDGET = "Budget (thousand USD)"; // role: value

// Data: replace this block with your own records, one object per row
// Engineering org budget: one row per project, under its team and department
const data = [
  { [DEPARTMENT]: "Engineering", [TEAM]: "Backend", [PROJECT]: "API Platform", [BUDGET]: 120 },
  { [DEPARTMENT]: "Engineering", [TEAM]: "Backend", [PROJECT]: "Data Pipeline", [BUDGET]: 80 },
  { [DEPARTMENT]: "Engineering", [TEAM]: "Frontend", [PROJECT]: "Web App", [BUDGET]: 90 },
  { [DEPARTMENT]: "Engineering", [TEAM]: "Frontend", [PROJECT]: "Mobile App", [BUDGET]: 60 },
  { [DEPARTMENT]: "Engineering", [TEAM]: "Platform", [PROJECT]: "Infra", [BUDGET]: 80 },
  { [DEPARTMENT]: "Engineering", [TEAM]: "Platform", [PROJECT]: "DevOps", [BUDGET]: 50 },
  { [DEPARTMENT]: "Design", [TEAM]: "Product Design", [PROJECT]: "UX Research", [BUDGET]: 70 },
  { [DEPARTMENT]: "Design", [TEAM]: "Product Design", [PROJECT]: "Visual Design", [BUDGET]: 70 },
  { [DEPARTMENT]: "Design", [TEAM]: "Brand", [PROJECT]: "Identity", [BUDGET]: 50 },
  { [DEPARTMENT]: "Design", [TEAM]: "Brand", [PROJECT]: "Campaigns", [BUDGET]: 30 },
  { [DEPARTMENT]: "Marketing", [TEAM]: "Content", [PROJECT]: "Blog", [BUDGET]: 60 },
  { [DEPARTMENT]: "Marketing", [TEAM]: "Content", [PROJECT]: "Social", [BUDGET]: 40 },
  { [DEPARTMENT]: "Marketing", [TEAM]: "Growth", [PROJECT]: "SEO", [BUDGET]: 45 },
  { [DEPARTMENT]: "Marketing", [TEAM]: "Growth", [PROJECT]: "Paid Ads", [BUDGET]: 35 },
  { [DEPARTMENT]: "Operations", [TEAM]: "Finance", [PROJECT]: "Accounting", [BUDGET]: 40 },
  { [DEPARTMENT]: "Operations", [TEAM]: "Finance", [PROJECT]: "Payroll", [BUDGET]: 30 },
  { [DEPARTMENT]: "Operations", [TEAM]: "HR", [PROJECT]: "Recruiting", [BUDGET]: 30 },
  { [DEPARTMENT]: "Operations", [TEAM]: "HR", [PROJECT]: "Benefits", [BUDGET]: 20 },
];

// Plot: reads only data and the constants above
// Every ring lists its segments in the same branch order, so each ring sums to the
// grand total and a child's arc lies inside its parent's angular span
const departments = [...new Set(data.map((d) => d[DEPARTMENT]))];
const teams = departments.flatMap((dep) =>
  [...new Set(data.filter((d) => d[DEPARTMENT] === dep).map((d) => d[TEAM]))].map((team) => ({ dep, team })),
);
const leaves = teams.flatMap(({ dep, team }) => data.filter((d) => d[DEPARTMENT] === dep && d[TEAM] === team));
const rings = [
  departments.map((dep, i) => ({
    id: dep,
    label: dep,
    branch: i,
    value: data.filter((d) => d[DEPARTMENT] === dep).reduce((sum, d) => sum + d[BUDGET], 0),
  })),
  teams.map(({ dep, team }) => ({
    id: `${dep}/${team}`,
    label: team,
    branch: departments.indexOf(dep),
    value: data.filter((d) => d[DEPARTMENT] === dep && d[TEAM] === team).reduce((sum, d) => sum + d[BUDGET], 0),
  })),
  leaves.map((d) => ({
    id: `${d[DEPARTMENT]}/${d[TEAM]}/${d[PROJECT]}`,
    label: d[PROJECT],
    branch: departments.indexOf(d[DEPARTMENT]),
    value: d[BUDGET],
  })),
].map((ring, depth) =>
  ring.map((s) => {
    // one hue per department, lighter toward the outer rings; the label ink follows the fill's luminance
    const rgb = [1, 3, 5].map((k, c) =>
      Math.round(parseInt(t.palette[s.branch].slice(k, k + 2), 16) * (1 - RING_TINT[depth]) + TINT_RGB[c] * RING_TINT[depth]),
    );
    const luminance = rgb
      .map((v) => (v / 255 <= 0.04045 ? v / 255 / 12.92 : ((v / 255 + 0.055) / 1.055) ** 2.4))
      .reduce((sum, v, c) => sum + v * [0.2126, 0.7152, 0.0722][c], 0);
    return {
      ...s,
      color: `#${rgb.map((v) => v.toString(16).padStart(2, "0")).join("")}`,
      ink: luminance > LUMINANCE_SPLIT ? INK_ON_LIGHT : INK_ON_DARK,
    };
  }),
);
const total = data.reduce((sum, d) => sum + d[BUDGET], 0);
const budgetUnit = BUDGET.match(/\(([^)]+)\)/)?.[1] ?? "";
const ringIds = [DEPARTMENT, TEAM, PROJECT].map((name) => name.toLowerCase().replace(/\W+/g, "-"));
const labelSx = Object.fromEntries(
  rings.flatMap((ring, depth) =>
    ring.map((s, i) => [
      `& .MuiPieChart-seriesLabels[data-series="${ringIds[depth]}"] .MuiPieChart-arcLabel:nth-of-type(${i + 1})`,
      { fill: s.ink, fontSize: LABEL_SIZE[depth], fontWeight: depth === 0 ? 700 : 600 },
    ]),
  ),
);

const TITLE = "sunburst-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${BUDGET} · total ${total.toLocaleString("en-US")} across ${rings[0].length} ${DEPARTMENT.toLowerCase()}s, ${rings[1].length} ${TEAM.toLowerCase()}s, ${rings[2].length} ${PROJECT.toLowerCase()}s`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const side = Math.min(width, height - HEADER_H);
  const outer = side / 2 - PAD;
  const hole = outer * HOLE_SHARE;
  const thickness = (outer - hole - RING_GAP * (rings.length - 1)) / rings.length;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <PieChart
        width={side}
        height={side}
        skipAnimation
        hideLegend
        margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
        series={rings.map((ring, depth) => ({
          id: ringIds[depth],
          data: ring.map((s) => ({ id: s.id, label: s.label, value: s.value, color: s.color })),
          innerRadius: hole + depth * (thickness + RING_GAP),
          outerRadius: hole + depth * (thickness + RING_GAP) + thickness,
          arcLabel: "label",
          arcLabelMinAngle: LABEL_MIN_ANGLE[depth],
          valueFormatter: (item) => `${item.value} ${budgetUnit}`,
        }))}
        sx={{ "& .MuiPieChart-arc": { stroke: t.pageBg, strokeWidth: 2 }, ...labelSx }}
      />
    </Box>
  );
}
