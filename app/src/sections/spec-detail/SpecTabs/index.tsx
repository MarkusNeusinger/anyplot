import { useCallback, useEffect, useState } from 'react';

import { useNavigate } from 'react-router-dom';

import CodeIcon from '@mui/icons-material/Code';
import DescriptionIcon from '@mui/icons-material/Description';
import ImageIcon from '@mui/icons-material/Image';
import StarIcon from '@mui/icons-material/Star';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { apiGet, endpoints } from 'src/lib/api';
import { paths } from 'src/routes/paths';
import { CodeTab } from 'src/sections/spec-detail/SpecTabs/CodeTab';
import { ImplTab } from 'src/sections/spec-detail/SpecTabs/ImplTab';
import { TabPanel } from 'src/sections/spec-detail/SpecTabs/md';
import { QualityTab } from 'src/sections/spec-detail/SpecTabs/QualityTab';
import { SpecTab } from 'src/sections/spec-detail/SpecTabs/SpecTab';
import {
  getCachedTagCounts,
  IMPL_TAG_PARAM_MAP,
  setCachedTagCounts,
  SPEC_TAG_PARAM_MAP,
  type TrackEventFn,
} from 'src/sections/spec-detail/SpecTabs/utils';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

interface SpecTabsProps {
  // Code tab
  code: string | null;
  // Specification tab
  specId: string;
  title: string;
  description: string;
  applications?: string[];
  data?: string[];
  notes?: string[];
  tags?: Record<string, string[]>;
  created?: string;
  updated?: string;
  // Implementation tab
  imageDescription?: string;
  strengths?: string[];
  weaknesses?: string[];
  implTags?: Record<string, string[]>;
  // Quality tab
  qualityScore: number | null;
  criteriaChecklist?: Record<string, unknown>;
  // Implementation date
  generatedAt?: string;
  // Common
  libraryId: string;
  language?: string;
  onTrackEvent?: TrackEventFn;
  // Overview mode - only show Spec tab
  overviewMode?: boolean;
  // Tags to highlight (from similar specs hover)
  highlightedTags?: string[];
}

