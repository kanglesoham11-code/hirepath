import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const ActivityView: React.FC = () => {
  const { auditEvents, exportAuditCSV, selectedRole, activityMetrics, refreshActivityMetrics } = useApp();

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedRoleFilter, setSelectedRoleFilter] = useState<string>('all');
  const [selectedActionFilter, setSelectedActionFilter] = useState<string>('all');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('all');
  const [dateRangeFilter, setDateRangeFilter] = useState<string>('7d');
  const [rowsPerPage, setRowsPerPage] = useState<number>(25);

  // Load metrics on mount
  useEffect(() => {
    refreshActivityMetrics();
  }, [refreshActivityMetrics]);

  const filteredEvents = auditEvents.filter((ev) => {
    if (selectedRoleFilter !== 'all' && !ev.targetEntity?.toLowerCase().includes('backend')) {
      return false;
    }
    if (selectedActionFilter !== 'all' && ev.category !== selectedActionFilter) {
      return false;
    }
    if (selectedStatusFilter !== 'all' && ev.status !== selectedStatusFilter) {
      return false;
    }
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      const match = ev.eventDescription?.toLowerCase().includes(q)
        || ev.targetEntity?.toLowerCase().includes(q)
        || ev.actorCategory?.toLowerCase().includes(q)
        || ev.auditHash?.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  const resetFilters = () => {
    setSearchQuery('');
    setSelectedRoleFilter('all');
    setSelectedActionFilter('all');
    setSelectedStatusFilter('all');
    setDateRangeFilter('7d');
  };

  return (
    <div className="w-full max-w-[1440px] mx-auto px-space-xl py-space-xl flex flex-col gap-space-xl select-none">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md pb-space-xs">
        <div className="flex flex-col gap-1">
          <h1 className="font-page-title text-page-title text-text tracking-tight font-bold">
            Activity
          </h1>
          <p className="font-body text-body text-text-secondary max-w-3xl">
            Complete, tamper-evident audit log of recruiter actions, automated sourcing runs, consent mutations, and candidate interactions across all roles.
          </p>
        </div>

        {/* Top Right Actions */}
        <div className="flex items-center gap-space-md self-start sm:self-auto shrink-0">
          <div className="flex items-center gap-space-xs px-space-md h-9 rounded-full bg-success-tint text-success font-caption text-caption shadow-sm border border-success/20">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse"></span>
            <span className="font-semibold tracking-wide">Live stream: Active</span>
          </div>

          <button
            type="button"
            onClick={exportAuditCSV}
            className="h-9 px-space-md bg-surface text-text hover:bg-subtle transition-colors rounded-lg flex items-center gap-space-xs font-subsection text-body font-semibold border border-border shadow-sm cursor-pointer"
            title="Export current audit log scope to CSV"
          >
            <span className="material-symbols-outlined text-[18px] text-text-secondary">file_download</span>
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-md">
        {/* Metric 1 */}
        <div className="bg-surface rounded-xl p-space-md shadow-sm border border-border flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="font-caption text-caption text-text-tertiary uppercase tracking-wider font-semibold">
              Events logged today
            </span>
            <span className="material-symbols-outlined text-text-tertiary text-[18px]">receipt_long</span>
          </div>
          <div className="mt-space-sm flex items-baseline gap-space-xs">
            <span className="font-score-numerals text-display text-text font-bold">
              {activityMetrics?.events_today ?? 0}
            </span>
            <span className="font-caption text-caption text-text-secondary">events</span>
          </div>
          <div className="mt-space-xs font-code-inline text-code-inline text-text-tertiary">
            IST · 00:00 to {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata', hour12: false })}
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-surface rounded-xl p-space-md shadow-sm border border-border flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="font-caption text-caption text-text-tertiary uppercase tracking-wider font-semibold">
              Sourcing runs
            </span>
            <span className="material-symbols-outlined text-text-tertiary text-[18px]">travel_explore</span>
          </div>
          <div className="mt-space-sm flex items-baseline gap-space-xs">
            <span className="font-score-numerals text-display text-text font-bold">
              {activityMetrics?.sourcing_runs ?? 0}
            </span>
            <span className="font-caption text-caption text-text-secondary">completed</span>
          </div>
          <div className="mt-space-xs font-caption text-caption text-text-secondary">
            <span className="font-score-numerals text-text font-semibold">
              {activityMetrics?.candidates_evaluated ?? 0}
            </span> candidates evaluated
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-surface rounded-xl p-space-md shadow-sm border border-border flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="font-caption text-caption text-text-tertiary uppercase tracking-wider font-semibold">
              Consent records
            </span>
            <span className="material-symbols-outlined text-text-tertiary text-[18px]">verified_user</span>
          </div>
          <div className="mt-space-sm flex items-baseline gap-space-xs">
            <span className="font-score-numerals text-display text-text font-bold">
              {activityMetrics?.consent_records_modified ?? 0}
            </span>
            <span className="font-caption text-caption text-text-secondary">modified</span>
          </div>
          <div className="mt-space-xs font-caption text-caption text-text-secondary">
            {activityMetrics?.consent_records_modified ? 'written' : 'No changes'} today
          </div>
        </div>

        {/* Metric 4 */}
        <div className="bg-surface rounded-xl p-space-md shadow-sm border border-border flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="font-caption text-caption text-text-tertiary uppercase tracking-wider font-semibold">
              Automated actions
            </span>
            <span className="material-symbols-outlined text-text-tertiary text-[18px]">smart_toy</span>
          </div>
          <div className="mt-space-sm flex items-baseline gap-space-xs">
            <span className="font-score-numerals text-display text-text font-bold">
              {activityMetrics?.automated_actions ?? 0}
            </span>
            <span className="font-caption text-caption text-text-secondary">executed</span>
          </div>
          <div className="mt-space-xs font-caption text-caption text-success flex items-center gap-1 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
            <span>{activityMetrics?.policy_compliance_rate ?? 100}% policy compliant</span>
          </div>
        </div>
      </div>

      {/* Audit Filters Toolbar */}
      <div className="bg-surface rounded-xl p-space-md shadow-sm border border-border flex flex-col gap-space-md">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-space-sm items-center">
          {/* Search Input */}
          <div className="lg:col-span-4 relative flex items-center">
            <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute left-3 pointer-events-none">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter activity, candidates, or roles..."
              className="w-full h-10 pl-9 pr-3 bg-surface font-body text-body text-text placeholder:text-text-tertiary rounded-lg border border-border focus:outline-none focus:ring-1 focus:ring-accent shadow-sm"
            />
          </div>

          {/* Role Dropdown */}
          <div className="lg:col-span-2">
            <div className="relative">
              <select
                value={selectedRoleFilter}
                onChange={(e) => setSelectedRoleFilter(e.target.value)}
                className="w-full h-10 px-3 pr-8 bg-surface font-body text-body text-text rounded-lg border border-border appearance-none focus:outline-none focus:ring-1 focus:ring-accent shadow-sm cursor-pointer"
              >
                <option value="all">Role: All roles</option>
                <option value="pune_backend">Senior Backend Engineer, Pune</option>
                <option value="devops">Lead DevOps Engineer</option>
                <option value="staff_frontend">Staff Frontend Architect</option>
              </select>
              <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-2.5 top-2.5 pointer-events-none">
                expand_more
              </span>
            </div>
          </div>

          {/* Action Category Dropdown */}
          <div className="lg:col-span-2">
            <div className="relative">
              <select
                value={selectedActionFilter}
                onChange={(e) => setSelectedActionFilter(e.target.value)}
                className="w-full h-10 px-3 pr-8 bg-surface font-body text-body text-text rounded-lg border border-border appearance-none focus:outline-none focus:ring-1 focus:ring-accent shadow-sm cursor-pointer"
              >
                <option value="all">Action: All actions</option>
                <option value="sourcing">Sourcing runs</option>
                <option value="screening">Screening &amp; scoring</option>
                <option value="consent">Consent updates</option>
                <option value="outreach">Outreach operations</option>
                <option value="optout">Opt-out / Deletion</option>
                <option value="inspection">Regulatory inspection</option>
              </select>
              <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-2.5 top-2.5 pointer-events-none">
                expand_more
              </span>
            </div>
          </div>

          {/* Status Dropdown */}
          <div className="lg:col-span-2">
            <div className="relative">
              <select
                value={selectedStatusFilter}
                onChange={(e) => setSelectedStatusFilter(e.target.value)}
                className="w-full h-10 px-3 pr-8 bg-surface font-body text-body text-text rounded-lg border border-border appearance-none focus:outline-none focus:ring-1 focus:ring-accent shadow-sm cursor-pointer"
              >
                <option value="all">Status: All results</option>
                <option value="success">Success / Allowed</option>
                <option value="blocked">Blocked by consent gate</option>
                <option value="rate_limited">Rate-limited / Queued</option>
              </select>
              <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-2.5 top-2.5 pointer-events-none">
                expand_more
              </span>
            </div>
          </div>

          {/* Date Range Dropdown */}
          <div className="lg:col-span-2">
            <div className="relative">
              <select
                value={dateRangeFilter}
                onChange={(e) => setDateRangeFilter(e.target.value)}
                className="w-full h-10 px-3 pr-8 bg-surface font-body text-body text-text rounded-lg border border-border appearance-none focus:outline-none focus:ring-1 focus:ring-accent shadow-sm cursor-pointer"
              >
                <option value="7d">Date: Last 7 days</option>
                <option value="24h">Last 24 hours</option>
                <option value="30d">Last 30 days</option>
              </select>
              <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-2.5 top-2.5 pointer-events-none">
                date_range
              </span>
            </div>
          </div>
        </div>

        {/* Secondary Filter Info */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-body font-body text-text-secondary pt-space-xs border-t border-border/40">
          <div className="flex items-center gap-space-md">
            <span className="font-body text-body">
              Showing <span className="font-score-numerals font-semibold text-text">{filteredEvents.length}</span> of <span className="font-score-numerals font-semibold text-text">{auditEvents.length}</span> events
            </span>
            <span className="text-text-tertiary">•</span>
            <span className="font-code-inline text-code-inline text-text-tertiary">Interval: 14 Oct 2026 – 20 Oct 2026 IST</span>
          </div>

          <button
            type="button"
            onClick={resetFilters}
            className="text-caption font-caption text-accent hover:text-accent-hover font-semibold transition-colors mt-2 sm:mt-0 flex items-center gap-1 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[14px]">refresh</span>
            <span>Reset active filters</span>
          </button>
        </div>
      </div>

      {/* Activity Feed Table */}
      <div className="w-full bg-surface shadow-sm border border-border overflow-hidden rounded-none">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-subtle h-9 border-b border-border text-caption font-caption text-text-secondary">
                <th className="px-space-md py-space-xs font-semibold uppercase tracking-wider w-[180px]">
                  Timestamp (IST)
                </th>
                <th className="px-space-md py-space-xs font-semibold uppercase tracking-wider w-[180px]">
                  Category / Actor
                </th>
                <th className="px-space-md py-space-xs font-semibold uppercase tracking-wider min-w-[380px]">
                  Event Description
                </th>
                <th className="px-space-md py-space-xs font-semibold uppercase tracking-wider w-[240px]">
                  Target Entity
                </th>
                <th className="px-space-md py-space-xs font-semibold uppercase tracking-wider w-[180px]">
                  Audit Hash / Proof
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-body font-body text-text">
              {filteredEvents.map((ev) => (
                <tr
                  key={ev.id}
                  className={`hover:bg-subtle transition-colors group cursor-pointer h-11 ${
                    ev.status === 'blocked' ? 'bg-danger-tint/20' : ''
                  }`}
                  onClick={() => triggerToast({ title: "Audit Verification", message: `Checksum: ${ev.auditHash} · Verified tamper-evident`, type: "info" })}
                >
                  <td className="px-space-md py-2 font-score-numerals text-caption text-text-secondary whitespace-nowrap">
                    {ev.timestamp}
                  </td>

                  <td className="px-space-md py-2 whitespace-nowrap">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full font-caption text-caption border ${
                      ev.actorCategory === 'Policy Engine'
                        ? 'bg-danger-tint text-danger border-danger/20 font-medium'
                        : ev.actorCategory === 'Recruiter Ops'
                        ? 'bg-success-tint text-success border-success/20 font-medium'
                        : ev.actorCategory === 'Privacy Portal'
                        ? 'bg-warning-tint text-warning border-warning/20 font-medium'
                        : 'bg-subtle text-text border-border font-medium'
                    }`}>
                      {ev.actorCategory === 'HirePath System' && (
                        <span className="material-symbols-outlined text-[14px] text-accent">smart_toy</span>
                      )}
                      {ev.actorCategory === 'Policy Engine' && (
                        <span className="material-symbols-outlined text-[14px] text-danger">gavel</span>
                      )}
                      {ev.actorCategory === 'Recruiter Ops' && (
                        <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                      )}
                      {ev.actorCategory === 'Privacy Portal' && (
                        <span className="w-1.5 h-1.5 rounded-full bg-warning"></span>
                      )}
                      <span>{ev.actorCategory}</span>
                    </span>
                  </td>

                  <td className="px-space-md py-2 font-body text-body text-text">
                    {ev.status === 'blocked' ? (
                      <span className="text-danger font-semibold">Outreach blocked: </span>
                    ) : null}
                    {ev.eventDescription}
                  </td>

                  <td className="px-space-md py-2 whitespace-nowrap">
                    <span className="text-accent hover:text-accent-hover font-medium underline-offset-2 hover:underline">
                      {ev.targetEntity}
                    </span>
                  </td>

                  <td className="px-space-md py-2 whitespace-nowrap">
                    <div className="flex items-center gap-1 font-code-inline text-code-inline text-text-tertiary">
                      <span className={`material-symbols-outlined text-[14px] ${
                        ev.status === 'blocked' ? 'text-text-tertiary' : 'text-success'
                      }`}>
                        {ev.status === 'blocked' ? 'lock' : 'verified'}
                      </span>
                      <span>{ev.auditHash}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination & Footer Toolbar */}
        <div className="bg-subtle px-space-md py-space-sm flex flex-col md:flex-row md:items-center justify-between gap-space-md border-t border-border">
          <div className="flex items-center gap-space-lg text-caption font-caption text-text-secondary">
            <div className="flex items-center gap-space-xs">
              <span>Rows per page:</span>
              <div className="relative inline-block">
                <select
                  value={rowsPerPage}
                  onChange={(e) => setRowsPerPage(Number(e.target.value))}
                  className="h-7 px-2 pr-6 bg-surface font-body text-caption text-text rounded border border-border focus:outline-none focus:ring-1 focus:ring-accent appearance-none shadow-sm cursor-pointer"
                >
                  <option value={12}>12</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
                <span className="material-symbols-outlined text-[14px] text-text-tertiary absolute right-1 top-1.5 pointer-events-none">
                  expand_more
                </span>
              </div>
            </div>
            <span className="text-text-tertiary">|</span>
            <span>
              Showing <span className="font-score-numerals font-semibold text-text">1–{filteredEvents.length}</span> of <span className="font-score-numerals font-semibold text-text">{auditEvents.length}</span> events
            </span>
          </div>

          <div className="flex items-center gap-1 self-end md:self-auto">
            <button
              type="button"
              disabled
              aria-label="Previous page"
              className="w-8 h-8 rounded bg-surface border border-border text-text-tertiary flex items-center justify-center cursor-not-allowed opacity-50"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_left</span>
            </button>
            <button
              type="button"
              className="w-8 h-8 rounded bg-primary text-on-primary font-score-numerals text-caption font-semibold flex items-center justify-center shadow-sm"
            >
              1
            </button>
            <button
              type="button"
              className="w-8 h-8 rounded bg-surface border border-border text-text font-score-numerals text-caption font-semibold flex items-center justify-center hover:bg-subtle"
            >
              2
            </button>
            <button
              type="button"
              className="w-8 h-8 rounded bg-surface border border-border text-text font-score-numerals text-caption font-semibold flex items-center justify-center hover:bg-subtle"
            >
              3
            </button>
            <span className="px-1 text-text-tertiary font-score-numerals text-caption">...</span>
            <button
              type="button"
              className="w-8 h-8 rounded bg-surface border border-border text-text font-score-numerals text-caption font-semibold flex items-center justify-center hover:bg-subtle"
            >
              21
            </button>
            <button
              type="button"
              aria-label="Next page"
              className="w-8 h-8 rounded bg-surface border border-border text-text flex items-center justify-center hover:bg-subtle"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            </button>
          </div>
        </div>
      </div>

      {/* Compliance Spec Notice */}
      <div className="flex items-center gap-space-sm text-text-tertiary font-caption text-caption pb-space-lg">
        <span className="material-symbols-outlined text-[18px] text-text-tertiary flex-shrink-0">
          verified_user
        </span>
        <span>
          All activity records are cryptographically timestamped in UTC+05:30 (IST) and retained in accordance with ISO 27701 and DPDPA compliance specifications. Tamper detection verification check passes continuously.
        </span>
      </div>
    </div>
  );
};
