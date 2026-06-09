import { Component, ReactNode } from 'react';

import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import HomeIcon from '@mui/icons-material/Home';
import RefreshIcon from '@mui/icons-material/Refresh';
import ReplayIcon from '@mui/icons-material/Replay';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

import { CONFIG } from 'src/global-config';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  componentStack: string | null;
  showDetails: boolean;
  copied: boolean;
}

/**
 * Error boundary component that catches rendering errors in child components.
 * Displays a user-friendly error message with recovery options and — behind
 * a disclosure — the diagnostic context (message, stack, UA, URL) needed to
 * debug device-specific crashes (e.g. iOS-only WebKit incompatibilities).
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      componentStack: null,
      showDetails: false,
      copied: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ componentStack: errorInfo.componentStack ?? null });
  }

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      componentStack: null,
      showDetails: false,
      copied: false,
    });
  };

  handleToggleDetails = (): void => {
    this.setState(s => ({ showDetails: !s.showDetails }));
  };

  buildDetails = (): string => {
    const { error, componentStack } = this.state;
    const lines = [
      `Message: ${error?.message ?? '(unknown)'}`,
      `URL: ${typeof window !== 'undefined' ? window.location.href : '(unknown)'}`,
      `User-Agent: ${typeof navigator !== 'undefined' ? navigator.userAgent : '(unknown)'}`,
      `Timestamp: ${new Date().toISOString()}`,
      '',
      '--- Stack ---',
      error?.stack ?? '(no stack)',
    ];
    if (componentStack) {
      lines.push('', '--- React component stack ---', componentStack.trim());
    }
    return lines.join('\n');
  };

  handleCopyDetails = async (): Promise<void> => {
    const text = this.buildDetails();
    try {
      await navigator.clipboard?.writeText(text);
      this.setState({ copied: true });
      window.setTimeout(() => this.setState({ copied: false }), 2000);
    } catch {
      // Clipboard API unavailable (older iOS, insecure context). The text is
      // already visible in the disclosure block, so the user can copy manually.
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, componentStack, showDetails, copied } = this.state;

      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '50vh',
            padding: 4,
            textAlign: 'center',
          }}
        >
          <Alert
            severity="error"
            sx={{
              maxWidth: 640,
              width: '100%',
              mb: 3,
            }}
          >
            <Typography variant="h6" component="div" sx={{ fontWeight: 600, mb: 1 }}>
              Something went wrong
            </Typography>
            <Typography variant="body2" sx={{ color: 'var(--ink-muted)' }}>
              An unexpected error occurred. Please try reloading the page.
            </Typography>

            {error && (
              <Typography
                variant="caption"
                component="pre"
                sx={{
                  mt: 2,
                  p: 1,
                  bgcolor: 'var(--bg-surface)',
                  color: 'var(--ink-soft)',
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: 80,
                  textAlign: 'left',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {error.message || error.name || 'Unknown error'}
              </Typography>
            )}

            <Box
              sx={{
                mt: 2,
                display: 'flex',
                gap: 1,
                flexWrap: 'wrap',
                justifyContent: 'center',
              }}
            >
              <Button
                size="small"
                variant="text"
                onClick={this.handleToggleDetails}
                sx={{ textTransform: 'none' }}
                aria-expanded={showDetails}
              >
                {showDetails ? 'Hide technical details' : 'Show technical details'}
              </Button>
              <Button
                size="small"
                variant="text"
                startIcon={<ContentCopyIcon fontSize="small" />}
                onClick={this.handleCopyDetails}
                sx={{ textTransform: 'none' }}
              >
                {copied ? 'Copied' : 'Copy details'}
              </Button>
            </Box>

            {showDetails && (
              <Typography
                variant="caption"
                component="pre"
                data-testid="error-details"
                sx={{
                  mt: 2,
                  p: 1.5,
                  bgcolor: 'var(--bg-surface)',
                  color: 'var(--ink-soft)',
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: 280,
                  textAlign: 'left',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontSize: '0.7rem',
                }}
              >
                {this.buildDetails()}
              </Typography>
            )}

            {componentStack && CONFIG.isDev && !showDetails && (
              <Typography
                variant="caption"
                sx={{ mt: 1, display: 'block', color: 'var(--ink-muted)' }}
              >
                React component stack available — click "Show technical details".
              </Typography>
            )}
          </Alert>

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Button
              variant="contained"
              startIcon={<ReplayIcon />}
              onClick={this.handleRetry}
              sx={{ textTransform: 'none' }}
            >
              Try Again
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={this.handleReload}
              sx={{ textTransform: 'none' }}
            >
              Reload Page
            </Button>
            <Button
              variant="outlined"
              startIcon={<HomeIcon />}
              onClick={this.handleGoHome}
              sx={{ textTransform: 'none' }}
            >
              Go Home
            </Button>
          </Box>
        </Box>
      );
    }

    return this.props.children;
  }
}
