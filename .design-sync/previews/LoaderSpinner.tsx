import { LoaderSpinner } from 'anyplot';

// The brand loader — two dots tween between imprint green and ochre. The frozen
// screenshot catches one frame of the 2s loop; both sizes shown.
export function Large() {
  return (
    <div style={{ padding: 40, display: 'flex', justifyContent: 'center' }}>
      <LoaderSpinner size="large" />
    </div>
  );
}

export function Small() {
  return (
    <div style={{ padding: 40, display: 'flex', justifyContent: 'center' }}>
      <LoaderSpinner size="small" />
    </div>
  );
}
