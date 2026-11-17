/**
 * `/agent` without a catalogue pair in its query: what the chat does, in the words of the about
 * page's "use with my data" section, and which model it runs on; a few example pairs that open the
 * chat; the way on to the catalogue, where every other pair starts; one line on how the chat is
 * built, with a link to its design on GitHub; and below it the assistant's terms of use in a few
 * quiet lines (`AgentTerms`, which the closed notice carries too). The landing page's
 * `.use_my_data()` leads here.
 *
 * It is text and links only, with no request of its own: it opens no session, so a visitor who
 * only reads costs the agents service nothing. The page decides the lane before it shows this (a
 * closed public lane reads as closed, with the terms below the notice), and keeps it out of the
 * index (`AgentChatPage`). With no feedback of its own, it keeps the site's feedback button,
 * which the layout hides only at an address that names a chat (`RootLayout`).
 */

import { Fragment, type ReactNode } from 'react';

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { GITHUB_URL, LIB_TO_LANG } from 'src/constants';
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
  "pick any plot, choose .use_my_data() on its page, and paste your data. an agent adapts that plot's code to your columns, renders it in a sandbox with no network access, reviews the render against the catalogue's rubric, repairs it once if needed, and hands back the image and the code.";

/**
 * Where the chat's design and code are described: the README's section on "use with my data", by
 * GitHub's anchor for its heading. tests/unit/test_agent_intro_crawler_copy.py checks that the
 * README has that heading, so a renamed one fails a test instead of landing the link at the
 * README's top.
 */
const AGENT_DESIGN_URL = `${GITHUB_URL}#use-with-my-data-agent-chat`;

/**
 * A link of the examples' list and the closing action: a box of its own, 44 px high at phone width
 * and 32 px from `sm` up, which the layout makes room for.
 */
const targetSx = { display: 'inline-flex', alignItems: 'center', minHeight: { xs: 44, sm: 32 } };

/**
 * The privacy line's link: at phone width the same box as the links above, 44 px high and in the
 * layout, so its target stays between its own label and the next one instead of reaching over
 * them. The link wraps inside the box on a phone up to about 390 px wide; on a wider phone it
 * takes one line at the box's top, under its label like the other sentences, and the rest of the
 * target lies below it. From `sm` up the label stands beside the sentence, so the box is only as
 * tall as its text and the two stay level.
 */
const privacyLinkSx = {
  ...proseLinkStyle,
  display: 'inline-flex',
  alignItems: 'flex-start',
  minHeight: { xs: 44, sm: 0 },
} as const;

/**
 * The link at the end of the line on how the chat is built. Inside a sentence, a 44 px box would
 * make its line taller than the others, so at phone width the link keeps its place in the line and
 * is padded 13 px above and below its 18 px of text instead, which does not move a line: the
 * target reaches only into the plain text above it and stays well clear of the heading below. It
 * stays on one line, so the target is one box.
 */
const githubLinkSx = {
  ...proseLinkStyle,
  whiteSpace: 'nowrap',
  // 13 + 18 + 13 = 44: the padding completes the link's 18 px of text to a 44 px target.
  py: { xs: '13px', sm: 0 },
} as const;

/** The heading above the terms, here and under the closed notice. */
export const AGENT_TERMS_HEADING = 'ground rules';

/**
 * The assistant's terms of use, label and sentence, after the way on as the page's fine print, so
 * the two ways in (the examples and the catalogue) stay together above it.
 * Where each sentence holds in the code: the Highcharts note is the chat's own (`HIGHCHARTS_NOTE`
 * in `AgentChatPage`); the second line leads to the legal page's section on what the assistant
 * stores, where and for how long; the daily limits count the tab's random id and the network
 * (`agents/anyplot/settings.py`); the pause for the day is the day's `attack` strikes
 * (`AGENT_ATTACK_STRIKES`, `locked_out`); the operator's pause is the public door
 * (`AGENT_PUBLIC_ENABLED`, `api/routers/agent_public.py`).
 */
const AGENT_TERMS: [string, ReactNode][] = [
  [
    'your code',
    'yours to use, as is. Highcharts needs a licence from Highsoft for commercial use.',
  ],
  [
    'privacy',
    <Box key="privacy" component={RouterLink} to={`${paths.legal}#assistant`} sx={privacyLinkSx}>
      what is stored, where and for how long
    </Box>,
  ],
  [
    'limits',
    'use it only with data you may share, never for unlawful content or automated requests. daily limits apply per tab and per network; a misuse can pause you for the day.',
  ],
  [
    'status',
    'experimental, without warranty: results can be wrong and nobody checks them by hand. the operator may pause it at any time.',
  ],
];

