import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { MdHeading, MdListItem } from 'src/sections/spec-detail/SpecTabs/md';
import { parseInlineCode } from 'src/sections/spec-detail/SpecTabs/utils';
import { proseLinkStyle, semanticColors, typography } from 'src/theme';
import type { SourceEntry, SpecSources } from 'src/types';
import { doiUrl, hasSourceEntries, isWebAddress } from 'src/utils/specSources';

interface SpecTabProps {
  title: string;
  description: string;
  applications?: string[];
  data?: string[];
  notes?: string[];
  sources?: SpecSources | null;
}

const sourceLinkSx = { ...proseLinkStyle, overflowWrap: 'anywhere' } as const;

// One work: its title as a link to its address, a DOI as a link to its resolver, an ISBN as text.
function SourceItem({ entry }: { entry: SourceEntry }) {
  return (
    <Typography
      component="li"
      sx={{
        fontFamily: typography.fontFamily,
        fontSize: '0.85rem',
        color: semanticColors.labelText,
        lineHeight: 1.7,
        ml: 2,
        mb: 0.25,
        '&::marker': { color: 'var(--ink-muted)' },
      }}
    >
      {isWebAddress(entry.url) ? (
        <Link href={entry.url} target="_blank" rel="noopener noreferrer" sx={sourceLinkSx}>
          {entry.title}
        </Link>
      ) : (
        entry.title
      )}
      {entry.doi && (
        <>
          {' · '}
          <Link
            href={doiUrl(entry.doi)}
            target="_blank"
            rel="noopener noreferrer"
            sx={sourceLinkSx}
          >
            {`doi:${entry.doi}`}
          </Link>
        </>
      )}
      {entry.isbn && (
        <>
          {' · '}
          {/* One line: a phone would otherwise break the number at one of its hyphens. */}
          <Box component="span" sx={{ whiteSpace: 'nowrap' }}>{`ISBN ${entry.isbn}`}</Box>
        </>
      )}
    </Typography>
  );
}

function SourceGroup({ label, entries }: { label: string; entries: SourceEntry[] }) {
  if (!entries.length) return null;
  return (
    <>
      <Typography
        component="h3"
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: '0.8rem',
          fontWeight: 400,
          color: semanticColors.mutedText,
          mt: 1,
          mb: 0.5,
        }}
      >
        {label}
      </Typography>
      <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
        {entries.map((entry, i) => (
          <SourceItem key={i} entry={entry} />
        ))}
      </Box>
    </>
  );
}

export function SpecTab({ title, description, applications, data, notes, sources }: SpecTabProps) {
  return (
    <Box
      sx={{
        bgcolor: 'var(--bg-page)',
        p: 3,
        borderRadius: 1,
        fontFamily: typography.fontFamily,
      }}
    >
      {/* Title only - spec ID visible in breadcrumb */}
      <Typography
        component="h2"
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: '1.1rem',
          fontWeight: 600,
          color: 'var(--ink)',
          mb: 1.5,
        }}
      >
        {title}
      </Typography>

      {/* ## Description */}
      <MdHeading level={2}>Description</MdHeading>
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: '0.85rem',
          color: semanticColors.labelText,
          lineHeight: 1.7,
        }}
      >
        {parseInlineCode(description)}
      </Typography>

      {/* Applications */}
      {applications && applications.length > 0 && (
        <>
          <MdHeading level={2}>Applications</MdHeading>
          <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
            {applications.map((app, i) => (
              <MdListItem key={i}>{app}</MdListItem>
            ))}
          </Box>
        </>
      )}

      {/* Data */}
      {data && data.length > 0 && (
        <>
          <MdHeading level={2}>Data</MdHeading>
          <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
            {data.map((d, i) => (
              <MdListItem key={i}>{d}</MdListItem>
            ))}
          </Box>
        </>
      )}

      {/* Notes */}
      {notes && notes.length > 0 && (
        <>
          <MdHeading level={2}>Notes</MdHeading>
          <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
            {notes.map((note, i) => (
              <MdListItem key={i}>{note}</MdListItem>
            ))}
          </Box>
        </>
      )}

      {/* Sources: only on a spec that names a work; most of the catalogue names none yet */}
      {hasSourceEntries(sources) && (
        <>
          <MdHeading level={2}>Sources</MdHeading>
          <SourceGroup label="inspired by" entries={sources.inspired_by ?? []} />
          <SourceGroup label="references" entries={sources.references ?? []} />
        </>
      )}
    </Box>
  );
}
