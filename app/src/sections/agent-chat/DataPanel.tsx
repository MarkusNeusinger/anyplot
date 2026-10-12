/**
 * The data card of the agent chat, the first turn of the thread: paste data
 * (200 KB cap with a live counter), parse it on the server, check the 20-row
 * preview and the parser's warnings, and bind each spec role to a column (the
 * server's defaults come preselected).
 *
 * Two steps, data first. Step 1 ends with `.confirm()` at the foot of the card,
 * once every required role has a column: the user says the preview and the
 * bindings are right. The card then collapses into a pinned header at the top
 * of the thread, which stays in view on scroll: `✓ data fits · N rows · M
 * columns · version V` with `.show()`, which opens the full card again below it
 * without leaving step 2 and brings its top into view, and `.hide()`, which
 * closes it and goes back to where the user was. Step 2's `.create_plot()` is
 * the page's composer, not the card's. A new parse, a binding change, a change
 * the assistant made to the data and an undo take the page back to step 1 with
 * the card open, because a plot of the wrong data is wrong however good it
 * looks; the server drops its confirmation for each of them already. The
 * header stays then and reads as a warning (`! confirm again · ...`, the
 * phrase in bold on a surface tinted with the warning token), and its
 * `.show()` leads back to the card from anywhere in the thread, for example
 * after a data request sent from below the plot. The step line next to
 * `.confirm()` names what dropped the confirmation, as the thread's notice
 * does. A table read from text that waits for its decision holds the page in
 * step 1 as well, whatever a turn's sync says, and the header names that
 * decision.
 *
 * Work in flight shows on the card: a line under `.parse()` while the data is
 * parsed, and, while anything runs (the parse, a turn, a theme render, a
 * binding change, a confirmation, an undo), a line under the bindings label
 * that says the dropdowns and `.confirm()` wait, because the server runs one
 * thing per session and would refuse a second. The controls keep their
 * disabled look; a hidden live region announces the parse and the step.
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

import { useLayoutEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import GlobalStyles from '@mui/material/GlobalStyles';

import {
  type AgentSessionState,
  type DataChange,
  type Failure,
  sessionBusy,
  type TranscriptionState,
} from 'src/hooks/useAgentSession';
import {
  type ColumnProfile,
  type LongSuggestion,
  longSuggestion,
  MAX_DATASET_BYTES,
  utf8Bytes,
} from 'src/lib/agent';
import { bindingRows, kindsHint, signHint } from 'src/sections/agent-chat/bindings';
import { Ellipsis } from 'src/sections/agent-chat/Ellipsis';
import { CONFIRM_LOST_TEXT, describeDataFailure } from 'src/sections/agent-chat/messages';
import { inStep2 } from 'src/sections/agent-chat/steps';
import {
  actionButtonSx,
  bodyTextSx,
  cardSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  PINNED_CLEARANCE,
  PINNED_TOP,
  smallText,
  visuallyHiddenSx,
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
  /** The `.use()` button, for the page to bring into view and focus. */
  decisionRef?: React.Ref<HTMLButtonElement>;
}

