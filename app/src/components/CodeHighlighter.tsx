import SyntaxHighlighter from 'react-syntax-highlighter/dist/esm/prism-light';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import { typography } from '../theme';

SyntaxHighlighter.registerLanguage('python', python);

// Custom dark theme using Okabe-Ito palette colors
const okabeItoDark: Record<string, React.CSSProperties> = {
  'pre[class*="language-"]': {
    color: '#E8E8E0',
    background: 'var(--code-bg)',
  },
  'code[class*="language-"]': {
    color: '#E8E8E0',
    background: 'none',
  },
  comment: { color: '#666', fontStyle: 'italic' },
  prolog: { color: '#666' },
  doctype: { color: '#666' },
  cdata: { color: '#666' },
  keyword: { color: '#56B4E9' },       // sky blue
  builtin: { color: '#56B4E9' },
  operator: { color: '#E8E8E0' },
  string: { color: '#009E73' },        // green
  'attr-value': { color: '#009E73' },
  'template-string': { color: '#009E73' },
  function: { color: '#E69F00' },      // orange
  'function-variable': { color: '#E69F00' },
  'class-name': { color: '#E69F00' },
  number: { color: '#F0E442' },        // yellow
  boolean: { color: '#F0E442' },
  variable: { color: '#CC79A7' },      // purple
  property: { color: '#CC79A7' },
  constant: { color: '#D55E00' },      // vermillion
  decorator: { color: '#D55E00' },
  punctuation: { color: '#8A8A82' },
  selector: { color: '#009E73' },
  tag: { color: '#D55E00' },
  'attr-name': { color: '#E69F00' },
  regex: { color: '#009E73' },
  important: { color: '#D55E00', fontWeight: 'bold' },
};

interface CodeHighlighterProps {
  code: string;
}

export default function CodeHighlighter({ code }: CodeHighlighterProps) {
  return (
    <SyntaxHighlighter
      language="python"
      style={okabeItoDark}
      customStyle={{
        margin: 0,
        padding: '28px 32px',
        fontSize: '0.85rem',
        fontFamily: typography.fontFamily,
        background: 'var(--code-bg)',
        borderRadius: '12px',
        lineHeight: 1.7,
      }}
    >
      {code}
    </SyntaxHighlighter>
  );
}
