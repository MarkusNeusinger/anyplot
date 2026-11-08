import { describe, expect, it } from 'vitest';

import {
  ATTACHMENT_LINE,
  attachmentWaitLine,
  chainStopText,
  describeConvertFailure,
  describeDataFailure,
  describeLibraryFailure,
  describeMemoryFailure,
  describeViewFailure,
  localClock,
  nextUtcMidnight,
  servicePausedText,
} from './messages';

describe('attachmentWaitLine', () => {
  it('reads the table without data, and says it replaces the data with', () => {
    expect(attachmentWaitLine(null)).toBe(ATTACHMENT_LINE);
    expect(attachmentWaitLine(22)).toBe(
      'the attached table replaces your data (22 rows, no .undo()) when you press Enter ↵, with a note if you like'
    );
    expect(attachmentWaitLine(1)).toContain('(1 row, no .undo())');
  });

  it('names the plot button that reads and plots it, and Enter that only reads it', () => {
    expect(attachmentWaitLine(null, '.create_plot()')).toBe(
      '.create_plot() reads the attached table and plots it · Enter ↵ only reads it'
    );
    expect(attachmentWaitLine(22, 'plot the new data')).toBe(
      'the attached table replaces your data (22 rows, no .undo()) · plot the new data reads and plots it, Enter ↵ only reads it'
    );
  });
});

describe('chainStopText', () => {
  it.each([
    [
      { reason: 'question' as const },
      'the assistant asked a question · answer it in the box, or .create_plot()',
    ],
    [
      { reason: 'data_warnings' as const, count: 2 },
      '2 warnings on the data · check above, then .create_plot()',
    ],
    [
      { reason: 'tables' as const, count: 3 },
      'the paste held 3 tables · check the one read above, then .create_plot()',
    ],
    [
      { reason: 'wide' as const },
      'the table is wide for this plot · check .to_long() above, then .create_plot()',
    ],
    [
      { reason: 'binding_warning' as const, role: 'size' },
      'a warning on size · check it above, then .create_plot()',
    ],
    [
      { reason: 'bindings_failed' as const },
      'the binding check failed · check the bindings above, then .create_plot()',
    ],
    [
      { reason: 'refused' as const },
      'the reading ended in a refusal · see above, then .create_plot()',
    ],
    [
      { reason: 'error' as const },
      'the reading ended in an error · see above, then .create_plot()',
    ],
    [
      { reason: 'stopped' as const },
      'the reading was stopped · check the data above, then .create_plot()',
    ],
  ])('says what to look at for %o', (stop, text) => {
    expect(chainStopText(stop, '.create_plot()')).toBe(text);
  });
});

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

  it('names the service pause like the other data calls', () => {
    expect(describeViewFailure('service_paused', null)).toBe(
      `could not show every row: ${servicePausedText()}`
    );
  });
});

describe('the service pause', () => {
  it('ends at the next 00:00 UTC, also a second before it', () => {
    expect(nextUtcMidnight(Date.parse('2026-11-02T14:05:00Z'))).toBe('2026-11-03T00:00:00.000Z');
    expect(nextUtcMidnight(Date.parse('2026-11-02T23:59:59Z'))).toBe('2026-11-03T00:00:00.000Z');
    expect(nextUtcMidnight(Date.parse('2026-12-31T00:00:00Z'))).toBe('2027-01-01T00:00:00.000Z');
  });

  it("names the end in the user's own time, and claims nothing about their own limit", () => {
    const until = '2026-11-03T00:00:00Z';
    expect(localClock(until)).toMatch(/^\d{2}:\d{2}/);
    expect(servicePausedText(until)).toBe(
      `the chat has reached today's overall limit and is paused until ${localClock(until)}`
    );
    expect(localClock('not a time')).toBeNull();
    expect(servicePausedText('not a time')).toContain('paused until 00:00 UTC');
  });

  it('is the line of a paused paste or file, never the daily limit of the user', () => {
    expect(describeDataFailure('service_paused', 'r-9')).toBe(`${servicePausedText()} · ref r-9`);
    expect(describeConvertFailure('a.xlsx', 'service_paused', null, null, null)).toBe(
      `"a.xlsx" ${servicePausedText()}`
    );
    expect(describeDataFailure('daily_limit', null)).toBe(
      "today's limit is reached; try again tomorrow"
    );
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

describe('library and memory failures', () => {
  it('says the switch failed, with the reason and the ref', () => {
    expect(describeLibraryFailure('not_eligible', 'r-1')).toBe(
      'could not switch: this plot cannot be adapted in that library · ref r-1'
    );
    expect(describeLibraryFailure('invalid', null)).toBe(
      'could not switch: the server refused this switch'
    );
    expect(describeLibraryFailure('teapot', null)).toBe(
      'could not switch: request failed (teapot)'
    );
  });

  it('says the removal failed, with the reason and the ref', () => {
    expect(describeMemoryFailure('not_found', null)).toBe(
      'could not forget: that decision was already forgotten'
    );
    expect(describeMemoryFailure('unreachable', 'r-2')).toMatch(
      /^could not forget: no answer from the server.* · ref r-2$/
    );
  });
});
