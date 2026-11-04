/**
 * Content of the agent chat's data card (`DataPanel.tsx`): the free-text transcription decision
 * card, the stored dataset's preview and full-view dialog, the table and sheet pickers, and the
 * role bindings. The data comes in through the composer's message box (`Composer.tsx`): a
 * pasted table or a file waits there as an attachment until Enter. `.create_plot()`, which takes
 * the data as shown, sits at the composer's end too.
 */

import { Suspense } from 'react';

import Box from '@mui/material/Box';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { longSuggestion, type tableChoice } from 'src/lib/agent';
import { bindingRows } from 'src/sections/agent-chat/bindings';
import { countOf } from 'src/sections/agent-chat/countOf';
import {
  BindingsBlock,
  ChangeBlock,
  CodeBlock,
  DataViewUnavailable,
  LongHint,
  NotesBlock,
  PreviewTable,
  TranscriptionCard,
  WarningList,
} from 'src/sections/agent-chat/dataCardParts';
import { Ellipsis } from 'src/sections/agent-chat/Ellipsis';
import { lazyOrFallback } from 'src/sections/agent-chat/lazyOrFallback';
import {
  actionButtonSx,
  bodyTextSx,
  labelSx,
  nativeControlSx,
} from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

/** What the server keeps for a file's name its content check refused (`dataset_context.FILE_NAME_WITHHELD`). */
const FILE_NAME_WITHHELD = '(name withheld)';

// The full view's chunk holds the Data Grid: it loads when the user first opens the view (or points at the button).
const loadDataView = () => import('src/sections/agent-chat/DataView');
const DataView = lazyOrFallback(loadDataView, DataViewUnavailable);
// A preload that fails stays quiet: opening the view shows the line above.
const preloadDataView = () => void loadDataView().catch(() => undefined);

export interface DataCardProps {
  state: AgentSessionState;
  ready: boolean;
  working: boolean;
  busy: boolean;
  choice: ReturnType<typeof tableChoice>;
  viewOpen: boolean;
  setViewOpen: (open: boolean) => void;
  viewButtonRef: React.RefObject<HTMLButtonElement | null>;
  onTable: (table: number) => void;
  /** The sheet picker of a workbook the data came from: that sheet, read again on the server. */
  onSheet: (sheet: string) => void;
  /** While the server reads another sheet, what the picker's line says; null otherwise. */
  sheetLine: string | null;
  /** Why the server could not read the sheet. */
  sheetError: string | null;
  onUse: () => void;
  onDiscardTranscription: () => void;
  onBind: (role: string, column: string | null) => void;
  onUndo: () => void;
  onToLong?: () => void;
  onLoadData?: (signal: AbortSignal) => Promise<string>;
  onDataViewShown?: () => void;
}

