import type { ReactNode } from 'react';

import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';

import { proseLinkStyle, tableStyle } from 'src/theme';

/** An external link in the page's prose style, opened in a new tab. */
export function Ext({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} target="_blank" rel="noopener" sx={proseLinkStyle}>
      {children}
    </Link>
  );
}

/** A two-column fact table: a short label as the row header, then the fact. */
export function FactTable({
  rows,
  labelWidth = '25%',
}: {
  rows: [string, ReactNode][];
  labelWidth?: string;
}) {
  return (
    <Table
      sx={{
        ...tableStyle,
        '& .MuiTableCell-body': { verticalAlign: 'top' },
        // :first-child, not :first-of-type: the label is a <th>, so the value <td> is a first of its type too.
        '& .MuiTableCell-root:first-child': {
          fontWeight: 500,
          color: 'var(--ink-soft)',
          width: labelWidth,
        },
      }}
    >
      <TableBody>
        {rows.map(([label, fact]) => (
          <TableRow key={label}>
            <TableCell component="th" scope="row">
              {label}
            </TableCell>
            <TableCell>{fact}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
