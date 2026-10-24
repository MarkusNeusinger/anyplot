// anyplot.ai
// network-bipartite: Bipartite Network Graph
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
//# anyplot-orientation: square

import { useState } from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "network-bipartite · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 60;
const LEGEND_HEIGHT = 86;
const MARGIN = { top: 44, right: 220, bottom: 24, left: 220 };
const NODE_MIN_R = 12;
const NODE_MAX_R = 26;
const ISOLATED_R = 7.5;
const EDGE_MIN_W = 1.6;
const EDGE_MAX_W = 6;

// Columns: set these to your data's column names
const STUDENT = "Student (Set A)"; // role: source
const COURSE = "Course (Set B)"; // role: target
const HOURS = "Weekly contact (h)"; // role: weight

// Data: replace this block with your own records
const data: Array<Record<string, string | number | null>> = [
  { [STUDENT]: "Ava Chen", [COURSE]: "Linear Algebra", [HOURS]: 4 },
  { [STUDENT]: "Ava Chen", [COURSE]: "Data Structures", [HOURS]: 5 },
  { [STUDENT]: "Ava Chen", [COURSE]: "Machine Learning", [HOURS]: 3 },
  { [STUDENT]: "Ava Chen", [COURSE]: "Statistics", [HOURS]: 3 },
  { [STUDENT]: "Liam Brooks", [COURSE]: "Data Structures", [HOURS]: 5 },
  { [STUDENT]: "Liam Brooks", [COURSE]: "Machine Learning", [HOURS]: 4 },
  { [STUDENT]: "Liam Brooks", [COURSE]: "Digital Design", [HOURS]: 3 },
  { [STUDENT]: "Noor Malik", [COURSE]: "Organic Chemistry", [HOURS]: 6 },
  { [STUDENT]: "Noor Malik", [COURSE]: "Cell Biology", [HOURS]: 4 },
  { [STUDENT]: "Noor Malik", [COURSE]: "Statistics", [HOURS]: 3 },
  { [STUDENT]: "Ethan Diaz", [COURSE]: "Microeconomics", [HOURS]: 4 },
  { [STUDENT]: "Ethan Diaz", [COURSE]: "World History", [HOURS]: 2 },
  { [STUDENT]: "Ethan Diaz", [COURSE]: "Statistics", [HOURS]: 4 },
  { [STUDENT]: "Priya Nair", [COURSE]: "Organic Chemistry", [HOURS]: 4 },
  { [STUDENT]: "Priya Nair", [COURSE]: "Cell Biology", [HOURS]: 5 },
  { [STUDENT]: "Priya Nair", [COURSE]: "Statistics", [HOURS]: 3 },
  { [STUDENT]: "Marcus Lee", [COURSE]: "Linear Algebra", [HOURS]: 3 },
  { [STUDENT]: "Marcus Lee", [COURSE]: "Thermodynamics", [HOURS]: 5 },
  { [STUDENT]: "Marcus Lee", [COURSE]: "Statistics", [HOURS]: 3 },
  { [STUDENT]: "Sofia Reyes", [COURSE]: "Microeconomics", [HOURS]: 3 },
  { [STUDENT]: "Sofia Reyes", [COURSE]: "World History", [HOURS]: 3 },
  { [STUDENT]: "Jamal Carter", [COURSE]: "Data Structures", [HOURS]: 4 },
  { [STUDENT]: "Jamal Carter", [COURSE]: "Machine Learning", [HOURS]: 5 },
  { [STUDENT]: "Jamal Carter", [COURSE]: "Digital Design", [HOURS]: 4 },
  { [STUDENT]: "Elena Popov", [COURSE]: "Linear Algebra", [HOURS]: 4 },
  { [STUDENT]: "Elena Popov", [COURSE]: "Thermodynamics", [HOURS]: 4 },
  { [STUDENT]: "Diego Silva", [COURSE]: "Microeconomics", [HOURS]: 5 },
  { [STUDENT]: "Diego Silva", [COURSE]: "World History", [HOURS]: 3 },
  { [STUDENT]: "Diego Silva", [COURSE]: "Statistics", [HOURS]: 2 },
  { [STUDENT]: "Grace Kim", [COURSE]: "Cell Biology", [HOURS]: 4 },
  { [STUDENT]: "Grace Kim", [COURSE]: "Machine Learning", [HOURS]: 3 },
  { [STUDENT]: "Grace Kim", [COURSE]: "Statistics", [HOURS]: 4 },
  { [STUDENT]: "Omar Haddad", [COURSE]: "Data Structures", [HOURS]: 3 },
  { [STUDENT]: "Omar Haddad", [COURSE]: "Digital Design", [HOURS]: 5 },
  { [STUDENT]: "Isla Fraser", [COURSE]: "Organic Chemistry", [HOURS]: 5 },
  { [STUDENT]: "Isla Fraser", [COURSE]: "Cell Biology", [HOURS]: 3 },
  { [STUDENT]: "Victor Alves", [COURSE]: "Linear Algebra", [HOURS]: 3 },
  { [STUDENT]: "Victor Alves", [COURSE]: "Thermodynamics", [HOURS]: 3 },
  { [STUDENT]: "Victor Alves", [COURSE]: "Digital Design", [HOURS]: 3 },
  { [STUDENT]: "Talia Novak", [COURSE]: null, [HOURS]: 0 },
  { [STUDENT]: null, [COURSE]: "Advanced Robotics", [HOURS]: 0 },
];

