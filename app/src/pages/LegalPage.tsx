import { type ReactNode, useEffect } from 'react';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { GITHUB_URL } from 'src/constants';
import { useAnalytics } from 'src/hooks';
import {
  fontSize,
  proseLinkStyle,
  semanticColors,
  subheadingStyle,
  tableStyle,
  textStyle,
} from 'src/theme';

const firstColStyle = {
  '& .MuiTableCell-root:first-of-type': {
    fontWeight: 500,
    color: 'var(--ink-soft)',
    width: '25%',
  },
};

const AVATAR_URL = 'https://storage.googleapis.com/anyplot-static/images/markusneusinger.webp';

/** A two-column fact table: a short label, then the fact. */
function FactTable({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <Table
      sx={{ ...tableStyle, ...firstColStyle, '& .MuiTableCell-body': { verticalAlign: 'top' } }}
    >
      <TableBody>
        {rows.map(([label, fact]) => (
          <TableRow key={label}>
            <TableCell>{label}</TableCell>
            <TableCell>{fact}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function LegalPage() {
  const { trackPageview, trackEvent } = useAnalytics();

  useEffect(() => {
    trackPageview('/legal');
  }, [trackPageview]);

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
          onClick={() => trackEvent('external_link', { destination: 'linkedin' })}
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
          onClick={() => trackEvent('external_link', { destination: 'x' })}
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
          onClick={() => trackEvent('external_link', { destination: 'github_personal' })}
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
        <Link
          href="https://kurrentschrift.ink"
          target="_blank"
          rel="noopener"
          onClick={() => trackEvent('external_link', { destination: 'kurrentschrift' })}
          sx={proseLinkStyle}
        >
          kurrentschrift.ink
        </Link>{' '}
        — read and write old german cursive
        <br />
        <Link
          href="https://github.com/MarkusNeusinger/cite-citadel"
          target="_blank"
          rel="noopener"
          onClick={() => trackEvent('external_link', { destination: 'cite_citadel' })}
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
        <Box component="section" id="legal-notice" sx={{ py: { xs: 2, md: 3 } }}>
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
        <Box component="section" id="privacy" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>privacy policy</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={subheadingStyle}>controller</Typography>
            <Typography sx={textStyle}>
              Markus Neusinger (see above). swiss data protection law applies, and the GDPR for
              visitors from the EU.
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
                    counts page views, searches, clicks, copies, downloads and Core Web Vitals, only
                    in aggregate, on a{' '}
                    <Link
                      href="https://plausible.io/anyplot.ai"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      public dashboard
                    </Link>
                    . its script is served through this domain: no cookies, no cross-site id, no IP
                    address kept.
                  </>,
                ],
                [
                  'server logs',
                  'IP address, URL and user-agent of each request, for security and debugging.',
                ],
                [
                  'edge',
                  'Cloudflare uses your IP address to rate-limit, filter bots and absorb DDoS attacks.',
                ],
                [
                  'feedback',
                  'message, reaction, optional contact, page, your window size, user-agent and a random id that ties your own submissions together, read only by the operator. a salted hash of your IP address limits spam.',
                ],
                [
                  'github',
                  'suggest a plot type there and your public username may be credited in its spec.',
                ],
              ]}
            />

            <Typography sx={subheadingStyle}>where it runs</Typography>
            <FactTable
              rows={[
                [
                  'hosting',
                  'Google Cloud (Run, SQL, Storage, Logging) in the Netherlands (europe-west4)',
                ],
                ['cdn / ddos', 'Cloudflare (global, EU data centers for EU visitors)'],
                ['analytics', 'Plausible Analytics (EU, proxied)'],
                [
                  'data assistant',
                  'Claude by Anthropic via Google Cloud Vertex AI (EU), if you use it',
                ],
              ]}
            />
            <Typography sx={textStyle}>
              Google Cloud and Cloudflare process data under their data processing terms, including
              their safeguards for transfers outside Switzerland and the EU.
            </Typography>

            <Typography sx={subheadingStyle}>how long it stays</Typography>
            <FactTable
              rows={[
                ['server logs', '30 days'],
                ['feedback IP hash', 'ten minutes'],
                ['assistant telemetry', 'up to 180 days'],
                ['feedback case files', '180 days'],
                ['feedback entries, case rows', 'until you ask to delete them'],
              ]}
            />

            <Typography sx={subheadingStyle}>legal bases (GDPR)</Typography>
            <FactTable
              rows={[
                [
                  'Art. 6(1)(f)',
                  "legitimate interest in protecting the site, counting its readers, and the assistant's telemetry and limits",
                ],
                ['Art. 6(1)(b)', 'your request: making the plot you ask the data assistant for'],
                [
                  'Art. 6(1)(a)',
                  'your consent to a feedback case, given when you send it and withdrawable at any time by asking',
                ],
              ]}
            />

            <Typography sx={subheadingStyle}>what we do not do</Typography>
            <Typography sx={textStyle}>
              • no cookies for visitors; the browser&apos;s storage keeps UI settings, your plot
              votes, a release number and the random ids named here. admins sign in through
              Cloudflare Access, which sets its own login cookie
              <br />
              • no accounts, and no name or email unless you type one
              <br />• <strong>no ai training</strong> on what you send. the catalogue is written at
              build time, so browsing never reaches a model
            </Typography>

            <Typography id="assistant" sx={subheadingStyle}>
              only if you use the data assistant (experimental)
            </Typography>
            <Typography sx={textStyle}>
              if you only browse the catalogue, none of it touches you.
            </Typography>
            <FactTable
              rows={[
                [
                  'what it is',
                  'it adapts a catalogue plot to your data. open to everyone, experimental and without warranty: results can be wrong and nobody checks them by hand. the operator may pause it at any time.',
                ],
                [
                  'the model',
                  "what you paste and write goes to Claude by Anthropic, served through Google Cloud Vertex AI in the EU under Google Cloud's data processing terms; your prompts are not used for training. don't paste personal data you are not allowed to share.",
                ],
                [
                  'memory',
                  'a session (data, chat, plots) lives in server memory only, with no database, and is cleared after an hour idle. the render service keeps its last 16 results in memory.',
                ],
                [
                  'logs',
                  'no content: never your text, data, column or file names. telemetry holds event types, formats, sizes, plot type, library, language code (rare ones as "other"), attempts, defect ids, statuses, latencies and token counts.',
                ],
                [
                  'ids',
                  'a random tab id stands in for you, and the per-network limits count your IP address; both are salted with a value that lives only as long as the server instance, in memory, never written down. nothing durable: only timestamps could match them to the 30-day server logs, so they are pseudonymous. admins: a keyed hash (HMAC).',
                ],
                [
                  'feedback',
                  <>
                    kept only when you send feedback: the conversation, a profile of your data with
                    its first 5 rows, the plot&apos;s code and images, and the whole data file only
                    if you tick{' '}
                    <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
                      &quot;# include data.csv&quot;
                    </Box>
                    . it starts unticked, which leaves out that file only. files go to a private
                    bucket in the Netherlands; a triage row keeps your reaction, message, a hash of
                    your tab id and the run&apos;s details.
                  </>,
                ],
                [
                  'limits',
                  'use it only with data you may share, never for unlawful content or automated requests. daily limits apply per tab and per network; a misuse can pause you for the day.',
                ],
                [
                  'your code',
                  "yours to use, as is, like the catalogue's code under the MIT License. Highcharts is free for non-commercial use, and a commercial use needs a licence from Highsoft.",
                ],
              ]}
            />

            <Typography sx={subheadingStyle}>your rights</Typography>
            <Typography sx={textStyle}>
              you can ask what is stored about you and have it corrected, erased or restricted,
              object to the processing on grounds relating to your particular situation, and
              complain to a supervisory authority. a few lines to{' '}
              <Link href="mailto:admin@anyplot.ai" sx={proseLinkStyle}>
                admin@anyplot.ai
              </Link>{' '}
              are enough, also to have a feedback case deleted early.
            </Typography>
          </Box>
        </Box>

        {/* Transparency */}
        <Box component="section" id="transparency" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>transparency</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={textStyle}>open source, down to what it costs to run.</Typography>

            <Typography sx={subheadingStyle}>technology stack</Typography>
            <Table sx={{ ...tableStyle, ...firstColStyle }}>
              <TableBody>
                <TableRow>
                  <TableCell>editor</TableCell>
                  <TableCell>
                    <Link
                      href="https://www.jetbrains.com/pycharm/"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      JetBrains PyCharm
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>frontend</TableCell>
                  <TableCell>
                    <Link
                      href="https://react.dev"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      React
                    </Link>{' '}
                    19,{' '}
                    <Link
                      href="https://vite.dev"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      Vite
                    </Link>
                    ,{' '}
                    <Link href="https://mui.com" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      MUI
                    </Link>{' '}
                    9,{' '}
                    <Link
                      href="https://typescriptlang.org"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      TypeScript
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>backend</TableCell>
                  <TableCell>
                    <Link
                      href="https://python.org"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      Python
                    </Link>{' '}
                    3.14,{' '}
                    <Link
                      href="https://fastapi.tiangolo.com"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      FastAPI
                    </Link>
                    ,{' '}
                    <Link
                      href="https://sqlalchemy.org"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      SQLAlchemy
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>database</TableCell>
                  <TableCell>
                    <Link
                      href="https://postgresql.org"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      PostgreSQL
                    </Link>{' '}
                    18
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>hosting</TableCell>
                  <TableCell>
                    <Link
                      href="https://cloud.google.com/run"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      Google Cloud Run
                    </Link>{' '}
                    (Netherlands)
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>cdn / ddos</TableCell>
                  <TableCell>
                    <Link
                      href="https://cloudflare.com"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      Cloudflare
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>storage</TableCell>
                  <TableCell>
                    <Link
                      href="https://cloud.google.com/storage"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      Google Cloud Storage
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>analytics</TableCell>
                  <TableCell>
                    <Link
                      href="https://plausible.io"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      Plausible
                    </Link>{' '}
                    (privacy-friendly, no cookies,{' '}
                    <Link
                      href="https://plausible.io/anyplot.ai"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      public dashboard
                    </Link>
                    )
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>code generation</TableCell>
                  <TableCell>
                    <Link
                      href="https://anthropic.com"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      Anthropic Claude
                    </Link>{' '}
                    (code generation &amp; review),{' '}
                    <Link
                      href="https://github.com/features/copilot"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      GitHub Copilot
                    </Link>{' '}
                    (PR reviews)
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>typography</TableCell>
                  <TableCell>
                    <Link
                      href="https://www.monolisa.dev/"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      MonoLisa
                    </Link>{' '}
                    by Marcus Sterz
                    <br />
                    <Link
                      href="https://github.com/JetBrains/JetBrainsMono"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      JetBrains Mono
                    </Link>{' '}
                    2.304 (
                    <Link
                      href="https://openfontlicense.org"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      SIL Open Font License 1.1
                    </Link>
                    ) — for the attribution strip under plots created from your own data
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>

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

            <Typography sx={subheadingStyle}>monthly hosting costs (approximate)</Typography>
            <Table sx={{ ...tableStyle, ...firstColStyle }}>
              <TableBody>
                <TableRow>
                  <TableCell>Cloud Run</TableCell>
                  <TableCell>~$15</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Cloud SQL</TableCell>
                  <TableCell>~$10</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Cloud Storage</TableCell>
                  <TableCell>~$1</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Domain (.ai)</TableCell>
                  <TableCell>~$8</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <strong>total</strong>
                  </TableCell>
                  <TableCell>
                    <strong>~$34/month</strong>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
            <Typography
              sx={{ ...textStyle, fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 1 }}
            >
              direct hosting costs only. subscriptions (GitHub Pro, Plausible, Claude MAX, PyCharm,
              etc.) are shared across projects. all costs are currently covered privately.
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
