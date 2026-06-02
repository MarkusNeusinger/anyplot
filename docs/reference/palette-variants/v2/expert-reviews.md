# palette-variants-v2 — expert review synthesis

Companion to [`index.html`](./index.html). Five independent Opus subagents
were asked to play domain experts from different fields, given only the
hex values, the CVD performance numbers, the warm-paper bg context, and a
pointer to the v2 comparison page. Each was instructed to pick a winner
(or argue for neither) and defend the choice in their domain's idiom.

## Verdict

**5 of 5 chose muted-8 (was D1-8).** Unanimous, across domains that
disagree on most other things.

| Persona | Vote | One-line argument |
|---|---|---|
| Editorial (FT / Economist / NYT Upshot) | **muted-8** | "C ∈ [20–32] is editorial-standard. Vivid reads cheap on coated stock." |
| B2B consulting (McKinsey / BCG / Bain) | **muted-8** | "Chroma reads as opinion. CFOs disengage from 'designed' decks." |
| Scientific publishing (Nature / IEEE) | **muted-8** | "Paul Tol's muted, Okabe-Ito, ColorBrewer Set2 all live in B's range. B = 'OI rebalanced for n=8'." |
| Accessibility / CVD specialist | **muted-8** | "A's vivid red collapses worse under deuteranopia — L-drift narrows the gap with lime." |
| Brand / product design (Linear / Radix) | **muted-8** | "Vivid-8 = '2014 Tableau screenshot'. Muted = Radix / Linear / Notion mood." |

## Recurring themes across the five reviews

### 1. Vivid-8 is read as "dated dashboard"

Every reviewer — independently — placed vivid-8 in roughly the
2014-Tableau era. The industry has spent ~5 years moving away from
high-chroma categorical palettes: Linear, Radix, Stripe, dracula-pro,
the BBC Visual Vocabulary post-2018, Notion's tag colors, Tailwind v4's
P3 accents all sit in muted-8's chroma range. Shipping vivid-8 today
signals "we have not been paying attention."

### 2. The CVD numerical advantage is illusory

vivid-8's nominally better worst-pair ΔE (n=4: 17.3 vs 15.2; n=8:
9.8 vs 8.8) is below pixel anti-aliasing resolution at typical chart
sizes and both palettes fall under the 10 ΔE "confident discrimination"
floor at n=8 anyway. The accessibility specialist was explicit: "the
1-point gap at n=8 is noise; the binding constraint is the lime-red
deuteranopia pair, which muted-8 actually handles better because its
matte red has less chroma to rotate toward yellow under simulation."

### 3. Vivid red is a semantic resource that shouldn't be spent on series-3

Both the consulting and editorial reviewers raised this: a true vivid
red (`#B71D27`) is semantically loaded for loss / error / negative
signal. Burning it as the third categorical slot in every plot anyplot
generates wastes that semantic. This argument actually *validates* the
v1 design move that put `#AE3030` at pos 1 of muted-8 via hue-band
pinning instead of using live-D's vivid red.

### 4. Tertiary tones (rosé, lavender, ochre) read as legitimate in muted-8

The scientific and brand reviewers both noted that muted-8's `#954477`
matte rosé, `#C475FD` lavender, and `#BD8233` ochre sit inside the
respected Paul Tol / ColorBrewer / Tableau-CB tradition of desaturated
tertiary tones. Vivid-8's `#D359A7` hot pink and `#7981FD` indigo
read as marketing/dashboard palette in the same contexts.

## Recurring critique — the red anchor is too soft

Three of five reviewers (editorial, brand, accessibility implicit)
flagged that muted-8's `#AE3030` is too weak for the semantic-red role
the rest of the argument relies on:

- **Editorial:** under deuteranopia `#AE3030` sits too close to `#954477`
  rosé; "would push to `#B71D27` or `#A41E22`."
