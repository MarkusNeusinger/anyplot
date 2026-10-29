import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

interface DebugAuthViewProps {
  error: string | null;
  tokenInput: string;
  setTokenInput: (val: string) => void;
  handleTokenSubmit: (e: React.FormEvent) => void;
  adminToken: string;
  handleTokenClear: () => void;
}

export function DebugAuthView({
  error,
  tokenInput,
  setTokenInput,
  handleTokenSubmit,
  adminToken,
  handleTokenClear,
}: DebugAuthViewProps) {
  return (
    <Box sx={{ py: 4, maxWidth: 420, mx: 'auto' }}>
      <title>debug | anyplot.ai</title>
      <SectionHeader prompt="❯" title={<em>debug · admin auth</em>} />
      <Typography
        sx={{
          fontFamily: typography.fontFamily,
          fontSize: fontSize.xs,
          color: semanticColors.mutedText,
          mb: 2,
        }}
      >
        {error || 'sign in via your browser session, or paste an admin token as a fallback.'}
      </Typography>
      <Box
        component="form"
        onSubmit={handleTokenSubmit}
        sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
      >
        <Box
          component="input"
          type="password"
          placeholder="Admin token (fallback)"
          value={tokenInput}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTokenInput(e.target.value)}
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.sm,
            p: 1,
            border: '1px solid var(--rule)',
            borderRadius: 1,
            bgcolor: 'var(--bg-surface)',
            color: 'var(--ink)',
            outline: 'none',
            '&:focus': { borderColor: colors.primary },
          }}
        />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Box
            component="button"
            type="submit"
            disabled={!tokenInput.trim()}
            sx={{
              flex: 1,
              p: 1,
              border: 'none',
              borderRadius: 1,
              bgcolor: tokenInput.trim() ? colors.primary : 'var(--bg-elevated)',
              color: tokenInput.trim() ? 'var(--bg-page)' : 'var(--ink-muted)',
              fontFamily: typography.fontFamily,
              fontSize: fontSize.sm,
              fontWeight: 600,
              cursor: tokenInput.trim() ? 'pointer' : 'default',
              '&:hover': tokenInput.trim() ? { bgcolor: colors.primaryDark } : undefined,
            }}
          >
            unlock
          </Box>
          {adminToken && (
            <Box
              component="button"
              type="button"
              onClick={handleTokenClear}
              sx={{
                p: 1,
                border: '1px solid var(--rule)',
                borderRadius: 1,
                bgcolor: 'transparent',
                color: colors.error,
                fontFamily: typography.fontFamily,
                fontSize: fontSize.sm,
                fontWeight: 600,
                cursor: 'pointer',
                '&:hover': { bgcolor: 'var(--bg-elevated)' },
              }}
            >
              clear stored token
            </Box>
          )}
        </Box>
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xxs,
            color: semanticColors.mutedText,
            mt: 1,
          }}
        >
          stored in sessionStorage — clears when this tab closes.
        </Typography>
      </Box>
    </Box>
  );
}
