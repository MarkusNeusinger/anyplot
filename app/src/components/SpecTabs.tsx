import { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import Box from '@mui/material/Box';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import CodeIcon from '@mui/icons-material/Code';
import DescriptionIcon from '@mui/icons-material/Description';
import ImageIcon from '@mui/icons-material/Image';
import StarIcon from '@mui/icons-material/Star';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const CodeHighlighter = lazy(() => import('./CodeHighlighter'));
import { colors, fontSize, semanticColors, typography } from '../theme';
import { API_URL } from '../constants';


// Cached global tag counts — loaded once, shared across all SpecTabs instances
let cachedTagCounts: Record<string, Record<string, number>> | null = null;

// Map tag category names to URL parameter names
const SPEC_TAG_PARAM_MAP: Record<string, string> = {
  plot_type: 'plot',
  data_type: 'data',
  domain: 'dom',
  features: 'feat',
};

const IMPL_TAG_PARAM_MAP: Record<string, string> = {
  dependencies: 'dep',
  techniques: 'tech',
  patterns: 'pat',
  dataprep: 'prep',
  styling: 'style',
};

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
  onTrackEvent?: (name: string, props?: Record<string, string | undefined>) => void;
  // Overview mode - only show Spec tab
  overviewMode?: boolean;
  // Tags to highlight (from similar specs hover)
  highlightedTags?: string[];
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number | null;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  const isOpen = value === index;
  return (
    <Collapse in={isOpen}>
      <Box role="tabpanel" sx={{ pt: 2 }}>
        {children}
      </Box>
    </Collapse>
  );
}

// Clean heading without markdown syntax
function MdHeading({ level, children }: { level: 1 | 2; children: React.ReactNode }) {
  return (
    <Typography
      component={level === 1 ? 'h1' : 'h2'}
      sx={{
        fontFamily: typography.fontFamily,
        fontSize: level === 1 ? '1rem' : '0.8rem',
        fontWeight: 600,
        color: level === 1 ? colors.gray[800] : semanticColors.mutedText,
        textTransform: level === 2 ? 'uppercase' : 'none',
        letterSpacing: level === 2 ? '0.05em' : 'normal',
        mt: level === 1 ? 0 : 2.5,
        mb: 1,
      }}
    >
      {children}
    </Typography>
  );
}

