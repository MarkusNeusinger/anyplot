/**
 * The "⋯" menu at the end of the chat header: `.save()` with its `# include data.csv` box
 * (`SaveButton`), out of the header row since 2026-11-02 (owner: less text). In a menu of its
 * own rather than in the feedback area, because the two do different things: `.save()` downloads
 * the session to the user's own computer and stores nothing, while feedback stores a case on the
 * server for the operator to read; one box for both would blur what goes where.
 *
 * A popover, as the language chip's: it opens on a tap as on a click and returns the focus to
 * the button when it closes. It stays mounted while closed, so the data box keeps the user's
 * choice from one save to the next. A save that started its download closes it; a failure keeps
 * it open with its line. Like the chip, the button waits until the session is open and while
 * anything else is in flight, which also closes an open menu.
 */

import { useId, useState } from 'react';

import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import Box from '@mui/material/Box';
import Popover from '@mui/material/Popover';

import { SaveButton, type SaveButtonProps } from 'src/sections/agent-chat/SaveButton';
import { actionButtonSx, labelSx } from 'src/sections/agent-chat/styles';

export type SessionMenuProps = SaveButtonProps;

export function SessionMenu({ disabled, onSave }: SessionMenuProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  // Something else started (a turn, a parse, a render): the menu closes, as the language chip's does.
  const [wasDisabled, setWasDisabled] = useState(disabled);
  if (disabled !== wasDisabled) {
    setWasDisabled(disabled);
    if (disabled) setAnchor(null);
  }
  const popoverId = useId();
  const open = anchor !== null;

  return (
    <Box sx={{ ml: 'auto' }}>
      <Box
        component="button"
        type="button"
        data-testid="session-menu"
        onClick={(event: React.MouseEvent<HTMLElement>) => setAnchor(event.currentTarget)}
        disabled={disabled}
        aria-label="More actions"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? popoverId : undefined}
        title="more · .save() the session as a json file"
        sx={{
          ...actionButtonSx,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          minWidth: 32,
          px: 0.75,
          border: '1px solid var(--rule)',
          color: 'var(--ink)',
        }}
      >
        <MoreHorizIcon aria-hidden sx={{ fontSize: 18 }} />
      </Box>
      <Popover
        id={popoverId}
        open={open}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        keepMounted
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{
          paper: {
            role: 'dialog',
            'aria-label': 'Save the session',
            sx: { width: { xs: 'calc(100vw - 32px)', sm: 340 }, p: 1.5, mt: 0.5 },
          },
        }}
      >
        <Box sx={{ ...labelSx, mb: 0.75 }}># save the session as a json file</Box>
        <SaveButton disabled={disabled} onSave={onSave} onSaved={() => setAnchor(null)} />
      </Popover>
    </Box>
  );
}
