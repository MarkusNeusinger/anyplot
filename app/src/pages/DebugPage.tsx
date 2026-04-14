import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import Paper from '@mui/material/Paper';
import Skeleton from '@mui/material/Skeleton';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

import { API_URL, LIBRARIES } from '../constants';
import { Breadcrumb } from '../components/Breadcrumb';
import {
  typography,
  colors,
  semanticColors,
  fontSize,
} from '../theme';

// ============================================================================
// Types
// ============================================================================

interface SpecStatus {
  id: string;
  title: string;
  updated: string | null;
  avg_score: number | null;
  altair: number | null;
  bokeh: number | null;
  highcharts: number | null;
  letsplot: number | null;
  matplotlib: number | null;
  plotly: number | null;
  plotnine: number | null;
  pygal: number | null;
  seaborn: number | null;
}

interface LibraryStats {
  id: string;
  name: string;
  impl_count: number;
  avg_score: number | null;
  min_score: number | null;
  max_score: number | null;
}

interface ProblemSpec {
  id: string;
  title: string;
  issue: string;
  value: string | null;
}

interface SystemHealth {
  database_connected: boolean;
  api_response_time_ms: number;
  timestamp: string;
  total_specs_in_db: number;
  total_impls_in_db: number;
}

interface DebugStatus {
  total_specs: number;
  total_implementations: number;
  coverage_percent: number;
  library_stats: LibraryStats[];
  low_score_specs: ProblemSpec[];
  oldest_specs: ProblemSpec[];
  missing_preview_specs: ProblemSpec[];
  missing_tags_specs: ProblemSpec[];
  system: SystemHealth;
  specs: SpecStatus[];
}

type SortKey = 'updated' | 'id' | 'title' | 'avg_score';
type SortDir = 'asc' | 'desc';

// ============================================================================
// Helper Components
// ============================================================================

const getScoreColor = (score: number | null): string => {
  if (score === null) return colors.gray[300];
  if (score >= 90) return colors.success;
  if (score >= 50) return colors.warning;
  return colors.error;
};

const ScoreCell = ({ score, specId, library }: { score: number | null; specId: string; library: string }) => {
  if (score === null) {
    return (
      <Typography sx={{ color: colors.gray[300], fontSize: fontSize.xs, textAlign: 'center' }}>-</Typography>
    );
  }
  return (
    <Box
      component={Link}
      to={`/${specId}/${library}`}
      sx={{ display: 'block', textDecoration: 'none', textAlign: 'center', '&:hover': { opacity: 0.7 } }}
    >
      <Typography sx={{ fontSize: fontSize.xs, fontFamily: typography.fontFamily, fontWeight: 600, color: getScoreColor(score) }}>
        {Math.round(score)}
      </Typography>
    </Box>
  );
};

