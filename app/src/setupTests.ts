import '@testing-library/jest-dom/vitest';

import { afterEach } from 'vitest';

import { endStay } from 'src/analytics/stay';

// The visit's ten-second clock is module state with a real timer. A test that sends a pageview
// under the production host starts it, and left alone it would fire in a later test of the
// same worker.
afterEach(() => {
  endStay();
});
