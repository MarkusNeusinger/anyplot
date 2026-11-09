/**
 * Presentational building blocks of the agent chat's data card, imported by
 * `DataCard.tsx`: the 20-row preview table, the lazy full-table view fallback,
 * the parser warnings, notes and code blocks, the free-text transcription card,
 * the assistant change/undo block, the wide-table offer, and the role bindings:
 * their one line (`BindingsLine`) and the dropdowns `.change()` opens
 * (`BindingsBlock`).
 * `DataPanel.tsx` imports only the full-view fallback, which it re-exports for
 * its tests.
 */

import { useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';

import type { DataChange, Failure, TranscriptionState } from 'src/hooks/useAgentSession';
import type { ColumnProfile, LongSuggestion } from 'src/lib/agent';
import {
  axisWord,
  bindingHint,
  type BindingRow,
  type BoundRole,
  columnLabel,
  dtypeWord,
  emptyChoice,
  fits,
  kindsHint,
  pairId,
  pairName,
  roleControlId,
} from 'src/sections/agent-chat/bindings';
import { CellText } from 'src/sections/agent-chat/CellText';
import { countOf } from 'src/sections/agent-chat/countOf';
import type { DataViewProps } from 'src/sections/agent-chat/DataView';
import { describeDataFailure } from 'src/sections/agent-chat/messages';
import {
  actionButtonSx,
  bodyTextSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  smallText,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors, fontSize, typography } from 'src/theme';

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

/**
 * The first rows of a table under its column names and types, one line each: `month · date`, in
 * the card's words for a type (`dtypeWord`), the name in ink and the type quieter.
 */
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
            fontWeight: 500,
          },
        }}
      >
        <thead>
          <tr>
            {columns.map(column => (
              <th key={column.name} scope="col">
                {column.name}
                <Box component="span" sx={{ color: 'var(--ink-muted)', fontWeight: 400 }}>
                  {` · ${dtypeWord(column.dtype)}`}
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
}

/** A table a model read from free text, for the user to check before it is stored. */
export function TranscriptionCard({
  transcription,
  canUse,
  onUse,
  onDiscard,
}: TranscriptionCardProps) {
  const { columns, rows } = transcription.profile;
  return (
    <Box
      component="section"
      aria-labelledby="agent-transcription-title"
      data-testid="transcription-card"
      sx={{
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
  /** The change made the session's first data (the server has nothing to undo after it). */
  first: boolean;
  canUndo: boolean;
  undoBusy: boolean;
  error: Failure | null;
  onUndo: () => void;
}

/**
 * What the assistant last changed in the data, or the undo of it, with
 * `.undo()`. A first dataset the assistant generated (`first`) has nothing
 * before it, so its block offers no `.undo()`.
 */
export function ChangeBlock({ change, first, canUndo, undoBusy, error, onUndo }: ChangeBlockProps) {
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
          {/* No version number: the card's label on its border names it already
              (`data v1 · back to v1`). */}
          {change.kind === 'changed' ? '# changed' : '# undone · back to the version before'}
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

interface BindingsBlockProps {
  /** The block's id, which the bindings line's `.change()` controls. */
  id: string;
  rows: BindingRow[];
  columns: ColumnProfile[];
  bindings: Record<string, string>;
  missingRoles: string[];
  bindingsBusy: boolean;
  bindingsError: Failure | null;
  parsing: boolean;
  ready: boolean;
  working: boolean;
  busy: boolean;
  suggestion: LongSuggestion | null;
  onBind: (role: string, column: string | null) => void;
  /** Escape in the block, outside a menu of its own: the block closes. */
  onEscape?: () => void;
}

/** A chip's height: a phone's touch target, smaller with a pointer. */
const CHIP_HEIGHT = { xs: 32, sm: 28 } as const;

const chipSx = {
  display: 'inline-flex',
  alignItems: 'center',
  height: CHIP_HEIGHT,
  pl: 1.25,
  border: '1px solid var(--rule)',
  borderRadius: '16px',
  bgcolor: 'var(--bg-elevated)',
  fontFamily: typography.mono,
  fontSize: fontSize.md,
  color: 'var(--ink)',
  whiteSpace: 'nowrap',
  maxWidth: '100%',
  minWidth: 0,
} as const;

const removeSx = {
  all: 'unset',
  boxSizing: 'border-box',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  flexShrink: 0,
  width: CHIP_HEIGHT,
  height: CHIP_HEIGHT,
  borderRadius: '50%',
  cursor: 'pointer',
  color: 'var(--ink-soft)',
  '&:hover:not(:disabled)': { color: colors.error },
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: -2 },
  '&:disabled': { cursor: 'default', opacity: 0.6 },
} as const;

/**
 * A variadic family's bound columns as chips, each with `×`, then `+ y ▾`, a menu of the
 * columns left, the ones the role cannot take greyed out with the reason. One row for two
 * series or eight, wrapping at a phone's width. After a change the keyboard stays in the
 * row: on the chip that took a removed one's place (or `+`), and on `+` after an addition.
 */
function FamilyChips({
  row,
  columns,
  disabled,
  listId,
  labelId,
  hintOf,
  onBind,
}: {
  row: BindingRow;
  columns: ColumnProfile[];
  disabled: boolean;
  /** The chips' list, where a click on the family's pair puts the focus (`roleControlId`). */
  listId: string;
  labelId: string;
  hintOf: (column: string) => string | null;
  onBind: (role: string, column: string | null) => void;
}) {
  const family = row.role.name;
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const addRef = useRef<HTMLButtonElement>(null);
  const removeRefs = useRef<(HTMLButtonElement | null)[]>([]);
  // The controls wait while the change is on its way; the focus follows once they answer again,
  // unless the user has moved it elsewhere meanwhile.
  const refocus = useRef<number | 'add' | null>(null);
  const count = row.members.length;
  useEffect(() => {
    const target = refocus.current;
    if (target === null || disabled) return;
    refocus.current = null;
    const active = document.activeElement;
    if (active && active !== document.body && !listRef.current?.contains(active)) return;
    const last = removeRefs.current[count - 1];
    // `+` is gone once the last column is taken: the chip that took it holds the focus then.
    // A removed chip's place goes to the chip after it; the last one's to `+`, which follows it.
    const element =
      target === 'add'
        ? (addRef.current ?? last)
        : ((target < count ? removeRefs.current[target] : null) ?? addRef.current ?? last);
    element?.focus();
  }, [disabled, count]);

  const taken = new Set(row.members.map(([, column]) => column));
  const choices = columns.filter(column => !taken.has(column.name));
  const menuId = `${labelId}-menu`;
  const buttonId = `${labelId}-add`;
  const hints = row.members.flatMap(([member, column]) => {
    const hint = hintOf(column);
    return hint ? [{ member, text: `${column}: ${hint}` }] : [];
  });
  return (
    // On a phone the chips take the card's width under the role's name: beside it they had
    // room for one chip a line, eight series made eight lines.
    <Box sx={{ minWidth: 0, gridColumn: { xs: '1 / -1', sm: 'auto' } }}>
      <Box
        component="ul"
        ref={listRef}
        id={listId}
        aria-labelledby={labelId}
        aria-describedby={hints.length ? `${labelId}-hints` : undefined}
        sx={{
          listStyle: 'none',
          m: 0,
          p: 0,
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 0.75,
        }}
      >
        {row.members.map(([member, column], index) => (
          <Box component="li" key={member} sx={chipSx}>
            {/* A long column name is cut with an ellipsis inside the card; its × names it in full. */}
            <Box
              component="span"
              title={column}
              sx={{ overflow: 'hidden', textOverflow: 'ellipsis', minWidth: 0 }}
            >
              {column}
            </Box>
            <Box
              component="button"
              type="button"
              ref={(element: HTMLButtonElement | null) => {
                removeRefs.current[index] = element;
              }}
              aria-label={`Remove ${column} from ${family}`}
              disabled={disabled}
              onClick={() => {
                refocus.current = index;
                onBind(member, null);
              }}
              sx={removeSx}
            >
              ×
            </Box>
          </Box>
        ))}
        {row.next && (
          <Box component="li">
            <Box
              component="button"
              type="button"
              ref={addRef}
              id={buttonId}
              // The visible "+ y" leads the name, so a voice command that says it finds the button.
              aria-label={`+ ${family}: add a column`}
              aria-haspopup="menu"
              aria-expanded={!!anchor}
              aria-controls={anchor ? menuId : undefined}
              disabled={disabled}
              onClick={(event: React.MouseEvent<HTMLElement>) => setAnchor(event.currentTarget)}
              sx={{ ...ghostButtonSx, height: CHIP_HEIGHT, minHeight: 0, py: 0 }}
            >
              + {family} ▾
            </Box>
            <Menu
              id={menuId}
              anchorEl={anchor}
              open={!!anchor}
              onClose={() => setAnchor(null)}
              slotProps={{ list: { 'aria-labelledby': buttonId, disabledItemsFocusable: true } }}
            >
              {/* A column the role cannot take stays listed, greyed out with the reason. */}
              {choices.map(column => (
                <MenuItem
                  key={column.name}
                  dense
                  disabled={!fits(row.role, column.dtype)}
                  onClick={() => {
                    setAnchor(null);
                    refocus.current = 'add';
                    if (row.next) onBind(row.next, column.name);
                  }}
                  sx={{ fontFamily: typography.mono, fontSize: fontSize.md, minHeight: 32 }}
                >
                  {columnLabel(row.role, column)}
                </MenuItem>
              ))}
            </Menu>
          </Box>
        )}
      </Box>
      {hints.length > 0 && (
        <Box id={`${labelId}-hints`}>
          {hints.map(hint => (
            <Box
              key={hint.member}
              data-testid="sign-hint"
              sx={{ ...labelSx, fontSize: smallText, color: colors.warning, mt: 0.25 }}
            >
              {hint.text}
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}

interface BindingsLineProps {
  roles: BoundRole[];
  /** Whether the spec names roles at all; without, the line says so, as the dropdowns would. */
  hasRoles: boolean;
  /** The binding set is on its way to the server. */
  checking: boolean;
  /** At the line's end: `.change()` from `sm` up; at phone width it stands on the action line. */
  toggle?: React.ReactNode;
  /**
   * A click on a pair: the dropdowns open on that role's control. Absent while the dropdowns would
   * not answer (a step in flight, the fan-out's panel open), and the pairs are words then.
   */
  onRole?: (name: string) => void;
}

/**
 * A pair of the bindings line that a click changes: the line's own words with a dotted underline,
 * green on hover, the site's focus ring. A 32 px target at phone width, as the chapter line's
 * controls: each row of a line that wraps grows to hold it, so the targets of two rows meet and
 * never overlap. 24 px from `sm` up, where its negative margin keeps the line's height. The padding
 * and its negative margin keep the words where plain words stand. The underline sits on the one
 * span inside, a block that holds the words, since engines differ on carrying a flex container's
 * decoration into its items.
 */
const pairSx = {
  font: 'inherit',
  letterSpacing: 'inherit',
  color: 'inherit',
  bgcolor: 'transparent',
  border: 'none',
  borderRadius: '4px',
  p: 0,
  px: 0.25,
  mx: -0.25,
  display: 'inline-flex',
  alignItems: 'center',
  maxWidth: '100%',
  minHeight: { xs: 32, sm: 24 },
  my: { xs: 0, sm: -0.25 },
  textAlign: 'start',
  overflowWrap: 'anywhere',
  cursor: 'pointer',
  '& > span': { minWidth: 0, textDecoration: 'underline dotted', textUnderlineOffset: '3px' },
  // Green as text in the shade that reads 4.5:1 in each theme; the underline in the brand green.
  '&:hover': {
    color: 'var(--code-comment)',
    '& *': { color: 'inherit' },
    '& > span': { textDecorationColor: colors.primary },
  },
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
} as const;

/**
 * The bindings in one line under the preview: `x (across): month · y (up): revenue · color:
 * region`, each column in ink, a family's columns side by side, a required role without a column
 * as `—`. Only `x` and `y` say which way they run (`axisWord`). An optional role left open says
 * nothing. The dropdowns stand behind `.change()` (`BindingsBlock`), and each pair opens them on
 * its own role while they answer (`onRole`); a pair wraps whole.
 */
export function BindingsLine({ roles, hasRoles, checking, toggle, onRole }: BindingsLineProps) {
  const empty = !hasRoles
    ? checking
      ? 'checking roles…'
      : 'this plot names no data roles'
    : 'no column bound yet';
  return (
    <Box
      sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', columnGap: 0.5, minWidth: 0 }}
    >
      <Box
        data-testid="bindings-line"
        sx={{
          fontFamily: typography.mono,
          fontSize: fontSize.md,
          lineHeight: 1.6,
          color: 'var(--ink-soft)',
          overflowWrap: 'anywhere',
          minWidth: 0,
        }}
      >
        {roles.length === 0 && empty}
        {roles.map((role, index) => {
          const words = (
            <>
              {role.name}
              {axisWord(role.name)}:{' '}
              {role.missing ? (
                <>
                  <span aria-hidden>—</span>
                  <Box component="span" sx={visuallyHiddenSx}>
                    no column yet
                  </Box>
                </>
              ) : (
                <Box component="span" sx={{ color: 'var(--ink)', fontWeight: 600 }}>
                  {role.columns.join(', ')}
                </Box>
              )}
            </>
          );
          return (
            <Box component="span" key={role.name}>
              {index > 0 && ' · '}
              {onRole ? (
                <Box
                  component="button"
                  type="button"
                  id={pairId(role.name)}
                  data-pair={role.name}
                  aria-label={pairName(role)}
                  onClick={() => onRole(role.name)}
                  sx={pairSx}
                >
                  {/* One flex item, so the space after the colon stays. */}
                  <span>{words}</span>
                </Box>
              ) : (
                words
              )}
            </Box>
          );
        })}
      </Box>
      {toggle}
    </Box>
  );
}

/** The bindings' heading, and the two it swaps to while the server works. */
const HEADING = {
  idle: '# bindings — which column plays which role',
  working: '# bindings — wait while the assistant works',
  parsing: '# bindings — wait while the data is parsed',
} as const;

/**
 * Every spec role's column dropdown, its accepted kinds, and its sign/wide-table hints: what
 * `.change()` on the bindings line opens, or a click on one of its pairs (`BindingsLine`).
 */
export function BindingsBlock({
  id,
  rows,
  columns,
  bindings,
  missingRoles,
  bindingsBusy,
  bindingsError,
  parsing,
  ready,
  working,
  busy,
  suggestion,
  onBind,
  onEscape,
}: BindingsBlockProps) {
  const heading = working ? (parsing ? HEADING.parsing : HEADING.working) : HEADING.idle;
  const handleKeyDown = (event: React.KeyboardEvent<HTMLElement>) => {
    // A family's menu stands in a portal outside the block and takes its own Escape first.
    if (event.key !== 'Escape' || event.defaultPrevented) return;
    if (!event.currentTarget.contains(event.target as Node)) return;
    event.preventDefault();
    onEscape?.();
  };
  return (
    <Box id={id} data-testid="bindings-editor" onKeyDown={onEscape ? handleKeyDown : undefined}>
      {/* While the server works, the heading itself says why the dropdowns do not answer: the
          server runs one thing per session. A line of its own under the heading read as the
          heading twice and moved the dropdowns as it came and went. The other headings stand
          unseen in the same place, so a swap never changes the line count at any width. Not a
          live region: the thread and the step status announce the work. */}
      <Box sx={{ ...labelSx, mb: 0.75, display: 'grid', '& > *': { gridArea: '1 / 1' } }}>
        {Object.values(HEADING).map(text => (
          <Box
            key={text}
            component="span"
            data-testid={text === heading ? 'bindings-heading' : undefined}
            aria-hidden={text === heading ? undefined : true}
            sx={{ visibility: text === heading ? undefined : 'hidden' }}
          >
            {text}
          </Box>
        ))}
      </Box>
      {rows.length === 0 && (
        <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
          {bindingsBusy ? 'checking roles…' : 'this plot names no data roles'}
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
          const missing = missingRoles.includes(row.role.name);
          const id = roleControlId(row.name);
          const family = row.role.variadic;
          const bound = bindings[row.name];
          const hintOf = (column: string | undefined) =>
            bindingHint(row.role, column, columns, suggestion);
          const sign = family ? null : hintOf(bound);
          return (
            <Box key={row.name} sx={{ display: 'contents' }}>
              {/* A family's chips are a list it names; a single role's dropdown has the label. */}
              <Box
                component={family ? 'div' : 'label'}
                id={`${id}-label`}
                htmlFor={family ? undefined : id}
                title={row.role.description || undefined}
                sx={{
                  fontFamily: typography.mono,
                  fontSize: fontSize.md,
                  color: missing ? colors.error : 'var(--ink)',
                  overflowWrap: 'anywhere',
                  // The kinds line wraps instead of squeezing the dropdowns.
                  maxWidth: { xs: '13ch', sm: '16ch' },
                  alignSelf: family ? 'start' : undefined,
                }}
              >
                {row.name}
                {row.role.required ? ' *' : ''}
                <Box component="span" sx={{ display: 'block', ...labelSx, fontSize: smallText }}>
                  {kindsHint(row.role)}
                </Box>
              </Box>
              {family ? (
                <FamilyChips
                  row={row}
                  columns={columns}
                  disabled={!ready || busy}
                  listId={id}
                  labelId={`${id}-label`}
                  hintOf={hintOf}
                  onBind={onBind}
                />
              ) : (
                <Box sx={{ minWidth: 0 }}>
                  <Box
                    component="select"
                    id={id}
                    value={bound ?? ''}
                    disabled={!ready || busy}
                    aria-describedby={sign ? `${id}-sign` : undefined}
                    onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                      onBind(row.name, event.target.value || null)
                    }
                    sx={{ ...nativeControlSx, width: '100%' }}
                  >
                    <option value="">{emptyChoice(row.role)}</option>
                    {/* A column the role cannot take stays listed, greyed out with the reason,
                      so the user sees why it is no choice instead of meeting a refusal. */}
                    {columns.map(column => (
                      <option
                        key={column.name}
                        value={column.name}
                        disabled={column.name !== bound && !fits(row.role, column.dtype)}
                      >
                        {columnLabel(row.role, column)}
                      </option>
                    ))}
                  </Box>
                  {sign && (
                    <Box
                      id={`${id}-sign`}
                      data-testid="sign-hint"
                      sx={{ ...labelSx, fontSize: smallText, color: colors.warning, mt: 0.25 }}
                    >
                      {sign}
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          );
        })}
      </Box>
      {missingRoles.length > 0 && (
        <Box sx={{ ...labelSx, mt: 1 }}>
          * required: pick a column for {missingRoles.join(', ')}
        </Box>
      )}
      {bindingsError && (
        <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: 1 }}>
          {describeDataFailure(bindingsError.code, bindingsError.ref)}
          {bindingsError.errors && bindingsError.errors.length > 0 && (
            <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2.5, fontSize: smallText }}>
              {bindingsError.errors.map((line, index) => (
                <li key={index}>{line}</li>
              ))}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}
