import { type ReactNode, useEffect } from 'react';

import { useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { GITHUB_URL } from 'src/constants';
import {
  fontSize,
  proseLinkStyle,
  semanticColors,
  subheadingStyle,
  tableStyle,
  textStyle,
} from 'src/theme';

const AVATAR_URL = 'https://storage.googleapis.com/anyplot-static/images/markusneusinger.webp';

/** Where a linked section lands: below the sticky masthead (42 to 44 px), with a little air. */
const ANCHOR_SX = { scrollMarginTop: '56px' } as const;

/** An external link in the page's prose style, opened in a new tab. */
function Ext({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} target="_blank" rel="noopener" sx={proseLinkStyle}>
      {children}
    </Link>
  );
}

/** A two-column fact table: a short label as the row header, then the fact. */
function FactTable({
  rows,
  labelWidth = '25%',
}: {
  rows: [string, ReactNode][];
  labelWidth?: string;
}) {
  return (
    <Table
      sx={{
        ...tableStyle,
        '& .MuiTableCell-body': { verticalAlign: 'top' },
        // :first-child, not :first-of-type: the label is a <th>, so the value <td> is a first of its type too.
        '& .MuiTableCell-root:first-child': {
          fontWeight: 500,
          color: 'var(--ink-soft)',
          width: labelWidth,
        },
      }}
    >
      <TableBody>
        {rows.map(([label, fact]) => (
          <TableRow key={label}>
            <TableCell component="th" scope="row">
              {label}
            </TableCell>
            <TableCell>{fact}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

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

  // The route loads lazily, after the browser has looked for the fragment and not found it, so a
  // fresh load of /legal#assistant (the chat's notice opens one in a new tab) would stay at the top.
  // Scroll to it once the page is there; ANCHOR_SX keeps it clear of the sticky masthead.
  useEffect(() => {
    if (!hash) return;
    document.getElementById(hash.slice(1))?.scrollIntoView?.();
  }, [hash]);

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

  const otherProjectsBlock = (
    <>
      <Typography sx={subheadingStyle}>other projects</Typography>
      <Typography sx={textStyle}>
        {/* no noreferrer — own sites, keep the referrer for their analytics */}
        <Link href="https://kurrentschrift.ink" target="_blank" rel="noopener" sx={proseLinkStyle}>
          kurrentschrift.ink
        </Link>{' '}
        — read and write old german cursive
        <br />
        <Link
          href="https://github.com/MarkusNeusinger/cite-citadel"
          target="_blank"
          rel="noopener"
          sx={proseLinkStyle}
        >
          cite-citadel
        </Link>{' '}
        — llm-maintained, fully-cited personal wiki
      </Typography>
    </>
  );

  const disclaimerBlock = (
    <>
      <Typography sx={subheadingStyle}>disclaimer</Typography>
      <Typography sx={textStyle}>
        a personal portfolio project: plot examples generated and maintained by ai workflows, meant
        as a starting point for your own data. the code is provided &quot;as is&quot; under the MIT
        License; review it before production use.
      </Typography>
    </>
  );

  return (
    <>
      <>
        <title>legal | anyplot.ai</title>
        <meta
          name="description"
          content="legal notice, privacy policy, and transparency information for anyplot.ai"
        />
        <meta property="og:title" content="legal | anyplot.ai" />
        <meta
          property="og:description"
          content="legal notice, privacy policy, and transparency information"
        />
        <link rel="canonical" href="https://anyplot.ai/legal" />
      </>

      <Box sx={{ pb: 4 }}>
        {/* Legal Notice */}
        <Box component="section" id="legal-notice" sx={{ py: { xs: 2, md: 3 }, ...ANCHOR_SX }}>
          <SectionHeader prompt="❯" title={<em>legal notice</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Box
              sx={{
                display: 'flex',
                gap: 6,
                alignItems: 'center',
                flexDirection: { xs: 'column', sm: 'row' },
                mb: 2,
              }}
            >
              <Box
                component="img"
                src={AVATAR_URL}
                alt=""
                aria-hidden="true"
                width={240}
                height={518}
                loading="lazy"
                sx={{ width: 120, height: 'auto', flexShrink: 0, display: 'block' }}
              />
              <Box sx={{ flex: 1, minWidth: 0 }}>{operatorContactBlock}</Box>
            </Box>
            {disclaimerBlock}
            {otherProjectsBlock}
          </Box>
        </Box>

        {/* Privacy Policy */}
        <Box component="section" id="privacy" sx={{ py: { xs: 2, md: 3 }, ...ANCHOR_SX }}>
          <SectionHeader prompt="❯" title={<em>privacy policy</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={subheadingStyle}>who is responsible</Typography>
            <Typography sx={textStyle}>Markus Neusinger (see above).</Typography>

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
                    : no cookies, no cross-site id, no IP address kept.
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
                    crawlers, ai assistants and mcp clients: one content-free line per request, with
                    vendor and purpose, whether Cloudflare verified it, the page or file and the
                    status, and nothing about anyone&apos;s browsing.
                    <Box
                      component="span"
                      id="shared-links"
                      sx={{ ...ANCHOR_SX, display: 'block', mt: 0.75 }}
                    >
                      shared links: link previews that messengers and social networks fetch, counted
                      per day, platform and page, and whether Cloudflare verified the fetcher, with
                      no time of day and nothing about who shared. neither holds an IP address or a
                      user-agent.
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
                  'cloudflare',
                  <>
                    as the cdn, Cloudflare uses your IP address to rate-limit, filter bots and
                    absorb DDoS attacks. when you send feedback, rate a plot or open the data
                    assistant, its Turnstile checks that a browser, not a script, is asking: it
                    reads your IP address, user-agent and TLS fingerprint and keeps an item in your
                    browser&apos;s storage, with no cookie. anyplot learns only whether the check
                    passed. Cloudflare also uses these signals on its own behalf, to improve the
                    check.
                    <Kept items={[['where', 'global, EU data centers for EU visitors']]} />
                  </>,
                ],
                [
                  'feedback',
                  <>
                    message, reaction, optional contact, page, your window size, user-agent and a
                    random id that ties your own submissions together, read only by the operator. a
                    salted IP hash limits spam.
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
                  'suggest a plot type there and your public username may be credited in its spec.',
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
              a legitimate interest in protecting the site, counting its readers, and the
              assistant&apos;s telemetry and limits; your request: making the plot you ask the data
              assistant for; and your consent to a feedback case, given when you send it and
              withdrawable at any time by asking.
            </Typography>

            <Typography sx={subheadingStyle}>what we do not do</Typography>
            <Typography sx={textStyle}>
              • no cookies for visitors; the browser&apos;s storage keeps UI settings, your plot
              votes, a release number, the random ids named here and Cloudflare Turnstile&apos;s own
              item. admins sign in through Cloudflare Access, which sets its own login cookie
              <br />
              • no accounts, and no name or email unless you type one
              <br />• <strong>no ai training</strong> on what you send
            </Typography>

            <Typography id="assistant" sx={{ ...subheadingStyle, ...ANCHOR_SX }}>
              only if you use the data assistant (experimental)
            </Typography>
            <FactTable
              rows={[
                [
                  'what it is',
                  'it adapts a catalogue plot to your data. experimental, without warranty: results can be wrong and nobody checks them by hand. the operator may pause it at any time.',
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
                  'a random tab id stands in for you, and the per-network limits count your IP address; both are salted with a value that lives only as long as the server instance, in memory, never written down. nothing durable: only timestamps could match them to the 30-day server logs, so they are pseudonymous. admins: a keyed hash (HMAC).',
                ],
                [
                  'feedback',
                  <>
                    only when you send feedback: a private bucket keeps the conversation, a profile
                    of your data with its first 5 rows, the plot&apos;s code and images, and the
                    whole data file only if you tick{' '}
                    <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
                      &quot;# include data.csv&quot;
                    </Box>{' '}
                    (it starts unticked, which leaves out that file only), and a triage row keeps
                    your reaction, message, a hash of your tab id and the run&apos;s details.
                    <Kept
                      items={[
                        ['case files', '180 days'],
                        ['case rows', 'until you ask to delete them'],
                        ['where', <GoogleCloud services="Storage, SQL" />],
                      ]}
                    />
                  </>,
                ],
                [
                  'limits',
                  'use it only with data you may share, never for unlawful content or automated requests. daily limits apply per tab and per network; a misuse can pause you for the day.',
                ],
                [
                  'your code',
                  'yours to use, as is. Highcharts needs a licence from Highsoft for commercial use.',
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
              are enough, also to have a feedback case deleted early.
            </Typography>
          </Box>
        </Box>

        {/* Transparency */}
        <Box component="section" id="transparency" sx={{ py: { xs: 2, md: 3 }, ...ANCHOR_SX }}>
          <SectionHeader prompt="❯" title={<em>transparency</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={textStyle}>open source, down to what it costs to run.</Typography>

            <Typography sx={subheadingStyle}>technology stack</Typography>
            <FactTable
              rows={[
                [
                  'site',
                  <>
                    <Ext href="https://react.dev">React</Ext> 19,{' '}
                    <Ext href="https://vite.dev">Vite</Ext>, <Ext href="https://mui.com">MUI</Ext> 9
                    with <Ext href="https://mui.com/x/">MUI X</Ext>,{' '}
                    <Ext href="https://typescriptlang.org">TypeScript</Ext>
                  </>,
                ],
                [
                  'api',
                  <>
                    <Ext href="https://python.org">Python</Ext> 3.14,{' '}
                    <Ext href="https://fastapi.tiangolo.com">FastAPI</Ext>,{' '}
                    <Ext href="https://sqlalchemy.org">SQLAlchemy</Ext>,{' '}
                    <Ext href="https://postgresql.org">PostgreSQL</Ext> 18
                  </>,
                ],
                [
                  'catalogue pipeline',
                  <>
                    <Ext href="https://github.com/features/actions">GitHub Actions</Ext> with Claude
                    (<Ext href="https://www.anthropic.com/claude-code">Claude Code</Ext>); 15
                    plotting libraries in Python, R, Julia and JavaScript
                  </>,
                ],
                [
                  'data assistant',
                  <>
                    <Ext href="https://google.github.io/adk-docs/">Google ADK</Ext>,{' '}
                    <Ext href="https://www.anthropic.com/claude/haiku">Claude Haiku 5.5</Ext> via{' '}
                    <Ext href="https://cloud.google.com/vertex-ai">Vertex AI</Ext> (EU), plots
                    rendered in Cloud Run sandboxes (<Ext href="https://gvisor.dev">gVisor</Ext>)
                  </>,
                ],
                [
                  'google cloud',
                  <>
                    <Ext href="https://cloud.google.com/run">Cloud Run</Ext>, Cloud SQL, Cloud
                    Storage, Cloud Logging, BigQuery, Cloud Build and Artifact Registry in the
                    Netherlands (europe-west4), plus Secret Manager and Cloud Monitoring
                  </>,
                ],
                [
                  'edge & analytics',
                  <>
                    <Ext href="https://cloudflare.com">Cloudflare</Ext>,{' '}
                    <Ext href="https://plausible.io">Plausible</Ext> (no cookies,{' '}
                    <Ext href="https://plausible.io/anyplot.ai">public dashboard</Ext>)
                  </>,
                ],
                [
                  'reviews',
                  <>
                    <Ext href="https://deepmind.google/technologies/gemini/">Gemini</Ext> via Vertex
                    AI for second opinions,{' '}
                    <Ext href="https://github.com/features/copilot">GitHub Copilot</Ext> for pull
                    requests
                  </>,
                ],
                [
                  'editor, typography',
                  <>
                    <Ext href="https://www.jetbrains.com/pycharm/">JetBrains PyCharm</Ext>;{' '}
                    <Ext href="https://www.monolisa.dev/">MonoLisa</Ext> by Marcus Sterz;{' '}
                    <Ext href="https://github.com/JetBrains/JetBrainsMono">JetBrains Mono</Ext>{' '}
                    2.304 (<Ext href="https://openfontlicense.org">SIL Open Font License 1.1</Ext>)
                    for the attribution strip under plots created from your own data
                  </>,
                ],
              ]}
            />

            <Typography sx={subheadingStyle}>source code</Typography>
            <Typography sx={textStyle}>
              the entire codebase is publicly available under the MIT License:
              <br />
              <Link href={GITHUB_URL} target="_blank" rel="noopener" sx={proseLinkStyle}>
                github.com/MarkusNeusinger/anyplot
              </Link>
              <br />
              bundled third-party fonts keep their own licences — JetBrains Mono is under the SIL
              Open Font License 1.1.
            </Typography>

            <Typography sx={subheadingStyle}>monthly running costs (October 2026)</Typography>
            <FactTable
              labelWidth="75%"
              rows={[
                ['hosting: Cloud Run (site, api, data assistant, renderer)', '~$10'],
                ['database: Cloud SQL', '~$25'],
                ['data assistant model: Claude Haiku via Vertex AI', '~$15'],
                ['storage, logs and builds', '~$1'],
                ['domain (.ai)', '~$8'],
                ['total', <strong key="total">~$60/month</strong>],
              ]}
            />
            <Typography
              sx={{ ...textStyle, fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 1 }}
            >
              after three-year commitments and promotional credits; the assistant&apos;s model cost
              grows with use. development tools and subscriptions are not included. all costs are
              covered privately.
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
