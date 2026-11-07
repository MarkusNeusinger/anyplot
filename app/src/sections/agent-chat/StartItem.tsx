/**
 * The start item, the thread's first item (kit 1 B of the v4 design): what the chat adapts and
 * what it needs, before any data. "You came from **Basic Scatter Plot**. It needs", then the
 * spec's roles as chips in the user's words (`x · numbers`, `y · numbers, one or more`;
 * `roleChip` in `specReference.ts`), with an ⓘ after them that lists the columns in full, in the
 * spec's words (its `data` bullets from a server whose open names no roles), and beside it the
 * catalogue plot's thumbnail in the library in use (`CataloguePreview`; a click opens it large).
 * It ends with a pointer to the message box, "drop a file or paste a table below", and the
 * how-to ⓘ.
 *
 * It repeats no control: `.example_data()` and `.open()` are the composer's, in the data line
 * right above the box, so the start item only points there. It is a message in the thread: it
 * stays first and scrolls up with the talk once data arrives, so nothing vanishes. Inside the
 * thread's polite log, a title or a picture that arrives late is no news to read out. On a phone
 * it is compact: a smaller thumbnail beside the first line, and the chips below, at the full
 * width, where they wrap.
 */

import Box from '@mui/material/Box';

import type { RoleSpec } from 'src/lib/agent';
import { CataloguePreview, type ThumbnailSize } from 'src/sections/agent-chat/CataloguePreview';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import { DATA_HOWTO } from 'src/sections/agent-chat/messages';
import { columnLines, roleChip } from 'src/sections/agent-chat/specReference';
import { bodyTextSx, smallText } from 'src/sections/agent-chat/styles';
import { parseInlineCode } from 'src/sections/spec-detail/SpecTabs/utils';
import { fontSize, typography } from 'src/theme';
import type { ThemedPreviewSource } from 'src/utils/themedPreview';

/**
 * The thumbnail: 144 px wide from `sm` up, 81 px high, about the three lines beside it; 96 px on
 * a phone, about the first line's height when it wraps.
 */
const START_THUMBNAIL: ThumbnailSize = { xs: 96, sm: 144 };

/**
 * The item's places: on a phone the thumbnail beside the first line and the chips and the hint
 * below at the full width; from `sm` up the thumbnail beside all three lines.
 */
const AREAS = {
  xs: '"thumb lead" "needs needs" "hint hint"',
  sm: '"thumb lead" "thumb needs" "thumb hint"',
} as const;

/** The chips and the hint: the text's size, on a phone the 13 px floor, so a chip fits a line. */
const QUIET_SIZE = { xs: smallText, sm: fontSize.md } as const;

/**
 * A role's chip: mono, in a quiet pill. An optional role's chip has a dashed edge and the soft
 * ink, while its words say `optional`, which carries the meaning.
 */
function chipSx(required: boolean) {
  return {
    fontFamily: typography.mono,
    fontSize: QUIET_SIZE,
    lineHeight: 1.6,
    color: required ? 'var(--ink)' : 'var(--ink-soft)',
    border: `1px ${required ? 'solid' : 'dashed'} var(--rule)`,
    borderRadius: '999px',
    px: 1.25,
    overflowWrap: 'anywhere',
  } as const;
}

export interface StartItemProps {
  /** The spec's title, or its id until the spec loads. */
  title: string;
  /** The library in use, whose catalogue plot shows. */
  library: string;
  /** That library's catalogue previews; null without one. */
  preview: ThemedPreviewSource | null;
  /** The spec's roles as the session's open named them; null or empty from an older server. */
  roles: readonly RoleSpec[] | null;
  /** The spec's `data` bullets, the ⓘ's lines while the open names no roles. */
  bullets: readonly string[] | null | undefined;
}

export function StartItem({ title, library, preview, roles, bullets }: StartItemProps) {
  const chips = roles ?? [];
  const lines = columnLines(roles, bullets);
  const columns = lines.length > 0 && (
    <InfoPopover
      label="Columns the plot expects"
      heading="# the plot expects"
      testId="expected-columns"
      lines={lines.map(line => parseInlineCode(line))}
    />
  );
  return (
    <Box
      data-testid="start-item"
      aria-live="off"
      // No readable-line cap: its lines are short, and the chips keep one row on a wide screen.
      sx={{
        ...bodyTextSx,
        whiteSpace: 'normal',
        display: 'grid',
        gridTemplateColumns: 'auto minmax(0, 1fr)',
        gridTemplateAreas: AREAS,
        alignItems: 'center',
        rowGap: 0.75,
      }}
    >
      {/* Its own gap, so a spec without a preview leaves no indent. */}
      <Box
        sx={{
          gridArea: 'thumb',
          display: 'flex',
          pr: { xs: 1.5, sm: 1.75 },
          '&:empty': { display: 'none' },
        }}
      >
        <CataloguePreview
          title={title}
          library={library}
          preview={preview}
          size={START_THUMBNAIL}
        />
      </Box>
      <Box sx={{ gridArea: 'lead' }}>
        You came from{' '}
        <Box component="strong" sx={{ fontWeight: 600 }}>
          {title}
        </Box>
        .{lines.length > 0 && ' It needs'}
        {/* An older server names no roles: the ⓘ with the spec's bullets ends the sentence. */}
        {chips.length === 0 && columns}
      </Box>
      {/* The ⓘ goes with the last chip, so a wrap never leaves it alone at the row's end. */}
      {chips.length > 0 && (
        <Box
          component="ul"
          aria-label="What the plot needs"
          sx={{
            gridArea: 'needs',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: 0.75,
            m: 0,
            p: 0,
            listStyle: 'none',
          }}
        >
          {chips.map((role, index) => (
            <Box component="li" key={role.name} sx={{ display: 'flex', alignItems: 'center' }}>
              <Box component="span" sx={chipSx(role.required)}>
                {roleChip(role)}
              </Box>
              {index === chips.length - 1 && columns}
            </Box>
          ))}
        </Box>
      )}
      {/* Where to put the data: the message box below, whose line above it offers example data
          and `.open()`. The last word keeps the how-to ⓘ beside it. */}
      <Box
        data-testid="start-hint"
        sx={{ gridArea: 'hint', color: 'var(--ink-soft)', fontSize: QUIET_SIZE }}
      >
        drop a file or paste a table{' '}
        <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
          below
          <InfoPopover
            label="How the chat takes data"
            heading="# how it works"
            lines={DATA_HOWTO}
            testId="data-howto"
          />
        </Box>
      </Box>
    </Box>
  );
}
