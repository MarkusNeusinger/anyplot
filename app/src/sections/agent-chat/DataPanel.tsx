/**
 * The data panel of the agent chat: paste data (200 KB cap with a live
 * counter), parse it on the server, check the 20-row preview and the parser's
 * warnings, and bind each spec role to a column (the server's defaults come
 * preselected).
 *
 * Two steps, data first. Step 1 ends with `.confirm()`, once every required
 * role has a column: the user says the preview and the bindings are right.
 * Only then does the panel show the data's shape and `.create_plot()` (step
 * 2). A new parse or a binding change takes the panel back to step 1, because
 * a plot of the wrong data is wrong however good it looks.
 *
 * Every role of the spec gets a column choice (`bindingRows` in `bindings.ts`):
 * a single role one dropdown, a variadic family one per member plus one for
 * the next member. Required roles carry a `*`; the kinds a role accepts sit
 * under its name and the spec's description is its tooltip.
 *
 * Text that is not a table comes back as a table a model read from it, which
 * the server has not stored. A card above the preview shows it with the
 * model's note, and `.parse()` waits until the user decides: `.use()` puts the
 * table's CSV into the text box and stores it through the normal parse,
 * `.discard()` drops it and keeps the pasted text for another try.
 *
 * The assistant can change the stored data in step 1 when the user asks it to
 * in the chat. The preview then shows the new version, and a `# changed` block
 * above it lists what changed, one line per operation, with `.undo()`, which
 * restores the version before. After an undo the block says which version is
 * back and keeps `.undo()` while an earlier one exists. Either way the panel is
 * back at step 1. A new parse clears the block.
 *
 * A formula is data the assistant computes, not text to paste. Asked for in
 * the chat, its table arrives like a change: the next version of the data, or
 * version 1 when there was none, whose `# changed` block names the generated
 * rows and offers no `.undo()`. Pasted into the text box, the server refuses it
 * (`422 formula`), and a line under the box offers `.send()`, which sends the
 * text to the chat as a turn and empties the box.
 */

import { useState } from 'react';

import Box from '@mui/material/Box';

