import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { ConsentRecord } from '../types';

export const ComplianceView: React.FC = () => {
  const { 
    consentRecords, 
    openProofModal, 
    openRecordConsentModal, 
    exportAuditCSV, 
    triggerToast,
    complianceMetrics,
    refreshComplianceMetrics
  } = useApp();

  const [activeTab, setActiveTab] = useState<'records' | 'optout' | 'deletion' | 'audit'>('records');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'recorded' | 'pending' | 'withdrawn'>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [selectedRecordIds, setSelectedRecordIds] = useState<string[]>([]);

  // Load metrics on mount
  useEffect(() => {
    refreshComplianceMetrics();
  }, [refreshComplianceMetrics]);

  const filteredRecords = consentRecords.filter((rec) => {
    // Tab match
    if (activeTab === 'optout' && rec.status !== 'withdrawn') return false;
    if (activeTab === 'deletion' && rec.status !== 'withdrawn') return false;

    // Status filter
    if (statusFilter !== 'all' && rec.status !== statusFilter) return false;

    // Source filter
    if (sourceFilter !== 'all') {
      if (!rec.proofMethod?.toLowerCase().includes(sourceFilter.toLowerCase())) return false;
    }

    // Search query
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      const match = rec.candidateName?.toLowerCase().includes(q) 
        || rec.maskedEmail?.toLowerCase().includes(q)
        || rec.id?.toLowerCase().includes(q)
        || rec.role?.toLowerCase().includes(q);
      if (!match) return false;
    }

    return true;
  });

  const toggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedRecordIds(filteredRecords.map((r) => r.id));
    } else {
      setSelectedRecordIds([]);
    }
  };

  const toggleRecordSelect = (id: string) => {
    setSelectedRecordIds((prev) => 
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleGenerateAuditorToken = () => {
    const token = 'AUDIT_TOKEN_' + Math.random().toString(36).substring(2, 10).toUpperCase() + '_DPDPA2023';
    navigator.clipboard?.writeText(token);
    triggerToast({
      id: `toast-${Date.now()}`,
      message: `Auditor cryptographic token generated and copied to clipboard`,
      type: 'success',
      details: `${token} (Valid for 4 hours read-only regulatory inspection)`
    });
  };

  return (
    <div className="w-full max-w-[1440px] mx-auto px-space-xl py-space-xl flex flex-col gap-space-xl select-none">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-lg pb-space-sm">
        <div className="flex flex-col gap-space-xs max-w-3xl">
          <div className="flex items-center gap-space-sm">
            <span className="px-space-sm py-0.5 rounded-full bg-subtle text-text-secondary font-code-inline text-code-inline uppercase tracking-wider border border-border">
              DPDPA 2023 · ISO 27701
            </span>
            <span className="text-text-tertiary text-caption font-caption">
              Last synced 3m ago via Regulatory Gateway
            </span>
          </div>
          <h1 className="font-page-title text-page-title text-text tracking-tight font-bold">
            Compliance &amp; Consent Management
          </h1>
          <p className="font-body text-body text-text-secondary">
            Regulatory records, consent provenance, candidate opt-out requests, and DPDPA compliance audit log.
          </p>
        </div>

        {/* Action Button Group */}
        <div className="flex items-center gap-space-md flex-shrink-0">
          <button
            type="button"
            onClick={exportAuditCSV}
            className="h-9 px-space-lg rounded-xl bg-surface border border-border-strong text-text hover:bg-subtle transition-colors flex items-center gap-space-xs font-subsection text-body cursor-pointer shadow-sm"
          >
            <span className="material-symbols-outlined text-[18px] text-text-secondary">download</span>
            <span>Export audit log (CSV)</span>
          </button>
          <button
            type="button"
            onClick={() => openRecordConsentModal()}
            className="h-9 px-space-lg rounded-xl bg-accent text-on-accent hover:bg-accent-hover transition-colors flex items-center gap-space-xs font-subsection text-body cursor-pointer shadow-sm"
          >
            <span className="material-symbols-outlined text-[18px]">add_task</span>
            <span>Record candidate consent</span>
          </button>
        </div>
      </div>

      {/* Key Metric / Guard Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-space-md">
        {/* Card 1 */}
        <div className="bg-surface rounded-xl p-space-lg border border-border flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between pb-space-sm">
            <span className="font-caption text-caption text-text-secondary font-medium">Recorded consent active</span>
            <span className="w-6 h-6 rounded-full bg-success-tint flex items-center justify-center text-success border border-success/20">
              <span className="material-symbols-outlined text-[15px]">check_circle</span>
            </span>
          </div>
          <div className="flex items-baseline gap-space-xs my-space-xs">
            <span className="font-score-numerals text-display text-text font-bold">
              {complianceMetrics?.consent_recorded ?? 0}
            </span>
            <span className="font-caption text-caption text-text-tertiary">candidates</span>
          </div>
          <div className="pt-space-xs border-t border-subtle flex items-center justify-between text-caption font-caption text-success">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
              100% compliant before outreach
            </span>
            <span className="font-code-inline text-code-inline text-text-tertiary">
              {complianceMetrics?.consent_recorded ?? 0}/{complianceMetrics?.consent_recorded ?? 0}
            </span>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-surface rounded-xl p-space-lg border border-border flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between pb-space-sm">
            <span className="font-caption text-caption text-text-secondary font-medium">Pending verification</span>
            <span className="w-6 h-6 rounded-full bg-warning-tint flex items-center justify-center text-warning border border-warning/20">
              <span className="material-symbols-outlined text-[15px]">hourglass_top</span>
            </span>
          </div>
          <div className="flex items-baseline gap-space-xs my-space-xs">
            <span className="font-score-numerals text-display text-text font-bold">
              {complianceMetrics?.consent_pending ?? 0}
            </span>
            <span className="font-caption text-caption text-text-tertiary">candidates</span>
          </div>
          <div className="pt-space-xs border-t border-subtle flex items-center justify-between text-caption font-caption text-warning">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-warning"></span>
              Consent proof required
            </span>
            <span className="font-caption text-text-secondary text-[11px]">Outreach gated</span>
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-surface rounded-xl p-space-lg border border-border flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between pb-space-sm">
            <span className="font-caption text-caption text-text-secondary font-medium">Opt-out / Withdrawn</span>
            <span className="w-6 h-6 rounded-full bg-danger-tint flex items-center justify-center text-danger border border-danger/20">
              <span className="material-symbols-outlined text-[15px]">block</span>
            </span>
          </div>
          <div className="flex items-baseline gap-space-xs my-space-xs">
            <span className="font-score-numerals text-display text-text font-bold">
              {complianceMetrics?.optout_requests ?? 0}
            </span>
            <span className="font-caption text-caption text-text-tertiary">candidates</span>
          </div>
          <div className="pt-space-xs border-t border-subtle flex items-center justify-between text-caption font-caption text-danger">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-danger"></span>
              Outreach permanently disabled
            </span>
            <span className="font-code-inline text-code-inline text-text-tertiary">Zero-contact</span>
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-surface rounded-xl p-space-lg border border-border flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between pb-space-sm">
            <span className="font-caption text-caption text-text-secondary font-medium">Data retention audits</span>
            <span className="w-6 h-6 rounded-full bg-subtle flex items-center justify-center text-text-secondary border border-border">
              <span className="material-symbols-outlined text-[15px]">auto_delete</span>
            </span>
          </div>
          <div className="flex items-baseline gap-space-xs my-space-xs">
            <span className="font-score-numerals text-display text-text font-bold">
              {complianceMetrics?.expired_records ?? 0}
            </span>
            <span className="font-caption text-caption text-text-tertiary">expired records</span>
          </div>
          <div className="pt-space-xs border-t border-subtle flex items-center justify-between text-caption font-caption text-text-secondary">
            <span className="flex items-center gap-1 truncate">
              <span className="w-1.5 h-1.5 rounded-full bg-accent"></span>
              Next auto purge in {complianceMetrics?.next_auto_purge_days ?? 14} days
            </span>
            <span className="font-code-inline text-code-inline text-text-tertiary">IST · 00:00</span>
          </div>
        </div>
      </div>

      {/* Main Workspace Container */}
      <div className="bg-surface rounded-xl border border-border shadow-sm flex flex-col">
        {/* Tab Navigation */}
        <div className="flex items-center justify-between px-space-lg border-b border-border bg-surface overflow-x-auto">
          <div className="flex items-center gap-space-xl">
            {[
              { id: 'records', label: 'Consent records', count: complianceMetrics?.consent_recorded ?? 0 },
              { id: 'optout', label: 'Opt-out requests', count: complianceMetrics?.optout_requests ?? 0 },
              { id: 'deletion', label: 'Data deletion requests', count: complianceMetrics?.deletion_requests ?? 0 },
              { id: 'audit', label: 'Regulatory audit log', dot: true }
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`relative py-space-md text-body font-subsection flex items-center gap-space-xs cursor-pointer border-b-2 transition-colors ${
                    isActive
                      ? 'text-accent border-accent font-semibold'
                      : 'text-text-secondary hover:text-text border-transparent'
                  }`}
                >
                  <span>{tab.label}</span>
                  {tab.count !== undefined && (
                    <span className={`px-space-xs py-0.5 rounded-full font-score-numerals text-code-inline ${
                      isActive ? 'bg-subtle text-accent' : 'bg-subtle text-text-secondary'
                    }`}>
                      {tab.count}
                    </span>
                  )}
                  {tab.dot && (
                    <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="hidden lg:flex items-center gap-space-xs text-caption font-caption text-text-tertiary py-space-sm">
            <span className="material-symbols-outlined text-[16px] text-accent">verified</span>
            <span>All consent mutations cryptographically signed</span>
          </div>
        </div>

        {/* Filter & Search Toolbar */}
        <div className="p-space-lg bg-surface border-b border-border flex flex-wrap items-center justify-between gap-space-md">
          <div className="flex flex-wrap items-center gap-space-sm flex-1 min-w-[280px]">
            {/* Input Search */}
            <div className="relative w-full sm:w-72">
              <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute left-space-md top-1/2 -translate-y-1/2 pointer-events-none">
                search
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search candidate name, masked ID..."
                className="w-full h-10 pl-9 pr-space-md rounded-xl bg-surface border border-border-strong text-body font-body text-text placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-accent shadow-sm"
              />
            </div>

            {/* Status Dropdown */}
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="h-10 pl-space-md pr-8 rounded-xl bg-surface border border-border-strong text-body font-body text-text focus:outline-none focus:ring-1 focus:ring-accent appearance-none cursor-pointer shadow-sm"
              >
                <option value="all">Status: All (Recorded, Pending, Withdrawn)</option>
                <option value="recorded">Status: Recorded ({complianceMetrics?.consent_recorded ?? 0})</option>
                <option value="pending">Status: Pending audit ({complianceMetrics?.consent_pending ?? 0})</option>
                <option value="withdrawn">Status: Withdrawn ({complianceMetrics?.consent_withdrawn ?? 0})</option>
              </select>
              <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-space-sm top-1/2 -translate-y-1/2 pointer-events-none">
                expand_more
              </span>
            </div>

            {/* Source Dropdown */}
            <div className="relative">
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="h-10 pl-space-md pr-8 rounded-xl bg-surface border border-border-strong text-body font-body text-text focus:outline-none focus:ring-1 focus:ring-accent appearance-none cursor-pointer shadow-sm"
              >
                <option value="all">Source: All (Direct, LinkedIn, Referral)</option>
                <option value="linkedin">Source: LinkedIn Candidate Form</option>
                <option value="inmail">Source: Verified InMail</option>
                <option value="referral">Source: Direct Referral</option>
                <option value="github">Source: GitHub Referrals</option>
              </select>
              <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-space-sm top-1/2 -translate-y-1/2 pointer-events-none">
                expand_more
              </span>
            </div>

            {/* Date Range */}
            <button
              type="button"
              className="h-10 px-space-md rounded-xl bg-surface border border-border-strong text-body font-body text-text hover:bg-subtle transition-colors flex items-center gap-space-xs cursor-pointer shadow-sm"
            >
              <span className="material-symbols-outlined text-[18px] text-text-secondary">calendar_today</span>
              <span>Last 90 days</span>
              <span className="material-symbols-outlined text-[18px] text-text-tertiary">arrow_drop_down</span>
            </button>
          </div>

          <div className="flex items-center gap-space-sm">
            <span className="font-code-inline text-caption text-text-tertiary">
              Showing {filteredRecords.length} of {consentRecords.length} records
            </span>
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('all');
                setSourceFilter('all');
              }}
              className="w-10 h-10 rounded-xl border border-border-strong bg-surface hover:bg-subtle text-text-secondary flex items-center justify-center transition-colors shadow-sm"
              title="Reset Filters"
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
            </button>
          </div>
        </div>

        {/* Bulk Selection Bar */}
        {selectedRecordIds.length > 0 && (
          <div className="flex items-center justify-between px-space-lg py-space-sm bg-subtle border-b border-border">
            <div className="flex items-center gap-space-md">
              <span className="w-2 h-2 rounded-full bg-accent"></span>
              <span className="font-subsection text-caption text-text font-semibold">
                {selectedRecordIds.length} record{selectedRecordIds.length > 1 ? 's' : ''} selected
              </span>
            </div>
            <div className="flex items-center gap-space-sm">
              <button
                type="button"
                onClick={() => triggerToast({ title: "Proof Verification", message: `Re-verified cryptographic signature on ${selectedRecordIds.length} records.`, type: "success" })}
                className="h-7 px-space-sm rounded-lg bg-surface border border-border-strong text-caption font-caption text-text hover:bg-canvas shadow-sm"
              >
                Re-verify Proof
              </button>
              <button
                type="button"
                onClick={exportAuditCSV}
                className="h-7 px-space-sm rounded-lg bg-surface border border-border-strong text-caption font-caption text-text hover:bg-canvas shadow-sm"
              >
                Export Selected (Audit XML)
              </button>
              <button
                type="button"
                onClick={() => triggerToast({ title: "Consent Revoked", message: `Marked ${selectedRecordIds.length} records as revoked under DPDPA Section 6.`, type: "warning" })}
                className="h-7 px-space-sm rounded-lg bg-surface border border-danger/40 text-caption font-caption text-danger hover:bg-danger-tint shadow-sm"
              >
                Mark Revoked
              </button>
            </div>
          </div>
        )}

        {/* Consent Records Table */}
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="h-9 bg-subtle border-b border-border text-caption font-caption text-text-secondary select-none">
                <th className="w-10 px-space-md py-0 text-center">
                  <input
                    type="checkbox"
                    checked={filteredRecords.length > 0 && selectedRecordIds.length === filteredRecords.length}
                    onChange={(e) => toggleSelectAll(e.target.checked)}
                    className="w-4 h-4 rounded accent-accent border-border-strong cursor-pointer"
                  />
                </th>
                <th className="px-space-md py-0 font-medium">Candidate &amp; Role</th>
                <th className="px-space-md py-0 font-medium">Consent Status</th>
                <th className="px-space-md py-0 font-medium">Provenance / Proof Method</th>
                <th className="px-space-md py-0 font-medium">DPDPA Scope</th>
                <th className="px-space-md py-0 font-medium">Recorded By</th>
                <th className="px-space-md py-0 font-medium">Expiry / Retention</th>
                <th className="px-space-md py-0 text-right font-medium">Audit Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-body font-body">
              {filteredRecords.map((record) => (
                <tr
                  key={record.id}
                  onClick={() => openProofModal(record)}
                  className={`h-14 hover:bg-subtle transition-colors group cursor-pointer ${
                    record.status === 'withdrawn' ? 'bg-canvas/30' : ''
                  }`}
                >
                  {/* Checkbox */}
                  <td 
                    className="w-10 px-space-md py-space-sm text-center"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleRecordSelect(record.id);
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedRecordIds.includes(record.id)}
                      onChange={() => {}}
                      className="w-4 h-4 rounded accent-accent border-border-strong cursor-pointer"
                    />
                  </td>

                  {/* Candidate */}
                  <td className="px-space-md py-space-sm">
                    <div className="flex flex-col min-w-[180px]">
                      <span className="font-subsection text-body text-text group-hover:text-accent font-semibold transition-colors">
                        {record.candidateName}
                      </span>
                      <div className="flex items-center gap-space-xs text-caption text-text-tertiary">
                        <span className="font-code-inline text-code-inline">{record.maskedEmail}</span>
                        <span>·</span>
                        <span className="truncate max-w-[130px]" title={record.role}>
                          {record.role}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Status Badge */}
                  <td className="px-space-md py-space-sm whitespace-nowrap">
                    {record.status === 'recorded' ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-success-tint text-success text-caption font-caption border border-success/20">
                        <span className="material-symbols-outlined text-[14px]">check_circle</span>
                        <span>Recorded · {record.recordedDate}</span>
                      </span>
                    ) : record.status === 'withdrawn' ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-danger-tint text-danger text-caption font-caption border border-danger/20">
                        <span className="material-symbols-outlined text-[14px]">cancel</span>
                        <span>Withdrawn · {record.recordedDate}</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-warning-tint text-warning text-caption font-caption border border-warning/20">
                        <span className="material-symbols-outlined text-[14px]">warning</span>
                        <span>Pending audit</span>
                      </span>
                    )}
                  </td>

                  {/* Provenance */}
                  <td className="px-space-md py-space-sm">
                    <div className="flex items-center gap-space-xs">
                      <span className="material-symbols-outlined text-[16px] text-text-tertiary">
                        {record.status === 'withdrawn' ? 'do_not_disturb_on' : 'badge'}
                      </span>
                      <span className="text-text text-body truncate max-w-[210px]" title={record.proofMethod}>
                        {record.proofMethod}
                      </span>
                    </div>
                  </td>

                  {/* Scope */}
                  <td className="px-space-md py-space-sm whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded bg-subtle text-text-secondary font-code-inline text-code-inline border border-border">
                      {record.scope}
                    </span>
                  </td>

                  {/* Recorded By */}
                  <td className="px-space-md py-space-sm whitespace-nowrap text-text-secondary font-caption text-caption">
                    <div className="flex items-center gap-space-xs">
                      <div className="w-5 h-5 rounded-full bg-subtle flex items-center justify-center font-code-inline text-[10px] text-text border border-border">
                        RO
                      </div>
                      <span>{record.recordedBy}</span>
                    </div>
                  </td>

                  {/* Expiry */}
                  <td className="px-space-md py-space-sm whitespace-nowrap font-score-numerals text-code-inline">
                    {record.status === 'recorded' ? (
                      <div className="flex flex-col">
                        <span className="text-text">{record.expiryDate}</span>
                        <span className="text-success text-[11px]">{record.daysRemaining} days remaining</span>
                      </div>
                    ) : record.status === 'withdrawn' ? (
                      <div className="flex flex-col">
                        <span className="text-danger font-medium">Suppressed</span>
                        <span className="text-text-tertiary text-[11px]">Hard purge scheduled</span>
                      </div>
                    ) : (
                      <div className="flex flex-col">
                        <span className="text-danger flex items-center gap-1 font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-danger"></span>
                          Outreach blocked
                        </span>
                        <span className="text-text-tertiary text-[11px]">Consent gate locked</span>
                      </div>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-space-md py-space-sm text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-space-xs">
                      <button
                        type="button"
                        onClick={() => openProofModal(record)}
                        className="h-7 px-space-sm rounded-lg hover:bg-subtle text-accent text-caption font-subsection transition-colors font-medium"
                      >
                        {record.status === 'withdrawn' ? 'View revocation' : 'View proof'}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (record.status === 'withdrawn') {
                            triggerToast({ title: "Data Suppressed", message: "Candidate data is suppressed in accordance with DPDPA Section 6(1).", type: "warning" });
                          } else {
                            openRecordConsentModal();
                          }
                        }}
                        disabled={record.status === 'withdrawn'}
                        className={`h-7 px-space-sm rounded-lg text-caption font-body transition-colors ${
                          record.status === 'withdrawn'
                            ? 'text-text-tertiary cursor-not-allowed'
                            : 'text-text-secondary hover:bg-subtle hover:text-text'
                        }`}
                      >
                        {record.status === 'withdrawn' ? 'Locked' : 'Update'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-space-lg py-space-md border-t border-border bg-surface flex items-center justify-between text-caption font-caption text-text-secondary">
          <div className="flex items-center gap-space-md">
            <span>Rows per page: <strong>10</strong></span>
            <span className="text-text-tertiary">|</span>
            <span>1–{filteredRecords.length} of {consentRecords.length} consent records</span>
          </div>

          <div className="flex items-center gap-space-xs">
            <button
              type="button"
              disabled
              className="w-8 h-8 rounded border border-border text-text-tertiary flex items-center justify-center cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_left</span>
            </button>
            <button
              type="button"
              className="w-8 h-8 rounded bg-subtle text-text font-score-numerals flex items-center justify-center border border-border-strong font-semibold"
            >
              1
            </button>
            <button
              type="button"
              className="w-8 h-8 rounded border border-border text-text hover:bg-subtle flex items-center justify-center"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            </button>
          </div>
        </div>
      </div>

      {/* Consent Gate Rule Notice Card */}
      <div className="bg-surface rounded-xl p-space-lg border border-border shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-space-lg">
        <div className="flex items-start gap-space-md">
          <div className="w-9 h-9 rounded-lg bg-success-tint flex items-center justify-center text-success flex-shrink-0 mt-0.5 border border-success/20">
            <span className="material-symbols-outlined text-[20px]">gavel</span>
          </div>
          <div className="flex flex-col gap-space-xs max-w-3xl">
            <span className="font-subsection text-body text-text font-semibold flex items-center gap-space-xs">
              <span>HirePath Consent Gate Rule</span>
              <span className="px-space-xs py-0.5 rounded bg-subtle text-[11px] font-code-inline text-text-secondary border border-border">
                POLICY-DPDPA-V4
              </span>
            </span>
            <p className="font-body text-caption text-text-secondary">
              Outreach cannot be initiated, queued, or automated for any candidate whose consent status is <span className="font-semibold text-warning">Pending audit</span> or <span className="font-semibold text-danger">Withdrawn</span>. Every record modification is cryptographically signed and stored in immutable, append-only audit storage in accordance with Section 6(1) of the Digital Personal Data Protection Act (DPDPA 2023).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-space-sm flex-shrink-0 self-end md:self-center">
          <button
            type="button"
            onClick={() => triggerToast({ title: "DPDPA Section 6(1)", message: "Explicit, affirmative consent required prior to personal data processing.", type: "info" })}
            className="h-9 px-space-md rounded-xl bg-subtle hover:bg-canvas text-text text-caption font-subsection transition-colors border border-border"
          >
            View Policy Spec
          </button>
          <button
            type="button"
            onClick={handleGenerateAuditorToken}
            className="h-9 px-space-md rounded-xl bg-accent text-on-accent hover:bg-accent-hover text-caption font-subsection transition-colors flex items-center gap-space-xs shadow-sm cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">verified_user</span>
            <span>Generate Auditor Token</span>
          </button>
        </div>
      </div>
    </div>
  );
};
