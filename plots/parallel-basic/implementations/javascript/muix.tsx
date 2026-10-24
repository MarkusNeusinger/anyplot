// anyplot.ai
// parallel-basic: Basic Parallel Coordinates Plot
// Library: muix 9.x | JavaScript 22.23.1
// Quality: 92/100 | Created: 2026-07-24

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FONT = "Inter, system-ui, -apple-system, sans-serif";
const TITLE = "parallel-basic · javascript · muix · anyplot.ai";
const TITLE_H = 64;
const TICK_FRACTIONS = [0, 0.5, 1];
const DIM_PAD_SHARE = 0.08;

const ARCH_COL = "architecture";
const BATCH_COL = "batch_size";
const LAYERS_COL = "hidden_layers";
const DROPOUT_COL = "dropout_pct";
const ACCURACY_COL = "val_accuracy_pct";
const TIME_COL = "train_time_min";

// Data: 30 model-training runs across 3 architectures on 5 dimensions (flat scalar records)
const DATA: Array<Record<string, string | number>> = [
  // CNN runs
  { architecture: "CNN", batch_size: 84, hidden_layers: 4, dropout_pct: 12, val_accuracy_pct: 84, train_time_min: 68 },
  { architecture: "CNN", batch_size: 108, hidden_layers: 5, dropout_pct: 16, val_accuracy_pct: 88, train_time_min: 82 },
  { architecture: "CNN", batch_size: 72, hidden_layers: 3, dropout_pct: 9, val_accuracy_pct: 81, train_time_min: 56 },
  { architecture: "CNN", batch_size: 124, hidden_layers: 5, dropout_pct: 18, val_accuracy_pct: 86, train_time_min: 91 },
  { architecture: "CNN", batch_size: 96, hidden_layers: 4, dropout_pct: 14, val_accuracy_pct: 85, train_time_min: 74 },
  { architecture: "CNN", batch_size: 64, hidden_layers: 3, dropout_pct: 8, val_accuracy_pct: 79, train_time_min: 52 },
  { architecture: "CNN", batch_size: 116, hidden_layers: 5, dropout_pct: 15, val_accuracy_pct: 89, train_time_min: 86 },
  { architecture: "CNN", batch_size: 88, hidden_layers: 4, dropout_pct: 11, val_accuracy_pct: 83, train_time_min: 64 },
  { architecture: "CNN", batch_size: 104, hidden_layers: 4, dropout_pct: 13, val_accuracy_pct: 87, train_time_min: 78 },
  { architecture: "CNN", batch_size: 78, hidden_layers: 3, dropout_pct: 10, val_accuracy_pct: 82, train_time_min: 60 },

  // RNN runs
  { architecture: "RNN", batch_size: 48, hidden_layers: 2, dropout_pct: 28, val_accuracy_pct: 71, train_time_min: 118 },
  { architecture: "RNN", batch_size: 64, hidden_layers: 3, dropout_pct: 34, val_accuracy_pct: 75, train_time_min: 136 },
  { architecture: "RNN", batch_size: 36, hidden_layers: 2, dropout_pct: 24, val_accuracy_pct: 68, train_time_min: 104 },
  { architecture: "RNN", batch_size: 80, hidden_layers: 4, dropout_pct: 38, val_accuracy_pct: 77, train_time_min: 148 },
  { architecture: "RNN", batch_size: 56, hidden_layers: 3, dropout_pct: 31, val_accuracy_pct: 73, train_time_min: 126 },
  { architecture: "RNN", batch_size: 32, hidden_layers: 2, dropout_pct: 22, val_accuracy_pct: 66, train_time_min: 98 },
  { architecture: "RNN", batch_size: 72, hidden_layers: 3, dropout_pct: 35, val_accuracy_pct: 76, train_time_min: 142 },
  { architecture: "RNN", batch_size: 52, hidden_layers: 2, dropout_pct: 26, val_accuracy_pct: 70, train_time_min: 112 },
  { architecture: "RNN", batch_size: 68, hidden_layers: 3, dropout_pct: 32, val_accuracy_pct: 74, train_time_min: 132 },
  { architecture: "RNN", batch_size: 44, hidden_layers: 2, dropout_pct: 25, val_accuracy_pct: 69, train_time_min: 108 },

  // Transformer runs
  { architecture: "Transformer", batch_size: 184, hidden_layers: 6, dropout_pct: 15, val_accuracy_pct: 92, train_time_min: 146 },
  { architecture: "Transformer", batch_size: 216, hidden_layers: 7, dropout_pct: 20, val_accuracy_pct: 96, train_time_min: 164 },
  { architecture: "Transformer", batch_size: 168, hidden_layers: 6, dropout_pct: 12, val_accuracy_pct: 90, train_time_min: 134 },
  { architecture: "Transformer", batch_size: 236, hidden_layers: 8, dropout_pct: 22, val_accuracy_pct: 97, train_time_min: 174 },
  { architecture: "Transformer", batch_size: 196, hidden_layers: 7, dropout_pct: 18, val_accuracy_pct: 94, train_time_min: 154 },
  { architecture: "Transformer", batch_size: 160, hidden_layers: 5, dropout_pct: 11, val_accuracy_pct: 89, train_time_min: 128 },
  { architecture: "Transformer", batch_size: 224, hidden_layers: 7, dropout_pct: 19, val_accuracy_pct: 95, train_time_min: 168 },
  { architecture: "Transformer", batch_size: 180, hidden_layers: 6, dropout_pct: 14, val_accuracy_pct: 91, train_time_min: 140 },
  { architecture: "Transformer", batch_size: 208, hidden_layers: 7, dropout_pct: 17, val_accuracy_pct: 95, train_time_min: 160 },
  { architecture: "Transformer", batch_size: 172, hidden_layers: 6, dropout_pct: 13, val_accuracy_pct: 91, train_time_min: 138 },
];

