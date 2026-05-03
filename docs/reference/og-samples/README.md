# OG image samples

Reference renders of every `/og/*.png` endpoint in the new **any.plot()** visual
identity (issue [#5652](https://github.com/MarkusNeusinger/anyplot/issues/5652)).
Regenerate with:

```bash
uv run python scripts/generate_og_samples.py --out docs/reference/og-samples
```

The script does not depend on the API or live database — it renders against
inline matplotlib placeholders so the cards are reproducible across machines.

## What's in here

| File pattern                                | Endpoint                                | Purpose                              |
|---------------------------------------------|-----------------------------------------|--------------------------------------|
| `home__{theme}.png`                         | `/og/home.png`, `/og/plots.png`         | Hero card — fallback for site root   |
| `branded__{spec}__{library}__{theme}.png`   | `/og/{spec}/{lang}/{library}.png`       | Single-implementation branded card   |
| `collage__{spec}__{theme}.png`              | `/og/{spec}.png`                        | 2×3 grid across libraries            |
| `compare__{spec}__{library}__{theme}.png`   | impl-review comparison images           | Before/after for spec updates        |
| `compare__{spec}__{library}__new.png`       | impl-review for first-time impls        | "no previous version" placeholder    |

Each variant is rendered in both `light` (cream `#FFFDF6`) and `dark`
(`#0A0A08`) themes so we can pick the right surface per share context.

## Visual reference for review

### `/og/home.png` + `/og/plots.png`

![home light](home__light.png)

![home dark](home__dark.png)

### `/og/{spec_id}/{language}/{library}.png`

![scatter-basic / matplotlib / light](branded__scatter-basic__matplotlib__light.png)

![sankey-flow / plotly / dark](branded__sankey-flow__plotly__dark.png)

### `/og/{spec_id}.png`

![ridgeline-density collage / light](collage__ridgeline-density__light.png)

### Implementation comparison

![area-basic / matplotlib / before+after](compare__area-basic__matplotlib__light.png)

![area-basic / matplotlib / new impl (no before)](compare__area-basic__matplotlib__new.png)
