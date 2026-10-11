/**
 * The data panel of the agent chat: paste data (200 KB cap with a live
 * counter), parse it on the server, check the 20-row preview and the parser's
 * warnings, and bind each spec role to a column (the server's defaults come
 * preselected). `.create_plot()` runs the pipeline once every required role
 * has a column.
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
 */

import { useState } from 'react';

import Box from '@mui/material/Box';

import {
  type AgentSessionState,
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

interface DataPanelProps {
  state: AgentSessionState;
  onParse: (text: string) => void;
  onConfirmTranscription: () => void;
  onDiscardTranscription: () => void;
  onBind: (role: string, column: string | null) => void;
  onCreatePlot: () => void;
}

export function DataPanel({
  state,
  onParse,
  onConfirmTranscription,
  onDiscardTranscription,
  onBind,
  onCreatePlot,
}: DataPanelProps) {
  const [text, setText] = useState('');
  const bytes = utf8Bytes(text);
  const over = bytes > MAX_DATASET_BYTES;
  const ready = state.phase === 'ready' && !!state.sessionId;
  // A turn, a theme render, a parse or a binding change in flight: the server
  // would refuse or race a second one.
  const busy = sessionBusy(state);
  const transcription = state.transcription;
  const dataset = state.dataset;
  const columns = dataset?.parsed.profile.columns ?? [];
  // A pending transcription blocks the plot too: the user decides on the data first.
  const canCreate = ready && !!dataset && state.bindingsComplete && !busy && !transcription;
  const rows = bindingRows(state.roles, state.bindings, columns.length);

  // `.use()`: the text box shows the CSV that gets stored, so the user can
  // read it and edit it for a later `.parse()`.
  const handleUse = () => {
    if (!transcription) return;
    setText(transcription.text);
    onConfirmTranscription();
  };

  return (
    <Box component="section" aria-label="Your data" sx={panelSx}>
      <Box component="label" htmlFor="agent-data" sx={{ ...labelSx, display: 'block', mb: 0.75 }}>
        # your data — paste CSV, TSV, semicolon CSV, JSON or plain text
      </Box>
      <Box
        component="textarea"
        id="agent-data"
        value={text}
        rows={8}
        spellCheck={false}
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
            <Box
              component="button"
              type="button"
              onClick={onCreatePlot}
              disabled={!canCreate}
              sx={{
                ...actionButtonSx,
                border: '1px solid var(--rule)',
                px: 2,
                py: 1,
                width: { xs: '100%', sm: 'auto' },
              }}
            >
              .create_plot()
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}
