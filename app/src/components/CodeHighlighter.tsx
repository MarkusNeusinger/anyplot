import SyntaxHighlighter from 'react-syntax-highlighter/dist/esm/prism-light';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import { typography } from '../theme';

SyntaxHighlighter.registerLanguage('python', python);

// Theme-aware Okabe-Ito syntax theme. All colors come from CSS variables in
// tokens.css so the block adapts to light (paper) and dark modes. Comments
// use the brand green as a deliberate editorial accent.
const okabeItoTheme: Record<string, React.CSSProperties> = {
  'pre[class*="language-"]': {
    color: 'var(--code-text)',
    background: 'var(--code-bg)',
  },
  'code[class*="language-"]': {
    color: 'var(--code-text)',
    background: 'none',
  },
  comment: { color: 'var(--code-comment)', fontStyle: 'italic' },
  prolog: { color: 'var(--code-comment)', fontStyle: 'italic' },
  doctype: { color: 'var(--code-comment)' },
  cdata: { color: 'var(--code-comment)' },
  keyword: { color: 'var(--code-keyword)' },
  builtin: { color: 'var(--code-keyword)' },
  operator: { color: 'var(--code-operator)' },
  string: { color: 'var(--code-string)' },
  'attr-value': { color: 'var(--code-string)' },
  'template-string': { color: 'var(--code-string)' },
  function: { color: 'var(--code-function)', fontWeight: 600 },
  'function-variable': { color: 'var(--code-function)', fontWeight: 600 },
  'class-name': { color: 'var(--code-function)', fontWeight: 600 },
  number: { color: 'var(--code-number)' },
  boolean: { color: 'var(--code-number)' },
  variable: { color: 'var(--code-variable)' },
  property: { color: 'var(--code-variable)' },
  constant: { color: 'var(--code-constant)' },
  decorator: { color: 'var(--code-constant)' },
  punctuation: { color: 'var(--code-punctuation)' },
  selector: { color: 'var(--code-string)' },
  tag: { color: 'var(--code-constant)' },
  'attr-name': { color: 'var(--code-function)' },
  regex: { color: 'var(--code-string)' },
  important: { color: 'var(--code-constant)', fontWeight: 'bold' },
};

interface CodeHighlighterProps {
  code: string;
}

export default function CodeHighlighter({ code }: CodeHighlighterProps) {
  return (
    <SyntaxHighlighter
      language="python"
      style={okabeItoTheme}
      customStyle={{
        margin: 0,
        padding: '24px 28px',
        fontSize: '0.85rem',
        fontFamily: typography.fontFamily,
        background: 'var(--code-bg)',
        color: 'var(--code-text)',
        border: '1px solid var(--code-border)',
        borderRadius: '8px',
        lineHeight: 1.7,
        overflow: 'auto',
        maxWidth: '100%',
      }}
    >
      {code}
    </SyntaxHighlighter>
  );
}