// Plot: reads only data and the constants above
const unitMatch = /\(([^)]+)\)/.exec(HOURS);
const unit = unitMatch ? unitMatch[1] : "";
const unitSuffix = unit ? `${unit}` : "";

const students: string[] = [];
const courses: string[] = [];
const edges: Array<{ student: number; course: number; hours: number }> = [];

for (let i = 0; i < data.length; i++) {
  const sVal = data[i][STUDENT];
  const cVal = data[i][COURSE];
  if (sVal !== null && sVal !== undefined) {
    const sName = String(sVal);
    if (!students.includes(sName)) students.push(sName);
  }
  if (cVal !== null && cVal !== undefined) {
    const cName = String(cVal);
    if (!courses.includes(cName)) courses.push(cName);
  }
}

for (let i = 0; i < data.length; i++) {
  const sVal = data[i][STUDENT];
  const cVal = data[i][COURSE];
  const hours = Number(data[i][HOURS]);
  if (sVal !== null && sVal !== undefined && cVal !== null && cVal !== undefined && hours > 0) {
    edges.push({
      student: students.indexOf(String(sVal)),
      course: courses.indexOf(String(cVal)),
      hours,
    });
  }
}

const minHours = Math.min(...edges.map((e) => e.hours));
const maxHours = Math.max(...edges.map((e) => e.hours));
const hoursSpan = maxHours - minHours;

const studentDegree = students.map(() => 0);
const courseDegree = courses.map(() => 0);
const studentNeighbors: number[][] = students.map(() => []);
const courseNeighbors: number[][] = courses.map(() => []);

for (let i = 0; i < edges.length; i++) {
  const e = edges[i];
  studentDegree[e.student] += 1;
  courseDegree[e.course] += 1;
  studentNeighbors[e.student].push(e.course);
  courseNeighbors[e.course].push(e.student);
}

const initStudentOrder = students
  .map((_, i) => i)
  .sort((a, b) => studentDegree[b] - studentDegree[a] || a - b);
const initCourseOrder = courses
  .map((_, i) => i)
  .sort((a, b) => courseDegree[b] - courseDegree[a] || a - b);

const initStudentRanks = students.map(() => 0);
for (let r = 0; r < initStudentOrder.length; r++) initStudentRanks[initStudentOrder[r]] = r;
const initCourseRanks = courses.map(() => 0);
for (let r = 0; r < initCourseOrder.length; r++) initCourseRanks[initCourseOrder[r]] = r;

const courseOrder = courseDegree
  .map((d, i) => {
    const neigh = courseNeighbors[i];
    const bary =
      neigh.length === 0
        ? Infinity
        : neigh.reduce((sum, j) => sum + initStudentRanks[j], 0) / neigh.length;
    return { i, d, bary };
  })
  .sort((a, b) => b.d - a.d || a.bary - b.bary || a.i - b.i)
  .map((x) => x.i);

