import { afterEach, describe, expect, it, vi } from 'vitest';

import { ChromaWheel } from 'src/sections/palette/ChromaWheel';
import type { WheelDot } from 'src/sections/palette/types';
import { render, screen } from 'src/test-utils';

const SAMPLE_DOTS: WheelDot[] = [
  { hex: '#009E73', L: 0.62, C: 0.13, H: 165.5, name: 'brand green' },
  { hex: '#C475FD', L: 0.704, C: 0.202, H: 308.9, name: 'lavender' },
  { hex: '#4467A3', L: 0.516, C: 0.104, H: 260.6 },
];

const OVERLAY_DOTS: WheelDot[] = [
  { hex: '#D55E00', L: 0.621, C: 0.17, H: 47.5 },
  { hex: '#56B4E9', L: 0.735, C: 0.117, H: 236.2 },
];

function stubCanvas2D() {
  const putImageData = vi.fn();
  const createImageData = vi.fn((w: number, h: number) => ({
    width: w,
    height: h,
    colorSpace: 'srgb' as PredefinedColorSpace,
    data: new Uint8ClampedArray(w * h * 4),
  }));
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(
    () =>
      ({
        createImageData,
        putImageData,
      }) as unknown as CanvasRenderingContext2D
  );
  return { createImageData, putImageData };
}

describe('ChromaWheel', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('renders angle labels, brand star title, and dot titles in full mode and paints the canvas once per size', () => {
    const { putImageData } = stubCanvas2D();
    const { rerender } = render(<ChromaWheel size={64} imprintDots={SAMPLE_DOTS} />);

    expect(screen.getByText('0°')).toBeInTheDocument();
    expect(screen.getByText('90°')).toBeInTheDocument();
    expect(screen.getByText('180°')).toBeInTheDocument();
    expect(screen.getByText('270°')).toBeInTheDocument();

    expect(screen.getByText('★ brand green · #009E73')).toBeInTheDocument();
    expect(screen.getByText('lavender · #C475FD')).toBeInTheDocument();
    expect(screen.getByText('#4467A3')).toBeInTheDocument();
    expect(putImageData).toHaveBeenCalledTimes(1);

    // Re-rendering with the same size and dpr skips the per-pixel repaint.
    rerender(<ChromaWheel size={64} imprintDots={SAMPLE_DOTS} />);
    expect(putImageData).toHaveBeenCalledTimes(1);
  });

  it('hides angle labels in compact mode and renders overlay palette rings when provided', () => {
    stubCanvas2D();
    render(<ChromaWheel size={64} compact imprintDots={SAMPLE_DOTS} overlay={OVERLAY_DOTS} />);

    expect(screen.queryByText('0°')).not.toBeInTheDocument();
    expect(screen.queryByText('90°')).not.toBeInTheDocument();
    expect(screen.getByText('#D55E00')).toBeInTheDocument();
    expect(screen.getByText('#56B4E9')).toBeInTheDocument();
  });

  it('renders cleanly with default size when 2D canvas context is unavailable', () => {
    vi.stubGlobal('devicePixelRatio', 0);
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);

    render(<ChromaWheel imprintDots={SAMPLE_DOTS} />);

    expect(screen.getByText('★ brand green · #009E73')).toBeInTheDocument();
    expect(screen.getByText('180°')).toBeInTheDocument();
  });
});
