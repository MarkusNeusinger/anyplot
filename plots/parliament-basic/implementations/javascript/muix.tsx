// anyplot.ai
// parliament-basic: Parliament Seat Chart
// Library: muix 9.x | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-02

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "parliament-basic · javascript · muix · anyplot.ai";
const TITLE_FONT_SIZE = 22;
const TITLE_H = 44;
const LEGEND_H = 38;
const OUTER_R = 628;
const INNER_R = 252;
const TOP_PAD_SHARE = 0.14;
const BOTTOM_PAD_SHARE = 0.13;
const X_PAD_SHARE = 0.12;

const PARTY_COL = "party_name";
const SEATS_COL = "seat_count";

// Data: fictional chamber assembly with neutral party names (flat scalar records)
const DATA: Array<Record<string, string | number>> = [
  { party_name: "Harbor Guild", seat_count: 24 },
  { party_name: "Meadow Union", seat_count: 38 },
  { party_name: "Lantern League", seat_count: 52 },
  { party_name: "Bridge Assembly", seat_count: 46 },
  { party_name: "Granite Circle", seat_count: 28 },
  { party_name: "Orchard Compact", seat_count: 12 },
];

const parties = DATA.map((row, idx) => ({
  name: String(row[PARTY_COL]),
  seats: Number(row[SEATS_COL]),
  color: t.palette[idx],
}));

const totalSeats = parties.reduce((sum, p) => sum + p.seats, 0);
const majoritySeats = Math.floor(totalSeats / 2) + 1;

// Concentric semicircular arcs with seat count proportional to arc length
const rowCount = Math.min(9, Math.max(3, Math.round(Math.sqrt(totalSeats / 6))));
const rowRadii = Array.from({ length: rowCount }, (_, i) =>
  rowCount === 1 ? OUTER_R : INNER_R + (i * (OUTER_R - INNER_R)) / (rowCount - 1),
);
const radiusSum = rowRadii.reduce((sum, r) => sum + r, 0);
const rowCapacities = rowRadii.map((r) => Math.max(1, Math.round((totalSeats * r) / radiusSum)));
const capacityDrift = totalSeats - rowCapacities.reduce((sum, c) => sum + c, 0);
rowCapacities[rowCount - 1] += capacityDrift;

interface SeatSlot {
  r: number;
  theta: number;
  x: number;
  y: number;
}

const slots: SeatSlot[] = [];
for (let rowIndex = 0; rowIndex < rowRadii.length; rowIndex += 1) {
  const r = rowRadii[rowIndex];
  const capacity = rowCapacities[rowIndex];
  for (let j = 0; j < capacity; j += 1) {
    // theta from pi (left) to 0 (right) so seats order naturally left-to-right
    const theta = Math.PI - ((j + 0.5) / capacity) * Math.PI;
    slots.push({ r, theta, x: r * Math.cos(theta), y: r * Math.sin(theta) });
  }
}
slots.sort((a, b) => b.theta - a.theta || a.r - b.r);

interface AssignedSeat extends SeatSlot {
  partyIndex: number;
}

const assignedSeats: AssignedSeat[] = [];
let cursor = 0;
for (let partyIndex = 0; partyIndex < parties.length; partyIndex += 1) {
  const count = parties[partyIndex].seats;
  for (let i = 0; i < count; i += 1) {
    if (cursor < slots.length) {
      assignedSeats.push({ ...slots[cursor], partyIndex });
      cursor += 1;
    }
  }
}

const rowRadialGap = rowCount > 1 ? (OUTER_R - INNER_R) / (rowCount - 1) : OUTER_R - INNER_R;
const minAngularSpacing = Math.min(...rowRadii.map((r, i) => (r * Math.PI) / rowCapacities[i]));
const seatDataRadius = 0.42 * Math.min(rowRadialGap, minAngularSpacing);

// Majority threshold angle bisecting seat majoritySeats - 1 and majoritySeats
const majorityLower = slots[majoritySeats - 1];
const majorityUpper = slots[majoritySeats] ?? majorityLower;
const majorityTheta = (majorityLower.theta + majorityUpper.theta) / 2;

