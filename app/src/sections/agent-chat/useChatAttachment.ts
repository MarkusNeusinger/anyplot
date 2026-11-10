/**
 * The attachment of the chat's one message box: a table pasted into the box, a file opened with
 * `.open()`, dropped on the chat or pasted as a file. It waits as a chip in the composer until
 * Enter (or the `↵` a touch screen shows in the box) posts it to the dataset route with the typed
 * text as its note; the text of
 * a paste never enters the textarea, and nothing of it goes to browser storage.
 *
 * A paste is routed first (`routeInput.ts`): a table becomes the attachment, anything else the
 * browser pastes into the box as typed text. Browsers that hide the pasted text from the paste
 * event (iOS Safari may) insert it and report `insertFromPaste` on the input event: the same
 * routing runs on the inserted part then, and only for that input type, so typing and an input
 * method's composition never become an attachment while the user types. Enter routes the box's
 * text once more when no attachment waits (`attachTyped`): a table typed by hand, or pasted where
 * no paste event said so, goes to the dataset route at once, as a paste of it would.
 *
 * Text files are read in the browser (`fileText.ts`); binary formats (Excel, OpenDocument,
 * Parquet, Feather, Arrow, NumPy) go to the server's sandbox (`onConvert`) and come back as
 * text, while the chip says it reads. Every new attachment, and ×, supersedes a read still in
 * flight: its answer is dropped when it arrives. A file is refused while a step runs or the
 * fan-out's panel copies the data, and while another file is still read on the server; a text
 * paste attaches at any time, and Enter waits for the session.
 */

import { useEffect, useRef, useState } from 'react';

import {
  AgentApiError,
  type ConvertAnswer,
  MAX_DATASET_BYTES,
  toBase64,
  utf8Bytes,
} from 'src/lib/agent';
import { countOf } from 'src/sections/agent-chat/countOf';
import {
  countLines,
  type FileEncoding,
  type FileKind,
  type FileReading,
  readFile,
} from 'src/sections/agent-chat/fileText';
import { spannedTable } from 'src/sections/agent-chat/htmlTable';
import {
  describeConvertFailure,
  describeConvertWarnings,
  describeFileRefusal,
  FILE_BUSY_TEXT,
  FILE_CONVERTING_TEXT,
  FILE_LOCKED_TEXT,
} from 'src/sections/agent-chat/messages';
import { routeInput } from 'src/sections/agent-chat/routeInput';

/** What happened to a dropped, chosen or pasted file, for `agent_data_file`. */
export type FileOutcome =
  | 'filled'
  | 'replaced'
  | 'kept'
  | 'attached'
  | 'removed'
  | 'refused'
  | 'too_large'
  | 'busy'
  | 'unreadable'
  | 'failed'
  | 'sheet';

/** A binary file the server converted: kept in the browser for the sheet picker, which converts it again. */
export interface ConvertedFile {
  name: string;
  base64: string;
  /** The browser's reading of the format, for the analytics of a failed re-conversion. */
  browserKind: FileKind;
  /** The server's reading of the format (`xlsx`, `ods`, `parquet`, ...). */
  kind: string;
  sheet: string | null;
  sheets: string[];
  sheetCount: number;
  /** The text the conversion produced, to tell whether the user edited it since. */
  text: string;
}

/**
 * The most non-empty lines a pasted table may have: the server reads at most 20,000 rows
 * (`schemas.MAX_ROWS`), and a header and a few notes come with them. One JSON document is
 * exempt: a pretty-printed record spans many lines, and the byte cap and the server's row cap
 * remain. JSON Lines is not: each of its lines is a row.
 */
export const MAX_ATTACHMENT_LINES = 20_050;

/** Where an attachment is: read on the server, waiting for Enter, too large, posted, or refused. */
export type AttachmentStatus = 'reading' | 'ready' | 'over_cap' | 'sending' | 'failed';

