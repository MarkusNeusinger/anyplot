/**
 * The Data Grid's columns and rows of the full data view (`DataView.tsx`),
 * built from the table `viewTable.ts` read. Every data cell is the file's text;
 * the `#` column is the row's place in the data, which the search never reads.
 * A numeric column sorts by number and adds `>`, `>=`, `<` and `<=` to the text
 * filters, all read from the cell's text; the empty cells sort last either way
 * up. Only the view's lazy chunk imports this module.
 */

import Box from '@mui/material/Box';
import {
  getGridNumericOperators,
  getGridStringOperators,
  type GridColDef,
  type GridFilterOperator,
  type GridRenderCellParams,
} from '@mui/x-data-grid';

import { CellText } from 'src/sections/agent-chat/CellText';
import {
  compareNumericText,
  compareTextCells,
  numberOf,
  rowNumberWidth,
  type ViewTable,
} from 'src/sections/agent-chat/viewTable';

export type ViewRow = { id: number } & Record<string, string | number>;

/** The `#` column's field; a data column's is `c<index>`, so no column name can clash with it. */
export const ROW_FIELD = 'row';
export const fieldOf = (index: number) => `c${index}`;

/** `>`, `>=`, `<` and `<=` on a numeric column: the grid's own, fed the cell's number (null when empty). */
export const NUMBER_OPERATORS: GridFilterOperator<ViewRow>[] = getGridNumericOperators()
  .filter(operator => ['>', '>=', '<', '<='].includes(operator.value))
  .map(operator => ({
    ...operator,
    getApplyFilterFn: (item, column) => {
      const apply = operator.getApplyFilterFn(item, column);
      if (!apply) return null;
      return (value, row, col, apiRef) => apply(numberOf(String(value ?? '')), row, col, apiRef);
    },
  }));

/** A header: the column's name over its dtype, both in the header's accessible name. */
function columnLabel(name: string, kind: string | null) {
  return (
    <Box
      component="span"
      sx={{ display: 'flex', flexDirection: 'column', minWidth: 0, lineHeight: 1.3 }}
    >
      {/* A taller line than the dtype's: the clipped box must not cut an underscore off (`reading_1`). */}
      <Box
        component="span"
        sx={{
          fontWeight: 600,
          lineHeight: 1.5,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {name}
      </Box>
      {kind && (
        <Box component="span" sx={{ color: 'var(--ink-muted)', fontWeight: 400 }}>
          {kind}
        </Box>
      )}
    </Box>
  );
}

const renderText = (params: GridRenderCellParams<ViewRow, string>) => (
  <CellText cell={params.value ?? ''} />
);

export function gridColumns(table: ViewTable): GridColDef<ViewRow>[] {
  const textOperators = getGridStringOperators();
  return [
    {
      field: ROW_FIELD,
      headerName: '#',
      description: "the row's place in your data, not a column of it",
      width: rowNumberWidth(table.rows.length),
      align: 'right',
      headerAlign: 'right',
      sortable: false,
      filterable: false,
      disableColumnMenu: true,
      // The search reads the data, never the row numbers.
      getApplyQuickFilterFn: () => null,
      cellClassName: 'data-view-row',
      renderHeader: () => columnLabel('#', 'row'),
    },
    ...table.columns.map((column, index): GridColDef<ViewRow> => ({
      field: fieldOf(index),
      headerName: column.name,
      description: column.dtype ? `${column.name} · ${column.dtype}` : column.name,
      width: column.width,
      renderHeader: () => columnLabel(column.name, column.dtype),
      renderCell: renderText,
      // A comparator per direction: the grid's default negates one, which would bring the gaps first.
      getSortComparator: direction => (a, b) => compareTextCells(a, b, direction),
      ...(column.numeric && {
        align: 'right' as const,
        headerAlign: 'right' as const,
        getSortComparator: direction => (a, b) => compareNumericText(a, b, direction),
        filterOperators: [...NUMBER_OPERATORS, ...textOperators],
      }),
    })),
  ];
}

/** One grid row per data row: its index as the id, its number in `#`, its cells as they are. */
export function gridRows(table: ViewTable): ViewRow[] {
  const fields = table.columns.map((_, index) => fieldOf(index));
  return table.rows.map((cells, id) => {
    const row: ViewRow = { id, [ROW_FIELD]: id + 1 };
    for (let index = 0; index < fields.length; index += 1) row[fields[index]] = cells[index];
    return row;
  });
}
