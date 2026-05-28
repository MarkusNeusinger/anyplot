import { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import { typography, colors } from '../theme';
import { ThemeToggle } from './ThemeToggle';
import { useTheme, useLatestRelease, useAnalytics } from '../hooks';
import { RESERVED_TOP_LEVEL } from '../utils/paths';
import { LIB_ABBREV, LANG_EXT } from '../constants';

// Symmetric block-comment delimiters used when no language context is in the URL.
// One is picked on mount so each page load reveals a different classic.
const COMMENT_POOL = [
  { open: '"""', close: '"""' },       // python docstring
  { open: '/*', close: '*/' },         // js / c / rust / css / go
  { open: '<!--', close: '-->' },      // html
  { open: '{-', close: '-}' },         // haskell
  { open: '(*', close: '*)' },         // ocaml / fsharp
  { open: '--[[', close: ']]' },       // lua
] as const;

// When the URL carries a language segment, use its native block-comment style instead.
const LANG_DELIM: Record<string, { open: string; close: string }> = {
  python: { open: '"""', close: '"""' },
  javascript: { open: '/*', close: '*/' },
  typescript: { open: '/*', close: '*/' },
  rust: { open: '/*', close: '*/' },
  go: { open: '/*', close: '*/' },
  r: { open: '#', close: '#' },
  julia: { open: '#=', close: '=#' },
  ruby: { open: '=begin', close: '=end' },
  haskell: { open: '{-', close: '-}' },
  ocaml: { open: '(*', close: '*)' },
  lua: { open: '--[[', close: ']]' },
  html: { open: '<!--', close: '-->' },
  css: { open: '/*', close: '*/' },
};

const REPO_URL = 'https://github.com/MarkusNeusinger/anyplot';

const linkSx = {
  color: 'inherit',
  textDecoration: 'none',
  borderBottom: '1px dotted transparent',
  transition: 'color 0.2s, border-color 0.2s',
  '&:hover': { color: colors.primary, borderBottomColor: 'currentColor' },
} as const;

const staticSx = {
  color: 'inherit',
} as const;

interface Segment {
  label: string;
  to?: string;
  // Shorthand label used on xs viewports — the masthead would otherwise
  // truncate the spec-id and cut off language/library entirely (the parts the
  // user is actively looking at). Falls back to `label` when absent.
  short?: string;
}

/**
 * Build path segments from the current pathname. Returned segments are rendered
 * after the `~/anyplot.ai` root marker. Each segment may carry an internal
 * route — the last segment never does (it's the current page).
 *
 * Routes covered:
 *   /<page>                                 → [<page>]
 *   /:specId                                → [specId]
 *   /:specId/:language                      → [specId(→/specId), language]
 *   /:specId/:language/:library             → [specId(→/specId), language(→/specId/language), library]
 */
function pathSegments(pathname: string): Segment[] {
  const parts = pathname.split('/').filter(Boolean);
  if (parts.length === 0) return [];

  // Reserved top-level routes (single segment)
  if (RESERVED_TOP_LEVEL.has(parts[0])) {
    return [{ label: parts[0] }];
  }

  // Spec routes: /:specId[/:language[/:library]]
  const [specId, language, library] = parts;
  const segs: Segment[] = [];
  if (language) {
    segs.push({ label: specId, to: `/${specId}` });
  } else {
    segs.push({ label: specId });
  }
  if (language) {
    if (library) {
      segs.push({ label: language, to: `/${specId}/${language}`, short: LANG_EXT[language] });
      segs.push({ label: library, short: LIB_ABBREV[library] });
    } else {
      segs.push({ label: language, short: LANG_EXT[language] });
    }
  }
  return segs;
}

/**
 * Top masthead bar (style-guide §6.4) — also serves as the global breadcrumb.
 *
 * On `/`, the linkable left slot shows `~/anyplot.ai · main · v1.1.0` and the
 * center carries the catchphrase. On every other route, the left slot becomes
 * the breadcrumb path (`~/anyplot.ai · python · scatter-basic · matplotlib`)
 * and the catchphrase is suppressed so the line stays uncluttered.
 */
export function MastheadRule() {
  const { mode, cycle } = useTheme();
  const { trackEvent } = useAnalytics();
  const releaseTag = useLatestRelease();
  const location = useLocation();
  const segments = pathSegments(location.pathname);
  const isLanding = segments.length === 0;
  const version = releaseTag ?? 'v1.0';

  const NEXT_MODE = { system: 'light', light: 'dark', dark: 'system' } as const;
  const handleThemeToggle = () => {
    trackEvent('theme_toggle', { to: NEXT_MODE[mode] });
    cycle();
  };

  // Pick one random comment style per browser session (stable across client-side nav).
  const [randomIdx] = useState(() => Math.floor(Math.random() * COMMENT_POOL.length));

  // Short single-segment breadcrumbs (e.g. `/palette`, `/about`, `/mcp`) leave
  // plenty of room on xs — hiding `~/anyplot.ai` there strands the breadcrumb
  // as a tiny label and makes the masthead look empty. Keep the root marker
  // visible whenever the xs-effective breadcrumb is under 15 chars.
  const xsBreadcrumbLength = isLanding
    ? 0
    : segments.reduce((sum, s) => {
        const xsLabel = s.short && s.short !== s.label ? s.short : s.label;
        return sum + xsLabel.length;
      }, 0);
  const keepRootMarkerOnXs = !isLanding && xsBreadcrumbLength < 15;
  const rootMarkerDisplay = keepRootMarkerOnXs ? 'inline' : { xs: 'none', sm: 'inline' };

  // Determine whether the center comment shows, what it says, and in which syntax.
  // - Landing: random delim + brand claim
  // - Spec routes (/:specId[/:language[/:library]]): random or language-matched delim,
  //   content switches to spec-id (+ library if present) for contextual anchoring
  // - Reserved pages (about, libraries, legal, …): hidden
  const parts = location.pathname.split('/').filter(Boolean);
  const isReserved = parts.length > 0 && RESERVED_TOP_LEVEL.has(parts[0]);
  const isSpecRoute = parts.length > 0 && !isReserved;
  // On impl pages (/:specId/:language/:library) the breadcrumb already shows
  // all three parts; the center `""" specId.library """` echo is redundant
  // and steals room that pushes the breadcrumb into truncation. Hide it.
  const isImplPage = isSpecRoute && parts.length >= 3;
  const centerVisible = (isLanding || isSpecRoute) && !isImplPage;

  let centerContent = 'the open plot catalogue';
  let centerDelim: { open: string; close: string } = COMMENT_POOL[randomIdx];
  if (isSpecRoute) {
    const [specId, language, library] = parts;
    centerContent = library ? `${specId}.${library}` : specId;
    // Hub pages carry the language via ?language=… query param (see router.tsx
    // SpecLanguageRedirect). Detail pages carry it as a path segment.
    const queryLanguage = new URLSearchParams(location.search).get('language');
    const effectiveLanguage = language || queryLanguage;
    if (effectiveLanguage && LANG_DELIM[effectiveLanguage]) centerDelim = LANG_DELIM[effectiveLanguage];
  }

  return (
    <Box sx={{
      display: 'grid',
      // xs+sm: left takes all remaining room, toggle hugs the right edge —
      // the center comment is hidden until md, so giving it its own balanced
      // 1fr column at sm just wastes ~half the bar on whitespace and forces
      // the breadcrumb to truncate. md+: when the center comment actually
      // shows (landing / spec hub / lang hub), use balanced 1fr auto 1fr so
      // the comment sits visually centred. On impl pages the comment is
      // hidden — collapse the right column to `auto` so the breadcrumb can
      // claim the full row width instead of half.
      gridTemplateColumns: {
        xs: '1fr auto auto',
        md: centerVisible ? '1fr auto 1fr' : '1fr auto auto',
      },
      alignItems: 'center',
      columnGap: { xs: 1, sm: 2 },
      py: 1.25,
      mb: 0,
      borderBottom: '1px solid var(--rule)',
      fontFamily: typography.mono,
      fontSize: '11px',
      color: 'var(--ink-muted)',
      letterSpacing: '0.04em',
    }}>
      <Box sx={{
        display: 'block',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      }}>
        {/* Root marker — hidden on xs (where the NavBar logo `any.plot()` below
            already anchors the brand) so the breadcrumb has room for the
            spec-id + lang + lib without truncating. Short single-segment
            breadcrumbs override this and keep the marker on xs (see
            keepRootMarkerOnXs above). */}
        <Box
          component={RouterLink}
          to="/"
          onClick={() => trackEvent('nav_click', { source: 'masthead_logo', target: '/' })}
          sx={{ ...linkSx, display: rootMarkerDisplay }}
        >
          ~/anyplot.ai
        </Box>

        {isLanding ? (
          <>
            <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
              {' · '}
            </Box>
            <Box
              component="a"
              href={`${REPO_URL}/tree/main`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent('nav_click', { source: 'masthead_branch', target: 'github_main' })}
              sx={linkSx}
            >
              main
            </Box>
            {' · '}
            <Box
              component="a"
              href={releaseTag ? `${REPO_URL}/releases/tag/${releaseTag}` : `${REPO_URL}/releases`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent('nav_click', { source: 'masthead_release', target: version })}
              sx={linkSx}
            >
              {version}
            </Box>
          </>
        ) : (
          segments.map((seg, i) => {
            const hasShort = seg.short && seg.short !== seg.label;
            const labelEl = hasShort ? (
              <>
                {/* xs+sm show the shorthand (`py`, `p9`); md+ has room for the
                    full name. Matches NavBar's md-breakpoint convention. */}
                <Box component="span" sx={{ display: { xs: 'inline', md: 'none' } }} title={seg.label}>
                  {seg.short}
                </Box>
                <Box component="span" sx={{ display: { xs: 'none', md: 'inline' } }}>
                  {seg.label}
                </Box>
              </>
            ) : (
              seg.label
            );
            return (
              <Box key={`${seg.label}-${i}`} component="span">
                {/* First separator follows the root marker's xs visibility —
                    showing it without the marker would dangle a stray ` · `;
                    later separators always show. */}
                <Box component="span" sx={i === 0 ? { display: rootMarkerDisplay } : undefined}>
                  {' · '}
                </Box>
                {seg.to ? (
                  <Box
                    component={RouterLink}
                    to={seg.to}
                    onClick={() => trackEvent('nav_click', { source: 'breadcrumb', target: seg.to })}
                    sx={linkSx}
                  >
                    {labelEl}
                  </Box>
                ) : (
                  <Box component="span" sx={{ ...staticSx, color: 'var(--ink-soft)' }}>
                    {labelEl}
                  </Box>
                )}
              </Box>
            );
          })
        )}
      </Box>

      <Box sx={{
        px: 2,
        fontFeatureSettings: '"tnum"',
        textAlign: 'center',
        display: { xs: 'none', md: centerVisible ? 'block' : 'none' },
      }}>
        {`${centerDelim.open} ${centerContent} ${centerDelim.close}`}
      </Box>

      <Box sx={{
        textAlign: 'right',
        gridColumn: '3',
        display: 'flex',
        justifyContent: 'flex-end',
      }}>
        <ThemeToggle mode={mode} onCycle={handleThemeToggle} />
      </Box>
    </Box>
  );
}
