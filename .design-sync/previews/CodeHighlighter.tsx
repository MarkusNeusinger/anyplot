import { CodeHighlighter } from 'anyplot';

// The anyplot imprint syntax theme across the four catalog languages. Each
// cell is a real plotting snippet in the brand's "first series is green"
// idiom — text-heavy on purpose so MonoLisa + the var(--code-*) token colors
// are visible.
const frame = (el: React.ReactNode) => <div style={{ maxWidth: 680, padding: 8 }}>{el}</div>;

export function Python() {
  return frame(
    <CodeHighlighter
      language="python"
      code={`import matplotlib.pyplot as plt
import numpy as np

# imprint palette — brand green is always the first series
phases = ["Render", "Parse", "Layout", "Paint", "Idle"]
ms = np.array([42, 31, 18, 12, 7])

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(phases, ms, color="#009E73")
ax.set_title("Frame budget by phase")
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("pareto.svg")`}
    />,
  );
}

export function RGgplot2() {
  return frame(
    <CodeHighlighter
      language="r"
      code={`library(ggplot2)

df <- data.frame(
  phase = c("Render", "Parse", "Layout", "Paint", "Idle"),
  ms    = c(42, 31, 18, 12, 7)
)

ggplot(df, aes(reorder(phase, -ms), ms)) +
  geom_col(fill = "#009E73") +
  labs(title = "Frame budget by phase", x = NULL, y = "ms") +
  theme_minimal(base_family = "MonoLisa")`}
    />,
  );
}

export function JuliaMakie() {
  return frame(
    <CodeHighlighter
      language="julia"
      code={`using CairoMakie

phases = ["Render", "Parse", "Layout", "Paint", "Idle"]
ms = [42, 31, 18, 12, 7]

fig = Figure(size = (800, 500))
ax = Axis(fig[1, 1], title = "Frame budget by phase")
barplot!(ax, 1:length(ms), ms; color = "#009E73")
ax.xticks = (1:length(phases), phases)
save("pareto.svg", fig)`}
    />,
  );
}

export function MuiXReact() {
  return frame(
    <CodeHighlighter
      language="javascript"
      library="muix"
      code={`import { BarChart } from '@mui/x-charts/BarChart';

const phases = ['Render', 'Parse', 'Layout', 'Paint', 'Idle'];
const ms = [42, 31, 18, 12, 7];

export default function FrameBudget() {
  return (
    <BarChart
      xAxis={[{ data: phases, scaleType: 'band' }]}
      series={[{ data: ms, color: '#009E73' }]}
      height={320}
    />
  );
}`}
    />,
  );
}
