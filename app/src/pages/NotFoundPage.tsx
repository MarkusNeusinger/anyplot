import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { Footer } from '../components/Footer';
import { typography, colors, semanticColors } from '../theme';

export function NotFoundPage() {
  return (
    <>
      <Helmet>
        <title>page not found | anyplot.ai</title>
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      <Box sx={{ textAlign: 'center', py: 12 }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{ fontFamily: typography.fontFamily, fontWeight: 600, mb: 2, color: colors.gray[800] }}
        >
          404
        </Typography>
        <Typography sx={{ fontFamily: typography.fontFamily, color: semanticColors.mutedText, mb: 4 }}>
          page not found
        </Typography>
        <Box
          component={Link}
          to="/"
          sx={{ color: colors.primary, fontFamily: typography.fontFamily, textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
        >
          back to anyplot.ai
        </Box>
      </Box>
      <Footer />
    </>
  );
}
