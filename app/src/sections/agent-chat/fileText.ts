/**
 * Reading a dropped, chosen or pasted file into the data card's text box.
 *
 * This is UX only: the browser says early what it cannot read, and the server
 * stays the trust boundary (the text goes through the ordinary paste route,
 * with its size cap, control-character refusal, pre-filter and judges).
 *
 * The order: the raw size against `MAX_FILE_BYTES` before anything is read;
 * then the magic bytes of the binary formats people drop (spreadsheets,
 * Parquet, Arrow, NumPy, HDF5, pickle, PDF, archives), each with its own
 * answer; then the text encoding: a byte order mark (UTF-8, UTF-16LE as in
 * Excel's "Unicode text" export, UTF-16BE), NUL bytes on every other byte as
 * UTF-16 without one, strict UTF-8, else windows-1252. Not ISO-8859-1: that
 * would turn the bytes 0x80–0x9F (`€`, `„`, `’` in windows-1252) into C1
 * control characters, which the server's parser refuses. A decoded text with
 * a NUL, or with more than 1 % control characters other than tab and line
 * breaks, is binary all the same. Last, the decoded text's UTF-8 length
 * against the paste cap (`MAX_DATASET_BYTES`).
 */

import { MAX_DATASET_BYTES, utf8Bytes } from 'src/lib/agent';

/** The largest file the browser reads at all: UTF-16 doubles the bytes of a 1 MB text, and a margin. */
export const MAX_FILE_BYTES = 4 * 1024 * 1024;

/** What a file is, as far as its first bytes and its name tell. */
export type FileKind =
  | 'text'
  | 'spreadsheet'
  | 'parquet'
  | 'arrow'
  | 'numpy'
  | 'hdf5'
  | 'pickle'
  | 'pdf'
  | 'archive'
  | 'binary';

export type FileEncoding = 'utf-8' | 'utf-8-bom' | 'utf-16le' | 'utf-16be' | 'windows-1252';

/** Why a file did not go into the box. */
export type FileRefusal = 'binary' | 'too_large' | 'empty';

export type FileReading =
  | { ok: true; text: string; encoding: FileEncoding; lines: number }
  | { ok: false; reason: FileRefusal; kind: FileKind; encoding: FileEncoding | null };

/**
 * The file picker's filter: MIME types first (iOS and Android filter by them),
 * then the extensions. Windows reports a `.csv` as `application/vnd.ms-excel`,
 * so that type is in the list; an old `.xls` it lets through gets the
 * spreadsheet answer from its magic bytes.
 */
export const FILE_ACCEPT = [
  'text/csv',
  'text/comma-separated-values',
  'application/csv',
  'text/tab-separated-values',
  'text/plain',
  'application/json',
  'application/vnd.ms-excel',
  '.csv',
  '.tsv',
  '.tab',
  '.txt',
  '.json',
  '.dat',
  '.psv',
].join(',');

const ascii = (text: string) => Array.from(text, char => char.charCodeAt(0));

/** The signatures, longest first where one is the prefix of another. */
const MAGIC: ReadonlyArray<readonly [number[], FileKind]> = [
  [[0x50, 0x4b, 0x03, 0x04], 'archive'], // zip: xlsx, ods, docx, a plain zip
  [[0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1], 'binary'], // OLE: xls, doc
  [ascii('PAR1'), 'parquet'],
  [ascii('ARROW1'), 'arrow'], // Arrow IPC file, Feather v2
  [[0x93, ...ascii('NUMPY')], 'numpy'],
  [[0x89, ...ascii('HDF\r\n'), 0x1a, 0x0a], 'hdf5'],
  [ascii('%PDF'), 'pdf'],
  [[0x1f, 0x8b], 'archive'], // gzip
  [[0x37, 0x7a, 0xbc, 0xaf, 0x27, 0x1c], 'archive'], // 7z
];

const SPREADSHEET_NAME = /\.(xlsx|xlsm|xlsb|xls|ods|numbers)$/i;
const SPREADSHEET_TYPE = /spreadsheet|excel|sheet/i;

function startsWith(bytes: Uint8Array, signature: readonly number[]): boolean {
  return (
    bytes.length >= signature.length && signature.every((byte, index) => bytes[index] === byte)
  );
}

/** The binary format the first bytes name, or null for anything that may be text. */
export function sniffBinary(bytes: Uint8Array, name = '', type = ''): FileKind | null {
  // Pickle protocols 2 to 5 open with 0x80 and the protocol number; `€` and a control in windows-1252 never do.
  if (bytes.length >= 2 && bytes[0] === 0x80 && bytes[1] >= 2 && bytes[1] <= 5) return 'pickle';
  for (const [signature, kind] of MAGIC) {
    if (!startsWith(bytes, signature)) continue;
    // A zip or an OLE container is a spreadsheet when its name or its type says so.
    if (
      (signature[0] === 0x50 || signature[0] === 0xd0) &&
      (SPREADSHEET_NAME.test(name) || SPREADSHEET_TYPE.test(type))
    ) {
      return 'spreadsheet';
    }
    return kind;
  }
  return null;
}