/** A table a model read from free text, for the user to check before it is stored. */
function TranscriptionCard({
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

/** Step 1's one action under the bindings: `.confirm()`. */
const stepButtonSx = {
  ...actionButtonSx,
  border: '1px solid var(--rule)',
  px: 2,
  py: 1,
  width: { xs: '100%', sm: 'auto' },
} as const;

/** The line the pinned header shows, and `.create_plot()` names as its description. */
export const DATA_SUMMARY_ID = 'agent-data-summary';

/** The data's shape in one line: `2 rows · 2 columns · version 1`. */
function dataShape(dataset: NonNullable<AgentSessionState['dataset']>): string {
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
function LongHint({ suggestion, canApply, busy, error, onApply }: LongHintProps) {
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
  /** `.to_long()`: apply the wide-table offer as the next data version. */
  onToLong?: () => void;
  /** The pinned header's `.show()` / `.hide()`, for the page to move the keyboard focus to. */
  toggleRef?: React.Ref<HTMLButtonElement>;
  /**
   * Step 1's `.confirm()` and a pending table's `.use()`: the composer's notice
   * before the confirmation brings them into view and focuses them.
   */
  confirmRef?: React.Ref<HTMLButtonElement>;
  decisionRef?: React.Ref<HTMLButtonElement>;
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
  onToLong,
  toggleRef,
  confirmRef,
  decisionRef,
}: DataPanelProps) {
  const [text, setText] = useState('');
  // Step 2 only: whether the full card shows below the pinned header.
  const [expanded, setExpanded] = useState(false);
  const cardRef = useRef<HTMLElement>(null);
  // Where the commit after a toggle scrolls: the card's top after `.show()`,
  // back to the reading position from before it after `.hide()`.
  const scrollTarget = useRef<'card' | number | null>(null);
  const returnTo = useRef<number | null>(null);
  const bytes = utf8Bytes(text);
  const over = bytes > MAX_DATASET_BYTES;
  const ready = state.phase === 'ready' && !!state.sessionId;
  // A turn, a theme render, a parse, a binding change or a confirmation in
  // flight: the server would refuse or race a second one.
  const busy = sessionBusy(state);
  const transcription = state.transcription;
  const dataset = state.dataset;
  const columns = dataset?.parsed.profile.columns ?? [];
  // Step 2: the card is collapsed into the pinned header unless the user opened it.
  const confirmed = inStep2(state);
  const open = !confirmed || expanded;
  // Once the data was confirmed, the pinned header stays, also when the page is
  // back at step 1: it leads back to the card from anywhere in the thread, and
  // the content below it does not jump when the confirmation drops.
  const everConfirmed = useRef(false);
  if (confirmed) everConfirmed.current = true;
  const pinned = !!dataset && everConfirmed.current;
  // A pending transcription blocks the confirmation: the user decides on the data first.
  const canConfirm = ready && !!dataset && state.bindingsComplete && !busy && !transcription;
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

  // `.show()` from far down the thread opens the card at the top of the thread,
  // out of view: bring its top in below the pinned header (the page's
  // scroll-padding keeps it clear). `.hide()` goes back to where the user read.
  useLayoutEffect(() => {
    const target = scrollTarget.current;
    scrollTarget.current = null;
    if (target === 'card') {
      cardRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
    } else if (target !== null && target !== window.scrollY) {
      window.scrollTo({ top: target });
    }
  }, [expanded]);

  const handleToggle = () => {
    // Step 1 again: the card is open anyway, somewhere above; the header leads to it.
    if (!confirmed) {
      cardRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (expanded) {
      scrollTarget.current = returnTo.current;
      returnTo.current = null;
    } else {
      returnTo.current = window.scrollY;
      scrollTarget.current = 'card';
    }
    setExpanded(!expanded);
  };

  // `.confirm()` collapses the card; a later step 1 opens it in full anyway.
  const handleConfirm = () => {
    setExpanded(false);
    onConfirmData();
  };

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

  // The full card: the text box and its offers, then the stored data with its
  // bindings, and in step 1 the confirmation at its foot.
  const cardContent = (
    <>
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
          aria-describedby={transcription || state.parsing ? 'agent-parse-hint' : undefined}
          sx={ghostButtonSx}
        >
          {state.parsing ? '.parse() …' : '.parse()'}
        </Box>
      </Box>
      {/* A parse clears a pending table, so the two lines never show together. */}
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
          {state.parsing ? (
            <>
              # parsing your data <Ellipsis />
            </>
          ) : (
            'decide on the table below first: .use() or .discard()'
          )}
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
          decisionRef={decisionRef}
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
            {/* Why the dropdowns and `.confirm()` do not answer: the server runs one thing
                per session. Not a live region: the thread and the step status announce the work. */}
            {busy && (
              <Box
                data-testid="bindings-lock"
                sx={{ ...labelSx, color: 'var(--ink-soft)', mt: -0.25, mb: 1 }}
              >
                # {confirmed ? 'bindings wait' : 'bindings and .confirm() wait'} while{' '}
                {state.parsing ? 'the data is parsed' : 'the assistant works'} <Ellipsis />
              </Box>
            )}
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
                const bound = state.bindings[row.name];
                const sign = signHint(
                  row.role,
                  columns.find(column => column.name === bound)
                );
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
                        <option value="">{row.next ? '— add a column —' : '— none —'}</option>
                        {columns.map(column => (
                          <option key={column.name} value={column.name}>
                            {column.name} ({column.dtype})
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

          {/* Step 2 has no foot: the pinned header says the data fits, and the
              composer below the thread holds `.create_plot()`. */}
          {!confirmed && (
            <Box>
              <Box
                id="agent-step-line"
                data-testid="data-step"
                // A notch above the `#` labels: this line says what to do next, and after a
                // lost confirmation what lost it, as the thread's notice does.
                sx={{ ...labelSx, mb: 0.75, color: 'var(--ink-soft)' }}
              >
                {state.confirmLoss
                  ? `# step 1 again — ${CONFIRM_LOST_TEXT[state.confirmLoss]}`
                  : '# step 1 — check the preview and the bindings, then confirm'}
              </Box>
              <Box
                component="button"
                type="button"
                ref={confirmRef}
                onClick={handleConfirm}
                disabled={!canConfirm}
                aria-describedby="agent-step-line"
                sx={stepButtonSx}
              >
                {state.confirmBusy ? '.confirm() …' : '.confirm()'}
              </Box>
              {state.confirmError && (
                <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: 1 }}>
                  {describeDataFailure(state.confirmError.code, state.confirmError.ref)}
                </Box>
              )}
            </Box>
          )}
        </Box>
      )}
    </>
  );

  return (
    <>
      {/* Stays mounted, so a screen reader hears the step change: the lines that
          say it on screen come and go with the card. */}
      <Box data-testid="data-step-status" aria-live="polite" sx={visuallyHiddenSx}>
        {state.parsing
          ? 'parsing your data'
          : confirmed
            ? 'step 2: the data is confirmed; create the plot below'
            : dataset
              ? 'step 1: check the data, then confirm it'
              : ''}
      </Box>

      {/* While the header sticks, the page's focus and scrolling land below it (WCAG 2.4.11). */}
      {pinned && <GlobalStyles styles={{ html: { scrollPaddingTop: PINNED_CLEARANCE } }} />}
      {pinned && dataset && (
        <Box
          data-testid="data-pinned"
          sx={{
            position: 'sticky',
            top: PINNED_TOP,
            zIndex: 10,
            // One row: at phone width the line wraps beside the toggle, never under it,
            // so the header stays two lines high at most.
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            // Back at step 1 the header reads as a warning. The amber token is too light
            // for text on the light page (1.6:1), so it tints the surface instead.
            bgcolor: confirmed
              ? 'var(--bg-elevated)'
              : `color-mix(in srgb, ${colors.warning} 18%, var(--bg-elevated))`,
            border: '1px solid var(--rule)',
            borderLeft: `3px solid ${confirmed ? colors.primary : colors.warning}`,
            borderRadius: 1,
            pl: 1.5,
            pr: 0.75,
            py: 0.5,
            minWidth: 0,
          }}
        >
          <Box
            id={DATA_SUMMARY_ID}
            data-testid="data-summary"
            sx={{
              ...labelSx,
              color: 'var(--ink)',
              flex: '1 1 auto',
              minWidth: 0,
              overflowWrap: 'anywhere',
            }}
          >
            <Box
              component="span"
              aria-hidden
              sx={{ color: confirmed ? colors.success : colors.warning, mr: 0.75 }}
            >
              {confirmed ? '✓' : '!'}
            </Box>
            {confirmed ? (
              `data fits · ${dataShape(dataset)}`
            ) : (
              <>
                {/* What to do, in bold: the warning reads in the words, not only the colour. */}
                <Box component="span" data-tone="warning" sx={{ fontWeight: 600 }}>
                  {transcription ? 'decide on the table first' : 'confirm again'}
                </Box>
                {transcription ? ': .use() or .discard()' : ` · ${dataShape(dataset)}`}
              </>
            )}
          </Box>
          <Box
            component="button"
            type="button"
            ref={toggleRef}
            onClick={handleToggle}
            // Step 1 again: the card is open, and the button leads to it.
            aria-expanded={confirmed ? expanded : undefined}
            aria-controls={open ? 'agent-data-card' : undefined}
            aria-label={
              !confirmed ? 'Go to the data' : expanded ? 'Hide the data' : 'Show the data'
            }
            sx={{ ...actionButtonSx, flex: 'none' }}
          >
            {confirmed && expanded ? '.hide()' : '.show()'}
          </Box>
        </Box>
      )}

      {open && (
        <Box
          component="section"
          aria-label="Your data"
          id="agent-data-card"
          data-testid="data-card"
          ref={cardRef}
          sx={cardSx}
        >
          {/* With the header above it, one line says what a change here does; the line
              stays when the confirmation drops, so the controls below it do not jump. */}
          {pinned && (
            <Box sx={{ ...labelSx, mb: 1.5 }}>
              {confirmed
                ? '# a change here takes the data back to step 1, where you confirm it again'
                : '# step 1 again: check the data, then confirm it below'}
            </Box>
          )}
          {cardContent}
        </Box>
      )}
    </>
  );
}
