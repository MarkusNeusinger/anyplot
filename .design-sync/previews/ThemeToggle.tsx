import { ThemeToggle } from 'anyplot';

// Controlled tri-state toggle (system → light → dark). onCycle is a no-op here
// so each cell shows one fixed mode with its glyph (◑ / ☀ / ☾) and label.
const noop = () => {};
const frame = (el: React.ReactNode) => (
  <div style={{ padding: 40, display: 'flex', justifyContent: 'center' }}>{el}</div>
);

export function System() {
  return frame(<ThemeToggle mode="system" onCycle={noop} />);
}

export function Light() {
  return frame(<ThemeToggle mode="light" onCycle={noop} />);
}

export function Dark() {
  return frame(<ThemeToggle mode="dark" onCycle={noop} />);
}
