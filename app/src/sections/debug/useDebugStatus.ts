import { useEffect, useState } from 'react';

import { DEBUG_API_URL } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';
import { clearAccessReloadGuard, reloadOnceForAccess, setAdminHint } from 'src/utils/adminAuth';

export interface SpecStatus {
  id: string;
  title: string;
  updated: string | null;
  avg_score: number | null;
  altair: number | null;
  bokeh: number | null;
  chartjs: number | null;
  d3: number | null;
  echarts: number | null;
  ggplot2: number | null;
  highcharts: number | null;
  letsplot: number | null;
  makie: number | null;
  matplotlib: number | null;
  muix: number | null;
  plotly: number | null;
  plotnine: number | null;
  pygal: number | null;
  seaborn: number | null;
}

export interface LibraryStats {
  id: string;
  name: string;
  impl_count: number;
  avg_score: number | null;
  min_score: number | null;
  max_score: number | null;
}

export interface ProblemSpec {
  id: string;
  title: string;
  issue: string;
  value: string | null;
}

export interface SystemHealth {
  database_connected: boolean;
  api_response_time_ms: number;
  timestamp: string;
  total_specs_in_db: number;
  total_impls_in_db: number;
}

export interface DailyImplPoint {
  date: string;
  impls_updated: number;
}

export interface RecentActivity {
  spec_id: string;
  spec_title: string;
  library_id: string;
  language_id: string;
  quality_score: number | null;
  generated_by: string | null;
  updated: string;
}

export interface WeaknessCount {
  text: string;
  count: number;
}

export interface DebugStatus {
  total_specs: number;
  total_implementations: number;
  coverage_percent: number;
  library_stats: LibraryStats[];
  low_score_specs: ProblemSpec[];
  oldest_specs: ProblemSpec[];
  missing_preview_specs: ProblemSpec[];
  missing_tags_specs: ProblemSpec[];
  daily_impls: DailyImplPoint[];
  recent_activity: RecentActivity[];
  common_weaknesses: WeaknessCount[];
  system: SystemHealth;
  specs: SpecStatus[];
}

export function useDebugStatus(
  adminToken: string,
  reloadCounter: number,
  setAuthRequired: (v: boolean) => void
) {
  const [data, setData] = useState<DebugStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prevFetchKey, setPrevFetchKey] = useState({ adminToken, reloadCounter });

  if (prevFetchKey.adminToken !== adminToken || prevFetchKey.reloadCounter !== reloadCounter) {
    setPrevFetchKey({ adminToken, reloadCounter });
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    fetchWithAuth(`${DEBUG_API_URL}/debug/status`, adminToken)
      .then(async r => {
        clearAccessReloadGuard();
        if (r.status === 401 || r.status === 403 || r.status === 503) {
          setAdminHint(false);
          setAuthRequired(true);
          if (r.status === 403) {
            const body = await r.json().catch(() => ({}));
            throw new Error(body?.message || 'this account is not authorized for /debug');
          }
          throw new Error(
            r.status === 503 ? 'admin auth not configured on server' : 'admin token required'
          );
        }
        if (!r.ok) throw new Error(`${r.status}`);
        setAdminHint(true);
        setAuthRequired(false);
        return r.json();
      })
      .then(setData)
      .catch(e => {
        if (e instanceof TypeError && reloadOnceForAccess()) return;
        setError(e.message || 'failed to load');
      })
      .finally(() => setLoading(false));
  }, [adminToken, reloadCounter, setAuthRequired]);

  return { data, loading, error };
}
