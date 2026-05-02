import { useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import { Link as RouterLink, useNavigate } from 'react-router-dom';

import { HeroSection } from '../components/HeroSection';
import { NumbersStrip } from '../components/NumbersStrip';
import { LibrariesSection } from '../components/LibrariesSection';
import { SectionHeader } from '../components/SectionHeader';
import { useAppData, useAnalytics } from '../hooks';
import { usePlotOfTheDay } from '../hooks/usePlotOfTheDay';
import { useFeaturedSpecs, type FeaturedImpl } from '../hooks/useFeaturedSpecs';
import { useTheme } from '../hooks/useLayoutContext';
import { GITHUB_URL } from '../constants';
import { specPath } from '../utils/paths';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';
import { selectPreviewUrl } from '../utils/themedPreview';
import { colors, semanticColors, typography } from '../theme';

export function LandingPage() {
  const { librariesData, stats } = useAppData();
  const potd = usePlotOfTheDay();
  const featured = useFeaturedSpecs(5);
  const navigate = useNavigate();
  const { trackEvent, trackPageview } = useAnalytics();

  useEffect(() => {
    trackPageview('/');
  }, [trackPageview]);

  const handleLibraryClick = (lib: string) => {
    trackEvent('nav_click', { source: 'library_card', target: '/plots', value: lib });
    navigate(`/plots?lib=${encodeURIComponent(lib)}`);
  };

  return (
    <>
      <Helmet>
        <title>any.plot() — any library.</title>
        <meta
          name="description"
          content="any library. get inspired. grab the code. make it yours. human ideas, ai builds the rest. 9 python plotting libraries, colorblind-safe, open source."
        />
        <link rel="canonical" href="https://anyplot.ai/" />
      </Helmet>

      {/* Hero — fills the viewport so the fold shows only the hero */}
      <Box
        component="section"
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          minHeight: { xs: 'auto', md: 'calc(88svh - 88px)' },
          pb: { xs: 4, md: 7 },
        }}
      >
        <HeroSection potd={potd} />
        <NumbersStrip stats={stats} />
      </Box>

      <SpecsSection specCount={stats?.specs} featured={featured} />

      <MapSection specCount={stats?.specs} />

      <LibrariesSection
        libraries={librariesData}
        onLibraryClick={handleLibraryClick}
        widthTier="catalog"
      />

      <PaletteSection />
    </>
  );
}

/**
 * Map section — teases the interactive force-directed map at /map. Mirrors
 * SpecsSection / PaletteSection two-column layout: short description on the
 * left, decorative SVG cluster preview on the right. The preview is purely
 * static (no data fetch, no force simulation) so it stays cheap on the
 * landing page; it only hints at the real map's clustering aesthetic using
 * the same Okabe-Ito palette.
 */
function MapSection({ specCount }: { specCount?: number }) {
  const { trackEvent } = useAnalytics();
  return (
    <Box sx={{ py: { xs: 2, md: 3 } }}>
      <SectionHeader prompt="❯" title={<em>map</em>} linkText="map.explore()" linkTo="/map" />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(0, 1.1fr) minmax(0, 1fr)' },
          gap: { xs: 4, md: 8, lg: 12 },
          alignItems: 'center',
        }}
      >
        <Box
          sx={{
            fontFamily: typography.serif,
            fontSize: { xs: '1rem', md: '1.25rem' },
            lineHeight: 1.55,
            color: 'var(--ink-soft)',
            fontWeight: 300,
            maxWidth: '52ch',
          }}
        >
          {specCount != null ? `all ${specCount} specs` : 'every spec'} on a single canvas —{' '}
          <Box component="span" sx={{ color: 'var(--ink)' }}>
            clustered by tag similarity, coloured by plot type, searchable.
          </Box>{' '}
          zoom in for thumbnails, hover for details, click to open the spec.
        </Box>

        <Box
          component={RouterLink}
          to="/map"
          onClick={() => trackEvent('nav_click', { source: 'map_teaser_preview', target: '/map' })}
          sx={{
            display: 'block',
            textDecoration: 'none',
            color: 'inherit',
            border: '1px solid var(--rule)',
            borderRadius: 2,
            bgcolor: 'var(--bg-surface)',
            overflow: 'hidden',
            position: 'relative',
            transition: 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s, border-color 0.25s',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '2px',
              background: colors.primary,
              transform: 'scaleX(0)',
              transformOrigin: 'left',
              transition: 'transform 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
              zIndex: 1,
            },
            '&:hover': {
              transform: 'translateY(-3px)',
              boxShadow: '0 16px 32px -12px rgba(0,0,0,0.08)',
              borderColor: 'rgba(0, 158, 115, 0.2)',
              '&::before': { transform: 'scaleX(1)' },
            },
          }}
          aria-label="Open the interactive specifications map"
        >
          <MapClusterPreview />
        </Box>
      </Box>
    </Box>
  );
}

