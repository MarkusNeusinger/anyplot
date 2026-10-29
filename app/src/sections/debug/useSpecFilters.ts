import { useMemo, useState } from 'react';

import { LIBRARIES } from 'src/constants';

import { SpecStatus } from './useDebugStatus';

export type SortKey = 'updated' | 'id' | 'title' | 'avg_score';
export type SortDir = 'asc' | 'desc';

export const LOW_SCORE_THRESHOLD = 90;

export const countImpls = (spec: SpecStatus): number =>
  LIBRARIES.filter(lib => spec[lib as keyof SpecStatus] !== null).length;

export const hasLowScore = (spec: SpecStatus): boolean =>
  LIBRARIES.some(lib => {
    const s = spec[lib as keyof SpecStatus] as number | null;
    return s !== null && s < LOW_SCORE_THRESHOLD;
  });

export function useSpecFilters(specs: SpecStatus[]) {
  const [sortKey, setSortKey] = useState<SortKey>('updated');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [searchText, setSearchText] = useState('');
  const [showIncomplete, setShowIncomplete] = useState(false);
  const [showLowScores, setShowLowScores] = useState(false);
  const [missingLibrary, setMissingLibrary] = useState('');

  const filteredSpecs = useMemo(() => {
    if (!specs) return [];
    let filtered = [...specs];

    if (searchText) {
      const q = searchText.toLowerCase();
      filtered = filtered.filter(
        s => s.id.toLowerCase().includes(q) || s.title.toLowerCase().includes(q)
      );
    }
    if (showIncomplete) filtered = filtered.filter(s => countImpls(s) < LIBRARIES.length);
    if (showLowScores) filtered = filtered.filter(hasLowScore);
    if (missingLibrary)
      filtered = filtered.filter(s => s[missingLibrary as keyof SpecStatus] === null);

    filtered.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'updated':
          cmp = (a.updated || '').localeCompare(b.updated || '');
          break;
        case 'id':
          cmp = a.id.localeCompare(b.id);
          break;
        case 'title':
          cmp = a.title.localeCompare(b.title);
          break;
        case 'avg_score':
          cmp = (a.avg_score ?? 0) - (b.avg_score ?? 0);
          break;
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });

    return filtered;
  }, [specs, searchText, showIncomplete, showLowScores, missingLibrary, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'updated' || key === 'avg_score' ? 'desc' : 'asc');
    }
  };

  return {
    sortKey,
    sortDir,
    searchText,
    setSearchText,
    showIncomplete,
    setShowIncomplete,
    showLowScores,
    setShowLowScores,
    missingLibrary,
    setMissingLibrary,
    filteredSpecs,
    handleSort,
  };
}
