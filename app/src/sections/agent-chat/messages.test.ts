import { describe, expect, it } from 'vitest';

import { describeConvertFailure, describeDataFailure } from './messages';

describe('describeDataFailure', () => {
  it('names what a refused paste fails on, before the ref', () => {
    expect(
      describeDataFailure('unparseable', 'r-1', 'the header has 3 fields, but line 3 has 4')
    ).toBe(
      'could not read this as CSV, TSV, semicolon CSV, JSON or JSON Lines: the header has 3 fields, but line 3 has 4 · ref r-1'
    );
  });

  it('keeps the code text alone without a cause', () => {
    expect(describeDataFailure('unparseable', 'r-1')).toBe(
      'could not read this as CSV, TSV, semicolon CSV, JSON or JSON Lines · ref r-1'
    );
    expect(describeDataFailure('too_long', null)).toBe('more than 1 MB; paste fewer rows');
  });

  it('leads a too_long with a cause by the cause, not the 1 MB the page checks', () => {
    expect(
      describeDataFailure('too_long', null, 'the data is larger than 4,096 KB once written out')
    ).toBe('too large: the data is larger than 4,096 KB once written out');
  });
});

describe('describeConvertFailure', () => {
  it('names the format a damaged file claimed to be', () => {
    expect(describeConvertFailure('a.xlsx', 'file_corrupt', null, null, 'r', 'spreadsheet')).toBe(
      '"a.xlsx" starts like a spreadsheet (Excel or OpenDocument) but could not be read as one: the file is damaged (a cut-off download or copy), or it is another format saved under this name · ref r'
    );
  });

  it('keeps the generic line without a known kind', () => {
    expect(describeConvertFailure('a.bin', 'file_corrupt', null, null, null)).toBe(
      '"a.bin" could not be read: the file looks damaged, or it is not the format it seems to be'
    );
  });
});