const topPad = OUTER_R * TOP_PAD_SHARE;
const bottomPad = OUTER_R * BOTTOM_PAD_SHARE;
const xPad = OUTER_R * X_PAD_SHARE;
const domain = {
  xMin: -(OUTER_R + xPad),
  xMax: OUTER_R + xPad,
  yMin: -bottomPad,
  yMax: OUTER_R + topPad,
};
const domainWidth = domain.xMax - domain.xMin;
const domainHeight = domain.yMax - domain.yMin;

function ParliamentOverlay() {
  const xScale = useXScale();
  const yScale = useYScale();

  const pxRadius = Math.abs(xScale(seatDataRadius) - xScale(0));
  const innerX = (INNER_R * 0.28) * Math.cos(majorityTheta);
  const innerY = (INNER_R * 0.28) * Math.sin(majorityTheta);
  const outerX = (OUTER_R + topPad * 0.48) * Math.cos(majorityTheta);
  const outerY = (OUTER_R + topPad * 0.48) * Math.sin(majorityTheta);
  const labelX = (OUTER_R + topPad * 0.8) * Math.cos(majorityTheta);
  const labelY = (OUTER_R + topPad * 0.8) * Math.sin(majorityTheta);

  return (
    <g data-drawing-container>
      {assignedSeats.map((seat, i) => (
        <circle
          key={`seat-${i}`}
          cx={xScale(seat.x)}
          cy={yScale(seat.y)}
          r={pxRadius}
          fill={parties[seat.partyIndex].color}
          stroke={t.pageBg}
          strokeWidth={1}
        />
      ))}
      <line
        x1={xScale(innerX)}
        y1={yScale(innerY)}
        x2={xScale(outerX)}
        y2={yScale(outerY)}
        stroke={t.ink}
        strokeOpacity={0.45}
        strokeWidth={1.5}
        strokeDasharray="7,6"
      />
      <text x={xScale(labelX)} y={yScale(labelY)} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
        {`Majority · ${majoritySeats}`}
      </text>
      <text
        x={xScale(0)}
        y={yScale(-bottomPad * 0.45)}
        textAnchor="middle"
        fontSize={16}
        fontWeight={500}
        fill={t.ink}
      >
        {`${totalSeats} seats`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const availW = width;
  const availH = height - TITLE_H - LEGEND_H;

  // Enforce exact 1:1 px/unit scale so the chamber arc is a true semicircle
  const margin = 12;
  const maxDrawW = availW - margin * 2;
  const maxDrawH = availH - margin * 2;
  const pxPerUnit = Math.min(maxDrawW / domainWidth, maxDrawH / domainHeight);
  const drawW = Math.round(domainWidth * pxPerUnit);
  const drawH = Math.round(domainHeight * pxPerUnit);
  const hPad = Math.max(margin, Math.floor((availW - drawW) / 2));
  const vPad = Math.max(margin, Math.floor((availH - drawH) / 2));

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
          height: `${TITLE_H}px`,
          lineHeight: `${TITLE_H}px`,
          fontSize: `${TITLE_FONT_SIZE}px`,
          fontWeight: 600,
          color: t.ink,
          paddingLeft: "24px",
        }}
      >
        {TITLE}
      </div>
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          gap: "18px",
          flexWrap: "wrap",
          paddingLeft: "24px",
        }}
      >
        {parties.map((party) => (
          <div key={party.name} style={{ display: "flex", alignItems: "center", gap: "7px" }}>
            <span
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                backgroundColor: party.color,
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: "14px", color: t.inkSoft }}>
              {party.name} ({party.seats})
            </span>
          </div>
        ))}
      </div>
      <ChartsContainer
        width={availW}
        height={availH}
        series={[]}
        margin={{ top: vPad, bottom: availH - drawH - vPad, left: hPad, right: availW - drawW - hPad }}
        xAxis={[{ id: "x", scaleType: "linear", min: domain.xMin, max: domain.xMax, position: "none" }]}
        yAxis={[{ id: "y", scaleType: "linear", min: domain.yMin, max: domain.yMax, position: "none" }]}
        skipAnimation
      >
        <ParliamentOverlay />
      </ChartsContainer>
    </div>
  );
}