/** UTF-16 without a byte order mark: NUL bytes on the odd (LE) or the even (BE) positions of the first 4 KB. */
function utf16Pattern(bytes: Uint8Array): 'utf-16le' | 'utf-16be' | null {
  const pairs = Math.min(bytes.length, 4096) >> 1;
  if (pairs < 2) return null;
  let even = 0;
  let odd = 0;
  for (let index = 0; index < pairs * 2; index += 2) {
    if (bytes[index] === 0) even += 1;
    if (bytes[index + 1] === 0) odd += 1;
  }
  if (odd >= pairs * 0.3 && even <= pairs * 0.02) return 'utf-16le';
  if (even >= pairs * 0.3 && odd <= pairs * 0.02) return 'utf-16be';
  return null;
}

function decodeWith(label: string, bytes: Uint8Array, fatal: boolean): string | null {
  try {
    return new TextDecoder(label, { fatal }).decode(bytes);
  } catch {
    return null;
  }
}

/** The text of `bytes` and the encoding it was read with, or null when no encoding reads it. */
export function decodeText(bytes: Uint8Array): { text: string; encoding: FileEncoding } | null {
  if (startsWith(bytes, [0xef, 0xbb, 0xbf])) {
    // The decoder drops the mark itself. Strict, as without a mark: a broken sequence is
    // refused rather than turned into `�` in a cell.
    const text = decodeWith('utf-8', bytes, true);
    return text === null ? null : { text, encoding: 'utf-8-bom' };
  }
  const utf16: 'utf-16le' | 'utf-16be' | null = startsWith(bytes, [0xff, 0xfe])
    ? 'utf-16le'
    : startsWith(bytes, [0xfe, 0xff])
      ? 'utf-16be'
      : utf16Pattern(bytes);
  if (utf16) {
    const text = decodeWith(utf16, bytes, true);
    return text === null ? null : { text, encoding: utf16 };
  }
  const utf8 = decodeWith('utf-8', bytes, true);
  if (utf8 !== null) return { text: utf8, encoding: 'utf-8' };
  const legacy = decodeWith('windows-1252', bytes, false);
  return legacy === null ? null : { text: legacy, encoding: 'windows-1252' };
}

/** Whether decoded text reads as binary: any NUL, or more than 1 % C0, DEL or C1 controls besides tab and line breaks. */
export function looksBinary(text: string): boolean {
  if (text.includes('\u0000')) return true;
  let controls = 0;
  for (let index = 0; index < text.length; index += 1) {
    const code = text.charCodeAt(index);
    if (code === 0x09 || code === 0x0a || code === 0x0d) continue;
    if (code < 0x20 || (code >= 0x7f && code <= 0x9f)) controls += 1;
  }
  return controls > text.length * 0.01;
}

/** The non-empty lines of a text, for the line that says what was read. */
export function countLines(text: string): number {
  return text.split(/\r\n|\r|\n/).filter(line => line.trim()).length;
}

/** Read a file's bytes into text for the box, or say why not. */
export function readBytes(bytes: Uint8Array, name = '', type = ''): FileReading {
  const kind = sniffBinary(bytes, name, type);
  if (kind) return { ok: false, reason: 'binary', kind, encoding: null };
  const decoded = decodeText(bytes);
  if (!decoded || looksBinary(decoded.text)) {
    return { ok: false, reason: 'binary', kind: 'binary', encoding: decoded?.encoding ?? null };
  }
  const { text, encoding } = decoded;
  if (!text.trim()) return { ok: false, reason: 'empty', kind: 'text', encoding };
  if (utf8Bytes(text) > MAX_DATASET_BYTES) {
    return { ok: false, reason: 'too_large', kind: 'text', encoding };
  }
  return { ok: true, text, encoding, lines: countLines(text) };
}

function fileBytes(file: Blob): Promise<ArrayBuffer> {
  if (typeof file.arrayBuffer === 'function') return file.arrayBuffer();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = () => reject(reader.error ?? new Error('read failed'));
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Read a `File` for the box: the first bytes for a binary format (a 20 MB
 * workbook gets the spreadsheet answer, not "too large"), then the size, then
 * `readBytes`. Rejects only when the browser cannot read the file.
 */
export async function readFile(file: File): Promise<FileReading> {
  const head = new Uint8Array(await fileBytes(file.slice(0, 16)));
  const kind = sniffBinary(head, file.name, file.type);
  if (kind) return { ok: false, reason: 'binary', kind, encoding: null };
  if (file.size > MAX_FILE_BYTES) {
    return { ok: false, reason: 'too_large', kind: 'text', encoding: null };
  }
  const bytes = new Uint8Array(await fileBytes(file));
  return readBytes(bytes, file.name, file.type);
}