export interface Attachment {
  /** Counts attachments, so an answer for an earlier one never touches a later one. */
  id: number;
  /** `typed`: the box's own text, a table typed or inserted without a paste event, sent with Enter. */
  via: 'paste' | 'file' | 'typed';
  /** The text the dataset route reads; empty while a file is read on the server. */
  text: string;
  /** The file's name, for the chip; null for a paste. */
  name: string | null;
  /** The dataset route's `source`: the file's name, and the sheet of a converted workbook. */
  source?: string;
  lines: number;
  bytes: number;
  /** What the server counted while it converted the file, and how many files came with it. */
  notes: string[];
  /** A converted binary file, kept for the sheet picker, which converts it again. */
  converted: ConvertedFile | null;
  /** Analytics only: the format and the browser's reading of the encoding. */
  kind: string;
  encoding: FileEncoding | null;
  status: AttachmentStatus;
  /** Why the dataset route did not take it, the alert under a red chip. */
  error: string | null;
  /** While a file is read on the server, what the chip says. */
  readingLine: string | null;
}

/** A sheet or array name in single angle quotes, so it never nests inside a file name's straight quotes. */
export function sheetLabel(sheet: string): string {
  return `‹${sheet}›`;
}

/** `Bericht.xlsx · sheet ‹2024›`: the source of a converted workbook names the sheet that was read. */
export function convertedSource(name: string, answer: ConvertAnswer): string {
  if (answer.sheet === null) return name;
  return `${name} · ${answer.kind === 'npz' ? 'array' : 'sheet'} ${sheetLabel(answer.sheet)}`;
}

/** The "read ... " part of the line after a conversion. */
export function convertedRead(answer: ConvertAnswer): string {
  const where =
    answer.sheet === null
      ? ''
      : ` ${answer.kind === 'npz' ? 'array' : 'sheet'} ${sheetLabel(answer.sheet)} of`;
  const shape = `${countOf(answer.rows, 'row')} × ${countOf(answer.columns, 'column')}`;
  return `on the server:${where} ${answer.kind} · ${shape}${answer.format === 'json' ? ' as JSON records' : ''}`;
}

/** Whether the text is one JSON array or object, as a whole: a `[Source: X]` above a CSV is no JSON. */
function isJsonDocument(text: string): boolean {
  const trimmed = text.trim();
  if (!/^[[{]/.test(trimmed) || !/[\]}]$/.test(trimmed)) return false;
  try {
    JSON.parse(trimmed);
    return true;
  } catch {
    return false;
  }
}

/** Whether a pasted text is too large for the dataset route: the byte cap, and the row cap outside JSON. */
export function overCap(text: string): boolean {
  if (utf8Bytes(text) > MAX_DATASET_BYTES) return true;
  return countLines(text) > MAX_ATTACHMENT_LINES && !isJsonDocument(text);
}

/** Whether a drag carries files (not text dragged from the page or another app). */
function dragHasFiles(transfer: DataTransfer | null): boolean {
  return !!transfer && Array.from(transfer.types ?? []).includes('Files');
}

/**
 * The part of a textarea's new value an input inserted: what lies between the common start and
 * the common end of the old and the new value.
 */
export function insertedText(before: string, after: string): string {
  let start = 0;
  while (start < before.length && start < after.length && before[start] === after[start])
    start += 1;
  let end = 0;
  while (
    end < before.length - start &&
    end < after.length - start &&
    before[before.length - 1 - end] === after[after.length - 1 - end]
  ) {
    end += 1;
  }
  return after.slice(start, after.length - end);
}

export interface ChatAttachmentOptions {
  /** The session is open and answers. */
  ready: boolean;
  /** A turn, a parse or another step runs: a file waits. */
  working: boolean;
  /** The admin fan-out's panel copies this data: a file waits until it closes. */
  locked: boolean;
  /** The session holds data, which a paste would replace: the routing asks more of a pair list. */
  hasData?: boolean;
  onConvert?: (dataBase64: string, sheet?: string) => Promise<ConvertAnswer>;
  onTrack?: (event: string, props?: Record<string, string | undefined>) => void;
}

