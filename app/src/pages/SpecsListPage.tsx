import { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Skeleton from '@mui/material/Skeleton';
import Fab from '@mui/material/Fab';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

import { API_URL, GITHUB_URL } from '../constants';
import { buildSrcSet, getFallbackSrc, CATALOG_SIZES } from '../utils/responsiveImage';
import { useAnalytics } from '../hooks';
import { useAppData, useHomeState } from '../hooks';
import { specPath } from '../utils/paths';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import type { PlotImage } from '../types';
import { typography, colors, fontSize, semanticColors } from '../theme';

interface CatalogSpec {
  id: string;
  title: string;
  description?: string;
  images: PlotImage[];
}

export function SpecsListPage() {
  const { specsData } = useAppData();
  const { saveScrollPosition } = useHomeState();
  const { trackPageview, trackEvent } = useAnalytics();

  // Track catalog page view
  useEffect(() => {
    trackPageview('/plots');
  }, [trackPageview]);

  const [allImages, setAllImages] = useState<PlotImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [rotationIndex, setRotationIndex] = useState<Record<string, number>>({});
  const [expandedDescs, setExpandedDescs] = useState<Record<string, boolean>>({});
  const [showScrollTop, setShowScrollTop] = useState(false);

  // Fetch all images
  useEffect(() => {
    const abortController = new AbortController();

    const fetchImages = async () => {
      try {
        const res = await fetch(`${API_URL}/plots/filter`, {
          signal: abortController.signal,
        });
        if (abortController.signal.aborted) return;
        if (res.ok) {
          const data = await res.json();
          setAllImages(data.images || []);
        }
      } catch (err) {
        if (abortController.signal.aborted) return;
        console.error('Error fetching images:', err);
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false);
        }
      }
    };
    fetchImages();

    return () => abortController.abort();
  }, []);

  // Group images by spec_id and merge with spec metadata
  const catalogSpecs = useMemo(() => {
    // Group images by spec_id
    const imagesBySpec: Record<string, PlotImage[]> = {};
    for (const img of allImages) {
      const specId = img.spec_id || '';
      if (!imagesBySpec[specId]) {
        imagesBySpec[specId] = [];
      }
      imagesBySpec[specId].push(img);
    }

    // Merge with spec metadata and sort images by library name
    const specs: CatalogSpec[] = specsData
      .filter((spec) => imagesBySpec[spec.id])
      .map((spec) => ({
        id: spec.id,
        title: spec.title,
        description: spec.description,
        images: imagesBySpec[spec.id].sort((a, b) => a.library.localeCompare(b.library)),
      }));

    // Sort alphabetically by title
    specs.sort((a, b) => a.title.localeCompare(b.title));

    return specs;
  }, [allImages, specsData]);

  // Initialize random rotation indices once specs are loaded
  useEffect(() => {
    if (catalogSpecs.length > 0 && Object.keys(rotationIndex).length === 0) {
      const initialIndices: Record<string, number> = {};
      catalogSpecs.forEach((spec) => {
        initialIndices[spec.id] = Math.floor(Math.random() * spec.images.length);
      });
      setRotationIndex(initialIndices);
    }
  }, [catalogSpecs, rotationIndex]);

  // Show/hide scroll-to-top button based on scroll position
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 300);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Handle image click - rotate to next implementation
  const handleImageClick = useCallback(
    (specId: string, totalImages: number) => {
      setRotationIndex((prev) => ({
        ...prev,
        [specId]: ((prev[specId] || 0) + 1) % totalImages,
      }));
      trackEvent('catalog_rotate', { spec: specId });
    },
    [trackEvent]
  );

  if (loading || specsData.length === 0) {
    return (
      <Box sx={{ py: 4 }}>
        <Skeleton variant="text" width={200} height={40} sx={{ mb: 4 }} />
        {[1, 2, 3, 4, 5].map((i) => (
          <Box key={i} sx={{ display: 'flex', gap: 3, mb: 3 }}>
            <Skeleton variant="rectangular" width={280} height={158} sx={{ borderRadius: 1, flexShrink: 0 }} />
            <Box sx={{ flex: 1 }}>
              <Skeleton variant="text" width="60%" height={28} />
              <Skeleton variant="text" width="100%" height={20} />
              <Skeleton variant="text" width="80%" height={20} />
            </Box>
          </Box>
        ))}
      </Box>
    );
  }

  return (
    <>
      <Helmet>
        <title>plots | anyplot.ai</title>
        <meta name="description" content="Browse all Python plotting specifications alphabetically" />
        <meta property="og:title" content="plots | anyplot.ai" />
        <meta property="og:description" content="Browse all Python plotting specifications alphabetically" />
        <link rel="canonical" href="https://anyplot.ai/plots" />
      </Helmet>

      <Box sx={{ pb: 4 }}>
        {/* Breadcrumb navigation */}
        <Breadcrumb
          items={[{ label: 'anyplot.ai', shortLabel: 'ap', to: '/' }, { label: 'plots' }]}
          rightAction={
            <Box
              component="a"
              href={`${GITHUB_URL}/issues/new?template=request-new-plot.yml`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent('suggest_spec')}
              sx={{
                color: semanticColors.mutedText,
                textDecoration: 'none',
                '&:hover': { color: colors.primary },
              }}
            >
              suggest spec
            </Box>
          }
          sx={{ mb: 3, position: 'sticky', top: 0, zIndex: 100 }}
        />

        {/* Title */}
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontFamily: typography.serif,
            fontWeight: 400,
            mb: 4,
            color: colors.gray[800],
          }}
        >
          plots
          <Typography
            component="span"
            sx={{
              ml: 2,
              fontSize: fontSize.lg,
              fontWeight: 400,
              color: semanticColors.mutedText,
            }}
          >
            {catalogSpecs.length} specifications
          </Typography>
        </Typography>

        {/* Spec List */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {catalogSpecs.map((spec) => {
            const currentIndex = rotationIndex[spec.id] || 0;
            const currentImage = spec.images[currentIndex];

            return (
              <Box
                key={spec.id}
                sx={{
                  display: 'flex',
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: { xs: 2, sm: 3 },
                  p: 2,
                  bgcolor: 'var(--bg-surface)',
                  borderRadius: 2,
                  boxShadow: '0 1px 2px rgba(0,0,0,0.02), 0 24px 48px -24px rgba(0,0,0,0.08)',
                  transition: 'box-shadow 0.2s',
                  '&:hover': {
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  },
                }}
              >
                {/* Image - Click to rotate */}
                <Box
                  onClick={() => handleImageClick(spec.id, spec.images.length)}
                  sx={{
                    position: 'relative',
                    width: { xs: '100%', sm: 280 },
                    height: { xs: 180, sm: 158 },
                    borderRadius: 1.5,
                    overflow: 'hidden',
                    bgcolor: '#fff',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                    flexShrink: 0,
                    cursor: spec.images.length > 1 ? 'pointer' : 'default',
                    '&:hover .rotate-hint': {
                      opacity: spec.images.length > 1 ? 1 : 0,
                    },
                    '&:hover .library-hint': {
                      opacity: 1,
                    },
                  }}
                >
                  {currentImage && (
                    <Box
                      component="picture"
                      sx={{ display: 'contents' }}
                    >
                      <source
                        type="image/webp"
                        srcSet={buildSrcSet(currentImage.url, 'webp')}
                        sizes={CATALOG_SIZES}
                      />
                      <source
                        type="image/png"
                        srcSet={buildSrcSet(currentImage.url, 'png')}
                        sizes={CATALOG_SIZES}
                      />
                      <Box
                        component="img"
                        src={getFallbackSrc(currentImage.url)}
                        alt={spec.title}
                        sx={{
                          display: 'block',
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                        }}
                        onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                          const target = e.target as HTMLImageElement;
                          if (!target.dataset.fallback) {
                            target.dataset.fallback = '1';
                            target.closest('picture')?.querySelectorAll('source').forEach(s => s.remove());
                            target.removeAttribute('srcset');
                            target.src = currentImage.url;
                          }
                        }}
                      />
                    </Box>
                  )}

                  {/* Rotation hint badge */}
                  {spec.images.length > 1 && (
                    <Box
                      className="rotate-hint"
                      sx={{
                        position: 'absolute',
                        bottom: 4,
                        right: 4,
                        px: 1,
                        py: 0.25,
                        bgcolor: 'rgba(0,0,0,0.6)',
                        borderRadius: 1,
                        fontSize: fontSize.xs,
                        fontFamily: typography.fontFamily,
                        color: '#fff',
                        opacity: 0,
                        transition: 'opacity 0.2s',
                      }}
                    >
                      {currentIndex + 1}/{spec.images.length}
                    </Box>
                  )}

                  {/* Current library badge */}
                  <Box
                    className="library-hint"
                    sx={{
                      position: 'absolute',
                      top: 4,
                      left: 4,
                      px: 0.75,
                      py: 0.25,
                      bgcolor: 'rgba(0,0,0,0.6)',
                      borderRadius: 0.5,
                      fontSize: fontSize.xs,
                      fontFamily: typography.fontFamily,
                      color: '#fff',
                      opacity: 0,
                      transition: 'opacity 0.2s',
                    }}
                  >
                    {currentImage?.library}
                  </Box>
                </Box>

                {/* Text - Click to navigate to overview */}
                <Box
                  component={Link}
                  to={specPath(spec.id)}
                  onClick={saveScrollPosition}
                  sx={{
                    flex: 1,
                    textDecoration: 'none',
                    color: 'inherit',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                  }}
                >
                  <Typography
                    sx={{
                      fontFamily: typography.serif,
                      fontWeight: 400,
                      fontSize: fontSize.xl,
                      color: colors.gray[800],
                      mb: 0.5,
                      '&:hover': { color: colors.primary },
                    }}
                  >
                    {spec.title}
                  </Typography>
                  {spec.description && (
                    <Typography
                      onClick={(e) => {
                        if (!expandedDescs[spec.id]) {
                          e.preventDefault();
                          e.stopPropagation();
                          setExpandedDescs((prev) => ({ ...prev, [spec.id]: true }));
                        }
                      }}
                      sx={{
                        fontFamily: typography.serif,
                        fontWeight: 300,
                        fontSize: fontSize.base,
                        color: semanticColors.subtleText,
                        lineHeight: 1.6,
                        cursor: expandedDescs[spec.id] ? 'default' : 'pointer',
                        ...(!expandedDescs[spec.id] && {
                          display: '-webkit-box',
                          WebkitLineClamp: 5,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }),
                      }}
                    >
                      {spec.description}
                    </Typography>
                  )}
                </Box>
              </Box>
            );
          })}
        </Box>

        {/* Footer */}
        <Footer onTrackEvent={trackEvent} />
      </Box>

      {/* Floating scroll-to-top button */}
      <Fab
        size="small"
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          bgcolor: colors.gray[100],
          color: semanticColors.mutedText,
          opacity: showScrollTop ? 1 : 0,
          visibility: showScrollTop ? 'visible' : 'hidden',
          transition: 'opacity 0.3s, visibility 0.3s',
          '&:hover': { bgcolor: colors.gray[200], color: colors.primary },
        }}
      >
        <KeyboardArrowUpIcon />
      </Fab>
    </>
  );
}
