import { useEffect } from 'react';

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
        this is a personal portfolio project showcasing data visualization examples, generated and
        maintained through ai-powered workflows. all code examples are meant for inspiration and
        learning — take them as a starting point, adapt them to your data and requirements, or use
        ai tools to customize them for your specific needs. code is provided &quot;as is&quot; under
        the MIT License and should be reviewed before production use.
      </Typography>
    </>
  );

  return (
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
            <Typography sx={subheadingStyle}>data controller</Typography>
            <Typography sx={textStyle}>
              Markus Neusinger (see legal notice above). the ground for the site itself is an
              operator&apos;s legitimate interest in protecting the site and knowing how often it is
              read; the data assistant below, which only its users meet, names its own grounds.
              swiss data protection law applies, and the GDPR on top for visitors from the EU.
            </Typography>

            <Typography sx={subheadingStyle}>what we collect</Typography>
            <Typography sx={textStyle}>
              <strong>anonymized analytics.</strong> the counting is done by{' '}
              <Link href="https://plausible.io" target="_blank" rel="noopener" sx={proseLinkStyle}>
                Plausible Analytics
              </Link>
              . the script is theirs, but it is served over a path on this domain: no cookies, no
              identifier that would recognize you on other sites, no IP address kept there, and your
              browser talks only to us. counted are page views, search queries and filter usage,
              code copies and image downloads, theme and navigation clicks, and Core Web Vitals
              (LCP, CLS, INP) to keep the site fast. when you share a link, we read the requesting
              bot&apos;s user-agent to detect the platform (e.g., LinkedIn, WhatsApp) — no data
              about the eventual viewer is collected at that step. all data is aggregated and
              anonymous.
            </Typography>
            <Typography sx={textStyle}>
              <strong>public dashboard.</strong> our analytics are{' '}
              <Link
                href="https://plausible.io/anyplot.ai"
                target="_blank"
                rel="noopener"
                sx={proseLinkStyle}
              >
                fully public
              </Link>{' '}
              — see exactly what we see.
            </Typography>
            <Typography sx={textStyle}>
              <strong>server logs.</strong> technical server logs including IP addresses, request
              URLs, and user agents are retained for 30 days via{' '}
              <Link
                href="https://cloud.google.com/logging"
                target="_blank"
                rel="noopener"
                sx={proseLinkStyle}
              >
                Google Cloud Logging
              </Link>{' '}
              for security and debugging purposes.
            </Typography>
            <Typography sx={textStyle}>
              <strong>feedback.</strong> the feedback widget keeps what you send it: the message,
              the reaction, anything you put in the optional contact field, the page you were on,
              your window size, your user-agent, a random id that ties your own submissions
              together, and a one-way hash of your IP address that limits spam. only the operator
              can read those entries, and nothing deletes them on a timer — ask and yours is gone.
            </Typography>
            <Typography sx={textStyle}>
              <strong>the edge.</strong> Cloudflare stands in front of the site and processes your
              IP address there to rate-limit, to filter bots — which can put a short check page in
              front of a request — and to absorb DDoS attacks.
            </Typography>

            <Typography sx={subheadingStyle}>
              only if you use the data assistant (preview)
            </Typography>
            <Typography sx={textStyle}>
              everything in this part applies only to people who use the data assistant. if you only
              browse the catalogue, none of it touches you. anyplot is building an assistant that
              adapts a catalogue plot to data you bring (&quot;use with my data&quot;). today it is
              a preview that only the operator and the site&apos;s admins can open; nobody else can
              reach it yet. this is what it does with what you give it.
            </Typography>
            <Typography sx={textStyle}>
              <strong>what the model sees.</strong> what you paste or drop and the messages you
              write go to Claude models by Anthropic, served through Google Cloud Vertex AI in the
              EU, to make the plot you asked for. they are processed under Google Cloud&apos;s data
              processing terms, and under Google Cloud&apos;s terms for Vertex AI your prompts are
              not used to train the models. don&apos;t paste personal data you are not allowed to
              share.
            </Typography>
            <Typography sx={textStyle}>
              <strong>sessions.</strong> a session — your data, the conversation and the plots made
              from it — is held in the server&apos;s memory only. it is cleared after an hour
              without activity or when the server instance stops; there is no session database. the
              separate render service also keeps its last 16 results (converted data, plot images)
              in memory, until newer renders push them out or its instance stops.
            </Typography>
            <Typography sx={textStyle}>
              <strong>usage telemetry.</strong> to see how the assistant is used and where it fails,
              it writes content-free lines: event types, data formats, size buckets, the plot type
              and library, attempts, review defect ids, statuses, latencies and token counts. a line
              never holds your text, your data, your column names or your file names. the lines of
              one session share a salted hash of the session, whose salt lives only as long as the
              server instance, and they carry no user id — pseudonymous, not anonymous. they are
              kept for up to 180 days in a Google Cloud Logging bucket in the Netherlands
              (europe-west4) and read through BigQuery.
            </Typography>
            <Typography sx={textStyle}>
              <strong>attribution and rate limits.</strong> the assistant&apos;s own log lines,
              which debug it and enforce the per-user limits, carry a keyed hash (HMAC) of your
              identity in place of it, and no content. they sit in the server logs above, for 30
              days.
            </Typography>
            <Typography sx={textStyle}>
              <strong>feedback cases.</strong> only when you send feedback on a result or on the
              chat does the assistant store a case: the conversation, the profile of your data
              (column types and the first 5 rows as a sample), the plot&apos;s code and images if
              one was made and, while the &quot;# include data.csv&quot; box is ticked — it is by
              default — the whole data file. unticking leaves out that file only: what the
              conversation, the sample, the code and the images show of your data stays in the case.
              the files go to a private bucket in the Netherlands (europe-west4) and are deleted
              after 180 days. a row with your reaction, your short message, a keyed hash of your
              identity and the technical details of the run (plot type, library, model) stays for
              the triage, and nothing deletes it on a timer — ask and yours is gone.
            </Typography>
            <Typography sx={textStyle}>
              <strong>legal basis.</strong> making the plot you asked for is the performance of your
              request (Art. 6(1)(b) GDPR); the telemetry and the rate limits rest on legitimate
              interest (Art. 6(1)(f) GDPR); a feedback case rests on your explicit submission.
            </Typography>

            <Typography sx={subheadingStyle}>what we do not collect</Typography>
            <Typography sx={textStyle}>
              • no user accounts or personal profiles
              <br />
              • no name or email unless you type one — the optional contact field in the feedback
              widget is the only place that asks
              <br />
              • no cookies at all (localStorage holds UI preferences — theme, image size — a cached
              release number, and, once you use the feedback widget, the random id above)
              <br />• <strong>no ai training</strong>: nothing you send is used to train ai models.
              when you browse the catalogue, the ai in this project has already done its part: it
              writes the catalogue at build time and never sees a visitor&apos;s request. only the
              data assistant above sends what you give it to a model, under the terms described
              there
            </Typography>

            <Typography sx={textStyle}>
              <strong>contributors.</strong> if you suggest a plot type via GitHub, your GitHub
              username may be credited in the specification metadata. this is public information
              from your GitHub profile.
            </Typography>

            <Typography sx={subheadingStyle}>hosting &amp; third parties</Typography>
            <Typography sx={textStyle}>
              the site, its database and its images run in the EU (Netherlands, europe-west4);
              Cloudflare&apos;s network is global, Plausible is a service of its own on its own EU
              servers, and the data assistant&apos;s models — used only when you use the assistant —
              are called in Vertex AI&apos;s EU region:
            </Typography>
            <Table sx={{ ...tableStyle, ...firstColStyle }}>
              <TableBody>
                <TableRow>
                  <TableCell>hosting</TableCell>
                  <TableCell>Google Cloud Run (Netherlands)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>database</TableCell>
                  <TableCell>Google Cloud SQL (Netherlands)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>storage</TableCell>
                  <TableCell>Google Cloud Storage (Netherlands)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>cdn / ddos</TableCell>
                  <TableCell>Cloudflare (global, EU data centers for EU visitors)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>analytics</TableCell>
                  <TableCell>Plausible Analytics (EU, proxied)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>ai assistant</TableCell>
                  <TableCell>
                    Google Cloud Vertex AI, Claude models by Anthropic (EU) — only when you use the
                    data assistant
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>

            <Typography sx={subheadingStyle}>your rights</Typography>
            <Typography sx={textStyle}>
              you can ask what is stored about you and have it corrected, erased or its use
              restricted, object to the processing on grounds relating to your particular situation,
              and complain to a supervisory authority. in practice that means a feedback entry, an
              assistant feedback case or a log line; a few lines to{' '}
              <Link href="mailto:admin@anyplot.ai" sx={proseLinkStyle}>
                admin@anyplot.ai
              </Link>{' '}
              are enough, also to have an assistant feedback case deleted early, its files and its
              row.
            </Typography>
          </Box>
        </Box>

        {/* Transparency */}
        <Box component="section" id="transparency" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>transparency</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={textStyle}>
              this project is open source and committed to full transparency about how it works and
              what it costs.
            </Typography>

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
          last updated: October 2026
        </Typography>
      </Box>
    </>
  );
}
