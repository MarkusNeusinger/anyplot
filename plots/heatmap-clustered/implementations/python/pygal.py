""" pyplots.ai
heatmap-clustered: Clustered Heatmap
Library: pygal 3.1.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-25
"""

import sys

import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


# Temporarily remove current directory from path to avoid name collision
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path
sys.path.insert(0, _cwd)


class ClusteredHeatmap(Graph):
    """Custom Clustered Heatmap for pygal - displays matrix with hierarchical clustering dendrograms."""

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.colormap = kwargs.pop("colormap", [])
        self.show_values = kwargs.pop("show_values", False)
        self.row_linkage = kwargs.pop("row_linkage", None)
        self.col_linkage = kwargs.pop("col_linkage", None)
        self.row_order = kwargs.pop("row_order", None)
        self.col_order = kwargs.pop("col_order", None)
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value, min_val, max_val):
        """Interpolate color for diverging colormap."""
        if max_val == min_val:
            return self.colormap[len(self.colormap) // 2]

        # Normalize value to 0-1 range
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0, min(1, normalized))

        # Get position in colormap
        pos = normalized * (len(self.colormap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(self.colormap) - 1)
        frac = pos - idx1

        # Interpolate between colors
        c1 = self.colormap[idx1]
        c2 = self.colormap[idx2]

        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)

        r = int(r1 + (r2 - r1) * frac)
        g = int(g1 + (g2 - g1) * frac)
        b = int(b1 + (b2 - b1) * frac)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_text_color(self, bg_color):
        """Get contrasting text color based on background brightness."""
        r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 140 else "#333333"

    def _draw_dendrogram(self, group, linkage_matrix, x_offset, y_offset, width, height, orientation="left"):
        """Draw dendrogram from hierarchical clustering linkage matrix."""
        if linkage_matrix is None or len(linkage_matrix) == 0:
            return

        # Get dendrogram data without plotting
        dend = dendrogram(linkage_matrix, no_plot=True, orientation=orientation)

        # Extract coordinates
        icoord = np.array(dend["icoord"])  # x coordinates
        dcoord = np.array(dend["dcoord"])  # y coordinates (distance)

        # Normalize coordinates
        max_d = dcoord.max() if dcoord.max() > 0 else 1
        n_leaves = len(dend["leaves"])

        for i in range(len(icoord)):
            if orientation in ("left", "right"):
                # Vertical dendrogram - swap x and y
                xs = dcoord[i] / max_d * width
                ys = (icoord[i] / (n_leaves * 10)) * height

                if orientation == "left":
                    xs = width - xs  # Flip for left side

                # Build path
                path_data = f"M {x_offset + xs[0]} {y_offset + ys[0]} "
                for j in range(1, 4):
                    path_data += f"L {x_offset + xs[j]} {y_offset + ys[j]} "

            else:  # top or bottom
                # Horizontal dendrogram
                xs = (icoord[i] / (n_leaves * 10)) * width
                ys = dcoord[i] / max_d * height

                if orientation == "top":
                    ys = height - ys  # Flip for top

                # Build path
                path_data = f"M {x_offset + xs[0]} {y_offset + ys[0]} "
                for j in range(1, 4):
                    path_data += f"L {x_offset + xs[j]} {y_offset + ys[j]} "

            path = self.svg.node(group, "path")
            path.set("d", path_data)
            path.set("fill", "none")
            path.set("stroke", "#333333")
            path.set("stroke-width", "2")

    def _plot(self):
        """Draw the clustered heatmap with dendrograms."""
        if not self.matrix_data:
            return

        # Reorder matrix according to clustering
        matrix = np.array(self.matrix_data)
        if self.row_order is not None:
            matrix = matrix[self.row_order, :]
            reordered_row_labels = [self.row_labels[i] for i in self.row_order]
        else:
            reordered_row_labels = self.row_labels

        if self.col_order is not None:
            matrix = matrix[:, self.col_order]
            reordered_col_labels = [self.col_labels[i] for i in self.col_order]
        else:
            reordered_col_labels = self.col_labels

        n_rows, n_cols = matrix.shape

        # Find value range
        min_val = matrix.min()
        max_val = matrix.max()
        # Center around zero for diverging colormap
        abs_max = max(abs(min_val), abs(max_val))
        min_val, max_val = -abs_max, abs_max

        # Get plot dimensions
        plot_width = self.view.width
        plot_height = self.view.height

        # Layout: [axis_label][row_dend][row_labels][heatmap][colorbar]
        #                                          [col_dend]
        #                                          [col_labels]
        #                                          [axis_label]
        axis_label_width = 80  # Space for "Genes" label
        row_dend_width = 280  # Width for row dendrogram
        col_dend_height = 180  # Height for column dendrogram
        label_margin_left = 280  # Space for row labels
        label_margin_bottom = 300  # Increased for rotated column labels + axis label
        label_margin_top = 80  # Space for title
        colorbar_width = 180  # Tighter colorbar for better integration

        # Heatmap area - adjusted for axis labels and wider dendrogram
        heatmap_x = axis_label_width + row_dend_width + label_margin_left
        heatmap_width = plot_width - heatmap_x - colorbar_width - 20  # Small right margin
        heatmap_height = plot_height - col_dend_height - label_margin_bottom - label_margin_top

        cell_width = heatmap_width / n_cols
        cell_height = heatmap_height / n_rows

        # Create group for the heatmap
        plot_node = self.nodes["plot"]
        heatmap_group = self.svg.node(plot_node, class_="clustered-heatmap")

        # Draw row dendrogram (left side) - positioned with more space
        self._draw_dendrogram(
            heatmap_group,
            self.row_linkage,
            self.view.x(0) + axis_label_width + 40,  # Account for axis label
            self.view.y(n_rows) + label_margin_top,
            row_dend_width - 40,  # Slightly narrower to fit after axis label
            heatmap_height,
            orientation="left",
        )

        # Draw column dendrogram (top)
        self._draw_dendrogram(
            heatmap_group,
            self.col_linkage,
            self.view.x(0) + heatmap_x,
            self.view.y(n_rows) + heatmap_height + label_margin_top + 10,
            heatmap_width,
            col_dend_height,
            orientation="bottom",
        )

        # Draw row labels
        row_font_size = min(38, int(cell_height * 0.7))
        for i, label in enumerate(reordered_row_labels):
            x = self.view.x(0) + heatmap_x - 15
            y = self.view.y(n_rows) + label_margin_top + i * cell_height + cell_height / 2
            text_node = self.svg.node(heatmap_group, "text", x=x, y=y + row_font_size * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{row_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.text = label

        # Draw column labels (rotated at 45 degrees for optimal readability)
        col_font_size = min(30, int(cell_width * 0.5))
        for j, label in enumerate(reordered_col_labels):
            x = self.view.x(0) + heatmap_x + j * cell_width + cell_width / 2
            y = self.view.y(n_rows) + label_margin_top + heatmap_height + col_dend_height + 25
            text_node = self.svg.node(heatmap_group, "text", x=x, y=y)
            text_node.set("text-anchor", "start")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{col_font_size}px;font-weight:600;font-family:sans-serif")
            # Use 45 degree rotation for less cramped, more readable labels
            text_node.set("transform", f"rotate(45, {x}, {y})")
            text_node.text = label

        # Draw heatmap cells
        value_font_size = min(28, int(min(cell_width, cell_height) * 0.35))
        for i in range(n_rows):
            for j in range(n_cols):
                value = matrix[i, j]
                color = self._interpolate_color(value, min_val, max_val)

                x = self.view.x(0) + heatmap_x + j * cell_width
                y = self.view.y(n_rows) + label_margin_top + i * cell_height

                # Draw cell rectangle
                rect = self.svg.node(
                    heatmap_group, "rect", x=x, y=y, width=cell_width - 1, height=cell_height - 1, rx=2, ry=2
                )
                rect.set("fill", color)
                rect.set("stroke", "#ffffff")
                rect.set("stroke-width", "1")

                # Add value annotation if enabled
                if self.show_values:
                    text_color = self._get_text_color(color)
                    text_x = x + cell_width / 2
                    text_y = y + cell_height / 2 + value_font_size * 0.35

                    text_node = self.svg.node(heatmap_group, "text", x=text_x, y=text_y)
                    text_node.set("text-anchor", "middle")
                    text_node.set("fill", text_color)
                    text_node.set("style", f"font-size:{value_font_size}px;font-weight:bold;font-family:sans-serif")
                    text_node.text = f"{value:.1f}"

        # Draw colorbar on the right - positioned closer to heatmap for better integration
        colorbar_bar_width = 45
        colorbar_height = heatmap_height * 0.75
        colorbar_x = self.view.x(0) + heatmap_x + heatmap_width + 40
        colorbar_y = self.view.y(n_rows) + label_margin_top + (heatmap_height - colorbar_height) / 2

        # Draw gradient colorbar
        n_segments = 60
        segment_height = colorbar_height / n_segments
        for seg_i in range(n_segments):
            seg_value = max_val - (max_val - min_val) * seg_i / (n_segments - 1)
            seg_color = self._interpolate_color(seg_value, min_val, max_val)
            seg_y = colorbar_y + seg_i * segment_height

            self.svg.node(
                heatmap_group,
                "rect",
                x=colorbar_x,
                y=seg_y,
                width=colorbar_bar_width,
                height=segment_height + 1,
                fill=seg_color,
            )

        # Colorbar border
        self.svg.node(
            heatmap_group,
            "rect",
            x=colorbar_x,
            y=colorbar_y,
            width=colorbar_bar_width,
            height=colorbar_height,
            fill="none",
            stroke="#333333",
        )

        # Colorbar labels - positioned next to bar with proper spacing
        cb_label_size = 32
        for val, y_pos in [
            (max_val, colorbar_y),
            (0, colorbar_y + colorbar_height / 2),
            (min_val, colorbar_y + colorbar_height),
        ]:
            text_node = self.svg.node(
                heatmap_group, "text", x=colorbar_x + colorbar_bar_width + 12, y=y_pos + cb_label_size * 0.35
            )
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
            text_node.text = f"{val:+.1f}"

        # Colorbar title - positioned above the bar
        cb_title_size = 36
        cb_title_x = colorbar_x + colorbar_bar_width / 2
        cb_title_y = colorbar_y - 25
        text_node = self.svg.node(heatmap_group, "text", x=cb_title_x, y=cb_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Z-Score"

        # Axis label: "Genes" (left side, rotated 90 degrees)
        axis_label_size = 48
        genes_label_x = self.view.x(0) + 50
        genes_label_y = self.view.y(n_rows) + label_margin_top + heatmap_height / 2
        genes_text = self.svg.node(heatmap_group, "text", x=genes_label_x, y=genes_label_y)
        genes_text.set("text-anchor", "middle")
        genes_text.set("fill", "#333333")
        genes_text.set("style", f"font-size:{axis_label_size}px;font-weight:bold;font-family:sans-serif")
        genes_text.set("transform", f"rotate(-90, {genes_label_x}, {genes_label_y})")
        genes_text.text = "Genes"

        # Axis label: "Samples" (bottom, horizontal) - positioned with proper spacing
        samples_label_x = self.view.x(0) + heatmap_x + heatmap_width / 2
        samples_label_y = (
            self.view.y(n_rows) + label_margin_top + heatmap_height + col_dend_height + label_margin_bottom - 40
        )
        samples_text = self.svg.node(heatmap_group, "text", x=samples_label_x, y=samples_label_y)
        samples_text.set("text-anchor", "middle")
        samples_text.set("fill", "#333333")
        samples_text.set("style", f"font-size:{axis_label_size}px;font-weight:bold;font-family:sans-serif")
        samples_text.text = "Samples"

    def _compute(self):
        """Compute the box for rendering."""
        n_rows = len(self.matrix_data) if self.matrix_data else 1
        n_cols = len(self.matrix_data[0]) if self.matrix_data and len(self.matrix_data) > 0 else 1
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# Data: Gene expression analysis (classic bioinformatics use case)
np.random.seed(42)

# Gene names (12 genes)
genes = ["BRCA1", "TP53", "MYC", "EGFR", "VEGFA", "KRAS", "AKT1", "PTEN", "PIK3CA", "CDKN2A", "RB1", "ERBB2"]

# Sample names (10 samples)
samples = [
    "Tumor_A1",
    "Tumor_A2",
    "Tumor_B1",
    "Tumor_B2",
    "Tumor_B3",
    "Normal_C1",
    "Normal_C2",
    "Normal_C3",
    "Normal_D1",
    "Normal_D2",
]

# Create gene expression data with clear cluster structure
# Group 1: Tumor samples (upregulated in oncogenes)
# Group 2: Normal samples (baseline expression)
n_genes = len(genes)
n_samples = len(samples)

# Create expression matrix with meaningful patterns
expression_data = np.zeros((n_genes, n_samples))

# Tumor suppressor genes (BRCA1, TP53, PTEN, CDKN2A, RB1) - downregulated in tumors
tumor_suppressors = [0, 1, 7, 9, 10]
for i in tumor_suppressors:
    expression_data[i, :5] = np.random.randn(5) * 0.5 - 1.5  # Tumors: low
    expression_data[i, 5:] = np.random.randn(5) * 0.5 + 0.5  # Normal: baseline

# Oncogenes (MYC, EGFR, KRAS, AKT1, PIK3CA, ERBB2) - upregulated in tumors
oncogenes = [2, 3, 5, 6, 8, 11]
for i in oncogenes:
    expression_data[i, :5] = np.random.randn(5) * 0.5 + 1.8  # Tumors: high
    expression_data[i, 5:] = np.random.randn(5) * 0.5 - 0.3  # Normal: baseline

# VEGFA - angiogenesis marker, highly variable
expression_data[4, :5] = np.random.randn(5) * 0.8 + 1.2
expression_data[4, 5:] = np.random.randn(5) * 0.6 - 0.2

# Perform hierarchical clustering
row_linkage = linkage(pdist(expression_data), method="ward")
col_linkage = linkage(pdist(expression_data.T), method="ward")

# Get leaf ordering from dendrograms
row_dend = dendrogram(row_linkage, no_plot=True)
col_dend = dendrogram(col_linkage, no_plot=True)
row_order = row_dend["leaves"]
col_order = col_dend["leaves"]

# Convert to list format
matrix_data = expression_data.tolist()

# Custom style for 3600x3600 square canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=64,
    legend_font_size=44,
    label_font_size=40,
    value_font_size=32,
    font_family="sans-serif",
)

# Colorblind-friendly diverging colormap: purple (low) -> white (zero) -> green (high)
# Based on ColorBrewer PRGn (Purple-Green) which is colorblind-safe
diverging_colormap = [
    "#40004b",  # Dark purple (negative)
    "#762a83",
    "#9970ab",
    "#c2a5cf",
    "#e7d4e8",
    "#f7f7f7",  # White (zero)
    "#d9f0d3",
    "#a6dba0",
    "#5aae61",
    "#1b7837",
    "#00441b",  # Dark green (positive)
]

# Create clustered heatmap
chart = ClusteredHeatmap(
    width=3600,
    height=3600,
    style=custom_style,
    title="heatmap-clustered · pygal · pyplots.ai",
    matrix_data=matrix_data,
    row_labels=genes,
    col_labels=samples,
    colormap=diverging_colormap,
    row_linkage=row_linkage,
    col_linkage=col_linkage,
    row_order=row_order,
    col_order=col_order,
    show_values=False,
    show_legend=False,
    margin=100,  # Base margin
    margin_top=180,  # Space for title
    margin_bottom=80,  # Space at bottom
    margin_left=60,  # Account for genes axis label
    show_x_labels=False,
    show_y_labels=False,
)

# Add a dummy series to trigger _plot
chart.add("", [0])

# Save outputs
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Also save HTML for interactivity
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-clustered - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {chart.render(is_unicode=True)}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