/**
 * Decorative SVG mini-cluster — three loose groups of circles in Okabe-Ito
 * cluster colours, connected by hairline edges. Static (no force simulation,
 * no data fetch) so it's cheap to render; the aspect ratio matches the
 * featured-thumb cards (16:10) for visual rhythm. Positions are hand-picked
 * to read as "three blobs gently bridged" — like the real map at low zoom.
 */
const MAP_PREVIEW_NODES: Array<{ x: number; y: number; r: number; cluster: 0 | 1 | 2 | 3 }> = [
  // Cluster A — left, brand green
  { x: 90, y: 95, r: 9, cluster: 0 },
  { x: 70, y: 130, r: 7, cluster: 0 },
  { x: 115, y: 125, r: 8, cluster: 0 },
  { x: 95, y: 160, r: 6, cluster: 0 },
  { x: 135, y: 95, r: 6, cluster: 0 },
  { x: 60, y: 100, r: 5, cluster: 0 },
  // Cluster B — top-right, vermillion
  { x: 320, y: 70, r: 9, cluster: 1 },
  { x: 350, y: 100, r: 7, cluster: 1 },
  { x: 295, y: 105, r: 6, cluster: 1 },
  { x: 365, y: 60, r: 5, cluster: 1 },
  { x: 330, y: 130, r: 7, cluster: 1 },
  // Cluster C — bottom-right, blue
  { x: 290, y: 200, r: 8, cluster: 2 },
  { x: 325, y: 220, r: 9, cluster: 2 },
  { x: 360, y: 195, r: 6, cluster: 2 },
  { x: 305, y: 235, r: 6, cluster: 2 },
  { x: 350, y: 240, r: 5, cluster: 2 },
  // Bridges — neutral nodes
  { x: 200, y: 130, r: 6, cluster: 3 },
  { x: 225, y: 175, r: 5, cluster: 3 },
  { x: 175, y: 165, r: 4, cluster: 3 },
];

const MAP_PREVIEW_LINKS: Array<[number, number]> = [
  // Cluster A internal
  [0, 1], [0, 2], [1, 2], [2, 3], [0, 4], [1, 5], [0, 5],
  // Cluster B internal
  [6, 7], [6, 8], [7, 9], [6, 10], [7, 10],
  // Cluster C internal
  [11, 12], [12, 13], [11, 14], [13, 14], [14, 15], [12, 15],
  // Bridges via neutrals
  [2, 16], [16, 8], [3, 17], [17, 11], [16, 17], [17, 18], [18, 3],
];

const CLUSTER_PALETTE = ['#009E73', '#D55E00', '#0072B2'] as const;

function MapClusterPreview() {
  return (
    <Box
      component="svg"
      viewBox="0 0 420 280"
      aria-hidden="true"
      sx={{
        display: 'block',
        width: '100%',
        height: 'auto',
        aspectRatio: '16 / 10',
        bgcolor: 'var(--bg-elevated)',
      }}
    >
      <g stroke="var(--rule)" strokeWidth={0.75} fill="none" opacity={0.85}>
        {MAP_PREVIEW_LINKS.map(([a, b], i) => {
          const na = MAP_PREVIEW_NODES[a];
          const nb = MAP_PREVIEW_NODES[b];
          return <line key={i} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} />;
        })}
      </g>
      {MAP_PREVIEW_NODES.map((n, i) => {
        const fill = n.cluster === 3 ? 'var(--ink-soft)' : CLUSTER_PALETTE[n.cluster];
        const opacity = n.cluster === 3 ? 0.45 : 0.92;
        return (
          <circle
            key={i}
            cx={n.x}
            cy={n.y}
            r={n.r}
            fill={fill}
            opacity={opacity}
            stroke="var(--bg-surface)"
            strokeWidth={1.5}
          />
        );
      })}
    </Box>
  );
}

