import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';

import { useAnalytics } from 'src/hooks';
import { useAgentLaneOpen } from 'src/hooks/useAgentLaneOpen';
import type { PlotOfTheDayData } from 'src/hooks/usePlotOfTheDay';
import { paths } from 'src/routes/paths';
import { PlotOfTheDayTerminal } from 'src/sections/landing/PlotOfTheDayTerminal';
import { TypewriterText } from 'src/sections/landing/TypewriterText';
import { colors, typography } from 'src/theme';

interface HeroSectionProps {
  potd?: PlotOfTheDayData | null;
}

/**
 * Full-width editorial hero. Text column left, terminal-framed plot of the
 * day right. Scales up to catalog tier so the plot becomes the visual anchor
 * on ultrawide. Each landing-page section below mirrors this width so the
 * page reads as one continuous grid.
 */
export function HeroSection({ potd = null }: HeroSectionProps) {
  const { trackEvent } = useAnalytics();
  return (
    <Box
      sx={{
        py: { xs: 5, md: 4 },
        display: 'grid',
        gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(320px, 1fr) minmax(0, 1.8fr)' },
        gap: { xs: 4, md: 6, lg: 8 },
        alignItems: 'center',
      }}
    >
      {/* Left: editorial text */}
      <Box sx={{ maxWidth: 560, minWidth: 0 }}>
        <Box
          sx={{
            animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) backwards',
            fontFamily: typography.mono,
            fontSize: '11px',
            letterSpacing: '0.08em',
            color: 'var(--ink-muted)',
            mb: 3,
            display: 'flex',
            alignItems: 'center',
            gap: 1.25,
            '&::before': {
              content: '""',
              display: 'inline-block',
              width: 18,
              height: '1px',
              background: 'var(--rule)',
            },
          }}
        >
          the open plot catalogue
        </Box>

        <Box
          component="h1"
          sx={{
            animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.1s backwards',
            fontFamily: typography.serif,
            fontWeight: 400,
            fontSize: { xs: '2.5rem', sm: '3rem', md: 'clamp(2.75rem, 4.5vw, 4.75rem)' },
            lineHeight: 0.95,
            letterSpacing: '-0.03em',
            color: 'var(--ink)',
            m: 0,
            mb: 3,
          }}
        >
          <Box
            component="span"
            sx={{
              fontFamily: typography.mono,
              fontWeight: 700,
              fontSize: '0.75em',
              letterSpacing: '-0.02em',
            }}
          >
            any
            <Box
              component="span"
              sx={{
                color: colors.primary,
                display: 'inline-block',
                transform: 'scale(1.3)',
                mx: '2px',
              }}
            >
              .
            </Box>
            plot
            <Box component="span" sx={{ fontWeight: 400, opacity: 0.45 }}>
              ()
            </Box>
          </Box>
          <br />
          <Box
            component="span"
            sx={{
              fontFamily: typography.serif,
              fontWeight: 400,
              fontStyle: 'italic',
              fontFeatureSettings: '"ss01"',
              whiteSpace: 'nowrap',
              fontSize: '0.75em',
            }}
          >
            — any library.
          </Box>
        </Box>

        <Box
          component="p"
          sx={{
            animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.15s backwards',
            fontFamily: typography.mono,
            fontSize: { xs: '0.9375rem', sm: '1rem', md: '1.125rem' },
            lineHeight: 1.4,
            color: 'var(--ink)',
            mt: 0,
            mb: 2.5,
            fontWeight: 500,
            letterSpacing: '-0.005em',
            textAlign: 'center',
          }}
        >
          from .md to art.
        </Box>

        <Box
          sx={{
            animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.2s backwards',
            fontFamily: typography.serif,
            fontSize: { xs: '1rem', md: '1.1875rem' },
            lineHeight: 1.55,
            color: 'var(--ink-soft)',
            mb: 4,
            fontWeight: 300,
          }}
        >
          every plot begins as a library-agnostic spec. ai drafts implementations across every
          supported library, validates them against quality criteria, and keeps them current. you
          discover, copy, and adapt — plug in <em>your</em> data. that&apos;s it.
        </Box>

        <TypewriterText
          lines={['steal like an artist.']}
          charDelay={68}
          sx={{
            animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.25s backwards',
            fontFamily: typography.serif,
            fontSize: { xs: '1.125rem', md: '1.375rem' },
            lineHeight: 1.35,
            color: 'var(--ink)',
            mb: 4,
            fontWeight: 400,
            fontStyle: 'italic',
          }}
        />

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2.5,
            flexWrap: 'wrap',
            animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.3s backwards',
          }}
        >
          <PrimaryCta
            to={paths.plots}
            subject="plots"
            verb="browse"
            ariaLabel="Browse plots"
            onClick={() =>
              trackEvent('nav_click', { source: 'hero_cta_browse', target: paths.plots })
            }
          />
          <Box
            aria-hidden="true"
            sx={{
              fontFamily: typography.mono,
              fontSize: '13px',
              color: 'var(--ink-muted)',
              userSelect: 'none',
            }}
          >
            |
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
            <SecondaryLink
              to={paths.mcp}
              subject="mcp"
              verb="connect"
              ariaLabel="Connect via MCP"
              onClick={() => trackEvent('nav_click', { source: 'hero_mcp', target: paths.mcp })}
            />
            <SecondaryLink
              href="https://github.com/MarkusNeusinger/anyplot"
              subject="github"
              verb="clone"
              ariaLabel="Clone on GitHub"
              external
              onClick={() => trackEvent('nav_click', { source: 'hero_github', target: 'github' })}
            />
          </Box>
        </Box>
        <AgentEntry
          onClick={() =>
            trackEvent('nav_click', { source: 'hero_use_my_data', target: paths.agent })
          }
        />
      </Box>

      {/* Right: terminal plot */}
      <PlotOfTheDayTerminal
        potd={potd}
        sizes="(max-width: 899px) 92vw, (max-width: 1600px) 60vw, 1400px"
      />
    </Box>
  );
}