/** The explainer's two small headings, "or start with" and the terms' own. */
const subheadingSx = { ...labelSx, fontWeight: 400, mb: 0.5 } as const;

/** The sentences: the body face one step smaller, in the soft ink, which reads 4.5:1 and more. */
const termTextSx = { ...bodyTextSx, fontSize: smallText, color: 'var(--ink-soft)', m: 0 } as const;

/**
 * Where the column reaches the window's right edge (on a phone and a small tablet), the site's
 * feedback button floats over it, and the line on how the chat is built and the terms reach the
 * first screen's foot, so without room they would sit under it on arrival. They keep out of its
 * column (`clearOfButtonSx`): the button's inset, size and
 * gap from the window's edge (`FeedbackWidget`), less the layout's side gutter, 16 px and from
 * `sm` 32 px (`RootLayout`), which the column already leaves free. From `md` the column, at most
 * 640 px wide (560 px under the closed notice) and centred, stands clear of the button.
 */
const buttonClearance = (breakpoint: 'xs' | 'sm', gutter: number) =>
  `${FAB_INSET[breakpoint] + FAB_SIZE[breakpoint] + FAB_GAP - gutter}px`;

/** The right padding that keeps a line at the column's foot out of the button's column. */
const clearOfButtonSx = {
  pr: { xs: buttonClearance('xs', 16), sm: buttonClearance('sm', 32), md: 0 },
} as const;

/**
 * The assistant's terms of use as labelled lines under their heading: the explainer's fine print,
 * and the same block under the closed notice (`LaneClosed` in `AgentChatPage`): `/agent` is where
 * the assistant's terms live, so they must stand there also while the operator has paused the
 * assistant. Text and links only: it opens no session and asks nothing. The crawler copy of
 * `/agent` (`/seo-proxy/agent` in `api/routers/seo.py`) carries the same heading and sentences,
 * and tests/unit/test_agent_intro_crawler_copy.py fails when the two differ. A fragment, so the
 * list stays the last element of the explainer and of the notice.
 */
export function AgentTerms() {
  return (
    <>
      <Box component="h3" sx={{ ...subheadingSx, mt: 4 }}>
        {AGENT_TERMS_HEADING}
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
          ...clearOfButtonSx,
          my: 0,
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
    </>
  );
}

export function AgentIntro() {
  return (
    <Box data-testid="agent-intro" sx={{ py: 4, maxWidth: 640, mx: 'auto' }}>
      {/* The Open Graph pair replaces the home page's shell defaults in the head, so the rendered
          page never describes itself as the home page. A link-preview fetcher runs no JavaScript
          and never sees it; one that nginx recognises gets the crawler copy instead
          (`/seo-proxy/agent`), with the same title and description. No canonical: the page is
          never indexed. */}
      <title>{AGENT_INTRO_TITLE}</title>
      <meta name="description" content={AGENT_INTRO_DESCRIPTION} />
      <meta property="og:title" content={AGENT_INTRO_TITLE} />
      <meta property="og:description" content={AGENT_INTRO_DESCRIPTION} />
      <SectionHeader prompt="❯" title={<em>use with my data</em>} />
      <Box component="p" sx={{ ...bodyTextSx, m: 0 }}>
        experimental, open to everyone since november 2026.{' '}
        <Box component={RouterLink} to={paths.plots} sx={proseLinkStyle}>
          pick any plot
        </Box>
        , choose{' '}
        <Box component="code" sx={inlineCodeSx}>
          .use_my_data()
        </Box>{' '}
        on its page, and paste your data. an agent adapts that plot&apos;s code to your columns,
        renders it in a sandbox with no network access, reviews the render against the
        catalogue&apos;s rubric, repairs it once if needed, and hands back the image and the code.
        the model is Claude by Anthropic, served through Google Cloud Vertex AI in the EU. your chat
        and data live only in server memory and are deleted after an hour idle, unless you send
        feedback.
      </Box>

      <Box component="h3" id="agent-intro-examples" sx={{ ...subheadingSx, mt: 3 }}>
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

      <Box component="p" sx={{ ...termTextSx, ...clearOfButtonSx, mt: 3 }}>
        how it works: one agent talks to you, and the loop around it is plain code. the design and
        the code are{' '}
        <Box
          component="a"
          href={AGENT_DESIGN_URL}
          target="_blank"
          rel="noopener noreferrer"
          sx={githubLinkSx}
        >
          on GitHub
        </Box>
        .
      </Box>

      <AgentTerms />
    </Box>
  );
}