/**
 * Palette section — mirrors SpecsSection's two-column layout: description on
 * the left, labelled palette strip on the right.
 */
function PaletteSection() {
  const { trackEvent } = useAnalytics();
  return (
    <Box sx={{ py: { xs: 2, md: 3 } }}>
      <SectionHeader prompt="❯" title={<em>palette</em>} linkText="palette.explore()" linkTo="/palette" />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(0, 1fr) minmax(0, 1.2fr)' },
          gap: { xs: 4, md: 8, lg: 12 },
          alignItems: 'center',
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Box
            sx={{
              fontFamily: typography.serif,
              fontSize: { xs: '1rem', md: '1.25rem' },
              lineHeight: 1.55,
              color: 'var(--ink-soft)',
              fontWeight: 300,
              maxWidth: '52ch',
            }}
          >
            a colourblind-safe set of eight, proposed by{' '}
            <Box
              component="a"
              href="https://jfly.uni-koeln.de/color/"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent('nav_click', { source: 'palette_okabe_ito', target: 'jfly_uni_koeln' })}
              sx={{
                color: 'var(--ink)',
                textDecoration: 'none',
                borderBottom: '1px dotted currentColor',
                '&:hover': { color: colors.primary },
              }}
            >
              Okabe &amp; Ito (2002, rev. 2008)
            </Box>
            . every plot in the catalogue picks from it — and so does this
            site, accent for accent.
          </Box>
        </Box>

        <LabelledPaletteStrip />
      </Box>
    </Box>
  );
}

const PALETTE = [
  { background: '#009E73', hex: '#009E73', name: 'bluish green' },
  { background: '#D55E00', hex: '#D55E00', name: 'vermillion' },
  { background: '#0072B2', hex: '#0072B2', name: 'blue' },
  { background: '#CC79A7', hex: '#CC79A7', name: 'reddish purple' },
  { background: '#E69F00', hex: '#E69F00', name: 'orange' },
  { background: '#56B4E9', hex: '#56B4E9', name: 'sky blue' },
  { background: '#F0E442', hex: '#F0E442', name: 'yellow' },
  { background: 'var(--ink)', hex: 'adaptive', name: 'ink' },
] as const;

function LabelledPaletteStrip() {
  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          borderRadius: '6px',
          overflow: 'hidden',
          '&:hover .swatch': { flex: 0.6 },
          '&:hover .swatch:hover': { flex: 3 },
        }}
      >
        {PALETTE.map(({ background, hex }) => (
          <Box
            key={background}
            className="swatch"
            sx={{
              flex: 1,
              height: 120,
              background,
              transition: 'flex 0.3s',
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              '& .hex-label': { opacity: 0, transition: 'opacity 0.2s' },
              '&:hover .hex-label': { opacity: 1 },
            }}
          >
            <Box
              className="hex-label"
              sx={{
                fontFamily: typography.mono,
                fontSize: '12px',
                fontWeight: 500,
                color: '#fff',
                bgcolor: 'rgba(0,0,0,0.65)',
                px: 1,
                py: 0.25,
                borderRadius: 1,
                whiteSpace: 'nowrap',
                pointerEvents: 'none',
              }}
            >
              {hex}
            </Box>
          </Box>
        ))}
      </Box>
      <Box sx={{ display: 'grid', gridTemplateColumns: `repeat(${PALETTE.length}, 1fr)`, mt: 1 }}>
        {PALETTE.map(({ background, name }) => (
          <Box
            key={background}
            sx={{
              fontFamily: typography.mono,
              fontSize: { xs: '9px', md: '10px' },
              color: semanticColors.mutedText,
              textAlign: 'center',
              px: 0.5,
              lineHeight: 1.3,
            }}
          >
            {name}
          </Box>
        ))}
      </Box>
    </Box>
  );
}

