import { useEffect } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { useAnalytics } from 'src/hooks';
import { AgentCasesSection } from 'src/sections/debug/AgentCasesSection';
import { AgentUsageSection } from 'src/sections/debug/AgentUsageSection';
import { DebugAuthView } from 'src/sections/debug/DebugAuthView';
import { DebugFeedbackSection } from 'src/sections/debug/DebugFeedbackSection';
import { DebugOverviewSection } from 'src/sections/debug/DebugOverviewSection';
import { DebugSpecsSection } from 'src/sections/debug/DebugSpecsSection';
import { SystemHealthRow } from 'src/sections/debug/SystemHealthRow';
import { useDebugAuth } from 'src/sections/debug/useDebugAuth';
import { useDebugFeedback } from 'src/sections/debug/useDebugFeedback';
import { useDebugPing } from 'src/sections/debug/useDebugPing';
import { useDebugStatus } from 'src/sections/debug/useDebugStatus';
import { useSpecFilters } from 'src/sections/debug/useSpecFilters';
import { colors, semanticColors, typography } from 'src/theme';

export function DebugPage() {
  const { trackPageview } = useAnalytics();
  useEffect(() => {
    trackPageview('/debug');
  }, [trackPageview]);

  const {
    authRequired,
    setAuthRequired,
    adminToken,
    tokenInput,
    setTokenInput,
    reloadCounter,
    handleTokenSubmit,
    handleTokenClear,
  } = useDebugAuth();

  const { data, loading, error } = useDebugStatus(adminToken, reloadCounter, setAuthRequired);
  const { pings } = useDebugPing(adminToken, authRequired);

  const {
    topThumbsUp,
    topThumbsDown,
    feedbackMessages,
    feedbackStatusFilter,
    setFeedbackStatusFilter,
    updateFeedbackStatus,
  } = useDebugFeedback(adminToken, authRequired, reloadCounter);

  const {
    sortKey,
    sortDir,
    searchText,
    setSearchText,
    showIncomplete,
    setShowIncomplete,
    showLowScores,
    setShowLowScores,
    missingLibrary,
    setMissingLibrary,
    filteredSpecs,
    handleSort,
  } = useSpecFilters(data?.specs || []);

  if (authRequired) {
    return (
      <DebugAuthView
        error={error}
        tokenInput={tokenInput}
        setTokenInput={setTokenInput}
        handleTokenSubmit={handleTokenSubmit}
        adminToken={adminToken}
        handleTokenClear={handleTokenClear}
      />
    );
  }

  if (loading) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <title>debug | anyplot.ai</title>
        <Typography sx={{ fontFamily: typography.fontFamily, color: semanticColors.mutedText }}>
          loading debug data...
        </Typography>
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <title>debug | anyplot.ai</title>
        <Typography sx={{ fontFamily: typography.fontFamily, color: colors.error }}>
          failed to load{error ? `: ${error}` : ''}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ pt: { xs: 2, md: 3 }, pb: 4 }}>
      <title>debug | anyplot.ai</title>
      {/* Header */}
      <SectionHeader prompt="❯" title={<em>debug</em>} />

      {/* System health row */}
      <SystemHealthRow pings={pings} system={data.system} />

      {/* Dashboard KPI + Problem Areas Overview */}
      <DebugOverviewSection data={data} />

      {/* Feedback: top pages + messages with triage (issue #5662) */}
      <DebugFeedbackSection
        topThumbsUp={topThumbsUp}
        topThumbsDown={topThumbsDown}
        feedbackMessages={feedbackMessages}
        feedbackStatusFilter={feedbackStatusFilter}
        setFeedbackStatusFilter={setFeedbackStatusFilter}
        updateFeedbackStatus={updateFeedbackStatus}
      />

      {/* Agent cases: the triage of the agent chat's quick feedback */}
      {/* Agent usage: the agent chat's content-free telemetry, 7 or 30 days */}
      <AgentUsageSection token={adminToken} reloadCounter={reloadCounter} />

      <AgentCasesSection token={adminToken} reloadCounter={reloadCounter} />

      {/* Spec Matrix */}
      <DebugSpecsSection
        filteredSpecs={filteredSpecs}
        searchText={searchText}
        setSearchText={setSearchText}
        showIncomplete={showIncomplete}
        setShowIncomplete={setShowIncomplete}
        showLowScores={showLowScores}
        setShowLowScores={setShowLowScores}
        missingLibrary={missingLibrary}
        setMissingLibrary={setMissingLibrary}
        sortKey={sortKey}
        sortDir={sortDir}
        handleSort={handleSort}
      />
    </Box>
  );
}
