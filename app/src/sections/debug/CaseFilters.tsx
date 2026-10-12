/**
 * The filter row of the agent cases list: reaction, status and library as
 * selects (applied at once), spec, model version and tag as text (applied on
 * Enter or when the field loses the focus), and `show superseded`.
 */

import { useState } from 'react';

import Box from '@mui/material/Box';

import { LIBRARIES } from 'src/constants';
import { CASE_STATUSES, FEEDBACK_REACTIONS, type FeedbackReaction } from 'src/lib/agent';
import { REACTION_TEXT } from 'src/sections/agent-chat/reactions';
import { debugControlSx, listMutedSx } from 'src/sections/debug/styles';
import type { CaseFilterValues } from 'src/sections/debug/triage';
import { colors } from 'src/theme';

type TextKey = 'spec' | 'model_version' | 'tag';

interface TextField {
  key: TextKey;
  placeholder: string;
  label: string;
  max: number;
  /** Wide enough for the placeholder. */
  width: string;
}

const TEXT_FIELDS: readonly TextField[] = [
  { key: 'spec', placeholder: 'spec', label: 'Filter by spec', max: 100, width: '14ch' },
  {
    key: 'model_version',
    placeholder: 'model version',
    label: 'Filter by model version',
    max: 100,
    width: '18ch',
  },
  { key: 'tag', placeholder: 'tag', label: 'Filter by tag', max: 40, width: '12ch' },
];

/** A spec id and a tag are lowercase slugs; a model version is kept as typed. */
function normalise(key: TextKey, value: string): string {
  const trimmed = value.trim();
  return key === 'model_version' ? trimmed : trimmed.toLowerCase();
}

export interface CaseFiltersProps {
  filters: CaseFilterValues;
  onChange: (filters: CaseFilterValues) => void;
}

export function CaseFilters({ filters, onChange }: CaseFiltersProps) {
  // What is typed but not applied yet.
  const [drafts, setDrafts] = useState<Record<TextKey, string>>({
    spec: filters.spec,
    model_version: filters.model_version,
    tag: filters.tag,
  });

  const apply = (key: TextKey) => {
    const value = normalise(key, drafts[key]);
    if (value !== drafts[key]) setDrafts(prev => ({ ...prev, [key]: value }));
    if (value !== filters[key]) onChange({ ...filters, [key]: value });
  };

  const selectSx = { ...debugControlSx, cursor: 'pointer', maxWidth: '100%' } as const;

  return (
    <Box
      role="group"
      aria-label="Filter the agent cases"
      sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.75, minWidth: 0 }}
    >
      <Box
        component="select"
        aria-label="Filter by reaction"
        value={filters.reaction}
        onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
          onChange({ ...filters, reaction: event.target.value as FeedbackReaction | '' })
        }
        sx={selectSx}
      >
        <option value="">any reaction</option>
        {FEEDBACK_REACTIONS.map(reaction => (
          <option key={reaction} value={reaction}>
            {REACTION_TEXT[reaction]}
          </option>
        ))}
      </Box>
      <Box
        component="select"
        aria-label="Filter by status"
        value={filters.status}
        onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
          onChange({ ...filters, status: event.target.value as CaseFilterValues['status'] })
        }
        sx={selectSx}
      >
        <option value="open">open (new + in progress)</option>
        <option value="">all statuses</option>
        {CASE_STATUSES.map(status => (
          <option key={status} value={status}>
            {status.replace('_', ' ')}
          </option>
        ))}
      </Box>
      <Box
        component="select"
        aria-label="Filter by library"
        value={filters.library}
        onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
          onChange({ ...filters, library: event.target.value })
        }
        sx={selectSx}
      >
        <option value="">any library</option>
        {LIBRARIES.map(library => (
          <option key={library} value={library}>
            {library}
          </option>
        ))}
      </Box>
      {TEXT_FIELDS.map(field => (
        <Box
          key={field.key}
          component="input"
          type="search"
          aria-label={field.label}
          placeholder={field.placeholder}
          value={drafts[field.key]}
          maxLength={field.max}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setDrafts(prev => ({ ...prev, [field.key]: event.target.value }))
          }
          onKeyDown={(event: React.KeyboardEvent<HTMLInputElement>) => {
            if (event.key === 'Enter') apply(field.key);
          }}
          onBlur={() => apply(field.key)}
          sx={{ ...debugControlSx, width: field.width, minWidth: 0 }}
        />
      ))}
      <Box
        component="label"
        sx={{
          ...listMutedSx,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.75,
          minHeight: 30,
          cursor: 'pointer',
          whiteSpace: 'nowrap',
        }}
      >
        <Box
          component="input"
          type="checkbox"
          checked={filters.include_superseded}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            onChange({ ...filters, include_superseded: event.target.checked })
          }
          sx={{ m: 0, width: 14, height: 14, accentColor: colors.primary, cursor: 'inherit' }}
        />
        show superseded
      </Box>
    </Box>
  );
}
