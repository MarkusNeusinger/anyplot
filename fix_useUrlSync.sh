#!/bin/bash

# 1. Update useUrlSync.ts
file="app/src/hooks/useUrlSync.ts"

sed -i '/const filterParts = activeFilters/,/document.title =/d' $file
sed -i "/document.title = 'anyplot.ai'/d" $file
sed -i "/if (filterParts) {/d" $file
sed -i "/} else {/d" $file
sed -i "/}/d" $file
sed -i "s/and updates document title//" $file
sed -i "s/\/\/ Update document title//g" $file

# 1b. Update useUrlSync.test.ts
file_test="app/src/hooks/useUrlSync.test.ts"
sed -i "s/updates URL and title/updates URL/" $file_test
sed -i "/expect(document.title).toBe('lib:matplotlib | anyplot.ai');/d" $file_test
sed -i "/expect(document.title).toBe('anyplot.ai');/d" $file_test