const ProblemList = ({ items, title, icon }: { items: ProblemSpec[]; title: string; icon?: React.ReactNode }) => {
  if (items.length === 0) return null;
  return (
    <Accordion defaultExpanded={items.length <= 5}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {icon}
          <Typography sx={{ fontWeight: 500 }}>{title}</Typography>
          <Chip label={items.length} size="small" color="warning" />
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Table size="small">
          <TableBody>
            {items.map((item, idx) => (
              <TableRow key={`${item.id}-${idx}`}>
                <TableCell sx={{ width: 200 }}>
                  <Box
                    component={Link}
                    to={`/${item.id}`}
                    sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.sm, color: colors.primary, textDecoration: 'none' }}
                  >
                    {item.id}
                  </Box>
                </TableCell>
                <TableCell sx={{ color: semanticColors.mutedText, fontSize: fontSize.sm }}>{item.issue}</TableCell>
                {item.value && (
                  <TableCell sx={{ fontFamily: typography.fontFamily, fontSize: fontSize.sm, color: colors.error }}>
                    {item.value}
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </AccordionDetails>
    </Accordion>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export function DebugPage() {
  const [data, setData] = useState<DebugStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('updated');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  // Filter states
  const [searchText, setSearchText] = useState('');
  const [showIncomplete, setShowIncomplete] = useState(false);
  const [showLowScores, setShowLowScores] = useState(false);
  const [missingLibrary, setMissingLibrary] = useState<string>('');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/debug/status`);
        if (!res.ok) throw new Error('Failed to load status');
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError('Failed to load debug status');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, []);

  const countImpls = (spec: SpecStatus): number => {
    return LIBRARIES.filter((lib) => spec[lib as keyof SpecStatus] !== null).length;
  };

  // Threshold for low scores - matches workflow ai-approved threshold
  const LOW_SCORE_THRESHOLD = 90;

  const hasLowScore = (spec: SpecStatus): boolean => {
    return LIBRARIES.some((lib) => {
      const score = spec[lib as keyof SpecStatus] as number | null;
      return score !== null && score < LOW_SCORE_THRESHOLD;
    });
  };

  const filteredSpecs = useMemo(() => {
    if (!data) return [];
    let filtered = [...data.specs];

    if (searchText) {
      const search = searchText.toLowerCase();
      filtered = filtered.filter(
        (spec) => spec.id.toLowerCase().includes(search) || spec.title.toLowerCase().includes(search)
      );
    }
    if (showIncomplete) {
      filtered = filtered.filter((spec) => countImpls(spec) < 9);
    }
    if (showLowScores) {
      filtered = filtered.filter((spec) => hasLowScore(spec));
    }
    if (missingLibrary) {
      filtered = filtered.filter((spec) => spec[missingLibrary as keyof SpecStatus] === null);
    }

    filtered.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'updated':
          cmp = (a.updated || '').localeCompare(b.updated || '');
          break;
        case 'id':
          cmp = a.id.localeCompare(b.id);
          break;
        case 'title':
          cmp = a.title.localeCompare(b.title);
          break;
        case 'avg_score':
          cmp = (a.avg_score || 0) - (b.avg_score || 0);
          break;
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });

    return filtered;
  }, [data, searchText, showIncomplete, showLowScores, missingLibrary, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'updated' || key === 'avg_score' ? 'desc' : 'asc');
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 4 }}>
        <Skeleton variant="text" width={300} height={40} />
        <Skeleton variant="rectangular" height={400} sx={{ mt: 2 }} />
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography color="error">{error || 'Failed to load'}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, minHeight: '100vh', bgcolor: colors.background }}>
      {/* Breadcrumb */}
      <Breadcrumb
        items={[{ label: 'anyplot.ai', shortLabel: 'ap', to: '/' }, { label: 'debug' }]}
        sx={{
          mx: 0,
          mt: 0,
          px: 0,
          bgcolor: 'transparent',
          borderBottom: 'none',
          fontWeight: 600,
          fontSize: fontSize.base,
        }}
      />

      {/* Stats */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Chip label={`${data.total_specs} specs`} size="small" />
          <Chip label={`${data.total_implementations} implementations`} size="small" />
          <Chip
            label={`${data.coverage_percent}% coverage`}
            size="small"
            color={data.coverage_percent >= 90 ? 'success' : data.coverage_percent >= 70 ? 'warning' : 'error'}
          />
          <Chip
            label={`${filteredSpecs.length} shown`}
            size="small"
            variant="outlined"
            color={filteredSpecs.length < data.total_specs ? 'primary' : 'default'}
          />
        </Box>
      </Box>

      {/* System Health */}
      <Paper sx={{ p: 2, mb: 2, display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {data.system.database_connected ? (
            <CheckCircleIcon sx={{ color: colors.success, fontSize: 18 }} />
          ) : (
            <WarningIcon sx={{ color: colors.error, fontSize: 18 }} />
          )}
          <Typography sx={{ fontSize: fontSize.sm }}>Database</Typography>
        </Box>
        <Typography sx={{ fontSize: fontSize.sm, color: semanticColors.mutedText }}>
          Response: <strong>{data.system.api_response_time_ms.toFixed(0)}ms</strong>
        </Typography>
        <Typography sx={{ fontSize: fontSize.sm, color: semanticColors.mutedText }}>
          Updated: {new Date(data.system.timestamp).toLocaleTimeString()}
        </Typography>
      </Paper>

      {/* Library Stats */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography sx={{ fontWeight: 600, mb: 1.5 }}>Library Coverage</Typography>
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
          {data.library_stats.map((lib) => (
            <Paper
              key={lib.id}
              elevation={0}
              sx={{
                p: 1.5,
                bgcolor: colors.gray[50],
                border: `1px solid ${colors.gray[200]}`,
                borderRadius: 1,
                minWidth: 100,
              }}
            >
              <Typography sx={{ fontSize: fontSize.xs, fontWeight: 600, color: colors.gray[700] }}>{lib.name}</Typography>
              <Typography sx={{ fontSize: '1.25rem', fontWeight: 700, color: colors.primary }}>{lib.impl_count}</Typography>
              <Typography sx={{ fontSize: fontSize.xs, color: getScoreColor(lib.avg_score) }}>
                avg: {lib.avg_score?.toFixed(1) || '-'}
              </Typography>
              <Typography sx={{ fontSize: fontSize.xxs, color: semanticColors.mutedText }}>
                {lib.min_score?.toFixed(0) || '-'} - {lib.max_score?.toFixed(0) || '-'}
              </Typography>
            </Paper>
          ))}
        </Box>
      </Paper>

      {/* Problem Areas */}
      {(data.low_score_specs.length > 0 ||
        data.oldest_specs.length > 0 ||
        data.missing_preview_specs.length > 0 ||
        data.missing_tags_specs.length > 0) && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography sx={{ fontWeight: 600, mb: 1.5 }}>Problem Areas</Typography>
          <ProblemList
            items={data.low_score_specs}
            title="Low Scores (avg < 85)"
            icon={<WarningIcon sx={{ color: colors.error, fontSize: 18 }} />}
          />
          <ProblemList
            items={data.missing_preview_specs}
            title="Missing Previews"
            icon={<WarningIcon sx={{ color: colors.warning, fontSize: 18 }} />}
          />
          <ProblemList
            items={data.missing_tags_specs}
            title="Missing Tags"
            icon={<WarningIcon sx={{ color: colors.warning, fontSize: 18 }} />}
          />
          <ProblemList
            items={data.oldest_specs}
            title="Oldest Specs"
            icon={<WarningIcon sx={{ color: semanticColors.mutedText, fontSize: 18 }} />}
          />
        </Paper>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          size="small"
          label="Search"
          placeholder="Spec ID or title..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          sx={{ minWidth: 200 }}
        />
        <FormControlLabel
          control={<Checkbox checked={showIncomplete} onChange={(e) => setShowIncomplete(e.target.checked)} />}
          label={<Typography sx={{ fontSize: fontSize.md }}>Incomplete ({'<'}9)</Typography>}
        />
        <FormControlLabel
          control={<Checkbox checked={showLowScores} onChange={(e) => setShowLowScores(e.target.checked)} />}
          label={<Typography sx={{ fontSize: fontSize.md }}>Low scores ({'<'}90)</Typography>}
        />
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Missing library</InputLabel>
          <Select value={missingLibrary} label="Missing library" onChange={(e) => setMissingLibrary(e.target.value)}>
            <MenuItem value="">
              <em>Any</em>
            </MenuItem>
            {LIBRARIES.map((lib) => (
              <MenuItem key={lib} value={lib}>
                {lib}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Paper>

      {/* Legend */}
      <Box sx={{ mb: 2, display: 'flex', gap: 3, flexWrap: 'wrap', fontSize: fontSize.xs }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, bgcolor: colors.success, borderRadius: 0.5 }} />
          <span>90+ (excellent)</span>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, bgcolor: colors.warning, borderRadius: 0.5 }} />
          <span>50-89 (acceptable)</span>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, bgcolor: colors.error, borderRadius: 0.5 }} />
          <span>&lt;50 (poor)</span>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, bgcolor: colors.gray[300], borderRadius: 0.5 }} />
          <span>- (missing)</span>
        </Box>
      </Box>

      {/* Table */}
      <TableContainer component={Paper} sx={{ maxHeight: 'calc(100vh - 580px)' }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600, minWidth: 180 }}>
                <TableSortLabel
                  active={sortKey === 'id'}
                  direction={sortKey === 'id' ? sortDir : 'asc'}
                  onClick={() => handleSort('id')}
                >
                  Spec ID
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 600, minWidth: 180 }}>
                <TableSortLabel
                  active={sortKey === 'title'}
                  direction={sortKey === 'title' ? sortDir : 'asc'}
                  onClick={() => handleSort('title')}
                >
                  Title
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 600, width: 50 }} align="center">
                #
              </TableCell>
              <TableCell sx={{ fontWeight: 600, width: 50 }} align="center">
                <TableSortLabel
                  active={sortKey === 'avg_score'}
                  direction={sortKey === 'avg_score' ? sortDir : 'desc'}
                  onClick={() => handleSort('avg_score')}
                >
                  Avg
                </TableSortLabel>
              </TableCell>
              {LIBRARIES.map((lib) => (
                <TableCell key={lib} align="center" sx={{ fontWeight: 600, fontSize: fontSize.xs, minWidth: 45, px: 0.5 }}>
                  {lib.slice(0, 4)}
                </TableCell>
              ))}
              <TableCell sx={{ fontWeight: 600, width: 100 }}>
                <TableSortLabel
                  active={sortKey === 'updated'}
                  direction={sortKey === 'updated' ? sortDir : 'desc'}
                  onClick={() => handleSort('updated')}
                >
                  Updated
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredSpecs.map((spec) => {
              const implCount = countImpls(spec);
              return (
                <TableRow key={spec.id} hover sx={{ '&:hover': { bgcolor: colors.gray[100] } }}>
                  <TableCell>
                    <Box
                      component={Link}
                      to={`/${spec.id}`}
                      sx={{
                        fontFamily: typography.fontFamily,
                        fontSize: fontSize.sm,
                        color: colors.primary,
                        textDecoration: 'none',
                        '&:hover': { textDecoration: 'underline' },
                      }}
                    >
                      {spec.id}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography
                      sx={{
                        fontSize: fontSize.sm,
                        color: semanticColors.labelText,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        maxWidth: 200,
                      }}
                    >
                      {spec.title}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography
                      sx={{
                        fontSize: fontSize.xs,
                        fontWeight: 600,
                        fontFamily: typography.fontFamily,
                        color: implCount === 9 ? colors.success : implCount > 0 ? semanticColors.mutedText : colors.gray[300],
                      }}
                    >
                      {implCount}/9
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography
                      sx={{
                        fontSize: fontSize.xs,
                        fontWeight: 600,
                        fontFamily: typography.fontFamily,
                        color: getScoreColor(spec.avg_score),
                      }}
                    >
                      {spec.avg_score?.toFixed(1) || '-'}
                    </Typography>
                  </TableCell>
                  {LIBRARIES.map((lib) => (
                    <TableCell key={lib} align="center" sx={{ px: 0.5 }}>
                      <ScoreCell score={spec[lib as keyof SpecStatus] as number | null} specId={spec.id} library={lib} />
                    </TableCell>
                  ))}
                  <TableCell>
                    <Typography sx={{ fontSize: fontSize.xs, fontFamily: typography.fontFamily, color: semanticColors.mutedText }}>
                      {spec.updated
                        ? new Date(spec.updated).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                        : '-'}
                    </Typography>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
