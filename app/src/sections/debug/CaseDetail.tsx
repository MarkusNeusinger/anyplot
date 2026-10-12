/**
 * One opened case, below the list: who sent it and when, the message, the
 * triage controls (status, tags, promotion), both renders, what the pipeline
 * reported, the code as a diff against the catalogue or as is, the
 * conversation and the config stamp. The text holds the agent chat's 13 px
 * floor, because most of it is the chat's own content.
 *
 * When the bucket's lifecycle rule has deleted the files (`expired`), one line
 * replaces everything read from them; the row and its triage stay.
 */

import { lazy, Suspense, useState } from 'react';

import Box from '@mui/material/Box';

import {
  type AgentCaseDetail,
  CASE_STATUSES,
  type CasePatch,
  type CaseStatus,
  caseVersionLabel,
} from 'src/lib/agent';
import { ghostButtonSx, smallText } from 'src/sections/agent-chat/styles';
import { acceptMatch } from 'src/sections/debug/acceptMatch';
import { CaseImages } from 'src/sections/debug/CaseImages';
import { ReactionMark } from 'src/sections/debug/CaseList';
import { formatUtc } from 'src/sections/debug/format';
import { PromoteControl } from 'src/sections/debug/PromoteControl';
import {
  detailControlSx,
  detailLabelSx,
  detailMutedSx,
  detailTextSx,
} from 'src/sections/debug/styles';
import { TagsEditor } from 'src/sections/debug/TagsEditor';
import { UnifiedDiff } from 'src/sections/debug/UnifiedDiff';
import { colors, semanticColors, typography } from 'src/theme';

const CodeHighlighter = lazy(() => import('src/components/CodeHighlighter'));

export interface CaseDetailProps {
  token: string;
  detail: AgentCaseDetail;
  /** A change of this case is in flight. */
  busy: boolean;
  /** The failure line of the last change. */
  patchError: string | null;
  onPatch: (patch: CasePatch) => void;
  /** Open another case (a sibling, the one it replaces or the one that supersedes it). */
  onSelect: (id: string) => void;
  onClose: () => void;
}

/** A case id as a link-like button that opens that case. */
function CaseLink({ id, onSelect }: { id: string; onSelect: (id: string) => void }) {
  return (
    <Box
      component="button"
      type="button"
      aria-label={`Open case ${id}`}
      onClick={() => onSelect(id)}
      sx={{
        fontFamily: typography.mono,
        fontSize: smallText,
        color: colors.primary,
        bgcolor: 'transparent',
        border: 'none',
        p: 0,
        cursor: 'pointer',
        overflowWrap: 'anywhere',
        textAlign: 'left',
        '&:hover': { textDecoration: 'underline' },
        '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 1 },
      }}
    >
      {id}
    </Box>
  );
}

function Block({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Box component="section" aria-label={label} sx={{ minWidth: 0 }}>
      <Box sx={detailLabelSx}># {label}</Box>
      {children}
    </Box>
  );
}

function Lines({ items }: { items: string[] }) {
  return (
    <Box component="ul" sx={{ ...detailTextSx, m: 0, pl: 2.5 }}>
      {items.map((item, index) => (
        <Box component="li" key={index} sx={{ overflowWrap: 'anywhere' }}>
          {item}
        </Box>
      ))}
    </Box>
  );
}

/** A config value as text: strings and numbers as they are, anything else as JSON. */
function configText(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return JSON.stringify(value);
}

function ConfigStamp({ config }: { config: Record<string, unknown> }) {
  const entries = Object.entries(config);
  if (entries.length === 0) return <Box sx={detailMutedSx}>no config stamp</Box>;
  return (
    <Box
      component="dl"
      sx={{
        ...detailTextSx,
        m: 0,
        display: 'grid',
        gridTemplateColumns: 'max-content minmax(0, 1fr)',
        columnGap: 2,
        rowGap: 0.5,
      }}
    >
      {entries.map(([key, value]) => {
        const nested =
          value && typeof value === 'object' && !Array.isArray(value)
            ? Object.entries(value as Record<string, unknown>)
            : null;
        return (
          <Box key={key} sx={{ display: 'contents' }}>
            <Box component="dt" sx={{ color: semanticColors.mutedText }}>
              {key}
            </Box>
            <Box component="dd" sx={{ m: 0, overflowWrap: 'anywhere' }}>
              {nested
                ? nested.length === 0
                  ? '—'
                  : nested.map(([name, inner]) => (
                      <Box key={name}>
                        {name}: {configText(inner)}
                      </Box>
                    ))
                : configText(value)}
            </Box>
          </Box>
        );
      })}
    </Box>
  );
}

