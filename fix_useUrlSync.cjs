const fs = require('fs');

// 1. Update useUrlSync.ts
const file = "app/src/hooks/useUrlSync.ts";
let content = fs.readFileSync(file, 'utf8');

content = content.replace(/\/\*\*[\s\S]*?Hook to synchronize active filters with URL and updates document title\.[\s\S]*?\*\//, "/**\n * Hook to synchronize active filters with URL.\n */");

const titleRegex = /\s*const filterParts = activeFilters[\s\S]*?if \(filterParts\) \{[\s\S]*?document\.title = `\$\{filterParts\} \| anyplot\.ai`;[\s\S]*?\} else \{[\s\S]*?document\.title = 'anyplot\.ai';[\s\S]*?\}/;
content = content.replace(titleRegex, "");

content = content.replace(/\s*\/\/ Update document title/, "");

fs.writeFileSync(file, content);

// 1b. Update useUrlSync.test.ts
const file_test = "app/src/hooks/useUrlSync.test.ts";
let content_test = fs.readFileSync(file_test, 'utf8');

content_test = content_test.replace("updates URL and title", "updates URL");
content_test = content_test.replace(/\s*expect\(document\.title\)\.toBe\('lib:matplotlib \| anyplot\.ai'\);/, "");
content_test = content_test.replace(/\s*expect\(document\.title\)\.toBe\('anyplot\.ai'\);/, "");

fs.writeFileSync(file_test, content_test);
