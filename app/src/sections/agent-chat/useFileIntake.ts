/**
 * File-intake state, refs, handlers and window drop guard for the agent chat's
 * data input (`DataPanel.tsx`, `DataCard.tsx`).
 *
 * Text files are read in the browser (`fileText.ts`); binary formats (Excel,
 * OpenDocument, Parquet, Feather, Arrow, NumPy) go to the server's sandbox via
 * `onConvert` and return as text for the box, keeping the workbook in memory
 * when it offers several sheets.
 */

import { useEffect, useRef, useState } from 'react';

import { AgentApiError, type ConvertAnswer, toBase64 } from 'src/lib/agent';
import { countOf } from 'src/sections/agent-chat/countOf';
import {
  countLines,
  type FileEncoding,
  type FileKind,
  type FileReading,
  readFile,
} from 'src/sections/agent-chat/fileText';
import {
  describeConvertFailure,
  describeConvertWarnings,
  describeFileRefusal,
  FILE_BUSY_TEXT,
  FILE_CONVERTING_TEXT,
  FILE_LOCKED_TEXT,
} from 'src/sections/agent-chat/messages';
import type { ConvertedFile, FileOutcome } from 'src/sections/agent-chat/useChatAttachment';

/** Whether a drag carries files (not text dragged from the page or another app). */
function dragHasFiles(transfer: DataTransfer | null): boolean {
  return !!transfer && Array.from(transfer.types ?? []).includes('Files');
}

export type { ConvertedFile };

/** A file read and waiting for the user's `.replace()` because the box holds text. */
export interface PendingFile {
  name: string;
  /** What travels as the dataset route's `source`: the name, and the sheet for a converted workbook. */
  source: string;
  text: string;
  lines: number;
  /** How it was read, after the name: `as utf-8`, `on the server: sheet ‹2024› of xlsx · …`. */
  read: string;
  /** What the server counted while it converted the file. */
  notes: string[];
  /** How many files came with it; only the first is read. */
  of: number;
  kind: string;
  encoding: FileEncoding | null;
  converted: ConvertedFile | null;
}

export type { FileOutcome };

/**
 * A sheet or array name as the page writes it: in single angle quotes, `‹Übersicht›`, so it
 * never nests inside the straight quotes around a file name (`from "Museen_2025.xlsx ·
 * sheet ‹Übersicht›"`; live test round 4 of 2026-10-15).
 */
function sheetLabel(sheet: string): string {
  return `‹${sheet}›`;
}

/** `Bericht.xlsx · sheet ‹2024›`: the source of a converted workbook names the sheet that was read. */
function convertedSource(name: string, answer: ConvertAnswer): string {
  if (answer.sheet === null) return name;
  return `${name} · ${answer.kind === 'npz' ? 'array' : 'sheet'} ${sheetLabel(answer.sheet)}`;
}

/** The "read ... " part of the line after a conversion. */
function convertedRead(answer: ConvertAnswer): string {
  const where =
    answer.sheet === null
      ? ''
      : ` ${answer.kind === 'npz' ? 'array' : 'sheet'} ${sheetLabel(answer.sheet)} of`;
  const shape = `${countOf(answer.rows, 'row')} × ${countOf(answer.columns, 'column')}`;
  return `on the server:${where} ${answer.kind} · ${shape}${answer.format === 'json' ? ' as JSON records' : ''}`;
}

export interface FileIntakeOptions {
  text: string;
  setText: (text: string) => void;
  ready: boolean;
  working: boolean;
  busy: boolean;
  locked: boolean;
  hasTranscription: boolean;
  onDiscardTranscription: () => void;
  onExpand: () => void;
  onConvert?: (dataBase64: string, sheet?: string) => Promise<ConvertAnswer>;
  onTrack?: (event: string, props?: Record<string, string | undefined>) => void;
}