function CodeBlock({ detail }: { detail: AgentCaseDetail }) {
  const [view, setView] = useState<'diff' | 'code'>(detail.diff !== null ? 'diff' : 'code');
  const versions = [
    `catalogue ${detail.catalogue_library_version ?? '—'}`,
    `session ${detail.snapshot_library_version ?? '—'}`,
  ].join(' · ');
  if (detail.code === null) return <Box sx={detailMutedSx}>no code in this case</Box>;
  const toggleSx = (active: boolean) => ({
    ...ghostButtonSx,
    py: 0.5,
    color: active ? colors.primary : 'var(--ink-soft)',
    borderColor: active ? colors.primary : 'var(--rule)',
  });
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}>
        {detail.diff !== null && (
          <Box role="group" aria-label="Code view" sx={{ display: 'flex', gap: 0.5 }}>
            {(['diff', 'code'] as const).map(option => (
              <Box
                key={option}
                component="button"
                type="button"
                aria-pressed={view === option}
                onClick={() => setView(option)}
                sx={toggleSx(view === option)}
              >
                {option}
              </Box>
            ))}
          </Box>
        )}
        <Box sx={detailMutedSx}>library {versions}</Box>
      </Box>
      {detail.diff === null && (
        <Box sx={detailMutedSx}>catalogue has no implementation for this pair any more</Box>
      )}
      {view === 'diff' && detail.diff !== null ? (
        detail.diff === '' ? (
          <Box sx={detailMutedSx}>the code equals the catalogue&apos;s</Box>
        ) : (
          <UnifiedDiff
            diff={detail.diff}
            label={`Diff from the catalogue's ${detail.spec_id ?? ''} ${detail.library_id ?? ''} to this case`}
          />
        )
      ) : (
        <Box sx={{ maxHeight: 520, overflow: 'auto', borderRadius: '8px', minWidth: 0 }}>
          <Suspense
            fallback={
              <Box
                component="pre"
                sx={{ ...detailTextSx, fontFamily: typography.mono, m: 0, whiteSpace: 'pre' }}
              >
                {detail.code}
              </Box>
            }
          >
            <CodeHighlighter
              code={detail.code}
              language="python"
              library={detail.library_id ?? undefined}
            />
          </Suspense>
        </Box>
      )}
    </Box>
  );
}

