import type { ReactNode } from 'react';

import { Navigate, Link as RouterLink, useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { FactTable } from 'src/components/FactTable';
import { SectionHeader } from 'src/components/SectionHeader';
import { ANCHOR_SX, useHashScroll } from 'src/hooks/useHashScroll';
import { paths } from 'src/routes/paths';
import { MOVED_TO_ABOUT } from 'src/routes/redirects';
import { fontSize, proseLinkStyle, semanticColors, subheadingStyle, textStyle } from 'src/theme';

/** 13 px, the smallest size this page allows at phone width: `fontSize.sm` (12.8 px) is under it. */
const KEPT_FONT_SIZE = '0.8125rem';

/**
 * A fact row's second line: how long its data is kept and where it runs, as `label: value`
 * pairs. A span shown as a block, so it can sit inside an anchor span such as #shared-links.
 * The labels are muted and the values keep the cell's ink, because the period is the fact a
 * reader looks for. On a phone each pair takes a line of its own, where a separator would only
 * start a line, so it is hidden there; it stays in the text, so the line's text is the same at
 * every width. Wider, a no-break space ties the separator to the pair before it, so a line can
 * break after the dot but never start with it.
 */
function Kept({ items }: { items: [string, ReactNode][] }) {
  return (
    <Box
      component="span"
      data-kept-line=""
      sx={{ display: 'block', mt: 0.75, fontSize: KEPT_FONT_SIZE, lineHeight: 1.6 }}
    >
      {items.map(([label, value], i) => (
        <Box component="span" key={label} sx={{ display: { xs: 'block', sm: 'inline' } }}>
          {i > 0 && (
            <Box
              component="span"
              sx={{ display: { xs: 'none', sm: 'inline' }, color: semanticColors.mutedText }}
            >
              &nbsp;·{' '}
            </Box>
          )}
          <Box component="span" sx={{ color: semanticColors.mutedText }}>
            {label}:
          </Box>{' '}
          {value}
        </Box>
      ))}
    </Box>
  );
}

/**
 * Where data runs on Google Cloud. The region stays on one line: a break at its hyphen
 * ("europe-" / "west4") reads as two words. Without `services`, a row that ties each of its
 * periods to its own service names only the place.
 */
function GoogleCloud({ services }: { services?: string }) {
  return (
    <>
      Google Cloud{services ? ` (${services})` : ''} in the Netherlands{' '}
      <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
        (europe-west4)
      </Box>
    </>
  );
}

export function LegalPage() {
  const { hash } = useLocation();

  // A fresh load of /legal#assistant (the chat's notice opens one in a new tab) lands on its section.
  useHashScroll();

  // The route's loader sends a fresh load of /legal#transparency on; an in-app link lands here.
  if (hash === MOVED_TO_ABOUT) {
    return <Navigate to={`${paths.about}${MOVED_TO_ABOUT}`} replace />;
  }

  const operatorContactBlock = (
    <>
      <Typography sx={subheadingStyle}>operator</Typography>
      <Typography sx={textStyle}>
        Markus Neusinger
        <br />
        Visp, Switzerland
      </Typography>

      <Typography sx={subheadingStyle}>contact</Typography>
      <Typography sx={textStyle}>
        email:{' '}
        <Link href="mailto:admin@anyplot.ai" sx={proseLinkStyle}>
          admin@anyplot.ai
        </Link>
        <br />
        linkedin:{' '}
        <Link
          href="https://www.linkedin.com/in/markus-neusinger/"
          target="_blank"
          rel="noopener noreferrer"
          sx={proseLinkStyle}
        >
          markus-neusinger
        </Link>
        <br />
        x:{' '}
        <Link
          href="https://x.com/MarkusNeusinger"
          target="_blank"
          rel="noopener noreferrer"
          sx={proseLinkStyle}
        >
          @MarkusNeusinger
        </Link>
        <br />
        github:{' '}
        <Link
          href="https://github.com/MarkusNeusinger"
          target="_blank"
          rel="noopener noreferrer"
          sx={proseLinkStyle}
        >
          MarkusNeusinger
        </Link>
      </Typography>
    </>
  );

  const disclaimerBlock = (
    <>
      <Typography sx={subheadingStyle}>disclaimer</Typography>
      <Typography sx={textStyle}>
        a personal portfolio project. the plot examples are generated and maintained by ai workflows
        and meant as a starting point for your own data. how that works, and my part in it: see{' '}
        <Link component={RouterLink} to={paths.about} sx={proseLinkStyle}>
          about
        </Link>
        . the code is provided &quot;as is&quot; under the MIT License; review it before production
        use.
      </Typography>
    </>
  );

  return (
    <>
      <>
        <title>legal | anyplot.ai</title>
        <meta name="description" content="legal notice and privacy policy for anyplot.ai" />
        <meta property="og:title" content="legal | anyplot.ai" />
        <meta property="og:description" content="legal notice and privacy policy" />
        <link rel="canonical" href="https://anyplot.ai/legal" />
      </>

      <Box sx={{ pb: 4 }}>
        {/* Legal Notice */}
        <Box component="section" id="legal-notice" sx={{ py: { xs: 2, md: 3 }, ...ANCHOR_SX }}>
          <SectionHeader prompt="❯" title={<em>legal notice</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            {operatorContactBlock}
            {disclaimerBlock}
          </Box>
        </Box>

        {/* Privacy Policy */}
        <Box component="section" id="privacy" sx={{ py: { xs: 2, md: 3 }, ...ANCHOR_SX }}>
          <SectionHeader prompt="❯" title={<em>privacy policy</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={subheadingStyle}>who is responsible</Typography>
            <Typography sx={textStyle}>Markus Neusinger (see above).</Typography>

            <Typography sx={subheadingStyle}>in short</Typography>
            <Typography sx={textStyle}>
              • no cookies for visitors
              <br />
              • no accounts, and no name or email unless you type one
              <br />• <strong>no ai training</strong> on what you send
            </Typography>
            <Typography sx={textStyle}>
              the browser&apos;s storage keeps UI settings, your plot votes, a release number, the
              random ids named here and Cloudflare Turnstile&apos;s own item. I sign in through
              Cloudflare Access, which sets its own login cookie.
            </Typography>

            <Typography sx={subheadingStyle}>what is processed</Typography>
            <FactTable
              rows={[
                [
                  'analytics',
                  <>
                    <Link
                      href="https://plausible.io"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      Plausible
                    </Link>{' '}
                    counts page views, searches, clicks, copies and downloads, only in aggregate, on
                    a{' '}
                    <Link
                      href="https://plausible.io/anyplot.ai"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      public dashboard
                    </Link>
                    : no cookies, no cross-site id, no IP address kept. search texts sent up to and
                    including november 2026 still show there.
                    <Kept items={[['where', 'Plausible Analytics (EU, proxied)']]} />
                  </>,
                ],
                [
                  'server logs',
                  <>
                    IP address, URL and user-agent of each request, for security and debugging.
                    <Kept
                      items={[
                        ['kept', '30 days'],
                        ['where', <GoogleCloud services="Logging" />],
                      ]}
                    />
                  </>,
                ],
                [
                  'machine readers, shared links',
                  // Two anchors in one row, for the two tiles on /stats that link here. The shares
                  // start on a line of their own that names them, so a fresh load of #shared-links
                  // lands on a line start rather than mid-sentence; their span runs to the end of
                  // the cell, so it also covers the negative and the periods both kinds share.
                  <Box component="span" id="machine-readers" sx={ANCHOR_SX}>
                    crawlers, ai assistants and mcp clients: one line per request.
                    <Box
                      component="span"
                      id="shared-links"
                      sx={{ ...ANCHOR_SX, display: 'block', mt: 0.75 }}
                    >
                      shared links: counts of the link previews that messengers and social networks
                      fetch. neither holds an IP address or a user-agent.
                      <Kept
                        items={[
                          ['machine reads', 'up to 180 days (Logging, BigQuery)'],
                          ['shares', 'no time limit (SQL)'],
                          ['where', <GoogleCloud />],
                        ]}
                      />
                    </Box>
                  </Box>,
                ],
                [
                  'searches without a hit',
                  <Box component="span" id="search-misses" sx={ANCHOR_SX}>
                    when a gallery search finds nothing, two seconds after you stop typing or when
                    you leave the field, its text (lowercase, first 40 characters) is counted per
                    day, so I see what the catalogue lacks. an e-mail address or a link with http://
                    is not kept; anything else you type may be, so please type no personal data. a
                    row holds no IP address and no time of day; only timestamps could match one to
                    the 30-day server logs, so it is pseudonymous. only I read the list, and I
                    delete an entry on request.
                    <Kept
                      items={[
                        ['kept', '180 days'],
                        ['where', <GoogleCloud services="SQL" />],
                      ]}
                    />
                  </Box>,
                ],
                [
                  'cloudflare',
                  <>
                    as the cdn, Cloudflare uses your IP address to rate-limit, filter bots and
                    absorb DDoS attacks. its Turnstile runs when you send feedback, rate a plot or
                    open the data assistant, and checks that a browser, not a script, is asking. for
                    that it reads your IP address, user-agent and TLS fingerprint and keeps an item
                    in your browser&apos;s storage, with no cookie. anyplot learns only whether the
                    check passed. Cloudflare also uses these signals on its own behalf, to improve
                    the check.
                    <Kept items={[['where', 'global, EU data centers for EU visitors']]} />
                  </>,
                ],
                [
                  'feedback',
                  <>
                    message, reaction, optional contact, page, your window size, user-agent and a
                    random id that ties your own submissions together. I read them, and when I work
                    on one, its message, page and reaction can go to an ai coding assistant (such as
                    Claude Code by Anthropic), which processes it under its provider&apos;s own
                    terms, outside the EU hosting named above, with training on what I send switched
                    off. a salted IP hash limits spam.
                    <Kept
                      items={[
                        ['entries', 'until you ask to delete them'],
                        [
                          'IP hash',
                          'cleared by the next feedback after ten minutes; its salt dies with the server instance',
                        ],
                        ['where', <GoogleCloud services="SQL" />],
                      ]}
                    />
                  </>,
                ],
                [
                  'github',
                  // The username is the issue author's login, which spec-create writes into the
                  // spec's `suggested` field; a pull request can empty that field, while the issue
                  // and the git history stay public.
                  'suggest a plot type there and your public username may be credited in its spec. ask and I remove it; the public history keeps it.',
                ],
              ]}
            />
            <Typography sx={{ ...textStyle, mt: 2 }}>
              hosting: <GoogleCloud services="Run, SQL, Storage, Logging, BigQuery" />. Google Cloud
              and Cloudflare process data under their data processing terms, including their
              safeguards for transfers outside Switzerland and the EU.
            </Typography>

            <Typography sx={subheadingStyle}>why this is allowed</Typography>
            <Typography sx={textStyle}>
              • a legitimate interest in protecting the site, counting its readers, seeing what its
              catalogue lacks, and the assistant&apos;s telemetry and limits
              <br />
              • your request: making the plot you ask the data assistant for
              <br />• your consent to a feedback case: you give it when you send it and can withdraw
              it at any time by asking
            </Typography>

            <Typography id="assistant" sx={{ ...subheadingStyle, ...ANCHOR_SX }}>
              only if you use the data assistant (experimental)
            </Typography>
            <FactTable
              rows={[
                [
                  'what it is',
                  // Its terms of use (status, limits, the code's licence) stand on its own page;
                  // what touches personal data stays in the rows below.
                  <>
                    it adapts a catalogue plot to your data. status, limits and your code: see{' '}
                    <Link component={RouterLink} to={paths.agent} sx={proseLinkStyle}>
                      the data assistant&apos;s page
                    </Link>
                    .
                  </>,
                ],
                [
                  'the model',
                  "what you paste and write goes to Claude by Anthropic, served through Google Cloud Vertex AI in the EU under Google Cloud's data processing terms; your prompts are not used for training. don't paste personal data you are not allowed to share.",
                ],
                [
                  'memory',
                  'a session (data, chat, plots) lives in server memory only and is cleared after an hour idle. the render service keeps its last 16 results in memory.',
                ],
                [
                  'logs',
                  <>
                    no content: never your text, data, column or file names. telemetry holds event
                    types, formats, sizes, plot type, library, language code (rare ones as
                    &quot;other&quot;), attempts, defect ids, statuses, latencies and token counts.
                    for 30 days, the time or the token counts of a telemetry line could match it to
                    the request that wrote it.
                    <Kept
                      items={[
                        ['telemetry', 'up to 180 days'],
                        ['where', <GoogleCloud services="Logging, BigQuery" />],
                      ]}
                    />
                  </>,
                ],
                [
                  'ids',
                  'a random tab id stands in for you. the per-tab limits and a pause after misuse go by that id, the per-network limits by your IP address. both ids are salted with a value that lives only as long as the server instance, in memory, never written down. nothing durable: only timestamps could match them to the 30-day server logs, so they are pseudonymous. admins: a keyed hash (HMAC).',
                ],
                [
                  'feedback',
                  <>
                    only when you send feedback. a private bucket then keeps the conversation, a
                    profile of your data with its first 5 rows, and the plot&apos;s code and images.
                    it keeps the whole data file only if you tick{' '}
                    <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
                      &quot;# include data.csv&quot;
                    </Box>
                    ; the box starts unticked, which leaves out that file only. a triage row then
                    keeps your reaction, message, hashes of your tab id and of the session id, and
                    the run&apos;s details. I read the cases to fix what went wrong, also with ai
                    coding assistants (such as Claude Code by Anthropic) and in test runs on other
                    ai models: your reaction and message, the conversation, the data sample or file,
                    the plot and its code, the run&apos;s details and the two hashes. those tools
                    process a case under their providers&apos; own terms, outside the EU route named
                    above, with training on what I send switched off.
                    <Kept
                      items={[
                        ['case files', '180 days'],
                        ['case rows', 'until you ask to delete them'],
                        ['where', <GoogleCloud services="Storage, SQL" />],
                      ]}
                    />
                  </>,
                ],
              ]}
            />

            <Typography sx={subheadingStyle}>your rights</Typography>
            <Typography sx={textStyle}>
              you can ask what is stored about you and have it corrected, erased or restricted,
              object to the processing for a reason specific to your situation, and complain to a
              data protection authority. a few lines to{' '}
              <Link href="mailto:admin@anyplot.ai" sx={proseLinkStyle}>
                admin@anyplot.ai
              </Link>{' '}
              are enough, also to have a feedback case deleted early. tell me what you sent and
              roughly when, or the contact you typed, so I can find it. log lines cannot be deleted
              one by one: they expire after 30 days (server logs) or 180 days (machine reads,
              assistant telemetry). the database&apos;s automatic backups keep a deleted entry for
              about 30 days.
            </Typography>
          </Box>
        </Box>

        <Typography
          sx={{
            textAlign: 'center',
            fontSize: fontSize.sm,
            color: semanticColors.mutedText,
            mt: 2,
          }}
        >
          last updated: November 2026
        </Typography>
      </Box>
    </>
  );
}
