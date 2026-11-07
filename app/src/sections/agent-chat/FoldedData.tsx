/**
 * An older data version in the thread (a `data_stub`, `useAgentSession`): folded to its label, `▸
 * data v2 · sheet "2026" · 12 rows × 5 cols`, which is the button that opens it (`CardFrame`).
 * Open, it shows what the version held, read-only, from the snapshot the thread took when the
 * version arrived (`DataSnapshot`): a line that says so, the assistant's change lines, how the
 * data was read, the parser's warnings and the preview. It has no controls: the live card is
 * the one that changes the data, and an older version comes back only through the chat (no
 * `.restore()`, decided in the v4 plan).
 *
 * The preview table shows at every width, also on a phone, where the live card leaves it to
 * `.view_all()`: an older version has no full view, since the server serves only the current
 * version's rows. It scrolls sideways in its own box.
 *
 * A stub without a snapshot (only a thread built by hand has one) is a quiet line with its shape.
 */

import { useId, useState } from 'react';

import Box from '@mui/material/Box';

import type { ChatItem, DataSnapshot } from 'src/hooks/useAgentSession';
import { CardFrame } from 'src/sections/agent-chat/CardFrame';
import { dataCardLabel, dataVersionLabel } from 'src/sections/agent-chat/cardLabels';
import { PreviewTable, WarningList } from 'src/sections/agent-chat/dataCardParts';
import { labelSx, readableSx } from 'src/sections/agent-chat/styles';
import { typography } from 'src/theme';

/** What a version held, read-only: its change lines, its source, its warnings and its preview. */
function VersionContent({ snapshot }: { snapshot: DataSnapshot }) {
  const { profile } = snapshot;
  const source = [
    `read as ${profile.source_format}`,
    snapshot.fileName ? `from "${snapshot.fileName}"` : null,
    snapshot.sheet ? `sheet "${snapshot.sheet}"` : null,
  ].filter(Boolean);
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minWidth: 0 }}>
      {/* It looks like the live card: one line says it is not. No "below": a table read from
          text that `.use()` took after a turn's version puts the live card above the stub. */}
      <Box data-testid="folded-data-note" sx={{ ...labelSx, ...readableSx }}>
        # an earlier version, read-only · the open data card holds the latest
      </Box>
      {snapshot.changes.length > 0 && (
        <Box data-testid="folded-data-changes">
          <Box sx={labelSx}># changed</Box>
          <Box
            component="ul"
            sx={{
              m: 0,
              mt: 0.5,
              pl: 2.5,
              fontFamily: typography.mono,
              fontSize: labelSx.fontSize,
              color: 'var(--ink)',
              lineHeight: 1.6,
              overflowWrap: 'anywhere',
            }}
          >
            {snapshot.changes.map((line, index) => (
              <li key={index}>{line}</li>
            ))}
          </Box>
        </Box>
      )}
      <Box
        data-testid="folded-data-source"
        sx={{ ...labelSx, ...readableSx, color: 'var(--ink-soft)', overflowWrap: 'anywhere' }}
      >
        {source.join(' · ')}
      </Box>
      <WarningList warnings={profile.warnings} />
      <Box sx={{ minWidth: 0 }}>
        <Box sx={{ ...labelSx, mb: 0.5 }}># preview — first {snapshot.preview.length} rows</Box>
        <PreviewTable columns={profile.columns} rows={snapshot.preview} />
      </Box>
    </Box>
  );
}

export function FoldedData({ item }: { item: Extract<ChatItem, { kind: 'data_stub' }> }) {
  const [open, setOpen] = useState(false);
  const bodyId = useId();
  const snapshot = item.snapshot;
  if (!snapshot) {
    const label = dataCardLabel(item.rows, item.columns);
    return (
      <Box data-testid="data-stub" sx={{ ...labelSx, ...readableSx, color: 'var(--ink-soft)' }}>
        {label.text}
      </Box>
    );
  }
  const label = dataVersionLabel(snapshot);
  return (
    <CardFrame
      label={label.text}
      spokenLabel={label.spoken}
      toggle={{ expanded: open, onToggle: () => setOpen(value => !value), bodyId }}
      labelTestId="data-stub-label"
      data-testid="data-stub"
      // The thread is a polite live log: a version opened to look at is no news to read out.
      aria-live="off"
    >
      <VersionContent snapshot={snapshot} />
    </CardFrame>
  );
}
