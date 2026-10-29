export type CompPalette = {
  id: string;
  name: string;
  href?: string;
  hexes: { hex: string; L: number; C: number; H: number }[];
};

export type Anchor = {
  key: string;
  hexLight: string;
  hexDark?: string;
  role: string;
  hint: string;
};

export type HistoryEntry = {
  id: string;
  title: string;
  hexes: string[];
  summary: string;
  href?: string;
  hrefLabel?: string;
};

export type WheelDot = { hex: string; L: number; C: number; H: number; name?: string };
