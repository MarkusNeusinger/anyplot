/**
 * The data card of the agent chat, at its place in the thread: right after the
 * paste it came from (its `data` item, `ChatThread.tsx`), the data the
 * composer's message box sent (a pasted table or a file, with a note), as the
 * server parsed it: the 20-row preview and the parser's warnings, and a column
 * for each spec role (the server's defaults come preselected). A later paste
 * gets a card of its own below it, and this one stays as a stub of its shape;
 * a change to the data, an undo, `.to_long()` and the table and sheet pickers
 * update the card where it is. A table read from text waits in a card of its
 * own at its paste (`part: 'transcription'`).
 *
 * Two steps, data first. Step 1 ends with `.create_plot()` at the composer's end
 * (`Composer.tsx`), once every required role has a column: its click takes the
 * preview and the bindings as shown, confirms them on the server and starts the
 * plot. The card collapses with that click; the pinned header above the thread
 * (`PinnedHeader`), which stays in view on scroll, says `✓ data fits · N rows ·
 * M columns · version V` with `.show()`, which opens the card again at its
 * place without leaving step 2 and brings its top into view, and `.hide()`,
 * which closes it and goes back to where the user was (`useDataCardView`). The
 * plot buttons are the page's composer's, not the card's. A new parse, a
 * binding change, a change the assistant made to the data and an undo take the
 * page back to step 1 with the card open, because a plot of the wrong data is
 * wrong however good it looks; the server drops its confirmation for each of
 * them already. The header stays then and reads as a warning (`! check again ·
 * ...`, the phrase in bold on a surface tinted with the warning token), and its
 * `.show()` leads back to the card from anywhere in the thread, for example
 * after a data request sent from below the plot. The step line above the
 * composer names what dropped the confirmation, as the thread's notice
 * does. A table read from text that waits for its decision holds the page in
 * step 1 as well, whatever a turn's sync says, and the header names that
 * decision.
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
 * Every role of the spec gets a column choice (`bindingRows` in `bindings.ts`):
 * a single role one dropdown, a variadic family one per member plus one for
 * the next member. Required roles carry a `*`; the kinds a role accepts sit
 * under its name and the spec's description is its tooltip.
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
 * `.view_all()` next to the preview's label opens every row of the current
 * version in a read-only grid (`DataView.tsx`, loaded on demand): the
 * canonical `data.csv` with each value as the data holds it, to search, sort
 * and filter without changing the data. Read-only, so it opens while a step
 * runs and while the fan-out's panel is open; the focus returns to the button
 * when it closes.
 */

import { useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { type AgentSessionState, sessionBusy } from 'src/hooks/useAgentSession';
import { AgentApiError, type ConvertAnswer, tableChoice } from 'src/lib/agent';
import { DataCard } from 'src/sections/agent-chat/DataCard';
import { DataViewUnavailable } from 'src/sections/agent-chat/dataCardParts';
import { describeConvertFailure } from 'src/sections/agent-chat/messages';
import { DATA_LOCK_TEXT, DATA_SUMMARY_ID, DataCardShell } from 'src/sections/agent-chat/PinnedData';
import { cardSx } from 'src/sections/agent-chat/styles';
import {
  type ConvertedFile,
  convertedSource,
  sheetLabel,
} from 'src/sections/agent-chat/useChatAttachment';
import type { DataCardView } from 'src/sections/agent-chat/useDataCardView';

export { DATA_LOCK_TEXT, DATA_SUMMARY_ID, DataViewUnavailable };

interface DataPanelProps {
  state: AgentSessionState;
  /** The card's view, shared with the pinned header above the thread (`useDataCardView`). */
  view: DataCardView;
  /** Which item this card stands for: the stored data, or a table read from text that waits. */
  part: 'data' | 'transcription';
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
}

export function DataPanel({
  state,
  view,
  part,
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
}: DataPanelProps) {
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
    />
  );

  // A table read from text waits in a frame of its own at its paste; the stored data's card
  // above it stays as it is until `.use()`.
  if (part === 'transcription') {
    return transcription ? (
      // Off for the thread's live log, as the data card's shell is.
      <Box data-testid="transcription-item" ref={view.transcriptionRef} aria-live="off" sx={cardSx}>
        {card}
      </Box>
    ) : null;
  }
  // Step 2 without `.show()`: the card waits behind the pinned header.
  if (!view.open) return null;
  return (
    <DataCardShell view={view} locked={locked}>
      {card}
    </DataCardShell>
  );
}