export interface FileIntake {
  convertLine: string | null;
  converting: boolean;
  converted: ConvertedFile | null;
  source: string | null;
  dragOver: boolean;
  dropReady: boolean;
  fileNotice: { tone: 'ok' | 'error'; text: string } | null;
  pendingFile: PendingFile | null;
  convertStart: React.RefObject<number>;
  boxRef: React.RefObject<HTMLTextAreaElement | null>;
  parseButtonRef: React.RefObject<HTMLButtonElement | null>;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  replaceButtonRef: React.RefObject<HTMLButtonElement | null>;
  clearFile: () => void;
  handleTextChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  fillFromFile: (pending: PendingFile, outcome: FileOutcome) => void;
  handleSheet: (sheet: string) => void;
  handleKeep: () => void;
  handleDragEnter: (event: React.DragEvent) => void;
  handleDragOver: (event: React.DragEvent) => void;
  handleDragLeave: (event: React.DragEvent) => void;
  handleDrop: (event: React.DragEvent) => void;
  handlePaste: (event: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  handleChosen: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function useFileIntake({
  text,
  setText,
  ready,
  working,
  busy,
  locked,
  hasTranscription,
  onDiscardTranscription,
  onExpand,
  onConvert,
  onTrack,
}: FileIntakeOptions): FileIntake {
  // A binary file on its way to the server and back, as the line the box shows meanwhile
  // (`reading "x.parquet" on the server`); the box, `.open()` and `.parse()` wait for it.
  const [convertLine, setConvertLine] = useState<string | null>(null);
  const converting = convertLine !== null;
  // The converted file whose text is in the box, for the sheet picker; a text paste or an empty box drops it.
  const [converted, setConverted] = useState<ConvertedFile | null>(null);
  // The name of the file the box's text came from; typing keeps it, a text paste or an empty box drops it.
  const [source, setSource] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const dragDepth = useRef(0);
  // The line under the box after a file: what was read (a live status), or why it was not (an alert).
  const [fileNotice, setFileNotice] = useState<{ tone: 'ok' | 'error'; text: string } | null>(null);
  const [pendingFile, setPendingFile] = useState<PendingFile | null>(null);
  // Bumped by each fill, so the effect below hands the focus to `.parse()` even for the same text again.
  const [fills, setFills] = useState(0);
  const parseButtonRef = useRef<HTMLButtonElement>(null);
  const replaceButtonRef = useRef<HTMLButtonElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const boxRef = useRef<HTMLTextAreaElement>(null);
  // Counts file reads, so the result of a superseded one is dropped.
  const readSeq = useRef(0);
  // The read whose server conversion `convertLine` shows.
  const convertSeq = useRef(0);
  // When the box's current conversion began, set where it starts, so the overlay's count survives its remount.
  const convertStart = useRef(0);
  // The box's text as of the last render, for a file read that ends after an edit.
  const textRef = useRef(text);
  textRef.current = text;
  // Whether a dropped file would be taken now: not while a step runs or another file is being read.
  const dropReady = ready && !busy && !converting;

  const trackFile = (kind: string, encoding: FileEncoding | null, outcome: FileOutcome) =>
    onTrack?.('agent_data_file', { kind, encoding: encoding ?? 'none', outcome });

  const clearFile = () => {
    setSource(null);
    setConverted(null);
  };

  const handleTextChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(event.target.value);
    if (!event.target.value.trim()) {
      setSource(null);
      setConverted(null);
    }
    setFileNotice(null);
    // An edit after the question wins: `.replace()` would overwrite it.
    setPendingFile(null);
  };

  // The file's text goes into the box as it is; the user reads it and presses `.parse()`.
  const fillFromFile = (pending: PendingFile, outcome: FileOutcome) => {
    // A table read from the box's earlier text belongs to that text: it goes, so `.use()`
    // never stores it under this file's name and `.parse()` is free for the new text. The
    // card stays open, also when dropping the table takes the page back to step 2.
    if (hasTranscription) {
      onExpand();
      onDiscardTranscription();
    }
    setText(pending.text);
    setSource(pending.source);
    setConverted(pending.converted);
    setPendingFile(null);
    // Several files dropped at once: the first is read, and the line says so (owner, 2026-10-15).
    const several =
      pending.of > 1 ? `first of ${pending.of} files read — one file at a time · ` : '';
    const notes = pending.notes.length > 0 ? ` · ${pending.notes.join(' · ')}` : '';
    setFileNotice({
      tone: 'ok',
      text: `${several}read "${pending.name}" ${pending.read} · ${countOf(pending.lines, 'line')}${notes} · check it, then .parse()`,
    });
    setFills(count => count + 1);
    trackFile(pending.kind, pending.encoding, outcome);
  };

  // Into an empty box, or held for `.replace()` when the box has text the user did not get from this
  // very conversion (a sheet switch over the untouched text of the same file replaces it at once).
  const offerFile = (pending: PendingFile, outcome: FileOutcome = 'filled') => {
    const current = textRef.current;
    if (current.trim() && !(outcome === 'sheet' && converted && current === converted.text)) {
      setFileNotice(null);
      setPendingFile(pending);
      return;
    }
    fillFromFile(pending, outcome);
  };

  // A binary format goes to the server (in the renderer's sandbox) and comes back as text for the box.
  const convertOnServer = async (
    file: { name: string; base64: string; browserKind: FileKind },
    of: number,
    seq: number,
    sheet?: string
  ) => {
    if (!onConvert) {
      setFileNotice({ tone: 'error', text: describeFileRefusal(file.name, 'binary') });
      trackFile(file.browserKind, null, 'refused');
      return;
    }
    const line = sheet
      ? `reading the sheet ${sheetLabel(sheet)} of "${file.name}" on the server`
      : `reading "${file.name}" on the server`;
    convertSeq.current = seq;
    convertStart.current = Date.now();
    setConvertLine(line);
    setFileNotice({ tone: 'ok', text: `${line} …` });
    let answer: ConvertAnswer;
    try {
      answer = await onConvert(file.base64, sheet);
    } catch (err) {
      if (seq !== readSeq.current) return;
      const failure =
        err instanceof AgentApiError ? err : new AgentApiError(0, 'unreachable', null);
      setFileNotice({
        tone: 'error',
        text: describeConvertFailure(
          file.name,
          failure.code,
          failure.measured,
          failure.limit,
          failure.ref,
          file.browserKind,
          failure.damage
        ),
      });
      trackFile(file.browserKind, null, failure.code.startsWith('file_') ? 'refused' : 'failed');
      return;
    } finally {
      // Only the conversion that set the line clears it; a later read that converted
      // nothing (refused, or a text file) must not leave the box waiting forever.
      if (seq === convertSeq.current) setConvertLine(null);
    }
    if (seq !== readSeq.current) return;
    offerFile(
      {
        name: file.name,
        source: convertedSource(file.name, answer),
        text: answer.text,
        lines: countLines(answer.text),
        read: convertedRead(answer),
        notes: describeConvertWarnings(answer.warnings, answer.dropped),
        of,
        kind: answer.kind,
        encoding: null,
        converted: {
          ...file,
          kind: answer.kind,
          sheet: answer.sheet,
          sheets: answer.sheets,
          sheetCount: answer.sheet_count,
          text: answer.text,
        },
      },
      sheet ? 'sheet' : 'filled'
    );
  };

  // A drop, `.open()` or a pasted file: refused while the session works, read in the
  // browser, then into an empty box, or held for `.replace()` when the box has text.
  const handleFile = async (file: File, of = 1) => {
    // A file the server still reads keeps its place: the next one is refused, not swapped in.
    if (converting) {
      setFileNotice({ tone: 'error', text: FILE_CONVERTING_TEXT });
      trackFile('unknown', null, 'busy');
      return;
    }
    // Only the latest file counts: a slow read of an earlier one must not land after it.
    readSeq.current += 1;
    const seq = readSeq.current;
    setPendingFile(null);
    if (!ready || busy) {
      setFileNotice({
        tone: 'error',
        text: locked && !working ? FILE_LOCKED_TEXT : FILE_BUSY_TEXT,
      });
      trackFile('unknown', null, 'busy');
      return;
    }
    let reading: FileReading;
    try {
      reading = await readFile(file);
    } catch {
      if (seq !== readSeq.current) return;
      setFileNotice({ tone: 'error', text: describeFileRefusal(file.name, 'unreadable') });
      trackFile('unknown', null, 'unreadable');
      return;
    }
    if (seq !== readSeq.current) return;
    if (!reading.ok && reading.reason === 'convert') {
      await convertOnServer(
        { name: file.name, base64: toBase64(reading.bytes), browserKind: reading.kind },
        of,
        seq
      );
      return;
    }
    if (!reading.ok) {
      const code = reading.reason === 'binary' ? reading.kind : reading.reason;
      setFileNotice({ tone: 'error', text: describeFileRefusal(file.name, code) });
      trackFile(
        reading.kind,
        reading.encoding,
        reading.reason === 'too_large' || reading.reason === 'too_large_binary'
          ? 'too_large'
          : 'refused'
      );
      return;
    }
    offerFile({
      name: file.name,
      source: file.name,
      text: reading.text,
      lines: reading.lines,
      read: `as ${reading.encoding}`,
      notes: [],
      of,
      kind: 'text',
      encoding: reading.encoding,
      converted: null,
    });
  };

  // The sheet picker: the same file again, another sheet, read on the server.
  const handleSheet = (sheet: string) => {
    if (!converted || sheet === converted.sheet || !ready || busy || converting) return;
    readSeq.current += 1;
    setPendingFile(null);
    void convertOnServer(converted, 1, readSeq.current, sheet);
  };

  // `.keep()`: the box stays as it was, and so does the focus's place in it, not on the page.
  const handleKeep = () => {
    if (pendingFile) trackFile(pendingFile.kind, pendingFile.encoding, 'kept');
    setPendingFile(null);
    boxRef.current?.focus();
  };

  // `.parse()` takes the focus after a fill (the box, when `.parse()` cannot take it),
  // `.replace()` when a file waits for it.
  useEffect(() => {
    if (fills === 0) return;
    const parse = parseButtonRef.current;
    if (parse && !parse.disabled) parse.focus();
    else boxRef.current?.focus();
  }, [fills]);
  useEffect(() => {
    if (pendingFile) replaceButtonRef.current?.focus();
  }, [pendingFile]);

  // While the chat is mounted, a file dropped next to the box must not make the
  // browser leave the page to open it. Text drags keep their default.
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
    // Stop here, so the page's guard above does not mark the box as no drop target.
    event.stopPropagation();
    event.dataTransfer.dropEffect = dropReady ? 'copy' : 'none';
  };

