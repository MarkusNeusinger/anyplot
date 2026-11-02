/**
 * The data panel's full view (`.view_all()`): every row of the current data
 * version in a read-only MUI X Data Grid, the MIT edition, in a dialog that
 * fills a phone's screen.
 *
 * Loaded on demand (`lazyOrFallback` in `DataPanel.tsx`), so the grid's code
 * never reaches the main bundle. It reads the version's canonical `data.csv`
 * (`GET .../dataset/data.csv`) with the minimal RFC 4180 reader of `csv.ts`:
 * every cell is the text the file holds, never formatted again, an empty cell
 * stays empty, and a cell's line breaks and space runs are drawn as the preview
 * draws them (`CellText`). Each header names the column's dtype as the profile
 * does; the `#` column is the row's place in the data, not a column of it.
 *
 * Search over every column (the quick filter), sorting, the column filter and
 * hiding or resizing columns change what the view shows, never the data. A
 * numeric column sorts by number and offers `>`, `>=`, `<` and `<=` beside the
 * text filters, read from the cell's text (`viewTable.ts`); a sort either way
 * up keeps the empty cells last. The MIT grid pages
 * at most 100 rows and filters one column at a time (its forced props); the
 * search, the sort and the filter run over every row.
 *
 * The grid and the inputs, menus and panels it opens take the site theme
 * through a theme of their own (`dataViewTheme.ts`). A new data version while
 * the view is open (a turn that changed the data) makes it read the data again.
 */

import { useEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Dialog from '@mui/material/Dialog';
import InputAdornment from '@mui/material/InputAdornment';
import { ThemeProvider } from '@mui/material/styles';
import TextField from '@mui/material/TextField';
import useMediaQuery from '@mui/material/useMediaQuery';
import {
  ColumnsPanelTrigger,
  DataGrid,
  FilterPanelTrigger,
  GridCloseIcon,
  type GridLocaleText,
  GridSearchIcon,
  QuickFilter,
  QuickFilterClear,
  QuickFilterControl,
} from '@mui/x-data-grid';

import { useTheme } from 'src/hooks/useLayoutContext';
import { AgentApiError, type DatasetProfile } from 'src/lib/agent';
import { CsvError } from 'src/sections/agent-chat/csv';
import { gridColumns, gridRows } from 'src/sections/agent-chat/dataViewGrid';
import { dataViewTheme } from 'src/sections/agent-chat/dataViewTheme';
import { Ellipsis } from 'src/sections/agent-chat/Ellipsis';
import { describeViewFailure } from 'src/sections/agent-chat/messages';
import {
  actionButtonSx,
  bodyTextSx,
  ghostButtonSx,
  labelSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { type ViewTable, viewTable } from 'src/sections/agent-chat/viewTable';
import { colors, fontSize } from 'src/theme';

export interface DataViewProps {
  /** The profile of the version the panel shows; a new one (a new version) reads the data again. */
  profile: DatasetProfile;
  version: number;
  /** The current version's `data.csv` (`agentApi.datasetCsv`). */
  load: (signal: AbortSignal) => Promise<string>;
  onClose: () => void;
  /** Once per opening, when the rows are on screen: the content-free `opened_data_view` beacon. */
  onShown?: () => void;
}

const TITLE_ID = 'agent-data-view-title';
const NOTE_ID = 'agent-data-view-note';
const PAGE_SIZES = [25, 50, 100];

function countOf(count: number, noun: string): string {
  return `${count.toLocaleString('en-US')} ${noun}${count === 1 ? '' : 's'}`;
}

const LOCALE_TEXT: Partial<GridLocaleText> = {
  noRowsLabel: 'no rows',
  noResultsOverlayLabel: 'no row matches the search and the filter',
  paginationRowsPerPage: 'rows a page:',
  paginationDisplayedRows: ({ from, to, count }) =>
    `${from.toLocaleString('en-US')}–${to.toLocaleString('en-US')} of ${count.toLocaleString('en-US')}`,
};

const toolbarButtonSx = { ...actionButtonSx, border: '1px solid var(--rule)' } as const;

/** Search over every column, always open, then the columns panel and the filter panel. */
function DataViewToolbar() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: 1,
        p: 1,
        borderBottom: '1px solid var(--DataGrid-t-color-border-base)',
      }}
    >
      <QuickFilter expanded debounceMs={250} style={{ flex: '1 1 14rem', minWidth: 0 }}>
        <QuickFilterControl
          render={({ ref, ...other }) => (
            <TextField
              {...other}
              inputRef={ref}
              size="small"
              fullWidth
              placeholder="search every column"
              slotProps={{
                ...other.slotProps,
                htmlInput: { ...other.slotProps?.htmlInput, 'aria-label': 'Search every column' },
                input: {
                  ...other.slotProps?.input,
                  startAdornment: (
                    <InputAdornment position="start">
                      <GridSearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                  endAdornment: other.value ? (
                    <InputAdornment position="end">
                      <QuickFilterClear edge="end" size="small" aria-label="Clear the search">
                        <GridCloseIcon fontSize="small" />
                      </QuickFilterClear>
                    </InputAdornment>
                  ) : null,
                },
              }}
            />
          )}
        />
      </QuickFilter>
      <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
        <ColumnsPanelTrigger
          render={props => (
            <Box component="button" type="button" {...props} sx={toolbarButtonSx}>
              .columns()
            </Box>
          )}
        />
        <FilterPanelTrigger
          render={(props, state) => (
            <Box component="button" type="button" {...props} sx={toolbarButtonSx}>
              {state.filterCount > 0 ? `.filter() · ${state.filterCount}` : '.filter()'}
            </Box>
          )}
        />
      </Box>
    </Box>
  );
}

