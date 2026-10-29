import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { pingColor } from 'src/sections/debug/debugFormat';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

export interface PingData {
  ms: number;
  ok: boolean;
}

export function SystemHealthRow({
  pings,
  systemData,
  pingHistory,
}: {
  pings: PingData[];
  systemData: { database_connected: boolean; api_response_time_ms: number; timestamp: string };
  pingHistory: number;
}) {
  const latest = pings[pings.length - 1];
  const okPings = pings.filter(p => p.ok);
  const currentOk = latest ? latest.ok : systemData.database_connected;
  const currentMs = latest ? latest.ms : systemData.api_response_time_ms;
  const avgMs = okPings.length > 0 ? okPings.reduce((a, p) => a + p.ms, 0) / okPings.length : null;
  const maxMs = Math.max(...pings.map(p => p.ms), 1);

  return (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: { xs: 1.5, md: 3 },
        mt: -2,
        mb: 3,
        fontSize: fontSize.xs,
        fontFamily: typography.fontFamily,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            bgcolor: currentOk ? colors.success : colors.error,
          }}
        />
        <Typography
          component="span"
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xs,
            color: 'var(--ink-soft)',
          }}
        >
          database {currentOk ? 'connected' : 'down'}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip
          title={
            avgMs !== null
              ? `avg ${avgMs.toFixed(0)}ms · max ${maxMs.toFixed(0)}ms · ${pings.length} samples`
              : 'measuring...'
          }
          arrow
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: '1px',
              height: 18,
              width: pingHistory * 4,
              borderBottom: '1px solid var(--rule)',
              px: 0.25,
            }}
          >
            {Array.from({ length: pingHistory }).map((_, i) => {
              const idx = pings.length - pingHistory + i;
              const p = idx >= 0 ? pings[idx] : null;
              if (!p) return <Box key={i} sx={{ flex: 1 }} />;
              return (
                <Box
                  key={i}
                  sx={{
                    flex: 1,
                    height: p.ok ? `${Math.max((p.ms / maxMs) * 100, 8)}%` : '100%',
                    bgcolor: p.ok ? pingColor(p.ms) : colors.error,
                    opacity: 0.7,
                  }}
                />
              );
            })}
          </Box>
        </Tooltip>
        <Typography
          component="span"
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xs,
            color: currentOk ? pingColor(currentMs) : colors.error,
            fontWeight: 600,
            minWidth: 52,
          }}
        >
          {currentMs.toFixed(0)}ms
        </Typography>
        {avgMs !== null && (
          <Typography
            component="span"
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: fontSize.xxs,
              color: semanticColors.mutedText,
            }}
          >
            avg {avgMs.toFixed(0)}
          </Typography>
        )}
      </Box>
      <Typography
        component="span"
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          color: semanticColors.mutedText,
        }}
      >
        updated {new Date(systemData.timestamp).toLocaleTimeString()}
      </Typography>
    </Box>
  );
}
