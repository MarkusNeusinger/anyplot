import type { ImageSize } from 'src/constants';
import type { TrackEvent } from 'src/hooks/useAnalytics';
import { ToolbarActions } from 'src/sections/plots-gallery/ToolbarActions';

export interface FilterSizeToggleProps {
  imageSize: ImageSize;
  onImageSizeChange: (size: ImageSize) => void;
  onTrackEvent: TrackEvent;
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
