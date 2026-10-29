import { useState } from 'react';

import { clearAdminToken, readAdminToken, writeAdminToken } from 'src/utils/adminAuth';

export function useDebugAuth() {
  const [authRequired, setAuthRequired] = useState(false);
  const [adminToken, setAdminToken] = useState<string>(() => readAdminToken());
  const [tokenInput, setTokenInput] = useState('');
  const [reloadCounter, setReloadCounter] = useState(0);

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = tokenInput.trim();
    if (!trimmed) return;
    writeAdminToken(trimmed);
    setAdminToken(trimmed);
    setTokenInput('');
  };

  const handleTokenClear = () => {
    clearAdminToken();
    setAdminToken('');
    setReloadCounter(c => c + 1);
  };

  return {
    authRequired,
    setAuthRequired,
    adminToken,
    setAdminToken,
    tokenInput,
    setTokenInput,
    reloadCounter,
    handleTokenSubmit,
    handleTokenClear,
  };
}
