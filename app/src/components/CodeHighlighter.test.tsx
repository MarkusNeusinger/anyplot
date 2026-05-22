import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../test-utils';

vi.mock('react-syntax-highlighter/dist/esm/prism-light', () => {
  const MockHighlighter = ({
    children,
    language,
    ...props
  }: {
    children: string;
    language: string;
    style?: object;
    customStyle?: object;
  }) => (
    <pre data-testid="syntax-highlighter" data-language={language} {...props}>
      {children}
    </pre>
  );
  MockHighlighter.registerLanguage = vi.fn();
  return { default: MockHighlighter };
});

vi.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
  oneLight: {},
}));

vi.mock('react-syntax-highlighter/dist/esm/languages/prism/python', () => ({
  default: {},
}));

vi.mock('react-syntax-highlighter/dist/esm/languages/prism/r', () => ({
  default: {},
}));

vi.mock('react-syntax-highlighter/dist/esm/languages/prism/julia', () => ({
  default: {},
}));

import CodeHighlighter from './CodeHighlighter';

describe('CodeHighlighter', () => {
  it('renders without crashing', () => {
    render(<CodeHighlighter code="x = 1" />);
    expect(screen.getByTestId('syntax-highlighter')).toBeInTheDocument();
  });

  it('renders the provided code text', () => {
    const code = 'import matplotlib.pyplot as plt\nplt.show()';
    render(<CodeHighlighter code={code} />);
    const highlighter = screen.getByTestId('syntax-highlighter');
    expect(highlighter).toHaveTextContent('import matplotlib.pyplot as plt');
    expect(highlighter).toHaveTextContent('plt.show()');
  });

  it('defaults to python when no language prop given', () => {
    render(<CodeHighlighter code="print('hello')" />);
    expect(screen.getByTestId('syntax-highlighter')).toHaveAttribute(
      'data-language',
      'python'
    );
  });

  it('uses r grammar when language is "r"', () => {
    render(<CodeHighlighter code='library(ggplot2)' language="r" />);
    expect(screen.getByTestId('syntax-highlighter')).toHaveAttribute(
      'data-language',
      'r'
    );
  });

  it('uses julia grammar when language is "julia"', () => {
    render(<CodeHighlighter code='using CairoMakie' language="julia" />);
    expect(screen.getByTestId('syntax-highlighter')).toHaveAttribute(
      'data-language',
      'julia'
    );
  });

  it('falls back to plain text for unknown languages', () => {
    render(<CodeHighlighter code='echo "hi"' language="bash" />);
    expect(screen.getByTestId('syntax-highlighter')).toHaveAttribute(
      'data-language',
      'text'
    );
  });
});
