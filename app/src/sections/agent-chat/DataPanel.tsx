/**
 * The data card of the agent chat, the first turn of the thread: paste data
 * (1 MB cap with a live counter), parse it on the server, check the 20-row
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
 * disabled look; a hidden live region announces the parse and the step. While
 * the admin fan-out's panel is open (`locked`), every action waits in the same
 * way, since its sessions copy this data, and a line at the top of the card,
 * which the card names as its description, says to close the panel first.
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
 *
 * Code that generates data (Python, JavaScript, R) is refused the same way
 * (`422 code`) and offered to the chat, where the assistant runs it in a
 * sandbox; code longer than a chat message cannot move there, so the line asks
 * to shorten it instead. A version the assistant computed from code shows the
 * Python that ran in a `# code that made this data` block, collapsed behind
 * `.show()`.
 *
 * Lines pasted above or below the table (a title, a source line, a sentence
 * about the columns) are left out of the table but kept as notes the assistant
 * reads with the data. A `# notes sent to the assistant` block under the
 * warnings lists the ones the server kept, collapsed behind `.show()`.
 *
 * A text file comes in three ways: dropped on the box, chosen with `.open()`
 * (the keyboard's and the phone's way), or pasted as a file. The browser
 * reads it (`fileText.ts`: binary formats answered by name, the encoding
 * found, the size checked) and fills the box with the text exactly as in the
 * file; the user checks it and presses `.parse()`, which takes the focus. A
 * box with text asks first (`.replace()` / `.keep()`), a running step refuses
 * the file, and a live line says what was read. The file's name travels as the
 * dataset route's `source` field, never in the text. The server screens it and
 * keeps it apart from the notes (the assistant reads it as data, never as a
 * request); the data line shows it. Typing keeps the name, a text paste or an
 * empty box drops it; a table read from the file keeps it for `.use()`.
 * Several files at once: the first is read, and the line says so.
 *
 * A binary data file (Excel, OpenDocument, Parquet, Feather, Arrow, NumPy, at
 * most 5 MB) goes to the server instead (`onConvert`, `POST .../dataset/convert`),
 * which reads it in the renderer's sandbox and answers the text for the box;
 * then it fills the box like a text file, and `.parse()` sends that text with
 * the name and the sheet as `source` (`Bericht.xlsx · sheet ‹2024›`: the sheet in
 * single angle quotes, so the data line's `from "…"` never nests quotes). While it
 * is read, `.open()`, `.parse()` and the drop zone wait. The line names what
 * was read and what the server counted (formula cells without a saved value,
 * hidden sheets, columns left out); a refusal names its numbers. A workbook
 * with several sheets keeps the file in the page and offers a sheet picker,
 * which reads the chosen sheet again: over the file's own untouched text at
 * once, over an edited box after `.replace()`. Text with several tables one
 * below the other (a report sheet) is read as its first table, and a table
 * picker beside the preview parses the same text again for another one
 * (`tables` in the dataset route's answer).
 *
 * `.view_all()` next to the preview's label opens every row of the current
 * version in a read-only grid (`DataView.tsx`, loaded on demand): the
 * canonical `data.csv` with each value as the data holds it, to search, sort
 * and filter without changing the data. Read-only, so it opens while a step
 * runs and while the fan-out's panel is open; the focus returns to the button
 * when it closes.
 */