const studentOrder = studentDegree
  .map((d, i) => {
    const neigh = studentNeighbors[i];
    const bary =
      neigh.length === 0
        ? Infinity
        : neigh.reduce((sum, j) => sum + initCourseRanks[j], 0) / neigh.length;
    return { i, d, bary };
  })
  .sort((a, b) => b.d - a.d || a.bary - b.bary || a.i - b.i)
  .map((x) => x.i);

const studentRow = students.map(() => 0);
for (let r = 0; r < studentOrder.length; r++) studentRow[studentOrder[r]] = r;
const courseRow = courses.map(() => 0);
for (let r = 0; r < courseOrder.length; r++) courseRow[courseOrder[r]] = r;

const minDegree = 1;
const maxDegree = Math.max(...studentDegree, ...courseDegree);
const degreeSpan = maxDegree - minDegree;

const studentRadii = studentDegree.map((deg) =>
  deg === 0
    ? ISOLATED_R
    : NODE_MIN_R + ((deg - minDegree) / degreeSpan) * (NODE_MAX_R - NODE_MIN_R),
);
const courseRadii = courseDegree.map((deg) =>
  deg === 0
    ? ISOLATED_R
    : NODE_MIN_R + ((deg - minDegree) / degreeSpan) * (NODE_MAX_R - NODE_MIN_R),
);

interface HoverInfo {
  label: string;
  detail: string;
  x: number;
  y: number;
}