// Derive architectures in order of first appearance
const architectures: string[] = [];
for (const row of DATA) {
  const arch = String(row[ARCH_COL]);
  if (!architectures.includes(arch)) architectures.push(arch);
}

const archColorMap: Record<string, string> = {};
for (let i = 0; i < architectures.length; i += 1) {
  archColorMap[architectures[i]] = t.palette[i];
}

const dimensionSpecs = [
  { col: BATCH_COL, label: "Batch Size", unitSuffix: "" },
  { col: LAYERS_COL, label: "Hidden Layers", unitSuffix: "" },
  { col: DROPOUT_COL, label: "Dropout (%)", unitSuffix: "%" },
  { col: ACCURACY_COL, label: "Val Accuracy (%)", unitSuffix: "%" },
  { col: TIME_COL, label: "Train Time (min)", unitSuffix: "" },
];

interface DimensionConfig {
  col: string;
  label: string;
  unitSuffix: string;
  min: number;
  max: number;
}

const dimensions: DimensionConfig[] = dimensionSpecs.map((spec) => {
  const vals = DATA.map((r) => Number(r[spec.col]));
  const rawMin = Math.min(...vals);
  const rawMax = Math.max(...vals);
  const pad = (rawMax - rawMin || 1) * DIM_PAD_SHARE;
  return {
    col: spec.col,
    label: spec.label,
    unitSuffix: spec.unitSuffix,
    min: Math.floor(rawMin - pad),
    max: Math.ceil(rawMax + pad),
  };
});

function ParallelCoordinatesOverlay() {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();

  return (
    <g fontFamily={FONT}>
      {/* Polylines for each model-training run */}
      <g fill="none" strokeWidth={1.8} strokeOpacity={0.58}>
        {DATA.map((row, i) => {
          const arch = String(row[ARCH_COL]);
          const points = dimensions
            .map((dim, dIdx) => {
              const val = Number(row[dim.col]);
              const fraction = (val - dim.min) / (dim.max - dim.min || 1);
              const x = xScale(dIdx);
              const y = top + height * (1 - fraction);
              return `${x},${y}`;
            })
            .join(" ");
          return <polyline key={i} points={points} stroke={archColorMap[arch]} />;
        })}
      </g>

      {/* Parallel vertical axes, tick marks, and tick labels */}
      {dimensions.map((dim, i) => {
        const x = xScale(i);
        return (
          <g key={dim.col}>
            <line x1={x} y1={top} x2={x} y2={top + height} stroke={t.inkSoft} strokeWidth={1.5} />
            {TICK_FRACTIONS.map((f) => {
              const y = top + height * (1 - f);
              const value = Math.round(dim.min + f * (dim.max - dim.min));
              const formatted = `${value}${dim.unitSuffix}`;
              return (
                <g key={f}>
                  <line x1={x - 6} y1={y} x2={x + 6} y2={y} stroke={t.inkSoft} strokeWidth={1.5} />
                  <rect
                    x={x + 8}
                    y={y - 10}
                    width={formatted.length * 8.4 + 8}
                    height={20}
                    rx={3}
                    fill={t.pageBg}
                    fillOpacity={0.86}
                  />
                  <text x={x + 12} y={y} fontSize={14} fill={t.inkSoft} dominantBaseline="middle">
                    {formatted}
                  </text>
                </g>
              );
            })}
            <text x={x} y={top - 18} fontSize={15} fontWeight={600} fill={t.ink} textAnchor="middle">
              {dim.label}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const N = dimensions.length;

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
          justifyContent: "space-between",
          padding: "0 90px",
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
          {architectures.map((archName) => (
            <div key={archName} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  backgroundColor: archColorMap[archName],
                  display: "inline-block",
                }}
              />
              <span style={{ fontSize: 15, color: t.ink }}>{archName}</span>
            </div>
          ))}
        </div>
      </div>
      <ChartsContainer
        width={W}
        height={H - TITLE_H}
        skipAnimation
        series={[]}
        margin={{ top: 56, right: 100, bottom: 36, left: 90 }}
        xAxis={[{ scaleType: "linear", min: 0, max: N - 1, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: 0, max: 1, position: "none" }]}
      >
        <ParallelCoordinatesOverlay />
      </ChartsContainer>
    </div>
  );
}