import {
  type AgentSessionState,
  type DataChange,
  type Failure,
  sessionBusy,
  type TranscriptionState,
} from 'src/hooks/useAgentSession';
import { type ColumnProfile, MAX_DATASET_BYTES, utf8Bytes } from 'src/lib/agent';
import { bindingRows, kindsHint } from 'src/sections/agent-chat/bindings';
import { describeDataFailure } from 'src/sections/agent-chat/messages';
import {
  actionButtonSx,
  bodyTextSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  panelSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { colors, fontSize, typography } from 'src/theme';

function formatKb(bytes: number): string {
  return `${(bytes / 1024).toFixed(bytes < 10 * 1024 ? 1 : 0)} KB`;
}

function countOf(count: number, noun: string): string {
  return `${count.toLocaleString('en-US')} ${noun}${count === 1 ? '' : 's'}`;
}

/** The first rows of a table under its column names and types. */
function PreviewTable({ columns, rows }: { columns: ColumnProfile[]; rows: string[][] }) {
  return (
    <Box
      sx={{
        overflowX: 'auto',
        maxHeight: 320,
        overflowY: 'auto',
        border: '1px solid var(--rule)',
        borderRadius: 1,
      }}
    >
      <Box
        component="table"
        sx={{
          borderCollapse: 'collapse',
          fontFamily: typography.mono,
          fontSize: smallText,
          color: 'var(--ink)',
          width: '100%',
          '& th, & td': {
            px: 1,
            py: 0.5,
            textAlign: 'left',
            whiteSpace: 'nowrap',
            borderBottom: '1px solid var(--rule)',
          },
          '& th': {
            position: 'sticky',
            top: 0,
            bgcolor: 'var(--bg-elevated)',
            fontWeight: 600,
          },
        }}
      >
        <thead>
          <tr>
            {columns.map(column => (
              <th key={column.name} scope="col">
                {column.name}
                <Box
                  component="span"
                  sx={{ display: 'block', color: 'var(--ink-muted)', fontWeight: 400 }}
                >
                  {column.dtype}
                </Box>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </Box>
    </Box>
  );
}

/** The parser's warnings, if any. */
function WarningList({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) return null;
  return (
    <Box sx={{ borderLeft: `3px solid ${colors.warning}`, pl: 1.5 }}>
      <Box sx={labelSx}># warnings</Box>
      <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2.5, ...bodyTextSx, fontSize: smallText }}>
        {warnings.map((warning, index) => (
          <li key={index}>{warning}</li>
        ))}
      </Box>
    </Box>
  );
}

interface TranscriptionCardProps {
  transcription: TranscriptionState;
  canUse: boolean;
  onUse: () => void;
  onDiscard: () => void;
}

/** A table a model read from free text, for the user to check before it is stored. */
function TranscriptionCard({ transcription, canUse, onUse, onDiscard }: TranscriptionCardProps) {
  const { columns, rows } = transcription.profile;
  return (
    <Box
      component="section"
      aria-labelledby="agent-transcription-title"
      data-testid="transcription-card"
      sx={{
        mt: 2.5,
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        minWidth: 0,
        border: '1px solid var(--rule)',
        borderLeft: `3px solid ${colors.primary}`,
        borderRadius: 1,
        p: 1.5,
      }}
    >
      <Box>
        <Box id="agent-transcription-title" sx={{ ...labelSx, color: 'var(--ink)' }}>
          # read from your text — {countOf(rows, 'row')}, {countOf(columns.length, 'column')}
        </Box>
        <Box sx={{ ...bodyTextSx, fontSize: smallText, color: 'var(--ink-soft)', mt: 0.5 }}>
          this was not a table, so a model read it into one. check that every value sits in the
          right column, then use it or discard it.
        </Box>
      </Box>

      {transcription.note && (
        <Box>
          <Box sx={labelSx}># note from the model</Box>
          <Box sx={{ ...bodyTextSx, fontSize: smallText, mt: 0.5 }}>{transcription.note}</Box>
        </Box>
      )}

      <WarningList warnings={transcription.warnings} />

      <PreviewTable columns={columns} rows={transcription.preview} />

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Box component="button" type="button" onClick={onUse} disabled={!canUse} sx={ghostButtonSx}>
          .use()
        </Box>
        <Box component="button" type="button" onClick={onDiscard} sx={actionButtonSx}>
          .discard()
        </Box>
      </Box>
    </Box>
  );
}

interface ChangeBlockProps {
  change: DataChange;
  canUndo: boolean;
  undoBusy: boolean;
  error: Failure | null;
  onUndo: () => void;
}

/**
 * What the assistant last changed in the data, or the undo of it, with
 * `.undo()`. A first dataset the assistant generated (version 1) has nothing
 * before it, so its block offers no `.undo()`.
 */
function ChangeBlock({ change, canUndo, undoBusy, error, onUndo }: ChangeBlockProps) {
  const first = change.kind === 'changed' && change.version <= 1;
  return (
    <Box
      component="section"
      aria-labelledby="agent-change-title"
      data-testid="data-change"
      sx={{
        borderLeft: `3px solid ${colors.primary}`,
        pl: 1.5,
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
        minWidth: 0,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          columnGap: 1,
          rowGap: 0.5,
        }}
      >
        <Box id="agent-change-title" sx={{ ...labelSx, color: 'var(--ink)' }}>
          {change.kind === 'changed'
            ? `# changed · version ${change.version}`
            : `# undone · back to version ${change.version}`}
        </Box>
        {!first && (
          <Box
            component="button"
            type="button"
            onClick={onUndo}
            disabled={!canUndo}
            aria-describedby="agent-change-title"
            sx={ghostButtonSx}
          >
            {undoBusy ? '.undo() …' : '.undo()'}
          </Box>
        )}
      </Box>
      {change.kind === 'changed' && change.changes.length > 0 && (
        <Box
          component="ul"
          sx={{
            m: 0,
            pl: 2.5,
            fontFamily: typography.mono,
            fontSize: smallText,
            color: 'var(--ink)',
            lineHeight: 1.6,
            overflowWrap: 'anywhere',
          }}
        >
          {change.changes.map((line, index) => (
            <li key={index}>{line}</li>
          ))}
        </Box>
      )}
      {error && (
        <Box role="alert" sx={{ ...bodyTextSx, color: colors.error }}>
          {describeDataFailure(error.code, error.ref)}
        </Box>
      )}
    </Box>
  );
}

/** The step's one action under the bindings: `.confirm()`, then `.create_plot()`. */
const stepButtonSx = {
  ...actionButtonSx,
  border: '1px solid var(--rule)',
  px: 2,
  py: 1,
  width: { xs: '100%', sm: 'auto' },
} as const;

interface DataPanelProps {
  state: AgentSessionState;
  onParse: (text: string) => void;
  onConfirmTranscription: () => void;
  onDiscardTranscription: () => void;
  /** `.send()` next to a refused formula: the refused text goes to the chat as a turn. */
  onSendFormula: () => void;
  onBind: (role: string, column: string | null) => void;
  onConfirmData: () => void;
  onUndo: () => void;
  onCreatePlot: () => void;
}

export function DataPanel({
  state,
  onParse,
  onConfirmTranscription,
  onDiscardTranscription,
  onSendFormula,
  onBind,
  onConfirmData,
  onUndo,
  onCreatePlot,
}: DataPanelProps) {
  const [text, setText] = useState('');
  const bytes = utf8Bytes(text);
  const over = bytes > MAX_DATASET_BYTES;
  const ready = state.phase === 'ready' && !!state.sessionId;
  // A turn, a theme render, a parse, a binding change or a confirmation in
  // flight: the server would refuse or race a second one.
  const busy = sessionBusy(state);
  const transcription = state.transcription;
  const dataset = state.dataset;
  const columns = dataset?.parsed.profile.columns ?? [];
  // A pending transcription blocks both steps: the user decides on the data first.
  const canConfirm = ready && !!dataset && state.bindingsComplete && !busy && !transcription;
  const canCreate = canConfirm && state.dataConfirmed;
  // An earlier version exists above the paste's 1, until the server says the
  // history ended (it keeps the last five versions).
  const canUndo =
    ready &&
    !busy &&
    (dataset?.parsed.version ?? 1) > 1 &&
    state.undoError?.code !== 'nothing_to_undo';
  const rows = bindingRows(state.roles, state.bindings, columns.length);

  // `.use()`: the text box shows the CSV that gets stored, so the user can
  // read it and edit it for a later `.parse()`.
  const handleUse = () => {
    if (!transcription) return;
    setText(transcription.text);
    onConfirmTranscription();
  };

  // `.send()`: the formula moves to the chat as a turn, so the box is free for a table.
  const handleSendFormula = () => {
    setText('');
    onSendFormula();
  };

  return (
    <Box component="section" aria-label="Your data" sx={panelSx}>
      <Box
        component="label"
        htmlFor="agent-data"
        sx={{ ...labelSx, display: 'block', mb: dataset ? 0.75 : 0.25 }}
      >
        # your data — paste CSV, TSV, semicolon CSV, JSON or plain text
      </Box>
      {/* Until there is data, the other source: a curve the assistant computes. */}
      {!dataset && (
        <Box id="agent-data-hint" sx={{ ...labelSx, mb: 0.75 }}>
          or ask for a curve in the chat: y = sin(x), x from{' '}
          <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
            -pi
          </Box>{' '}
          to pi
        </Box>
      )}
      <Box
        component="textarea"
        id="agent-data"
        value={text}
        rows={8}
        spellCheck={false}
        aria-describedby={dataset ? undefined : 'agent-data-hint'}
        placeholder={'month,revenue\n2026-01,120\n2026-02,135'}
        onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => setText(event.target.value)}
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
        }}
      />
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
          {formatKb(bytes)} / 200 KB
        </Box>
        <Box
          component="button"
          type="button"
          onClick={() => onParse(text)}
          disabled={!ready || !text.trim() || over || busy || !!transcription}
          aria-describedby={transcription ? 'agent-parse-hint' : undefined}
          sx={ghostButtonSx}
        >
          {state.parsing ? '.parse() …' : '.parse()'}
        </Box>
      </Box>
      {transcription && (
        <Box id="agent-parse-hint" sx={{ ...labelSx, mt: 0.75, textAlign: 'right' }}>
          decide on the table below first: .use() or .discard()
        </Box>
      )}

      {/* The offer belongs to the text it was made for: an edit of the box takes it away, so
          `.send()` never sends an older text than the one shown. */}
      {state.formula !== null && text === state.formula && (
        <Box
          data-testid="formula-offer"
          sx={{
            mt: 1.5,
            borderLeft: `3px solid ${colors.primary}`,
            pl: 1.5,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            columnGap: 1,
            rowGap: 0.75,
          }}
        >
          <Box
            id="agent-formula-line"
            role="status"
            sx={{ ...labelSx, color: 'var(--ink)', flex: '1 1 220px', lineHeight: 1.6 }}
          >
            looks like a formula: send it to the chat? the assistant computes the table from it.
          </Box>
          <Box
            component="button"
            type="button"
            onClick={handleSendFormula}
            disabled={!ready || busy}
            aria-describedby="agent-formula-line"
            sx={ghostButtonSx}
          >
            .send()
          </Box>
        </Box>
      )}

      {state.datasetError && (
        <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: 1.5 }}>
          {describeDataFailure(state.datasetError.code, state.datasetError.ref)}
        </Box>
      )}

      {transcription && (
        <TranscriptionCard
          transcription={transcription}
          canUse={ready && !busy}
          onUse={handleUse}
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

          <Box sx={{ ...labelSx, color: 'var(--ink-soft)' }}>
            {dataset.parsed.profile.rows.toLocaleString('en-US')} rows · {columns.length} columns ·{' '}
            {dataset.parsed.profile.source_format}
          </Box>

          <WarningList warnings={dataset.parsed.warnings} />

          <Box sx={{ minWidth: 0 }}>
            <Box sx={{ ...labelSx, mb: 0.5 }}>
              # preview — first {dataset.parsed.preview.length} rows
            </Box>
            <PreviewTable columns={columns} rows={dataset.parsed.preview} />
          </Box>

          <Box>
            <Box sx={{ ...labelSx, mb: 0.75 }}># bindings — which column plays which role</Box>
            {rows.length === 0 && (
              <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
                {state.bindingsBusy ? 'checking roles…' : 'this plot names no data roles'}
              </Box>
            )}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'minmax(0, max-content) minmax(0, 1fr)',
                alignItems: 'center',
                columnGap: 1.5,
                rowGap: 1,
              }}
            >
              {rows.map(row => {
                const missing = row.first && state.missingRoles.includes(row.role.name);
                const id = `agent-role-${row.name}`;
                return (
                  <Box key={row.name} sx={{ display: 'contents' }}>
                    <Box
                      component="label"
                      htmlFor={id}
                      title={row.role.description || undefined}
                      sx={{
                        fontFamily: typography.mono,
                        fontSize: fontSize.md,
                        color: missing
                          ? colors.error
                          : row.next
                            ? 'var(--ink-muted)'
                            : 'var(--ink)',
                        overflowWrap: 'anywhere',
                        // The kinds line wraps instead of squeezing the dropdowns.
                        maxWidth: { xs: '13ch', sm: '16ch' },
                      }}
                    >
                      {row.name}
                      {row.first && row.role.required ? ' *' : ''}
                      {row.first && (
                        <Box
                          component="span"
                          sx={{ display: 'block', ...labelSx, fontSize: smallText }}
                        >
                          {kindsHint(row.role)}
                        </Box>
                      )}
                    </Box>
                    <Box
                      component="select"
                      id={id}
                      value={state.bindings[row.name] ?? ''}
                      disabled={!ready || busy}
                      onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                        onBind(row.name, event.target.value || null)
                      }
                      sx={{ ...nativeControlSx, width: '100%' }}
                    >
                      <option value="">{row.next ? '— add a column —' : '— none —'}</option>
                      {columns.map(column => (
                        <option key={column.name} value={column.name}>
                          {column.name} ({column.dtype})
                        </option>
                      ))}
                    </Box>
                  </Box>
                );
              })}
            </Box>
            {state.missingRoles.length > 0 && (
              <Box sx={{ ...labelSx, mt: 1 }}>
                * required: pick a column for {state.missingRoles.join(', ')}
              </Box>
            )}
            {state.bindingsError && (
              <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: 1 }}>
                {describeDataFailure(state.bindingsError.code, state.bindingsError.ref)}
                {state.bindingsError.errors && state.bindingsError.errors.length > 0 && (
                  <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2.5, fontSize: smallText }}>
                    {state.bindingsError.errors.map((line, index) => (
                      <li key={index}>{line}</li>
                    ))}
                  </Box>
                )}
              </Box>
            )}
          </Box>

          <Box>
            {/* One line that stays mounted, so a screen reader hears the step change. */}
            <Box
              id="agent-step-line"
              data-testid="data-step"
              aria-live="polite"
              // A notch above the `#` labels: this line says what to do next.
              sx={{ ...labelSx, mb: 0.75, color: 'var(--ink-soft)' }}
            >
              {state.dataConfirmed ? (
                <>
                  <Box component="span" aria-hidden sx={{ color: colors.success, mr: 0.75 }}>
                    ✓
                  </Box>
                  data fits · {countOf(dataset.parsed.profile.rows, 'row')} ·{' '}
                  {countOf(columns.length, 'column')}
                </>
              ) : (
                '# step 1 — check the preview and the bindings, then confirm'
              )}
            </Box>
            {state.dataConfirmed ? (
              <Box
                component="button"
                type="button"
                onClick={onCreatePlot}
                disabled={!canCreate}
                aria-describedby="agent-step-line"
                sx={stepButtonSx}
              >
                .create_plot()
              </Box>
            ) : (
              <Box
                component="button"
                type="button"
                onClick={onConfirmData}
                disabled={!canConfirm}
                aria-describedby="agent-step-line"
                sx={stepButtonSx}
              >
                {state.confirmBusy ? '.confirm() …' : '.confirm()'}
              </Box>
            )}
            {state.confirmError && (
              <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: 1 }}>
                {describeDataFailure(state.confirmError.code, state.confirmError.ref)}
              </Box>
            )}
          </Box>
        </Box>
      )}
    </Box>
  );
}
