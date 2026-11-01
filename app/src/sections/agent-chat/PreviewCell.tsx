import Box from '@mui/material/Box';

import { previewSegments } from 'src/sections/agent-chat/previewCell';
import { visuallyHiddenSx } from 'src/sections/agent-chat/styles';

/**
 * One cell of the data as text, its line breaks and space runs drawn as muted marks a screen reader
 * names (`previewCell.ts`): the data card's preview and the full view (`DataView.tsx`) draw cells alike.
 */
export function PreviewCell({ cell }: { cell: string }) {
  return (
    <>
      {previewSegments(cell).map((segment, index) => {
        if (!segment.mark) return <span key={index}>{segment.text}</span>;
        const label = { break: 'line break', tab: 'tab', spaces: `${segment.text.length} spaces` }[
          segment.mark
        ];
        return (
          <span key={index} title={label}>
            <Box component="span" aria-hidden="true" sx={{ color: 'var(--ink-muted)' }}>
              {segment.text}
            </Box>
            <Box component="span" sx={visuallyHiddenSx}>
              {` (${label}) `}
            </Box>
          </span>
        );
      })}
    </>
  );
}
