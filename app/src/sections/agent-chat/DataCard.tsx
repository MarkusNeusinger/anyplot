/**
 * Content of the agent chat's data card (`DataPanel.tsx`): the text box and
 * file drop zone, the free-text transcription
 * decision card, the stored dataset's preview and full-view dialog, and the
 * role bindings. Step 1's `.confirm()` sits at the composer's end (`Composer.tsx`).
 */

import { Suspense } from 'react';

import Box from '@mui/material/Box';

import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { longSuggestion, MAX_DATASET_BYTES, type tableChoice, utf8Bytes } from 'src/lib/agent';
import { bindingRows } from 'src/sections/agent-chat/bindings';
import { BoxWorking } from 'src/sections/agent-chat/BoxWorking';
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
import { FILE_ACCEPT } from 'src/sections/agent-chat/fileText';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import { lazyOrFallback } from 'src/sections/agent-chat/lazyOrFallback';
import {
  DATA_HOWTO,
  DATA_PLACEHOLDER,
  describeDataFailure,
} from 'src/sections/agent-chat/messages';
import {
  actionButtonSx,
  bodyTextSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import type { FileIntake } from 'src/sections/agent-chat/useFileIntake';
import { colors, fontSize } from 'src/theme';

/** What the server keeps for a file's name its content check refused (`dataset_context.FILE_NAME_WITHHELD`). */
const FILE_NAME_WITHHELD = '(name withheld)';

// The full view's chunk holds the Data Grid: it loads when the user first opens the view (or points at the button).
const loadDataView = () => import('src/sections/agent-chat/DataView');
const DataView = lazyOrFallback(loadDataView, DataViewUnavailable);
// A preload that fails stays quiet: opening the view shows the line above.
const preloadDataView = () => void loadDataView().catch(() => undefined);

function formatKb(bytes: number): string {
  return `${(bytes / 1024).toFixed(bytes < 10 * 1024 ? 1 : 0)} KB`;
}

export interface DataCardProps {
  state: AgentSessionState;
  intake: FileIntake;
  text: string;
  ready: boolean;
  working: boolean;
  busy: boolean;
  locked: boolean;
  confirmed: boolean;
  choice: ReturnType<typeof tableChoice>;
  viewOpen: boolean;
  setViewOpen: (open: boolean) => void;
  viewButtonRef: React.RefObject<HTMLButtonElement | null>;
  parseStart: React.RefObject<number>;
  onParse: () => void;
  onTable: (table: number) => void;
  onUse: () => void;
  onDiscardTranscription: () => void;
  onBind: (role: string, column: string | null) => void;
  onUndo: () => void;
  onToLong?: () => void;
  onLoadData?: (signal: AbortSignal) => Promise<string>;
  onDataViewShown?: () => void;
}

export function DataCard(props: DataCardProps) {
  const { state, intake, text, ready, working, busy, locked, confirmed, choice } = props;
  const { viewOpen, setViewOpen, viewButtonRef, parseStart } = props;
  const { onParse, onTable, onUse, onDiscardTranscription } = props;
  const { onBind, onUndo, onToLong, onLoadData, onDataViewShown } = props;
  const { convertLine, converting, converted, dragOver, dropReady, fileNotice } = intake;
  const { pendingFile, convertStart, boxRef, parseButtonRef, fileInputRef } = intake;
  const { replaceButtonRef, handleTextChange, fillFromFile, handleSheet, handleKeep } = intake;
  const { handleDragEnter, handleDragOver, handleDragLeave, handleDrop } = intake;
  const { handlePaste, handleChosen } = intake;

  const bytes = utf8Bytes(text);
  const over = bytes > MAX_DATASET_BYTES;
  const transcription = state.transcription;
  const dataset = state.dataset;
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
      {/* One short label (since 2026-11-02, owner: less text); the how-to behind its ⓘ, the
          other sources (example data, a curve) in the box's placeholder. The button sits beside
          the label, not in it, so it never joins the box's accessible name. */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.75 }}>
        <Box component="label" htmlFor="agent-data" sx={labelSx}>
          # your data
        </Box>
        <InfoPopover
          label="How the data card works"
          heading="# how it works"
          lines={DATA_HOWTO}
          testId="data-howto"
        />
      </Box>
      {/* The drop zone: the box itself. A file dragged over it tints it with the brand
          colour, or with the warning colour while a step runs and the drop would be refused. */}
      <Box
        data-testid="data-drop-zone"
        data-drag={dragOver ? (dropReady ? 'ready' : 'busy') : undefined}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        sx={{ position: 'relative' }}
      >
        <Box
          component="textarea"
          id="agent-data"
          value={text}
          rows={8}
          spellCheck={false}
          placeholder={DATA_PLACEHOLDER}
          aria-busy={converting || state.parsing || undefined}
          ref={boxRef}
          onChange={handleTextChange}
          onPaste={handlePaste}
          sx={{
            ...nativeControlSx,
            display: 'block',
            width: '100%',
            boxSizing: 'border-box',
            resize: 'vertical',
            fontSize: smallText,
            lineHeight: 1.5,
            whiteSpace: 'pre',
            overflowX: 'auto',
            // A table keeps its lines; the placeholder's lines wrap at phone width.
            '&::placeholder': { whiteSpace: 'pre-wrap' },
            ...(dragOver && {
              borderColor: dropReady ? colors.primary : colors.warning,
              borderStyle: 'dashed',
              outline: `1px dashed ${dropReady ? colors.primary : colors.warning}`,
              bgcolor: `color-mix(in srgb, ${dropReady ? colors.primary : colors.warning} 10%, var(--bg-elevated))`,
            }),
          }}
        />
        {dragOver && (
          <Box
            aria-hidden
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 2,
              textAlign: 'center',
              pointerEvents: 'none',
            }}
          >
            {/* On its own surface: over a filled box the line would sit on the text. */}
            <Box
              component="span"
              sx={{
                ...labelSx,
                fontSize: fontSize.md,
                color: 'var(--ink)',
                bgcolor: 'var(--bg-elevated)',
                border: `1px dashed ${dropReady ? colors.primary : colors.warning}`,
                borderRadius: '4px',
                px: 1.5,
                py: 0.75,
              }}
            >
              {dropReady
                ? 'drop the file to read it into the box'
                : converting
                  ? 'a file is still being read: drop the next one when it is done'
                  : locked && !working
                    ? 'all libraries are plotting this data: close the panel first'
                    : 'a step is still running: drop the file when it is done'}
            </Box>
          </Box>
        )}
        {/* A file read on the server or a parse takes seconds: the box says so while it waits. */}
        {(converting || state.parsing) && (
          <BoxWorking
            line={convertLine ?? 'parsing your data'}
            since={converting ? convertStart.current : parseStart.current}
            hidden={dragOver}
          />
        )}
      </Box>
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
          mt: 1,
        }}
      >
        <Box
          component="span"
          data-testid="data-counter"
          aria-live="polite"
          sx={{ ...labelSx, color: over ? colors.error : 'var(--ink-muted)' }}
        >
          {formatKb(bytes)} / 1 MB
        </Box>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 'auto' }}>
          {/* The keyboard's and the phone's way in: iOS has no drag and drop into a page. */}
          <Box
            component="button"
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={!ready || busy || converting}
            aria-label="Open a data file"
            sx={actionButtonSx}
          >
            .open()
          </Box>
          <Box
            component="input"
            type="file"
            ref={fileInputRef}
            accept={FILE_ACCEPT}
            onChange={handleChosen}
            tabIndex={-1}
            aria-hidden
            data-testid="data-file-input"
            sx={{ display: 'none' }}
          />
          <Box
            component="button"
            type="button"
            ref={parseButtonRef}
            onClick={onParse}
            disabled={!ready || !text.trim() || over || busy || converting || !!transcription}
            aria-describedby={transcription || state.parsing ? 'agent-parse-hint' : undefined}
            sx={ghostButtonSx}
          >
            {state.parsing ? '.parse() …' : '.parse()'}
          </Box>
        </Box>
      </Box>
      {/* Stays mounted, so a screen reader hears what a file brought in. */}
      <Box
        data-testid="file-status"
        aria-live="polite"
        sx={{
          ...labelSx,
          color: 'var(--ink-soft)',
          overflowWrap: 'anywhere',
          mt: fileNotice?.tone === 'ok' ? 0.75 : 0,
        }}
      >
        {fileNotice?.tone === 'ok' ? `# ${fileNotice.text}` : ''}
      </Box>
      {fileNotice?.tone === 'error' && (
        <Box
          role="alert"
          data-testid="file-error"
          sx={{ ...bodyTextSx, color: colors.error, mt: 0.75, overflowWrap: 'anywhere' }}
        >
          {fileNotice.text}
        </Box>
      )}
      {/* The other sheets of the workbook in the box (or arrays of an .npz): a choice reads the
          same file again on the server. Only the visible sheets are named, at most ten. */}
      {converted && converted.sheets.length > 1 && (
        <Box
          data-testid="file-sheets"
          sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}
        >
          <Box component="label" htmlFor="agent-file-sheet" sx={labelSx}>
            # {converted.kind === 'npz' ? 'array' : 'sheet'}
            {converted.sheetCount > converted.sheets.length
              ? ` (first ${converted.sheets.length} of ${converted.sheetCount})`
              : ` (${converted.sheets.length})`}
          </Box>
          <Box
            component="select"
            id="agent-file-sheet"
            value={converted.sheet ?? ''}
            disabled={!dropReady}
            onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
              handleSheet(event.target.value)
            }
            sx={{ ...nativeControlSx, maxWidth: '100%', minWidth: 0 }}
          >
            {converted.sheets.map(name => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </Box>
        </Box>
      )}
      {pendingFile && (
        <Box
          role="group"
          aria-labelledby="agent-file-replace-line"
          data-testid="file-replace"
          sx={{
            mt: 1,
            borderLeft: `3px solid ${colors.warning}`,
            pl: 1.5,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            columnGap: 1,
            rowGap: 0.5,
          }}
        >
          <Box
            id="agent-file-replace-line"
            sx={{ ...labelSx, color: 'var(--ink)', flex: '1 1 220px', overflowWrap: 'anywhere' }}
          >
            replace the text in the box with &quot;{pendingFile.source}&quot; (
            {countOf(pendingFile.lines, 'line')})?
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Box
              component="button"
              type="button"
              ref={replaceButtonRef}
              onClick={() => fillFromFile(pendingFile, 'replaced')}
              // Not while a parse of the box's text runs: its answer (a table to decide on)
              // would arrive after the swap and be stored under this file's name.
              disabled={!ready || busy}
              sx={ghostButtonSx}
            >
              .replace()
            </Box>
            <Box component="button" type="button" onClick={handleKeep} sx={actionButtonSx}>
              .keep()
            </Box>
          </Box>
        </Box>
      )}
      {/* A parse clears a pending table, so the two lines never show together. The
          parse's motion is the loader over the box; this line only says it. */}
      {(transcription || state.parsing) && (
        <Box
          id="agent-parse-hint"
          data-testid="parse-hint"
          sx={{
            ...labelSx,
            mt: 0.75,
            textAlign: 'right',
            color: state.parsing ? 'var(--ink-soft)' : 'var(--ink-muted)',
          }}
        >
          {state.parsing
            ? '# parsing your data'
            : 'decide on the table below first: .use() or .discard()'}
        </Box>
      )}

      {state.datasetError && (
        <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: 1.5 }}>
          {describeDataFailure(
            state.datasetError.code,
            state.datasetError.ref,
            state.datasetError.cause
          )}
        </Box>
      )}

      {transcription && (
        <TranscriptionCard
          transcription={transcription}
          canUse={ready && !busy}
          onUse={onUse}
          onDiscard={onDiscardTranscription}
        />
      )}

      {dataset && (
        <Box sx={{ mt: 2.5, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
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
                disabled={!ready || busy || converting}
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
            confirmed={confirmed}
            suggestion={suggestion}
            onBind={onBind}
          />

          {/* No foot: `.confirm()` and the line that says what it waits for sit at the
              composer's end in step 1, and `.create_plot()` there in step 2. */}
        </Box>
      )}
    </>
  );
}
