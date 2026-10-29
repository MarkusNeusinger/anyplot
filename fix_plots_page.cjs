const fs = require('fs');

const pageFile = 'app/src/pages/PlotsPage.tsx';
let content = fs.readFileSync(pageFile, 'utf8');

// The reason useMemo is unused is because I am using it, but it might be imported twice or something?
// Let's print out the first 20 lines to see.
const lines = content.split('\n');
console.log(lines.slice(0, 20).join('\n'));
