""" anyplot.ai
line-tanabe-sugano: Tanabe-Sugano Diagram for Crystal Field Theory
Library: plotly | Python 3.13
Quality: pending | Created: 2026-10-01
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
SPIN_ALLOWED = "#009E73"  # Imprint palette position 1 — spin-allowed (triplet) terms
SPIN_FORBIDDEN = "#C475FD"  # Imprint palette position 2 — spin-forbidden (singlet) terms

# Data — d² (V³⁺) in an octahedral field at C/B = 4.5.
# Diagonal elements of the Tanabe-Sugano matrices are in units of B relative to the
# free-ion ³F term, with Dq = Δ_o/10; off-diagonal elements do not depend on Dq.
# The ground term is subtracted at the end, so E/B = 0 runs along the x axis.
c_over_b = 4.5
delta_over_b = np.linspace(0, 40, 320)
dq = delta_over_b / 10

off_3t1 = np.full_like(dq, 6.0)
off_1d = np.full_like(dq, 2 * np.sqrt(3))
off_1a1 = np.full_like(dq, np.sqrt(6) * (2 + c_over_b))

e_3t1 = np.linalg.eigvalsh(np.array([[-8 * dq + 3, off_3t1], [off_3t1, 2 * dq + 12]]).T)
e_1t2 = np.linalg.eigvalsh(np.array([[-8 * dq + 9 + 2 * c_over_b, off_1d], [off_1d, 2 * dq + 8 + 2 * c_over_b]]).T)
e_1eg = np.linalg.eigvalsh(np.array([[-8 * dq + 9 + 2 * c_over_b, off_1d], [off_1d, 12 * dq + 8 + 2 * c_over_b]]).T)
e_1a1 = np.linalg.eigvalsh(np.array([[-8 * dq + 18 + 5 * c_over_b, off_1a1], [off_1a1, 12 * dq + 16 + 4 * c_over_b]]).T)
ground = e_3t1[:, 0]

# (term label, energy, spin-allowed, label nudge for near-degenerate pairs)
terms = [
    ("<sup>3</sup>T<sub>1g</sub>(F)", e_3t1[:, 0], True, 0.0),
    ("<sup>3</sup>T<sub>2g</sub>", 2 * dq, True, 0.5),
    ("<sup>3</sup>T<sub>1g</sub>(P)", e_3t1[:, 1], True, 0.0),
    ("<sup>3</sup>A<sub>2g</sub>", 12 * dq, True, 0.0),
    ("<sup>1</sup>T<sub>2g</sub>(D)", e_1t2[:, 0], False, -1.6),
    ("<sup>1</sup>E<sub>g</sub>(D)", e_1eg[:, 0], False, 1.6),
    ("<sup>1</sup>A<sub>1g</sub>(G)", e_1a1[:, 0], False, -0.5),
    ("<sup>1</sup>T<sub>2g</sub>(G)", e_1t2[:, 1], False, 0.0),
    ("<sup>1</sup>T<sub>1g</sub>(G)", 2 * dq + 12 + 2 * c_over_b, False, 0.0),
]

# Plot — one curve per term, labelled in the right margin
fig = go.Figure()
for label, energy, spin_allowed, label_nudge in terms:
    energy_over_b = energy - ground
    fig.add_trace(
        go.Scatter(
            x=delta_over_b,
            y=energy_over_b,
            mode="lines",
            name=label,
            line=dict(
                color=SPIN_ALLOWED if spin_allowed else SPIN_FORBIDDEN,
                width=3.0 if spin_allowed else 1.8,
                dash="solid" if spin_allowed else "dash",
            ),
        )
    )
    fig.add_annotation(
        x=1.015,
        xref="paper",
        xanchor="left",
        y=energy_over_b[-1] + label_nudge,
        yref="y",
        text=label,
        showarrow=False,
        font=dict(size=11, color=INK if spin_allowed else INK_SOFT),
    )

# Style
fig.add_annotation(
    x=1.0,
    y=78,
    xanchor="left",
    yanchor="top",
    align="left",
    text=(
        "d<sup>2</sup> (V<sup>3+</sup>) in an octahedral field, C/B = 4.5<br>"
        "solid: spin-allowed (triplet) · dashed: spin-forbidden (singlet)"
    ),
    showarrow=False,
    font=dict(size=11, color=INK_SOFT),
)
fig.update_layout(
    autosize=False,
    margin=dict(l=70, r=92, t=72, b=62),
    showlegend=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    title=dict(
        text="line-tanabe-sugano · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Δ<sub>o</sub>/B  (reduced ligand-field strength)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        range=[0, 40],
        tick0=0,
        dtick=10,
        ticks="",
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="E/B  (reduced term energy)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        range=[-2, 80],
        tick0=0,
        dtick=10,
        ticks="",
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
