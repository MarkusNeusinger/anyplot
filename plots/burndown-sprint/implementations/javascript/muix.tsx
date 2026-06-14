// anyplot.ai
// burndown-sprint: Agile Sprint Burndown Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-14

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts";

const t = window.ANYPLOT_TOKENS;

// Sprint: start state + 10 working days (2 weeks Mon–Fri)
// Scope change: +8 story points added by stakeholder on Thu of Week 1 (Day 4)
const days = [
  "Start",
  "Mon 1", "Tue 2", "Wed 3", "Thu 4", "Fri 5",
  "Mon 8", "Tue 9", "Wed 10", "Thu 11", "Fri 12",
];

// Remaining story points recorded at end of each day.
// Thu 4: team completed 2 pts but +8 scope added → jump from 32 to 38
const actual = [40, 37, 34, 32, 38, 34, 28, 21, 14, 7, 2];

// Ideal burndown: straight line from 40 → 0 across 10 working days (4 pts/day)
const ideal = [40, 36, 32, 28, 24, 20, 16, 12, 8, 4, 0];

const TITLE_H = 60;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        overflow: "hidden",
        boxSizing: "border-box",
        fontFamily: "'Roboto', 'Helvetica Neue', Arial, sans-serif",
      }}
    >
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          paddingLeft: 28,
          paddingRight: 28,
        }}
      >
        <span
          style={{
            color: t.ink,
            fontSize: 22,
            fontWeight: 500,
            letterSpacing: 0.3,
          }}
        >
          burndown-sprint · javascript · muix · anyplot.ai
        </span>
      </div>

      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        xAxis={[{
          scaleType: "band",
          data: days,
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
        }]}
        yAxis={[{
          label: "Story Points Remaining",
          min: 0,
          max: 48,
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
          labelStyle: { fontSize: 15, fill: t.ink },
        }]}
        series={[
          {
            id: "actual",
            data: actual,
            label: "Actual Remaining",
            curve: "step",
            showMark: true,
            color: t.palette[0],
          },
          {
            id: "ideal",
            data: ideal,
            label: "Ideal Burndown",
            curve: "linear",
            showMark: false,
            color: t.inkSoft,
          },
        ]}
        sx={{
          "& .MuiLineElement-series-ideal": {
            strokeDasharray: "10 6",
            strokeOpacity: 0.6,
          },
          "& .MuiLineElement-series-actual": {
            strokeWidth: 3,
          },
          "& .MuiMarkElement-series-actual": {
            strokeWidth: 2,
          },
        }}
        slotProps={{
          legend: {
            itemMarkWidth: 20,
            itemMarkHeight: 3,
            markGap: 8,
            itemGap: 24,
            labelStyle: { fontSize: 14, fill: t.ink },
          },
        }}
      >
        <ChartsReferenceLine
          x="Thu 4"
          label="Scope +8 pts"
          lineStyle={{
            stroke: t.palette[3],
            strokeWidth: 2,
            strokeDasharray: "5 4",
          }}
          labelStyle={{
            fill: t.palette[3],
            fontSize: 13,
            fontWeight: 500,
          }}
        />
      </LineChart>
    </div>
  );
}