import { Suspense, useLayoutEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import GlobalStyles from '@mui/material/GlobalStyles';

import { type AgentSessionState, sessionBusy } from 'src/hooks/useAgentSession';
import {
  type ConvertAnswer,
  longSuggestion,
  MAX_DATASET_BYTES,
  MAX_MESSAGE_CHARS,
  tableChoice,
  utf8Bytes,
} from 'src/lib/agent';
import {
  bindingRows,
  emptyChoice,
  kindsHint,
  siblingHint,
  signHint,
} from 'src/sections/agent-chat/bindings';
import { BoxWorking } from 'src/sections/agent-chat/BoxWorking';
import {
  ChangeBlock,
  CodeBlock,
  countOf,
  dataShape,
  DataView,
  DataViewUnavailable,
  formatKb,
  LongHint,
  NotesBlock,
  offerLine,
  preloadDataView,
  PreviewTable,
  stepButtonSx,
  TranscriptionCard,
  WarningList,
} from 'src/sections/agent-chat/dataCardParts';
import { Ellipsis } from 'src/sections/agent-chat/Ellipsis';
import { FILE_ACCEPT } from 'src/sections/agent-chat/fileText';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import {
  CONFIRM_LOST_TEXT,
  DATA_HOWTO,
  DATA_PLACEHOLDER,
  describeDataFailure,
} from 'src/sections/agent-chat/messages';
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
import { FILE_NAME_WITHHELD, useFileIntake } from 'src/sections/agent-chat/useFileIntake';
import { colors, fontSize, typography } from 'src/theme';

export { DataViewUnavailable };

/** The line the pinned header shows, and `.create_plot()` names as its description. */
export const DATA_SUMMARY_ID = 'agent-data-summary';

interface DataPanelProps {
  state: AgentSessionState;
  /**
   * `.parse()`; `source` is the name of the file the text was read from, if it was;
   * `table` reads another of the tables the stored paste named (the table picker).
   */
  onParse: (text: string, source?: string, table?: number) => void;
  /** `.use()` on a transcription; the session keeps the file's name with the table it was read from. */
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
  /** Analytics: `agent_data_file{kind, encoding, outcome}`; never the file's name. */
  onTrack?: (event: string, props?: Record<string, string | undefined>) => void;
  /**
   * A dropped binary data file read on the server (`POST .../dataset/convert`); `sheet`
   * asks for another sheet of the same file. Without it, such files are refused.
   */
  onConvert?: (dataBase64: string, sheet?: string) => Promise<ConvertAnswer>;
  /**
   * The admin fan-out's panel is open: its sessions copy this session's confirmed data, so
   * nothing here may change it until the panel closes. Every action waits, as while a step
   * runs, and a line at the top of the card says why.
   */
  locked?: boolean;
  /**
   * `.view_all()`: the current data version's canonical `data.csv` (`GET .../dataset/data.csv`)
   * for the full view of every row. Without it the preview has no `.view_all()`.
   */
  onLoadData?: (signal: AbortSignal) => Promise<string>;
  /** The full view showed its rows, once per opening: the `opened_data_view` beacon. */
  onDataViewShown?: () => void;
}

/** The card's line while the fan-out's panel is open, which the card names as its description. */
export const DATA_LOCK_TEXT =
  '# the data waits while all libraries plot it · .close() the panel to change it';
const DATA_LOCK_ID = 'agent-data-lock';

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
  onTrack,
  onConvert,
  locked = false,
  onLoadData,
  onDataViewShown,
}: DataPanelProps) {
  const [text, setText] = useState('');
  // `.view_all()`: the full view of every row is open. Read-only, so it opens while a step runs too.
  const [viewOpen, setViewOpen] = useState(false);
  const viewButtonRef = useRef<HTMLButtonElement>(null);
  // When the panel's last parse began, set where it starts (every parse starts here: `.parse()`,
  // the table picker, `.use()`), so the overlay's count survives its remount.
  const parseStart = useRef(0);
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
  const working = sessionBusy(state);
  // Every action also waits while the fan-out's panel copies this data (`locked`).
  const busy = working || locked;
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

  const {
    convertLine,
    converting,
    converted,
    source,
    dragOver,
    dropReady,
    fileNotice,
    pendingFile,
    convertStart,
    boxRef,
    parseButtonRef,
    fileInputRef,
    replaceButtonRef,
    clearFile,
    handleTextChange,
    fillFromFile,
    handleSheet,
    handleKeep,
    handleDragEnter,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handlePaste,
    handleChosen,
  } = useFileIntake({
    text,
    setText,
    ready,
    working,
    busy,
    locked,
    hasTranscription: !!transcription,
    onDiscardTranscription,
    onExpand: () => setExpanded(true),
    onConvert,
    onTrack,
  });

  // A request for data moved to the chat as the user's message (`dataRequest`), as `.send()` moves a formula: the
  // box is free for a table. Only while it still holds that text: an edit made while the parse ran stays. Adjusted
  // during render, as React adjusts state when a prop changes.
  const [requestSeen, setRequestSeen] = useState(state.dataRequest?.seq ?? 0);
  if (state.dataRequest && state.dataRequest.seq !== requestSeen) {
    setRequestSeen(state.dataRequest.seq);
    if (text.trim() === state.dataRequest.text) {
      setText('');
      clearFile();
    }
  }

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
  // A paste of several tables: the picker reads another one (live test round 5 of 2026-10-15). The text
  // is the stored paste's own (`DatasetState.paste`): an edit of the box or a failed parse since does not count.
  const paste = dataset?.paste;
  const choice = dataset && paste ? tableChoice(dataset.parsed) : null;

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
    parseStart.current = Date.now();
    onConfirmTranscription();
  };

  // `.parse()`: the file's name rides along only when the text came from a file.
  const handleParse = () => {
    parseStart.current = Date.now();
    if (source) onParse(text, source);
    else onParse(text);
  };

  // The table picker: the stored paste's text again, another of its tables.
  const handleTable = (table: number) => {
    if (!paste || !ready || busy || converting || table === choice?.table) return;
    parseStart.current = Date.now();
    onParse(paste.text, paste.source, table);
  };

  // Code over the chat's cap is refused all the same, but cannot move there: the line asks to shorten it.
  const codeTooLong =
    state.formulaKind === 'code' && (state.formula ?? '').trim().length > MAX_MESSAGE_CHARS;

  // `.send()`: the formula or code moves to the chat as a turn, so the box is free for a table.
  const handleSendFormula = () => {
    setText('');
    clearFile();
    onSendFormula();
  };

  // The full card: the text box and its offers, then the stored data with its
  // bindings, and in step 1 the confirmation at its foot.
  const cardContent = (
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
            onClick={handleParse}
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
            {offerLine(state.formulaKind, codeTooLong)}
          </Box>
          {!codeTooLong && (
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
          )}
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
                  handleTable(Number(event.target.value))
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

          <Box>
            <Box sx={{ ...labelSx, mb: 0.75 }}># bindings — which column plays which role</Box>
            {/* Why the dropdowns and `.confirm()` do not answer: the server runs one thing
                per session. Not a live region: the thread and the step status announce the work. */}
            {working && (
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
                // A wide table's number column in a role that wants labels comes first: the plot would be meaningless.
                const sign =
                  siblingHint(row.role, bound, suggestion) ??
                  signHint(
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
                        <option value="">{emptyChoice(row)}</option>
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
          aria-describedby={locked ? DATA_LOCK_ID : undefined}
          id="agent-data-card"
          data-testid="data-card"
          ref={cardRef}
          sx={cardSx}
        >
          {/* Why every control below waits: the fan-out's sessions copy this data. */}
          {locked && (
            <Box
              id={DATA_LOCK_ID}
              data-testid="data-lock"
              sx={{ ...labelSx, color: 'var(--ink)', mb: 1.5 }}
            >
              {DATA_LOCK_TEXT}
            </Box>
          )}
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
