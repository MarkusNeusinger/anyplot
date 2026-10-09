/**
 * The data panel of the agent chat: paste data (200 KB cap with a live
 * counter), parse it on the server, check the 20-row preview and the parser's
 * warnings, and bind each spec role to a column (the server's defaults come
 * preselected). `.create_plot()` runs the pipeline once every required role
 * has a column.
 */

import { useState } from 'react';

import Box from '@mui/material/Box';

import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { MAX_DATASET_BYTES, utf8Bytes } from 'src/lib/agent';
import { describeDataFailure } from 'src/sections/agent-chat/messages';
import {
  bodyTextSx,
  ctaButtonSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  panelSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { colors, fontSize, typography } from 'src/theme';

function formatKb(bytes: number): string {
  return `${(bytes / 1024).toFixed(bytes < 10 * 1024 ? 1 : 0)} KB`;
}

interface DataPanelProps {
  state: AgentSessionState;
  onParse: (text: string) => void;
  onBind: (role: string, column: string | null) => void;
  onCreatePlot: () => void;
}

export function DataPanel({ state, onParse, onBind, onCreatePlot }: DataPanelProps) {
  const [text, setText] = useState('');
  const bytes = utf8Bytes(text);
  const over = bytes > MAX_DATASET_BYTES;
  const ready = state.phase === 'ready' && !!state.sessionId;
  const running = !!state.run;
  const dataset = state.dataset;
  const columns = dataset?.parsed.profile.columns ?? [];
  const canCreate = ready && !!dataset && state.bindingsComplete && !state.bindingsBusy && !running;

  return (
    <Box component="section" aria-label="Your data" sx={panelSx}>
      <Box component="label" htmlFor="agent-data" sx={{ ...labelSx, display: 'block', mb: 0.75 }}>
        # your data — paste CSV, TSV, semicolon CSV or JSON
      </Box>
      <Box
        component="textarea"
        id="agent-data"
        value={text}
        rows={8}
        spellCheck={false}
        placeholder={'month,revenue\n2026-01,120\n2026-02,135'}
        onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => setText(event.target.value)}
        sx={{
          ...nativeControlSx,
          display: 'block',
          width: '100%',
          boxSizing: 'border-box',
          resize: 'vertical',
          fontSize: smallText,
          lineHeight: 1.5,
          whiteSpace: 'pre',
          overflowX: 'auto',
        }}
      />
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
          mt: 1,
        }}
      >
        <Box
          component="span"
          data-testid="data-counter"
          aria-live="polite"
          sx={{ ...labelSx, color: over ? colors.error : 'var(--ink-muted)' }}
        >
          {formatKb(bytes)} / 200 KB
        </Box>
        <Box
          component="button"
          type="button"
          onClick={() => onParse(text)}
          disabled={!ready || !text.trim() || over || state.parsing || running}
          sx={ghostButtonSx}
        >
          {state.parsing ? '.parse() …' : '.parse()'}
        </Box>
      </Box>

      {state.datasetError && (
        <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: 1.5 }}>
          {describeDataFailure(state.datasetError.code, state.datasetError.ref)}
        </Box>
      )}

      {dataset && (
        <Box sx={{ mt: 2.5, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
          <Box sx={{ ...labelSx, color: 'var(--ink-soft)' }}>
            {dataset.parsed.profile.rows.toLocaleString('en-US')} rows · {columns.length} columns ·{' '}
            {dataset.parsed.profile.source_format}
          </Box>

          {dataset.parsed.warnings.length > 0 && (
            <Box sx={{ borderLeft: `3px solid ${colors.warning}`, pl: 1.5 }}>
              <Box sx={labelSx}># warnings</Box>
              <Box
                component="ul"
                sx={{ m: 0, mt: 0.5, pl: 2.5, ...bodyTextSx, fontSize: smallText }}
              >
                {dataset.parsed.warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </Box>
            </Box>
          )}

          <Box sx={{ minWidth: 0 }}>
            <Box sx={{ ...labelSx, mb: 0.5 }}>
              # preview — first {dataset.parsed.preview.length} rows
            </Box>
            <Box
              sx={{
                overflowX: 'auto',
                maxHeight: 320,
                overflowY: 'auto',
                border: '1px solid var(--rule)',
                borderRadius: 1,
              }}
            >
              <Box
                component="table"
                sx={{
                  borderCollapse: 'collapse',
                  fontFamily: typography.mono,
                  fontSize: smallText,
                  color: 'var(--ink)',
                  width: '100%',
                  '& th, & td': {
                    px: 1,
                    py: 0.5,
                    textAlign: 'left',
                    whiteSpace: 'nowrap',
                    borderBottom: '1px solid var(--rule)',
                  },
                  '& th': {
                    position: 'sticky',
                    top: 0,
                    bgcolor: 'var(--bg-elevated)',
                    fontWeight: 600,
                  },
                }}
              >
                <thead>
                  <tr>
                    {columns.map(column => (
                      <th key={column.name} scope="col">
                        {column.name}
                        <Box
                          component="span"
                          sx={{ display: 'block', color: 'var(--ink-muted)', fontWeight: 400 }}
                        >
                          {column.dtype}
                        </Box>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataset.parsed.preview.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {row.map((cell, cellIndex) => (
                        <td key={cellIndex}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </Box>
            </Box>
          </Box>

          <Box>
            <Box sx={{ ...labelSx, mb: 0.75 }}># bindings — which column plays which role</Box>
            {state.roles.length === 0 && (
              <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
                {state.bindingsBusy ? 'checking roles…' : 'this plot names no data roles'}
              </Box>
            )}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'minmax(0, max-content) minmax(0, 1fr)',
                alignItems: 'center',
                columnGap: 1.5,
                rowGap: 1,
              }}
            >
              {state.roles.map(role => {
                const missing = state.missingRoles.includes(role);
                const id = `agent-role-${role}`;
                return (
                  <Box key={role} sx={{ display: 'contents' }}>
                    <Box
                      component="label"
                      htmlFor={id}
                      sx={{
                        fontFamily: typography.mono,
                        fontSize: fontSize.md,
                        color: missing ? colors.error : 'var(--ink)',
                        overflowWrap: 'anywhere',
                      }}
                    >
                      {role}
                      {missing ? ' *' : ''}
                    </Box>
                    <Box
                      component="select"
                      id={id}
                      value={state.bindings[role] ?? ''}
                      disabled={!ready || running || state.bindingsBusy}
                      onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                        onBind(role, event.target.value || null)
                      }
                      sx={{ ...nativeControlSx, width: '100%' }}
                    >
                      <option value="">— none —</option>
                      {columns.map(column => (
                        <option key={column.name} value={column.name}>
                          {column.name} ({column.dtype})
                        </option>
                      ))}
                    </Box>
                  </Box>
                );
              })}
            </Box>
            {state.missingRoles.length > 0 && (
              <Box sx={{ ...labelSx, mt: 1 }}>
                * required: pick a column for {state.missingRoles.join(', ')}
              </Box>
            )}
            {state.bindingsError && (
              <Box role="alert" sx={{ ...bodyTextSx, color: colors.error, mt: 1 }}>
                {describeDataFailure(state.bindingsError.code, state.bindingsError.ref)}
              </Box>
            )}
          </Box>

          <Box>
            <Box
              component="button"
              type="button"
              onClick={onCreatePlot}
              disabled={!canCreate}
              sx={{ ...ctaButtonSx, width: { xs: '100%', sm: 'auto' } }}
            >
              .create_plot()
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}