export function SpecTabs({
  code,
  specId,
  title,
  description,
  applications,
  data,
  notes,
  tags,
  created,
  updated,
  imageDescription,
  strengths,
  weaknesses,
  implTags,
  qualityScore,
  criteriaChecklist,
  generatedAt,
  libraryId,
  language,
  onTrackEvent,
  overviewMode = false,
  highlightedTags = [],
}: SpecTabsProps) {
  // In overview mode, start with Spec tab open; in detail mode, all collapsed
  const [tabIndex, setTabIndex] = useState<number | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [tagCounts, setTagCounts] = useState<Record<string, Record<string, number>> | null>(
    getCachedTagCounts()
  );

  // Fetch global tag counts once (module-level cache)
  useEffect(() => {
    if (getCachedTagCounts()) return;
    const controller = new AbortController();
    // Non-ok responses previously resolved to null and were ignored; apiGet
    // throws instead, so the empty catch keeps the same silent-skip behavior.
    apiGet<{ globalCounts?: Record<string, Record<string, number>> }>(
      endpoints.plotsFilter('limit=1'),
      { signal: controller.signal }
    )
      .then(data => {
        if (data?.globalCounts) {
          setCachedTagCounts(data.globalCounts);
          setTagCounts(data.globalCounts);
        }
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);

  // Get count for a tag value (e.g., "scatter" in "plot" category → 421 implementations)
  const getTagCount = useCallback(
    (paramName: string | undefined, value: string): number | null => {
      if (!tagCounts || !paramName) return null;
      return tagCounts[paramName]?.[value] ?? null;
    },
    [tagCounts]
  );

  const navigate = useNavigate();

  // Handle tag click — in-app navigation (preserves AppDataContext, no full reload).
  // The previous `window.location.href = …` forced /specs, /libraries, /stats
  // to be re-fetched on every tag click on a SpecTabs page.
  const handleTagClick = useCallback(
    (paramName: string, value: string) => {
      onTrackEvent?.('tag_click', { param: paramName, value, source: 'spec_detail' });
      navigate(paths.plotsFiltered(paramName, value));
    },
    [navigate, onTrackEvent]
  );

  const toggleCategory = useCallback((category: string) => {
    setExpandedCategories(prev => ({ ...prev, [category]: !prev[category] }));
  }, []);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    // In overview mode, only Spec tab exists at index 0
    const tabNames = overviewMode
      ? ['specification']
      : ['code', 'specification', 'implementation', 'quality'];

    // Toggle: clicking same tab collapses it
    if (tabIndex === newValue) {
      onTrackEvent?.('tab_toggle', {
        action: 'close',
        tab: tabNames[tabIndex],
        library: libraryId || undefined,
      });
      setTabIndex(null);
    } else {
      setTabIndex(newValue);
      onTrackEvent?.('tab_toggle', {
        action: 'open',
        tab: tabNames[newValue],
        library: libraryId || undefined,
      });
    }
  };

  // In overview mode, use different tab indexing (only Spec tab at index 0)
  const specTabIndex = overviewMode ? 0 : 1;

  return (
    <Box sx={{ mt: 3, maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 }, mx: 'auto' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={tabIndex !== null ? tabIndex : false}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              fontFamily: typography.fontFamily,
              textTransform: 'none',
              fontSize: '0.875rem',
              minHeight: 48,
              transition: 'background-color 0.15s ease, color 0.15s ease',
              borderRadius: '4px 4px 0 0',
              '&:hover': {
                backgroundColor: 'var(--bg-surface)',
                color: colors.primary,
              },
            },
            '& .Mui-selected': {
              color: colors.primary,
            },
            '& .MuiTabs-indicator': {
              backgroundColor: colors.primary,
            },
          }}
        >
          {!overviewMode && (
            <Tab
              onClick={e => tabIndex === 0 && handleTabChange(e, 0)}
              icon={<CodeIcon sx={{ fontSize: '1.1rem' }} />}
              iconPosition="start"
              label="Code"
            />
          )}
          <Tab
            onClick={e => tabIndex === specTabIndex && handleTabChange(e, specTabIndex)}
            icon={<DescriptionIcon sx={{ fontSize: '1.1rem' }} />}
            iconPosition="start"
            label={
              <>
                <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
                  Specification
                </Box>
                <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>
                  Spec
                </Box>
              </>
            }
          />
          {!overviewMode && (
            <Tab
              onClick={e => tabIndex === 2 && handleTabChange(e, 2)}
              icon={<ImageIcon sx={{ fontSize: '1.1rem' }} />}
              iconPosition="start"
              label={
                <>
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
                    Implementation
                  </Box>
                  <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>
                    Impl
                  </Box>
                </>
              }
            />
          )}
          {!overviewMode && (
            <Tab
              onClick={e => tabIndex === 3 && handleTabChange(e, 3)}
              icon={
                <StarIcon
                  sx={{
                    fontSize: '1.1rem',
                    color: tabIndex === 3 ? colors.primary : colors.warning,
                  }}
                />
              }
              iconPosition="start"
              label={qualityScore !== null ? `${Math.round(qualityScore)}` : 'Quality'}
            />
          )}
        </Tabs>
      </Box>

      {/* Code Tab - only in detail mode */}
      {!overviewMode && (
        <TabPanel value={tabIndex} index={0}>
          <CodeTab
            code={code}
            specId={specId}
            libraryId={libraryId}
            language={language}
            onTrackEvent={onTrackEvent}
          />
        </TabPanel>
      )}

      {/* Specification Tab */}
      <TabPanel value={tabIndex} index={specTabIndex}>
        <SpecTab
          title={title}
          description={description}
          applications={applications}
          data={data}
          notes={notes}
        />
      </TabPanel>

      {/* Implementation Tab - only in detail mode */}
      {!overviewMode && (
        <TabPanel value={tabIndex} index={2}>
          <ImplTab
            imageDescription={imageDescription}
            strengths={strengths}
            weaknesses={weaknesses}
            specId={specId}
            libraryId={libraryId}
            generatedAt={generatedAt}
            updated={updated}
            created={created}
          />
        </TabPanel>
      )}

      {/* Quality Tab - only in detail mode */}
      {!overviewMode && (
        <TabPanel value={tabIndex} index={3}>
          <QualityTab
            qualityScore={qualityScore}
            criteriaChecklist={criteriaChecklist}
            expandedCategories={expandedCategories}
            onToggleCategory={toggleCategory}
          />
        </TabPanel>
      )}

      {/* Tags — always visible after tab content (spec tags + impl tags on detail page) */}
      {((tags && Object.keys(tags).length > 0) ||
        (implTags && Object.values(implTags).some(v => v?.length > 0))) && (
        <Box sx={{ mt: 1.5, display: 'flex', flexWrap: 'wrap', gap: 2.5, py: 1.5 }}>
          {tags &&
            Object.entries(tags).map(([category, values]) => {
              const paramName = SPEC_TAG_PARAM_MAP[category];
              return (
                <Box
                  key={`spec-${category}`}
                  sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                >
                  <Typography
                    component="span"
                    sx={{
                      fontFamily: typography.fontFamily,
                      fontSize: fontSize.sm,
                      color: semanticColors.mutedText,
                    }}
                  >
                    {category.replace(/_/g, ' ')}:
                  </Typography>
                  {values.map((value, i) => {
                    const isHighlighted = highlightedTags.includes(value);
                    const count = getTagCount(paramName, value);
                    const chip = (
                      <Chip
                        key={i}
                        label={value}
                        size="small"
                        onClick={paramName ? () => handleTagClick(paramName, value) : undefined}
                        sx={{
                          fontFamily: typography.fontFamily,
                          fontSize: fontSize.xs,
                          height: 24,
                          bgcolor: isHighlighted ? colors.highlight.bg : 'var(--bg-surface)',
                          color: isHighlighted ? colors.highlight.text : semanticColors.labelText,
                          cursor: paramName ? 'pointer' : 'default',
                          transition: 'all 0.2s ease',
                          fontWeight: isHighlighted ? 600 : 400,
                          '&:hover': paramName ? { bgcolor: 'var(--bg-elevated)' } : {},
                        }}
                      />
                    );
                    return count !== null ? (
                      <Tooltip key={i} title={`${count} plots`} placement="top" enterDelay={200}>
                        {chip}
                      </Tooltip>
                    ) : (
                      chip
                    );
                  })}
                </Box>
              );
            })}
          {!overviewMode &&
            implTags &&
            Object.entries(implTags)
              .filter(([, values]) => values && values.length > 0)
              .map(([category, values]) => {
                const paramName = IMPL_TAG_PARAM_MAP[category];
                return (
                  <Box
                    key={`impl-${category}`}
                    sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                  >
                    <Typography
                      component="span"
                      sx={{
                        fontFamily: typography.fontFamily,
                        fontSize: fontSize.sm,
                        color: semanticColors.mutedText,
                      }}
                    >
                      {category}:
                    </Typography>
                    {values.map((value, i) => {
                      const isHighlighted = highlightedTags.includes(value);
                      const count = getTagCount(paramName, value);
                      const chip = (
                        <Chip
                          key={i}
                          label={value}
                          size="small"
                          onClick={paramName ? () => handleTagClick(paramName, value) : undefined}
                          sx={{
                            fontFamily: typography.fontFamily,
                            fontSize: fontSize.xs,
                            height: 24,
                            bgcolor: isHighlighted ? colors.highlight.bg : 'var(--bg-surface)',
                            color: isHighlighted ? colors.highlight.text : semanticColors.labelText,
                            cursor: paramName ? 'pointer' : 'default',
                            transition: 'all 0.2s ease',
                            fontWeight: isHighlighted ? 600 : 400,
                            '&:hover': paramName ? { bgcolor: 'var(--bg-elevated)' } : {},
                          }}
                        />
                      );
                      return count !== null ? (
                        <Tooltip key={i} title={`${count} plots`} placement="top" enterDelay={200}>
                          {chip}
                        </Tooltip>
                      ) : (
                        chip
                      );
                    })}
                  </Box>
                );
              })}
        </Box>
      )}
    </Box>
  );
}
