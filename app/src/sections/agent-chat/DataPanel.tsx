/**
 * The live data card of the agent chat, at the latest data version (its `data`
 * item, `ChatThread.tsx`): the data the composer's message box sent (a pasted
 * table or a file, with a note), as the server parsed it: the 20-row preview and
 * the parser's warnings, and a column for each spec role (the server's defaults
 * come preselected). Every version keeps an item of its own: the card follows
 * the latest, and each older version folds to its label in the thread
 * (`FoldedData.tsx`). A version a turn made puts the card right after that
 * turn's message, before its reply, and a paste brings a card of its own; one
 * its own controls made (an undo, `.to_long()`, the table and sheet pickers)
 * moves it to the thread's end, before and after a plot alike, after a plot as
 * a new `# data` chapter (owner, 2026-11-07). The keyboard focus follows the
 * card (`useFollowFocus`). A
 * table read from text waits in a card of its own at its paste (`part:
 * 'transcription'`).
 *
 * Two steps, data first. Step 1 ends with `.create_plot()` at the composer's end
 * (`Composer.tsx`), once every required role has a column: its click takes the
 * preview and the bindings as shown, confirms them on the server and starts the
 * plot. The card stays open in both steps, so the data the plot was made from
 * stays in view in its chapter. The plot buttons are the page's composer's, not
 * the card's. A new parse, a binding change, a change the assistant made to the
 * data and an undo take the page back to step 1, because a plot of the wrong
 * data is wrong however good it looks; the server drops its confirmation for
 * each of them already. The status line at the chat frame's foot names what
 * dropped the confirmation, and only it: the thread adds no notice that would
 * say the same. A table read from text that waits for its decision holds the
 * page in step 1 as well, whatever a turn's sync says, and the status line
 * names that decision.
 *
 * Work in flight shows on the card: while anything runs (the parse, a turn, a
 * theme render, a binding change, a confirmation, an undo), a line under the
 * bindings label says the dropdowns wait, because the server runs one thing
 * per session and would refuse a second. The controls keep their disabled
 * look; a hidden live region announces the parse and the step. While
 * the admin fan-out's panel is open (`locked`), every action waits in the same
 * way, since its sessions copy this data, and a line at the top of the card,
 * which the card names as its description, says to close the panel first.
 *
 * The card is framed like the chat window (`CardFrame.tsx`), with the version on
 * its top border (`data v3 · made long · 48 rows × 4 cols`). The bindings read as one
 * line under the preview (`x (across): month · y (up): revenue`), and `.change()`
 * at its end opens a column choice for every role of the spec (`bindingRows` in
 * `bindings.ts`): a single role one dropdown, a variadic family its columns as
 * chips with `×` and `+ y` for the next one. Required roles carry a `*`; the
 * kinds a role accepts sit under its name and the spec's description is its
 * tooltip. The choices open by themselves while a required role has no column
 * or the server refused the bindings (`DataCard.tsx`).
 *
 * Text that is not a table comes back as a table a model read from it, which
 * the server has not stored. A card above the preview shows it with the
 * model's note, and the plot buttons wait until the user decides: `.use()`
 * stores the table's CSV through the normal parse, `.discard()` drops it and
 * puts the pasted text back into the message box for another try.
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
 * rows and offers no `.undo()`. Sent as an attachment (a file of it), the server
 * refuses it (`422 formula`), and the page sends the text to the chat as the
 * user's turn at once, as for a request for data (`422 data_request`).
 *
 * Code that generates data (Python, JavaScript, R) goes the same way (`422
 * code`), and the assistant runs it in a sandbox; code longer than a chat message
 * cannot move there, so the attachment turns red and asks to shorten it instead. A
 * version the assistant computed from code shows the
 * Python that ran in a `# code that made this data` block, collapsed behind
 * `.show()`.
 *
 * Lines pasted above or below the table (a title, a source line, a sentence
 * about the columns) are left out of the table but kept as notes the assistant
 * reads with the data. A `# notes sent to the assistant` block under the
 * warnings lists the ones the server kept, collapsed behind `.show()`.
 *
 * A file comes in through the composer (`useChatAttachment.ts`): dropped on the
 * chat, chosen with `.open()` or pasted as a file. Its name travels as the
 * dataset route's `source` field, never in the text. The server screens it and
 * keeps it apart from the notes (the assistant reads it as data, never as a
 * request); the data line shows it, and a table read from the file keeps it
 * for `.use()`. A binary data file (Excel, OpenDocument, Parquet, Feather,
 * Arrow, NumPy) is read on the server first; a workbook with several sheets
 * stays in the page with the data it made (`DatasetState.file`), and the
 * sheet picker beside the preview reads the chosen sheet again on the server
 * and parses it (the sheet in single angle quotes in the source, `Bericht.xlsx
 * · sheet ‹2024›`, so the data line's `from "…"` never nests quotes). Text with
 * several tables one below the other (a report sheet) is read as its first
 * table, and a table picker beside the preview parses the same text again for
 * another one (`tables` in the dataset route's answer).
 *
 * `.view_all()` next to the preview's label (on a phone, where the card shows no
 * preview table, on its last line beside `.change()`) opens every row of the current
 * version in a read-only grid (`DataView.tsx`, loaded on demand): the
 * canonical `data.csv` with each value as the data holds it, to search, sort
 * and filter without changing the data. Read-only, so it opens while a step
 * runs and while the fan-out's panel is open; the focus returns to the button
 * when it closes.
 */

import { useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { type AgentSessionState, type DataSnapshot, sessionBusy } from 'src/hooks/useAgentSession';
import { AgentApiError, type ConvertAnswer, tableChoice } from 'src/lib/agent';
import { CardFrame } from 'src/sections/agent-chat/CardFrame';
import { dataCardLabel, dataVersionLabel } from 'src/sections/agent-chat/cardLabels';
import { DataCard } from 'src/sections/agent-chat/DataCard';
import { DataViewUnavailable } from 'src/sections/agent-chat/dataCardParts';
import { describeConvertFailure } from 'src/sections/agent-chat/messages';
import { labelSx } from 'src/sections/agent-chat/styles';
import {
  type ConvertedFile,
  convertedSource,
  sheetLabel,
} from 'src/sections/agent-chat/useChatAttachment';
import { useFollowFocus } from 'src/sections/agent-chat/useFollowFocus';

export { DataViewUnavailable };

/** The card's line while the fan-out's panel is open, which the card names as its description. */
export const DATA_LOCK_TEXT =
  '# the data waits while all libraries plot it · .close() the panel to change it';
const DATA_LOCK_ID = 'agent-data-lock';

interface DataPanelProps {
  state: AgentSessionState;
  /** Which item this card stands for: the stored data, or a table read from text that waits. */
  part: 'data' | 'transcription';
  /** The version the live card shows (its `data` item's snapshot), for its label and the focus. */
  version?: DataSnapshot;
  /**
   * A parse of the stored data's text again: `table` reads another of the tables the stored
   * paste named (the table picker), `file` is the workbook a sheet picker's text came from.
   */
  onParse: (text: string, source?: string, table?: number, file?: ConvertedFile) => void;
  /** `.use()` on a transcription; the session keeps the file's name with the table it was read from. */
  onConfirmTranscription: () => void;
  onDiscardTranscription: () => void;
  onBind: (role: string, column: string | null) => void;
  onUndo: () => void;
  /** `.to_long()`: apply the wide-table offer as the next data version. */
  onToLong?: () => void;
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
  /**
   * The user opened `.change()` or `.view_all()` to look at the data: the page's one click on
   * the plot button plots nothing after that (`plotChain.ts`).
   */
  onLook?: () => void;
}

export function DataPanel({
  state,
  part,
  version,
  onParse,
  onConfirmTranscription,
  onDiscardTranscription,
  onBind,
  onUndo,
  onToLong,
  onTrack,
  onConvert,
  locked = false,
  onLoadData,
  onDataViewShown,
  onLook,
}: DataPanelProps) {
  // The focus follows the live card to its new version, wherever the version put it.
  const follow = useFollowFocus(part === 'data' ? version : undefined);
  // `.view_all()`: the full view of every row is open. Read-only, so it opens while a step runs too.
  const [viewOpen, setViewOpen] = useState(false);
  const viewButtonRef = useRef<HTMLButtonElement>(null);
  // The sheet picker's read on the server: what its line says meanwhile, and why it failed.
  const [sheetLine, setSheetLine] = useState<string | null>(null);
  const [sheetError, setSheetError] = useState<string | null>(null);
  // Counts sheet reads, so the answer of a superseded one is dropped.
  const sheetSeq = useRef(0);
  const ready = state.phase === 'ready' && !!state.sessionId;
  // A turn, a theme render, a parse, a binding change or a confirmation in
  // flight: the server would refuse or race a second one.
  const working = sessionBusy(state);
  // Every action also waits while the fan-out's panel copies this data (`locked`).
  const busy = working || locked;
  const transcription = state.transcription;
  const dataset = state.dataset;

  // A paste of several tables: the picker reads another one. The text is the stored paste's
  // own (`DatasetState.paste`): a failed parse since does not count.
  const paste = dataset?.paste;
  const choice = dataset && paste ? tableChoice(dataset.parsed) : null;

  // `.use()`: the table read from the text is stored through the normal parse.
  const handleUse = () => {
    if (transcription) onConfirmTranscription();
  };

  // The table picker: the stored paste's text again, another of its tables.
  const handleTable = (table: number) => {
    if (!paste || !ready || busy || sheetLine || table === choice?.table) return;
    onParse(paste.text, paste.source, table, dataset?.file);
  };

  // The sheet picker: the workbook the data came from, read again on the server for the chosen
  // sheet, then parsed as a paste of that sheet with its name in the source.
  const handleSheet = async (sheet: string) => {
    const file = dataset?.file;
    if (!file || !onConvert || sheet === file.sheet || !ready || busy || sheetLine) return;
    sheetSeq.current += 1;
    const seq = sheetSeq.current;
    setSheetError(null);
    setSheetLine(`reading the sheet ${sheetLabel(sheet)} of "${file.name}" on the server`);
    try {
      const answer = await onConvert(file.base64, sheet);
      if (seq !== sheetSeq.current) return;
      onTrack?.('agent_data_file', { kind: answer.kind, encoding: 'none', outcome: 'sheet' });
      onParse(answer.text, convertedSource(file.name, answer), undefined, {
        ...file,
        kind: answer.kind,
        sheet: answer.sheet,
        sheets: answer.sheets,
        sheetCount: answer.sheet_count,
        text: answer.text,
      });
    } catch (err) {
      if (seq !== sheetSeq.current) return;
      const failure =
        err instanceof AgentApiError ? err : new AgentApiError(0, 'unreachable', null);
      setSheetError(
        describeConvertFailure(
          file.name,
          failure.code,
          failure.measured,
          failure.limit,
          failure.shownRef,
          file.browserKind,
          failure.damage
        )
      );
      onTrack?.('agent_data_file', { kind: file.browserKind, encoding: 'none', outcome: 'failed' });
    } finally {
      if (seq === sheetSeq.current) setSheetLine(null);
    }
  };

  const card = (
    <DataCard
      state={state}
      part={part}
      ready={ready}
      working={working}
      busy={busy}
      choice={choice}
      viewOpen={viewOpen}
      setViewOpen={setViewOpen}
      viewButtonRef={viewButtonRef}
      onTable={handleTable}
      onSheet={sheet => void handleSheet(sheet)}
      sheetLine={sheetLine}
      sheetError={sheetError}
      onUse={handleUse}
      onDiscardTranscription={onDiscardTranscription}
      onBind={onBind}
      onUndo={onUndo}
      onToLong={onToLong}
      onLoadData={onLoadData}
      onDataViewShown={onDataViewShown}
      onLook={onLook}
    />
  );

  // A table read from text waits in a frame of its own at its paste; the stored data's card
  // above it stays as it is until `.use()`.
  if (part === 'transcription') {
    if (!transcription) return null;
    const { profile } = transcription;
    const label = dataCardLabel(profile.rows, profile.columns.length, 'text');
    return (
      // Off for the thread's live log, as the data card is.
      <CardFrame
        label={label.text}
        spokenLabel={label.spoken}
        labelTestId="transcription-label"
        data-testid="transcription-item"
        aria-live="off"
      >
        {card}
      </CardFrame>
    );
  }
  if (!dataset) return null;
  // A thread built by hand gives its card no version: the label names the shape alone.
  const label = version
    ? dataVersionLabel(version)
    : dataCardLabel(dataset.parsed.profile.rows, dataset.parsed.profile.columns.length);
  return (
    <CardFrame
      component="section"
      label={label.text}
      spokenLabel={label.spoken}
      labelTestId="data-card-label"
      labelRef={follow.labelRef}
      aria-label="Your data"
      aria-describedby={locked ? DATA_LOCK_ID : undefined}
      // The thread is a polite live log: a dropdown or a preview changing in the card is no news
      // to read out. The card's own status lines keep their roles.
      aria-live="off"
      id="agent-data-card"
      data-testid="data-card"
      ref={follow.cardRef}
      onFocus={follow.onFocus}
      onBlur={follow.onBlur}
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
      {card}
    </CardFrame>
  );
}
