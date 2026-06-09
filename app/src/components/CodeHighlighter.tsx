import SyntaxHighlighter from 'react-syntax-highlighter/dist/esm/prism-light';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import r from 'react-syntax-highlighter/dist/esm/languages/prism/r';
import julia from 'react-syntax-highlighter/dist/esm/languages/prism/julia';
import javascript from 'react-syntax-highlighter/dist/esm/languages/prism/javascript';
import tsx from 'react-syntax-highlighter/dist/esm/languages/prism/tsx';
import { typography } from '../theme';

SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('r', r);
SyntaxHighlighter.registerLanguage('julia', julia);
SyntaxHighlighter.registerLanguage('javascript', javascript);
// The refractor `tsx` grammar auto-registers its own dependencies (jsx →
// javascript + markup, and typescript), so this one call covers React TSX.
SyntaxHighlighter.registerLanguage('tsx', tsx);

// Map anyplot language IDs → Prism grammar names. Anything we don't know about
// falls back to plain text so the block still renders, just unhighlighted.
const PRISM_LANGUAGE: Record<string, string> = {
  python: 'python',
  r: 'r',
  julia: 'julia',
  javascript: 'javascript',
};

// Per-library grammar override: a library whose snippets are authored in a
// dialect that needs a richer grammar than its language default. MUI X (`muix`)
// is JavaScript-language but authored as React TSX, so it highlights with the
// `tsx` grammar (JSX + TypeScript) rather than plain `javascript`.
const LIBRARY_GRAMMAR_OVERRIDE: Record<string, string> = {
  muix: 'tsx',
};

// Theme-aware imprint syntax theme. All colors come from CSS variables in
// tokens.css so the block adapts to light (paper) and dark modes. Comments
// use the brand green as a deliberate editorial accent.
const imprintTheme: Record<string, React.CSSProperties> = {
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
  language?: string;
  /** Library id — lets a library override its language's default grammar
   *  (e.g. muix → tsx even though its language is javascript). */
  library?: string;
}

export default function CodeHighlighter({ code, language = 'python', library }: CodeHighlighterProps) {
  const prismLanguage =
    (library ? LIBRARY_GRAMMAR_OVERRIDE[library.toLowerCase()] : undefined) ??
    PRISM_LANGUAGE[language.toLowerCase()] ??
    'text';
  return (
    <SyntaxHighlighter
      language={prismLanguage}
      style={imprintTheme}
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