export function CaseDetail({
  token,
  detail,
  busy,
  patchError,
  onPatch,
  onSelect,
  onClose,
}: CaseDetailProps) {
  const match = acceptMatch(detail.reaction, detail.pipeline_status);
  const pipeline = [
    detail.pipeline_status ?? 'no pipeline status',
    detail.attempts !== null ? `${detail.attempts} attempts` : null,
    detail.model,
    detail.judge_model ? `judge ${detail.judge_model}` : null,
    detail.model_version ? `model version ${detail.model_version}` : null,
    detail.prompt_hash ? `prompt ${detail.prompt_hash}` : null,
    detail.tokens !== null ? `${detail.tokens} tokens` : null,
    detail.cost_estimate !== null ? `cost ${detail.cost_estimate}` : null,
  ].filter((part): part is string => !!part);

  return (
    <Box
      component="article"
      aria-label={`Case ${detail.id}`}
      sx={{
        border: '1px solid var(--rule)',
        borderRadius: 1,
        p: { xs: 1.5, sm: 2 },
        display: 'flex',
        flexDirection: 'column',
        gap: 2.5,
        minWidth: 0,
      }}
    >
      {/* 1. Header */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <ReactionMark reaction={detail.reaction} />
          <Box
            component="h3"
            sx={{
              ...detailTextSx,
              fontFamily: typography.mono,
              fontWeight: 600,
              m: 0,
              overflowWrap: 'anywhere',
            }}
          >
            {detail.id}
          </Box>
          <Box
            component="button"
            type="button"
            aria-label={`Close case ${detail.id}`}
            onClick={onClose}
            sx={{ ...ghostButtonSx, ml: 'auto' }}
          >
            .close()
          </Box>
        </Box>
        <Box sx={{ ...detailMutedSx, overflowWrap: 'anywhere' }}>
          {[
            `created ${formatUtc(detail.created_at)}`,
            `${detail.spec_id ?? '—'} · ${detail.library_id ?? '—'} · ${caseVersionLabel(detail.result_version)}`,
            `user ${detail.user_hash}`,
            `session ${detail.session_hash}`,
            detail.locale ? `locale ${detail.locale}` : null,
            detail.include_data ? 'with data.csv' : 'without data.csv',
          ]
            .filter(Boolean)
            .join(' · ')}
        </Box>
        {(detail.replaces || detail.superseded_by || detail.siblings.length > 0) && (
          <Box
            sx={{
              ...detailMutedSx,
              display: 'flex',
              flexWrap: 'wrap',
              columnGap: 2,
              rowGap: 0.25,
            }}
          >
            {detail.replaces && (
              <Box sx={{ display: 'inline-flex', gap: 0.75, flexWrap: 'wrap' }}>
                replaces <CaseLink id={detail.replaces} onSelect={onSelect} />
              </Box>
            )}
            {detail.superseded_by && (
              <Box sx={{ display: 'inline-flex', gap: 0.75, flexWrap: 'wrap' }}>
                superseded by <CaseLink id={detail.superseded_by} onSelect={onSelect} />
              </Box>
            )}
            {detail.siblings.length > 0 && (
              <Box sx={{ display: 'inline-flex', gap: 0.75, flexWrap: 'wrap' }}>
                siblings: {detail.siblings.length}
                {detail.siblings.map(id => (
                  <CaseLink key={id} id={id} onSelect={onSelect} />
                ))}
              </Box>
            )}
          </Box>
        )}
      </Box>

      {/* 2. Message: plain text, a message may hold `#` lines. */}
      <Block label="message">
        {detail.message ? (
          <Box sx={{ ...detailTextSx, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
            {detail.message}
          </Box>
        ) : (
          <Box sx={detailMutedSx}>no message</Box>
        )}
      </Block>

      {/* 3. Triage */}
      <Block label="triage">
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minWidth: 0 }}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', gap: 1.5 }}>
            <Box
              component="label"
              sx={{ ...detailMutedSx, display: 'inline-flex', alignItems: 'center', gap: 0.75 }}
            >
              status
              <Box
                component="select"
                aria-label="Status"
                value={detail.status}
                disabled={busy}
                onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                  onPatch({ status: event.target.value as CaseStatus })
                }
                sx={{ ...detailControlSx, cursor: 'pointer' }}
              >
                {CASE_STATUSES.map(status => (
                  <option key={status} value={status}>
                    {status.replace('_', ' ')}
                  </option>
                ))}
              </Box>
            </Box>
            <TagsEditor tags={detail.tags} disabled={busy} onChange={tags => onPatch({ tags })} />
          </Box>
          <PromoteControl
            key={detail.id}
            reaction={detail.reaction}
            expected={detail.expected}
            promotedAt={detail.promoted_at}
            includeData={detail.include_data}
            noPlot={detail.result_version === 0}
            busy={busy}
            onPatch={onPatch}
          />
          {patchError && (
            <Box
              role="alert"
              sx={{ ...detailTextSx, color: colors.error, overflowWrap: 'anywhere' }}
            >
              {patchError}
            </Box>
          )}
        </Box>
      </Block>

      {detail.expired ? (
        <Box sx={{ ...detailMutedSx, borderLeft: '3px solid var(--rule)', pl: 1.5 }}>
          the case files expired in the bucket (180-day lifecycle); the row and its triage state
          stay
        </Box>
      ) : (
        <>
          {/* 4. Renders */}
          <Block label="renders">
            {detail.result_version === 0 ? (
              <Box sx={detailMutedSx}>
                no plot: the feedback is on the chat itself, which made no plot version
              </Box>
            ) : (
              <CaseImages
                token={token}
                caseId={detail.id}
                files={detail.files}
                specId={detail.spec_id}
                libraryId={detail.library_id}
              />
            )}
          </Block>

          {/* 5. Pipeline */}
          <Block label="pipeline">
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
              <Box sx={{ ...detailTextSx, overflowWrap: 'anywhere' }}>{pipeline.join(' · ')}</Box>
              {match !== null && (
                <Box
                  sx={{
                    ...detailTextSx,
                    borderLeft: `3px solid ${match ? colors.primary : colors.warning}`,
                    pl: 1.5,
                  }}
                >
                  {match
                    ? `your reaction matches the pipeline outcome (${detail.pipeline_status})`
                    : `your reaction contradicts the pipeline outcome (${detail.pipeline_status})`}
                </Box>
              )}
              {detail.result_reason && (
                <Box sx={{ ...detailTextSx, overflowWrap: 'anywhere' }}>
                  <Box component="span" sx={{ color: semanticColors.mutedText }}>
                    reason:{' '}
                  </Box>
                  {detail.result_reason}
                </Box>
              )}
              {detail.residual_defects.length > 0 && (
                <Box>
                  <Box sx={detailMutedSx}>residual defects</Box>
                  <Lines items={detail.residual_defects} />
                </Box>
              )}
              {detail.changes.length > 0 && (
                <Box>
                  <Box sx={detailMutedSx}>changes</Box>
                  <Lines items={detail.changes} />
                </Box>
              )}
              {detail.bindings.length > 0 && (
                <Box sx={{ ...detailMutedSx, overflowWrap: 'anywhere' }}>
                  bindings:{' '}
                  {detail.bindings.map(binding => `${binding.role} → ${binding.column}`).join(', ')}
                </Box>
              )}
            </Box>
          </Block>

          {/* 6. Code */}
          <Block label="code">
            <CodeBlock key={detail.id} detail={detail} />
          </Block>

          {/* 7. Transcript */}
          <Block label="transcript">
            {detail.transcript && detail.transcript.length > 0 ? (
              <Box
                component="ol"
                sx={{
                  m: 0,
                  p: 0,
                  listStyle: 'none',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1,
                }}
              >
                {detail.transcript.map((turn, index) => (
                  <Box component="li" key={index} sx={{ minWidth: 0 }}>
                    <Box sx={detailMutedSx}>{turn.role === 'user' ? 'you' : 'assistant'}</Box>
                    <Box sx={{ ...detailTextSx, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
                      {turn.text}
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Box sx={detailMutedSx}>no transcript</Box>
            )}
          </Block>

          {/* 8. Config stamp */}
          <Block label="config">
            {detail.config ? (
              <ConfigStamp config={detail.config} />
            ) : (
              <Box sx={detailMutedSx}>no config stamp</Box>
            )}
          </Block>
        </>
      )}
    </Box>
  );
}
