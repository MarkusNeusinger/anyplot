import Box from '@mui/material/Box';
import { SectionHeader } from './SectionHeader';
import { LibraryCard } from './LibraryCard';
import type { LibraryInfo } from '../types';
import { LIBRARIES } from '../constants';

interface LibrariesSectionProps {
  libraries: LibraryInfo[];
  onLibraryClick: (library: string) => void;
}

export function LibrariesSection({ libraries, onLibraryClick }: LibrariesSectionProps) {
  // Use known library order, with counts from stats if available
  const libList = LIBRARIES.map(name => {
    const info = libraries.find(l => l.id === name);
    return { name, count: info ? undefined : undefined }; // counts come from API if available
  });

  return (
    <Box sx={{ maxWidth: 'var(--max)', mx: 'auto', py: { xs: 6, md: 10 } }}>
      <SectionHeader
        number="§ 01"
        title={<>The <em>libraries</em></>}
        linkText="view all"
        linkTo="/plots"
      />

      <Box sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(auto-fill, minmax(280px, 1fr))' },
        gap: 2.5,
      }}>
        {libList.map(lib => (
          <LibraryCard
            key={lib.name}
            name={lib.name}
            onClick={() => onLibraryClick(lib.name)}
          />
        ))}
      </Box>
    </Box>
  );
}