/**
 * The hero's entry to "use with my data", shown only while the public agent lane is open
 * (`useAgentLaneOpen`), so closing the lane on the server removes it too. Two lines in one
 * link, as the chat's plot button names its action over what a click does: the name,
 * `.use_my_data()`, the idiom of the plot page's own entry, over plain words on what the
 * feature does, so a reader who does not read code learns it exists. A catalogue plot, not
 * any plot: a pair the agent cannot adapt (a map spec, a blocked file) has no entry on its
 * plot page, and this line says no more than that page does. A text link in
 * the secondary links' size, so it never outweighs `plots.browse()`. It leads to `/agent`
 * without a plot, which explains the chat and leads on to the catalogue or to a few example
 * plots: the visitor still picks the plot before a chat opens. Tracked as
 * `nav_click{source: hero_use_my_data}`. No "experimental" here: the chat's notice says it.
 *
 * While the lane's answer is out, the entry keeps its box, invisible and out of reach (no link,
 * hidden from assistive technology), so the answer moves nothing below it: in one column the
 * plot of the day sits under it, and in two columns it sets the left column's height, which
 * centres the card. The open lane, the usual answer, then shows the entry in place. Only a
 * closed lane, the rare answer, removes the box, and the content below moves up once.
 */
export const AGENT_ENTRY_NAME = '.use_my_data()';
/** What the feature does, in plain words. */
export const AGENT_ENTRY_TEXT = 'an ai agent adapts a catalogue plot to your data';
/** The link's accessible name: words rather than the method-call style, the plain line kept. */
export const AGENT_ENTRY_LABEL =
  'Use with my data: an AI agent adapts a catalogue plot to your data';

