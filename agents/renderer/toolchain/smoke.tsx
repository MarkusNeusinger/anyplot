// The toolchain build's check of the JavaScript row's React path (agents/renderer/toolchain.Dockerfile):
// esbuild bundles a MUI X component with React and MUI from the image's packages, and the harness mounts it.
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;

export default function Chart() {
  return (
    <BarChart
      width={window.ANYPLOT_SIZE.width}
      height={window.ANYPLOT_SIZE.height}
      colors={t.palette}
      skipAnimation
      xAxis={[{ scaleType: "band", data: ["a", "b", "c"] }]}
      series={[{ data: [3, 1, 2], label: "Größe" }]}
    />
  );
}
