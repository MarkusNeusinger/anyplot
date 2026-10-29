const fs = require('fs');

const pageFile = 'app/src/pages/PlotsPage.tsx';
let content = fs.readFileSync(pageFile, 'utf8');

// I inserted it at the end of the file, around useFilterState, where is that? Let's check lines 30-60
const lines = content.split('\n');
console.log(lines.slice(20, 70).join('\n'));
