import { createTheme } from '@mui/material/styles';

import { components } from 'src/theme/components';
import { palette } from 'src/theme/palette';
import { typographyOptions } from 'src/theme/typography';

export const theme = createTheme({
  typography: typographyOptions,
  palette,
  shape: {
    borderRadius: 12,
  },
  components,
});
