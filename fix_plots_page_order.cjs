const fs = require('fs');

const pageFile = 'app/src/pages/PlotsPage.tsx';
let content = fs.readFileSync(pageFile, 'utf8');

// Fix the import order for useMemo and useState
content = content.replace("import { useCallback, useEffect, useRef, useState, useMemo } from 'react';", "import { useCallback, useEffect, useMemo, useRef, useState } from 'react';");

// Move filterParts computation after activeFilters is declared
// activeFilters is declared at line:
//   const {
//     activeFilters,
// ...
//     clearFilters,
//   } = useFilterState(specsData, librariesData, languagesData);

const filterLogic = `
  const filterParts = useMemo(() => {
    return activeFilters
      .filter(f => f.values.length > 0)
      .map(f => \`\${f.category}:\${f.values.join(',')}\`)
      .join(' ');
  }, [activeFilters]);

  const pageTitle = filterParts ? \`\${filterParts} | plots | anyplot.ai\` : 'plots | anyplot.ai';
`;

// Remove it from its current place
content = content.replace(/\s*const filterParts = useMemo\(\(\) => \{[\s\S]*?\}, \[activeFilters\]\);\s*const pageTitle = filterParts \? `\$\{filterParts\} \| plots \| anyplot\.ai` : 'plots \| anyplot\.ai';/, "");

// Insert after clearFilters
content = content.replace(/\s*clearFilters,\s*\} = useFilterState\(specsData, librariesData, languagesData\);/, (match) => {
    return `${match}\n\n${filterLogic}`;
});


fs.writeFileSync(pageFile, content);
