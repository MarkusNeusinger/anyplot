import Box from '@mui/material/Box';

const SWATCHES = [
  '#009E73', '#D55E00', '#0072B2', '#CC79A7',
  '#E69F00', '#56B4E9', '#F0E442', 'var(--ink)',
];

export function PaletteStrip() {
  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      gap: 0,
      mt: 5,
      borderRadius: '6px',
      overflow: 'hidden',
      maxWidth: 400,
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
            height: 40,
            background: color,
            transition: 'flex 0.3s',
          }}
        />
      ))}
    </Box>
  );
}
