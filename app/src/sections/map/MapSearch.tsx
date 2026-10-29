import type React from 'react';

import Box from '@mui/material/Box';

import { type SpecMapItem } from 'src/sections/map/MapPage.helpers';
import { colors, fontSize, typography } from 'src/theme';

export function MapSearch({
  searchInputRef,
  searchQuery,
  setSearchQuery,
  searchIdx,
  setSearchIdx,
  searchOpen,
  setSearchOpen,
  searchMatches,
  selectMatch,
}: {
  searchInputRef: React.RefObject<HTMLInputElement | null>;
  searchQuery: string;
  setSearchQuery: (val: string) => void;
  searchIdx: number;
  setSearchIdx: React.Dispatch<React.SetStateAction<number>>;
  searchOpen: boolean;
  setSearchOpen: (val: boolean) => void;
  searchMatches: SpecMapItem[];
  selectMatch: (item: SpecMapItem) => void;
}) {
  return (
    <Box
      sx={{
        position: 'absolute',
        top: { xs: 8, sm: 16 },
        left: { xs: 16, sm: '50%' },
        right: { xs: 16, sm: 'auto' },
        transform: { xs: 'none', sm: 'translateX(-50%)' },
        zIndex: 4,
        width: { xs: 'auto', sm: 280 },
        maxWidth: { xs: 'none', sm: 'calc(100vw - 320px)' },
        fontFamily: typography.mono,
      }}
    >
      <Box
        component="input"
        ref={searchInputRef}
        type="text"
        value={searchQuery}
        placeholder="specs.search()"
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
          setSearchQuery(e.target.value);
          setSearchIdx(0);
        }}
        onFocus={() => setSearchOpen(true)}
        onBlur={() => window.setTimeout(() => setSearchOpen(false), 150)}
        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSearchIdx(i => Math.min(i + 1, Math.max(0, searchMatches.length - 1)));
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSearchIdx(i => Math.max(i - 1, 0));
          } else if (e.key === 'Enter') {
            e.preventDefault();
            const pick = searchMatches[searchIdx];
            if (pick) selectMatch(pick);
          } else if (e.key === 'Escape') {
            setSearchQuery('');
            searchInputRef.current?.blur();
          }
        }}
        sx={{
          width: '100%',
          boxSizing: 'border-box',
          px: 1.25,
          py: 0.75,
          bgcolor: 'var(--bg-surface)',
          border: '1px solid var(--rule)',
          borderRadius: '4px',
          fontFamily: typography.mono,
          fontSize: fontSize.xs,
          color: 'var(--ink)',
          outline: 'none',
          '&::placeholder': { color: 'var(--ink-soft)', opacity: 0.65 },
          '&:focus': { borderColor: colors.primary },
        }}
      />
      {searchOpen && searchQuery.trim() && (
        <Box
          sx={{
            mt: 0.5,
            bgcolor: 'var(--bg-surface)',
            border: '1px solid var(--rule)',
            borderRadius: '4px',
            overflow: 'hidden',
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
          }}
        >
          {searchMatches.length === 0 ? (
            <Box
              aria-label="No matches"
              sx={{
                px: 1.25,
                py: 0.75,
                fontSize: fontSize.xs,
                color: 'var(--ink-soft)',
                fontFamily: typography.mono,
                '& .subj': { opacity: 0.7 },
              }}
            >
              <span className="subj">results</span>.empty()
            </Box>
          ) : (
            searchMatches.map((s, i) => (
              <Box
                key={s.id}
                onMouseDown={e => {
                  e.preventDefault();
                  selectMatch(s);
                }}
                onMouseEnter={() => setSearchIdx(i)}
                sx={{
                  px: 1.25,
                  py: 0.75,
                  cursor: 'pointer',
                  fontSize: fontSize.xs,
                  color: 'var(--ink)',
                  bgcolor: i === searchIdx ? 'var(--bg-page)' : 'transparent',
                  borderBottom: i < searchMatches.length - 1 ? '1px solid var(--rule)' : 'none',
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: 1,
                }}
              >
                <Box
                  sx={{
                    flex: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {s.title}
                </Box>
                <Box sx={{ color: 'var(--ink-soft)', opacity: 0.7, fontSize: '0.65rem' }}>
                  {s.id}
                </Box>
              </Box>
            ))
          )}
        </Box>
      )}
    </Box>
  );
}
