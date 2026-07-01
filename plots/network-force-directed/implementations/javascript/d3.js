// anyplot.ai
// network-force-directed: Force-Directed Graph
// Library: d3 7.9.0 | JavaScript 22.23.0
// Quality: 87/100 | Created: 2026-07-01

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 72, right: 175, bottom: 60, left: 60 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: Tech Ecosystem Dependency Network (35 nodes, 51 edges) ---
const GROUPS = ["Languages", "Frameworks", "Databases", "DevOps", "ML / Data"];

const rawNodes = [
  { id: "Python",        group: 0 }, { id: "JavaScript",    group: 0 },
  { id: "TypeScript",    group: 0 }, { id: "Java",          group: 0 },
  { id: "Go",            group: 0 }, { id: "Scala",         group: 0 },
  { id: "Ruby",          group: 0 },
  { id: "React",         group: 1 }, { id: "Angular",       group: 1 },
  { id: "Vue",           group: 1 }, { id: "Django",        group: 1 },
  { id: "FastAPI",       group: 1 }, { id: "Spring",        group: 1 },
  { id: "Express",       group: 1 }, { id: "Rails",         group: 1 },
  { id: "Next.js",       group: 1 }, { id: "Svelte",        group: 1 },
  { id: "PostgreSQL",    group: 2 }, { id: "MySQL",         group: 2 },
  { id: "MongoDB",       group: 2 }, { id: "Redis",         group: 2 },
  { id: "SQLite",        group: 2 }, { id: "Elasticsearch", group: 2 },
  { id: "Docker",        group: 3 }, { id: "Kubernetes",    group: 3 },
  { id: "AWS",           group: 3 }, { id: "GitHub",        group: 3 },
  { id: "Terraform",     group: 3 }, { id: "Nginx",         group: 3 },
  { id: "TensorFlow",    group: 4 }, { id: "PyTorch",       group: 4 },
  { id: "NumPy",         group: 4 }, { id: "Pandas",        group: 4 },
  { id: "Spark",         group: 4 }, { id: "Keras",         group: 4 },
];

const rawLinks = [
  { source: "Python",     target: "Django"         },
  { source: "Python",     target: "FastAPI"        },
  { source: "Python",     target: "TensorFlow"     },
  { source: "Python",     target: "PyTorch"        },
  { source: "Python",     target: "NumPy"          },
  { source: "Python",     target: "Pandas"         },
  { source: "Python",     target: "Keras"          },
  { source: "JavaScript", target: "React"          },
  { source: "JavaScript", target: "Angular"        },
  { source: "JavaScript", target: "Vue"            },
  { source: "JavaScript", target: "Express"        },
  { source: "JavaScript", target: "Svelte"         },
  { source: "JavaScript", target: "TypeScript"     },
  { source: "TypeScript", target: "React"          },
  { source: "TypeScript", target: "Angular"        },
  { source: "TypeScript", target: "Next.js"        },
  { source: "React",      target: "Next.js"        },
  { source: "Java",       target: "Spring"         },
  { source: "Java",       target: "Elasticsearch"  },
  { source: "Scala",      target: "Spark"          },
  { source: "Scala",      target: "Java"           },
  { source: "Go",         target: "Docker"         },
  { source: "Go",         target: "Kubernetes"     },
  { source: "Ruby",       target: "Rails"          },
  { source: "Django",     target: "PostgreSQL"     },
  { source: "Django",     target: "MySQL"          },
  { source: "Django",     target: "SQLite"         },
  { source: "Django",     target: "Redis"          },
  { source: "FastAPI",    target: "PostgreSQL"     },
  { source: "FastAPI",    target: "MongoDB"        },
  { source: "FastAPI",    target: "Redis"          },
  { source: "Spring",     target: "PostgreSQL"     },
  { source: "Spring",     target: "MySQL"          },
  { source: "Express",    target: "MongoDB"        },
  { source: "Express",    target: "PostgreSQL"     },
  { source: "Rails",      target: "PostgreSQL"     },
  { source: "Rails",      target: "MySQL"          },
  { source: "Rails",      target: "SQLite"         },
  { source: "Docker",     target: "Kubernetes"     },
  { source: "Kubernetes", target: "AWS"            },
  { source: "Terraform",  target: "AWS"            },
  { source: "Nginx",      target: "Docker"         },
  { source: "Nginx",      target: "Kubernetes"     },
  { source: "GitHub",     target: "Docker"         },
  { source: "GitHub",     target: "Kubernetes"     },
  { source: "TensorFlow", target: "Keras"          },
  { source: "TensorFlow", target: "NumPy"          },
  { source: "PyTorch",    target: "NumPy"          },
  { source: "Pandas",     target: "NumPy"          },
  { source: "Pandas",     target: "PostgreSQL"     },
  { source: "Spark",      target: "Elasticsearch"  },
];

