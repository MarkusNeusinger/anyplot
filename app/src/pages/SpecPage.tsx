import { useState, useEffect, useMemo, useCallback, lazy, Suspense } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import Skeleton from '@mui/material/Skeleton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import BugReportIcon from '@mui/icons-material/BugReport';
import ListIcon from '@mui/icons-material/List';
import { NotFoundPage } from './NotFoundPage';

import { API_URL, GITHUB_URL, LIB_ABBREV } from '../constants';
import { typography, colors, fontSize, semanticColors } from '../theme';
import { useAnalytics, useCodeFetch } from '../hooks';
import { useAppData } from '../hooks';
import { LibraryPills } from '../components/LibraryPills';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { RelatedSpecs } from '../components/RelatedSpecs';

const SpecTabs = lazy(() => import('../components/SpecTabs').then(m => ({ default: m.SpecTabs })));
const SpecOverview = lazy(() => import('../components/SpecOverview').then(m => ({ default: m.SpecOverview })));
const SpecDetailView = lazy(() => import('../components/SpecDetailView').then(m => ({ default: m.SpecDetailView })));
import type { Implementation } from '../types';

interface SpecDetail {
  id: string;
  title: string;
  description: string;
  applications?: string[];
  data?: string[];
  notes?: string[];
  tags?: Record<string, string[]>;
  created?: string;
  updated?: string;
  implementations: Implementation[];
}

