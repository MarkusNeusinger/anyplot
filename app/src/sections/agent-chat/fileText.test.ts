import { describe, expect, it } from 'vitest';

import { MAX_DATASET_BYTES } from 'src/lib/agent';
import {
  decodeText,
  looksBinary,
  MAX_FILE_BYTES,
  readBytes,
  readFile,
  sniffBinary,
} from 'src/sections/agent-chat/fileText';

const utf8 = (text: string) => new TextEncoder().encode(text);

/** UTF-16 code units as bytes, little or big endian, with or without the byte order mark. */
function utf16(text: string, endian: 'le' | 'be', bom = true): Uint8Array {
  const units = [...(bom ? [0xfeff] : []), ...Array.from(text, char => char.charCodeAt(0))];
  const bytes = new Uint8Array(units.length * 2);
  units.forEach((unit, index) => {
    const [high, low] = [unit >> 8, unit & 0xff];
    bytes[index * 2] = endian === 'le' ? low : high;
    bytes[index * 2 + 1] = endian === 'le' ? high : low;
  });
  return bytes;
}

const bytesOf = (...parts: Array<number[] | string>) =>
  new Uint8Array(parts.flatMap(part => (typeof part === 'string' ? Array.from(utf8(part)) : part)));

const TABLE = 'month,revenue\n2026-01,120\n2026-02,135\n';

describe('decodeText', () => {
  it('reads plain UTF-8', () => {
    expect(decodeText(utf8('Ort,Wert\nZürich,1\n'))).toEqual({
      text: 'Ort,Wert\nZürich,1\n',
      encoding: 'utf-8',
    });
  });

  it('reads UTF-8 with a byte order mark and drops the mark', () => {
    expect(decodeText(bytesOf([0xef, 0xbb, 0xbf], TABLE))).toEqual({
      text: TABLE,
      encoding: 'utf-8-bom',
    });
  });

  it("reads Excel's Unicode text: UTF-16LE with a byte order mark", () => {
    const tsv = 'Monat\tUmsatz\nJänner\t120\n';
    expect(decodeText(utf16(tsv, 'le'))).toEqual({ text: tsv, encoding: 'utf-16le' });
  });

  it('reads UTF-16BE with a byte order mark', () => {
    expect(decodeText(utf16(TABLE, 'be'))).toEqual({ text: TABLE, encoding: 'utf-16be' });
  });

  it('reads UTF-16 without a mark from the NUL bytes on every other byte', () => {
    expect(decodeText(utf16(TABLE, 'le', false))?.encoding).toBe('utf-16le');
    expect(decodeText(utf16(TABLE, 'be', false))?.encoding).toBe('utf-16be');
  });

  it('reads windows-1252, not ISO-8859-1: €, „ and ’ stay printable', () => {
    // "Preis €;„Zitat“;it’s" in windows-1252: 0x80 €, 0x84 „, 0x93 “, 0x92 ’.
    const bytes = bytesOf('Preis ', [0x80], ';', [0x84], 'Zitat', [0x93], ';it', [0x92], 's\n');

    const decoded = decodeText(bytes);

    expect(decoded).toEqual({ text: 'Preis €;„Zitat“;it’s\n', encoding: 'windows-1252' });
    expect(looksBinary(decoded!.text)).toBe(false);
  });
});

