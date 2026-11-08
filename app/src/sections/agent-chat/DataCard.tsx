/**
 * Content of the agent chat's data card (`DataPanel.tsx`): for the stored data (`part: 'data'`)
 * its preview and full-view dialog, the table and sheet pickers, and the role bindings; for a
 * table read from text (`part: 'transcription'`) the decision card with `.use()` and `.discard()`.
 * The data comes in through the composer's message box (`Composer.tsx`): a pasted table or a
 * file waits there as an attachment until Enter. `.create_plot()`, which takes the data as shown,
 * sits at the composer's end too.
 *
 * The bindings stand in one line under the preview (`BindingsLine`), with `.change()`, which
 * opens the dropdowns (`BindingsBlock`) and turns into `.hide()`. The dropdowns open by
 * themselves when a required role has no column or the server refused the bindings, and stay
 * open after the user fixed it, so the focus never loses its control; `.hide()` closes them.
 * While they are closed, a warning on a bound column (negative values, a wide table's number
 * column) stands under the line.
 *
 * At phone width the card shows no preview table: `.view_all()` opens every row, and it stands
 * with `.change()` on the card's action line under the bindings line.
 */

import { Suspense, useState } from 'react';

import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { longSuggestion, type tableChoice } from 'src/lib/agent';
import {
  bindingHint,
  bindingRows,
  boundRoles,
  checkOnlyWarnings,
} from 'src/sections/agent-chat/bindings';
import { fileSource } from 'src/sections/agent-chat/cardLabels';
import { countOf } from 'src/sections/agent-chat/countOf';
import {
  BindingsBlock,
  BindingsLine,
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
import { liveDataVersion } from 'src/sections/agent-chat/steps';
import {
  actionButtonSx,
  bodyTextSx,
  cardActionSx,
  labelSx,
  nativeControlSx,
  PHONE_QUERY,
  smallText,
} from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

/** The dropdowns' block, which `.change()` controls; the thread has one live data card. */
const BINDINGS_EDITOR_ID = 'agent-bindings-editor';

// The full view's chunk holds the Data Grid: it loads when the user first opens the view (or points at the button).
const loadDataView = () => import('src/sections/agent-chat/DataView');
const DataView = lazyOrFallback(loadDataView, DataViewUnavailable);
// A preload that fails stays quiet: opening the view shows the line above.
const preloadDataView = () => void loadDataView().catch(() => undefined);

export interface DataCardProps {
  state: AgentSessionState;
  /** The stored data's card, or the card of a table read from text that waits for its decision. */
  part: 'data' | 'transcription';
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
  /** `.change()` opened the dropdowns, or `.view_all()` the full view: the user looks at the data. */
  onLook?: () => void;
}

export function DataCard(props: DataCardProps) {
  const { state, part, ready, working, busy, choice, viewOpen, setViewOpen, viewButtonRef } = props;
  const { onTable, onSheet, sheetLine, sheetError, onUse, onDiscardTranscription } = props;
  const { onBind, onUndo, onToLong, onLoadData, onDataViewShown, onLook } = props;

  const transcription = part === 'transcription' ? state.transcription : null;
  const dataset = part === 'data' ? state.dataset : null;
  const file = dataset?.file;
  const columns = dataset?.parsed.profile.columns ?? [];
  // The server says whether its history holds a version to restore (it keeps the last five);
  // the version's number says nothing about it, since a paste can carry any number.
  const undoable = dataset?.parsed.can_undo === true;
  const canUndo = ready && !busy && undoable && state.undoError?.code !== 'nothing_to_undo';
  const rows = bindingRows(state.roles, state.bindings, columns.length);
  // The service's wide-table offer, checked again here: the dataset route's answer is not typed.
  const suggestion = longSuggestion(dataset?.parsed.suggestion);
  // Read at the first render, so a phone never paints the preview table first.
  const narrow = useMediaQuery(PHONE_QUERY, { noSsr: true });

  // The dropdowns behind `.change()`: open by themselves when a required role has no column or
  // the server refused the bindings, and open after that until the user closes them, so a fix
  // never takes the control from under the focus. Adjusted while rendering, React's pattern for
  // state that follows a prop.
  const attention = !!dataset && (state.missingRoles.length > 0 || !!state.bindingsError);
  const [editing, setEditing] = useState(attention);
  const [attentionSeen, setAttentionSeen] = useState(attention);
  if (attention !== attentionSeen) {
    setAttentionSeen(attention);
    if (attention) setEditing(true);
  }
  // A bound column's warning: in the dropdowns' rows while they are open, under the line else.
  const hints = editing
    ? []
    : rows.flatMap(row => {
        const bound: string[] = row.role.variadic
          ? row.members.map(([, column]) => column)
          : state.bindings[row.name]
            ? [state.bindings[row.name]]
            : [];
        return bound.flatMap(column => {
          const hint = bindingHint(row.role, column, columns, suggestion);
          return hint ? [`${column}: ${hint}`] : [];
        });
      });

  const checkOnly = dataset ? checkOnlyWarnings(state.bindingWarnings) : [];

  const bindingsToggle = (
    <Box
      component="button"
      type="button"
      onClick={() => {
        if (!editing) onLook?.();
        setEditing(open => !open);
      }}
      aria-expanded={editing}
      aria-controls={editing ? BINDINGS_EDITOR_ID : undefined}
      aria-label={editing ? 'Hide the bindings' : 'Change the bindings'}
      sx={narrow ? cardActionSx : actionButtonSx}
    >
      {editing ? '.hide()' : '.change()'}
    </Box>
  );
  const viewAll = onLoadData && dataset && (
    <Box
      component="button"
      type="button"
      ref={viewButtonRef}
      onClick={() => {
        onLook?.();
        setViewOpen(true);
      }}
      // The grid's chunk starts loading as the pointer or the focus reaches the button.
      onPointerEnter={preloadDataView}
      onFocus={preloadDataView}
      aria-haspopup="dialog"
      aria-label={`View all ${countOf(dataset.parsed.profile.rows, 'row')}`}
      // Flush right beside the preview's label, also on its own line; first on the phone's line.
      sx={narrow ? cardActionSx : { ...actionButtonSx, ml: 'auto', mr: -1.25 }}
    >
      .view_all()
    </Box>
  );

  return (
    <>
      {transcription && (
        <TranscriptionCard
          transcription={transcription}
          canUse={ready && !busy}
          onUse={onUse}
          onDiscard={onDiscardTranscription}
        />
      )}

      {dataset && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
          {state.dataChange && (
            <ChangeBlock
              change={state.dataChange}
              first={state.dataChange.kind === 'changed' && !undoable}
              canUndo={canUndo}
              undoBusy={state.undoBusy}
              error={state.undoError}
              onUndo={onUndo}
            />
          )}

          {suggestion && onToLong && (
            <LongHint
              suggestion={suggestion}
              canApply={ready && !busy && !state.toLongBusy && !state.transcription}
              busy={state.toLongBusy}
              error={state.toLongError}
              onApply={onToLong}
            />
          )}

          {/* The shape is the card's label: the line says how the data came. */}
          <Box data-testid="data-source" sx={{ ...labelSx, color: 'var(--ink-soft)' }}>
            read as {dataset.parsed.profile.source_format}
            {/* The file's name as the server kept it: the assistant reads it as data, never as a note. */}
            {dataset.parsed.file_name && (
              <Box component="span" data-testid="data-file-name" sx={{ overflowWrap: 'anywhere' }}>
                {' '}
                · {fileSource(dataset.parsed.file_name)}
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

          {/* The preview from `sm` up; a phone has no room for a table, `.view_all()` opens it. */}
          {!narrow && (
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
                {viewAll}
              </Box>
              <PreviewTable columns={columns} rows={dataset.parsed.preview} />
            </Box>
          )}

          <Box sx={{ minWidth: 0, display: 'flex', flexDirection: 'column', gap: 1 }}>
            <BindingsLine
              roles={boundRoles(rows, state.bindings)}
              hasRoles={rows.length > 0}
              checking={state.bindingsBusy}
              toggle={narrow ? undefined : bindingsToggle}
            />
            {hints.map(hint => (
              <Box
                key={hint}
                data-testid="sign-hint"
                sx={{ ...labelSx, fontSize: smallText, color: colors.warning }}
              >
                {hint}
              </Box>
            ))}
            {/* The server's binding check names more than a bound column's own warning: a key
                whose rows repeat, another window, an inverted pair. Open or closed dropdowns,
                they stand under the line, since no single dropdown holds them. */}
            {checkOnly.map(line => (
              <Box
                key={line}
                data-testid="binding-warning"
                sx={{
                  ...labelSx,
                  fontSize: smallText,
                  color: colors.warning,
                  overflowWrap: 'anywhere',
                }}
              >
                {line}
              </Box>
            ))}
            {/* The phone's action line: what the desktop has beside the preview and the line. */}
            {narrow && (
              <Box
                data-testid="data-actions"
                sx={{ display: 'flex', flexWrap: 'wrap', columnGap: 1, rowGap: 0.5, ml: -1.25 }}
              >
                {viewAll}
                {bindingsToggle}
              </Box>
            )}
            {editing && (
              <BindingsBlock
                id={BINDINGS_EDITOR_ID}
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
            )}
          </Box>

          {viewOpen && onLoadData && (
            <Suspense
              fallback={
                <Box role="status" sx={labelSx}>
                  # loading the table view <Ellipsis />
                </Box>
              }
            >
              <DataView
                profile={dataset.parsed.profile}
                version={liveDataVersion(state) ?? dataset.parsed.version ?? 1}
                load={onLoadData}
                onShown={onDataViewShown}
                onClose={() => {
                  setViewOpen(false);
                  viewButtonRef.current?.focus({ preventScroll: true });
                }}
              />
            </Suspense>
          )}

          {/* No foot: `.create_plot()`, which takes the data as shown, and the line that says
              what it waits for sit at the composer's end. */}
        </Box>
      )}
    </>
  );
}
