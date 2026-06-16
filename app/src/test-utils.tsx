import type { ReactElement, ReactNode } from 'react';

import { render, type RenderOptions } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { ThemeProvider } from '@mui/material/styles';

import { theme } from 'src/theme';

function AllProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <MemoryRouter>{children}</MemoryRouter>
    </ThemeProvider>
  );
}

function customRender(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, { wrapper: AllProviders, ...options });
}

export { customRender as render };
export { screen, within, waitFor, act, fireEvent } from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
