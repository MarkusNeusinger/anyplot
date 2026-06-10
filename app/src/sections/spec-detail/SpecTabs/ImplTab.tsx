import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { MdHeading } from 'src/sections/spec-detail/SpecTabs/md';
import { formatDate } from 'src/sections/spec-detail/SpecTabs/utils';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

interface ImplTabProps {
  imageDescription?: string;
  strengths?: string[];
  weaknesses?: string[];
  specId: string;
  libraryId: string;
  generatedAt?: string;
  updated?: string;
  created?: string;
}

export function ImplTab({
  imageDescription,
  strengths,
  weaknesses,
  specId,
  libraryId,
  generatedAt,
  updated,
  created,
}: ImplTabProps) {
  return (
    <Box
      sx={{
        bgcolor: 'var(--bg-page)',
        p: 3,
        borderRadius: 1,
        fontFamily: typography.fontFamily,
      }}
    >
      {/* Image Description */}
      {imageDescription && (
        <>
          <MdHeading level={2}>Description</MdHeading>
          <Typography
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: '0.85rem',
              color: semanticColors.labelText,
              lineHeight: 1.7,
            }}
          >
            {imageDescription}
          </Typography>
        </>
      )}

      {/* Strengths */}
      {strengths && strengths.length > 0 && (
        <>
          <MdHeading level={2}>Strengths</MdHeading>
          <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
            {strengths.map((s, i) => (
              <Typography
                key={i}
                component="li"
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: '0.85rem',
                  color: semanticColors.labelText,
                  lineHeight: 1.7,
                  ml: 2,
                  mb: 0.25,
                  '&::marker': { color: colors.success },
                }}
              >
                {s}
              </Typography>
            ))}
          </Box>
        </>
      )}

      {/* Weaknesses */}
      {weaknesses && weaknesses.length > 0 && (
        <>
          <MdHeading level={2}>Weaknesses</MdHeading>
          <Box component="ul" sx={{ m: 0, pl: 0, listStyle: 'disc' }}>
            {weaknesses.map((w, i) => (
              <Typography
                key={i}
                component="li"
                sx={{
                  fontFamily: typography.fontFamily,
                  fontSize: '0.85rem',
                  color: semanticColors.labelText,
                  lineHeight: 1.7,
                  ml: 2,
                  mb: 0.25,
                  '&::marker': { color: colors.error },
                }}
              >
                {w}
              </Typography>
            ))}
          </Box>
        </>
      )}

      {/* No data message */}
      {!imageDescription &&
        (!strengths || strengths.length === 0) &&
        (!weaknesses || weaknesses.length === 0) && (
          <Typography
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: '0.85rem',
              color: 'var(--ink-muted)',
            }}
          >
            No implementation review data available.
          </Typography>
        )}

      {/* Metadata */}
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.sm,
          color: 'var(--ink-muted)',
          mt: 2,
        }}
      >
        {specId}
        {libraryId && ` · ${libraryId}`}
        {(() => {
          const date = generatedAt || updated || created;
          return date ? ` · ${formatDate(date)}` : '';
        })()}
      </Typography>
    </Box>
  );
}
