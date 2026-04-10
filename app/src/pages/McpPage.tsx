import { useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';

import { useAnalytics } from '../hooks';
import { Breadcrumb } from '../components/Breadcrumb';
import { Footer } from '../components/Footer';
import { GITHUB_URL } from '../constants';
import {
  colors,
  fontSize,
  headingStyle,
  subheadingStyle,
  textStyle,
  codeBlockStyle,
  tableStyle,
} from '../theme';

export function McpPage() {
  const { trackPageview, trackEvent } = useAnalytics();

  useEffect(() => {
    trackPageview('/mcp');
  }, [trackPageview]);

  return (
    <>
      <Helmet>
        <title>mcp | pyplots.ai</title>
        <meta
          name="description"
          content="Configure your AI assistant (Claude Desktop, Claude Code) to access pyplots data via the Model Context Protocol (MCP) server."
        />
        <meta property="og:title" content="mcp | pyplots.ai" />
        <meta
          property="og:description"
          content="Configure your AI assistant to access pyplots data via MCP"
        />
        <link rel="canonical" href="https://pyplots.ai/mcp" />
      </Helmet>

      <Breadcrumb items={[{ label: 'pyplots.ai', shortLabel: 'pp', to: '/' }, { label: 'mcp' }]} sx={{ mb: 2 }} />

      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link href="#what-is-mcp" sx={{ color: colors.primary, fontFamily: textStyle.fontFamily, fontSize: fontSize.base }}>
          What is MCP
        </Link>
        <Link href="#configuration" sx={{ color: colors.primary, fontFamily: textStyle.fontFamily, fontSize: fontSize.base }}>
          Configuration
        </Link>
        <Link href="#tools" sx={{ color: colors.primary, fontFamily: textStyle.fontFamily, fontSize: fontSize.base }}>
          Available Tools
        </Link>
        <Link href="#use-cases" sx={{ color: colors.primary, fontFamily: textStyle.fontFamily, fontSize: fontSize.base }}>
          Use Cases
        </Link>
        <Link href="#resources" sx={{ color: colors.primary, fontFamily: textStyle.fontFamily, fontSize: fontSize.base }}>
          Resources
        </Link>
      </Box>

      <Box sx={{ pb: 4, maxWidth: 1100, mx: 'auto' }}>
        {/* What is MCP */}
        <Paper component="section" id="what-is-mcp" sx={{ p: 3, mb: 2 }}>
          <Typography variant="h2" sx={headingStyle}>
            What is MCP?
          </Typography>

          <Typography sx={textStyle}>
            The{' '}
            <Link href="https://modelcontextprotocol.io" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
              Model Context Protocol (MCP)
            </Link>{' '}
            is an open standard by Anthropic that enables AI assistants to securely connect to external data sources and tools.
          </Typography>

          <Typography sx={textStyle}>
            pyplots provides an MCP server so you can use your AI assistant to:
          </Typography>

          <Box component="ul" sx={{ m: 0, pl: 3, mb: 2 }}>
            {['Search and discover plot types by tags, features, or keywords',
              'Fetch ready-to-use Python code for any supported library',
              'Get AI-powered help adapting code to your specific data'].map((item, i) => (
              <Typography
                key={i}
                component="li"
                sx={textStyle}
              >
                {item}
              </Typography>
            ))}
          </Box>

          <Typography sx={textStyle}>
            <strong>Endpoint</strong>:{' '}
            <code style={{ backgroundColor: colors.gray[100], padding: '4px 8px', borderRadius: '4px', color: colors.primary }}>
              https://api.pyplots.ai/mcp/
            </code>
          </Typography>
        </Paper>

        {/* Configuration */}
        <Paper component="section" id="configuration" sx={{ p: 3, mb: 2 }}>
          <Typography variant="h2" sx={headingStyle}>
            Configuration
          </Typography>

          <Typography sx={textStyle}>
            Use these parameters to configure pyplots in your MCP client:
          </Typography>

          <Table sx={{ ...tableStyle, mb: 3 }}>
            <TableBody>
              <TableRow>
                <TableCell sx={{ width: 140 }}>Server Name</TableCell>
                <TableCell><code>pyplots</code></TableCell>
              </TableRow>
              <TableRow>
                <TableCell>URL</TableCell>
                <TableCell><code>https://api.pyplots.ai/mcp/</code></TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Transport</TableCell>
                <TableCell><code>http</code> (Streamable HTTP)</TableCell>
              </TableRow>
            </TableBody>
          </Table>

          <Typography sx={subheadingStyle}>Claude Code</Typography>
          <Box sx={codeBlockStyle}>
            {`claude mcp add pyplots --transport http https://api.pyplots.ai/mcp/`}
          </Box>

          <Typography sx={{ ...textStyle, mt: 3 }}>
            Verify by asking &quot;list available plot types from pyplots&quot;.
          </Typography>
        </Paper>

        {/* Available Tools */}
        <Paper component="section" id="tools" sx={{ p: 3, mb: 2 }}>
          <Typography variant="h2" sx={headingStyle}>
            Available Tools
          </Typography>

          <Typography sx={textStyle}>
            The MCP server provides these tools for AI assistants to interact with pyplots:
          </Typography>

          <Table sx={tableStyle}>
            <TableHead>
              <TableRow>
                <TableCell>Tool</TableCell>
                <TableCell>Description</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>
                  <code>list_specs</code>
                </TableCell>
                <TableCell>List all plot specifications with summary information (title, tags, library count)</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>
                  <code>search_specs_by_tags</code>
                </TableCell>
                <TableCell>
                  Search specifications using tag filters (plot_type, data_type, domain, features, library)
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>
                  <code>get_spec_detail</code>
                </TableCell>
                <TableCell>Get complete specification including all implementations and metadata</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>
                  <code>get_implementation</code>
                </TableCell>
                <TableCell>Get implementation code for a specific specification and library</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>
                  <code>list_libraries</code>
                </TableCell>
                <TableCell>List all supported plotting libraries (matplotlib, seaborn, plotly, etc.)</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>
                  <code>get_tag_values</code>
                </TableCell>
                <TableCell>Get all available values for a specific tag category with counts</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Paper>

        {/* Use Cases */}
        <Paper component="section" id="use-cases" sx={{ p: 3, mb: 2 }}>
          <Typography variant="h2" sx={headingStyle}>
            Use Cases
          </Typography>

          <Typography sx={subheadingStyle}>AI-Assisted Plot Discovery</Typography>
          <Typography sx={textStyle}>
            Ask Claude to find the right plot type for your data. For example: &quot;I have two numeric variables and
            want to show their correlation. What plot types does pyplots have?&quot; Claude will search the
            specifications and suggest appropriate visualizations.
          </Typography>

          <Typography sx={subheadingStyle}>Code Generation with AI</Typography>
          <Typography sx={textStyle}>
            Claude can fetch implementation code and adapt it to your specific data. Ask: &quot;Get me the matplotlib
            code for a scatter plot and modify it to use my sales data.&quot; Claude will retrieve the code and
            customize it for your needs.
          </Typography>

          <Typography sx={subheadingStyle}>Comparing Library Implementations</Typography>
          <Typography sx={textStyle}>
            Compare how different libraries implement the same visualization. Ask: &quot;Show me how to create a heatmap
            in both seaborn and plotly.&quot; Claude will fetch both implementations so you can compare their approaches
            and choose the best fit for your project.
          </Typography>
        </Paper>

        {/* Resources */}
        <Paper component="section" id="resources" sx={{ p: 3, mb: 2 }}>
          <Typography variant="h2" sx={headingStyle}>
            Resources
          </Typography>

          <Table sx={tableStyle}>
            <TableBody>
              <TableRow>
                <TableCell>Full MCP Documentation</TableCell>
                <TableCell>
                  <Link
                    href={`${GITHUB_URL}/blob/main/docs/reference/mcp.md`}
                    target="_blank"
                    rel="noopener"
                    sx={{ color: colors.primary }}
                  >
                    docs/reference/mcp.md
                  </Link>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>MCP Official Website</TableCell>
                <TableCell>
                  <Link href="https://modelcontextprotocol.io" target="_blank" rel="noopener" sx={{ color: colors.primary }}>
                    modelcontextprotocol.io
                  </Link>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>MCP Inspector</TableCell>
                <TableCell>
                  <code>npx @modelcontextprotocol/inspector https://api.pyplots.ai/mcp/</code>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Paper>
      </Box>

      <Footer onTrackEvent={trackEvent} />
    </>
  );
}
