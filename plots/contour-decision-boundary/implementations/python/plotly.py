""" pyplots.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler


# Data - Generate moon-shaped classification data
np.random.seed(42)
X, y = make_moons(n_samples=200, noise=0.25, random_state=42)

# Scale features for better visualization
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Train a KNN classifier
clf = KNeighborsClassifier(n_neighbors=15)
clf.fit(X, y)

# Create mesh grid for decision boundary
x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
xx, yy = np.meshgrid(np.linspace(x_min, x_max, 150), np.linspace(y_min, y_max, 150))

# Get predictions for mesh grid
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

# Get prediction probabilities for smoother contours
Z_prob = clf.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, 1]
Z_prob = Z_prob.reshape(xx.shape)

# Create figure
fig = go.Figure()

# Add decision boundary contour using probability
fig.add_trace(
    go.Contour(
        x=np.linspace(x_min, x_max, 150),
        y=np.linspace(y_min, y_max, 150),
        z=Z_prob,
        colorscale=[[0, "#306998"], [1, "#FFD43B"]],
        opacity=0.6,
        showscale=True,
        colorbar=dict(
            title=dict(text="Class Probability", font=dict(size=18)), tickfont=dict(size=16), len=0.7, thickness=25
        ),
        contours=dict(showlines=False),
        hoverinfo="skip",
    )
)

# Add decision boundary line (where probability = 0.5)
fig.add_trace(
    go.Contour(
        x=np.linspace(x_min, x_max, 150),
        y=np.linspace(y_min, y_max, 150),
        z=Z_prob,
        showscale=False,
        contours=dict(start=0.5, end=0.5, size=0.1, coloring="lines", showlabels=False),
        line=dict(color="white", width=3, dash="dash"),
        hoverinfo="skip",
    )
)

# Separate training points by class
X_class0 = X[y == 0]
X_class1 = X[y == 1]

# Add training points - Class 0
fig.add_trace(
    go.Scatter(
        x=X_class0[:, 0],
        y=X_class0[:, 1],
        mode="markers",
        marker=dict(size=14, color="#306998", line=dict(color="white", width=2), symbol="circle"),
        name="Class 0",
        hovertemplate="Feature 1: %{x:.2f}<br>Feature 2: %{y:.2f}<extra>Class 0</extra>",
    )
)

# Add training points - Class 1
fig.add_trace(
    go.Scatter(
        x=X_class1[:, 0],
        y=X_class1[:, 1],
        mode="markers",
        marker=dict(size=14, color="#FFD43B", line=dict(color="black", width=2), symbol="diamond"),
        name="Class 1",
        hovertemplate="Feature 1: %{x:.2f}<br>Feature 2: %{y:.2f}<extra>Class 1</extra>",
    )
)

# Update layout
fig.update_layout(
    title=dict(text="contour-decision-boundary · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Feature 1 (Standardized)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.3)",
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Feature 2 (Standardized)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.3)",
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.3)",
        borderwidth=1,
    ),
    margin=dict(l=80, r=100, t=100, b=80),
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
