import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { colors, fontSize, typography } from 'src/theme';

import { PING_HISTORY, PingData } from './useDebugPing';
import { SystemHealth } from './useDebugStatus';

interface SystemHealthRowProps {
  pings: PingData[];
  system: SystemHealth;
}

function pingColor(ms: number): string {
  if (ms < 75) return colors.success;
  if (ms < 200) return colors.warning;
  return colors.error;
}

export function SystemHealthRow({ pings, system }: SystemHealthRowProps) {
  const latest = pings[pings.length - 1];
  const okPings = pings.filter(p => p.ok);
  const currentOk = latest ? latest.ok : system.database_connected;
  const currentMs = latest ? latest.ms : system.api_response_time_ms;
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
              width: PING_HISTORY * 4,
              borderBottom: '1px solid var(--rule)',
              px: 0.25,
            }}
          >
            {Array.from({ length: PING_HISTORY }).map((_, i) => {
              const idx = pings.length - PING_HISTORY + i;
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
          }}
        >
          {currentOk ? `${currentMs.toFixed(0)}ms` : 'offline'}
        </Typography>
      </Box>
      <Typography sx={{ color: 'var(--ink-soft)' }}>
        db{' '}
        <Box component="span" sx={{ fontWeight: 600 }}>
          {system.total_specs_in_db.toLocaleString()}
        </Box>{' '}
        specs,{' '}
        <Box component="span" sx={{ fontWeight: 600 }}>
          {system.total_impls_in_db.toLocaleString()}
        </Box>{' '}
        impls
      </Typography>
      <Typography sx={{ color: 'var(--ink-soft)' }}>
        server time{' '}
        <Box component="span" sx={{ fontWeight: 600 }}>
          {system.timestamp}
        </Box>
      </Typography>
    </Box>
  );
}
