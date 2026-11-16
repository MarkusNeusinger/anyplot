/**
 * `/agent` without a catalogue pair in its query: what the chat does, in the words of the about
 * page's "use with my data" section, a few example pairs that open the chat, the way on to the
 * catalogue, where every other pair starts, and below it the assistant's terms of use in a few
 * quiet lines. The landing page's `.use_my_data()` leads here.
 *
 * It is text and links only, with no request of its own: it opens no session, so a visitor who
 * only reads costs the agents service nothing. The page decides the lane before it shows this (a
 * closed public lane still reads as closed), and keeps it out of the index (`AgentChatPage`).
 * With no feedback of its own, it keeps the site's feedback button, which the layout hides only
 * at an address that names a chat (`RootLayout`).
 */

import { Fragment, type ReactNode } from 'react';

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_TO_LANG } from 'src/constants';
import { paths } from 'src/routes/paths';
import {
  actionButtonSx,
  bodyTextSx,
  inlineCodeSx,
  labelSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { colors, FAB_GAP, FAB_INSET, FAB_SIZE, proseLinkStyle } from 'src/theme';

/** `agent_open`'s `source` for a chat opened from one of the examples below. */
export const AGENT_INTRO_SOURCE = 'agent_intro';

/**
 * One catalogue pair per language, so the examples show that the chat is not Python-only. Each is
 * an implementation under `plots/` that the agents service's readiness scan finds eligible and
 * whose review score is at least 90, the score a first review needs (`QUALITY_THRESHOLD_APPROVAL`),
 * so a first chat starts from a plot that passed the bar. tests/unit/test_agent_intro_examples.py
 * checks that the files exist, so a renamed or removed implementation fails a test instead of
 * leaving a dead end here.
 */
const AGENT_EXAMPLES = [
  { spec: 'scatter-basic', library: 'matplotlib' },
  { spec: 'bar-basic', library: 'ggplot2' },
  { spec: 'line-basic', library: 'd3' },
] as const;

/** The page's title, in the tab and in the head's `og:title`. */
export const AGENT_INTRO_TITLE = 'use with my data | anyplot.ai';
/** The page's description: the about page's two sentences on what the chat does. */
export const AGENT_INTRO_DESCRIPTION =
  "pick any plot, choose .use_my_data(), and paste your data. an agent adapts that plot's code to your columns, renders it in a sandbox with no network access, reviews the render against the catalogue's rubric, repairs it once if needed, and hands back the image and the code.";

/** A link of the examples' list and the closing action: a 44 px target at phone width. */
const targetSx = { display: 'inline-flex', alignItems: 'center', minHeight: { xs: 44, sm: 32 } };

/**
 * The assistant's terms of use, label and sentence, after the way on as the page's fine print, so
 * the two ways in (the examples and the catalogue) stay together above it.
 * Where each sentence holds in the code: the operator's pause is the public door
 * (`AGENT_PUBLIC_ENABLED`, `api/routers/agent_public.py`); the daily limits count the tab's random
 * id and the network (`agents/anyplot/settings.py`); the pause for the day is the day's `attack`
 * strikes (`AGENT_ATTACK_STRIKES`, `locked_out`); the Highcharts note is the chat's own
 * (`HIGHCHARTS_NOTE` in `AgentChatPage`). The last line leads to the legal page's section on
 * what the assistant stores, where and for how long.
 */
const AGENT_TERMS: [string, ReactNode][] = [
  [
    'status',
    'experimental, without warranty: results can be wrong and nobody checks them by hand. the operator may pause it at any time.',
  ],
  [
    'limits',
    'use it only with data you may share, never for unlawful content or automated requests. daily limits apply per tab and per network; a misuse can pause you for the day.',
  ],
  [
    'your code',
    'yours to use, as is. Highcharts needs a licence from Highsoft for commercial use.',
  ],
  [
    'privacy',
    <Box key="privacy" component={RouterLink} to={`${paths.legal}#assistant`} sx={proseLinkStyle}>
      what is stored, where and for how long
    </Box>,
  ],
];

/** The sentences: the body face one step smaller, in the soft ink, which reads 4.5:1 and more. */
const termTextSx = { ...bodyTextSx, fontSize: smallText, color: 'var(--ink-soft)', m: 0 } as const;

/**
 * Where the column reaches the window's right edge (on a phone and a small tablet), the site's
 * feedback button floats over it, and the terms reach the first screen's foot, so without room
 * they would sit under it on arrival. They keep out of its column: the button's inset, size and
 * gap from the window's edge (`FeedbackWidget`), less the layout's side gutter, 16 px and from
 * `sm` 32 px (`RootLayout`), which the column already leaves free. From `md` the column, at most
 * 640 px wide and centred, stands clear of the button.
 */
const buttonClearance = (breakpoint: 'xs' | 'sm', gutter: number) =>
  `${FAB_INSET[breakpoint] + FAB_SIZE[breakpoint] + FAB_GAP - gutter}px`;

export function AgentIntro() {
  return (
    <Box data-testid="agent-intro" sx={{ py: 4, maxWidth: 640, mx: 'auto' }}>
      {/* The Open Graph pair replaces the home page's shell defaults in the head, so the rendered
          page never describes itself as the home page. A link-preview fetcher runs no JavaScript
          and never sees it. No canonical: the page is never indexed. */}
      <title>{AGENT_INTRO_TITLE}</title>
      <meta name="description" content={AGENT_INTRO_DESCRIPTION} />
      <meta property="og:title" content={AGENT_INTRO_TITLE} />
      <meta property="og:description" content={AGENT_INTRO_DESCRIPTION} />
      <SectionHeader prompt="❯" title={<em>use with my data</em>} />
      <Box component="p" sx={{ ...bodyTextSx, m: 0 }}>
        experimental, open to everyone since 2 november 2026.{' '}
        <Box component={RouterLink} to={paths.plots} sx={proseLinkStyle}>
          pick any plot
        </Box>
        , choose{' '}
        <Box component="code" sx={inlineCodeSx}>
          .use_my_data()
        </Box>
        , and paste your data. an agent adapts that plot&apos;s code to your columns, renders it in
        a sandbox with no network access, reviews the render against the catalogue&apos;s rubric,
        repairs it once if needed, and hands back the image and the code. your chat and data live
        only in server memory and are deleted after an hour idle, unless you send feedback.
      </Box>

      <Box
        component="h3"
        id="agent-intro-examples"
        sx={{ ...labelSx, fontWeight: 400, mt: 3, mb: 0.5 }}
      >
        or start with
      </Box>
      <Box
        component="ul"
        aria-labelledby="agent-intro-examples"
        sx={{ listStyle: 'none', p: 0, m: 0 }}
      >
        {AGENT_EXAMPLES.map(({ spec, library }) => {
          const language = LIB_TO_LANG[library] ?? 'python';
          return (
            <Box
              component="li"
              key={`${spec}/${library}`}
              sx={{ ...bodyTextSx, ...targetSx, display: 'flex' }}
            >
              <Box
                component={RouterLink}
                to={paths.agentChat(spec, library, language, AGENT_INTRO_SOURCE)}
                sx={{ ...proseLinkStyle, ...targetSx }}
              >
                {spec} in {library}
              </Box>
              <Box component="span" aria-hidden="true" sx={{ color: 'var(--ink-muted)', mx: 1 }}>
                ·
              </Box>
              <Box component="span" sx={{ color: 'var(--ink-muted)' }}>
                {language}
              </Box>
            </Box>
          );
        })}
      </Box>

      <Box
        component={RouterLink}
        to={paths.plots}
        aria-label="Browse plots"
        sx={{
          ...actionButtonSx,
          ...targetSx,
          mt: 3,
          ml: -1.25,
          textDecoration: 'none',
          '& .action-subject': { opacity: 0.7 },
          '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
        }}
      >
        <Box component="span" className="action-subject">
          plots
        </Box>
        .browse() →
      </Box>

      <Box
        component="dl"
        data-testid="agent-intro-terms"
        sx={{
          display: 'grid',
          // At phone width the label stands above its sentence, which keeps the full width.
          gridTemplateColumns: { xs: 'minmax(0, 1fr)', sm: 'max-content minmax(0, 1fr)' },
          columnGap: 2,
          rowGap: { xs: 0, sm: 0.75 },
          pr: { xs: buttonClearance('xs', 16), sm: buttonClearance('sm', 32), md: 0 },
          mt: 4,
          mb: 0,
        }}
      >
        {AGENT_TERMS.map(([term, text]) => (
          <Fragment key={term}>
            <Box component="dt" sx={{ ...labelSx, lineHeight: 1.6 }}>
              {term}
            </Box>
            <Box component="dd" sx={{ ...termTextSx, mb: { xs: 1, sm: 0 } }}>
              {text}
            </Box>
          </Fragment>
        ))}
      </Box>
    </Box>
  );
}
