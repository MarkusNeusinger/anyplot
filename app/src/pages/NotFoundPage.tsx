import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { Footer } from '../components';

export function NotFoundPage() {
  return (
    <>
      <Helmet>
        <title>page not found | pyplots.ai</title>
        <meta name="robots" content="noindex, follow" />
      </Helmet>
      <Box sx={{ textAlign: 'center', py: 12 }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{ fontFamily: '"MonoLisa", monospace', fontWeight: 600, mb: 2, color: '#1f2937' }}
        >
          404
        </Typography>
        <Typography sx={{ fontFamily: '"MonoLisa", monospace', color: '#6b7280', mb: 4 }}>
          page not found
        </Typography>
        <Box
          component={Link}
          to="/"
          sx={{ color: '#3776AB', fontFamily: '"MonoLisa", monospace', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
        >
          back to pyplots.ai
        </Box>
      </Box>
      <Footer />
    </>
  );
}