export function DataCard(props: DataCardProps) {
  const { state, ready, working, busy, choice, viewOpen, setViewOpen, viewButtonRef } = props;
  const { onTable, onSheet, sheetLine, sheetError, onUse, onDiscardTranscription } = props;
  const { onBind, onUndo, onToLong, onLoadData, onDataViewShown } = props;

  const transcription = state.transcription;
  const dataset = state.dataset;
  const file = dataset?.file;
  const columns = dataset?.parsed.profile.columns ?? [];
  // An earlier version exists above the paste's 1, until the server says the
  // history ended (it keeps the last five versions).
  const canUndo =
    ready &&
    !busy &&
    (dataset?.parsed.version ?? 1) > 1 &&
    state.undoError?.code !== 'nothing_to_undo';
  const rows = bindingRows(state.roles, state.bindings, columns.length);
  // The service's wide-table offer, checked again here: the dataset route's answer is not typed.
  const suggestion = longSuggestion(dataset?.parsed.suggestion);

  return (
    <>
      <Box sx={{ ...labelSx, mb: 0.75 }}># your data</Box>

      {transcription && (
        <TranscriptionCard
          transcription={transcription}
          canUse={ready && !busy}
          onUse={onUse}
          onDiscard={onDiscardTranscription}
        />
      )}

      {dataset && (
        <Box sx={{ mt: 1.5, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
          {state.dataChange && (
            <ChangeBlock
              change={state.dataChange}
              canUndo={canUndo}
              undoBusy={state.undoBusy}
              error={state.undoError}
              onUndo={onUndo}
            />
          )}

          {suggestion && onToLong && (
            <LongHint
              suggestion={suggestion}
              canApply={ready && !busy && !state.toLongBusy && !transcription}
              busy={state.toLongBusy}
              error={state.toLongError}
              onApply={onToLong}
            />
          )}

          <Box sx={{ ...labelSx, color: 'var(--ink-soft)' }}>
            {dataset.parsed.profile.rows.toLocaleString('en-US')} rows · {columns.length} columns ·{' '}
            {dataset.parsed.profile.source_format}
            {/* The file's name as the server kept it: the assistant reads it as data, never as a note. */}
            {dataset.parsed.file_name && (
              <Box component="span" data-testid="data-file-name" sx={{ overflowWrap: 'anywhere' }}>
                {' '}
                ·{' '}
                {dataset.parsed.file_name === FILE_NAME_WITHHELD
                  ? 'from a file, name withheld by the content check'
                  : `from "${dataset.parsed.file_name}"`}
              </Box>
            )}
          </Box>

          {/* The other tables of the pasted text (a report sheet with two tables one below the
              other): a choice parses the same text again and reads that table. */}
          {choice && (
            <Box
              data-testid="data-tables"
              sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1, minWidth: 0 }}
            >
              <Box component="label" htmlFor="agent-data-table" sx={labelSx}>
                # table ({choice.tables.length})
              </Box>
              <Box
                component="select"
                id="agent-data-table"
                value={choice.table}
                disabled={!ready || busy || !!sheetLine}
                onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                  onTable(Number(event.target.value))
                }
                sx={{ ...nativeControlSx, maxWidth: '100%', minWidth: 0 }}
              >
                {choice.tables.map((label, index) => (
                  <option key={index} value={index + 1}>
                    {`${index + 1} · ${label}`}
                  </option>
                ))}
              </Box>
            </Box>
          )}

          {/* The other sheets of the workbook the data came from (or arrays of an .npz): a choice
              reads the same file again on the server and parses that sheet. Only the visible
              sheets are named, at most ten. */}
          {file && file.sheets.length > 1 && (
            <Box
              data-testid="file-sheets"
              sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1, minWidth: 0 }}
            >
              <Box component="label" htmlFor="agent-file-sheet" sx={labelSx}>
                # {file.kind === 'npz' ? 'array' : 'sheet'}
                {file.sheetCount > file.sheets.length
                  ? ` (first ${file.sheets.length} of ${file.sheetCount})`
                  : ` (${file.sheets.length})`}
              </Box>
              <Box
                component="select"
                id="agent-file-sheet"
                value={file.sheet ?? ''}
                disabled={!ready || busy || !!sheetLine}
                onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                  onSheet(event.target.value)
                }
                sx={{ ...nativeControlSx, maxWidth: '100%', minWidth: 0 }}
              >
                {file.sheets.map(name => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </Box>
              {sheetLine && (
                <Box
                  role="status"
                  data-testid="sheet-reading"
                  sx={{ ...labelSx, display: 'inline-flex', alignItems: 'center', gap: 1 }}
                >
                  # {sheetLine}
                  <LoaderSpinner size="inline" />
                </Box>
              )}
            </Box>
          )}
          {sheetError && (
            <Box
              role="alert"
              data-testid="sheet-error"
              sx={{ ...bodyTextSx, color: colors.error, overflowWrap: 'anywhere' }}
            >
              {sheetError}
            </Box>
          )}

          <WarningList warnings={dataset.parsed.warnings} />

          <NotesBlock lines={dataset.parsed.context_lines ?? []} />

          <CodeBlock code={dataset.parsed.code} />

          <Box sx={{ minWidth: 0 }}>
            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                justifyContent: 'space-between',
                columnGap: 1,
                mb: 0.5,
              }}
            >
              <Box sx={labelSx}># preview — first {dataset.parsed.preview.length} rows</Box>
              {onLoadData && (
                <Box
                  component="button"
                  type="button"
                  ref={viewButtonRef}
                  onClick={() => setViewOpen(true)}
                  // The grid's chunk starts loading as the pointer or the focus reaches the button.
                  onPointerEnter={preloadDataView}
                  onFocus={preloadDataView}
                  aria-haspopup="dialog"
                  aria-label={`View all ${countOf(dataset.parsed.profile.rows, 'row')}`}
                  // Flush right, also on its own line at phone width.
                  sx={{ ...actionButtonSx, ml: 'auto', mr: -1.25 }}
                >
                  .view_all()
                </Box>
              )}
            </Box>
            <PreviewTable columns={columns} rows={dataset.parsed.preview} />
            {viewOpen && onLoadData && (
              <Suspense
                fallback={
                  <Box role="status" sx={{ ...labelSx, mt: 0.5 }}>
                    # loading the table view <Ellipsis />
                  </Box>
                }
              >
                <DataView
                  profile={dataset.parsed.profile}
                  version={dataset.parsed.version ?? 1}
                  load={onLoadData}
                  onShown={onDataViewShown}
                  onClose={() => {
                    setViewOpen(false);
                    viewButtonRef.current?.focus({ preventScroll: true });
                  }}
                />
              </Suspense>
            )}
          </Box>

          <BindingsBlock
            rows={rows}
            columns={columns}
            bindings={state.bindings}
            missingRoles={state.missingRoles}
            bindingsBusy={state.bindingsBusy}
            bindingsError={state.bindingsError}
            parsing={state.parsing}
            ready={ready}
            working={working}
            busy={busy}
            suggestion={suggestion}
            onBind={onBind}
          />

          {/* No foot: `.create_plot()`, which takes the data as shown, and the line that says
              what it waits for sit at the composer's end. */}
        </Box>
      )}
    </>
  );
}