function AgentEntry({ onClick }: { onClick: () => void }) {
  const open = useAgentLaneOpen();
  if (open === false) return null;
  const pending = open === null;
  // The placeholder is a plain element, so nothing can focus or click it; the link that replaces
  // it is a new element, whose rise plays as it appears.
  const elementProps = pending
    ? { component: 'span' as const, 'aria-hidden': true }
    : { component: RouterLink, to: paths.agent, onClick, 'aria-label': AGENT_ENTRY_LABEL };
  return (
    <Box
      {...elementProps}
      data-testid="hero-agent-entry"
      sx={{
        visibility: pending ? 'hidden' : 'visible',
        animation: 'rise 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) 0.35s backwards',
        display: 'inline-flex',
        flexDirection: 'column',
        gap: 0.25,
        mt: 3,
        fontFamily: typography.mono,
        fontSize: '13px',
        lineHeight: 1.5,
        color: 'var(--ink-soft)',
        textDecoration: 'none',
        '& .entry-name': { color: 'var(--ink)', fontWeight: 500, transition: 'color 0.2s' },
        '&:hover .entry-name': { color: colors.primary },
        '&:focus-visible': {
          outline: `2px solid ${colors.primary}`,
          outlineOffset: 2,
          borderRadius: '2px',
        },
      }}
    >
      <Box component="span" className="entry-name">
        {AGENT_ENTRY_NAME} →
      </Box>
      {/* Balanced: where the line is wider than the column (a phone), it breaks into two even
          lines instead of leaving one word alone on the second. */}
      <Box component="span" sx={{ textWrap: 'balance' }}>
        {AGENT_ENTRY_TEXT}
      </Box>
    </Box>
  );
}

function PrimaryCta({
  to,
  subject,
  verb,
  ariaLabel,
  onClick,
}: {
  to: string;
  subject: string;
  verb: string;
  ariaLabel: string;
  onClick?: () => void;
}) {
  return (
    <Box
      component={RouterLink}
      to={to}
      onClick={onClick}
      aria-label={ariaLabel}
      sx={{
        textDecoration: 'none',
        fontFamily: typography.mono,
        fontSize: '13px',
        padding: '13px 22px',
        borderRadius: '99px',
        border: '1px solid transparent',
        display: 'inline-flex',
        alignItems: 'center',
        gap: 1.25,
        bgcolor: 'var(--ink)',
        color: 'var(--bg-page)',
        transition: 'all 0.2s',
        '& .cta-subject': { opacity: 0.55, transition: 'opacity 0.2s' },
        '&:hover': { bgcolor: colors.primary, color: '#FFF' },
        '&:hover .cta-subject': { opacity: 0.8 },
        '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
      }}
    >
      <Box component="span">
        <Box component="span" className="cta-subject">
          {subject}
        </Box>
        {`.${verb}()`}
      </Box>{' '}
      <Box component="span">→</Box>
    </Box>
  );
}

function SecondaryLink({
  to,
  href,
  subject,
  verb,
  ariaLabel,
  external,
  onClick,
}: {
  to?: string;
  href?: string;
  subject: string;
  verb: string;
  ariaLabel: string;
  external?: boolean;
  onClick?: () => void;
}) {
  const linkProps = external
    ? { component: 'a' as const, href, target: '_blank', rel: 'noopener noreferrer' }
    : { component: RouterLink, to };

  return (
    <Box
      {...linkProps}
      onClick={onClick}
      aria-label={ariaLabel}
      sx={{
        textDecoration: 'none',
        fontFamily: typography.mono,
        fontSize: '13px',
        color: 'var(--ink-soft)',
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        transition: 'color 0.2s',
        '& .link-subject': { opacity: 0.7, transition: 'opacity 0.2s' },
        '&:hover': { color: colors.primary },
        '&:hover .link-subject': { opacity: 1 },
        '&:focus-visible': {
          outline: `2px solid ${colors.primary}`,
          outlineOffset: 2,
          borderRadius: '2px',
        },
      }}
    >
      <Box component="span">
        <Box component="span" className="link-subject">
          {subject}
        </Box>
        {`.${verb}()`}
      </Box>
    </Box>
  );
}
