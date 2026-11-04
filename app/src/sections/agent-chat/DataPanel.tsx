/**
 * The data card of the agent chat, the first turn of the thread: paste data
 * (1 MB cap with a live counter), parse it on the server, check the 20-row
 * preview and the parser's warnings, and bind each spec role to a column (the
 * server's defaults come preselected).
 *
 * Two steps, data first. Step 1 ends with `.confirm()` at the composer's end
 * (`Composer.tsx`), once every required role has a column: the user says the
 * preview and the bindings are right. The card then collapses into a pinned header at the top
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
 * after a data request sent from below the plot. The step line above the
 * composer names what dropped the confirmation, as the thread's notice
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

import { useLayoutEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { type AgentSessionState, sessionBusy } from 'src/hooks/useAgentSession';
import { type ConvertAnswer, tableChoice } from 'src/lib/agent';
import { DataCard } from 'src/sections/agent-chat/DataCard';
import { DataViewUnavailable } from 'src/sections/agent-chat/dataCardParts';
import { DATA_LOCK_TEXT, DATA_SUMMARY_ID, PinnedData } from 'src/sections/agent-chat/PinnedData';
import { inStep2 } from 'src/sections/agent-chat/steps';
import { visuallyHiddenSx } from 'src/sections/agent-chat/styles';
import { useFileIntake } from 'src/sections/agent-chat/useFileIntake';

export { DATA_LOCK_TEXT, DATA_SUMMARY_ID, DataViewUnavailable };

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
  onUndo: () => void;
  /** `.to_long()`: apply the wide-table offer as the next data version. */
  onToLong?: () => void;
  /** The pinned header's `.show()` / `.hide()`, for the page to move the keyboard focus to. */
  toggleRef?: React.Ref<HTMLButtonElement>;
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

export function DataPanel({
  state,
  onParse,
  onConfirmTranscription,
  onDiscardTranscription,
  onSendFormula,
  onBind,
  onUndo,
  onToLong,
  toggleRef,
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
  const ready = state.phase === 'ready' && !!state.sessionId;
  // A turn, a theme render, a parse, a binding change or a confirmation in
  // flight: the server would refuse or race a second one.
  const working = sessionBusy(state);
  // Every action also waits while the fan-out's panel copies this data (`locked`).
  const busy = working || locked;
  const transcription = state.transcription;
  const dataset = state.dataset;
  // Step 2: the card is collapsed into the pinned header unless the user opened it.
  const confirmed = inStep2(state);
  const open = !confirmed || expanded;
  // Once the data was confirmed, the pinned header stays, also when the page is
  // back at step 1: it leads back to the card from anywhere in the thread, and
  // the content below it does not jump when the confirmation drops.
  const everConfirmed = useRef(false);
  if (confirmed) everConfirmed.current = true;
  const pinned = !!dataset && everConfirmed.current;
  // The user's `.confirm()` (at the composer's end) collapses the card as it starts; a later
  // step 1 opens it in full anyway. A step 2 that returns without it (a discarded table) keeps
  // the card as the user left it. Adjusted while rendering, React's pattern for state that
  // follows a prop.
  const [confirmSeen, setConfirmSeen] = useState(state.confirmBusy);
  if (state.confirmBusy !== confirmSeen) {
    setConfirmSeen(state.confirmBusy);
    if (state.confirmBusy) setExpanded(false);
  }

  const intake = useFileIntake({
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
      intake.clearFile();
    }
  }

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
    if (intake.source) onParse(text, intake.source);
    else onParse(text);
  };

  // The table picker: the stored paste's text again, another of its tables.
  const handleTable = (table: number) => {
    if (!paste || !ready || busy || intake.converting || table === choice?.table) return;
    parseStart.current = Date.now();
    onParse(paste.text, paste.source, table);
  };

  // `.send()`: the formula or code moves to the chat as a turn, so the box is free for a table.
  const handleSendFormula = () => {
    setText('');
    intake.clearFile();
    onSendFormula();
  };

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

      <PinnedData
        pinned={pinned}
        confirmed={confirmed}
        expanded={expanded}
        open={open}
        locked={locked}
        dataset={dataset}
        hasTranscription={!!transcription}
        toggleRef={toggleRef}
        cardRef={cardRef}
        onToggle={handleToggle}
      >
        <DataCard
          state={state}
          intake={intake}
          text={text}
          ready={ready}
          working={working}
          busy={busy}
          locked={locked}
          confirmed={confirmed}
          choice={choice}
          viewOpen={viewOpen}
          setViewOpen={setViewOpen}
          viewButtonRef={viewButtonRef}
          parseStart={parseStart}
          onParse={handleParse}
          onTable={handleTable}
          onUse={handleUse}
          onDiscardTranscription={onDiscardTranscription}
          onSendFormula={handleSendFormula}
          onBind={onBind}
          onUndo={onUndo}
          onToLong={onToLong}
          onLoadData={onLoadData}
          onDataViewShown={onDataViewShown}
        />
      </PinnedData>
    </>
  );
}
