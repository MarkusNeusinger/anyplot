/**
 * `/agent` without a catalogue pair in its query: what the chat does, in the words of the about
 * page's "use with my data" section, a few example pairs that open the chat, and the way on to
 * the catalogue, where every other pair starts. The landing page's `.use_my_data()` leads here.
 *
 * It is text and links only, with no request of its own: it opens no session, so a visitor who
 * only reads costs the agents service nothing. The page decides the lane before it shows this (a
 * closed public lane still reads as closed), and keeps it out of the index (`AgentChatPage`).
 */

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_TO_LANG } from 'src/constants';
import { paths } from 'src/routes/paths';
import { actionButtonSx, bodyTextSx, inlineCodeSx, labelSx } from 'src/sections/agent-chat/styles';
import { colors, proseLinkStyle } from 'src/theme';

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

/** The page's description: the about page's two sentences on what the chat does. */
export const AGENT_INTRO_DESCRIPTION =
  "pick any plot, choose .use_my_data(), and paste your data. an agent adapts that plot's code to your columns, renders it in a sandbox with no network access, reviews the render against the catalogue's rubric, repairs it once if needed, and hands back the image and the code.";

/** A link of the examples' list and the closing action: a 44 px target at phone width. */
const targetSx = { display: 'inline-flex', alignItems: 'center', minHeight: { xs: 44, sm: 32 } };

export function AgentIntro() {
  return (
    <Box data-testid="agent-intro" sx={{ py: 4, maxWidth: 640, mx: 'auto' }}>
      <title>use with my data | anyplot.ai</title>
      <meta name="description" content={AGENT_INTRO_DESCRIPTION} />
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
    </Box>
  );
}
