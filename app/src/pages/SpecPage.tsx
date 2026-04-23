import { useState, useEffect, useMemo, useCallback, lazy, Suspense } from 'react';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Skeleton from '@mui/material/Skeleton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { NotFoundPage } from './NotFoundPage';

import { API_URL, GITHUB_URL } from '../constants';
import { typography, colors, fontSize, semanticColors } from '../theme';
import { useAnalytics, useCodeFetch } from '../hooks';
import { useAppData } from '../hooks';
import { specPath } from '../utils/paths';
import { LibraryPills } from '../components/LibraryPills';
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

type Mode = 'hub' | 'detail';

export function SpecPage() {
  const { specId, language: urlLanguage, library: urlLibrary } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
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

  const mode: Mode = urlLibrary ? 'detail' : 'hub';
  const selectedLibrary = urlLibrary || null;
  const languageFilter = mode === 'hub' ? searchParams.get('language') : null;

  const getLibraryMeta = useCallback(
    (libraryId: string) => librariesData.find((lib) => lib.id === libraryId),
    [librariesData]
  );

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

        // Detail mode: validate library matches an impl in the requested language.
        // If no match, fall back to the hub with a language filter to preserve intent.
        if (urlLibrary && urlLanguage) {
          const matched = data.implementations.find(
            (i) => i.library_id === urlLibrary && i.language === urlLanguage,
          );
          if (!matched) {
            navigate({ pathname: specPath(specId!), search: `?language=${encodeURIComponent(urlLanguage)}` }, { replace: true });
            return;
          }
        }
      } catch (err) {
        console.error('Error fetching spec:', err);
        setError('Failed to load spec');
      } finally {
        setLoading(false);
      }
    };

    fetchSpec();
  }, [specId, urlLanguage, urlLibrary, navigate]);

  // Implementations for the selected language (used in detail mode for library pills)
  const langImpls = useMemo(() => {
    if (!specData || !urlLanguage) return specData?.implementations || [];
    return specData.implementations.filter((i) => i.language === urlLanguage);
  }, [specData, urlLanguage]);

  // Languages present in this spec (for hub mode)
  const availableLanguages = useMemo(() => {
    if (!specData) return [];
    return Array.from(new Set(specData.implementations.map((i) => i.language))).sort();
  }, [specData]);

  // If ?language= points at a language that has no implementations, drop it.
  useEffect(() => {
    if (mode !== 'hub' || !specData || !languageFilter) return;
    if (availableLanguages.includes(languageFilter)) return;
    const params = new URLSearchParams(searchParams);
    params.delete('language');
    setSearchParams(params, { replace: true });
  }, [mode, specData, languageFilter, availableLanguages, searchParams, setSearchParams]);

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

  const currentCode = specId && selectedLibrary ? getCode(specId, selectedLibrary) : null;

  // Handle library switch (in detail mode)
  const handleLibrarySelect = useCallback(
    (libraryId: string) => {
      if (!specId || !urlLanguage) return;
      setImageLoaded(false);
      navigate(specPath(specId, urlLanguage, libraryId), { replace: true });
    },
    [specId, urlLanguage, navigate]
  );

  // Handle implementation click (in language overview)
  const handleImplClick = useCallback(
    (libraryId: string) => {
      if (!specId) return;
      const impl = specData?.implementations.find((i) => i.library_id === libraryId);
      const lang = impl?.language || urlLanguage;
      if (!lang) return;
      navigate(specPath(specId, lang, libraryId));
    },
    [specId, urlLanguage, specData, navigate]
  );

  // Interactive view mode (driven by ?view=interactive)
  const viewMode: 'preview' | 'interactive' =
    searchParams.get('view') === 'interactive' ? 'interactive' : 'preview';

  const handleViewModeChange = useCallback(
    (next: 'preview' | 'interactive') => {
      const params = new URLSearchParams(searchParams);
      if (next === 'interactive') params.set('view', 'interactive');
      else params.delete('view');
      setSearchParams(params, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  // Keep URL in sync with what's actually rendered: if interactive is requested
  // but the current impl has no preview_html, we fall back to the static preview
  // — drop the query param so shareable URLs reflect the visible state.
  useEffect(() => {
    if (viewMode === 'interactive' && currentImpl && !currentImpl.preview_html) {
      const params = new URLSearchParams(searchParams);
      params.delete('view');
      setSearchParams(params, { replace: true });
    }
  }, [viewMode, currentImpl, searchParams, setSearchParams]);

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
        page: mode === 'detail' ? 'spec_detail' : 'spec_hub',
      });
    },
    [specId, trackEvent, mode],
  );

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
          page: mode === 'detail' ? 'spec_detail' : 'spec_hub',
        });
        setTimeout(() => setCodeCopied(null), 2000);
      } catch (err) {
        console.error('Copy failed:', err);
      }
    },
    [specId, trackEvent, mode, fetchCode]
  );

  const buildReportUrl = useCallback(() => {
    const params = new URLSearchParams({
      template: 'report-plot-issue.yml',
      spec_id: specId || '',
    });
    return `${GITHUB_URL}/issues/new?${params.toString()}`;
  }, [specId]);

  // Track page view. Hub mode calls trackPageview() without an override so
  // buildPlausibleUrl() picks up ?language= from window.location and converts
  // it to the path-segment form (e.g. /{spec}/language/python). The URL
  // override path used for detail mode cannot carry query strings — see
  // useAnalytics.ts sendPageview() validation regex.
  useEffect(() => {
    if (!specData || !specId) return;
    if (mode === 'hub') {
      trackPageview();
    } else if (mode === 'detail' && selectedLibrary) {
      trackPageview(`/${specId}/${urlLanguage}/${selectedLibrary}`);
    }
  }, [specData, mode, specId, urlLanguage, selectedLibrary, languageFilter, trackPageview]);

  // Keyboard shortcuts: left/right arrows switch libraries in detail mode
  useEffect(() => {
    if (mode !== 'detail' || !specData) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return;
      const sorted = [...langImpls].sort((a, b) => a.library_id.localeCompare(b.library_id));
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
  }, [mode, specData, langImpls, selectedLibrary, handleLibrarySelect]);

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

  if (!specData) return null;

  const canonical =
    mode === 'detail'
      ? `https://anyplot.ai/${specId}/${urlLanguage}/${selectedLibrary}`
      : `https://anyplot.ai/${specId}`;

  const titleSuffix = mode === 'detail' ? ` - ${selectedLibrary}` : '';

  // Implementations to render in the grid: hub mode optionally filtered by ?language=
  const gridImpls =
    languageFilter
      ? specData.implementations.filter((i) => i.language === languageFilter)
      : specData.implementations;

  return (
    <>
      <Helmet>
        <title>{`${specData.title}${titleSuffix} | anyplot.ai`}</title>
        <meta name="description" content={specData.description} />
        <meta property="og:title" content={`${specData.title}${titleSuffix} | anyplot.ai`} />
        <meta property="og:description" content={specData.description} />
        {currentImpl?.preview_url && <meta property="og:image" content={currentImpl.preview_url} />}
        <meta property="og:url" content={canonical} />
        <link rel="canonical" href={canonical} />
      </Helmet>

      <Box sx={{ pt: 1.5, pb: 4 }}>
        {mode === 'hub' && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 0.5 }}>
            <Box
              component="a"
              href={buildReportUrl()}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent('report_issue', { spec: specId, library: selectedLibrary || undefined })}
              sx={{
                fontFamily: typography.mono,
                fontSize: fontSize.sm,
                color: semanticColors.mutedText,
                textDecoration: 'none',
                '&:hover': { color: colors.primary },
              }}
            >
              report issue ↗
            </Box>
          </Box>
        )}

        <Typography
          variant="h4"
          component="h1"
          sx={{
            textAlign: 'center',
            fontFamily: typography.serif,
            fontWeight: 400,
            fontSize: { xs: '1.375rem', sm: '1.625rem', md: '2.125rem' },
            mb: 1,
            color: 'var(--ink)',
          }}
        >
          {specData.title}
        </Typography>

        <Typography
          onClick={() => !descExpanded && setDescExpanded(true)}
          sx={{
            textAlign: 'center',
            fontFamily: typography.serif,
            fontWeight: 300,
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
        {mode !== 'detail' ? (
          <>
            <SpecOverview
              specId={specId || ''}
              specTitle={specData.title}
              implementations={gridImpls}
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
          <>
            <LibraryPills
              implementations={langImpls}
              selectedLibrary={selectedLibrary || ''}
              onSelect={handleLibrarySelect}
              onAll={() => navigate(specPath(specId!))}
            />

            <SpecDetailView
              specTitle={specData.title}
              selectedLibrary={selectedLibrary || ''}
              currentImpl={currentImpl}
              implementations={langImpls}
              imageLoaded={imageLoaded}
              codeCopied={codeCopied}
              downloadDone={downloadDone}
              viewMode={viewMode}
              reportUrl={buildReportUrl()}
              onViewModeChange={handleViewModeChange}
              onImageLoad={() => setImageLoaded(true)}
              onCopyCode={handleCopyCode}
              onDownload={handleDownload}
              onReport={() => trackEvent('report_issue', { spec: specId, library: selectedLibrary || undefined })}
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

        <RelatedSpecs specId={specId!} mode={mode === 'detail' ? 'full' : 'spec'} library={selectedLibrary || undefined} onHoverTags={setHighlightedTags} />
      </Box>
    </>
  );
}
