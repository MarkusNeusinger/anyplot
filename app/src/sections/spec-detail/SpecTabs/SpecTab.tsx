import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { MdHeading, MdListItem } from 'src/sections/spec-detail/SpecTabs/md';
import { parseInlineCode } from 'src/sections/spec-detail/SpecTabs/utils';
import { semanticColors, typography } from 'src/theme';

interface SpecTabProps {
  title: string;
  description: string;
  applications?: string[];
  data?: string[];
  notes?: string[];
}

export function SpecTab({ title, description, applications, data, notes }: SpecTabProps) {
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
    </Box>
  );
}
