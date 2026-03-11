import { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import Skeleton from '@mui/material/Skeleton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import BugReportIcon from '@mui/icons-material/BugReport';
import { NotFoundPage } from './NotFoundPage';

import { API_URL, GITHUB_URL } from '../constants';
import { useAnalytics } from '../hooks';
import { useAppData } from '../hooks';
import { LibraryPills } from '../components/LibraryPills';
import { SpecTabs } from '../components/SpecTabs';
import { Breadcrumb, Footer, SpecOverview, SpecDetailView } from '../components';
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

  // Handle image click (in detail mode - go back to overview)
  const handleImageClick = useCallback(() => {
    navigate(`/${specId}`);
  }, [specId, navigate]);

  // Handle download
  const handleDownload = useCallback(
    (impl: Implementation) => {
      if (!impl?.preview_url) return;
      const link = document.createElement('a');
      link.href = impl.preview_url;
      link.download = `${specId}-${impl.library_id}.png`;
      link.click();
      trackEvent('download_image', {
        spec: specId,
        library: impl.library_id,
        page: isOverviewMode ? 'spec_overview' : 'spec_detail',
      });
    },
    [specId, trackEvent, isOverviewMode]
  );

  // Handle copy code
  const handleCopyCode = useCallback(
    async (impl: Implementation) => {
      if (!impl?.code) return;
      try {
        await navigator.clipboard.writeText(impl.code);
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
    [specId, trackEvent, isOverviewMode]
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
        <Typography variant="h5" sx={{ mb: 2, color: '#6b7280' }}>
          {error}
        </Typography>
        <Button component={Link} to="/" startIcon={<ArrowBackIcon />} sx={{ color: '#3776AB' }}>
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
                  { label: 'pyplots.ai', to: '/' },
                  { label: 'catalog', to: '/catalog' },
                  { label: specId || '' },
                ]
              : [
                  { label: 'pyplots.ai', to: '/' },
                  { label: 'catalog', to: '/catalog' },
                  { label: specId || '', to: `/${specId}` },
                  { label: selectedLibrary || '' },
                ]
          }
          rightAction={
            <Tooltip title="report issue">
              <Box
                component="a"
                href={buildReportUrl()}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackEvent('report_issue', { spec: specId, library: selectedLibrary || undefined })}
                sx={{
                  color: '#9ca3af',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  '&:hover': { color: '#3776AB' },
                }}
              >
                <BugReportIcon sx={{ fontSize: '1.1rem', display: { xs: 'block', md: 'none' } }} />
                <Box
                  component="span"
                  sx={{
                    display: { xs: 'none', md: 'block' },
                    fontFamily: '"MonoLisa", monospace',
                    fontSize: '0.85rem',
                  }}
                >
                  report issue
                </Box>
              </Box>
            </Tooltip>
          }
        />

        {/* Title */}
        <Typography
          variant="h4"
          component="h1"
          sx={{
            textAlign: 'center',
            fontFamily: '"MonoLisa", monospace',
            fontWeight: 600,
            fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' },
            mb: 1,
            color: '#1f2937',
          }}
        >
          {specData.title}
        </Typography>

        {/* Description */}
        <Typography
          onClick={() => !descExpanded && setDescExpanded(true)}
          sx={{
            textAlign: 'center',
            fontFamily: '"MonoLisa", monospace',
            fontSize: { xs: '0.8rem', sm: '0.9rem' },
            color: '#6b7280',
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

        {isOverviewMode ? (
          /* OVERVIEW MODE */
          <>
            <SpecOverview
              specId={specId || ''}
              specTitle={specData.title}
              implementations={specData.implementations}
              codeCopied={codeCopied}
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
              imageDescription={undefined}
              strengths={undefined}
              weaknesses={undefined}
              qualityScore={null}
              criteriaChecklist={undefined}
              libraryId=""
              onTrackEvent={trackEvent}
              overviewMode={true}
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

            <SpecDetailView
              specId={specId || ''}
              specTitle={specData.title}
              selectedLibrary={selectedLibrary || ''}
              currentImpl={currentImpl}
              implementations={specData.implementations}
              imageLoaded={imageLoaded}
              codeCopied={codeCopied}
              onImageLoad={() => setImageLoaded(true)}
              onImageClick={handleImageClick}
              onCopyCode={handleCopyCode}
              onDownload={handleDownload}
              onTrackEvent={trackEvent}
            />

            <SpecTabs
              code={currentImpl?.code || null}
              specId={specData.id}
              title={specData.title}
              description={specData.description}
              applications={specData.applications}
              data={specData.data}
              notes={specData.notes}
              tags={specData.tags}
              created={specData.created}
              imageDescription={currentImpl?.review_image_description}
              strengths={currentImpl?.review_strengths}
              weaknesses={currentImpl?.review_weaknesses}
              implTags={currentImpl?.impl_tags}
              qualityScore={currentImpl?.quality_score || null}
              criteriaChecklist={currentImpl?.review_criteria_checklist}
              libraryId={selectedLibrary || ''}
              onTrackEvent={trackEvent}
            />
          </>
        )}

        <Footer onTrackEvent={trackEvent} selectedSpec={specId} selectedLibrary={selectedLibrary || ''} />
      </Box>
    </>
  );
}
