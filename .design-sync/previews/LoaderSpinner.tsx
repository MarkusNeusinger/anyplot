import { LoaderSpinner } from 'anyplot';

// The brand loader — a gray resting pair and an imprint-green runner that crosses it.
// The frozen screenshot catches one frame of the 2s loop; both sizes shown.
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
