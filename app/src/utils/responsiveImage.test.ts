import { describe, it, expect } from 'vitest';
import {
  buildSrcSet,
  buildDetailSrcSet,
  getResponsiveSizes,
  getFallbackSrc,
  DETAIL_SIZES,
  OVERVIEW_SIZES,
  SPECS_SIZES,
} from './responsiveImage';

describe('responsiveImage utilities', () => {
  const baseUrl = 'https://cdn.example.com/plots/scatter-basic/matplotlib/plot.png';

  describe('buildSrcSet', () => {
    it('generates webp srcSet with 400, 800, 1200 widths', () => {
      const result = buildSrcSet(baseUrl, 'webp');
      expect(result).toBe(
        'https://cdn.example.com/plots/scatter-basic/matplotlib/plot_400.webp 400w, ' +
        'https://cdn.example.com/plots/scatter-basic/matplotlib/plot_800.webp 800w, ' +
        'https://cdn.example.com/plots/scatter-basic/matplotlib/plot_1200.webp 1200w'
      );
    });

    it('generates png srcSet with 400, 800, 1200 widths', () => {
      const result = buildSrcSet(baseUrl, 'png');
      expect(result).toBe(
        'https://cdn.example.com/plots/scatter-basic/matplotlib/plot_400.png 400w, ' +
        'https://cdn.example.com/plots/scatter-basic/matplotlib/plot_800.png 800w, ' +
        'https://cdn.example.com/plots/scatter-basic/matplotlib/plot_1200.png 1200w'
      );
    });

    it('handles URL without .png extension (no stripping)', () => {
      const url = 'https://cdn.example.com/image';
      const result = buildSrcSet(url, 'webp');
      // getBasePath only strips trailing .png, so the base stays as-is
      expect(result).toContain('https://cdn.example.com/image_400.webp 400w');
      expect(result).toContain('https://cdn.example.com/image_800.webp 800w');
      expect(result).toContain('https://cdn.example.com/image_1200.webp 1200w');
    });

    it('handles empty string URL', () => {
      const result = buildSrcSet('', 'webp');
      expect(result).toBe('_400.webp 400w, _800.webp 800w, _1200.webp 1200w');
    });
  });

  describe('buildDetailSrcSet', () => {
    it('includes responsive sizes plus full-res at 3840w for webp', () => {
      const result = buildDetailSrcSet(baseUrl, 'webp');
      const base = 'https://cdn.example.com/plots/scatter-basic/matplotlib/plot';
      expect(result).toBe(
        `${base}_400.webp 400w, ${base}_800.webp 800w, ${base}_1200.webp 1200w, ${base}.webp 3840w`
      );
    });

    it('includes responsive sizes plus full-res at 3840w for png', () => {
      const result = buildDetailSrcSet(baseUrl, 'png');
      const base = 'https://cdn.example.com/plots/scatter-basic/matplotlib/plot';
      expect(result).toBe(
        `${base}_400.png 400w, ${base}_800.png 800w, ${base}_1200.png 1200w, ${base}.png 3840w`
      );
    });
  });

  describe('getResponsiveSizes', () => {
    it('returns normal sizes (1/2/3 columns)', () => {
      const result = getResponsiveSizes('normal');
      expect(result).toBe('(max-width: 899px) 100vw, (max-width: 1535px) 50vw, 33vw');
    });

    it('returns compact sizes (2/4/6 columns)', () => {
      const result = getResponsiveSizes('compact');
      expect(result).toBe('(max-width: 899px) 50vw, (max-width: 1535px) 25vw, 17vw');
    });
  });

  describe('getFallbackSrc', () => {
    it('returns _800.png variant for standard URL', () => {
      expect(getFallbackSrc(baseUrl)).toBe(
        'https://cdn.example.com/plots/scatter-basic/matplotlib/plot_800.png'
      );
    });

    it('handles URL without .png extension', () => {
      const url = 'https://cdn.example.com/image';
      expect(getFallbackSrc(url)).toBe('https://cdn.example.com/image_800.png');
    });

    it('handles empty string URL', () => {
      expect(getFallbackSrc('')).toBe('_800.png');
    });
  });

  describe('exported constants', () => {
    it('DETAIL_SIZES matches expected media queries', () => {
      expect(DETAIL_SIZES).toBe('(max-width: 1199px) 100vw, (max-width: 1535px) 1400px, 1600px');
    });

    it('OVERVIEW_SIZES matches expected media queries', () => {
      expect(OVERVIEW_SIZES).toBe('(max-width: 1199px) 33vw, (max-width: 1535px) 467px, 534px');
    });

    it('SPECS_SIZES matches expected media queries', () => {
      expect(SPECS_SIZES).toBe('(max-width: 599px) 100vw, 280px');
    });
  });
});
