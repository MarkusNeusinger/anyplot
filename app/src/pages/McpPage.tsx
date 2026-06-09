import { useEffect } from 'react';

import { Helmet } from 'react-helmet-async';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';

import { SectionHeader } from '../components/SectionHeader';
import { GITHUB_URL } from '../constants';
import { useAnalytics } from '../hooks';
import {
  codeBlockStyle,
  proseLinkStyle,
  subheadingStyle,
  tableStyle,
  textStyle,
  typography,
} from '../theme';

const inlineCodeSx = {
  fontFamily: typography.mono,
  fontSize: '0.9em',
  backgroundColor: 'var(--bg-elevated)',
  padding: '2px 6px',
  borderRadius: '3px',
  color: 'var(--ink)',
  // Long URLs / commands sit in TableCells; without explicit wrapping they
  // force the table wider than a mobile viewport.
  overflowWrap: 'anywhere' as const,
};

export function McpPage() {
  const { trackPageview } = useAnalytics();

  useEffect(() => {
    trackPageview('/mcp');
  }, [trackPageview]);

  return (
    <>
      <Helmet>
        <title>mcp | anyplot.ai</title>
        <meta
          name="description"
          content="configure Claude Code to access anyplot data via the Model Context Protocol (MCP) server."
        />
        <meta property="og:title" content="mcp | anyplot.ai" />
        <meta
          property="og:description"
          content="configure Claude Code to access anyplot data via MCP"
        />
        <link rel="canonical" href="https://anyplot.ai/mcp" />
      </Helmet>

      <Box sx={{ pb: 4 }}>
        {/* What is MCP */}
        <Box component="section" id="what-is-mcp" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>what is mcp</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={textStyle}>
              the{' '}
              <Link
                href="https://modelcontextprotocol.io"
                target="_blank"
                rel="noopener"
                sx={proseLinkStyle}
              >
                Model Context Protocol (MCP)
              </Link>{' '}
              is an open standard by Anthropic that enables ai assistants to securely connect to
              external data sources and tools.
            </Typography>

            <Typography sx={textStyle}>
              anyplot provides an MCP server so you can use your ai assistant to:
            </Typography>

            <Box component="ul" sx={{ m: 0, pl: 3, mb: 2 }}>
              {[
                'search and discover plot types by tags, features, or keywords',
                'fetch ready-to-use Python code for any supported library',
                'get AI-assisted help adapting code to your specific data',
              ].map((item, i) => (
                <Typography key={i} component="li" sx={textStyle}>
                  {item}
                </Typography>
              ))}
            </Box>

            <Typography sx={textStyle}>
              <strong>endpoint</strong>:{' '}
              <Box component="code" sx={inlineCodeSx}>
                https://api.anyplot.ai/mcp/
              </Box>
            </Typography>
          </Box>
        </Box>

        {/* Configuration */}
        <Box component="section" id="configuration" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>configuration</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={textStyle}>
              use these parameters to configure anyplot in your MCP client:
            </Typography>

            <Table sx={{ ...tableStyle, mb: 3 }}>
              <TableBody>
                <TableRow>
                  <TableCell sx={{ width: 140 }}>server name</TableCell>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      anyplot
                    </Box>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>url</TableCell>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      https://api.anyplot.ai/mcp/
                    </Box>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>transport</TableCell>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      http
                    </Box>{' '}
                    (Streamable HTTP)
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>

            <Typography sx={subheadingStyle}>claude code</Typography>
            <Box sx={codeBlockStyle}>
              {`claude mcp add anyplot --transport http https://api.anyplot.ai/mcp/`}
            </Box>

            <Typography sx={{ ...textStyle, mt: 3 }}>
              verify by asking &quot;list available plot types from anyplot&quot;.
            </Typography>
          </Box>
        </Box>

        {/* Available Tools */}
        <Box component="section" id="tools" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>available tools</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={textStyle}>
              the MCP server provides these tools for ai assistants to interact with anyplot:
            </Typography>

            <Table sx={tableStyle}>
              <TableHead>
                <TableRow>
                  <TableCell>tool</TableCell>
                  <TableCell>description</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      list_specs
                    </Box>
                  </TableCell>
                  <TableCell>
                    list all plot specifications with summary information (title, tags, library
                    count)
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      search_specs_by_tags
                    </Box>
                  </TableCell>
                  <TableCell>
                    search specifications using tag filters (plot_type, data_type, domain, features,
                    library)
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      get_spec_detail
                    </Box>
                  </TableCell>
                  <TableCell>
                    get complete specification including all implementations and metadata
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      get_implementation
                    </Box>
                  </TableCell>
                  <TableCell>
                    get implementation code for a specific specification and library
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      list_libraries
                    </Box>
                  </TableCell>
                  <TableCell>
                    list all supported plotting libraries (matplotlib, seaborn, plotly, etc.)
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      get_tag_values
                    </Box>
                  </TableCell>
                  <TableCell>
                    get all available values for a specific tag category with counts
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Box>
        </Box>

        {/* Use Cases */}
        <Box component="section" id="use-cases" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>use cases</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Typography sx={subheadingStyle}>ai-assisted plot discovery</Typography>
            <Typography sx={textStyle}>
              ask Claude to find the right plot type for your data. for example: &quot;I have two
              numeric variables and want to show their correlation. What plot types does anyplot
              have?&quot; Claude will search the specifications and suggest appropriate
              visualizations.
            </Typography>

            <Typography sx={subheadingStyle}>code generation with ai</Typography>
            <Typography sx={textStyle}>
              Claude can fetch implementation code and adapt it to your specific data. ask:
              &quot;Get me the matplotlib code for a scatter plot and modify it to use my sales
              data.&quot; Claude will retrieve the code and customize it for your needs.
            </Typography>

            <Typography sx={subheadingStyle}>comparing library implementations</Typography>
            <Typography sx={textStyle}>
              compare how different libraries implement the same visualization. ask: &quot;Show me
              how to create a heatmap in both seaborn and plotly.&quot; Claude will fetch both
              implementations so you can compare their approaches and choose the best fit for your
              project.
            </Typography>
          </Box>
        </Box>

        {/* Resources */}
        <Box component="section" id="resources" sx={{ py: { xs: 2, md: 3 } }}>
          <SectionHeader prompt="❯" title={<em>resources</em>} />

          <Box sx={{ maxWidth: 760, mx: 'auto' }}>
            <Table sx={tableStyle}>
              <TableBody>
                <TableRow>
                  <TableCell>full mcp documentation</TableCell>
                  <TableCell>
                    <Link
                      href={`${GITHUB_URL}/blob/main/docs/reference/mcp.md`}
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      docs/reference/mcp.md
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>mcp official website</TableCell>
                  <TableCell>
                    <Link
                      href="https://modelcontextprotocol.io"
                      target="_blank"
                      rel="noopener"
                      sx={proseLinkStyle}
                    >
                      modelcontextprotocol.io
                    </Link>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>mcp inspector</TableCell>
                  <TableCell>
                    <Box component="code" sx={inlineCodeSx}>
                      npx @modelcontextprotocol/inspector https://api.anyplot.ai/mcp/
                    </Box>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Box>
        </Box>
      </Box>
    </>
  );
}
