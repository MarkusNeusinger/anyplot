import Box from '@mui/material/Box';

export function MapPinMarker({
  pinnedId,
  pinScreen,
  pinColor,
}: {
  pinnedId: string | null;
  pinScreen: { x: number; y: number; w: number; h: number } | null;
  pinColor: string;
}) {
  if (!pinnedId || !pinScreen) return null;

  return (
    <Box
      sx={{
        position: 'absolute',
        left: pinScreen.x,
        top: pinScreen.y,
        width: pinScreen.w,
        height: pinScreen.h,
        pointerEvents: 'none',
        zIndex: 2,
        borderRadius: '2px',
        animation: 'mapPinPulse 1.4s ease-in-out infinite',
        '@keyframes mapPinPulse': {
          '0%, 100%': {
            outline: `2px solid ${pinColor}`,
            outlineOffset: '2px',
            boxShadow: `0 0 8px ${pinColor}`,
            opacity: 0.9,
          },
          '50%': {
            outline: `4px solid ${pinColor}`,
            outlineOffset: '5px',
            boxShadow: `0 0 28px ${pinColor}, 0 0 6px ${pinColor}`,
            opacity: 1,
          },
        },
      }}
    />
  );
}
