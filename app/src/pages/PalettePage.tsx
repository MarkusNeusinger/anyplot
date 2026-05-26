import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import Switch from '@mui/material/Switch';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Tooltip from '@mui/material/Tooltip';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { PaletteStrip } from '../components/PaletteStrip';
import { SectionHeader } from '../components/SectionHeader';
import { useAnalytics } from '../hooks';
import { colors, typography, textStyle } from '../theme';

// ─────────────────────────────────────────────────────────────────────────────
// Data — kept in this file because the page is the canonical visual reference
// ─────────────────────────────────────────────────────────────────────────────

type Swatch = {
  hex: string;
  name: string;
  family: string;
  role: string;
  oklch: string;
  hue: number;
};

const PALETTE: Swatch[] = [
  { hex: '#009E73', name: 'brand green', family: 'green',  role: '★ slot 0 — always first series', oklch: 'oklch(0.620 0.130 165.5)', hue: 166.2 },
  { hex: '#C475FD', name: 'lavender',    family: 'purple', role: 'slot 1',                          oklch: 'oklch(0.704 0.202 308.9)', hue: 305.1 },
  { hex: '#4467A3', name: 'blue',        family: 'blue',   role: 'slot 2',                          oklch: 'oklch(0.516 0.104 260.6)', hue: 254.7 },
  { hex: '#BD8233', name: 'ochre',       family: 'yellow', role: 'slot 3 — earth / commodity',      oklch: 'oklch(0.652 0.118 70.5)',  hue: 70.2 },
  { hex: '#AE3030', name: 'matte red',   family: 'red',    role: 'slot 4 — deferred bad/loss anchor', oklch: 'oklch(0.503 0.163 25.2)', hue: 25.3 },
  { hex: '#2ABCCD', name: 'cyan',        family: 'cyan',   role: 'slot 5 — sky / tech-cool',        oklch: 'oklch(0.730 0.117 207.1)', hue: 209.5 },
  { hex: '#954477', name: 'rose',        family: 'purple', role: 'slot 6 — wellness / health',      oklch: 'oklch(0.508 0.125 343.9)', hue: 344.8 },
  { hex: '#99B314', name: 'lime',        family: 'green',  role: 'slot 7 — growth / nature',        oklch: 'oklch(0.722 0.167 119.8)', hue: 115.1 },
];

type Anchor = {
  key: string;
  hexLight: string;
  hexDark?: string;
  oklchLight: string;
  oklchDark?: string;
  role: string;
  hint: string;
};

const ANCHORS: Anchor[] = [
  {
    key: 'amber',
    hexLight: '#DDCC77',
    oklchLight: 'oklch(0.841 0.108 98.3)',
    role: 'warning / caution',
    hint: "Paul Tol \"muted\" yellow. min ΔE under CVD to the 8 categorical hexes = 14.52 — confidently distinct from every member.",
  },
  {
    key: 'neutral',
    hexLight: '#1A1A17',
    hexDark: '#F0EFE8',
    oklchLight: 'oklch(0.217 0.006 106.9)',
    oklchDark: 'oklch(0.951 0.009 100.0)',
    role: 'totals / baseline / outline',
    hint: "Theme-adaptive ink. Same hex as text and gridlines — the series reads as part of the chart's structural layer.",
  },
  {
    key: 'muted',
    hexLight: '#6B6A63',
    hexDark: '#A8A79F',
    oklchLight: 'oklch(0.523 0.011 100.1)',
    oklchDark: 'oklch(0.727 0.011 100.9)',
    role: 'other / rest / disabled',
    hint: 'Theme-adaptive ink-muted. For "other" / "rest" slices, disabled series, confidence-band fills.',
  },
];

const CVD_TABLE: { n: number; de: number; verdict: string; note: string }[] = [
  { n: 2, de: 36.19, verdict: 'safe',     note: 'well above floor' },
  { n: 3, de: 16.34, verdict: 'safe',     note: 'well above floor' },
  { n: 4, de: 13.98, verdict: 'safe',     note: '' },
  { n: 5, de: 13.98, verdict: 'safe',     note: 'optional: marker shapes' },
  { n: 6, de: 13.70, verdict: 'borderline', note: 'add marker shape OR linestyle' },
  { n: 7, de: 10.70, verdict: 'borderline', note: 'marker + linestyle required' },
  { n: 8, de: 8.81,  verdict: 'fail',     note: 'small multiples or direct labels' },
];

