import type { ImageSize } from 'src/constants';
import { ToolbarActions } from 'src/sections/plots-gallery/ToolbarActions';

export interface FilterSizeToggleProps {
  imageSize: ImageSize;
  onImageSizeChange: (size: ImageSize) => void;
  onTrackEvent: (event: string, props?: Record<string, string>) => void;
}

/**
 * Image-size toggle wrapper used on both the desktop (absolute right) and
 * mobile (counter row) placements of the FilterBar.
 */
export function FilterSizeToggle({
  imageSize,
  onImageSizeChange,
  onTrackEvent,
}: FilterSizeToggleProps) {
  return (
    <ToolbarActions
      imageSize={imageSize}
      onImageSizeChange={onImageSizeChange}
      onTrackEvent={onTrackEvent}
    />
  );
}
