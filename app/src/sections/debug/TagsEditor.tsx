/**
 * The tags of one case: chips with `.remove()`, and an input that adds a tag on
 * Enter or a comma. A tag is a lowercase slug (`TAG_PATTERN`), a case has at
 * most `MAX_TAGS`; an invalid entry is refused here with a line and never sent.
 * Every add or remove hands the whole new list to `onChange` (one PATCH).
 */

import { useState } from 'react';

import CloseIcon from '@mui/icons-material/Close';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';

import { MAX_TAGS, TAG_PATTERN } from 'src/lib/agent';
import { smallText } from 'src/sections/agent-chat/styles';
import { chipSx, detailControlSx, detailMutedSx } from 'src/sections/debug/styles';
import { colors, typography } from 'src/theme';

export interface TagsEditorProps {
  tags: string[];
  disabled: boolean;
  onChange: (tags: string[]) => void;
}

/** Why a tag cannot be added, or `null` when it can. */
function refusal(tag: string, tags: string[]): string | null {
  if (!TAG_PATTERN.test(tag)) return 'tags are lowercase slugs, at most 40 characters';
  if (tags.includes(tag)) return 'already there';
  if (tags.length >= MAX_TAGS) return `at most ${MAX_TAGS} tags`;
  return null;
}

export function TagsEditor({ tags, disabled, onChange }: TagsEditorProps) {
  const [draft, setDraft] = useState('');
  const [problem, setProblem] = useState<string | null>(null);

  const add = (raw: string) => {
    const tag = raw.trim();
    if (!tag) return;
    const why = refusal(tag, tags);
    if (why) {
      setProblem(why);
      return;
    }
    setProblem(null);
    setDraft('');
    onChange([...tags, tag]);
  };

  const remove = (tag: string) => {
    setProblem(null);
    onChange(tags.filter(item => item !== tag));
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0 }}>
      <Box
        role="group"
        aria-label="Tags"
        sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.75 }}
      >
        {tags.map(tag => (
          <Box
            key={tag}
            component="span"
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.25,
              fontFamily: typography.fontFamily,
              fontSize: smallText,
              color: 'var(--ink)',
              border: '1px solid var(--rule)',
              borderRadius: '4px',
              pl: 0.75,
              bgcolor: 'var(--bg-surface)',
            }}
          >
            {tag}
            <IconButton
              aria-label={`remove tag ${tag}`}
              title=".remove()"
              disabled={disabled}
              onClick={() => remove(tag)}
              size="small"
              sx={{
                p: 0.5,
                color: 'var(--ink-muted)',
                '&:hover': { color: colors.error },
                '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
              }}
            >
              <CloseIcon sx={{ fontSize: 14 }} />
            </IconButton>
          </Box>
        ))}
        <Box
          component="input"
          type="text"
          aria-label="Add a tag"
          placeholder="add tag"
          value={draft}
          disabled={disabled}
          maxLength={41}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            const value = event.target.value.toLowerCase();
            const comma = value.indexOf(',');
            if (comma >= 0) {
              // A comma ends the tag: add what came before it, keep typing after it.
              add(value.slice(0, comma));
              return;
            }
            setProblem(null);
            setDraft(value);
          }}
          onKeyDown={(event: React.KeyboardEvent<HTMLInputElement>) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              add(draft);
            }
          }}
          sx={{ ...detailControlSx, width: '12ch', minWidth: 0 }}
        />
      </Box>
      {problem && (
        <Box role="alert" sx={{ ...detailMutedSx, color: colors.error }}>
          {problem}
        </Box>
      )}
    </Box>
  );
}

/** The case's tags as read-only chips (the list). */
export function TagChips({ tags }: { tags: string[] }) {
  if (tags.length === 0) return null;
  return (
    <Box
      component="ul"
      aria-label="Tags"
      sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, m: 0, p: 0, listStyle: 'none' }}
    >
      {tags.map(tag => (
        <Box component="li" key={tag} sx={chipSx}>
          {tag}
        </Box>
      ))}
    </Box>
  );
}
