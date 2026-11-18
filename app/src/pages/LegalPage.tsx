import { Navigate, useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { FactTable } from 'src/components/FactTable';
import { SectionHeader } from 'src/components/SectionHeader';
import { ANCHOR_SX, useHashScroll } from 'src/hooks/useHashScroll';
import { paths } from 'src/routes/paths';
import { MOVED_TO_ABOUT } from 'src/routes/redirects';
import { fontSize, proseLinkStyle, semanticColors, subheadingStyle, textStyle } from 'src/theme';

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
                    . its script is served through this domain: no cookies, no cross-site id, no IP
                    address kept.
                  </>,
                ],
                [
                  'server logs',
                  'IP address, URL and user-agent of each request, for security and debugging.',
                ],
                [
                  'machine readers',
                  <Box component="span" id="machine-readers" sx={ANCHOR_SX}>
                    each request by a crawler, an ai assistant or an mcp client is one content-free
                    line: the vendor and purpose, whether Cloudflare verified it, the page or file
                    it asked for and the status. no IP address, no user-agent, nothing about
                    anyone&apos;s browsing.
                  </Box>,
                ],
                [
                  'shared links',
                  <Box component="span" id="shared-links" sx={ANCHOR_SX}>
                    when a messenger or a social network fetches a page&apos;s preview image, one
                    counter goes up: the day, the platform and the page, and whether Cloudflare
                    verified the fetcher as a bot it knows. no IP address, no user-agent, no time of
                    day, nothing about who shared. unverified is no verdict on a share: WhatsApp and
                    Signal fetch the preview from the sender&apos;s own phone, which nobody can
                    verify. the counts are kept without a time limit.
                  </Box>,
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
                  'bot check',
                  "when you send feedback, rate a plot or open the data assistant, Cloudflare Turnstile checks that a browser, not a script, is asking: it reads your IP address, user-agent and TLS fingerprint and keeps an item of its own in your browser's storage, with no cookie. anyplot learns only whether the check passed. Cloudflare also uses these signals, as its own controller, to improve the check.",
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
                  'Google Cloud (Run, SQL, Storage, Logging, BigQuery) in the Netherlands (europe-west4)',
                ],
                ['cdn / ddos / bot check', 'Cloudflare (global, EU data centers for EU visitors)'],
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
                [
                  'feedback IP hash',
                  'cleared by the next feedback after ten minutes; its salt dies with the server instance',
                ],
                ['assistant telemetry', 'up to 180 days'],
                ['machine readers', 'up to 180 days'],
                [
                  'shared links',
                  'no time limit: counts per day, platform and page, verified or not',
                ],
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
              votes, a release number, the random ids named here and Cloudflare Turnstile&apos;s own
              item. admins sign in through Cloudflare Access, which sets its own login cookie
              <br />
              • no accounts, and no name or email unless you type one
              <br />• <strong>no ai training</strong> on what you send. the catalogue is written at
              build time, so browsing never reaches a model
            </Typography>

            <Typography id="assistant" sx={{ ...subheadingStyle, ...ANCHOR_SX }}>
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