  const handleDragLeave = (event: React.DragEvent) => {
    if (!dragHasFiles(event.dataTransfer)) return;
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setDragOver(false);
  };

  const handleDrop = (event: React.DragEvent) => {
    if (!dragHasFiles(event.dataTransfer)) return;
    event.preventDefault();
    dragDepth.current = 0;
    setDragOver(false);
    const { files } = event.dataTransfer;
    if (files[0]) void handleFile(files[0], files.length);
  };

  // A pasted file (copied in the file manager) is read like a dropped one. Excel and
  // Word put a picture of the cells next to their text: the text wins over an image.
  const handlePaste = (event: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const files = Array.from(event.clipboardData?.files ?? []);
    const pastedText = event.clipboardData?.getData('text/plain') ?? '';
    const file =
      files.find(candidate => !candidate.type.startsWith('image/')) ??
      (pastedText ? undefined : files[0]);
    if (file) {
      event.preventDefault();
      void handleFile(file);
      return;
    }
    // Pasted text is not the file's any more: its name, its line, its sheet picker and a file
    // waiting for `.replace()` (which would overwrite the paste) all go.
    setSource(null);
    setConverted(null);
    setFileNotice(null);
    setPendingFile(null);
  };

  const handleChosen = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    // Cleared, so choosing the same file again fires a change.
    event.target.value = '';
    if (file) void handleFile(file);
  };

  return {
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
  };
}