/**
 * Whether an Escape belongs to the grid rather than to the dialog: the grid's panels and menus close
 * on it, and the search clears its text on it. React passes a key press in their portals up to the
 * dialog too, which would close the whole view; the Escape after that closes it.
 */
function escapeForTheGrid(event: object): boolean {
  const target = 'target' in event ? event.target : null;
  if (!(target instanceof Element)) return false;
  if (target.closest('.MuiDataGrid-panel, .MuiDataGrid-menu')) return true;
  return target instanceof HTMLInputElement && target.value !== '';
}

function failureText(err: unknown): string {
  if (err instanceof CsvError) return describeViewFailure('csv', null, err.message);
  if (err instanceof AgentApiError) return describeViewFailure(err.code, err.ref);
  return describeViewFailure('unreachable', null);
}

interface Loaded {
  /** The request it answers: a newer one (a new version, `.retry()`) makes it stale. */
  request: object;
  table?: ViewTable;
  error?: string;
}

export default function DataView({ profile, version, load, onClose, onShown }: DataViewProps) {
  const { isDark } = useTheme();
  const theme = dataViewTheme(isDark ? 'dark' : 'light');
  const phone = useMediaQuery('(max-width: 599.95px)');
  const [attempt, setAttempt] = useState(0);
  // One request per data version and `.retry()`; its answer counts only while it is the current one.
  const request = useMemo(() => ({ profile, version, attempt }), [profile, version, attempt]);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const current = loaded?.request === request ? loaded : null;
  const table = current?.table ?? null;

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal)
      .then(csv => {
        if (!controller.signal.aborted)
          setLoaded({ request, table: viewTable(csv, profile.columns) });
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setLoaded({ request, error: failureText(err) });
      });
    return () => controller.abort();
  }, [load, request, profile]);

  const columns = useMemo(() => (table ? gridColumns(table) : []), [table]);
  const rows = useMemo(() => (table ? gridRows(table) : []), [table]);

  const shown = useRef(false);
  useEffect(() => {
    if (!table || shown.current) return;
    shown.current = true;
    onShown?.();
  }, [table, onShown]);

  const rowCount = table?.rows.length ?? profile.rows;
  const columnCount = table?.columns.length ?? profile.columns.length;

  // The grid's panels and menus mount inside the dialog. In the body they sit beside the modal, whose
  // manager hides them from screen readers for good once a select inside closes (MUI `syncAriaHidden`).
  const gridHome = useRef<HTMLDivElement>(null);
  const slotProps = useMemo(
    () => ({
      basePopper: { material: { container: () => gridHome.current } },
      // At phone width the filter's column, operator and value wrap instead of
      // scrolling the column choice out of the panel.
      ...(phone && { filterPanel: { sx: { '& .MuiDataGrid-filterForm': { flexWrap: 'wrap' } } } }),
    }),
    [phone]
  );

  return (
    <ThemeProvider theme={theme}>
      <Dialog
        open
        onClose={(event, reason) => {
          if (reason === 'escapeKeyDown' && escapeForTheGrid(event)) return;
          onClose();
        }}
        fullScreen={phone}
        fullWidth
        maxWidth="xl"
        aria-labelledby={TITLE_ID}
        aria-describedby={NOTE_ID}
        slotProps={{
          paper: {
            sx: {
              bgcolor: 'var(--bg-elevated)',
              backgroundImage: 'none',
              color: 'var(--ink)',
              colorScheme: isDark ? 'dark' : 'light',
              height: phone ? '100%' : 'min(90vh, 960px)',
              display: 'flex',
              flexDirection: 'column',
              border: phone ? 'none' : '1px solid var(--rule)',
              borderRadius: phone ? 0 : 2,
            },
          },
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 1,
            px: { xs: 1.5, sm: 2 },
            pt: 1.5,
            pb: 1,
          }}
        >
          <Box sx={{ flex: '1 1 auto', minWidth: 0 }}>
            <Box
              component="h2"
              id={TITLE_ID}
              sx={{ ...labelSx, fontSize: fontSize.md, color: 'var(--ink)', fontWeight: 600, m: 0 }}
            >
              # every row · {countOf(rowCount, 'row')} · {countOf(columnCount, 'column')} · version{' '}
              {version}
            </Box>
            <Box id={NOTE_ID} sx={{ ...labelSx, mt: 0.25, overflowWrap: 'anywhere' }}>
              read-only: search, sort and filters change this view, never your data · up to 100 rows
              a page
            </Box>
          </Box>
          <Box
            component="button"
            type="button"
            onClick={onClose}
            aria-label="Close the data view"
            sx={{ ...actionButtonSx, flex: 'none' }}
          >
            .close()
          </Box>
        </Box>

        <Box
          ref={gridHome}
          sx={{
            flex: '1 1 auto',
            minHeight: 0,
            display: 'flex',
            flexDirection: 'column',
            px: { xs: 0, sm: 2 },
            pb: { xs: 0, sm: 2 },
            // The dialog clips what it holds: on a short screen a panel scrolls within the room below the toolbar.
            '& .MuiDataGrid-panel .MuiDataGrid-paper': { maxHeight: 'calc(100dvh - 12rem)' },
          }}
        >
          {table ? (
            <DataGrid
              rows={rows}
              columns={columns}
              aria-labelledby={TITLE_ID}
              density="compact"
              columnHeaderHeight={52}
              showToolbar
              slots={{ toolbar: DataViewToolbar }}
              slotProps={slotProps}
              rowSelection={false}
              pageSizeOptions={PAGE_SIZES}
              initialState={{ pagination: { paginationModel: { pageSize: 100 } } }}
              localeText={LOCALE_TEXT}
              sx={{
                flex: '1 1 auto',
                minHeight: 0,
                borderRadius: phone ? 0 : '4px',
                borderLeftWidth: phone ? 0 : 1,
                borderRightWidth: phone ? 0 : 1,
                '& .data-view-row': { color: 'var(--ink-muted)' },
                '& .MuiDataGrid-columnHeaderTitleContainerContent': { minWidth: 0 },
                // The grid drops the page size below `sm`; the footer has room for it without its label.
                ...(phone && {
                  '& .MuiTablePagination-root .MuiTablePagination-input': {
                    display: 'inline-flex',
                    ml: 0,
                    mr: 1,
                  },
                  '& .MuiTablePagination-actions': { ml: 1 },
                }),
              }}
            />
          ) : current?.error ? (
            <Box sx={{ px: { xs: 1.5, sm: 0 }, display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box role="alert" sx={{ ...bodyTextSx, color: colors.error }}>
                {current.error}
              </Box>
              <Box>
                <Box
                  component="button"
                  type="button"
                  onClick={() => setAttempt(value => value + 1)}
                  sx={ghostButtonSx}
                >
                  .retry()
                </Box>
              </Box>
            </Box>
          ) : (
            <Box
              role="status"
              sx={{
                ...labelSx,
                fontSize: smallText,
                px: { xs: 1.5, sm: 0 },
                color: 'var(--ink-soft)',
              }}
            >
              # reading {countOf(rowCount, 'row')} <Ellipsis />
            </Box>
          )}
        </Box>
      </Dialog>
    </ThemeProvider>
  );
}