describe('sniffBinary', () => {
  it.each([
    [bytesOf([0x50, 0x4b, 0x03, 0x04], 'rest'), 'sales.xlsx', '', 'spreadsheet'],
    [bytesOf([0x50, 0x4b, 0x03, 0x04], 'rest'), 'table.ods', '', 'spreadsheet'],
    [bytesOf([0x50, 0x4b, 0x03, 0x04], 'rest'), 'export.zip', '', 'archive'],
    [
      bytesOf([0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1]),
      'old.xls',
      'application/vnd.ms-excel',
      'spreadsheet',
    ],
    [bytesOf([0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1]), 'letter.doc', '', 'binary'],
    [bytesOf('PAR1', [0x15, 0x04]), 'data.parquet', '', 'parquet'],
    [bytesOf('ARROW1', [0, 0]), 'data.feather', '', 'arrow'],
    [bytesOf([0x93], 'NUMPY', [0x01, 0x00]), 'a.npy', '', 'numpy'],
    [bytesOf([0x89], 'HDF\r\n', [0x1a, 0x0a]), 'store.h5', '', 'hdf5'],
    [bytesOf([0x80, 0x04, 0x95]), 'frame.pkl', '', 'pickle'],
    [bytesOf('%PDF-1.7\n'), 'report.pdf', '', 'pdf'],
    [bytesOf([0x1f, 0x8b, 0x08]), 'data.csv.gz', '', 'archive'],
  ])('names %#: %s as %s', (bytes, name, type, kind) => {
    expect(sniffBinary(bytes, name, type)).toBe(kind);
  });

  it('leaves text and a windows-1252 € at the start alone', () => {
    expect(sniffBinary(utf8(TABLE), 'a.csv')).toBeNull();
    expect(sniffBinary(bytesOf([0x80], ' 12\n'), 'a.csv')).toBeNull();
  });
});

describe('readBytes', () => {
  it('fills with the text, its encoding and its line count', () => {
    expect(readBytes(utf8(`${TABLE}\n\n`))).toEqual({
      ok: true,
      text: `${TABLE}\n\n`,
      encoding: 'utf-8',
      lines: 3,
    });
  });

  it('refuses a binary format by its kind', () => {
    expect(readBytes(bytesOf([0x80, 0x05]), 'x.pkl')).toMatchObject({
      ok: false,
      reason: 'binary',
      kind: 'pickle',
    });
  });

  it('refuses text with NUL bytes or with more than 1 % control characters', () => {
    expect(readBytes(bytesOf('abc', [0x00, 0x00, 0x00], 'def'))).toMatchObject({
      ok: false,
      reason: 'binary',
      kind: 'binary',
    });
    const noisy = bytesOf('a'.repeat(90), [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]);
    expect(readBytes(noisy)).toMatchObject({ ok: false, reason: 'binary' });
    // One control in a long text passes the browser; the server's parser names it.
    expect(readBytes(bytesOf('a'.repeat(500), [0x07]))).toMatchObject({ ok: true });
  });

  it('refuses an empty file and text over the paste cap', () => {
    expect(readBytes(utf8('  \n '))).toMatchObject({ ok: false, reason: 'empty' });
    // Under the raw cap, over the 1 MB cap once decoded: two bytes of UTF-8 per `ü`.
    const wide = utf8('ü'.repeat(MAX_DATASET_BYTES / 2 + 1));
    expect(readBytes(wide)).toMatchObject({ ok: false, reason: 'too_large', encoding: 'utf-8' });
  });
});

describe('readFile', () => {
  it('reads a File', async () => {
    const file = new File([TABLE], 'sales.csv', { type: 'text/csv' });
    await expect(readFile(file)).resolves.toMatchObject({ ok: true, text: TABLE, lines: 3 });
  });

  it('answers a large workbook by its format, not its size', async () => {
    const workbook = new File([bytesOf([0x50, 0x4b, 0x03, 0x04]), new Uint8Array(16)], 'big.xlsx');
    Object.defineProperty(workbook, 'size', { value: MAX_FILE_BYTES + 1 });
    await expect(readFile(workbook)).resolves.toMatchObject({ ok: false, kind: 'spreadsheet' });
  });

  it('refuses a text file over the raw cap before reading it', async () => {
    const file = new File(['a,b\n'], 'huge.csv');
    Object.defineProperty(file, 'size', { value: MAX_FILE_BYTES + 1 });
    await expect(readFile(file)).resolves.toMatchObject({ ok: false, reason: 'too_large' });
  });
});