/**
 * Specs section — catalog-tier layout. Description sits on the left, a 2×2
 * preview grid of featured implementations on the right so visitors see what
 * specs become.
 */
function SpecsSection({ specCount, featured }: { specCount?: number; featured: FeaturedImpl[] | null }) {
  const { trackEvent } = useAnalytics();
  return (
    <Box sx={{ py: { xs: 2, md: 3 } }}>
      <SectionHeader prompt="❯" title={<em>specifications</em>} linkText="specs.all()" linkTo="/specs" />

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: { xs: 4, md: 5 } }}>
        <Box
          sx={{
            fontFamily: typography.serif,
            fontSize: { xs: '1rem', md: '1.25rem' },
            lineHeight: 1.55,
            color: 'var(--ink-soft)',
            fontWeight: 300,
            maxWidth: '52ch',
          }}
        >
          a spec is a short, library-agnostic markdown document —{' '}
          <Box component="span" sx={{ color: 'var(--ink)' }}>
            what the plot shows, what data it needs, and when to use it.
          </Box>{' '}
          from that single source, implementations are generated for every
          supported library. new specs come from github issues; anyone can
          propose one.
        </Box>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          <MethodLink
            href={`${GITHUB_URL}/issues/new?template=request-new-plot.yml`}
            subject="spec"
            verb="suggest"
            external
            source="suggest_spec_link"
          />
        </Box>
      </Box>

      <FeaturedGrid featured={featured} />
      {specCount != null && featured && featured.length < specCount && (
        <Box
          component={RouterLink}
          to="/specs"
          onClick={() => trackEvent('nav_click', { source: 'specs_more_link', target: '/specs' })}
          sx={{
            display: 'inline-block',
            mt: 2.5,
            fontFamily: typography.mono,
            fontSize: '12px',
            color: semanticColors.mutedText,
            textDecoration: 'none',
            transition: 'color 0.2s',
            '&:hover': { color: colors.primary },
          }}
        >
          + {specCount - featured.length} more in the catalogue →
        </Box>
      )}
    </Box>
  );
}

function FeaturedGrid({ featured }: { featured: FeaturedImpl[] | null }) {
  return (
    <Box
      sx={{
        display: 'grid',
        // 2 cols on phones, 3 on tablets, 5 on desktop — always a full row,
        // never hanging singletons.
        gridTemplateColumns: {
          xs: 'repeat(2, 1fr)',
          sm: 'repeat(3, 1fr)',
          md: 'repeat(5, 1fr)',
        },
        alignItems: 'stretch',
        gap: { xs: 2, md: 2.5 },
      }}
    >
      {(featured ?? Array.from({ length: 5 }, () => null)).map((item, i) => (
        <FeaturedThumb
          key={item?.spec_id ? `${item.spec_id}-${item.library_id}` : `skel-${i}`}
          item={item}
        />
      ))}
    </Box>
  );
}

interface MethodLinkProps {
  to?: string;
  href?: string;
  subject: string;
  verb: string;
  external?: boolean;
  source?: string;
}

/**
 * Two-tone subject.verb() link — matches HeroSection.SecondaryLink: subject
 * rendered muted (opacity 0.7), `.verb()` at the link's current colour.
 * Whole element turns primary-green on hover; subject brightens to full.
 */
function MethodLink({ to, href, subject, verb, external, source }: MethodLinkProps) {
  const { trackEvent } = useAnalytics();
  const handleClick = source
    ? () => trackEvent('nav_click', { source, target: href ?? to ?? '' })
    : undefined;
  const sx = {
    fontFamily: typography.mono,
    fontSize: '13px',
    color: 'var(--ink-soft)',
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'baseline',
    transition: 'color 0.2s',
    '& .subj': { opacity: 0.7, transition: 'opacity 0.2s' },
    '&:hover': { color: colors.primary },
    '&:hover .subj': { opacity: 1 },
    '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2, borderRadius: '2px' },
  } as const;

  const content = (
    <>
      <Box component="span" className="subj">{subject}</Box>
      {`.${verb}()`}
    </>
  );

  if (href) {
    return (
      <Box
        component="a"
        href={href}
        target={external ? '_blank' : undefined}
        rel={external ? 'noopener noreferrer' : undefined}
        onClick={handleClick}
        sx={sx}
      >
        {content}
      </Box>
    );
  }
  return (
    <Box component={RouterLink} to={to ?? '#'} onClick={handleClick} sx={sx}>
      {content}
    </Box>
  );
}

