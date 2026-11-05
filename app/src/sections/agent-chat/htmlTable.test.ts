import { describe, expect, it } from 'vitest';

import { spannedTable } from 'src/sections/agent-chat/htmlTable';

/** A web table with grouped columns, shaped like an encyclopedia's density list (invented places). */
const GROUPED = `<html><body><p>intro</p><table class="wikitable sortable">
<thead>
<tr><th rowspan="2">Location</th><th colspan="2">Density</th><th rowspan="2">Population</th>
<th colspan="2">Land area</th><th rowspan="2">Ref.</th></tr>
<tr><th>/km<sup>2</sup></th><th>/mi<sup>2</sup></th><th>km<sup>2</sup></th><th>mi<sup>2</sup></th></tr>
</thead>
<tbody>
<tr><td>Ort A</td><td>21,826</td><td>56,530</td><td>720,262</td><td>33</td><td>13</td><td></td></tr>
<tr><td><span class="sortkey" style="display:none">!</span>Ort B</td><td>19,428</td><td>50,320</td>
<td>38,857</td><td>2</td><td>0.77</td><td><sup class="reference">[c]</sup></td></tr>
</tbody></table></body></html>`;

describe('spannedTable', () => {
  it('expands row and column spans so both header lines have the table width', () => {
    expect(spannedTable(GROUPED)).toBe(
      [
        'Location\tDensity\tDensity\tPopulation\tLand area\tLand area\tRef.',
        'Location\t/km2\t/mi2\tPopulation\tkm2\tmi2\tRef.',
        'Ort A\t21,826\t56,530\t720,262\t33\t13\t',
        'Ort B\t19,428\t50,320\t38,857\t2\t0.77\t[c]',
        '',
      ].join('\n')
    );
  });

  it('repeats a label that spans data rows in each of them', () => {
    const html =
      '<table><tr><th>Country</th><th>Year</th><th>Value</th></tr>' +
      '<tr><td rowspan="2">CH</td><td>2023</td><td>1</td></tr><tr><td>2024</td><td>2</td></tr></table>';
    expect(spannedTable(html)).toBe('Country\tYear\tValue\nCH\t2023\t1\nCH\t2024\t2\n');
  });

  it('leaves the plain text to a table without spans, no table, or several tables', () => {
    expect(
      spannedTable('<table><tr><th>a</th><th>b</th></tr><tr><td>1</td><td>2</td></tr></table>')
    ).toBeNull();
    expect(spannedTable('<p colspan="2">not a table</p>')).toBeNull();
    expect(spannedTable('')).toBeNull();
    const two = '<table><tr><td colspan="2">x</td></tr></table><table><tr><td>y</td></tr></table>';
    expect(spannedTable(two)).toBeNull();
  });

  it('keeps only text: nothing in the copied page runs', () => {
    const html =
      '<table><tr><th colspan="2">Group<script>window.__ran = true</script></th></tr>' +
      '<tr><td>a<img src="x" onerror="window.__ran = true"></td><td>b</td></tr></table>';
    expect(spannedTable(html)).toBe('Group\tGroup\na\tb\n');
    expect((window as { __ran?: boolean }).__ran).toBeUndefined();
  });

  it('caps an absurd span instead of filling thousands of columns', () => {
    const line = spannedTable('<table><tr><td colspan="100000">x</td></tr></table>') ?? '';
    expect(line.trim().split('\t')).toHaveLength(50);
  });
});
