import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import { Link as RouterLink } from 'react-router-dom';

import { HeroSection } from '../components/HeroSection';
import { NumbersStrip } from '../components/NumbersStrip';
import { LibrariesSection } from '../components/LibrariesSection';
import { SectionHeader } from '../components/SectionHeader';
import { useAppData } from '../hooks';
import { usePlotOfTheDay } from '../hooks/usePlotOfTheDay';
import { useFeaturedSpecs, type FeaturedImpl } from '../hooks/useFeaturedSpecs';
import { GITHUB_URL } from '../constants';
import { specPath } from '../utils/paths';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';
import { colors, fontSize, semanticColors, typography } from '../theme';

export function LandingPage() {
  const { librariesData, stats } = useAppData();
  const potd = usePlotOfTheDay();
  const featured = useFeaturedSpecs(4);

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

      <LibrariesSection
        libraries={librariesData}
        onLibraryClick={() => {}}
        widthTier="catalog"
      />

      <PaletteSection />
    </>
  );
}

/**
 * Palette section — mirrors SpecsSection's two-column layout: description on
 * the left, labelled palette strip on the right.
 */
function PaletteSection() {
  return (
    <Box sx={{ py: { xs: 4, md: 7 } }}>
      <SectionHeader prompt="§" title={<em>palette</em>} linkText="palette.explore()" linkTo="/palette" />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1fr) minmax(0, 1.2fr)' },
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
              sx={{
                color: 'var(--ink)',
                textDecoration: 'none',
                borderBottom: '1px dotted currentColor',
                '&:hover': { color: colors.primary },
              }}
            >
              Okabe &amp; Ito (2008)
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
  return (
    <Box sx={{ py: { xs: 4, md: 7 } }}>
      <SectionHeader prompt="§" title={<em>specifications</em>} linkText="specs.all()" linkTo="/specs" />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1fr) minmax(0, 1.2fr)' },
          gap: { xs: 4, md: 8, lg: 12 },
          alignItems: 'start',
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
            a spec is a short, library-agnostic markdown document —{' '}
            <Box component="span" sx={{ color: 'var(--ink)' }}>
              what the plot shows, what data it needs, and when to use it.
            </Box>{' '}
            from that single source, implementations are generated for every
            supported library. new specs come from github issues; anyone can
            propose one.
          </Box>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            <ActionChip to="/specs" label={`browse ${specCount ?? ''} specs`.trim()} />
            <ActionChip
              href={`${GITHUB_URL}/issues/new?template=request-new-plot.yml`}
              label="suggest spec"
              external
            />
          </Box>
        </Box>

        <FeaturedGrid featured={featured} />
      </Box>
    </Box>
  );
}

function FeaturedGrid({ featured }: { featured: FeaturedImpl[] | null }) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(2, 1fr)' },
        gap: 2,
      }}
    >
      {(featured ?? Array.from({ length: 4 }, () => null)).map((item, i) => (
        <FeaturedThumb key={item?.spec_id ? `${item.spec_id}-${item.library_id}` : `skel-${i}`} item={item} />
      ))}
    </Box>
  );
}

interface ActionChipProps {
  to?: string;
  href?: string;
  label: string;
  external?: boolean;
}

function ActionChip({ to, href, label, external }: ActionChipProps) {
  const sx = {
    fontFamily: typography.mono,
    fontSize: '13px',
    fontWeight: 500,
    color: 'var(--ink-muted)',
    bgcolor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    px: 1.25,
    py: 1,
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'baseline',
    transition: 'color 0.2s, background 0.2s',
    '&::before': { content: '"."', color: 'inherit' },
    '&:hover': { color: colors.primary, bgcolor: 'var(--bg-elevated)' },
  } as const;

  if (href) {
    return (
      <Box
        component="a"
        href={href}
        target={external ? '_blank' : undefined}
        rel={external ? 'noopener noreferrer' : undefined}
        sx={sx}
      >
        {label}()
      </Box>
    );
  }
  return (
    <Box component={RouterLink} to={to ?? '#'} sx={sx}>
      {label}()
    </Box>
  );
}

