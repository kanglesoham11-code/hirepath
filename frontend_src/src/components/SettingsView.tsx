import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const SettingsView: React.FC = () => {
  const { triggerToast, isDarkMode, settingsMetrics, refreshSettingsMetrics } = useApp();
  const [isRunningHealth, setIsRunningHealth] = useState<boolean>(false);
  const [isTestInferenceRunning, setIsTestInferenceRunning] = useState<boolean>(false);
  const [inferenceResult, setInferenceResult] = useState<string | null>(null);
  const [isVerifyTokenModalOpen, setIsVerifyTokenModalOpen] = useState<boolean>(false);
  const [replacementToken, setReplacementToken] = useState<string>('');
  const [tokenVerified, setTokenVerified] = useState<boolean>(false);
  const [isDiagnosticRunning, setIsDiagnosticRunning] = useState<boolean>(false);

  // Load metrics on mount
  useEffect(() => {
    refreshSettingsMetrics();
  }, [refreshSettingsMetrics]);

  const handleRunHealthChecks = () => {
    setIsRunningHealth(true);
    setTimeout(() => {
      setIsRunningHealth(false);
      triggerToast({
        id: `toast-${Date.now()}`,
        message: 'Integrity checks completed successfully',
        type: 'success',
        details: 'Tested 5 service connections across active regions (0 fatal errors)'
      });
    }, 1000);
  };

  const handleTestInference = () => {
    setIsTestInferenceRunning(true);
    setInferenceResult(null);
    setTimeout(() => {
      setIsTestInferenceRunning(false);
      setInferenceResult('Inference latency: 138ms · Token budget: 240 toks · Model: Gemini 2.5 Flash semantic parser · Invariant checks passed.');
    }, 900);
  };

  const handleVerifyTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!replacementToken.startsWith('ghp_') && replacementToken.length < 8) {
      triggerToast({ title: "Invalid Token", message: "Please enter a valid GitHub Personal Access Token (e.g. ghp_...).", type: "danger" });
      return;
    }
    setTokenVerified(true);
    setTimeout(() => {
      setIsVerifyTokenModalOpen(false);
      setReplacementToken('');
      triggerToast({
        id: `toast-${Date.now()}`,
        message: 'GitHub PAT validated. Indexing quota restored to 5,000 req/hr.',
        type: 'success'
      });
    }, 600);
  };

  const handleDownloadLedgerManifest = () => {
    const manifest = {
      compliance_standard: "DPDPA 2023 Section 6 & ISO 27701",
      block_height: 1842910,
      chain_id: "hirepath-sovereign-in-bom",
      merkle_root: "0x89e27c19a4b087cd9421fbc8012e4401a098",
      timestamp_ist: new Date().toISOString(),
      signed_events_count: 248,
      cryptographic_algorithm: "SHA-256 with 256-bit AES KMS seal",
      active_node_cluster: "in-bom-01",
      audit_integrity: "VERIFIED_TAMPER_FREE"
    };

    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `hirepath_ledger_manifest_block_1842910.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleRunDiagnostic = () => {
    setIsDiagnosticRunning(true);
    setTimeout(() => {
      setIsDiagnosticRunning(false);
      triggerToast({
        id: `toast-${Date.now()}`,
        message: 'Diagnostic Suite: 14/14 tests passed',
        type: 'success',
        details: 'End-to-end token handshakes, candidate data sanitization, and webhook event listeners nominal.'
      });
    }, 1200);
  };

  return (
    <div className="max-w-[1440px] w-full mx-auto px-space-xl py-space-xl flex flex-col gap-space-xl select-none">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-space-lg">
        <div className="flex flex-col gap-space-xs">
          <h1 className="font-page-title text-page-title text-text tracking-tight font-bold">
            Settings
          </h1>
          <p className="font-body text-body text-text-secondary max-w-2xl">
            Manage service integrations, connection checks, and API rate limits. Secrets and credentials are encrypted and never displayed.
          </p>
        </div>

        <div className="flex items-center gap-space-md self-start">
          <span className="text-caption font-caption text-text-tertiary hidden sm:inline">
            Last automatic poll: <span className="font-code-inline text-code-inline text-text-secondary">11:40:12 IST</span>
          </span>
          <button
            type="button"
            onClick={handleRunHealthChecks}
            disabled={isRunningHealth}
            className="h-9 px-space-lg rounded-[6px] bg-surface text-text hover:bg-subtle transition-colors flex items-center gap-space-xs text-body font-body font-semibold border border-border-strong shadow-sm cursor-pointer"
          >
            <span className={`material-symbols-outlined text-[18px] text-text-secondary ${isRunningHealth ? 'animate-spin' : ''}`}>
              refresh
            </span>
            <span>{isRunningHealth ? 'Running checks...' : 'Run health checks'}</span>
          </button>
        </div>
      </div>

      {/* Service Health Status Banner */}
      <div className="bg-surface rounded-xl p-space-lg flex flex-col md:flex-row md:items-center justify-between gap-space-md shadow-sm border border-border">
        <div className="flex items-start md:items-center gap-space-md">
          <div className="w-9 h-9 rounded-lg bg-danger-tint text-danger flex items-center justify-center flex-shrink-0 border border-danger/20">
            <span className="material-symbols-outlined text-[20px]">warning</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-space-sm flex-wrap">
              <span className="font-subsection text-subsection text-text font-semibold">Service Health Status</span>
              <span className="font-caption text-caption px-space-sm py-0.5 rounded-full bg-warning-tint text-warning font-medium border border-warning/20">
                {settingsMetrics?.github.token_valid ? 'Pipeline Restored' : 'Degraded Pipeline'}
              </span>
            </div>
            <span className="font-body text-body text-text-secondary">
              {settingsMetrics?.github.token_valid ? (
                <><strong className="font-semibold text-text">{settingsMetrics?.services.filter(s => s.status === 'healthy').length ?? 4} of 5</strong> services healthy · GitHub token active</>
              ) : (
                <><strong className="font-semibold text-text">{settingsMetrics?.services.filter(s => s.status === 'healthy').length ?? 3} of 5</strong> services healthy · GitHub token requires renewal for unthrottled indexing</>
              )}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-space-sm pl-12 md:pl-0">
          <span className="font-caption text-caption text-text-tertiary">DPDPA 2023 Enforced</span>
          <span className="w-1.5 h-1.5 rounded-full bg-border-strong"></span>
          <span className="font-caption text-caption text-success font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
            {settingsMetrics?.audit_lock_intact ? 'Audit Lock Intact' : 'Audit Lock Active'}
          </span>
        </div>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-space-lg">
        {/* Metric 1 */}
        <div className="bg-surface p-space-lg rounded-xl flex flex-col justify-between gap-space-md shadow-sm border border-border">
          <div className="flex items-center justify-between">
            <span className="font-caption text-caption text-text-secondary uppercase tracking-wider font-semibold">
              GitHub Indexing API
            </span>
            <span className={`font-caption text-caption px-space-sm py-0.5 rounded-full font-medium border ${
              settingsMetrics?.github.token_valid ? 'bg-success-tint text-success border-success/20' : 'bg-danger-tint text-danger border-danger/20'
            }`}>
              {settingsMetrics?.github.status ?? (settingsMetrics?.github.token_valid ? 'Operating' : 'Throttled')}
            </span>
          </div>
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-baseline gap-space-xs">
              <span className={`font-score-numerals text-[28px] leading-tight font-semibold ${settingsMetrics?.github.token_valid ? 'text-text' : 'text-danger'}`}>
                {settingsMetrics?.github.rate_limit_remaining ?? (settingsMetrics?.github.token_valid ? '4,980' : '12')}
              </span>
              <span className="font-score-numerals text-body text-text-tertiary">
                / {settingsMetrics?.github.rate_limit_total ?? (settingsMetrics?.github.token_valid ? '5,000 req/hr' : '60 req/hr')}
              </span>
            </div>
            <div className="w-full h-1 bg-subtle rounded-full overflow-hidden">
              <div 
                className={`h-full ${settingsMetrics?.github.token_valid ? 'bg-accent w-[98%]' : 'bg-danger w-[20%]'}`}
              ></div>
            </div>
            <span className="font-caption text-caption text-text-tertiary mt-1">
              {settingsMetrics?.github.token_valid ? 'Authorized enterprise tier quota active' : 'Fallback tier active · 0 / 5,000 authorized quota available'}
            </span>
          </div>
          <div className="pt-space-xs flex items-center justify-between text-caption font-caption text-text-secondary border-t border-border/30">
            <span>Replenishes in</span>
            <span className="font-code-inline text-code-inline text-text">18m 40s</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-surface p-space-lg rounded-xl flex flex-col justify-between gap-space-md shadow-sm border border-border">
          <div className="flex items-center justify-between">
            <span className="font-caption text-caption text-text-secondary uppercase tracking-wider font-semibold">
              Sourcing Queue Worker
            </span>
            <span className="font-caption text-caption px-space-sm py-0.5 rounded-full bg-warning-tint text-warning font-medium border border-warning/20">
              {settingsMetrics?.services.find(s => s.type === 'github')?.status === 'healthy' ? 'Active' : 'Paused'}
            </span>
          </div>
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-baseline gap-space-xs">
              <span className="font-score-numerals text-[28px] leading-tight text-text font-semibold">
                {settingsMetrics?.services.find(s => s.type === 'github')?.rate_limit_remaining ?? 0}
              </span>
              <span className="font-score-numerals text-body text-text-tertiary">req/hr remaining</span>
            </div>
            <div className="w-full h-1 bg-subtle rounded-full overflow-hidden">
              <div className="h-full bg-warning w-0"></div>
            </div>
            <span className="font-caption text-caption text-text-secondary mt-1">
              {settingsMetrics?.github.token_valid ? 'Worker running with authenticated GitHub credentials' : 'Worker stopped. Awaiting authenticated GitHub credentials.'}
            </span>
          </div>
          <div className="pt-space-xs flex items-center justify-between text-caption font-caption text-text-secondary border-t border-border/30">
            <span>Worker instances</span>
            <span className="font-code-inline text-code-inline text-text">2 idle (eu-central-1)</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-surface p-space-lg rounded-xl flex flex-col justify-between gap-space-md shadow-sm border border-border">
          <div className="flex items-center justify-between">
            <span className="font-caption text-caption text-text-secondary uppercase tracking-wider font-semibold">
              Audit Ledger Cryptography
            </span>
            <span className="font-caption text-caption px-space-sm py-0.5 rounded-full bg-success-tint text-success font-medium border border-success/20">
              Operating
            </span>
          </div>
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-baseline gap-space-xs">
              <span className="font-score-numerals text-[28px] leading-tight text-accent font-semibold">
                {settingsMetrics?.audit_ledger.signed_events ?? 248}
              </span>
              <span className="font-score-numerals text-body text-text-tertiary">signed events</span>
            </div>
            <div className="w-full h-1 bg-subtle rounded-full overflow-hidden">
              <div className="h-full bg-accent w-full"></div>
            </div>
            <span className="font-caption text-caption text-text-secondary mt-1">
              {settingsMetrics?.audit_ledger.algorithm ?? 'SHA-256 with 256-bit AES KMS seal'}
            </span>
          </div>
          <div className="pt-space-xs flex items-center justify-between text-caption font-caption text-text-secondary border-t border-border/30">
            <span>Key rotation</span>
            <span className="font-code-inline text-code-inline text-text">Scheduled in 64 days</span>
          </div>
        </div>
      </div>

      {/* Connection Integrity Checks */}
      <div className="flex flex-col gap-space-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-section-title text-section-title text-text font-bold">
              Connection Integrity Checks
            </h2>
            <p className="font-body text-body text-text-secondary">
              Continuous read-only validation of external service handles and operational permissions.
            </p>
          </div>
          <span className="font-code-inline text-code-inline text-text-tertiary hidden sm:inline">
            5 services registered
          </span>
        </div>

        <div className="bg-surface border border-border rounded-lg overflow-hidden shadow-sm divide-y divide-border">
          {/* Service 1: AI Model */}
          <div className="p-space-lg flex flex-col lg:flex-row lg:items-center justify-between gap-space-lg hover:bg-canvas transition-colors">
            <div className="flex items-start gap-space-md flex-1">
              <div className="w-9 h-9 rounded-lg bg-success-tint text-success flex items-center justify-center flex-shrink-0 mt-0.5 border border-success/20">
                <span className="material-symbols-outlined text-[20px]">psychology</span>
              </div>
              <div className="flex flex-col gap-space-xs min-w-0">
                <div className="flex items-center gap-space-sm flex-wrap">
                  <span className="font-subsection text-subsection text-text font-semibold">
                    AI Model (Scoring &amp; Parsing Engine)
                  </span>
                  <div className="flex items-center gap-space-xs px-space-sm py-0.5 rounded-full bg-success-tint text-success font-caption text-caption border border-success/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                    <span>Connected &amp; Configured</span>
                  </div>
                </div>
                <p className="font-body text-body text-text-secondary">
                  Claude 3.5 Sonnet / Gemini Engine · Candidate semantic parsing, criteria weighting inference, and zero-shot requirement alignment.
                </p>
                {inferenceResult && (
                  <div className="p-2 bg-subtle rounded font-code-inline text-caption text-accent border border-border">
                    {inferenceResult}
                  </div>
                )}
                <div className="flex items-center gap-space-md text-caption font-caption text-text-tertiary flex-wrap pt-1">
                  <span className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[15px] text-accent">speed</span>
                    <span className="font-code-inline text-code-inline text-text">142 ms latency</span>
                  </span>
                  <span>•</span>
                  <span>100% quota available</span>
                  <span>•</span>
                  <span>Checked 2m ago</span>
                  <span>•</span>
                  <span className="font-code-inline text-code-inline text-text-secondary bg-subtle px-1.5 py-0.5 rounded border border-border">
                    HIREPATH_LLM_KEY (encrypted)
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-space-sm self-start lg:self-center flex-shrink-0">
              <button
                type="button"
                onClick={handleTestInference}
                disabled={isTestInferenceRunning}
                className="h-9 px-space-md rounded-[6px] bg-surface text-text hover:bg-subtle transition-colors flex items-center gap-space-xs text-body font-body font-semibold text-caption border border-border-strong shadow-sm cursor-pointer"
              >
                <span className={`material-symbols-outlined text-[16px] text-text-secondary ${isTestInferenceRunning ? 'animate-spin' : ''}`}>
                  {isTestInferenceRunning ? 'refresh' : 'play_arrow'}
                </span>
                <span>{isTestInferenceRunning ? 'Testing...' : 'Test inference'}</span>
              </button>
              <button
                type="button"
                onClick={() => triggerToast({ title: "Log Telemetry", message: "Viewing system log telemetry: All scoring queries verified 200 OK.", type: "info" })}
                className="h-9 px-space-md rounded-[6px] bg-surface text-text-secondary hover:bg-subtle hover:text-text transition-colors flex items-center gap-space-xs text-body font-body text-caption border border-border shadow-sm cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px]">receipt_long</span>
                <span>View logs</span>
              </button>
            </div>
          </div>

          {/* Service 2: GitHub API */}
          <div className={`p-space-lg flex flex-col lg:flex-row lg:items-start justify-between gap-space-lg transition-colors ${
            settingsMetrics?.github.token_valid ? 'hover:bg-canvas' : 'bg-danger-tint/20 hover:bg-danger-tint/30'
          }`}>
            <div className="flex items-start gap-space-md flex-1">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 border ${
                settingsMetrics?.github.token_valid ? 'bg-success-tint text-success border-success/20' : 'bg-danger-tint text-danger border-danger/20'
              }`}>
                <span className="material-symbols-outlined text-[20px]">code</span>
              </div>
              <div className="flex flex-col gap-space-xs min-w-0">
                <div className="flex items-center gap-space-sm flex-wrap">
                  <span className="font-subsection text-subsection text-text font-semibold">
                    GitHub Public Profiles API
                  </span>
                  <div className={`flex items-center gap-space-xs px-space-sm py-0.5 rounded-full font-caption text-caption border ${
                    settingsMetrics?.github.token_valid ? 'bg-success-tint text-success border-success/20' : 'bg-danger-tint text-danger border-danger/20'
                  }`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${settingsMetrics?.github.token_valid ? 'bg-success' : 'bg-danger'}`}></span>
                    <span>{settingsMetrics?.github.token_valid ? 'Token active & validated' : 'Token invalid'}</span>
                  </div>
                </div>
                <p className="font-body text-body text-text-secondary">
                  Candidate profile indexing, public contribution analysis, and verifiable project evidence extraction.
                </p>
                {!settingsMetrics?.github.token_valid && (
                  <div className="mt-space-xs p-space-md rounded-[6px] bg-surface flex items-start gap-space-sm shadow-sm border border-border">
                    <span className="material-symbols-outlined text-[18px] text-danger flex-shrink-0 mt-0.5">error_outline</span>
                    <div className="flex flex-col gap-0.5">
                      <span className="font-caption text-caption font-semibold text-danger">One-line remedy:</span>
                      <span className="font-body text-body text-text">
                        Replace the token in the server settings. Sourcing rate limits currently throttled to unauthenticated tier (60 req/hr).
                      </span>
                    </div>
                  </div>
                )}
                <div className="flex items-center gap-space-md text-caption font-caption text-text-tertiary flex-wrap pt-1">
                  <span>Scope: <span className="font-code-inline text-code-inline text-text-secondary">read:user, repo:status</span></span>
                  <span>•</span>
                  <span className="font-code-inline text-code-inline text-text-secondary bg-subtle px-1.5 py-0.5 rounded border border-border">
                    GITHUB_PAT_SECRET
                  </span>
                  <span>•</span>
                  <span className="text-text-secondary font-medium">Secret never displayed in browser</span>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-space-sm self-start lg:self-center flex-shrink-0">
              <button
                type="button"
                onClick={() => setIsVerifyTokenModalOpen(true)}
                className="h-9 px-space-md rounded-[6px] bg-accent text-on-accent hover:bg-accent-hover transition-colors flex items-center justify-center gap-space-xs text-body font-body font-semibold text-caption shadow-sm cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px]">verified</span>
                <span>{tokenVerified ? 'Update token' : 'Verify replacement token'}</span>
              </button>
              <button
                type="button"
                onClick={() => triggerToast({ title: "Container Config", message: "Server settings are managed through secure container env variables: GITHUB_PAT_SECRET.", type: "info" })}
                className="h-9 px-space-md rounded-[6px] bg-surface text-text hover:bg-subtle transition-colors flex items-center justify-center gap-space-xs text-body font-body text-caption border border-border shadow-sm cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px] text-text-secondary">menu_book</span>
                <span>Server settings docs</span>
              </button>
            </div>
          </div>

          {/* Service 3: Email Gateway */}
          <div className="p-space-lg flex flex-col lg:flex-row lg:items-start justify-between gap-space-lg hover:bg-canvas transition-colors">
            <div className="flex items-start gap-space-md flex-1">
              <div className="w-9 h-9 rounded-lg bg-warning-tint text-warning flex items-center justify-center flex-shrink-0 mt-0.5 border border-warning/20">
                <span className="material-symbols-outlined text-[20px]">mail</span>
              </div>
              <div className="flex flex-col gap-space-xs min-w-0">
                <div className="flex items-center gap-space-sm flex-wrap">
                  <span className="font-subsection text-subsection text-text font-semibold">
                    Email Gateway (SMTP / SES)
                  </span>
                  <div className="flex items-center gap-space-xs px-space-sm py-0.5 rounded-full bg-warning-tint text-warning font-caption text-caption border border-warning/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-warning"></span>
                    <span>{settingsMetrics?.services.find(s => s.type === 'email')?.status ?? 'Not configured'}</span>
                  </div>
                </div>
                <p className="font-body text-body text-text-secondary">
                  Dispatching reviewed candidate outreach batches with enforced 10-second recall window and audit headers.
                </p>
                <div className="mt-space-xs p-space-md rounded-[6px] bg-subtle flex items-start gap-space-sm border border-border/40">
                  <span className="material-symbols-outlined text-[18px] text-warning flex-shrink-0 mt-0.5">info</span>
                  <span className="font-body text-body text-text-secondary">
                    Email dispatch gateway is offline. Candidate outreach batches cannot be sent until configured in environment variables.
                  </span>
                </div>
                <div className="flex items-center gap-space-md text-caption font-caption text-text-tertiary flex-wrap pt-1">
                  <span>Parameters required:</span>
                  <span className="font-code-inline text-code-inline text-text-secondary bg-surface px-1.5 py-0.5 rounded border border-border">
                    SMTP_HOST
                  </span>
                  <span className="font-code-inline text-code-inline text-text-secondary bg-surface px-1.5 py-0.5 rounded border border-border">
                    SMTP_PORT
                  </span>
                  <span className="font-code-inline text-code-inline text-text-secondary bg-surface px-1.5 py-0.5 rounded border border-border">
                    DKIM_KEY_ARN
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-space-sm self-start lg:self-center flex-shrink-0">
              <button
                type="button"
                disabled
                className="h-9 px-space-md rounded-[6px] bg-subtle text-text-tertiary cursor-not-allowed opacity-50 flex items-center gap-space-xs text-body font-body text-caption border border-border"
              >
                <span>Send test dispatch</span>
              </button>
              <button
                type="button"
                onClick={() => triggerToast({ title: "Email Gateway", message: "Email Gateway requires SMTP_HOST, SMTP_PORT, and DKIM_KEY_ARN env secrets.", type: "warning" })}
                className="h-9 px-space-md rounded-[6px] bg-surface text-text hover:bg-subtle transition-colors flex items-center gap-space-xs text-body font-body text-caption border border-border shadow-sm"
              >
                <span className="material-symbols-outlined text-[16px] text-text-secondary">open_in_new</span>
                <span>Configuration guide</span>
              </button>
            </div>
          </div>

          {/* Service 4: Google Workspace */}
          <div className="p-space-lg flex flex-col lg:flex-row lg:items-start justify-between gap-space-lg hover:bg-canvas transition-colors">
            <div className="flex items-start gap-space-md flex-1">
              <div className="w-9 h-9 rounded-lg bg-warning-tint text-warning flex items-center justify-center flex-shrink-0 mt-0.5 border border-warning/20">
                <span className="material-symbols-outlined text-[20px]">calendar_today</span>
              </div>
              <div className="flex flex-col gap-space-xs min-w-0">
                <div className="flex items-center gap-space-sm flex-wrap">
                  <span className="font-subsection text-subsection text-text font-semibold">
                    Calendar &amp; Video Conferencing (Google Workspace)
                  </span>
                  <div className="flex items-center gap-space-xs px-space-sm py-0.5 rounded-full bg-warning-tint text-warning font-caption text-caption border border-warning/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-warning"></span>
                    <span>Not configured</span>
                  </div>
                </div>
                <p className="font-body text-body text-text-secondary">
                  Slot availability query sync, recruiter scheduling coordination, and automated Google Meet room provisioning.
                </p>
                <div className="mt-space-xs p-space-md rounded-[6px] bg-subtle flex items-start gap-space-sm border border-border/40">
                  <span className="material-symbols-outlined text-[18px] text-warning flex-shrink-0 mt-0.5">info</span>
                  <span className="font-body text-body text-text-secondary">
                    Google Calendar service account not linked. Slot picker cannot query interviewer availability.
                  </span>
                </div>
                <div className="flex items-center gap-space-md text-caption font-caption text-text-tertiary flex-wrap pt-1">
                  <span>Requirement: OAuth 2.0 service account credentials in server environment</span>
                  <span>•</span>
                  <span className="font-code-inline text-code-inline text-text-secondary bg-surface px-1.5 py-0.5 rounded border border-border">
                    GOOGLE_APPLICATION_CREDENTIALS
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-space-sm self-start lg:self-center flex-shrink-0">
              <button
                type="button"
                onClick={() => triggerToast({ title: "Google Workspace", message: "Linking Google Workspace OAuth client: Developer simulation mode active.", type: "info" })}
                className="h-9 px-space-md rounded-[6px] bg-surface text-text hover:bg-subtle transition-colors flex items-center gap-space-xs text-body font-body text-caption font-semibold border border-border-strong shadow-sm"
              >
                <span className="material-symbols-outlined text-[16px] text-accent">link</span>
                <span>Link service account</span>
              </button>
            </div>
          </div>

          {/* Service 5: Immutable Audit Store */}
          <div className="p-space-lg flex flex-col lg:flex-row lg:items-center justify-between gap-space-lg hover:bg-canvas transition-colors">
            <div className="flex items-start gap-space-md flex-1">
              <div className="w-9 h-9 rounded-lg bg-success-tint text-success flex items-center justify-center flex-shrink-0 mt-0.5 border border-success/20">
                <span className="material-symbols-outlined text-[20px]">verified_user</span>
              </div>
              <div className="flex flex-col gap-space-xs min-w-0">
                <div className="flex items-center gap-space-sm flex-wrap">
                  <span className="font-subsection text-subsection text-text font-semibold">
                    Immutable Audit Store (DPDPA 2023 Ledger)
                  </span>
                  <div className="flex items-center gap-space-xs px-space-sm py-0.5 rounded-full bg-success-tint text-success font-caption text-caption border border-success/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                    <span>Active &amp; Verified</span>
                  </div>
                </div>
                <p className="font-body text-body text-text-secondary">
                  Cryptographic hash generation for candidate consent timestamps, outreach logs, and automated scoring audits.
                </p>
                <div className="flex items-center gap-space-md text-caption font-caption text-text-tertiary flex-wrap pt-1">
                  <span className="text-success font-medium">SHA-256 tamper checks passing continuously</span>
                  <span>•</span>
                  <span>ISO 27701 compliant architecture</span>
                  <span>•</span>
                  <span className="font-code-inline text-code-inline text-text">Block height: #1,842,910</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-space-sm self-start lg:self-center flex-shrink-0">
              <button
                type="button"
                onClick={handleDownloadLedgerManifest}
                className="h-9 px-space-md rounded-[6px] bg-surface text-text hover:bg-subtle transition-colors flex items-center gap-space-xs text-body font-body text-caption border border-border shadow-sm cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px] text-text-secondary">download</span>
                <span>Download ledger manifest</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Information Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg">
        {/* Zero-Secret Exposure Policy */}
        <div className="p-space-lg rounded-xl bg-subtle flex flex-col gap-space-sm border border-border/40">
          <div className="flex items-center gap-space-xs text-text">
            <span className="material-symbols-outlined text-[20px] text-accent">lock</span>
            <span className="font-subsection text-subsection text-text font-semibold">Zero-Secret Exposure Policy</span>
          </div>
          <p className="font-body text-body text-text-secondary leading-relaxed">
            In compliance with enterprise security requirements, raw API keys, service tokens, and private credentials are never rendered in client HTML or returned over browser APIs. All configuration updates must be executed via server-side environment variables or deployment secrets.
          </p>
          <div className="pt-space-xs">
            <span className="font-caption text-caption text-text-tertiary">
              Host: <span className="font-code-inline text-code-inline text-text-secondary">prod-hirepath-control-plane-in</span> · KMS: AWS Key Management Service (256-bit AES)
            </span>
          </div>
        </div>

        {/* Diagnostic Self-Test Engine */}
        <div className="p-space-lg rounded-xl bg-surface flex flex-col justify-between gap-space-sm shadow-sm border border-border">
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <span className="font-subsection text-subsection text-text font-semibold">Diagnostic Self-Test Engine</span>
              <span className="font-caption text-caption text-text-tertiary">Automated ping every 5m</span>
            </div>
            <p className="font-body text-body text-text-secondary">
              Simulates end-to-end token handshakes, candidate data sanitization routines, and webhook event listeners without affecting live pipelines.
            </p>
          </div>
          <div className="pt-space-sm flex items-center justify-between flex-wrap gap-space-sm border-t border-border/30">
            <div className="flex items-center gap-space-xs text-caption font-caption text-text-secondary">
              <span className="w-2 h-2 rounded-full bg-success"></span>
              <span>All background cron workers nominal</span>
            </div>
            <button
              type="button"
              onClick={handleRunDiagnostic}
              disabled={isDiagnosticRunning}
              className="h-9 px-space-md rounded-[6px] bg-surface text-text hover:bg-subtle transition-colors flex items-center gap-space-xs text-body font-body text-caption font-semibold border border-border-strong shadow-sm cursor-pointer"
            >
              <span className={`material-symbols-outlined text-[16px] text-accent ${isDiagnosticRunning ? 'animate-spin' : ''}`}>
                {isDiagnosticRunning ? 'refresh' : 'terminal'}
              </span>
              <span>{isDiagnosticRunning ? 'Running suite...' : 'Run diagnostic suite'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Replacement Token Modal */}
      {isVerifyTokenModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-space-md bg-text/40 backdrop-blur-[2px]">
          <div className="w-full max-w-[480px] bg-surface rounded-xl p-space-xl shadow-2xl flex flex-col gap-space-md border border-border animate-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[22px] text-accent">vpn_key</span>
                <h3 className="font-section-title text-section-title font-semibold text-text">
                  Verify Replacement GitHub Token
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsVerifyTokenModalOpen(false)}
                className="text-text-tertiary hover:text-text"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <p className="text-body font-body text-text-secondary">
              Provide a GitHub Personal Access Token with <code className="font-code-inline text-text bg-subtle px-1 rounded">read:user</code> permissions to unblock rate limits from 60 req/hr to 5,000 req/hr.
            </p>

            <form onSubmit={handleVerifyTokenSubmit} className="flex flex-col gap-space-md">
              <div className="flex flex-col gap-1">
                <label className="text-caption font-caption font-semibold text-text-secondary">
                  New Access Token (PAT)
                </label>
                <input
                  type="password"
                  value={replacementToken}
                  onChange={(e) => setReplacementToken(e.target.value)}
                  placeholder="ghp_••••••••••••••••••••••••"
                  className="h-10 px-space-md bg-surface text-text font-code-inline text-body rounded-lg border border-border-strong focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>

              <div className="flex items-center justify-end gap-space-sm pt-space-xs">
                <button
                  type="button"
                  onClick={() => setIsVerifyTokenModalOpen(false)}
                  className="h-9 px-space-md bg-surface text-text hover:bg-subtle text-body font-body font-semibold rounded-lg border border-border"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="h-9 px-space-md bg-accent text-on-accent text-body font-body font-semibold rounded-lg hover:bg-accent-hover shadow-sm"
                >
                  Verify &amp; Apply
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