export function SpecPage() {
  const { specId, library: urlLibrary } = useParams();
  const navigate = useNavigate();
  const { trackPageview, trackEvent } = useAnalytics();
  const { librariesData } = useAppData();

  const [specData, setSpecData] = useState<SpecDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [descExpanded, setDescExpanded] = useState(false);
  const [codeCopied, setCodeCopied] = useState<string | null>(null);
  const [openTooltip, setOpenTooltip] = useState<string | null>(null);
  const [highlightedTags, setHighlightedTags] = useState<string[]>([]);
  const { fetchCode, getCode } = useCodeFetch();

  // Get library metadata by ID
  const getLibraryMeta = useCallback(
    (libraryId: string) => librariesData.find((lib) => lib.id === libraryId),
    [librariesData]
  );

  // Mode: overview (no library) vs detail (with library)
  const isOverviewMode = !urlLibrary;
  const selectedLibrary = urlLibrary || null;

  // Fetch spec data
  useEffect(() => {
    if (!specId) return;

    const fetchSpec = async () => {
      setLoading(true);
      setError(null);
      setImageLoaded(false);
      setHighlightedTags([]);

      try {
        const res = await fetch(`${API_URL}/specs/${specId}`);
        if (!res.ok) {
          setError(res.status === 404 ? 'Spec not found' : 'Failed to load spec');
          return;
        }

        const data: SpecDetail = await res.json();
        setSpecData(data);

        // Validate library if provided
        if (urlLibrary && !data.implementations.some((impl) => impl.library_id === urlLibrary)) {
          navigate(`/${specId}`, { replace: true });
        }
      } catch (err) {
        console.error('Error fetching spec:', err);
        setError('Failed to load spec');
      } finally {
        setLoading(false);
      }
    };

    fetchSpec();
  }, [specId, urlLibrary, navigate]);

  // Get current implementation (only in detail mode)
  const currentImpl = useMemo(() => {
    if (!specData || !selectedLibrary) return null;
    return specData.implementations.find((impl) => impl.library_id === selectedLibrary) || null;
  }, [specData, selectedLibrary]);

  // Prefetch code in background when impl detail page opens
  useEffect(() => {
    if (specId && selectedLibrary) {
      fetchCode(specId, selectedLibrary);
    }
  }, [specId, selectedLibrary, fetchCode]);

  // Get code from cache (populated by prefetch or on-demand)
  const currentCode = specId && selectedLibrary ? getCode(specId, selectedLibrary) : null;

  // Handle library switch (in detail mode)
  const handleLibrarySelect = useCallback(
    (libraryId: string) => {
      setImageLoaded(false);
      navigate(`/${specId}/${libraryId}`, { replace: true });
    },
    [specId, navigate]
  );

  // Handle implementation click (in overview mode)
  const handleImplClick = useCallback(
    (libraryId: string) => {
      navigate(`/${specId}/${libraryId}`);
    },
    [specId, navigate]
  );

  // Handle download
  const [downloadDone, setDownloadDone] = useState<string | null>(null);

  const handleDownload = useCallback(
    async (impl: Implementation) => {
      if (!specId) return;
      const link = document.createElement('a');
      link.href = `${API_URL}/download/${specId}/${impl.library_id}`;
      link.download = `${specId}-${impl.library_id}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setDownloadDone(impl.library_id);
      setTimeout(() => setDownloadDone(null), 2000);
      trackEvent('download_image', {
        spec: specId,
        library: impl.library_id,
        page: isOverviewMode ? 'spec_overview' : 'spec_detail',
      });
    },
    [specId, trackEvent, isOverviewMode],
  );

  // Handle copy code (fetches on-demand if not prefetched yet)
  const handleCopyCode = useCallback(
    async (impl: Implementation) => {
      try {
        const code = impl.code || (specId ? await fetchCode(specId, impl.library_id) : null);
        if (!code) return;
        await navigator.clipboard.writeText(code);
        setCodeCopied(impl.library_id);
        trackEvent('copy_code', {
          spec: specId,
          library: impl.library_id,
          method: 'image',
          page: isOverviewMode ? 'spec_overview' : 'spec_detail',
        });
        setTimeout(() => setCodeCopied(null), 2000);
      } catch (err) {
        console.error('Copy failed:', err);
      }
    },
    [specId, trackEvent, isOverviewMode, fetchCode]
  );

  // Build report issue URL
  const buildReportUrl = useCallback(() => {
    const params = new URLSearchParams({
      template: 'report-plot-issue.yml',
      spec_id: specId || '',
    });
    return `${GITHUB_URL}/issues/new?${params.toString()}`;
  }, [specId]);

  // Track page view
  useEffect(() => {
    if (specData) {
      if (isOverviewMode) {
        trackPageview(`/${specId}`);
      } else if (selectedLibrary) {
        trackPageview(`/${specId}/${selectedLibrary}`);
      }
    }
  }, [specData, isOverviewMode, selectedLibrary, specId, trackPageview]);

  // Keyboard shortcuts: left/right arrows switch libraries in detail mode
  useEffect(() => {
    if (isOverviewMode || !specData) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return;
      const sorted = [...specData.implementations].sort((a, b) => a.library_id.localeCompare(b.library_id));
      const idx = sorted.findIndex((impl) => impl.library_id === selectedLibrary);
      if (idx < 0) return;

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        const prev = (idx - 1 + sorted.length) % sorted.length;
        handleLibrarySelect(sorted[prev].library_id);
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        const next = (idx + 1) % sorted.length;
        handleLibrarySelect(sorted[next].library_id);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOverviewMode, specData, selectedLibrary, handleLibrarySelect]);

  // Loading state
  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Skeleton variant="rectangular" width="100%" height={400} sx={{ maxWidth: 800, mx: 'auto', borderRadius: 2 }} />
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', mt: 2 }}>
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rounded" width={80} height={32} />
          ))}
        </Box>
      </Box>
    );
  }

  // Error state
  if (error === 'Spec not found' || (!error && !specData)) {
    return <NotFoundPage />;
  }
  if (error) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h5" sx={{ mb: 2, color: semanticColors.mutedText }}>
          {error}
        </Typography>
        <Button component={Link} to="/" startIcon={<ArrowBackIcon />} sx={{ color: colors.primary }}>
          Back to Home
        </Button>
      </Box>
    );
  }

  // After loading/error/not-found guards, specData is guaranteed to be non-null
  if (!specData) return null;

  return (
    <>
      <Helmet>
        <title>
          {isOverviewMode ? `${specData.title} | pyplots.ai` : `${specData.title} - ${selectedLibrary} | pyplots.ai`}
        </title>
        <meta name="description" content={specData.description} />
        <meta
          property="og:title"
          content={
            isOverviewMode ? `${specData.title} | pyplots.ai` : `${specData.title} - ${selectedLibrary} | pyplots.ai`
          }
        />
        <meta property="og:description" content={specData.description} />
        {currentImpl?.preview_url && <meta property="og:image" content={currentImpl.preview_url} />}
        <meta
          property="og:url"
          content={isOverviewMode ? `https://pyplots.ai/${specId}` : `https://pyplots.ai/${specId}/${selectedLibrary}`}
        />
        <link rel="canonical" href={isOverviewMode ? `https://pyplots.ai/${specId}` : `https://pyplots.ai/${specId}/${selectedLibrary}`} />
      </Helmet>

      <Box sx={{ pb: 4 }}>
        {/* Breadcrumb navigation */}
        <Breadcrumb
          items={
            isOverviewMode
              ? [
                  { label: 'pyplots.ai', shortLabel: 'pp', to: '/' },
                  { label: specId || '' },
                ]
              : [
                  { label: 'pyplots.ai', shortLabel: 'pp', to: '/' },
                  { label: specId || '', to: `/${specId}` },
                  { label: selectedLibrary || '', shortLabel: LIB_ABBREV[selectedLibrary || ''] || selectedLibrary || '' },
                ]
          }
          rightAction={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1.5, md: 0 } }}>
              <Tooltip title="catalog">
                <Box
                  component={Link}
                  to="/catalog"
                  sx={{
                    color: semanticColors.mutedText,
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    '&:hover': { color: colors.primary },
                  }}
                >
                  <ListIcon sx={{ fontSize: '1.4rem', display: { xs: 'block', md: 'none' } }} />
                  <Box
                    component="span"
                    sx={{
                      display: { xs: 'none', md: 'block' },
                      fontFamily: typography.fontFamily,
                      fontSize: fontSize.base,
                    }}
                  >
                    catalog
                  </Box>
                </Box>
              </Tooltip>
              <Box component="span" sx={{ mx: 0.5, color: semanticColors.mutedText, display: { xs: 'none', md: 'inline' } }}>·</Box>
              <Tooltip title="report issue">
                <Box
                  component="a"
                  href={buildReportUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => trackEvent('report_issue', { spec: specId, library: selectedLibrary || undefined })}
                  sx={{
                    color: semanticColors.mutedText,
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    '&:hover': { color: colors.primary },
                  }}
                >
                  <BugReportIcon sx={{ fontSize: '1.4rem', display: { xs: 'block', md: 'none' } }} />
                  <Box
                    component="span"
                    sx={{
                      display: { xs: 'none', md: 'block' },
                      fontFamily: typography.fontFamily,
                      fontSize: fontSize.base,
                    }}
                  >
                    report issue
                  </Box>
                </Box>
              </Tooltip>
            </Box>
          }
        />

        {/* Title */}
        <Typography
          variant="h4"
          component="h1"
          sx={{
            textAlign: 'center',
            fontFamily: typography.fontFamily,
            fontWeight: 600,
            fontSize: { xs: '1.375rem', sm: '1.625rem', md: '2.125rem' },
            mb: 1,
            color: colors.gray[800],
          }}
        >
          {specData.title}
        </Typography>

        {/* Description */}
        <Typography
          onClick={() => !descExpanded && setDescExpanded(true)}
          sx={{
            textAlign: 'center',
            fontFamily: typography.fontFamily,
            fontSize: { xs: '0.875rem', sm: '0.9375rem' },
            color: semanticColors.subtleText,
            maxWidth: { xs: '100%', md: 800, lg: 950, xl: 1100 },
            mx: 'auto',
            mb: 2,
            lineHeight: 1.6,
            cursor: descExpanded ? 'default' : 'pointer',
            ...(!descExpanded && {
              display: '-webkit-box',
              WebkitLineClamp: 5,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }),
          }}
        >
          {specData.description}
        </Typography>

        <Suspense fallback={<Box sx={{ minHeight: 400 }} />}>
        {isOverviewMode ? (
          /* OVERVIEW MODE */
          <>
            <SpecOverview
              specId={specId || ''}
              specTitle={specData.title}
              implementations={specData.implementations}
              codeCopied={codeCopied}
              downloadDone={downloadDone}
              openTooltip={openTooltip}
              onImplClick={handleImplClick}
              onCopyCode={handleCopyCode}
              onDownload={handleDownload}
              onTooltipToggle={setOpenTooltip}
              getLibraryMeta={getLibraryMeta}
              onTrackEvent={trackEvent}
            />

            <SpecTabs
              code={null}
              specId={specData.id}
              title={specData.title}
              description={specData.description}
              applications={specData.applications}
              data={specData.data}
              notes={specData.notes}
              tags={specData.tags}
              created={specData.created}
              updated={specData.updated}
              imageDescription={undefined}
              strengths={undefined}
              weaknesses={undefined}
              qualityScore={null}
              criteriaChecklist={undefined}
              libraryId=""
              onTrackEvent={trackEvent}
              overviewMode={true}
              highlightedTags={highlightedTags}
            />
          </>
        ) : (
          /* DETAIL MODE */
          <>
            <LibraryPills
              implementations={specData.implementations}
              selectedLibrary={selectedLibrary || ''}
              onSelect={handleLibrarySelect}
            />

            <Box sx={{ textAlign: 'center', mt: -0.5, mb: 1 }}>
              <Box component={Link} to={`/${specId}`} sx={{
                fontFamily: typography.fontFamily,
                fontSize: fontSize.sm,
                color: semanticColors.mutedText,
                textDecoration: 'none',
                '&:hover': { color: colors.primary },
              }}>
                {'< all implementations'}
              </Box>
            </Box>

            <SpecDetailView
              specId={specId || ''}
              specTitle={specData.title}
              selectedLibrary={selectedLibrary || ''}
              currentImpl={currentImpl}
              implementations={specData.implementations}
              imageLoaded={imageLoaded}
              codeCopied={codeCopied}
              downloadDone={downloadDone}
              onImageLoad={() => setImageLoaded(true)}
              onCopyCode={handleCopyCode}
              onDownload={handleDownload}
              onTrackEvent={trackEvent}
            />


            <SpecTabs
              code={currentCode || currentImpl?.code || null}
              specId={specData.id}
              title={specData.title}
              description={specData.description}
              applications={specData.applications}
              data={specData.data}
              notes={specData.notes}
              tags={specData.tags}
              created={specData.created}
              updated={specData.updated}
              imageDescription={currentImpl?.review_image_description}
              strengths={currentImpl?.review_strengths}
              weaknesses={currentImpl?.review_weaknesses}
              implTags={currentImpl?.impl_tags}
              qualityScore={currentImpl?.quality_score || null}
              criteriaChecklist={currentImpl?.review_criteria_checklist}
              generatedAt={currentImpl?.generated_at}
              libraryId={selectedLibrary || ''}
              onTrackEvent={trackEvent}
              highlightedTags={highlightedTags}
            />
          </>
        )}
        </Suspense>

        <RelatedSpecs specId={specId!} mode={isOverviewMode ? 'spec' : 'full'} library={selectedLibrary || undefined} onHoverTags={setHighlightedTags} />

        <Footer onTrackEvent={trackEvent} selectedSpec={specId} selectedLibrary={selectedLibrary || ''} />
      </Box>
    </>
  );
}
