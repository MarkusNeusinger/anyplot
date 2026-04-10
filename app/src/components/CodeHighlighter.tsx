import SyntaxHighlighter from 'react-syntax-highlighter/dist/esm/prism-light';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import { typography } from '../theme';

SyntaxHighlighter.registerLanguage('python', python);

interface CodeHighlighterProps {
  code: string;
}

export default function CodeHighlighter({ code }: CodeHighlighterProps) {
  return (
    <SyntaxHighlighter
      language="python"
      style={oneLight}
      customStyle={{
        margin: 0,
        fontSize: '0.85rem',
        fontFamily: typography.fontFamily,
        background: 'transparent',
      }}
    >
      {code}
    </SyntaxHighlighter>
  );
}
