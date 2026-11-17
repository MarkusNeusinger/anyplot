/**
 * MonoLisa's advance is 0.64em. The face the page shows while it loads is sized to match it
 * (`MonoLisa Fallback` in fonts.css) and comes to 0.641em at most, so a line is counted at that.
 */
const MONO_EM = 0.641;

/**
 * The width in px of one line of `text` at `size` px in the page's monospace face, as wide as a
 * browser lays it out either way. Most lay text out with fractional advances. Where the system
 * hints glyphs to whole pixels (full hinting, as Chrome's headless shell and some Linux desktops
 * do), each advance is rounded to the nearest pixel instead: a 12px character takes 8px rather
 * than 7.68px, so a line of them runs about 4 % wider, while an 11px one takes 7px. Each line is
 * counted at the wider of the two, so the figures' switches and the timeline's labels, which are
 * placed from this width rather than measured, hold in both.
 */
export function monoWidth(text: string, size: number): number {
  const advance = size * MONO_EM;
  return Math.ceil(text.length * Math.max(advance, Math.round(advance)));
}
