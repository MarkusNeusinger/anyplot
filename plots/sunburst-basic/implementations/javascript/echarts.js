// anyplot.ai
// sunburst-basic: Basic Sunburst Chart
// Library: echarts 6.1.0 | JavaScript 22.23.1
// Quality: 89/100 | Created: 2026-07-26

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Color helpers ----------------------------------------------------------
// Lighten an Imprint hex toward white by `amt` (0-1) — deeper rings get a
// paler tint of their branch color, independent of theme (data colors never
// change between light/dark, only chrome does).
function lighten(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const mix = (c) => Math.round(c + (255 - c) * amt);
  const r = mix((n >> 16) & 255);
  const g = mix((n >> 8) & 255);
  const b = mix(n & 255);
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}

// WCAG relative-luminance pick: dark ink on pale fills, white on saturated ones.
function textOn(hex) {
  const n = parseInt(hex.slice(1), 16);
  const chan = (c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  };
  const r = chan((n >> 16) & 255);
  const g = chan((n >> 8) & 255);
  const b = chan(n & 255);
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 0.42 ? "#1A1A17" : "#FFFFFF";
}

// --- Data: R&D budget allocation, department -> team -> project ($k) -------
const branches = [
  {
    name: "Engineering",
    color: t.palette[0],
    teams: [
      { name: "Platform", projects: [["Core API", 420], ["Infra Migration", 260]] },
      { name: "Product", projects: [["Mobile App", 380], ["Web App", 310]] },
      { name: "Data Science", projects: [["ML Models", 300], ["Analytics", 190]] },
    ],
  },
  {
    name: "Sales",
    color: t.palette[1],
    teams: [
      { name: "Enterprise", projects: [["Key Accounts", 340], ["New Business", 210]] },
      { name: "SMB", projects: [["Inbound", 160], ["Outbound", 140]] },
    ],
  },
  {
    name: "Marketing",
    color: t.palette[2],
    teams: [
      { name: "Brand", projects: [["Content", 150], ["Design", 120]] },
      { name: "Growth", projects: [["Paid Ads", 220], ["SEO", 130]] },
    ],
  },
  {
    name: "Operations",
    color: t.palette[3],
    teams: [
      { name: "Finance", projects: [["Accounting", 130], ["Payroll", 110]] },
      { name: "HR", projects: [["Recruiting", 95], ["Benefits", 85]] },
    ],
  },
];

const data = branches.map((branch) => ({
  name: branch.name,
  itemStyle: { color: branch.color },
  label: { color: textOn(branch.color) },
  children: branch.teams.map((team) => {
    const teamColor = lighten(branch.color, 0.35);
    return {
      name: team.name,
      itemStyle: { color: teamColor },
      label: { color: textOn(teamColor) },
      children: team.projects.map(([name, budget]) => {
        const projectColor = lighten(branch.color, 0.6);
        return {
          name,
          value: budget,
          itemStyle: { color: projectColor },
          label: { color: textOn(projectColor) },
        };
      }),
    };
  }),
}));

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "sunburst-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  tooltip: { formatter: (p) => `${p.name}: $${p.value}k` },
  series: [
    {
      type: "sunburst",
      center: ["50%", "55%"],
      sort: null,
      emphasis: { focus: "ancestor" },
      itemStyle: { borderColor: t.pageBg, borderWidth: 3 },
      label: { rotate: "radial", overflow: "truncate" },
      levels: [
        {},
        { r0: 0, r: "38%", label: { fontSize: 19, fontWeight: "bold" } },
        { r0: "38%", r: "64%", label: { fontSize: 15 } },
        { r0: "64%", r: "80%", label: { fontSize: 12, rotate: "tangential" } },
      ],
      data,
    },
  ],
});