// Parse text with backticks into React nodes with inline code styling
function parseInlineCode(text: string): React.ReactNode[] {
  const parts = text.split(/(`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <Box
          key={i}
          component="code"
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: '0.8rem',
            bgcolor: colors.gray[100],
            color: colors.primary,
            px: 0.5,
            py: 0.25,
            borderRadius: 0.5,
          }}
        >
          {part.slice(1, -1)}
        </Box>
      );
    }
    return part;
  });
}

// Clean bullet list item
function MdListItem({ children }: { children: string }) {
  return (
    <Typography
      component="li"
      sx={{
        fontFamily: typography.fontFamily,
        fontSize: '0.85rem',
        color: semanticColors.labelText,
        lineHeight: 1.7,
        ml: 2,
        mb: 0.25,
        '&::marker': {
          color: colors.gray[300],
        },
      }}
    >
      {parseInlineCode(children)}
    </Typography>
  );
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
  onTrackEvent,
  overviewMode = false,
  highlightedTags = [],
}: SpecTabsProps) {
  const [copied, setCopied] = useState(false);
  // In overview mode, start with Spec tab open; in detail mode, all collapsed
  const [tabIndex, setTabIndex] = useState<number | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [tagCounts, setTagCounts] = useState<Record<string, Record<string, number>> | null>(cachedTagCounts);

  // Fetch global tag counts once (module-level cache)
  useEffect(() => {
    if (cachedTagCounts) return;
    const controller = new AbortController();
    fetch(`${API_URL}/plots/filter?limit=1`, { signal: controller.signal })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.globalCounts) {
          cachedTagCounts = data.globalCounts;
          setTagCounts(data.globalCounts);
        }
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);

  // Get count for a tag value (e.g., "scatter" in "plot" category → 421 implementations)
  const getTagCount = useCallback((paramName: string | undefined, value: string): number | null => {
    if (!tagCounts || !paramName) return null;
    return tagCounts[paramName]?.[value] ?? null;
  }, [tagCounts]);

  // Handle tag click - navigate to filtered plots page (full page navigation)
  const handleTagClick = useCallback(
    (paramName: string, value: string) => {
      onTrackEvent?.('tag_click', { param: paramName, value, source: 'spec_detail' });
      window.location.href = `/?${paramName}=${encodeURIComponent(value)}`;
    },
    [onTrackEvent]
  );

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => ({ ...prev, [category]: !prev[category] }));
  };

  const handleCopy = useCallback(async () => {
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      onTrackEvent?.('copy_code', { spec: specId, library: libraryId, method: 'tab', page: 'spec_detail' });
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  }, [code, specId, libraryId, onTrackEvent]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    // In overview mode, only Spec tab exists at index 0
    const tabNames = overviewMode
      ? ['specification']
      : ['code', 'specification', 'implementation', 'quality'];

    // Toggle: clicking same tab collapses it
    if (tabIndex === newValue) {
      onTrackEvent?.('tab_toggle', { action: 'close', tab: tabNames[tabIndex], library: libraryId || undefined });
      setTabIndex(null);
    } else {
      setTabIndex(newValue);
      onTrackEvent?.('tab_toggle', { action: 'open', tab: tabNames[newValue], library: libraryId || undefined });
    }
  };

  // Lazy-loaded syntax highlighter - only loads when Code tab is opened
  const highlightedCode = code ? (
    <Suspense fallback={
      <Box sx={{ fontFamily: typography.fontFamily, fontSize: '0.85rem', whiteSpace: 'pre-wrap', color: semanticColors.labelText }}>
        {code}
      </Box>
    }>
      <CodeHighlighter code={code} />
    </Suspense>
  ) : null;

  // Format date
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
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
                backgroundColor: colors.gray[100],
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
            <Tab onClick={(e) => tabIndex === 0 && handleTabChange(e, 0)} icon={<CodeIcon sx={{ fontSize: '1.1rem' }} />} iconPosition="start" label="Code" />
          )}
          <Tab onClick={(e) => tabIndex === specTabIndex && handleTabChange(e, specTabIndex)} icon={<DescriptionIcon sx={{ fontSize: '1.1rem' }} />} iconPosition="start" label={<><Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Specification</Box><Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>Spec</Box></>} />
          {!overviewMode && (
            <Tab onClick={(e) => tabIndex === 2 && handleTabChange(e, 2)} icon={<ImageIcon sx={{ fontSize: '1.1rem' }} />} iconPosition="start" label={<><Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Implementation</Box><Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>Impl</Box></>} />
          )}
          {!overviewMode && (
            <Tab
              onClick={(e) => tabIndex === 3 && handleTabChange(e, 3)}
              icon={<StarIcon sx={{ fontSize: '1.1rem', color: tabIndex === 3 ? colors.primary : colors.warning }} />}
              iconPosition="start"
              label={qualityScore ? `${Math.round(qualityScore)}` : 'Quality'}
            />
          )}
        </Tabs>
      </Box>

      {/* Code Tab - only in detail mode */}
      {!overviewMode && (
        <TabPanel value={tabIndex} index={0}>
          <Box sx={{ position: 'relative' }}>
            <Tooltip title={copied ? '.copied' : '.copy()'}>
              <IconButton
                onClick={handleCopy}
                aria-label=".copy()"
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  bgcolor: 'rgba(255,255,255,0.9)',
                  zIndex: 1,
                  '&:hover': { bgcolor: '#fff' },
                }}
                size="small"
              >
                {copied ? <CheckIcon color="success" /> : <ContentCopyIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
            <Box
              sx={{
                bgcolor: colors.background,
                p: 3,
                borderRadius: 1,
              }}
            >
              {highlightedCode}
            </Box>
          </Box>
        </TabPanel>
      )}

      {/* Specification Tab */}
      <TabPanel value={tabIndex} index={specTabIndex}>
        <Box
          sx={{
            bgcolor: colors.background,
            p: 3,
            borderRadius: 1,
            fontFamily: typography.fontFamily,
          }}
        >
          {/* Title only - spec ID visible in breadcrumb */}
          <Typography
            component="h2"
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: '1.1rem',
              fontWeight: 600,
              color: colors.gray[800],
              mb: 1.5,
            }}
          >
            {title}
          </Typography>

          {/* ## Description */}
          <MdHeading level={2}>Description</MdHeading>
          <Typography
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: '0.85rem',
              color: semanticColors.labelText,
              lineHeight: 1.7,
            }}
          >
            {parseInlineCode(description)}
          </Typography>

          {/* Applications */}
          {applications && applications.length > 0 && (
            <>
              <MdHeading level={2}>Applications</MdHeading>
              <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
                {applications.map((app, i) => (
                  <MdListItem key={i}>{app}</MdListItem>
                ))}
              </Box>
            </>
          )}

          {/* Data */}
          {data && data.length > 0 && (
            <>
              <MdHeading level={2}>Data</MdHeading>
              <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
                {data.map((d, i) => (
                  <MdListItem key={i}>{d}</MdListItem>
                ))}
              </Box>
            </>
          )}

          {/* Notes */}
          {notes && notes.length > 0 && (
            <>
              <MdHeading level={2}>Notes</MdHeading>
              <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
                {notes.map((note, i) => (
                  <MdListItem key={i}>{note}</MdListItem>
                ))}
              </Box>
            </>
          )}

        </Box>
      </TabPanel>

      {/* Implementation Tab - only in detail mode */}
      {!overviewMode && (
        <TabPanel value={tabIndex} index={2}>
          <Box
            sx={{
              bgcolor: colors.background,
              p: 3,
              borderRadius: 1,
              fontFamily: typography.fontFamily,
            }}
          >
            {/* Image Description */}
            {imageDescription && (
              <>
                <MdHeading level={2}>Description</MdHeading>
                <Typography
                  sx={{
                    fontFamily: typography.fontFamily,
                    fontSize: '0.85rem',
                    color: semanticColors.labelText,
                    lineHeight: 1.7,
                  }}
                >
                  {imageDescription}
                </Typography>
              </>
            )}

            {/* Strengths */}
            {strengths && strengths.length > 0 && (
              <>
                <MdHeading level={2}>Strengths</MdHeading>
                <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
                  {strengths.map((s, i) => (
                    <Typography
                      key={i}
                      component="li"
                      sx={{
                        fontFamily: typography.fontFamily,
                        fontSize: '0.85rem',
                        color: semanticColors.labelText,
                        lineHeight: 1.7,
                        ml: 2,
                        mb: 0.25,
                        '&::marker': { color: colors.success },
                      }}
                    >
                      {s}
                    </Typography>
                  ))}
                </Box>
              </>
            )}

            {/* Weaknesses */}
            {weaknesses && weaknesses.length > 0 && (
              <>
                <MdHeading level={2}>Weaknesses</MdHeading>
                <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
                  {weaknesses.map((w, i) => (
                    <Typography
                      key={i}
                      component="li"
                      sx={{
                        fontFamily: typography.fontFamily,
                        fontSize: '0.85rem',
                        color: semanticColors.labelText,
                        lineHeight: 1.7,
                        ml: 2,
                        mb: 0.25,
                        '&::marker': { color: colors.error },
                      }}
                    >
                      {w}
                    </Typography>
                  ))}
                </Box>
              </>
            )}

            {/* No data message */}
            {!imageDescription && (!strengths || strengths.length === 0) && (!weaknesses || weaknesses.length === 0) && (
              <Typography sx={{ fontFamily: typography.fontFamily, fontSize: '0.85rem', color: colors.gray[400] }}>
                No implementation review data available.
              </Typography>
            )}

            {/* Metadata */}
            <Typography sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.sm, color: colors.gray[400], mt: 2 }}>
              {specId}
              {libraryId && ` · ${libraryId}`}
              {(() => {
                const date = generatedAt || updated || created;
                return date ? ` · ${formatDate(date)}` : '';
              })()}
            </Typography>
          </Box>
        </TabPanel>
      )}

      {/* Quality Tab - only in detail mode */}
      {!overviewMode && (
        <TabPanel value={tabIndex} index={3}>
        <Box
          sx={{
            bgcolor: colors.background,
            p: 3,
            borderRadius: 1,
            fontFamily: typography.fontFamily,
          }}
        >
          {/* Score */}
          <MdHeading level={2}>Score</MdHeading>
          <Typography
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: '2rem',
              fontWeight: 700,
              color: qualityScore && qualityScore >= 90 ? colors.success : qualityScore && qualityScore >= 70 ? colors.warning : colors.error,
            }}
          >
            {qualityScore ? `${Math.round(qualityScore)}/100` : 'N/A'}
          </Typography>

          {/* Criteria Checklist */}
          {criteriaChecklist && Object.keys(criteriaChecklist).length > 0 && (
            <>
              <MdHeading level={2}>Breakdown</MdHeading>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {Object.entries(criteriaChecklist).map(([category, data]) => {
                  const catData = data as { score?: number; max?: number; items?: Array<{ id: string; name: string; score: number; max: number; passed: boolean; comment?: string }> };
                  const score = catData.score ?? 0;
                  const max = catData.max ?? 0;
                  const pct = max > 0 ? (score / max) * 100 : 0;
                  const items = catData.items || [];
                  const isExpanded = expandedCategories[category] ?? false;

                  return (
                    <Box key={category}>
                      {/* Category header - clickable */}
                      <Box
                        onClick={() => items.length > 0 && toggleCategory(category)}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          mb: 0.5,
                          cursor: items.length > 0 ? 'pointer' : 'default',
                          '&:hover': items.length > 0 ? { opacity: 0.8 } : {},
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {items.length > 0 && (
                            isExpanded ? (
                              <ExpandLessIcon sx={{ fontSize: '1rem', color: colors.gray[400] }} />
                            ) : (
                              <ExpandMoreIcon sx={{ fontSize: '1rem', color: colors.gray[400] }} />
                            )
                          )}
                          <Typography sx={{ fontFamily: typography.fontFamily, fontSize: '0.85rem', color: semanticColors.labelText }}>
                            {category.replace(/_/g, ' ')}
                          </Typography>
                        </Box>
                        <Typography sx={{ fontFamily: typography.fontFamily, fontSize: '0.85rem', color: semanticColors.mutedText }}>
                          {score}/{max}
                        </Typography>
                      </Box>
                      {/* Progress bar */}
                      <Box sx={{ height: 4, bgcolor: colors.gray[200], borderRadius: 2, overflow: 'hidden' }}>
                        <Box
                          sx={{
                            height: '100%',
                            width: `${pct}%`,
                            bgcolor: pct >= 90 ? colors.success : pct >= 70 ? colors.warning : colors.error,
                            borderRadius: 2,
                          }}
                        />
                      </Box>
                      {/* Expandable items */}
                      <Collapse in={isExpanded}>
                        <Box sx={{ mt: 1, ml: 2, display: 'flex', flexDirection: 'column', gap: 0.75 }}>
                          {items.map((item) => (
                            <Box key={item.id} sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <Box
                                    sx={{
                                      width: 6,
                                      height: 6,
                                      borderRadius: '50%',
                                      bgcolor:
                                        item.score === 0
                                          ? colors.error
                                          : item.score === item.max
                                            ? colors.success
                                            : colors.warning,
                                    }}
                                  />
                                  <Typography sx={{ fontFamily: typography.fontFamily, fontSize: '0.85rem', color: semanticColors.labelText }}>
                                    {item.name}
                                  </Typography>
                                </Box>
                                <Typography sx={{ fontFamily: typography.fontFamily, fontSize: '0.8rem', color: colors.gray[400] }}>
                                  {item.score}/{item.max}
                                </Typography>
                              </Box>
                              {item.comment && (
                                <Typography
                                  sx={{
                                    fontFamily: typography.fontFamily,
                                    fontSize: '0.85rem',
                                    color: semanticColors.mutedText,
                                    ml: 1.5,
                                    fontStyle: 'italic',
                                  }}
                                >
                                  {item.comment}
                                </Typography>
                              )}
                            </Box>
                          ))}
                        </Box>
                      </Collapse>
                    </Box>
                  );
                })}
              </Box>
            </>
          )}

          {/* No data message */}
          {!qualityScore && (!criteriaChecklist || Object.keys(criteriaChecklist).length === 0) && (
            <Typography sx={{ fontFamily: typography.fontFamily, fontSize: '0.85rem', color: colors.gray[400] }}>
              No quality data available.
            </Typography>
          )}
        </Box>
        </TabPanel>
      )}

      {/* Tags — always visible after tab content (spec tags + impl tags on detail page) */}
      {((tags && Object.keys(tags).length > 0) || (implTags && Object.values(implTags).some(v => v?.length > 0))) && (
        <Box sx={{ mt: 1.5, display: 'flex', flexWrap: 'wrap', gap: 2.5, py: 1.5 }}>
          {tags && Object.entries(tags).map(([category, values]) => {
            const paramName = SPEC_TAG_PARAM_MAP[category];
            return (
              <Box key={`spec-${category}`} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography component="span" sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.sm, color: semanticColors.mutedText }}>
                  {category.replace(/_/g, ' ')}:
                </Typography>
                {values.map((value, i) => {
                  const isHighlighted = highlightedTags.includes(value);
                  const count = getTagCount(paramName, value);
                  const chip = (
                    <Chip key={i} label={value} size="small"
                      onClick={paramName ? () => handleTagClick(paramName, value) : undefined}
                      sx={{
                        fontFamily: typography.fontFamily, fontSize: fontSize.xs, height: 24,
                        bgcolor: isHighlighted ? colors.highlight.bg : colors.gray[100],
                        color: isHighlighted ? colors.highlight.text : semanticColors.labelText,
                        cursor: paramName ? 'pointer' : 'default',
                        transition: 'all 0.2s ease',
                        fontWeight: isHighlighted ? 600 : 400,
                        '&:hover': paramName ? { bgcolor: colors.gray[200] } : {},
                      }}
                    />
                  );
                  return count !== null ? (
                    <Tooltip key={i} title={`${count} plots`} placement="top" enterDelay={200}>{chip}</Tooltip>
                  ) : chip;
                })}
              </Box>
            );
          })}
          {!overviewMode && implTags && Object.entries(implTags)
            .filter(([, values]) => values && values.length > 0)
            .map(([category, values]) => {
              const paramName = IMPL_TAG_PARAM_MAP[category];
              return (
                <Box key={`impl-${category}`} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Typography component="span" sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.sm, color: semanticColors.mutedText }}>
                    {category}:
                  </Typography>
                  {values.map((value, i) => {
                    const isHighlighted = highlightedTags.includes(value);
                    const count = getTagCount(paramName, value);
                    const chip = (
                      <Chip key={i} label={value} size="small"
                        onClick={paramName ? () => handleTagClick(paramName, value) : undefined}
                        sx={{
                          fontFamily: typography.fontFamily, fontSize: fontSize.xs, height: 24,
                          bgcolor: isHighlighted ? colors.highlight.bg : colors.gray[100],
                          color: isHighlighted ? colors.highlight.text : semanticColors.labelText,
                          cursor: paramName ? 'pointer' : 'default',
                          transition: 'all 0.2s ease',
                          fontWeight: isHighlighted ? 600 : 400,
                          '&:hover': paramName ? { bgcolor: colors.gray[200] } : {},
                        }}
                      />
                    );
                    return count !== null ? (
                      <Tooltip key={i} title={`${count} plots`} placement="top" enterDelay={200}>{chip}</Tooltip>
                    ) : chip;
                  })}
                </Box>
              );
            })}
        </Box>
      )}

    </Box>
  );
}