/**
 * Featured plot card — mirrors the mockup's `.lib-card` pattern: bordered
 * surface with green accent bar that slides in from the left on hover,
 * translateY lift, shadow. Inside: the preview image (inset, rounded) +
 * spec title underneath. The whole card is the link to the spec hub.
 */
function FeaturedThumb({ item }: { item: FeaturedImpl | null }) {
  const { isDark } = useTheme();
  const { trackEvent } = useAnalytics();
  const previewUrl = selectPreviewUrl(item, isDark);
  const cardSx = {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 1.5,
    bgcolor: 'var(--bg-surface)',
    border: '1px solid var(--rule)',
    borderRadius: 2,
    p: 1.5,
    minWidth: 0,
    position: 'relative',
    overflow: 'hidden',
    textDecoration: 'none',
    color: 'inherit',
    transition: 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s, border-color 0.25s',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '2px',
      background: colors.primary,
      transform: 'scaleX(0)',
      transformOrigin: 'left',
      transition: 'transform 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
      zIndex: 1,
    },
    '&:hover': {
      transform: 'translateY(-3px)',
      boxShadow: '0 16px 32px -12px rgba(0,0,0,0.08)',
      borderColor: 'rgba(0, 158, 115, 0.2)',
      '&::before': { transform: 'scaleX(1)' },
    },
  } as const;

  const imageSx = {
    display: 'block',
    width: '100%',
    aspectRatio: '16 / 10',
    borderRadius: 1,
    overflow: 'hidden',
    bgcolor: 'var(--bg-elevated)',
  } as const;

  const titleSx = {
    fontFamily: typography.serif,
    fontSize: { xs: '0.875rem', md: '0.9375rem' },
    fontWeight: 400,
    lineHeight: 1.35,
    color: 'var(--ink)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    px: 0.25,
  } as const;

  const descSx = {
    fontFamily: typography.serif,
    fontSize: { xs: '0.75rem', md: '0.8125rem' },
    fontWeight: 300,
    lineHeight: 1.45,
    color: semanticColors.mutedText,
    px: 0.25,
    pb: 0.25,
    display: '-webkit-box',
    WebkitLineClamp: 3,
    WebkitBoxOrient: 'vertical' as const,
    overflow: 'hidden',
  } as const;

  if (!item || !previewUrl) {
    return (
      <Box sx={cardSx}>
        <Box sx={imageSx} />
        <Box sx={{ ...titleSx, height: 14, width: '70%', bgcolor: 'var(--bg-elevated)', borderRadius: 0.5 }} />
        <Box sx={{ height: 12, width: '90%', bgcolor: 'var(--bg-elevated)', borderRadius: 0.5, mx: 0.25 }} />
      </Box>
    );
  }

  return (
    <Box
      component={RouterLink}
      to={specPath(item.spec_id)}
      onClick={() => trackEvent('nav_click', { source: 'featured_thumb', target: 'spec_hub', spec: item.spec_id, library: item.library_id })}
      sx={cardSx}
    >
      <Box sx={imageSx}>
        <Box component="picture" key={previewUrl} sx={{ display: 'block', width: '100%', height: '100%' }}>
          <source type="image/webp" srcSet={buildSrcSet(previewUrl, 'webp')} sizes="(max-width: 599px) 50vw, 25vw" />
          <source type="image/png" srcSet={buildSrcSet(previewUrl, 'png')} sizes="(max-width: 599px) 50vw, 25vw" />
          <Box
            component="img"
            src={getFallbackSrc(previewUrl)}
            alt={item.spec_title}
            loading="lazy"
            sx={{ display: 'block', width: '100%', height: '100%', objectFit: 'cover' }}
          />
        </Box>
      </Box>
      <Box sx={titleSx}>{item.spec_title}</Box>
      {item.spec_description && <Box sx={descSx}>{item.spec_description}</Box>}
    </Box>
  );
}

