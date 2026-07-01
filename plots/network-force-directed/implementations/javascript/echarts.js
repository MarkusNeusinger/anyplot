// anyplot.ai
// network-force-directed: Force-Directed Graph
// Library: echarts 5.5.1 | JavaScript 22.23.1
// Quality: 85/100 | Created: 2026-07-01
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Software module dependency network — 30 nodes, 4 communities
const categoryDefs = [
  { name: "Frontend" },
  { name: "Backend" },
  { name: "Data Layer" },
  { name: "Infrastructure" },
];

const rawNodes = [
  { id: "App",        label: "App",        cat: 0 },
  { id: "Router",     label: "Router",     cat: 0 },
  { id: "Pages",      label: "Pages",      cat: 0 },
  { id: "Components", label: "Components", cat: 0 },
  { id: "Store",      label: "Store",      cat: 0 },
  { id: "Styles",     label: "Styles",     cat: 0 },
  { id: "Assets",     label: "Assets",     cat: 0 },
  { id: "API",        label: "API",        cat: 1 },
  { id: "Auth",       label: "Auth",       cat: 1 },
  { id: "Users",      label: "Users",      cat: 1 },
  { id: "Products",   label: "Products",   cat: 1 },
  { id: "Orders",     label: "Orders",     cat: 1 },
  { id: "Search",     label: "Search",     cat: 1 },
  { id: "Cache",      label: "Cache",      cat: 1 },
  { id: "Config",     label: "Config",     cat: 1 },
  { id: "Database",   label: "Database",   cat: 2 },
  { id: "Analytics",  label: "Analytics",  cat: 2 },
  { id: "Reports",    label: "Reports",    cat: 2 },
  { id: "ETL",        label: "ETL",        cat: 2 },
  { id: "DataStore",  label: "DataStore",  cat: 2 },
  { id: "Queue",      label: "Queue",      cat: 2 },
  { id: "Metrics",    label: "Metrics",    cat: 2 },
  { id: "CICD",       label: "CI/CD",      cat: 3 },
  { id: "Deploy",     label: "Deploy",     cat: 3 },
  { id: "Monitor",    label: "Monitor",    cat: 3 },
  { id: "Logging",    label: "Logging",    cat: 3 },
  { id: "Docker",     label: "Docker",     cat: 3 },
  { id: "K8s",        label: "K8s",        cat: 3 },
  { id: "Registry",   label: "Registry",   cat: 3 },
  { id: "Gateway",    label: "Gateway",    cat: 3 },
];

const edgePairs = [
  // Frontend internal
  ["App", "Router"], ["App", "Pages"], ["App", "Components"], ["App", "Store"],
  ["Pages", "Components"], ["Pages", "Styles"], ["Components", "Styles"], ["Components", "Assets"],
  // Backend internal
  ["API", "Auth"], ["API", "Users"], ["API", "Products"], ["API", "Orders"],
  ["API", "Search"], ["Auth", "Users"], ["Auth", "Config"],
  ["Users", "Cache"], ["Products", "Cache"],
  // Data Layer internal
  ["Database", "Analytics"], ["Database", "DataStore"], ["Analytics", "Reports"],
  ["ETL", "Database"], ["ETL", "DataStore"], ["Queue", "ETL"],
  ["Metrics", "Analytics"], ["DataStore", "Reports"],
  // Infrastructure internal
  ["K8s", "Docker"], ["K8s", "Deploy"], ["CICD", "Docker"], ["CICD", "Registry"],
  ["Deploy", "Monitor"], ["Deploy", "K8s"], ["Monitor", "Logging"],
  ["Gateway", "Monitor"], ["Gateway", "K8s"], ["Registry", "Docker"],
  // Cross-community
  ["App", "API"],
  ["API", "Database"], ["API", "Cache"], ["Auth", "Database"], ["Orders", "Queue"],
  ["CICD", "API"], ["Gateway", "API"],
  ["Monitor", "Metrics"], ["Logging", "DataStore"],
];

// Compute degree for proportional node sizing
const degree = {};
rawNodes.forEach(function(n) { degree[n.id] = 0; });
edgePairs.forEach(function(pair) {
  degree[pair[0]] = (degree[pair[0]] || 0) + 1;
  degree[pair[1]] = (degree[pair[1]] || 0) + 1;
});

const nodes = rawNodes.map(function(n) {
  return {
    name: n.id,
    value: degree[n.id],
    category: n.cat,
    symbolSize: Math.max(14, 10 + degree[n.id] * 4),
    label: { formatter: n.label },
  };
});

const links = edgePairs.map(function(pair) {
  return { source: pair[0], target: pair[1] };
});

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "network-force-directed · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
  },
  legend: {
    data: categoryDefs.map(function(c) { return c.name; }),
    top: 70,
    left: "center",
    orient: "horizontal",
    textStyle: { color: t.inkSoft, fontSize: 13 },
    icon: "circle",
    itemWidth: 10,
    itemHeight: 10,
    itemGap: 28,
  },
  series: [
    {
      type: "graph",
      layout: "force",
      data: nodes,
      links: links,
      categories: categoryDefs,
      roam: false,
      label: {
        show: true,
        position: "right",
        fontSize: 12,
        color: t.inkSoft,
      },
      labelLayout: { hideOverlap: true },
      lineStyle: {
        width: 1.5,
        opacity: 0.55,
        color: "source",
        curveness: 0,
      },
      itemStyle: {
        borderColor: t.pageBg,
        borderWidth: 2,
      },
      emphasis: { scale: false },
      force: {
        repulsion: 180,
        gravity: 0.15,
        edgeLength: [50, 120],
        layoutAnimation: false,
      },
    },
  ],
});
