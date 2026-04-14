import { useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';

import { useAnalytics } from '../hooks';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { GITHUB_URL } from '../constants';
import {
  colors,
  semanticColors,
  fontSize,
  headingStyle,
  subheadingStyle,
  textStyle,
  tableStyle,
} from '../theme';

export function LegalPage() {
  const { trackPageview, trackEvent } = useAnalytics();

  useEffect(() => {
    trackPageview('/legal');
  }, [trackPageview]);

  const firstColStyle = {
    '& .MuiTableCell-root:first-of-type': {
      fontWeight: 500,
      color: colors.gray[700],
      width: '25%',
    },
  };

  return (
    <>
      <Helmet>
        <title>legal | anyplot.ai</title>
        <meta name="description" content="Legal notice, privacy policy, and transparency information for anyplot.ai" />
        <meta property="og:title" content="legal | anyplot.ai" />
        <meta property="og:description" content="Legal notice, privacy policy, and transparency information" />
        <link rel="canonical" href="https://anyplot.ai/legal" />
      </Helmet>

      <Breadcrumb items={[{ label: 'anyplot.ai', shortLabel: 'ap', to: '/' }, { label: 'legal' }]} sx={{ mb: 2 }} />

      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link href="#legal-notice" sx={{ color: colors.primary, fontFamily: textStyle.fontFamily, fontSize: fontSize.base }}>
          Legal Notice
        </Link>
        <Link href="#privacy" sx={{ color: colors.primary, fontFamily: textStyle.fontFamily, fontSize: fontSize.base }}>
          Privacy Policy
        </Link>
        <Link href="#transparency" sx={{ color: colors.primary, fontFamily: textStyle.fontFamily, fontSize: fontSize.base }}>
          Transparency
        </Link>
      </Box>

      <Box sx={{ pb: 4, maxWidth: 1100, mx: 'auto' }}>
        {/* Legal Notice */}
        <Paper component="section" id="legal-notice" sx={{ p: 3, mb: 2 }}>
          <Typography variant="h2" sx={headingStyle}>
            Legal Notice
          </Typography>

          <Typography sx={textStyle}>
            <strong>Operator</strong>
            <br />
            Markus Neusinger
            <br />
            Visp, Switzerland
          </Typography>

          <Typography sx={textStyle}>
            <strong>Contact</strong>
            <br />
            Email:{' '}
            <Link href="mailto:admin@anyplot.ai" sx={{ color: colors.primary }}>
              admin@anyplot.ai
            </Link>
            <br />
            LinkedIn:{' '}
            <Link
              href="https://www.linkedin.com/in/markus-neusinger/"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent('external_link', { destination: 'linkedin' })}
              sx={{ color: colors.primary }}
            >
              markus-neusinger
            </Link>
            <br />
            X:{' '}
            <Link
              href="https://x.com/MarkusNeusinger"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent('external_link', { destination: 'x' })}
              sx={{ color: colors.primary }}
            >
              @MarkusNeusinger
            </Link>
            <br />
            GitHub:{' '}
            <Link
              href="https://github.com/MarkusNeusinger"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackEvent('external_link', { destination: 'github_personal' })}
              sx={{ color: colors.primary }}
            >
              MarkusNeusinger
            </Link>
          </Typography>

          <Typography sx={textStyle}>
            <strong>Disclaimer</strong>
            <br />
            This is a personal portfolio project showcasing Python visualization examples, generated and maintained
            through AI-powered workflows. All code examples are meant for inspiration and learning – take them as a
            starting point, adapt them to your data and requirements, or use AI tools to customize them for your
            specific needs. Code is provided &quot;as is&quot; under the MIT License and should be reviewed before
            production use.
          </Typography>
        </Paper>

        {/* Privacy Policy */}
        <Paper component="section" id="privacy" sx={{ p: 3, mb: 2 }}>
          <Typography variant="h2" sx={headingStyle}>
            Privacy Policy
          </Typography>

          <Typography sx={subheadingStyle}>Data Controller</Typography>
          <Typography sx={textStyle}>Markus Neusinger (see Legal Notice above)</Typography>

          <Typography sx={subheadingStyle}>What We Collect</Typography>
          <Typography sx={textStyle}>
            <strong>Anonymized Analytics</strong>: We use{' '}
            <Link href="https://plausible.io" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
              Plausible Analytics
            </Link>
            , a privacy-focused analytics tool. It collects no personal data, uses no cookies, and does not track you
            across websites. We track: page views, navigation patterns, code copies, image downloads, search queries,
            filter usage, and UI interactions. When you share a link, we detect which platform requests the preview
            (e.g., LinkedIn, WhatsApp). All data is aggregated and anonymous.
          </Typography>
          <Typography sx={textStyle}>
            <strong>Public Dashboard</strong>: Our analytics are{' '}
            <Link href="https://plausible.io/anyplot.ai" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
              fully public
            </Link>{' '}
            – see exactly what we see.
          </Typography>
          <Typography sx={textStyle}>
            <strong>Server Logs</strong>: Technical server logs including IP addresses, request URLs, and user agents
            are retained for 30 days via{' '}
            <Link href="https://cloud.google.com/logging" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
              Google Cloud Logging
            </Link>{' '}
            for security and debugging purposes.
          </Typography>

          <Typography sx={subheadingStyle}>What We Do NOT Collect</Typography>
          <Typography sx={textStyle}>
            • No user accounts or personal profiles
            <br />
            • No personal data (names, emails, etc.)
            <br />
            • No cookies at all (we use localStorage for UI preferences only)
            <br />• <strong>No AI training</strong>: Your interactions are not used to train AI models
          </Typography>

          <Typography sx={textStyle}>
            <strong>Contributors</strong>: If you suggest a plot type via GitHub, your GitHub username may be credited
            in the specification metadata. This is public information from your GitHub profile.
          </Typography>

          <Typography sx={subheadingStyle}>Hosting &amp; Third Parties</Typography>
          <Typography sx={textStyle}>All services are hosted in the EU (Netherlands, europe-west4):</Typography>
          <Table sx={{ ...tableStyle, ...firstColStyle }}>
            <TableBody>
              <TableRow>
                <TableCell>Hosting</TableCell>
                <TableCell>Google Cloud Run (Netherlands)</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Database</TableCell>
                <TableCell>Google Cloud SQL (Netherlands)</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Storage</TableCell>
                <TableCell>Google Cloud Storage (Netherlands)</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Analytics</TableCell>
                <TableCell>Plausible Analytics (EU, proxied)</TableCell>
              </TableRow>
            </TableBody>
          </Table>

          <Typography sx={subheadingStyle}>Your Rights</Typography>
          <Typography sx={textStyle}>
            You have the right to access, rectify, erase, and export your data. Since we do not store personal data,
            there is typically nothing to delete or export. For questions, contact{' '}
            <Link href="mailto:admin@anyplot.ai" sx={{ color: colors.primary }}>
              admin@anyplot.ai
            </Link>
            .
          </Typography>
        </Paper>

        {/* Transparency */}
        <Paper component="section" id="transparency" sx={{ p: 3, mb: 2 }}>
          <Typography variant="h2" sx={headingStyle}>
            Transparency
          </Typography>

          <Typography sx={textStyle}>
            This project is open source and committed to full transparency about how it works and what it costs.
          </Typography>

          <Typography sx={subheadingStyle}>Technology Stack</Typography>
          <Table sx={{ ...tableStyle, ...firstColStyle }}>
            <TableBody>
              <TableRow>
                <TableCell>Editor</TableCell>
                <TableCell>
                  <Link href="https://www.jetbrains.com/pycharm/" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    JetBrains PyCharm
                  </Link>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Frontend</TableCell>
                <TableCell>
                  <Link href="https://react.dev" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    React
                  </Link>{' '}
                  19,{' '}
                  <Link href="https://vite.dev" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    Vite
                  </Link>
                  ,{' '}
                  <Link href="https://mui.com" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    MUI
                  </Link>{' '}
                  7,{' '}
                  <Link href="https://typescriptlang.org" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    TypeScript
                  </Link>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Backend</TableCell>
                <TableCell>
                  <Link href="https://python.org" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    Python
                  </Link>{' '}
                  3.13,{' '}
                  <Link href="https://fastapi.tiangolo.com" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    FastAPI
                  </Link>
                  ,{' '}
                  <Link href="https://sqlalchemy.org" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    SQLAlchemy
                  </Link>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Database</TableCell>
                <TableCell>
                  <Link href="https://postgresql.org" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    PostgreSQL
                  </Link>{' '}
                  18
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Hosting</TableCell>
                <TableCell>
                  <Link href="https://cloud.google.com/run" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    Google Cloud Run
                  </Link>{' '}
                  (Netherlands)
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Storage</TableCell>
                <TableCell>
                  <Link href="https://cloud.google.com/storage" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    Google Cloud Storage
                  </Link>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Analytics</TableCell>
                <TableCell>
                  <Link href="https://plausible.io" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    Plausible
                  </Link>{' '}
                  (privacy-friendly, no cookies,{' '}
                  <Link href="https://plausible.io/anyplot.ai" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    public dashboard
                  </Link>
                  )
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Code Generation</TableCell>
                <TableCell>
                  <Link href="https://anthropic.com" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    Anthropic Claude
                  </Link>{' '}
                  (code generation &amp; review),{' '}
                  <Link href="https://github.com/features/copilot" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    GitHub Copilot
                  </Link>{' '}
                  (PR reviews)
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Typography</TableCell>
                <TableCell>
                  <Link href="https://www.monolisa.dev/" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    MonoLisa
                  </Link>{' '}
                  by Marcus Sterz
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>

          <Typography sx={subheadingStyle}>Source Code</Typography>
          <Typography sx={textStyle}>
            The entire codebase is publicly available under the MIT License:
            <br />
            <Link href={GITHUB_URL} target="_blank" rel="noopener" sx={{ color: colors.primary }}>
              github.com/MarkusNeusinger/anyplot
            </Link>
          </Typography>

          <Typography sx={subheadingStyle}>Monthly Hosting Costs (approximate)</Typography>
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
                  <strong>Total</strong>
                </TableCell>
                <TableCell>
                  <strong>~$34/month</strong>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
          <Typography sx={{ ...textStyle, fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 1 }}>
            Direct hosting costs only. Subscriptions (GitHub Pro, Plausible, Claude MAX, PyCharm, etc.) are shared
            across projects. All costs are currently covered privately.
          </Typography>
        </Paper>

        <Typography sx={{ textAlign: 'center', fontSize: fontSize.sm, color: semanticColors.mutedText, mt: 2 }}>
          Last updated: March 2026
        </Typography>
      </Box>

      <Footer onTrackEvent={trackEvent} />
    </>
  );
}