- **Brand:** "`#AE3030` is brick, not red. On warm paper it reads
  brown-ish. Anchor a true red around `#C8322C` or `#BE2B2B` — keep the
  matte chroma envelope, push hue back toward 25°."
- **Accessibility:** corroborated indirectly — matte red has less
  hue-rotation under CVD precisely because it has less chroma, which
  is good for CVD safety but reduces semantic-red instant-readability.

This corroborates the project memory note
[`palette_must_anchor_semantic_red`](file:///home/meake/.claude/projects/-home-meake-projects-anyplot/memory/feedback_palette_must_anchor_semantic_red.md)
— the rule that candidate palettes must allow a true red, via explicit
seeding if needed.

## Recommended next steps

1. **Re-anchor muted-8's pos-1 red.** Tighten the hue-band constraint
   to ~22–26° and let the chroma corridor open to C ∈ [30, 38] *for
   that one slot only* (the same kind of exception live-D already makes
   for `#B71D27` at C≈44). Target value: around `#BE2B2B` or `#C8322C`.

2. **Validate the matte rosé hasn't shifted.** A stronger red at pos 1
   changes the max-min CVD landscape — the greedy 8th pick (currently
   `#954477`) may want to move; run `palette-variants-v1.py` after the
   red fix and confirm the back-gap pick still bridges purple↔red
   cleanly.

3. **Document n>6 companion guidance — but only for unsorted-categorical
   chart slots.** All reviewers implicitly or explicitly noted that 8
   categorical lines on a single chart is a worst case. The
   recommendation stands for that case: "above 6 series in one chart,
   add a redundant encoding (linestyle / marker shape) or switch to
   small multiples." See the important caveat in the next section on
   semantic picking — that recommendation is _not_ a vote against
   having 8 colours in the pool, only against rendering 8 lines on top
   of each other and expecting the eye to keep them apart.

If those three land, muted-8 graduates from "compelling candidate" to
"defensible default upgrade over live-D" with five independent expert
endorsements behind it.

## Further optimization levers (beyond the three above)

The three recommended next-steps are the table stakes. Four additional
hooks would each push muted-8 from "good default" toward "state-of-the-art":

### 4. Separate hex sets for light vs dark theme

anyplot currently ships the same 8 hexes against both `#F5F3EC` light bg
and `#121210` dark bg. Modern systems (Radix 12-step scales, Apple
`UIColor.systemGreen` per appearance, Tailwind v4 P3) all define
per-theme variants. Some muted-8 hues sit awkwardly on one of the two:
`#4467A3` blue at L≈40 has only ~3 L-points separation from the dark bg
at L≈37. A dark-theme lift of L+12 on the cool half of the palette would
materially improve readability. Cost: a second optimization run + a
runtime mode-switcher; benefit: every chart on dark mode reads cleaner.

### 5. Named sub-palettes with their own optimal sort per length

Instead of one canonical 8-tuple from which "the first n" are taken,
ship `anyplot.palette.n3`, `n5`, `n8` as separately optimised slices
from the same hex pool. A chart with 3 series should get the 3
CVD-most-distinct picks, not "the first 3" of an n=8-optimised
ordering. Concrete example: pure-CVD greedy for n=3 picks
`green / lavender / lime` instead of `green / red / lavender` —
because red↔green collapses under deuteranopia and the algorithm
correctly avoids that pair when it only has to satisfy 3 slots.
Reduces the "I'll just take the first 3" failure mode users fall into.

### 6. Define the palette in OKLCH + ship a P3 variant

CSS Color Level 4 (`oklch()`, `color(display-p3 ...)`) has broad
browser support. Defining muted-8 in OKLCH instead of sRGB hex means
modern P3 displays show ~15% wider chroma headroom at *identical*
perceived colour on sRGB displays — no sRGB clipping. Linear and
Stripe ship P3-aware palettes already. Cost: low (notation change, no
algorithm change); benefit: forward-compat with the next 5 years of
display hardware.

### 7. Explicit grayscale-fallback ordering

For S/W print (academic supplementary PDFs, fax-machine fallbacks)
only the L values distinguish series. muted-8's hues sorted by L:
`lime(68) ≈ cyan(68) > green(58) > lavender(56) > tan(53) > rosé(45)
> red(42) ≈ blue(40)`. Two pairs (lime/cyan and red/blue) collapse to
indistinguishable greys. A separate `palette.grayscale_order` index that
sorts by max L-spread (so consecutive picks always have ≥10 L apart)
costs a few lines in `_charts_stack` and rescues reproducibility for
scientific figures. None of the experts mentioned this explicitly but
the scientific reviewer's "print + grayscale fallback" remark hinted
at it.

## Where does muted-8 sit among existing palettes?

The scientific reviewer's framing — "muted-8 = Okabe-Ito rebalanced
for n=8 line charts" — is the most accurate one-liner, but it's worth
unpacking the broader landscape. muted-8 sits inside a respected
family, which is a feature, not a bug.

```
Paul Tol "muted" (9):  #332288  #88CCEE  #44AA99  #117733  #999933
                       #DDCC77  #CC6677  #882255  #AA4499

ColorBrewer Set2 (8):  #66C2A5  #FC8D62  #8DA0CB  #E78AC3  #A6D854
                       #FFD92F  #E5C494  #B3B3B3

Okabe-Ito (8):         #000000  #E69F00  #56B4E9  #009E73  #F0E442
                       #0072B2  #D55E00  #CC79A7

muted-8 (anyplot):     #009E73  #AE3030  #C475FD  #99B314  #4467A3
                       #2ABCCD  #954477  #BD8233
```

Distinguishing characteristics versus each:

- **vs Paul Tol's "muted":** same dustier-tertiary family but muted-8
  is higher-chroma (C∈[24,32] vs Tol's ~C∈[15,25] — Tol is markedly
  pastel-leaning), brand-anchored on `#009E73`, has a true semantic red
  where Tol only has cool "wine" `#882255` that's too dark for
  loss/error mapping.

- **vs ColorBrewer Set2:** same general restraint but Set2 is genuinely
  pastel (L∈[65,80]), reads as "data viz tutorial" rather than
  "considered editorial". muted-8 spans a wider L range so dark hues
  carry weight on light bg and lights hold up on dark bg.

- **vs Okabe-Ito:** muted-8 inherits OI's green (`#009E73`) — the
  single most-cited CVD-safe brand-green in scientific publishing —
  but fixes OI's two known weak points: (1) the orange/vermillion
  near-collision (OI's `#E69F00` and `#D55E00` sit only ~25° apart on
  the hue wheel) is replaced by separating red (`#AE3030`) and tan
  (`#BD8233`) onto opposite sides of the wheel, and (2) OI's yellow
  `#F0E442` washes out on cream bg-page — muted-8 has no near-yellow,
  using olive-lime `#99B314` instead, which holds up on warm paper.

- **vs Tableau-10 / D3 schemeCategory10 (vivid-8's reference point):**
  ~one chroma-corridor step lower. Same overall hue diversity,
  different saturation register. Tableau-10 was designed for dashboard
  exploration; muted-8 is designed for published figures + slide decks.

### Is it too similar to anything specific?

Honest answer: **no, but it's deliberately *adjacent* to Paul Tol's
"muted"**. Same neighbourhood, distinct hex set, brand-anchored,
better semantic-red handling. The kinship places anyplot in the
respected Tol / ColorBrewer / Okabe-Ito lineage rather than as a
snowflake — the family it's joining is the *right* family for a
generative plot tool whose output lands in mixed academic, editorial,
and consulting contexts.

The defensible positioning if asked "why not just ship Okabe-Ito":
*OI is excellent but has a known orange-vermillion confusion and uses
a yellow that washes out on warm paper. muted-8 keeps the OI green
everyone already trusts and rebalances the rest of the palette to fix
those two specific weaknesses, while staying inside the same
publication-safe chroma envelope.* That's an upgrade story, not a
reinvention story.

## Important caveat — the experts missed semantic picking

The reviewers all treated the palette as a **categorical slot pool**:
"these 8 colours fill positions 0..7 of a chart with N series, and the
question is how well the first n hold up." Under that lens, the
"n>6 needs companion encoding" warning is correct.

But anyplot's palette also serves a **second, equally important
use case**: **semantic named picking**. When a customer expects:

- `green energy` → green, never pink
- `profit / gain` → green, never red or brown
- `loss / error / bad` → red, never matte rosé
- `warning` → amber / ochre, never cyan
- `water / cold` → blue, never lime
- `oil / commodity` → tan, never magenta

…then the user reaches into the palette **by name, by hue family**, not
by position. The picked colour must EXIST in the palette and must be
**unambiguously identifiable as red/green/blue/etc** when grabbed.

This is documented in the project memory
[`feedback_palette_semantic_exception`](file:///home/meake/.claude/projects/-home-meake-projects-anyplot/memory/feedback_palette_semantic_exception.md)
— the rule that conventions like "bad → red, good → green,
warning → amber" are first-class concerns, not categorical-distinctness
edge cases.

### What this means for muted-8

The semantic-picking use case **argues FOR n=8 as a target, not against
it**. The 8 hues aren't 8 slots all expected to coexist in one chart —
they're 8 **named anchors** in a semantic pool:

| Semantic role | muted-8 anchor | Why it works |
|---|---|---|
| `good / profit / energy-green` | `#009E73` brand-green | Okabe-Ito green; instant-readable as "green" |
| `bad / loss / error` | `#AE3030` → `#BE2B2B` (after fix) | Needs the red-anchor fix from next-steps #1 |
| `cold / water / cool` | `#4467A3` blue | Clearly readable as primary blue |
| `warning / commodity / earth` | `#BD8233` tan / ochre | Distinct from both red and green |
| `growth / nature / lime-energy` | `#99B314` lime | Distinct from brand-green |
| `info / sky / tech-cool` | `#2ABCCD` cyan | Distinct from blue |
| `creative / artistic / brand-secondary` | `#C475FD` lavender | Tertiary but unambiguous |
| `feminine-coded / health / wellness` | `#954477` matte rosé | Distinct from red AND from lavender |

Each anchor needs to be **independently recognisable as its
hue-category** when picked solo onto a chart — even if it would never
appear alongside its 7 siblings in one chart. The Pure-CVD-greedy
ordering is the right *default* when the user doesn't care which colour
gets slot 1; but the named API is what actually serves the "green
energy" / "profit-green" / "loss-red" customer expectation.

### Recommended additional design move

Ship muted-8 with **both** access patterns documented:

```python
# Position-based (current default — for "I just need 5 distinct lines")
anyplot.palette[:5]                  # first 5 by sort order

# Semantic-named (new — for "I need the loss colour for this series")
anyplot.palette.green                # → #009E73
anyplot.palette.red                  # → #BE2B2B
anyplot.palette.blue                 # → #4467A3
anyplot.palette.ochre                # → #BD8233
anyplot.palette.lime                 # → #99B314
anyplot.palette.cyan                 # → #2ABCCD
anyplot.palette.lavender             # → #C475FD
anyplot.palette.rose                 # → #954477

# Semantic-role aliases that map to the anchors above
anyplot.palette.semantic.good        # → green
anyplot.palette.semantic.bad         # → red
anyplot.palette.semantic.warning     # → ochre
anyplot.palette.semantic.info        # → cyan
```

This costs almost nothing in implementation (it's just dict access)
but turns the palette from "8 things in an array" into "a vocabulary
the customer can speak in." That second framing is what the experts'
"n>6 is bad" warning misses — the n=8 size isn't there to be packed
onto one chart, it's there so the customer never has to compromise on
which named colour they pick.
