// anyplot.ai
// network-bipartite: Bipartite Network Graph
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-05
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

// Data
const STUDENT_COL = "Student (Set A)";
const COURSE_COL = "Course (Set B)";
const HOURS_COL = "Weekly Contact Hours";

const DATA: Array<Record<string, string | number>> = [
  { [STUDENT_COL]: "Ava Chen", [COURSE_COL]: "Linear Algebra", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Ava Chen", [COURSE_COL]: "Data Structures", [HOURS_COL]: 5 },
  { [STUDENT_COL]: "Ava Chen", [COURSE_COL]: "Machine Learning", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Ava Chen", [COURSE_COL]: "Statistics", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Liam Brooks", [COURSE_COL]: "Data Structures", [HOURS_COL]: 5 },
  { [STUDENT_COL]: "Liam Brooks", [COURSE_COL]: "Machine Learning", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Liam Brooks", [COURSE_COL]: "Digital Design", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Noor Malik", [COURSE_COL]: "Organic Chemistry", [HOURS_COL]: 6 },
  { [STUDENT_COL]: "Noor Malik", [COURSE_COL]: "Cell Biology", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Noor Malik", [COURSE_COL]: "Statistics", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Ethan Diaz", [COURSE_COL]: "Microeconomics", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Ethan Diaz", [COURSE_COL]: "World History", [HOURS_COL]: 2 },
  { [STUDENT_COL]: "Ethan Diaz", [COURSE_COL]: "Statistics", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Priya Nair", [COURSE_COL]: "Organic Chemistry", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Priya Nair", [COURSE_COL]: "Cell Biology", [HOURS_COL]: 5 },
  { [STUDENT_COL]: "Priya Nair", [COURSE_COL]: "Statistics", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Marcus Lee", [COURSE_COL]: "Linear Algebra", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Marcus Lee", [COURSE_COL]: "Thermodynamics", [HOURS_COL]: 5 },
  { [STUDENT_COL]: "Marcus Lee", [COURSE_COL]: "Statistics", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Sofia Reyes", [COURSE_COL]: "Microeconomics", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Sofia Reyes", [COURSE_COL]: "World History", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Jamal Carter", [COURSE_COL]: "Data Structures", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Jamal Carter", [COURSE_COL]: "Machine Learning", [HOURS_COL]: 5 },
  { [STUDENT_COL]: "Jamal Carter", [COURSE_COL]: "Digital Design", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Elena Popov", [COURSE_COL]: "Linear Algebra", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Elena Popov", [COURSE_COL]: "Thermodynamics", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Diego Silva", [COURSE_COL]: "Microeconomics", [HOURS_COL]: 5 },
  { [STUDENT_COL]: "Diego Silva", [COURSE_COL]: "World History", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Diego Silva", [COURSE_COL]: "Statistics", [HOURS_COL]: 2 },
  { [STUDENT_COL]: "Grace Kim", [COURSE_COL]: "Cell Biology", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Grace Kim", [COURSE_COL]: "Machine Learning", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Grace Kim", [COURSE_COL]: "Statistics", [HOURS_COL]: 4 },
  { [STUDENT_COL]: "Omar Haddad", [COURSE_COL]: "Data Structures", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Omar Haddad", [COURSE_COL]: "Digital Design", [HOURS_COL]: 5 },
  { [STUDENT_COL]: "Isla Fraser", [COURSE_COL]: "Organic Chemistry", [HOURS_COL]: 5 },
  { [STUDENT_COL]: "Isla Fraser", [COURSE_COL]: "Cell Biology", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Victor Alves", [COURSE_COL]: "Linear Algebra", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Victor Alves", [COURSE_COL]: "Thermodynamics", [HOURS_COL]: 3 },
  { [STUDENT_COL]: "Victor Alves", [COURSE_COL]: "Digital Design", [HOURS_COL]: 3 },
  // Isolated entities with zero enrollments
  { [STUDENT_COL]: "Talia Novak", [COURSE_COL]: "", [HOURS_COL]: 0 },
  { [STUDENT_COL]: "", [COURSE_COL]: "Advanced Robotics", [HOURS_COL]: 0 },
];

// Derive unique students (Set A), courses (Set B), and active edges in appearance order
const students: string[] = [];
const courses: string[] = [];
const edges: Array<{ student: number; course: number; hours: number }> = [];

for (let i = 0; i < DATA.length; i++) {
  const sName = String(DATA[i][STUDENT_COL]);
  const cName = String(DATA[i][COURSE_COL]);
  if (sName && !students.includes(sName)) students.push(sName);
  if (cName && !courses.includes(cName)) courses.push(cName);
}

for (let i = 0; i < DATA.length; i++) {
  const sName = String(DATA[i][STUDENT_COL]);
  const cName = String(DATA[i][COURSE_COL]);
  const hours = Number(DATA[i][HOURS_COL]);
  if (sName && cName && hours > 0) {
    edges.push({
      student: students.indexOf(sName),
      course: courses.indexOf(cName),
      hours,
    });
  }
}

const minHours = Math.min(...edges.map((e) => e.hours));
const maxHours = Math.max(...edges.map((e) => e.hours));

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

// Initial degree order + barycenter crossing-reduction
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

const studentRadii = studentDegree.map((deg) =>
  deg === 0
    ? ISOLATED_R
    : NODE_MIN_R + ((deg - minDegree) / (maxDegree - minDegree || 1)) * (NODE_MAX_R - NODE_MIN_R),
);
const courseRadii = courseDegree.map((deg) =>
  deg === 0
    ? ISOLATED_R
    : NODE_MIN_R + ((deg - minDegree) / (maxDegree - minDegree || 1)) * (NODE_MAX_R - NODE_MIN_R),
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
      {/* Column headers */}
      <text
        x={studentX}
        y={top - 22}
        textAnchor="middle"
        fontSize={16}
        fontWeight={700}
        fill={t.palette[0]}
      >
        Students (Set A)
      </text>
      <text
        x={courseX}
        y={top - 22}
        textAnchor="middle"
        fontSize={16}
        fontWeight={700}
        fill={t.palette[1]}
      >
        Courses (Set B)
      </text>

      {/* Bipartite edges */}
      {edges.map((edge, i) => {
        const y1 = Number(yScale(1 - (studentRow[edge.student] + 0.5) / students.length));
        const y2 = Number(yScale(1 - (courseRow[edge.course] + 0.5) / courses.length));
        const hRatio = (edge.hours - minHours) / (maxHours - minHours || 1);
        const strokeW = EDGE_MIN_W + hRatio * (EDGE_MAX_W - EDGE_MIN_W);
        const strokeOp = 0.25 + hRatio * 0.45;
        const tooltip: HoverInfo = {
          label: `${students[edge.student]} → ${courses[edge.course]}`,
          detail: `${edge.hours} h/week`,
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

      {/* Student nodes (Set A) */}
      {students.map((label, i) => {
        const cy = Number(yScale(1 - (studentRow[i] + 0.5) / students.length));
        const r = studentRadii[i];
        const tooltip: HoverInfo = {
          label,
          detail: `${studentDegree[i]} course${studentDegree[i] === 1 ? "" : "s"}`,
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

      {/* Course nodes (Set B) */}
      {courses.map((label, i) => {
        const cy = Number(yScale(1 - (courseRow[i] + 0.5) / courses.length));
        const r = courseRadii[i];
        const tooltip: HoverInfo = {
          label,
          detail: `${courseDegree[i]} student${courseDegree[i] === 1 ? "" : "s"}`,
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

      {/* Interactive hover tooltip */}
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
            Students (Set A) · node size = enrolled courses
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
            Courses (Set B) · node size = enrolled students
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <span>Edge width = {HOURS_COL}:</span>
          {hourSamples.map((h) => {
            const hRatio = (h - minHours) / (maxHours - minHours || 1);
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
                <span>{h}h</span>
              </span>
            );
          })}
          <span>· Dashed outline = isolated node (0 enrollments)</span>
        </div>
      </div>
    </div>
  );
}
