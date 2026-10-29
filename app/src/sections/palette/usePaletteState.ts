import { useState } from 'react';

import type { Lang } from 'src/pages/PalettePage.helpers';

export function usePaletteState() {
  const [lang, setLang] = useState<Lang>('python');
  const [oklch, setOklch] = useState(false);
  const [compareId, setCompareId] = useState<string | null>(null);
  const [sort, setSort] = useState<'imprint' | 'cvd'>('imprint');
  const [copiedHex, setCopiedHex] = useState<string | null>(null);
  const [wheelOpen, setWheelOpen] = useState(false);

  const copyHex = (hex: string) => {
    void navigator.clipboard
      .writeText(hex)
      .then(() => {
        setCopiedHex(hex);
        setTimeout(() => setCopiedHex(c => (c === hex ? null : c)), 1500);
      })
      .catch(() => {});
  };

  return {
    lang,
    setLang,
    oklch,
    setOklch,
    compareId,
    setCompareId,
    sort,
    setSort,
    copiedHex,
    setCopiedHex,
    wheelOpen,
    setWheelOpen,
    copyHex,
  };
}
