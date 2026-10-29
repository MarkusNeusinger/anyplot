const fs = require('fs');

const testFile = 'app/src/pages/PlotsPage.test.tsx';
let testContent = fs.readFileSync(testFile, 'utf8');

// I accidentally duplicated the render and expect logic outside the test block or something!
// Look at the grep output:
// 140:  it('renders document metadata with filters', () => {
// 141-    state.activeFilters = [{ category: 'lib', values: ['matplotlib'] }];
// 142-    render(<PlotsPage />);
// 143-    expect(document.title).toBe('lib:matplotlib | plots | anyplot.ai');
// 144-  });
// 145-
// 146-  render(<PlotsPage />);
// 147-  expect(document.title).toBe('lib:matplotlib | plots | anyplot.ai');
// 148-});

testContent = testContent.replace(
    /it\('renders document metadata with filters', \(\) => \{\n\s*state\.activeFilters = \[\{ category: 'lib', values: \['matplotlib'\] \}\];\n\s*render\(<PlotsPage \/>\);\n\s*expect\(document\.title\)\.toBe\('lib:matplotlib \| plots \| anyplot\.ai'\);\n\s*\}\);\n\n\s*render\(<PlotsPage \/>\);\n\s*expect\(document\.title\)\.toBe\('lib:matplotlib \| plots \| anyplot\.ai'\);\n\}\);/,
    "it('renders document metadata with filters', () => {\n    state.activeFilters = [{ category: 'lib', values: ['matplotlib'] }];\n    render(<PlotsPage />);\n    expect(document.title).toBe('lib:matplotlib | plots | anyplot.ai');\n  });\n});"
);

fs.writeFileSync(testFile, testContent);