const WCAG_TABLE: { hex: string; name: string; light: number; dark: number }[] = [
  { hex: '#009E73', name: 'brand-green', light: 3.08,  dark: 5.48 },
  { hex: '#AE3030', name: 'matte-red',   light: 5.79,  dark: 2.92 },
  { hex: '#C475FD', name: 'lavender',    light: 2.59,  dark: 6.53 },
  { hex: '#99B314', name: 'lime',        light: 2.15,  dark: 7.87 },
  { hex: '#4467A3', name: 'blue',        light: 5.09,  dark: 3.32 },
  { hex: '#2ABCCD', name: 'cyan',        light: 2.06,  dark: 8.19 },
  { hex: '#954477', name: 'rose',        light: 5.61,  dark: 3.01 },
  { hex: '#BD8233', name: 'ochre',       light: 2.95,  dark: 5.72 },
  { hex: '#DDCC77', name: 'amber',       light: 1.46,  dark: 11.59 },
];

type HistoryEntry = {
  id: string;
  title: string;
  date: string;
  hexes: string[];
  summary: string;
};

const HISTORY: HistoryEntry[] = [
  {
    id: 'v3',
    title: 'v3 — imprint (current)',
    date: '2026',
    hexes: ['#009E73', '#C475FD', '#4467A3', '#BD8233', '#AE3030', '#2ABCCD', '#954477', '#99B314'],
    summary: '8 hues in hybrid-v3 sort. First 4 slots span 4 distinct hue families; semantic-red deferred to slot 4 so it stays a free named anchor. Plus 3 anchors outside the pool (amber, neutral, muted).',
  },
  {
    id: 'v2',
    title: 'v2 — D1-8 (8-hex expansion)',
    date: '2026',
    hexes: ['#009E73', '#AE3030', '#C475FD', '#99B314', '#4467A3', '#2ABCCD', '#954477', '#BD8233'],
    summary: '8-hex expansion of variant-D. Five expert reviewers picked it over a vivid-8 alternative — this version was muted and CVD-safe but had two "greens" and two "purples" close together in the canonical order.',
  },
  {
    id: 'v1',
    title: 'v1 — variant D ("balanced")',
    date: 'May 2026',
    hexes: ['#009E73', '#9418DB', '#B71D27', '#16B8F3', '#99B314', '#D359A7', '#BA843E'],
    summary: 'anyplot\'s first custom palette (PR #7617). 7 hues + adaptive neutral. Brand green inherited from Okabe-Ito; positions 2–7 from a Petroff-style max-min ΔE search in the muted-paper chroma envelope.',
  },
  {
    id: 'v0',
    title: 'v0 — Okabe-Ito',
    date: '2002/2011',
    hexes: ['#009E73', '#D55E00', '#0072B2', '#CC79A7', '#E69F00', '#56B4E9', '#F0E442'],
    summary: 'The original colorblind-safe categorical palette (Wong 2011, Nature Methods). 7 hues + adaptive neutral, brand-green at slot 0. Used by anyplot until v1.',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Code snippets per language
// ─────────────────────────────────────────────────────────────────────────────

type Lang = 'python' | 'r' | 'julia' | 'js' | 'go' | 'rust';

const LANG_LABELS: Record<Lang, string> = {
  python: 'Python', r: 'R', julia: 'Julia', js: 'JavaScript', go: 'Go', rust: 'Rust',
};

function snippet(lang: Lang, oklch: boolean): string {
  const hexes = PALETTE.map(s => s.hex);
  const oklchVals = PALETTE.map(s => s.oklch);
  const values = oklch ? oklchVals : hexes;
  switch (lang) {
    case 'python':
      return `# anyplot imprint palette — 8 categorical hues, hybrid-v3 sort
ANYPLOT_PALETTE = [
${values.map(v => `    ${oklch ? `"${v}"` : `"${v}"`}`).join(',\n')},
]
ANYPLOT_AMBER = ${oklch ? `"oklch(0.841 0.108 98.3)"` : `"#DDCC77"`}  # warning / caution

# first series is ALWAYS slot 0 (brand green)
color = ANYPLOT_PALETTE[0]`;
    case 'r':
      return `# anyplot imprint palette — 8 categorical hues, hybrid-v3 sort
ANYPLOT_PALETTE <- c(
${values.map(v => `  "${v}"`).join(',\n')}
)
ANYPLOT_AMBER <- "${oklch ? 'oklch(0.841 0.108 98.3)' : '#DDCC77'}"  # warning / caution

# first series is ALWAYS slot 0 (brand green)
color <- ANYPLOT_PALETTE[1]`;
    case 'julia':
      return `# anyplot imprint palette — 8 categorical hues, hybrid-v3 sort
const ANYPLOT_PALETTE = [
${values.map(v => `    ${oklch ? `"${v}"` : `colorant"${v}"`}`).join(',\n')},
]
const ANYPLOT_AMBER = ${oklch ? `"oklch(0.841 0.108 98.3)"` : `colorant"#DDCC77"`}  # warning

# first series is ALWAYS slot 0 (brand green)
color = ANYPLOT_PALETTE[1]`;
    case 'js':
      return `// anyplot imprint palette — 8 categorical hues, hybrid-v3 sort
const ANYPLOT_PALETTE = [
${values.map(v => `  "${v}"`).join(',\n')},
];
const ANYPLOT_AMBER = "${oklch ? 'oklch(0.841 0.108 98.3)' : '#DDCC77'}"; // warning

// first series is ALWAYS slot 0 (brand green)
const color = ANYPLOT_PALETTE[0];`;
    case 'go':
      return `// anyplot imprint palette — 8 categorical hues, hybrid-v3 sort
var AnyplotPalette = []string{
${values.map(v => `    "${v}"`).join(',\n')},
}
var AnyplotAmber = "${oklch ? 'oklch(0.841 0.108 98.3)' : '#DDCC77'}" // warning

// first series is ALWAYS slot 0 (brand green)
color := AnyplotPalette[0]`;
    case 'rust':
      return `// anyplot imprint palette — 8 categorical hues, hybrid-v3 sort
const ANYPLOT_PALETTE: [&str; 8] = [
${values.map(v => `    "${v}"`).join(',\n')},
];
const ANYPLOT_AMBER: &str = "${oklch ? 'oklch(0.841 0.108 98.3)' : '#DDCC77'}"; // warning

// first series is ALWAYS slot 0 (brand green)
let color = ANYPLOT_PALETTE[0];`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Layout
// ─────────────────────────────────────────────────────────────────────────────

const sectionSx = { py: { xs: 2, md: 3 } };
const proseColumnSx = { maxWidth: 880, mx: 'auto' };

// ─────────────────────────────────────────────────────────────────────────────
// Inline sub-components
// ─────────────────────────────────────────────────────────────────────────────

function ChromaWheel({ size = 280 }: { size?: number }) {
  // Render 8 swatch dots positioned at their CAM02-UCS hue on a perception-shaped wheel
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.42;
  const dotR = size * 0.052;
  return (
    <Box component="svg" viewBox={`0 0 ${size} ${size}`} sx={{ width: size, height: size, display: 'block' }}>
      {/* faint guide circle */}
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--rule)" strokeWidth="1" />
      {/* hue ticks (90° marks) */}
      {[0, 90, 180, 270].map((deg) => {
        const angle = ((deg - 90) * Math.PI) / 180;
        const x1 = cx + Math.cos(angle) * (r - 6);
        const y1 = cy + Math.sin(angle) * (r - 6);
        const x2 = cx + Math.cos(angle) * (r + 6);
        const y2 = cy + Math.sin(angle) * (r + 6);
        return <line key={deg} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--rule)" strokeWidth="1" />;
      })}
      {/* swatch dots */}
      {PALETTE.map((s, i) => {
        const angle = ((s.hue - 90) * Math.PI) / 180;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        return (
          <g key={s.hex}>
            <circle cx={x} cy={y} r={dotR} fill={s.hex} stroke={i === 0 ? 'var(--ink)' : 'none'} strokeWidth={i === 0 ? 2 : 0} />
            <text
              x={x + Math.cos(angle) * (dotR + 14)}
              y={y + Math.sin(angle) * (dotR + 14)}
              fontSize="9"
              fontFamily="var(--mono)"
              fill="var(--ink-muted)"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {i}
            </text>
          </g>
        );
      })}
      {/* center brand label */}
      <text x={cx} y={cy - 4} fontSize="9" fontFamily="var(--mono)" fill="var(--ink-muted)" textAnchor="middle" dominantBaseline="middle">
        imprint
      </text>
      <text x={cx} y={cy + 8} fontSize="8" fontFamily="var(--mono)" fill="var(--ink-muted)" textAnchor="middle" dominantBaseline="middle">
        n=8 · CAM02-UCS
      </text>
    </Box>
  );
}

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <Box sx={{ position: 'relative', mt: 2 }}>
      <Box
        component="pre"
        sx={{
          fontFamily: typography.mono,
          fontSize: '12px',
          lineHeight: 1.6,
          color: 'var(--code-text)',
          backgroundColor: 'var(--code-bg)',
          border: '1px solid var(--rule)',
          borderRadius: 1,
          p: 2,
          pr: 6,
          overflowX: 'auto',
          margin: 0,
          whiteSpace: 'pre',
        }}
      >
        {code}
      </Box>
      <Tooltip title={copied ? 'copied' : 'copy'} placement="left">
        <IconButton
          size="small"
          onClick={handleCopy}
          sx={{
            position: 'absolute', top: 6, right: 6,
            color: copied ? colors.primary : 'var(--ink-muted)',
          }}
        >
          <ContentCopyIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
}

function CollapsibleSection({ title, defaultOpen = false, children }: { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Box sx={{ borderTop: '1px solid var(--rule)', pt: 2 }}>
      <Box
        component="button"
        onClick={() => setOpen(o => !o)}
        sx={{
          width: '100%',
          display: 'flex', alignItems: 'center', gap: 1,
          background: 'none', border: 'none', cursor: 'pointer',
          fontFamily: typography.mono,
          fontSize: '13px',
          color: 'var(--ink)',
          py: 1,
          textAlign: 'left',
        }}
      >
        <ExpandMoreIcon sx={{ transition: 'transform 0.2s', transform: open ? 'rotate(0deg)' : 'rotate(-90deg)', fontSize: '20px', color: 'var(--ink-muted)' }} />
        {title}
      </Box>
      <Collapse in={open}>
        <Box sx={{ pb: 2, pt: 1 }}>{children}</Box>
      </Collapse>
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export function PalettePage() {
  const { trackPageview } = useAnalytics();
  const [lang, setLang] = useState<Lang>('python');
  const [oklch, setOklch] = useState(false);

  useEffect(() => {
    trackPageview('/palette');
  }, [trackPageview]);

  return (
    <>
      <Helmet>
        <title>palette | anyplot.ai</title>
        <meta name="description" content="The anyplot imprint palette — 8 colorblind-safe categorical hues plus 3 semantic anchors (amber, neutral, muted). Tuned for warm-paper rendering, validated against deuteranopia / protanopia / tritanopia." />
        <link rel="canonical" href="https://anyplot.ai/palette" />
      </Helmet>

      <Box sx={{ pb: 4 }}>
        {/* 1. HERO */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>the anyplot imprint palette</em>} />
          <Box sx={{ ...proseColumnSx, display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 280px' }, gap: 4, alignItems: 'center', mt: 3 }}>
            <Box sx={textStyle}>
              every plot on anyplot.ai uses <strong>imprint</strong>, a colorblind-safe categorical palette
              tuned for warm-cream paper backgrounds. 8 hues in hybrid-v3 sort order plus 3 semantic anchors
              (amber for warning, theme-adaptive neutral and muted). Sits in the academic-publishing-imprint
              family — Penguin Classics, FT Books, Nature Methods — between Paul Tol&apos;s &ldquo;muted&rdquo;
              and ColorBrewer Set2.
              <Box component="span" sx={{ display: 'block', mt: 2, fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)' }}>
                Full design rationale →{' '}
                <Box
                  component="a"
                  href="https://github.com/MarkusNeusinger/anyplot/blob/main/docs/reference/palette-variants-v3/decision-rationale.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ color: 'var(--ink-soft)', textDecoration: 'underline' }}
                >
                  decision-rationale.md
                </Box>
              </Box>
            </Box>
            <Box sx={{ justifySelf: { xs: 'center', md: 'end' } }}>
              <ChromaWheel size={260} />
            </Box>
          </Box>
          <Box sx={{ mt: 4 }}>
            <PaletteStrip maxWidth={null} height={48} mt={0} />
          </Box>
        </Box>

        {/* 2. PALETTE GRID */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>the 8 categorical hues</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 2 }}>
              {PALETTE.map((s, i) => (
                <Box key={s.hex} sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '48px 1fr', md: '48px 110px 110px 1fr' },
                  alignItems: 'center', gap: 2, py: 1,
                  borderBottom: i < PALETTE.length - 1 ? '1px solid var(--rule)' : 'none',
                }}>
                  <Box sx={{ width: 40, height: 40, borderRadius: '8px', bgcolor: s.hex, border: '1px solid var(--rule)' }} />
                  <Box sx={{ fontFamily: typography.mono, fontSize: '13px', fontWeight: 600, color: 'var(--ink)' }}>
                    {s.hex}
                  </Box>
                  <Box sx={{ fontFamily: typography.mono, fontSize: '12px', color: 'var(--ink-muted)', display: { xs: 'none', md: 'block' } }}>
                    {s.name}
                  </Box>
                  <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)' }}>
                    {s.role}
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </Box>

        {/* 3. SEMANTIC ANCHORS */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>semantic anchors</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              three additional anchors that live <strong>outside</strong> the categorical pool. they are never
              returned by <code>palette[:n]</code> — reached only by name (<code>palette.amber</code>,
              <code> palette.neutral</code>, <code>palette.muted</code>). two of them flip per theme.
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2, mt: 2 }}>
              {ANCHORS.map((a) => (
                <Box key={a.key} sx={{ border: '1px solid var(--rule)', borderRadius: 2, overflow: 'hidden', backgroundColor: 'var(--bg-surface)' }}>
                  {a.hexDark ? (
                    <Box sx={{ height: 56, display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
                      <Box sx={{ bgcolor: a.hexLight, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', pb: 0.5, color: '#F0EFE8', fontFamily: typography.mono, fontSize: '10px' }}>
                        {a.hexLight}
                      </Box>
                      <Box sx={{ bgcolor: a.hexDark, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', pb: 0.5, color: '#1A1A17', fontFamily: typography.mono, fontSize: '10px' }}>
                        {a.hexDark}
                      </Box>
                    </Box>
                  ) : (
                    <Box sx={{ height: 56, bgcolor: a.hexLight }} />
                  )}
                  <Box sx={{ p: 1.5 }}>
                    <Box sx={{ fontFamily: typography.mono, fontSize: '11px', fontWeight: 600, color: 'var(--ink)', mb: 0.5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      {a.role}
                    </Box>
                    <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)', mb: 0.75 }}>
                      palette.{a.key}{a.hexDark ? ' — adaptive' : ''}
                    </Box>
                    <Box sx={{ fontSize: '12px', color: 'var(--ink-muted)', lineHeight: 1.5 }}>
                      {a.hint}
                    </Box>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </Box>

        {/* 4. COPY SNIPPETS */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>copy &amp; paste</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={{ ...textStyle, mb: 2 }}>
              standalone snippets per language. no <code>pip install anyplot</code> needed — every block is a
              copy-paste-and-go set of constants.
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
              <Tabs
                value={lang}
                onChange={(_, v) => setLang(v as Lang)}
                variant="scrollable"
                scrollButtons="auto"
                sx={{
                  minHeight: 36,
                  '& .MuiTab-root': { fontFamily: typography.mono, fontSize: '11px', minHeight: 36, py: 0, textTransform: 'none', color: 'var(--ink-muted)' },
                  '& .Mui-selected': { color: 'var(--ink)' },
                  '& .MuiTabs-indicator': { backgroundColor: colors.primary },
                }}
              >
                {(Object.keys(LANG_LABELS) as Lang[]).map(l => (
                  <Tab key={l} value={l} label={LANG_LABELS[l]} />
                ))}
              </Tabs>
              <FormControlLabel
                control={<Switch size="small" checked={oklch} onChange={(e) => setOklch(e.target.checked)} sx={{ '& .MuiSwitch-switchBase.Mui-checked': { color: colors.primary }, '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: colors.primary } }} />}
                label={<Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)' }}>OKLCH</Box>}
              />
            </Box>
            <CodeBlock code={snippet(lang, oklch)} />
          </Box>
        </Box>

        {/* 5. CVD SAFETY */}
        <Box component="section" sx={sectionSx}>
          <SectionHeader prompt="❯" title={<em>best variant for CVD users</em>} />
          <Box sx={proseColumnSx}>
            <Box sx={textStyle}>
              the imprint sort holds worst-pair ΔE under simulated deuteranopia / protanopia / tritanopia
              above the 10-point discrimination floor through <strong>n = 6</strong>. beyond that the eye
              starts losing pairs — add a marker shape or linestyle.
            </Box>
            <Box sx={{ mt: 2, overflowX: 'auto' }}>
              <Box component="table" sx={{
                width: '100%',
                borderCollapse: 'collapse',
                fontFamily: typography.mono,
                fontSize: '11px',
                '& th, & td': { padding: '6px 12px', textAlign: 'left', borderBottom: '1px solid var(--rule)' },
                '& th': { color: 'var(--ink-muted)', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' },
                '& td.num': { textAlign: 'right', color: 'var(--ink)' },
              }}>
                <thead>
                  <tr>
                    <th>n series</th>
                    <th>ΔE_CVD floor</th>
                    <th>verdict</th>
                    <th>guidance</th>
                  </tr>
                </thead>
                <tbody>
                  {CVD_TABLE.map((row) => (
                    <tr key={row.n}>
                      <td>{row.n}</td>
                      <td className="num">{row.de.toFixed(2)}</td>
                      <td style={{
                        color: row.verdict === 'safe' ? '#007A59' : row.verdict === 'borderline' ? '#b56b18' : '#b62d2d',
                        fontWeight: 600,
                      }}>{row.verdict}</td>
                      <td style={{ color: 'var(--ink-muted)' }}>{row.note || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </Box>
            </Box>
          </Box>
        </Box>

        {/* 6. WCAG AUDIT (collapsible) */}
        <Box component="section" sx={sectionSx}>
          <Box sx={proseColumnSx}>
            <CollapsibleSection title="WCAG contrast on both themes (and the outline pattern)">
              <Box sx={textStyle}>
                muted palettes share a known limit: the lighter members carry their distinguishability through
                chroma, not L-spread. On cream bg <code>#F5F3EC</code>, five categorical hues + amber fall under
                WCAG 2.1 SC 1.4.11&apos;s 3:1 minimum. The industry-standard fix is a <strong>1px ink-color
                stroke</strong> on affected series — but it&apos;s a renderer judgment call, not a hard rule.
              </Box>
              <Box sx={{ mt: 2, overflowX: 'auto' }}>
                <Box component="table" sx={{
                  width: '100%', borderCollapse: 'collapse',
                  fontFamily: typography.mono, fontSize: '11px',
                  '& th, & td': { padding: '6px 12px', textAlign: 'left', borderBottom: '1px solid var(--rule)' },
                  '& th': { color: 'var(--ink-muted)', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' },
                }}>
                  <thead>
                    <tr>
                      <th>hex</th>
                      <th>name</th>
                      <th style={{ textAlign: 'right' }}>on cream</th>
                      <th style={{ textAlign: 'right' }}>on dark</th>
                    </tr>
                  </thead>
                  <tbody>
                    {WCAG_TABLE.map((row) => (
                      <tr key={row.hex}>
                        <td>
                          <Box component="span" sx={{ display: 'inline-block', width: 12, height: 12, borderRadius: 2, bgcolor: row.hex, mr: 1, verticalAlign: 'middle', border: '1px solid var(--rule)' }} />
                          {row.hex}
                        </td>
                        <td style={{ color: 'var(--ink-muted)' }}>{row.name}</td>
                        <td style={{ textAlign: 'right', color: row.light < 3 ? '#b62d2d' : '#007A59', fontWeight: 600 }}>
                          {row.light.toFixed(2)}:1 {row.light < 3 ? '✗' : '✓'}
                        </td>
                        <td style={{ textAlign: 'right', color: row.dark < 3 ? '#b62d2d' : '#007A59', fontWeight: 600 }}>
                          {row.dark.toFixed(2)}:1 {row.dark < 3 ? '✗' : '✓'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Box>
              </Box>
            </CollapsibleSection>
          </Box>
        </Box>

        {/* 7. HISTORY (collapsible) */}
        <Box component="section" sx={sectionSx}>
          <Box sx={proseColumnSx}>
            <CollapsibleSection title="palette history — how we got here">
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
                {HISTORY.map((entry) => (
                  <Box key={entry.id}>
                    <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2, mb: 1 }}>
                      <Box sx={{ fontFamily: typography.mono, fontSize: '13px', color: 'var(--ink)', fontWeight: 600 }}>
                        {entry.title}
                      </Box>
                      <Box sx={{ fontFamily: typography.mono, fontSize: '11px', color: 'var(--ink-muted)' }}>
                        {entry.date}
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', mb: 1, borderRadius: 1, overflow: 'hidden', boxShadow: '0 0 0 1px var(--rule)' }}>
                      {entry.hexes.map((hx) => (
                        <Box key={hx} sx={{ flex: 1, height: 32, bgcolor: hx }} title={hx} />
                      ))}
                    </Box>
                    <Box sx={{ fontSize: '12px', color: 'var(--ink-muted)', lineHeight: 1.55 }}>
                      {entry.summary}
                    </Box>
                  </Box>
                ))}
              </Box>
            </CollapsibleSection>
          </Box>
        </Box>
      </Box>
    </>
  );
}