function BipartiteOverlay({
  hover,
  onHoverChange,
}: {
  hover: HoverInfo | null;
  onHoverChange: (info: HoverInfo | null) => void;
}) {
  const { top } = useDrawingArea();
  const xScale = useXScale();
  const yScale = useYScale();
  const canvasW = window.ANYPLOT_SIZE.width;

  const studentX = Number(xScale(0));
  const courseX = Number(xScale(1));

  return (
    <g>
      <text
        x={studentX}
        y={top - 22}
        textAnchor="middle"
        fontSize={16}
        fontWeight={700}
        fill={t.ink}
      >
        <tspan fill={t.palette[0]}>● </tspan>
        {STUDENT}
      </text>
      <text
        x={courseX}
        y={top - 22}
        textAnchor="middle"
        fontSize={16}
        fontWeight={700}
        fill={t.ink}
      >
        <tspan fill={t.palette[1]}>● </tspan>
        {COURSE}
      </text>

      {edges.map((edge, i) => {
        const y1 = Number(yScale(1 - (studentRow[edge.student] + 0.5) / students.length));
        const y2 = Number(yScale(1 - (courseRow[edge.course] + 0.5) / courses.length));
        const hRatio = (edge.hours - minHours) / hoursSpan;
        const strokeW = EDGE_MIN_W + hRatio * (EDGE_MAX_W - EDGE_MIN_W);
        const strokeOp = 0.25 + hRatio * 0.45;
        const tooltip: HoverInfo = {
          label: `${students[edge.student]} → ${courses[edge.course]}`,
          detail: `${edge.hours} ${unitSuffix}`,
          x: (studentX + courseX) / 2,
          y: (y1 + y2) / 2,
        };
        return (
          <g key={`edge-${i}`}>
            <line
              x1={studentX}
              y1={y1}
              x2={courseX}
              y2={y2}
              stroke={t.inkSoft}
              strokeOpacity={strokeOp}
              strokeWidth={strokeW}
              strokeLinecap="round"
            />
            <line
              x1={studentX}
              y1={y1}
              x2={courseX}
              y2={y2}
              stroke="transparent"
              strokeWidth={16}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(tooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
          </g>
        );
      })}

      {students.map((label, i) => {
        const cy = Number(yScale(1 - (studentRow[i] + 0.5) / students.length));
        const r = studentRadii[i];
        const tooltip: HoverInfo = {
          label,
          detail: `degree = ${studentDegree[i]}`,
          x: studentX,
          y: cy,
        };
        return (
          <g key={`student-${i}`}>
            <circle
              cx={studentX}
              cy={cy}
              r={r}
              fill={t.palette[0]}
              fillOpacity={studentDegree[i] === 0 ? 0.4 : 1}
              stroke={t.pageBg}
              strokeWidth={2.5}
              strokeDasharray={studentDegree[i] === 0 ? "3 2" : undefined}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(tooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
            <text
              x={studentX - r - 12}
              y={cy}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize={15}
              fill={t.ink}
              style={{ pointerEvents: "none" }}
            >
              {label}
            </text>
          </g>
        );
      })}

      {courses.map((label, i) => {
        const cy = Number(yScale(1 - (courseRow[i] + 0.5) / courses.length));
        const r = courseRadii[i];
        const tooltip: HoverInfo = {
          label,
          detail: `degree = ${courseDegree[i]}`,
          x: courseX,
          y: cy,
        };
        return (
          <g key={`course-${i}`}>
            <circle
              cx={courseX}
              cy={cy}
              r={r}
              fill={t.palette[1]}
              fillOpacity={courseDegree[i] === 0 ? 0.4 : 1}
              stroke={t.pageBg}
              strokeWidth={2.5}
              strokeDasharray={courseDegree[i] === 0 ? "3 2" : undefined}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(tooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
            <text
              x={courseX + r + 12}
              y={cy}
              textAnchor="start"
              dominantBaseline="middle"
              fontSize={15}
              fill={t.ink}
              style={{ pointerEvents: "none" }}
            >
              {label}
            </text>
          </g>
        );
      })}

      {hover && (
        <g style={{ pointerEvents: "none" }}>
          {(() => {
            const boxW = Math.max(hover.label.length, hover.detail.length) * 8 + 24;
            const boxH = 50;
            const tx = Math.min(Math.max(hover.x - boxW / 2, 8), canvasW - boxW - 8);
            const ty = Math.max(hover.y - boxH - 16, 8);
            return (
              <>
                <rect
                  x={tx}
                  y={ty}
                  width={boxW}
                  height={boxH}
                  rx={6}
                  fill={t.elevatedBg}
                  stroke={t.inkSoft}
                  strokeOpacity={0.45}
                />
                <text
                  x={tx + boxW / 2}
                  y={ty + 20}
                  textAnchor="middle"
                  fontSize={14}
                  fontWeight={600}
                  fill={t.ink}
                >
                  {hover.label}
                </text>
                <text
                  x={tx + boxW / 2}
                  y={ty + 39}
                  textAnchor="middle"
                  fontSize={14}
                  fill={t.inkSoft}
                >
                  {hover.detail}
                </text>
              </>
            );
          })()}
        </g>
      )}
    </g>
  );
}

export default function Chart() {
  const [hover, setHover] = useState<HoverInfo | null>(null);
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT - LEGEND_HEIGHT;
  const hourSamples = [minHours, Math.round((minHours + maxHours) / 2), maxHours];

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
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
        width={width}
        height={chartHeight}
        margin={MARGIN}
        skipAnimation
        series={[]}
        xAxis={[{ position: "none", scaleType: "linear", min: 0, max: 1 }]}
        yAxis={[{ position: "none", scaleType: "linear", min: 0, max: 1 }]}
      >
        <BipartiteOverlay hover={hover} onHoverChange={setHover} />
      </ChartsContainer>
      <div
        style={{
          height: LEGEND_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 10,
          fontSize: 14,
          color: t.inkSoft,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 36 }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 8, color: t.ink }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                backgroundColor: t.palette[0],
                display: "inline-block",
              }}
            />
            {`${STUDENT} · node size = degree`}
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 8, color: t.ink }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                backgroundColor: t.palette[1],
                display: "inline-block",
              }}
            />
            {`${COURSE} · node size = degree`}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <span>{`Edge width = ${HOURS}:`}</span>
          {hourSamples.map((h) => {
            const hRatio = (h - minHours) / hoursSpan;
            const w = EDGE_MIN_W + hRatio * (EDGE_MAX_W - EDGE_MIN_W);
            const op = 0.25 + hRatio * 0.45;
            return (
              <span key={h} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <span
                  style={{
                    width: 34,
                    height: Math.round(w),
                    backgroundColor: t.inkSoft,
                    opacity: op,
                    borderRadius: 2,
                    display: "inline-block",
                  }}
                />
                <span>{`${h}${unitSuffix}`}</span>
              </span>
            );
          })}
          <span>· Dashed outline = isolated node (no edges)</span>
        </div>
      </div>
    </div>
  );
}
