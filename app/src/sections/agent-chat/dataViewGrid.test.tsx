import { describe, expect, it } from 'vitest';

import type { GridColDef, GridFilterItem } from '@mui/x-data-grid';

import { viewTable } from 'src/sections/agent-chat/dataView';
import {
  fieldOf,
  gridColumns,
  gridRows,
  NUMBER_OPERATORS,
  ROW_FIELD,
  type ViewRow,
} from 'src/sections/agent-chat/dataViewGrid';

const TABLE = viewTable('city,value\nBonn,1.50\nKöln,\n', [
  { name: 'city', dtype: 'text', missing: 0, unique: 2 },
  { name: 'value', dtype: 'number', missing: 1, unique: 1 },
]);

/** Whether `cell` passes the operator `operator` with `value`, as the grid applies it. */
function passes(operator: string, value: unknown, cell: string): boolean {
  const column = { field: 'c1' } as GridColDef<ViewRow>;
  const item: GridFilterItem = { field: 'c1', operator, value };
  const definition = NUMBER_OPERATORS.find(candidate => candidate.value === operator);
  const apply = definition?.getApplyFilterFn(item, column);
  if (!apply) throw new Error(`no filter for ${operator}`);
  return apply(cell, { id: 0 }, column, { current: null } as never);
}

describe('gridRows', () => {
  it('keeps every cell as its text and numbers the rows from 1', () => {
    expect(gridRows(TABLE)).toEqual([
      { id: 0, [ROW_FIELD]: 1, [fieldOf(0)]: 'Bonn', [fieldOf(1)]: '1.50' },
      { id: 1, [ROW_FIELD]: 2, [fieldOf(0)]: 'Köln', [fieldOf(1)]: '' },
    ]);
  });
});

describe('gridColumns', () => {
  const [rowColumn, city, value] = gridColumns(TABLE);

  it('leads with the row number, which nobody sorts, filters or finds with the search', () => {
    expect(rowColumn).toMatchObject({ field: ROW_FIELD, sortable: false, filterable: false });
    expect(
      rowColumn.getApplyQuickFilterFn?.('2', rowColumn as never, { current: null } as never)
    ).toBeNull();
  });

  it('gives a text column the grid’s text filters and order', () => {
    expect(city).toMatchObject({ field: 'c0', headerName: 'city', description: 'city · text' });
    expect(city.sortComparator).toBeUndefined();
    expect(city.filterOperators).toBeUndefined();
  });

  it('sorts a numeric column by number and adds the comparisons to the text filters', () => {
    expect(value).toMatchObject({ field: 'c1', align: 'right', description: 'value · number' });
    expect(['10', '9', ''].sort(value.sortComparator as (a: string, b: string) => number)).toEqual([
      '9',
      '10',
      '',
    ]);
    const operators = value.filterOperators?.map(operator => operator.value);
    expect(operators?.slice(0, 4)).toEqual(['>', '>=', '<', '<=']);
    expect(operators).toContain('contains');
    expect(operators).toContain('isEmpty');
  });
});

describe('NUMBER_OPERATORS', () => {
  it('compares the number a cell reads as', () => {
    expect(passes('>', 1.4, '1.50')).toBe(true);
    expect(passes('>', 10, '9')).toBe(false);
    expect(passes('<=', 1.5, '1.50')).toBe(true);
    expect(passes('>=', -1, '-0.0')).toBe(true);
  });

  it('never lets an empty cell or a text pass a comparison', () => {
    expect(passes('<', 5, '')).toBe(false);
    expect(passes('>', -5, '')).toBe(false);
    expect(passes('<', 5, 'n/a')).toBe(false);
  });
});