/**
 * Compact terminal-window card — mirrors PlotOfTheDay's shape (top bar with
 * `$` prompt, square-ish image body, bottom bar with `>>>` output) so the
 * featured grid feels part of the same language as the hero POTD.
 */
function FeaturedThumb({ item }: { item: FeaturedImpl | null }) {
  const cardSx = {
    display: 'flex',
    flexDirection: 'column' as const,
    borderRadius: 2,
    overflow: 'hidden',
    border: `1px solid ${colors.gray[200]}`,
    boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
    transition: 'box-shadow 0.25s, transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    textDecoration: 'none',
    color: 'inherit',
    bgcolor: 'var(--bg-surface)',
    '&:hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 6px 24px rgba(0,0,0,0.08)',
    },
  } as const;

  const barSx = {
    display: 'flex',
    alignItems: 'center',
    px: 1.25,
    py: 0.5,
    bgcolor: colors.gray[100],
    gap: 0.75,
    fontFamily: typography.mono,
    fontSize: fontSize.xxs,
  } as const;

  if (!item || !item.preview_url) {
    return (
      <Box sx={cardSx}>
        <Box sx={{ ...barSx, borderBottom: `1px solid ${colors.gray[200]}` }}>
          <Box component="span" sx={{ color: colors.gray[300] }}>$</Box>
          <Box component="span" sx={{ color: colors.gray[300] }}>&nbsp;</Box>
        </Box>
        <Box sx={{ aspectRatio: '16 / 10', bgcolor: 'var(--bg-elevated)' }} />
        <Box sx={{ ...barSx, borderTop: `1px solid ${colors.gray[200]}` }}>
          <Box component="span" sx={{ color: colors.gray[300] }}>&gt;&gt;&gt;</Box>
        </Box>
      </Box>
    );
  }

  return (
    <Box component={RouterLink} to={specPath(item.spec_id, item.language, item.library_id)} sx={cardSx}>
      {/* Top bar — mimics POTD's `$ python …` prompt */}
      <Box sx={{ ...barSx, borderBottom: `1px solid ${colors.gray[200]}` }}>
        <Box component="span" sx={{ color: colors.primary, fontWeight: 600 }}>$</Box>
        <Box
          component="span"
          sx={{
            color: semanticColors.mutedText,
            flex: 1,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {item.spec_id}.py
        </Box>
      </Box>

      {/* Image body */}
      <Box sx={{ aspectRatio: '16 / 10', overflow: 'hidden' }}>
        <Box component="picture" sx={{ display: 'block', width: '100%', height: '100%' }}>
          <source type="image/webp" srcSet={buildSrcSet(item.preview_url, 'webp')} sizes="(max-width: 599px) 50vw, 25vw" />
          <source type="image/png" srcSet={buildSrcSet(item.preview_url, 'png')} sizes="(max-width: 599px) 50vw, 25vw" />
          <Box
            component="img"
            src={getFallbackSrc(item.preview_url)}
            alt={item.spec_title}
            loading="lazy"
            sx={{ display: 'block', width: '100%', height: '100%', objectFit: 'cover' }}
          />
        </Box>
      </Box>

      {/* Bottom bar — mimics POTD's `>>> plot.png saved | library` */}
      <Box sx={{ ...barSx, borderTop: `1px solid ${colors.gray[200]}` }}>
        <Box component="span" sx={{ color: colors.primary }}>&gt;&gt;&gt;</Box>
        <Box
          component="span"
          sx={{
            color: semanticColors.mutedText,
            flex: 1,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          plot.png saved
        </Box>
        <Box component="span" sx={{ color: colors.gray[300] }}>│</Box>
        <Box component="span" sx={{ color: semanticColors.mutedText, flexShrink: 0 }}>
          {item.library_id}
        </Box>
      </Box>
    </Box>
  );
}
