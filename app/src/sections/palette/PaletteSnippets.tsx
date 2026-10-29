import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import { SectionHeader } from 'src/components/SectionHeader';
import { type Lang, snippet, type Swatch } from 'src/pages/PalettePage.helpers';
import { colors, typography } from 'src/theme';

import { CodeBlock } from './CodeBlock';
const sectionSx = { mt: 6 };
const proseColumnSx = { maxWidth: '720px' };
const LANG_LABELS: Record<Lang, string> = {
  python: 'Python',
  r: 'R',
  julia: 'Julia',
  js: 'JavaScript',
};

// ─────────────────────────────────────────────────────────────────────────────
// Inline sub-components
// ─────────────────────────────────────────────────────────────────────────────

// Theme-adaptive tooltip. MUI's default tooltip is a fixed dark grey that
// ignores the page's light/dark mode, so paint it from the design tokens —
// they cascade from :root / [data-theme="dark"] on <html> into the portal.
//

type PaletteSnippetsProps = {
  lang: Lang;
  setLang: React.Dispatch<React.SetStateAction<Lang>>;
  oklch: boolean;
  setOklch: React.Dispatch<React.SetStateAction<boolean>>;
  sortedPalette: Swatch[];
};

export function PaletteSnippets(props: PaletteSnippetsProps) {
  const { lang, setLang, oklch, setOklch, sortedPalette } = props;
  return (
    <>
      <Box component="section" sx={sectionSx}>
        <SectionHeader prompt="❯" title={<em>copy &amp; paste</em>} />
        <Box sx={proseColumnSx}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 2,
              mt: 2,
            }}
          >
            <Tabs
              value={lang}
              onChange={(_, v) => setLang(v as Lang)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{
                minHeight: 36,
                '& .MuiTab-root': {
                  fontFamily: typography.mono,
                  fontSize: '11px',
                  minHeight: 36,
                  py: 0,
                  textTransform: 'none',
                  color: 'var(--ink-muted)',
                },
                '& .Mui-selected': { color: 'var(--ink)' },
                '& .MuiTabs-indicator': { backgroundColor: colors.primary },
              }}
            >
              {(Object.keys(LANG_LABELS) as Lang[]).map(l => (
                <Tab key={l} value={l} label={LANG_LABELS[l]} />
              ))}
            </Tabs>
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={oklch}
                  onChange={e => setOklch(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': { color: colors.primary },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                      backgroundColor: colors.primary,
                    },
                  }}
                />
              }
              label={
                <Box
                  sx={{
                    fontFamily: typography.mono,
                    fontSize: '11px',
                    color: 'var(--ink-muted)',
                  }}
                >
                  OKLCH
                </Box>
              }
            />
          </Box>
          <CodeBlock code={snippet(lang, oklch, sortedPalette)} />
        </Box>
      </Box>
    </>
  );
}