export interface ChatAttachment {
  attachment: Attachment | null;
  /** Why a file was not attached (a running step, a format not read here): an alert in the composer. */
  notice: string | null;
  dragOver: boolean;
  /** Whether a dropped or opened file would be taken now. */
  dropReady: boolean;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  /** The routed text of a paste. */
  attachText: (text: string) => void;
  /**
   * The box's text on Enter, routed like a paste: the attachment it became when it is a table, to
   * send at once, or null for a message.
   */
  attachTyped: (text: string) => Attachment | null;
  /**
   * An attachment back as it was sent, under a new id: the file or the long text a discarded
   * table was read from, which the box could not send as typed text.
   */
  reattach: (previous: Attachment) => void;
  /** ×: the attachment goes, and a read still in flight with it. */
  remove: () => void;
  /** The send's outcome for the attachment it posted (`id`): it goes, or it stays with a status. */
  settle: (id: number, next: 'cleared' | 'ready' | 'sending' | { error: string }) => void;
  /** The textarea's paste: true when the paste became an attachment and the box takes nothing. */
  handlePaste: (event: React.ClipboardEvent<HTMLTextAreaElement>) => boolean;
  /**
   * The textarea's input, for a browser that hid the pasted text from the paste event: true
   * when the inserted part became an attachment and the box keeps its value from before.
   */
  handleInput: (event: React.ChangeEvent<HTMLTextAreaElement>, before: string) => boolean;
  handleDragEnter: (event: React.DragEvent) => void;
  handleDragOver: (event: React.DragEvent) => void;
  handleDragLeave: (event: React.DragEvent) => void;
  handleDrop: (event: React.DragEvent) => void;
  handleChosen: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function useChatAttachment({
  ready,
  working,
  locked,
  hasData = false,
  onConvert,
  onTrack,
}: ChatAttachmentOptions): ChatAttachment {
  const [attachment, setAttachment] = useState<Attachment | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const dragDepth = useRef(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Counts attachments and reads: an answer for a superseded one is dropped.
  const seq = useRef(0);
  // The paste event routed this paste's text already; the browser's input event that inserts it
  // must not route it a second time.
  const pasteRouted = useRef(false);
  const reading = attachment?.status === 'reading';
  const dropReady = ready && !working && !locked && !reading;

  const trackFile = (kind: string, encoding: FileEncoding | null, outcome: FileOutcome) => {
    onTrack?.('agent_data_file', { kind, encoding: encoding ?? 'none', outcome });
    if (outcome === 'attached') onTrack?.('agent_input_routed', { as: 'data', via: 'file' });
  };

  const next = () => {
    seq.current += 1;
    return seq.current;
  };

  const attachText = (text: string, via: 'paste' | 'typed' = 'paste'): Attachment => {
    const created: Attachment = {
      id: next(),
      via,
      text,
      name: null,
      lines: countLines(text),
      bytes: utf8Bytes(text),
      notes: [],
      converted: null,
      kind: 'text',
      encoding: null,
      status: overCap(text) ? 'over_cap' : 'ready',
      error: null,
      readingLine: null,
    };
    setNotice(null);
    setAttachment(created);
    return created;
  };

  // Only a paste was routed before Enter: a table typed by hand, or pasted where the browser
  // reported no paste, went out as a message the assistant cannot read data from. Only `data` is
  // counted: every typed message is a `message`, which would only drown the tuning signal.
  const attachTyped = (text: string) => {
    if (routeInput(text, { hasData }) !== 'data') return null;
    onTrack?.('agent_input_routed', { as: 'data', via: 'typed' });
    return attachText(text, 'typed');
  };

  const reattach = (previous: Attachment) => {
    const id = next();
    setNotice(null);
    setAttachment({
      ...previous,
      id,
      status: overCap(previous.text) ? 'over_cap' : 'ready',
      error: null,
      readingLine: null,
    });
  };

  const remove = () => {
    // A read in flight belongs to this attachment: its answer must not bring it back.
    next();
    setNotice(null);
    if (attachment?.via === 'file') trackFile(attachment.kind, attachment.encoding, 'removed');
    setAttachment(null);
  };

  const settle: ChatAttachment['settle'] = (id, outcome) => {
    setAttachment(current => {
      if (!current || current.id !== id) return current;
      if (outcome === 'cleared') return null;
      if (outcome === 'ready') return { ...current, status: 'ready', error: null };
      if (outcome === 'sending') return { ...current, status: 'sending', error: null };
      return { ...current, status: 'failed', error: outcome.error };
    });
  };

  // A binary format goes to the server (in the renderer's sandbox) and comes back as text.
  const convertOnServer = async (
    file: { name: string; base64: string; browserKind: FileKind },
    of: number,
    id: number,
    sheet?: string
  ) => {
    if (!onConvert) {
      setAttachment(null);
      setNotice(describeFileRefusal(file.name, 'binary'));
      trackFile(file.browserKind, null, 'refused');
      return;
    }
    const readingLine = sheet
      ? `reading the sheet ${sheetLabel(sheet)} of "${file.name}" on the server`
      : `reading "${file.name}" on the server`;
    setAttachment({
      id,
      via: 'file',
      text: '',
      name: file.name,
      source: file.name,
      lines: 0,
      bytes: 0,
      notes: [],
      converted: null,
      kind: file.browserKind,
      encoding: null,
      status: 'reading',
      error: null,
      readingLine,
    });
    let answer: ConvertAnswer;
    try {
      answer = await onConvert(file.base64, sheet);
    } catch (err) {
      if (id !== seq.current) return;
      const failure =
        err instanceof AgentApiError ? err : new AgentApiError(0, 'unreachable', null);
      setAttachment(null);
      setNotice(
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
      trackFile(file.browserKind, null, failure.code.startsWith('file_') ? 'refused' : 'failed');
      return;
    }
    if (id !== seq.current) return;
    const several = of > 1 ? [`first of ${of} files read — one file at a time`] : [];
    setAttachment({
      id,
      via: 'file',
      text: answer.text,
      name: file.name,
      source: convertedSource(file.name, answer),
      lines: countLines(answer.text),
      bytes: utf8Bytes(answer.text),
      notes: [
        convertedRead(answer),
        ...describeConvertWarnings(answer.warnings, answer.dropped),
        ...several,
      ],
      converted: {
        ...file,
        kind: answer.kind,
        sheet: answer.sheet,
        sheets: answer.sheets,
        sheetCount: answer.sheet_count,
        text: answer.text,
      },
      kind: answer.kind,
      encoding: null,
      status: overCap(answer.text) ? 'over_cap' : 'ready',
      error: null,
      readingLine: null,
    });
    trackFile(answer.kind, null, 'attached');
  };

  // A drop, `.open()` or a pasted file: refused while the session works, read in the browser or
  // on the server, then the attachment.
  const handleFile = async (file: File, of = 1) => {
    // A file the server still reads keeps its place: the next one is refused, not swapped in.
    if (reading) {
      setNotice(FILE_CONVERTING_TEXT);
      trackFile('unknown', null, 'busy');
      return;
    }
    if (!ready || working || locked) {
      setNotice(locked && !working ? FILE_LOCKED_TEXT : FILE_BUSY_TEXT);
      trackFile('unknown', null, 'busy');
      return;
    }
    const id = next();
    setNotice(null);
    let read: FileReading;
    try {
      read = await readFile(file);
    } catch {
      if (id !== seq.current) return;
      setNotice(describeFileRefusal(file.name, 'unreadable'));
      trackFile('unknown', null, 'unreadable');
      return;
    }
    if (id !== seq.current) return;
    if (!read.ok && read.reason === 'convert') {
      await convertOnServer(
        { name: file.name, base64: toBase64(read.bytes), browserKind: read.kind },
        of,
        id
      );
      return;
    }
    if (!read.ok) {
      const code = read.reason === 'binary' ? read.kind : read.reason;
      setNotice(describeFileRefusal(file.name, code));
      trackFile(
        read.kind,
        read.encoding,
        read.reason === 'too_large' || read.reason === 'too_large_binary' ? 'too_large' : 'refused'
      );
      return;
    }
    setAttachment({
      id,
      via: 'file',
      text: read.text,
      name: file.name,
      source: file.name,
      lines: read.lines,
      bytes: utf8Bytes(read.text),
      notes: of > 1 ? [`first of ${of} files read — one file at a time`] : [],
      converted: null,
      kind: 'text',
      encoding: read.encoding,
      status: overCap(read.text) ? 'over_cap' : 'ready',
      error: null,
      readingLine: null,
    });
    trackFile('text', read.encoding, 'attached');
  };

  // While the chat is mounted, a file dropped beside its drop target must not make the browser
  // leave the page to open it. Text drags keep their default.
  useEffect(() => {
    const block = (event: DragEvent) => {
      if (!dragHasFiles(event.dataTransfer)) return;
      event.preventDefault();
      if (event.type === 'dragover' && event.dataTransfer) event.dataTransfer.dropEffect = 'none';
    };
    window.addEventListener('dragover', block);
    window.addEventListener('drop', block);
    return () => {
      window.removeEventListener('dragover', block);
      window.removeEventListener('drop', block);
    };
  }, []);

  const handleDragEnter = (event: React.DragEvent) => {
    if (!dragHasFiles(event.dataTransfer)) return;
    event.preventDefault();
    dragDepth.current += 1;
    setDragOver(true);
  };

  const handleDragOver = (event: React.DragEvent) => {
    if (!dragHasFiles(event.dataTransfer)) return;
    event.preventDefault();
    // Stop here, so the window's guard does not mark the chat as no drop target.
    event.stopPropagation();
    event.dataTransfer.dropEffect = dropReady ? 'copy' : 'none';
  };

  const handleDragLeave = (event: React.DragEvent) => {
    if (!dragHasFiles(event.dataTransfer)) return;
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setDragOver(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    // A drop target inside the chat that took the file already wins.
    if (event.defaultPrevented || !dragHasFiles(event.dataTransfer)) return;
    event.preventDefault();
    dragDepth.current = 0;
    setDragOver(false);
    const { files } = event.dataTransfer;
    if (files[0]) void handleFile(files[0], files.length);
  };

  // A pasted file (copied in the file manager) is read like a dropped one; Excel and Word put a
  // picture of the cells next to their text, and the text wins over an image. Pasted text that
  // routes as data becomes the attachment; any other text is the box's.
  const handlePaste = (event: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const files = Array.from(event.clipboardData?.files ?? []);
    const pastedText = event.clipboardData?.getData('text/plain') ?? '';
    const file =
      files.find(candidate => !candidate.type.startsWith('image/')) ??
      (pastedText ? undefined : files[0]);
    if (file) {
      event.preventDefault();
      void handleFile(file);
      return true;
    }
    // A web table with grouped columns: its HTML keeps the spans that the plain text loses.
    const spanned = pastedText
      ? spannedTable(event.clipboardData?.getData('text/html') ?? '')
      : null;
    const text =
      spanned !== null && routeInput(spanned, { hasData }) === 'data' ? spanned : pastedText;
    const taken = routePaste(text, () => event.preventDefault());
    // Text the box takes: the browser inserts it and reports `insertFromPaste` next.
    pasteRouted.current = !taken && pastedText !== '';
    return taken;
  };

  // How a paste was routed, for tuning the rules (`agent_input_routed`); a data paste attaches.
  const routePaste = (text: string, take: () => void) => {
    const route = routeInput(text, { hasData });
    if (route) onTrack?.('agent_input_routed', { as: route, via: 'paste' });
    if (route !== 'data') return false;
    take();
    attachText(text);
    return true;
  };

  const handleInput = (event: React.ChangeEvent<HTMLTextAreaElement>, before: string) => {
    const native = event.nativeEvent as InputEvent | undefined;
    // Any input ends the paste the paste event routed, so a later one is routed on its own.
    const routed = pasteRouted.current;
    pasteRouted.current = false;
    if (native?.inputType !== 'insertFromPaste' || routed) return false;
    // Safari hands the pasted text over on the input event itself; elsewhere the box's change
    // tells it.
    const handed = native.dataTransfer?.getData('text/plain');
    return routePaste(handed || insertedText(before, event.target.value), () => undefined);
  };

  const handleChosen = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    // Cleared, so choosing the same file again fires a change.
    event.target.value = '';
    if (file) void handleFile(file);
  };

  return {
    attachment,
    notice,
    dragOver,
    dropReady,
    fileInputRef,
    attachText,
    attachTyped,
    reattach,
    remove,
    settle,
    handlePaste,
    handleInput,
    handleDragEnter,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleChosen,
  };
}
