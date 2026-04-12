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

  it('sets language to python', () => {
    render(<CodeHighlighter code="print('hello')" />);
    expect(screen.getByTestId('syntax-highlighter')).toHaveAttribute(
      'data-language',
      'python'
    );
  });
});
