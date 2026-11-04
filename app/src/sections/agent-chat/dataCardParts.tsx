/**
 * Presentational building blocks for the agent chat's data card (`DataCard.tsx`)
 * and pinned summary (`PinnedData.tsx`): the 20-row preview table, the lazy
 * full-table view fallback, the parser warnings, notes and code blocks, the
 * free-text transcription card, the assistant change/undo block, the wide-table
 * offer, and the shared text formatters.
 */

import { useState } from 'react';

import Box from '@mui/material/Box';

import type {
  AgentSessionState,
  DataChange,
  Failure,
  FormulaKind,
  TranscriptionState,
} from 'src/hooks/useAgentSession';
import { type ColumnProfile, type LongSuggestion, MAX_MESSAGE_CHARS } from 'src/lib/agent';
import { CellText } from 'src/sections/agent-chat/CellText';
import type { DataViewProps } from 'src/sections/agent-chat/DataView';
import { lazyOrFallback } from 'src/sections/agent-chat/lazyOrFallback';
import { describeDataFailure } from 'src/sections/agent-chat/messages';
import {
  actionButtonSx,
  bodyTextSx,
  ghostButtonSx,
  labelSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

/** In place of the full view when its chunk does not load (`lazyOrFallback`): a line in the card. */
export function DataViewUnavailable({ onClose }: Pick<DataViewProps, 'onClose'>) {
  return (
    <Box
      role="alert"
      sx={{ ...bodyTextSx, fontSize: smallText, color: colors.error, mt: 0.5, display: 'flex' }}
    >
      <Box sx={{ flex: '1 1 auto' }}>
        the table view did not load; reload the page to open it (your session ends with the page)
      </Box>
      <Box component="button" type="button" onClick={onClose} sx={actionButtonSx}>
        .close()
      </Box>
    </Box>
  );
}

// The full view's chunk holds the Data Grid: it loads when the user first opens the view (or points at the button).
const loadDataView = () => import('src/sections/agent-chat/DataView');
export const DataView = lazyOrFallback(loadDataView, DataViewUnavailable);
// A preload that fails stays quiet: opening the view shows the line above.
export const preloadDataView = () => void loadDataView().catch(() => undefined);

export function formatKb(bytes: number): string {
  return `${(bytes / 1024).toFixed(bytes < 10 * 1024 ? 1 : 0)} KB`;
}

export function countOf(count: number, noun: string): string {
  return `${count.toLocaleString('en-US')} ${noun}${count === 1 ? '' : 's'}`;
}

/** The first rows of a table under its column names and types. */
export function PreviewTable({ columns, rows }: { columns: ColumnProfile[]; rows: string[][] }) {
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
                <td key={cellIndex}>
                  <CellText cell={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </Box>
    </Box>
  );
}

/** The parser's warnings, if any. */
export function WarningList({ warnings }: { warnings: string[] }) {
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

/**
 * The notes the user pasted above or below the table, which the server kept
 * and the assistant reads with the data: collapsed to one line with `.show()`,
 * so the user can check what the assistant got without the card growing.
 */
export function NotesBlock({ lines }: { lines: string[] }) {
  const [open, setOpen] = useState(false);
  if (lines.length === 0) return null;
  return (
    <Box
      component="section"
      aria-labelledby="agent-notes-title"
      data-testid="data-notes"
      sx={{ borderLeft: '3px solid var(--rule)', pl: 1.5, minWidth: 0 }}
    >
      <Box
        sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', columnGap: 1, rowGap: 0.5 }}
      >
        <Box id="agent-notes-title" sx={labelSx}>
          # notes sent to the assistant · {lines.length} {lines.length === 1 ? 'line' : 'lines'}
        </Box>
        <Box
          component="button"
          type="button"
          onClick={() => setOpen(value => !value)}
          aria-expanded={open}
          aria-controls="agent-notes-list"
          aria-describedby="agent-notes-title"
          sx={actionButtonSx}
        >
          {open ? '.hide()' : '.show()'}
        </Box>
      </Box>
      {open && (
        <Box
          component="ul"
          id="agent-notes-list"
          sx={{
            m: 0,
            mt: 0.5,
            pl: 2.5,
            ...bodyTextSx,
            fontSize: smallText,
            color: 'var(--ink-soft)',
            overflowWrap: 'anywhere',
          }}
        >
          {lines.map((line, index) => (
            <li key={index}>{line}</li>
          ))}
        </Box>
      )}
    </Box>
  );
}

/** The line under the box for text the server refused as a formula or as code, which the chat takes instead. */
export function offerLine(kind: FormulaKind, tooLong: boolean): string {
  if (kind === 'formula') {
    return 'looks like a formula: send it to the chat? the assistant computes the table from it.';
  }
  if (tooLong) {
    return `looks like code that makes data: shorten it to ${MAX_MESSAGE_CHARS.toLocaleString('en-US')} characters, keeping only the part that computes the data, and the chat runs it.`;
  }
  return 'looks like code that makes data: send it to the chat? the assistant runs it in a sandbox and shows you the table.';
}

/**
 * The Python that computed this data version (the assistant's `run_data_code`),
 * collapsed behind `.show()`: the user can read what ran on their behalf, the
 * same way the notes block shows what the assistant reads.
 */
export function CodeBlock({ code }: { code: string | undefined }) {
  const [open, setOpen] = useState(false);
  if (!code) return null;
  const lines = code.split('\n').filter(line => line.trim()).length;
  return (
    <Box
      component="section"
      aria-labelledby="agent-code-title"
      data-testid="data-code"
      sx={{ borderLeft: '3px solid var(--rule)', pl: 1.5, minWidth: 0 }}
    >
      <Box
        sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', columnGap: 1, rowGap: 0.5 }}
      >
        <Box id="agent-code-title" sx={labelSx}>
          # code that made this data · {lines} {lines === 1 ? 'line' : 'lines'} of python
        </Box>
        <Box
          component="button"
          type="button"
          onClick={() => setOpen(value => !value)}
          aria-expanded={open}
          aria-controls="agent-code-text"
          aria-describedby="agent-code-title"
          sx={actionButtonSx}
        >
          {open ? '.hide()' : '.show()'}
        </Box>
      </Box>
      {open && (
        <Box
          component="pre"
          id="agent-code-text"
          sx={{
            m: 0,
            mt: 0.5,
            fontFamily: typography.mono,
            fontSize: smallText,
            lineHeight: 1.5,
            color: 'var(--ink-soft)',
            whiteSpace: 'pre',
            overflowX: 'auto',
            maxHeight: 320,
            overflowY: 'auto',
          }}
        >
          {code}
        </Box>
      )}
    </Box>
  );
}

interface TranscriptionCardProps {
  transcription: TranscriptionState;
  canUse: boolean;
  onUse: () => void;
  onDiscard: () => void;
  /** The `.use()` button, for the page to bring into view and focus. */
  decisionRef?: React.Ref<HTMLButtonElement>;
}

/** A table a model read from free text, for the user to check before it is stored. */
export function TranscriptionCard({
  transcription,
  canUse,
  onUse,
  onDiscard,
  decisionRef,
}: TranscriptionCardProps) {
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
        <Box
          component="button"
          type="button"
          ref={decisionRef}
          onClick={onUse}
          disabled={!canUse}
          sx={ghostButtonSx}
        >
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
export function ChangeBlock({ change, canUndo, undoBusy, error, onUndo }: ChangeBlockProps) {
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

/** Step 1's one action under the bindings: `.confirm()`. */
export const stepButtonSx = {
  ...actionButtonSx,
  border: '1px solid var(--rule)',
  px: 2,
  py: 1,
  width: { xs: '100%', sm: 'auto' },
} as const;

/** The data's shape in one line: `2 rows · 2 columns · version 1`. */
export function dataShape(dataset: NonNullable<AgentSessionState['dataset']>): string {
  const { profile, version } = dataset.parsed;
  return `${countOf(profile.rows, 'row')} · ${countOf(profile.columns.length, 'column')} · version ${version ?? 1}`;
}

interface LongHintProps {
  suggestion: LongSuggestion;
  canApply: boolean;
  busy: boolean;
  error: Failure | null;
  onApply: () => void;
}

/**
 * The wide-table offer (`agents/anyplot/data/shape.py`): the columns hold the
 * same quantity side by side where the plot wants one category column and one
 * value column. `.to_long()` applies it on the server, without a model call;
 * `.undo()` takes it back like any data change.
 */
export function LongHint({ suggestion, canApply, busy, error, onApply }: LongHintProps) {
  const kept = suggestion.keys.length > 0 ? `, ${suggestion.keys.join(', ')} kept` : '';
  return (
    <Box
      component="section"
      aria-labelledby="agent-long-title"
      data-testid="data-long-hint"
      sx={{
        borderLeft: `3px solid ${colors.primary}`,
        pl: 1.5,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        columnGap: 1,
        rowGap: 0.5,
        minWidth: 0,
      }}
    >
      <Box sx={{ minWidth: 0, flex: '1 1 16rem' }}>
        <Box id="agent-long-title" sx={{ ...labelSx, color: 'var(--ink)' }}>
          # wide table · this plot wants one {suggestion.names_to} and one {suggestion.values_to}{' '}
          column
        </Box>
        <Box
          id="agent-long-detail"
          sx={{
            ...bodyTextSx,
            fontSize: smallText,
            color: 'var(--ink-soft)',
            overflowWrap: 'anywhere',
          }}
        >
          {suggestion.columns.join(', ')} → {suggestion.names_to} and {suggestion.values_to},{' '}
          {suggestion.rows.toLocaleString('en-US')} rows{kept}
        </Box>
        {error && (
          <Box role="alert" sx={{ ...bodyTextSx, fontSize: smallText, color: colors.error }}>
            could not change the table ({error.code})
          </Box>
        )}
      </Box>
      <Box
        component="button"
        type="button"
        onClick={onApply}
        disabled={!canApply}
        aria-label="Make the table long"
        aria-describedby="agent-long-title agent-long-detail"
        sx={actionButtonSx}
      >
        {busy ? '.to_long() …' : '.to_long()'}
      </Box>
    </Box>
  );
}
