import { describe, expect, it } from 'vitest';

import { describeConvertFailure, describeDataFailure, describeViewFailure } from './messages';

describe('describeViewFailure', () => {
  it.each([
    ['no_dataset', null, undefined, 'could not show every row: parse the data first'],
    [
      'not_found',
      'r-2',
      undefined,
      'could not show every row: this server cannot show every row yet · ref r-2',
    ],
    [
      'too_large',
      null,
      undefined,
      'could not show every row: the data is larger than the view reads (4 MB)',
    ],
    [
      'csv',
      null,
      'row 3: a quote inside an unquoted cell',
      'could not show every row: the file is not the CSV it should be (row 3: a quote inside an unquoted cell)',
    ],
    ['boom', null, undefined, 'could not show every row: request failed (boom)'],
  ])('names %s', (code, ref, detail, text) => {
    expect(describeViewFailure(code, ref, detail)).toBe(text);
  });
});

describe('describeDataFailure', () => {
  it('leads with what a refused paste fails on, before the ref', () => {
    expect(
      describeDataFailure('unparseable', 'r-1', 'the header has 3 fields, but line 3 has 4')
    ).toBe('the header has 3 fields, but line 3 has 4 · ref r-1');
  });

  it('keeps the code text alone without a cause', () => {
    expect(describeDataFailure('unparseable', 'r-1')).toBe(
      'could not read this as CSV, TSV, semicolon CSV, JSON or JSON Lines · ref r-1'
    );
    expect(describeDataFailure('too_long', null)).toBe('more than 1 MB; paste fewer rows');
  });

  it('shows a too_long cause instead of the 1 MB the page checks', () => {
    expect(
      describeDataFailure('too_long', null, 'the data is larger than 4,096 KB once written out')
    ).toBe('the data is larger than 4,096 KB once written out');
  });
});

describe('describeConvertFailure', () => {
  it('names the format a damaged file claimed to be', () => {
    expect(describeConvertFailure('a.xlsx', 'file_corrupt', null, null, 'r', 'spreadsheet')).toBe(
      '"a.xlsx" starts like a spreadsheet (Excel or OpenDocument) but could not be read as one: the file is damaged (a cut-off download or copy), or it is another format saved under this name · ref r'
    );
  });

  it.each([
    ['zip', 'its zip container is broken or cut off'],
    ['workbook', 'its workbook parts are missing or broken'],
    ['sheet', 'the cells of this sheet are broken'],
    ['parquet', 'its Parquet footer or a data page is broken or cut off'],
    ['arrow', 'its Arrow or Feather structure is broken or cut off'],
    ['npy_header', 'its NumPy header is broken'],
    ['npy_data', 'it holds less data than its NumPy header announces'],
  ])('names the broken part %s of a damaged file', (damage, words) => {
    const line = describeConvertFailure('f', 'file_corrupt', null, null, 'r', 'parquet', damage);
    expect(line.startsWith('"f" could not be read as a Parquet file: ')).toBe(true);
    expect(line).toContain(words);
    expect(line.endsWith(' · ref r')).toBe(true);
  });

  it('ignores a broken part it has no words for', () => {
    expect(describeConvertFailure('a.bin', 'file_corrupt', null, null, null, null, 'other')).toBe(
      '"a.bin" could not be read: the file looks damaged, or it is not the format it seems to be'
    );
  });

  it('keeps the generic line without a known kind', () => {
    expect(describeConvertFailure('a.bin', 'file_corrupt', null, null, null)).toBe(
      '"a.bin" could not be read: the file looks damaged, or it is not the format it seems to be'
    );
  });
});
