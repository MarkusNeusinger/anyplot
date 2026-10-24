// anyplot.ai
// network-basic: Basic Network Graph
// Library: muix 9.2.1 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-07-24
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "network-basic · javascript · muix · anyplot.ai";
const FONT = "Inter, system-ui, -apple-system, sans-serif";
const TITLE_H = 60;
const CAPTION_H = 34;
const SPRING_K = 0.32;
const ITERATIONS = 300;
const INITIAL_TEMP = 0.06;
const GRAVITY = 0.01;
const DOMAIN_PAD_RATIO = 1.32;
const BASE_RADIUS = 7;
const RADIUS_PER_DEGREE = 2.8;

// Data
const SOURCE_COL = "Person A";
const SOURCE_GROUP_COL = "Group A";
const TARGET_COL = "Person B";
const TARGET_GROUP_COL = "Group B";

const DATA: Array<Record<string, string>> = [
  // Family circle
  { [SOURCE_COL]: "Maya", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Noah", [TARGET_GROUP_COL]: "Family" },
  { [SOURCE_COL]: "Maya", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Priya", [TARGET_GROUP_COL]: "Family" },
  { [SOURCE_COL]: "Maya", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Ethan", [TARGET_GROUP_COL]: "Family" },
  { [SOURCE_COL]: "Noah", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Sofia", [TARGET_GROUP_COL]: "Family" },
  { [SOURCE_COL]: "Priya", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Ethan", [TARGET_GROUP_COL]: "Family" },
  { [SOURCE_COL]: "Ethan", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Sofia", [TARGET_GROUP_COL]: "Family" },
  { [SOURCE_COL]: "Priya", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Sofia", [TARGET_GROUP_COL]: "Family" },
  // College circle
  { [SOURCE_COL]: "Liam", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Aisha", [TARGET_GROUP_COL]: "College" },
  { [SOURCE_COL]: "Liam", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Kenji", [TARGET_GROUP_COL]: "College" },
  { [SOURCE_COL]: "Aisha", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Grace", [TARGET_GROUP_COL]: "College" },
  { [SOURCE_COL]: "Kenji", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Grace", [TARGET_GROUP_COL]: "College" },
  { [SOURCE_COL]: "Kenji", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Diego", [TARGET_GROUP_COL]: "College" },
  { [SOURCE_COL]: "Grace", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Diego", [TARGET_GROUP_COL]: "College" },
  { [SOURCE_COL]: "Liam", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Diego", [TARGET_GROUP_COL]: "College" },
  // Work circle
  { [SOURCE_COL]: "Omar", [SOURCE_GROUP_COL]: "Work", [TARGET_COL]: "Isla", [TARGET_GROUP_COL]: "Work" },
  { [SOURCE_COL]: "Omar", [SOURCE_GROUP_COL]: "Work", [TARGET_COL]: "Victor", [TARGET_GROUP_COL]: "Work" },
  { [SOURCE_COL]: "Isla", [SOURCE_GROUP_COL]: "Work", [TARGET_COL]: "Nadia", [TARGET_GROUP_COL]: "Work" },
  { [SOURCE_COL]: "Victor", [SOURCE_GROUP_COL]: "Work", [TARGET_COL]: "Nadia", [TARGET_GROUP_COL]: "Work" },
  { [SOURCE_COL]: "Victor", [SOURCE_GROUP_COL]: "Work", [TARGET_COL]: "Felix", [TARGET_GROUP_COL]: "Work" },
  { [SOURCE_COL]: "Nadia", [SOURCE_GROUP_COL]: "Work", [TARGET_COL]: "Felix", [TARGET_GROUP_COL]: "Work" },
  { [SOURCE_COL]: "Omar", [SOURCE_GROUP_COL]: "Work", [TARGET_COL]: "Felix", [TARGET_GROUP_COL]: "Work" },
  // Neighbors circle
  { [SOURCE_COL]: "Ruby", [SOURCE_GROUP_COL]: "Neighbors", [TARGET_COL]: "Hassan", [TARGET_GROUP_COL]: "Neighbors" },
  { [SOURCE_COL]: "Ruby", [SOURCE_GROUP_COL]: "Neighbors", [TARGET_COL]: "Chloe", [TARGET_GROUP_COL]: "Neighbors" },
  { [SOURCE_COL]: "Hassan", [SOURCE_GROUP_COL]: "Neighbors", [TARGET_COL]: "Marcus", [TARGET_GROUP_COL]: "Neighbors" },
  { [SOURCE_COL]: "Chloe", [SOURCE_GROUP_COL]: "Neighbors", [TARGET_COL]: "Marcus", [TARGET_GROUP_COL]: "Neighbors" },
  { [SOURCE_COL]: "Chloe", [SOURCE_GROUP_COL]: "Neighbors", [TARGET_COL]: "Elena", [TARGET_GROUP_COL]: "Neighbors" },
  { [SOURCE_COL]: "Marcus", [SOURCE_GROUP_COL]: "Neighbors", [TARGET_COL]: "Elena", [TARGET_GROUP_COL]: "Neighbors" },
  { [SOURCE_COL]: "Ruby", [SOURCE_GROUP_COL]: "Neighbors", [TARGET_COL]: "Elena", [TARGET_GROUP_COL]: "Neighbors" },
  // Cross-circle bridges
  { [SOURCE_COL]: "Maya", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Liam", [TARGET_GROUP_COL]: "College" },
  { [SOURCE_COL]: "Noah", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Omar", [TARGET_GROUP_COL]: "Work" },
  { [SOURCE_COL]: "Aisha", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Ruby", [TARGET_GROUP_COL]: "Neighbors" },
  { [SOURCE_COL]: "Grace", [SOURCE_GROUP_COL]: "College", [TARGET_COL]: "Isla", [TARGET_GROUP_COL]: "Work" },
  { [SOURCE_COL]: "Victor", [SOURCE_GROUP_COL]: "Work", [TARGET_COL]: "Hassan", [TARGET_GROUP_COL]: "Neighbors" },
  { [SOURCE_COL]: "Sofia", [SOURCE_GROUP_COL]: "Family", [TARGET_COL]: "Chloe", [TARGET_GROUP_COL]: "Neighbors" },
];

// Derive unique nodes and groups across both endpoint columns in appearance order
const nodeNames: string[] = [];
const nodeGroupByName = new Map<string, string>();
const groups: string[] = [];

for (let i = 0; i < DATA.length; i++) {
  const row = DATA[i];
  const src = String(row[SOURCE_COL]);
  const srcG = String(row[SOURCE_GROUP_COL]);
  const tgt = String(row[TARGET_COL]);
  const tgtG = String(row[TARGET_GROUP_COL]);

  if (!nodeGroupByName.has(src)) {
    nodeNames.push(src);
    nodeGroupByName.set(src, srcG);
  }
  if (!groups.includes(srcG)) groups.push(srcG);

  if (!nodeGroupByName.has(tgt)) {
    nodeNames.push(tgt);
    nodeGroupByName.set(tgt, tgtG);
  }
  if (!groups.includes(tgtG)) groups.push(tgtG);
}

const groupColors = new Map<string, string>();
for (let i = 0; i < groups.length; i++) {
  groupColors.set(groups[i], t.palette[i]);
}

const nodeIndexByName = new Map<string, number>();
for (let i = 0; i < nodeNames.length; i++) {
  nodeIndexByName.set(nodeNames[i], i);
}

const edgePairs: Array<[number, number]> = [];
const degrees = nodeNames.map(() => 0);
for (let i = 0; i < DATA.length; i++) {
  const a = nodeIndexByName.get(String(DATA[i][SOURCE_COL])) ?? 0;
  const b = nodeIndexByName.get(String(DATA[i][TARGET_COL])) ?? 0;
  edgePairs.push([a, b]);
  degrees[a] += 1;
  degrees[b] += 1;
}

// Deterministic initial positions on group rings
const layoutPositions: Array<{ x: number; y: number }> = [];
for (let i = 0; i < nodeNames.length; i++) {
  const name = nodeNames[i];
  const grp = nodeGroupByName.get(name) ?? groups[0];
  const grpIdx = groups.indexOf(grp);
  const grpAngle = (2 * Math.PI * grpIdx) / groups.length;
  const members = nodeNames.filter((n) => nodeGroupByName.get(n) === grp);
  const localIdx = members.indexOf(name);
  const localAngle = (2 * Math.PI * localIdx) / members.length;
  layoutPositions.push({
    x: Math.cos(grpAngle) * 0.6 + Math.cos(localAngle) * 0.18,
    y: Math.sin(grpAngle) * 0.6 + Math.sin(localAngle) * 0.18,
  });
}

// Fruchterman-Reingold force-directed layout
const nodeCount = nodeNames.length;
const cooling = INITIAL_TEMP / ITERATIONS;
let temperature = INITIAL_TEMP;

for (let iter = 0; iter < ITERATIONS; iter++) {
  const disp = layoutPositions.map(() => ({ x: 0, y: 0 }));

  for (let i = 0; i < nodeCount; i++) {
    for (let j = i + 1; j < nodeCount; j++) {
      const dx = layoutPositions[i].x - layoutPositions[j].x;
      const dy = layoutPositions[i].y - layoutPositions[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.001;
      const force = (SPRING_K * SPRING_K) / dist;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      disp[i].x += fx;
      disp[i].y += fy;
      disp[j].x -= fx;
      disp[j].y -= fy;
    }
  }

  for (let e = 0; e < edgePairs.length; e++) {
    const [a, b] = edgePairs[e];
    const dx = layoutPositions[a].x - layoutPositions[b].x;
    const dy = layoutPositions[a].y - layoutPositions[b].y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.001;
    const force = (dist * dist) / SPRING_K;
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    disp[a].x -= fx;
    disp[a].y -= fy;
    disp[b].x += fx;
    disp[b].y += fy;
  }

  for (let i = 0; i < nodeCount; i++) {
    disp[i].x -= layoutPositions[i].x * GRAVITY;
    disp[i].y -= layoutPositions[i].y * GRAVITY;
    const dist = Math.sqrt(disp[i].x ** 2 + disp[i].y ** 2) || 0.001;
    const move = Math.min(dist, temperature);
    layoutPositions[i].x += (disp[i].x / dist) * move;
    layoutPositions[i].y += (disp[i].y / dist) * move;
  }
  temperature -= cooling;
}

const xs = layoutPositions.map((p) => p.x);
const ys = layoutPositions.map((p) => p.y);
const centerX = (Math.min(...xs) + Math.max(...xs)) / 2;
const centerY = (Math.min(...ys) + Math.max(...ys)) / 2;
const halfExtent =
  (Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) / 2) *
  DOMAIN_PAD_RATIO;
const xAxisMin = centerX - halfExtent;
const xAxisMax = centerX + halfExtent;
const yAxisMin = centerY - halfExtent;
const yAxisMax = centerY + halfExtent;

function NetworkOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();
  const screenPos = layoutPositions.map((p) => ({
    x: Number(xScale(p.x)),
    y: Number(yScale(p.y)),
  }));

  return (
    <g fontFamily={FONT}>
      {/* Edges */}
      <g stroke={t.inkSoft} strokeOpacity={0.42} strokeWidth={1.6}>
        {edgePairs.map(([a, b], i) => (
          <line
            key={`edge-${i}`}
            x1={screenPos[a].x}
            y1={screenPos[a].y}
            x2={screenPos[b].x}
            y2={screenPos[b].y}
          />
        ))}
      </g>

      {/* Nodes and collision-avoiding labels */}
      {nodeNames.map((label, i) => {
        const { x: cx, y: cy } = screenPos[i];
        const grp = nodeGroupByName.get(label) ?? groups[0];
        const color = groupColors.get(grp) ?? t.palette[0];
        const r = BASE_RADIUS + degrees[i] * RADIUS_PER_DEGREE;

        const edgeAngles: number[] = [];
        for (let e = 0; e < edgePairs.length; e++) {
          const [a, b] = edgePairs[e];
          if (a === i) edgeAngles.push(Math.atan2(screenPos[b].y - cy, screenPos[b].x - cx));
          else if (b === i) edgeAngles.push(Math.atan2(screenPos[a].y - cy, screenPos[a].x - cx));
        }

        let labelAngle = Math.PI / 2;
        if (edgeAngles.length > 0) {
          edgeAngles.sort((a, b) => a - b);
          let bestGap = -1;
          for (let k = 0; k < edgeAngles.length; k++) {
            const start = edgeAngles[k];
            const end =
              edgeAngles[(k + 1) % edgeAngles.length] +
              (k === edgeAngles.length - 1 ? 2 * Math.PI : 0);
            const gap = end - start;
            if (gap > bestGap) {
              bestGap = gap;
              labelAngle = start + gap / 2;
            }
          }
        }

        const labelDist = r + 15;
        const lx = cx + Math.cos(labelAngle) * labelDist;
        const ly = cy + Math.sin(labelAngle) * labelDist;

        return (
          <g key={label}>
            <circle cx={cx} cy={cy} r={r} fill={color} stroke={t.pageBg} strokeWidth={2.2} />
            <text
              x={lx}
              y={ly}
              fontSize={15}
              fontWeight={500}
              fill={t.ink}
              textAnchor="middle"
              dominantBaseline="middle"
              stroke={t.pageBg}
              strokeWidth={3.5}
              paintOrder="stroke"
            >
              {label}
            </text>
          </g>
        );
      })}

      {/* Group Legend */}
      <g transform="translate(28, 22)">
        {groups.map((grp, i) => (
          <g key={grp} transform={`translate(0, ${i * 30})`}>
            <circle cx={8} cy={8} r={7.5} fill={groupColors.get(grp) ?? t.palette[0]} />
            <text x={24} y={13} fontSize={15} fontWeight={500} fill={t.ink}>
              {grp}
            </text>
          </g>
        ))}
      </g>
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const chartH = H - TITLE_H - CAPTION_H;

  return (
    <div
      style={{
        width: W,
        height: H,
        backgroundColor: t.pageBg,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[]}
        margin={{ top: 16, right: 24, bottom: 16, left: 24 }}
        xAxis={[{ position: "none", min: xAxisMin, max: xAxisMax, scaleType: "linear" }]}
        yAxis={[{ position: "none", min: yAxisMin, max: yAxisMax, scaleType: "linear" }]}
      >
        <NetworkOverlay />
      </ChartsContainer>
      <div
        style={{
          height: CAPTION_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 14,
          color: t.inkSoft,
        }}
      >
        Fruchterman–Reingold force-directed layout · Node color = social circle · Node size = friendship count (degree)
      </div>
    </div>
  );
}