// --- Degree computation (before simulation mutates links) ---
const degMap = new Map(rawNodes.map(n => [n.id, 0]));
rawLinks.forEach(({ source, target }) => {
  degMap.set(source, degMap.get(source) + 1);
  degMap.set(target, degMap.get(target) + 1);
});
const nodes = rawNodes.map(n => ({ ...n, degree: degMap.get(n.id) }));
const links = rawLinks.map(l => ({ ...l }));

const maxDeg = d3.max(nodes, d => d.degree);
const nodeRadius = d => 6 + (d.degree / maxDeg) * 13;

// --- Force simulation (run synchronously for static render) ---
const sim = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(80).strength(0.7))
  .force("charge", d3.forceManyBody().strength(-280))
  .force("center", d3.forceCenter(iw / 2, ih / 2))
  .force("x", d3.forceX(iw / 2).strength(0.05))
  .force("y", d3.forceY(ih / 2).strength(0.05))
  .force("collide", d3.forceCollide().radius(d => nodeRadius(d) + 5).iterations(2))
  .stop();

for (let i = 0; i < 300; i++) sim.tick();

nodes.forEach(n => {
  const r = nodeRadius(n);
  n.x = Math.max(r + 2, Math.min(iw - r - 2, n.x));
  n.y = Math.max(r + 2, Math.min(ih - r - 2, n.y));
});

// --- SVG mount ---
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Edges ---
g.append("g")
  .selectAll("line")
  .data(links)
  .join("line")
  .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
  .attr("x2", d => d.target.x).attr("y2", d => d.target.y)
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 1)
  .attr("stroke-opacity", 0.35);

// --- Nodes ---
g.append("g")
  .selectAll("circle")
  .data(nodes)
  .join("circle")
  .attr("cx", d => d.x)
  .attr("cy", d => d.y)
  .attr("r", d => nodeRadius(d))
  .attr("fill", d => t.palette[d.group])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5)
  .attr("fill-opacity", 0.9);

// --- Labels for hub nodes (degree >= 4) ---
g.append("g")
  .selectAll("text")
  .data(nodes.filter(d => d.degree >= 4))
  .join("text")
  .attr("x", d => d.x)
  .attr("y", d => d.y - nodeRadius(d) - 4)
  .attr("text-anchor", "middle")
  .attr("fill", t.inkSoft)
  .style("font-size", "12px")
  .style("font-weight", "500")
  .text(d => d.id);

// --- Legend ---
const lgX = margin.left + iw + 24;
const lgY = margin.top + 20;
const lgG = svg.append("g").attr("transform", `translate(${lgX},${lgY})`);

GROUPS.forEach((name, i) => {
  const row = lgG.append("g").attr("transform", `translate(0,${i * 28})`);
  row.append("circle")
    .attr("cx", 8).attr("cy", 0).attr("r", 7)
    .attr("fill", t.palette[i]).attr("fill-opacity", 0.9)
    .attr("stroke", t.pageBg).attr("stroke-width", 1.5);
  row.append("text")
    .attr("x", 22).attr("y", 5)
    .attr("fill", t.inkSoft)
    .style("font-size", "13px")
    .text(name);
});

lgG.append("text")
  .attr("x", 0)
  .attr("y", GROUPS.length * 28 + 22)
  .attr("fill", t.inkSoft)
  .style("font-size", "11px")
  .text("Node size ∝ degree");

// --- Title ---
svg.append("text")
  .attr("x", width / 2).attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("network-force-directed · javascript · d3 · anyplot.ai");
