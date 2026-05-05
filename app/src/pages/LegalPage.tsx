import { useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';

import { SectionHeader } from '../components/SectionHeader';
import { useAnalytics } from '../hooks';
import { GITHUB_URL } from '../constants';
import {
  semanticColors,
  fontSize,
  subheadingStyle,
  textStyle,
  tableStyle,
  proseLinkStyle,
} from '../theme';

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
      <Helmet>
        <title>legal | anyplot.ai</title>
        <meta name="description" content="legal notice, privacy policy, and transparency information for anyplot.ai" />
        <meta property="og:title" content="legal | anyplot.ai" />
        <meta property="og:description" content="legal notice, privacy policy, and transparency information" />
        <link rel="canonical" href="https://anyplot.ai/legal" />
      </Helmet>

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
          </Box>
        </Box>

        {/* Privacy Policy */}
        <Box component="section" id="privacy" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>privacy policy</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={subheadingStyle}>data controller</Typography>
            <Typography sx={textStyle}>Markus Neusinger (see legal notice above)</Typography>

            <Typography sx={subheadingStyle}>what we collect</Typography>
            <Typography sx={textStyle}>
              <strong>anonymized analytics.</strong> we use{' '}
              <Link href="https://plausible.io" target="_blank" rel="noopener" sx={proseLinkStyle}>
                Plausible Analytics
              </Link>
              , a privacy-focused analytics tool. it collects no personal data, uses no cookies, and does
              not track you across websites. we track: page views, navigation patterns, code copies, image
              downloads, search queries, filter usage, UI interactions (tab toggles, theme preference,
              banner dismissals), and anonymized performance metrics (Core Web Vitals: LCP, CLS, INP) to
              keep the site fast. when you share a link, we read the requesting bot&apos;s user-agent to
              detect the platform (e.g., LinkedIn, WhatsApp) — no data about the eventual viewer is
              collected at that step. all data is aggregated and anonymous.
            </Typography>
            <Typography sx={textStyle}>
              <strong>public dashboard.</strong> our analytics are{' '}
              <Link href="https://plausible.io/anyplot.ai" target="_blank" rel="noopener" sx={proseLinkStyle}>
                fully public
              </Link>{' '}
              — see exactly what we see.
            </Typography>
            <Typography sx={textStyle}>
              <strong>server logs.</strong> technical server logs including IP addresses, request URLs, and
              user agents are retained for 30 days via{' '}
              <Link href="https://cloud.google.com/logging" target="_blank" rel="noopener" sx={proseLinkStyle}>
                Google Cloud Logging
              </Link>{' '}
              for security and debugging purposes.
            </Typography>

            <Typography sx={subheadingStyle}>what we do not collect</Typography>
            <Typography sx={textStyle}>
              • no user accounts or personal profiles
              <br />
              • no personal data (names, emails, etc.)
              <br />
              • no cookies at all (we use localStorage for UI preferences only)
              <br />• <strong>no ai training</strong>: your interactions are not used to train ai models
            </Typography>

            <Typography sx={textStyle}>
              <strong>contributors.</strong> if you suggest a plot type via GitHub, your GitHub username
              may be credited in the specification metadata. this is public information from your GitHub
              profile.
            </Typography>

            <Typography sx={subheadingStyle}>hosting &amp; third parties</Typography>
            <Typography sx={textStyle}>all services are hosted in the EU (Netherlands, europe-west4):</Typography>
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
              </TableBody>
            </Table>

            <Typography sx={subheadingStyle}>your rights</Typography>
            <Typography sx={textStyle}>
              you have the right to access, rectify, erase, and export your data. since we do not store
              personal data, there is typically nothing to delete or export. for questions, contact{' '}
              <Link href="mailto:admin@anyplot.ai" sx={proseLinkStyle}>
                admin@anyplot.ai
              </Link>
              .
            </Typography>
          </Box>
        </Box>

        {/* Transparency */}
        <Box component="section" id="transparency" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>transparency</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={textStyle}>
              this project is open source and committed to full transparency about how it works and what
              it costs.
            </Typography>

            <Typography sx={subheadingStyle}>technology stack</Typography>
            <Table sx={{ ...tableStyle, ...firstColStyle }}>
              <TableBody>
                <TableRow>
                  <TableCell>editor</TableCell>
                  <TableCell>
                    <Link href="https://www.jetbrains.com/pycharm/" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      JetBrains PyCharm
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>frontend</TableCell>
                  <TableCell>
                    <Link href="https://react.dev" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      React
                    </Link>{' '}
                    19,{' '}
                    <Link href="https://vite.dev" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      Vite
                    </Link>
                    ,{' '}
                    <Link href="https://mui.com" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      MUI
                    </Link>{' '}
                    9,{' '}
                    <Link href="https://typescriptlang.org" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      TypeScript
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>backend</TableCell>
                  <TableCell>
                    <Link href="https://python.org" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      Python
                    </Link>{' '}
                    3.14,{' '}
                    <Link href="https://fastapi.tiangolo.com" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      FastAPI
                    </Link>
                    ,{' '}
                    <Link href="https://sqlalchemy.org" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      SQLAlchemy
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>database</TableCell>
                  <TableCell>
                    <Link href="https://postgresql.org" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      PostgreSQL
                    </Link>{' '}
                    18
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>hosting</TableCell>
                  <TableCell>
                    <Link href="https://cloud.google.com/run" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      Google Cloud Run
                    </Link>{' '}
                    (Netherlands)
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>cdn / ddos</TableCell>
                  <TableCell>
                    <Link href="https://cloudflare.com" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      Cloudflare
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>storage</TableCell>
                  <TableCell>
                    <Link href="https://cloud.google.com/storage" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      Google Cloud Storage
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>analytics</TableCell>
                  <TableCell>
                    <Link href="https://plausible.io" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      Plausible
                    </Link>{' '}
                    (privacy-friendly, no cookies,{' '}
                    <Link href="https://plausible.io/anyplot.ai" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      public dashboard
                    </Link>
                    )
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>code generation</TableCell>
                  <TableCell>
                    <Link href="https://anthropic.com" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      Anthropic Claude
                    </Link>{' '}
                    (code generation &amp; review),{' '}
                    <Link href="https://github.com/features/copilot" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      GitHub Copilot
                    </Link>{' '}
                    (PR reviews)
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>typography</TableCell>
                  <TableCell>
                    <Link href="https://www.monolisa.dev/" target="_blank" rel="noopener" sx={proseLinkStyle}>
                      MonoLisa
                    </Link>{' '}
                    by Marcus Sterz
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
            <Typography sx={{ ...textStyle, fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 1 }}>
              direct hosting costs only. subscriptions (GitHub Pro, Plausible, Claude MAX, PyCharm, etc.)
              are shared across projects. all costs are currently covered privately.
            </Typography>
          </Box>
        </Box>

        <Typography sx={{ textAlign: 'center', fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 2 }}>
          last updated: April 2026
        </Typography>
      </Box>
    </>
  );
}
