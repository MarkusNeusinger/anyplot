/**
 * The debug page's "agent cases" section: the triage of the agent chat's quick
 * feedback (docs/concepts/agent-network.md, "Feedback capture"; the routes are
 * `GET|PATCH /debug/agent/cases...` in docs/reference/api.md).
 *
 * - The list shows the open queue first (`new` and `in progress`), newest
 *   first, superseded cases hidden; filters narrow it, `.more()` appends the
 *   next page.
 * - `.open()` shows one case below the list (`CaseDetail`).
 * - A triage change (status, tags, expected outcome, promotion) updates the
 *   row at once and sends one PATCH; a refusal puts the row back and shows the
 *   reason with the request id, under the control that sent it.
 * - The section never reloads the page for Cloudflare Access: the page's own
 *   `/debug/status` call owns that. A kill switch that is off (`not_enabled`)
 *   is one line; the rest of the page stays.
 */

import { useEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import {
  agentApi,
  AgentApiError,
  type AgentCase,
  type AgentCaseDetail,
  type CasePatch,
} from 'src/lib/agent';
import { ghostButtonSx } from 'src/sections/agent-chat/styles';
import { CaseDetail } from 'src/sections/debug/CaseDetail';
import { CaseFilters } from 'src/sections/debug/CaseFilters';
import { CaseList } from 'src/sections/debug/CaseList';
import { detailMutedSx, listMutedSx, listTextSx } from 'src/sections/debug/styles';
import {
  applyPatch,
  type CaseFilterValues,
  DEFAULT_FILTERS,
  describeCaseError,
  describeFilters,
  filtersToQuery,
  triageOf,
} from 'src/sections/debug/triage';
import { colors } from 'src/theme';

export interface AgentCasesSectionProps {
  /** The admin token of the page (`X-Admin-Token`), or `''` behind Cloudflare Access. */
  token: string;
  /** The page's reload count: a change reloads the list and the opened case. */
  reloadCounter: number;
}

interface ListState {
  /** The token, reload count and query the list belongs to. */
  key: string;
  items: AgentCase[];
  hasMore: boolean;
  failure: unknown;
  failed: boolean;
  loadingMore: boolean;
  moreFailure: string | null;
}

interface DetailState {
  id: string;
  data: AgentCaseDetail | null;
  failure: string | null;
}

const without = <T,>(record: Record<string, T>, key: string): Record<string, T> => {
  const next = { ...record };
  delete next[key];
  return next;
};

export function AgentCasesSection({ token, reloadCounter }: AgentCasesSectionProps) {
  const [filters, setFilters] = useState<CaseFilterValues>(DEFAULT_FILTERS);
  const query = useMemo(() => filtersToQuery(filters), [filters]);
  const listKey = `${token}\n${reloadCounter}\n${JSON.stringify(query)}`;
  const [list, setList] = useState<ListState | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DetailState | null>(null);
  const [busy, setBusy] = useState<Record<string, boolean>>({});
  const [patchErrors, setPatchErrors] = useState<Record<string, string>>({});
  const detailRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    agentApi
      .listCases(token, query)
      .then(page => {
        if (cancelled) return;
        setList({
          key: listKey,
          items: page.items,
          hasMore: page.has_more,
          failure: null,
          failed: false,
          loadingMore: false,
          moreFailure: null,
        });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setList({
          key: listKey,
          items: [],
          hasMore: false,
          failure: err,
          failed: true,
          loadingMore: false,
          moreFailure: null,
        });
      });
    return () => {
      cancelled = true;
    };
  }, [token, query, listKey]);

  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false;
    agentApi
      .getCase(token, selectedId)
      .then(data => {
        if (!cancelled) setDetail({ id: selectedId, data, failure: null });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setDetail({
          id: selectedId,
          data: null,
          failure: describeCaseError(err, 'failed to load the case'),
        });
      });
    return () => {
      cancelled = true;
    };
  }, [token, selectedId, reloadCounter]);

  const current = list && list.key === listKey ? list : null;
  const opened = detail && detail.id === selectedId ? detail : null;
  const openedCase = opened?.data ?? null;
  const answeredId = opened ? opened.id : null;

  // Bring the opened case into view once its answer is on screen: it renders
  // below the whole list. Started earlier, while the panel only says "loading",
  // the browser drops the smooth scroll when the panel's content arrives.
  useEffect(() => {
    if (!answeredId) return;
    const node = detailRef.current;
    if (node && typeof node.scrollIntoView === 'function') {
      node.scrollIntoView({ block: 'start', behavior: 'smooth' });
    }
  }, [answeredId]);

  const open = (id: string) => {
    setSelectedId(id);
  };
  const close = () => {
    // The case's failure line was read in the detail; it does not move to the row.
    if (selectedId) setPatchErrors(prev => without(prev, selectedId));
    setSelectedId(null);
    setDetail(null);
  };

  const loadMore = () => {
    if (!current || current.loadingMore) return;
    const last = current.items[current.items.length - 1];
    if (!last) return;
    const key = current.key;
    setList(prev =>
      prev && prev.key === key ? { ...prev, loadingMore: true, moreFailure: null } : prev
    );
    agentApi
      .listCases(token, { ...query, before: last.id })
      .then(page => {
        setList(prev => {
          if (!prev || prev.key !== key) return prev;
          const known = new Set(prev.items.map(item => item.id));
          return {
            ...prev,
            items: [...prev.items, ...page.items.filter(item => !known.has(item.id))],
            hasMore: page.has_more,
            loadingMore: false,
          };
        });
      })
      .catch((err: unknown) => {
        setList(prev =>
          prev && prev.key === key
            ? {
                ...prev,
                loadingMore: false,
                moreFailure: describeCaseError(err, 'failed to load more cases'),
              }
            : prev
        );
      });
  };

  /** Apply fields to the case wherever it shows: its row and the opened detail. */
  const merge = (id: string, fields: Partial<AgentCase>) => {
    setList(prev =>
      prev
        ? {
            ...prev,
            items: prev.items.map(item => (item.id === id ? { ...item, ...fields } : item)),
          }
        : prev
    );
    setDetail(prev =>
      prev && prev.data && prev.id === id ? { ...prev, data: { ...prev.data, ...fields } } : prev
    );
  };

  const patchCase = async (id: string, patch: CasePatch) => {
    const source =
      current?.items.find(item => item.id === id) ??
      (openedCase && openedCase.id === id ? openedCase : undefined);
    if (!source || busy[id]) return;
    const before = triageOf(source);
    merge(id, applyPatch(before, source.reaction, patch));
    setBusy(prev => ({ ...prev, [id]: true }));
    setPatchErrors(prev => without(prev, id));
    try {
      const updated = await agentApi.patchCase(token, id, patch);
      merge(id, updated);
    } catch (err) {
      merge(id, before);
      setPatchErrors(prev => ({ ...prev, [id]: describeCaseError(err, 'the change failed') }));
    } finally {
      setBusy(prev => without(prev, id));
    }
  };

  const failure = current?.failed ? current.failure : null;
  const notEnabled = failure instanceof AgentApiError && failure.code === 'not_enabled';
  const filterText = describeFilters(filters);

  let body: React.ReactNode;
  if (!current) {
    body = <Box sx={{ ...listMutedSx, py: 2 }}>loading cases…</Box>;
  } else if (notEnabled) {
    body = <Box sx={{ ...listMutedSx, py: 2 }}>agent chat is not enabled on this server</Box>;
  } else if (current.failed) {
    body = (
      <Box role="alert" sx={{ ...listTextSx, color: colors.error, py: 2 }}>
        {describeCaseError(failure, 'failed to load cases')}
      </Box>
    );
  } else if (current.items.length === 0) {
    body = (
      <Box sx={{ ...listMutedSx, py: 2 }}>no cases{filterText ? ` with ${filterText}` : ''}</Box>
    );
  } else {
    body = (
      <>
        <CaseList
          items={current.items}
          selectedId={selectedId}
          busy={busy}
          errors={selectedId ? without(patchErrors, selectedId) : patchErrors}
          onOpen={open}
          onClose={close}
          onStatus={(id, status) => void patchCase(id, { status })}
        />
        {(current.hasMore || current.moreFailure) && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mt: 1, flexWrap: 'wrap' }}>
            {current.hasMore && (
              <Box
                component="button"
                type="button"
                aria-label="Load more cases"
                disabled={current.loadingMore}
                onClick={loadMore}
                sx={ghostButtonSx}
              >
                {current.loadingMore ? '.more() …' : '.more()'}
              </Box>
            )}
            {current.moreFailure && (
              <Box role="alert" sx={{ ...listTextSx, color: colors.error }}>
                {current.moreFailure}
              </Box>
            )}
          </Box>
        )}
      </>
    );
  }

  return (
    <Box component="section" aria-label="Agent cases section" sx={{ mb: 4 }}>
      <Box sx={{ mt: 4, display: 'flex', alignItems: 'center', columnGap: 2, flexWrap: 'wrap' }}>
        <SectionHeader prompt="❯" title={<em>agent cases</em>} />
        <Box sx={{ ml: { sm: 'auto' }, mb: { xs: 2, sm: 0 }, minWidth: 0, maxWidth: '100%' }}>
          <CaseFilters filters={filters} onChange={setFilters} />
        </Box>
      </Box>
      {body}
      {selectedId && (
        <Box ref={detailRef} sx={{ mt: 2, scrollMarginTop: '64px' }}>
          {openedCase ? (
            <CaseDetail
              token={token}
              detail={openedCase}
              busy={!!busy[openedCase.id]}
              patchError={patchErrors[openedCase.id] ?? null}
              onPatch={patch => void patchCase(openedCase.id, patch)}
              onSelect={open}
              onClose={close}
            />
          ) : opened?.failure ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
              <Box role="alert" sx={{ ...detailMutedSx, color: colors.error }}>
                {opened.failure}
              </Box>
              <Box
                component="button"
                type="button"
                aria-label="Close the case"
                onClick={close}
                sx={ghostButtonSx}
              >
                .close()
              </Box>
            </Box>
          ) : (
            <Box sx={detailMutedSx}>loading case…</Box>
          )}
        </Box>
      )}
    </Box>
  );
}
