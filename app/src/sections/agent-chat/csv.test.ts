import { describe, expect, it } from 'vitest';

import { CsvError, parseCsv, readCsvTable } from 'src/sections/agent-chat/csv';

// Written by Python's `csv.writer(buffer, lineterminator="\n")`, the agents service's `_write_csv`.
const CANONICAL =
  'name,note,value\n"a, b","say ""hi""",1.50\n"line\nbreak",,-0.0\n"cr\rhere",  two  spaces ,1e-07\n,tab\there,\n';

describe('parseCsv', () => {
  it('reads the canonical CSV cell for cell, exactly as written', () => {
    expect(parseCsv(CANONICAL)).toEqual([
      ['name', 'note', 'value'],
      ['a, b', 'say "hi"', '1.50'],
      ['line\nbreak', '', '-0.0'],
      ['cr\rhere', '  two  spaces ', '1e-07'],
      ['', 'tab\there', ''],
    ]);
  });

  it('keeps an empty single cell, which Python writes as ""', () => {
    expect(parseCsv('x\n""\n1\n')).toEqual([['x'], [''], ['1']]);
  });

  it('reads a last row without a line end and a trailing empty cell', () => {
    expect(parseCsv('a,b\n1,')).toEqual([
      ['a', 'b'],
      ['1', ''],
    ]);
    expect(parseCsv('a,b\n1,2')).toEqual([
      ['a', 'b'],
      ['1', '2'],
    ]);
  });

  it('ends a row at \\r\\n as well, and keeps a quoted \\r\\n inside a cell', () => {
    expect(parseCsv('a,b\r\n"x\r\ny",2\r\n')).toEqual([
      ['a', 'b'],
      ['x\r\ny', '2'],
    ]);
  });

  it('reads nothing from an empty text', () => {
    expect(parseCsv('')).toEqual([]);
  });

  it('keeps text beyond ASCII and long digit strings as they are', () => {
    expect(parseCsv('n,v\nZoë 🌍,0.12345678901234568\n日本語,12345678901234567890\n')).toEqual([
      ['n', 'v'],
      ['Zoë 🌍', '0.12345678901234568'],
      ['日本語', '12345678901234567890'],
    ]);
  });

  it.each([
    ['an unclosed quote', 'a\n"open\n'],
    ['a quote inside an unquoted cell', 'a\nx"y\n'],
    ['text after a quoted cell', 'a\n"x"y\n'],
    ['a carriage return alone', 'a\nx\ry\n'],
  ])('refuses %s instead of reading it some other way', (_, text) => {
    expect(() => parseCsv(text)).toThrow(CsvError);
  });
});

describe('readCsvTable', () => {
  it('splits the header from the rows', () => {
    expect(readCsvTable('x,y\n1,2\n')).toEqual({ header: ['x', 'y'], rows: [['1', '2']] });
  });

  it('reads a header without rows', () => {
    expect(readCsvTable('x,y\n')).toEqual({ header: ['x', 'y'], rows: [] });
  });

  it('refuses a row of another width, naming its row in the file', () => {
    expect(() => readCsvTable('x,y\n1,2\n3\n')).toThrow('row 3 has 1 cells, the header 2 columns');
  });

  it('refuses an empty file', () => {
    expect(() => readCsvTable('')).toThrow(CsvError);
  });

  it('reads the largest table the service stores: 20,000 rows of 50 columns', () => {
    const header = Array.from({ length: 50 }, (_, index) => `col_${index}`).join(',');
    const row = Array.from({ length: 50 }, (_, index) =>
      index % 7 === 0 ? '"a, b"' : '123.4567'
    ).join(',');
    const { rows } = readCsvTable(`${header}\n${`${row}\n`.repeat(20_000)}`);
    expect(rows).toHaveLength(20_000);
    expect(rows[19_999]).toHaveLength(50);
    expect(rows[19_999][0]).toBe('a, b');
  });
});
