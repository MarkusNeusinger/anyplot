const fs = require('fs');

const pageFile = 'app/src/pages/PlotsPage.tsx';
let content = fs.readFileSync(pageFile, 'utf8');

// I mistakenly replaced `clearFilters,\n  } = useFilterState(specsData, librariesData, languagesData);`
// but it looks like `clearFilters` isn't there, or the hook signature changed.
// Let's insert the useMemo logic right after `setHasMore,` on line 43.
content = content.replace("  const { loadMoreRef } = useInfiniteScroll({", `  const filterParts = useMemo(() => {
    return activeFilters
      .filter(f => f.values.length > 0)
      .map(f => \`\${f.category}:\${f.values.join(',')}\`)
      .join(' ');
  }, [activeFilters]);

  const pageTitle = filterParts ? \`\${filterParts} | plots | anyplot.ai\` : 'plots | anyplot.ai';

  const { loadMoreRef } = useInfiniteScroll({`);

fs.writeFileSync(pageFile, content);
