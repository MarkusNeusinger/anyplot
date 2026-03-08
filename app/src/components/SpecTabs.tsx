import { useState, useCallback, useMemo } from 'react';
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
import SyntaxHighlighter from 'react-syntax-highlighter/dist/esm/prism-light';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';

SyntaxHighlighter.registerLanguage('python', python);

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
  // Implementation tab
  imageDescription?: string;
  strengths?: string[];
  weaknesses?: string[];
  implTags?: Record<string, string[]>;
  // Quality tab
  qualityScore: number | null;
  criteriaChecklist?: Record<string, unknown>;
  // Common
  libraryId: string;
  onTrackEvent?: (name: string, props?: Record<string, string | undefined>) => void;
  // Overview mode - only show Spec tab
  overviewMode?: boolean;
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
        fontFamily: '"MonoLisa", monospace',
        fontSize: level === 1 ? '1rem' : '0.8rem',
        fontWeight: 600,
        color: level === 1 ? '#1f2937' : '#6b7280',
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
            fontFamily: '"MonoLisa", monospace',
            fontSize: '0.8rem',
            bgcolor: '#f3f4f6',
            color: '#be185d',
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
        fontFamily: '"MonoLisa", monospace',
        fontSize: '0.85rem',
        color: '#4b5563',
        lineHeight: 1.7,
        ml: 2,
        mb: 0.25,
        '&::marker': {
          color: '#d1d5db',
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
  imageDescription,
  strengths,
  weaknesses,
  implTags,
  qualityScore,
  criteriaChecklist,
  libraryId,
  onTrackEvent,
  overviewMode = false,
}: SpecTabsProps) {
  const [copied, setCopied] = useState(false);
  // In overview mode, start with Spec tab open; in detail mode, all collapsed
  const [tabIndex, setTabIndex] = useState<number | null>(overviewMode ? 0 : null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});

  // Handle tag click - navigate to filtered catalog (full page navigation)
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
    // Toggle: clicking same tab collapses it
    if (tabIndex === newValue) {
      setTabIndex(null);
      onTrackEvent?.('tab_collapse', { library: libraryId });
    } else {
      setTabIndex(newValue);
      // In overview mode, only Spec tab exists at index 0
      const tabNames = overviewMode
        ? ['specification']
        : ['code', 'specification', 'implementation', 'quality'];
      onTrackEvent?.('tab_click', { tab: tabNames[newValue], library: libraryId });
    }
  };

  // Memoize syntax-highlighted code
  const highlightedCode = useMemo(() => {
    if (!code) return null;
    return (
      <SyntaxHighlighter
        language="python"
        style={oneLight}
        customStyle={{
          margin: 0,
          fontSize: '0.85rem',
          fontFamily: '"MonoLisa", "MonoLisa Fallback", monospace',
          background: 'transparent',
        }}
      >
        {code}
      </SyntaxHighlighter>
    );
  }, [code]);

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
              fontFamily: '"MonoLisa", monospace',
              textTransform: 'none',
              fontSize: '0.875rem',
              minHeight: 48,
            },
            '& .Mui-selected': {
              color: '#3776AB',
            },
            '& .MuiTabs-indicator': {
              backgroundColor: '#3776AB',
            },
          }}
        >
          {!overviewMode && (
            <Tab icon={<CodeIcon sx={{ fontSize: '1.1rem' }} />} iconPosition="start" label="Code" />
          )}
          <Tab icon={<DescriptionIcon sx={{ fontSize: '1.1rem' }} />} iconPosition="start" label="Spec" />
          {!overviewMode && (
            <Tab icon={<ImageIcon sx={{ fontSize: '1.1rem' }} />} iconPosition="start" label="Impl" />
          )}
          {!overviewMode && (
            <Tab
              icon={<StarIcon sx={{ fontSize: '1.1rem', color: tabIndex === 3 ? '#3776AB' : '#f59e0b' }} />}
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
            <Tooltip title={copied ? 'Copied!' : 'Copy code'}>
              <IconButton
                onClick={handleCopy}
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
                bgcolor: '#fafafa',
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
            bgcolor: '#fafafa',
            p: 3,
            borderRadius: 1,
            fontFamily: '"MonoLisa", monospace',
          }}
        >
          {/* Title only - spec ID visible in breadcrumb */}
          <Typography
            component="h2"
            sx={{
              fontFamily: '"MonoLisa", monospace',
              fontSize: '1.1rem',
              fontWeight: 600,
              color: '#1f2937',
              mb: 1.5,
            }}
          >
            {title}
          </Typography>

          {/* ## Description */}
          <MdHeading level={2}>Description</MdHeading>
          <Typography
            sx={{
              fontFamily: '"MonoLisa", monospace',
              fontSize: '0.85rem',
              color: '#4b5563',
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

          {/* Tags grouped by category - compact inline, clickable */}
          {tags && Object.keys(tags).length > 0 && (
            <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e5e7eb', display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              {Object.entries(tags).map(([category, values]) => {
                const paramName = SPEC_TAG_PARAM_MAP[category];
                return (
                  <Box key={category} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography
                      component="span"
                      sx={{
                        fontFamily: '"MonoLisa", monospace',
                        fontSize: '0.65rem',
                        color: '#9ca3af',
                      }}
                    >
                      {category.replace(/_/g, ' ')}:
                    </Typography>
                    {values.map((value, i) => (
                      <Chip
                        key={i}
                        label={value}
                        size="small"
                        onClick={paramName ? () => handleTagClick(paramName, value) : undefined}
                        sx={{
                          fontFamily: '"MonoLisa", monospace',
                          fontSize: '0.65rem',
                          height: 20,
                          bgcolor: '#f3f4f6',
                          color: '#4b5563',
                          cursor: paramName ? 'pointer' : 'default',
                          '&:hover': paramName ? { bgcolor: '#e5e7eb' } : {},
                        }}
                      />
                    ))}
                  </Box>
                );
              })}
            </Box>
          )}

          {/* Metadata footer */}
          <Typography
            sx={{
              fontFamily: '"MonoLisa", monospace',
              fontSize: '0.75rem',
              color: '#9ca3af',
              mt: 2,
            }}
          >
            {specId}{created && ` · ${formatDate(created)}`}
          </Typography>
        </Box>
      </TabPanel>

      {/* Implementation Tab - only in detail mode */}
      {!overviewMode && (
        <TabPanel value={tabIndex} index={2}>
          <Box
            sx={{
              bgcolor: '#fafafa',
              p: 3,
              borderRadius: 1,
              fontFamily: '"MonoLisa", monospace',
            }}
          >
            {/* Image Description */}
            {imageDescription && (
              <>
                <MdHeading level={2}>Description</MdHeading>
                <Typography
                  sx={{
                    fontFamily: '"MonoLisa", monospace',
                    fontSize: '0.85rem',
                    color: '#4b5563',
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
                        fontFamily: '"MonoLisa", monospace',
                        fontSize: '0.85rem',
                        color: '#4b5563',
                        lineHeight: 1.7,
                        ml: 2,
                        mb: 0.25,
                        '&::marker': { color: '#22c55e' },
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
                        fontFamily: '"MonoLisa", monospace',
                        fontSize: '0.85rem',
                        color: '#4b5563',
                        lineHeight: 1.7,
                        ml: 2,
                        mb: 0.25,
                        '&::marker': { color: '#ef4444' },
                      }}
                    >
                      {w}
                    </Typography>
                  ))}
                </Box>
              </>
            )}

            {/* Implementation Tags - only show non-empty categories, clickable */}
            {implTags && Object.entries(implTags).some(([, values]) => values && values.length > 0) && (
              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e5e7eb', display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                {Object.entries(implTags)
                  .filter(([, values]) => values && values.length > 0)
                  .map(([category, values]) => {
                    const paramName = IMPL_TAG_PARAM_MAP[category];
                    return (
                      <Box key={category} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography
                          component="span"
                          sx={{
                            fontFamily: '"MonoLisa", monospace',
                            fontSize: '0.65rem',
                            color: '#9ca3af',
                          }}
                        >
                          {category}:
                        </Typography>
                        {values.map((value, i) => (
                          <Chip
                            key={i}
                            label={value}
                            size="small"
                            onClick={paramName ? () => handleTagClick(paramName, value) : undefined}
                            sx={{
                              fontFamily: '"MonoLisa", monospace',
                              fontSize: '0.65rem',
                              height: 20,
                              bgcolor: '#f3f4f6',
                              color: '#4b5563',
                              cursor: paramName ? 'pointer' : 'default',
                              '&:hover': paramName ? { bgcolor: '#e5e7eb' } : {},
                            }}
                          />
                        ))}
                      </Box>
                    );
                  })}
              </Box>
            )}

            {/* No data message */}
            {!imageDescription && (!strengths || strengths.length === 0) && (!weaknesses || weaknesses.length === 0) && (
              <Typography sx={{ fontFamily: '"MonoLisa", monospace', fontSize: '0.85rem', color: '#9ca3af' }}>
                No implementation review data available.
              </Typography>
            )}
          </Box>
        </TabPanel>
      )}

      {/* Quality Tab - only in detail mode */}
      {!overviewMode && (
        <TabPanel value={tabIndex} index={3}>
        <Box
          sx={{
            bgcolor: '#fafafa',
            p: 3,
            borderRadius: 1,
            fontFamily: '"MonoLisa", monospace',
          }}
        >
          {/* Score */}
          <MdHeading level={2}>Score</MdHeading>
          <Typography
            sx={{
              fontFamily: '"MonoLisa", monospace',
              fontSize: '2rem',
              fontWeight: 700,
              color: qualityScore && qualityScore >= 90 ? '#22c55e' : qualityScore && qualityScore >= 70 ? '#f59e0b' : '#ef4444',
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
                              <ExpandLessIcon sx={{ fontSize: '1rem', color: '#9ca3af' }} />
                            ) : (
                              <ExpandMoreIcon sx={{ fontSize: '1rem', color: '#9ca3af' }} />
                            )
                          )}
                          <Typography sx={{ fontFamily: '"MonoLisa", monospace', fontSize: '0.85rem', color: '#4b5563' }}>
                            {category.replace(/_/g, ' ')}
                          </Typography>
                        </Box>
                        <Typography sx={{ fontFamily: '"MonoLisa", monospace', fontSize: '0.85rem', color: '#6b7280' }}>
                          {score}/{max}
                        </Typography>
                      </Box>
                      {/* Progress bar */}
                      <Box sx={{ height: 4, bgcolor: '#e5e7eb', borderRadius: 2, overflow: 'hidden' }}>
                        <Box
                          sx={{
                            height: '100%',
                            width: `${pct}%`,
                            bgcolor: pct >= 90 ? '#22c55e' : pct >= 70 ? '#f59e0b' : '#ef4444',
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
                                          ? '#ef4444' // red for 0
                                          : item.score === item.max
                                            ? '#22c55e' // green for full
                                            : '#f59e0b', // yellow for partial
                                    }}
                                  />
                                  <Typography sx={{ fontFamily: '"MonoLisa", monospace', fontSize: '0.85rem', color: '#4b5563' }}>
                                    {item.name}
                                  </Typography>
                                </Box>
                                <Typography sx={{ fontFamily: '"MonoLisa", monospace', fontSize: '0.8rem', color: '#9ca3af' }}>
                                  {item.score}/{item.max}
                                </Typography>
                              </Box>
                              {item.comment && (
                                <Typography
                                  sx={{
                                    fontFamily: '"MonoLisa", monospace',
                                    fontSize: '0.85rem',
                                    color: '#6b7280',
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
            <Typography sx={{ fontFamily: '"MonoLisa", monospace', fontSize: '0.85rem', color: '#9ca3af' }}>
              No quality data available.
            </Typography>
          )}
        </Box>
        </TabPanel>
      )}
    </Box>
  );
}
