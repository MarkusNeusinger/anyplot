import Box from '@mui/material/Box';

const SWATCHES = [
  '#009E73', '#D55E00', '#0072B2', '#CC79A7',
  '#E69F00', '#56B4E9', '#F0E442', 'var(--ink)',
];

interface PaletteStripProps {
  /** Maximum width in pixels (default 400). Set to `null` for no cap. */
  maxWidth?: number | null;
  /** Strip height in pixels (default 40). */
  height?: number;
  /** Top margin (MUI spacing units, default 5). */
  mt?: number;
}

export function PaletteStrip({ maxWidth = 400, height = 40, mt = 5 }: PaletteStripProps = {}) {
  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      gap: 0,
      mt,
      borderRadius: '6px',
      overflow: 'hidden',
      ...(maxWidth !== null && { maxWidth }),
      mx: 'auto',
      '&:hover .swatch': { flex: 0.5 },
      '&:hover .swatch:hover': { flex: 3 },
    }}>
      {SWATCHES.map((color, i) => (
        <Box
          key={i}
          className="swatch"
          sx={{
            flex: 1,
            height,
            background: color,
            transition: 'flex 0.3s',
          }}
        />
      ))}
    </Box>
  );
}
