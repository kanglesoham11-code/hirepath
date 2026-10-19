import React, { useState, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { Candidate, PipelineStage } from '../types';

export const RoleWorkspaceView: React.FC = () => {
  const {
    setIsEditRoleModalOpen,
    selectedRole,
    selectedStage,
    setSelectedStage,
    candidates,
    selectedCandidateIds,
    toggleCandidateSelection,
    selectAllCandidates,
    clearCandidateSelection,
    openCandidateDrawer,
    setIsSourceModalOpen,
    setIsOutreachModalOpen,
    openRecordConsentModal,
    exportStageCSV
  , screenCandidate, screenRole, triggerToast, refreshCandidates, refreshRoles, refreshAll} = useApp();

  const [filterQuery, setFilterQuery] = useState<string>('');
  const [filterConsent, setFilterConsent] = useState<'all' | 'recorded' | 'pending'>('all');
  const [isFilterOpen, setIsFilterOpen] = useState<boolean>(false);
  const [closedDropdownOpen, setClosedDropdownOpen] = useState<boolean>(false);

  // Filter candidates for selected stage and filters
  const stageCandidates = useMemo(() => {
    return candidates.filter((c) => {
      const matchStage = selectedStage === 'closed' 
        ? ['hired', 'rejected', 'stale', 'closed'].includes(c.stage) 
        : c.stage === selectedStage;

      const matchConsent = filterConsent === 'all' 
        ? true 
        : filterConsent === 'recorded' ? c.consent.status === 'recorded' : c.consent.status !== 'recorded';

      const matchQuery = filterQuery === '' 
        || c.name.toLowerCase().includes(filterQuery.toLowerCase())
        || c.location.toLowerCase().includes(filterQuery.toLowerCase())
        || c.source.toLowerCase().includes(filterQuery.toLowerCase());

      return matchStage && matchConsent && matchQuery;
    });
  }, [candidates, selectedStage, filterConsent, filterQuery]);

  const allSelectedInStage = stageCandidates.length > 0 && stageCandidates.every((c) => selectedCandidateIds.includes(c.id));
  const someSelected = stageCandidates.some((c) => selectedCandidateIds.includes(c.id));

  // Check consent status of selected candidates
  const selectedCandidatesList = candidates.filter((c) => selectedCandidateIds.includes(c.id));
  const unconsentedCandidate = selectedCandidatesList.find((c) => c.consent.status !== 'recorded');

  const stageTabs: Array<{ id: PipelineStage; label: string; count: number }> = [
    { id: 'sourced', label: 'Sourced', count: selectedRole?.pipelineStages?.sourced || 0 },
    { id: 'screened', label: 'Screened', count: selectedRole?.pipelineStages?.screened || 0 },
    { id: 'outreach', label: 'Outreach sent', count: selectedRole?.pipelineStages?.outreach || 0 },
    { id: 'replied', label: 'Replied', count: selectedRole?.pipelineStages?.replied || 0 },
    { id: 'interview', label: 'Interview scheduled', count: selectedRole?.pipelineStages?.interview || 0 },
    { id: 'offer', label: 'Offer', count: selectedRole?.pipelineStages?.offer || 0 }
  ];

  return (
    <div className="flex flex-col w-full relative">
      {/* Header Workspace Section */}
      <div className="flex flex-col gap-space-lg mb-space-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md">
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-space-md">
              <h1 className="font-page-title text-page-title text-text tracking-tight font-bold">
                {selectedRole?.title || 'Role'}
              </h1>
              <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-success-tint text-success font-caption text-caption">
                <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                <span className="font-semibold capitalize">{selectedRole?.status || 'Active'}</span>
              </div>
              <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-subtle text-text-secondary font-caption text-caption border border-border">
                <span className="material-symbols-outlined text-[14px] text-text-tertiary">
                  location_on
                </span>
                <span>{selectedRole?.location || 'Pune, India'}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-subtle text-text font-caption text-caption border border-border">
                <span className="text-text-tertiary">Health</span>
                <span className="font-score-numerals text-caption font-semibold">
                  {selectedRole?.healthScore || 70}
                </span>
                <span className="text-text-tertiary">·</span>
                <span className="text-success font-medium">{selectedRole?.healthStatus || 'Healthy'}</span>
              </div>
            </div>
            <p className="font-body text-body text-text-tertiary mt-0.5">
              {selectedRole.reqId} · Hiring Lead: {selectedRole.hiringLead} · {selectedRole.auditVerifiedTime}
            </p>
          </div>

          <div className="flex items-center gap-space-sm flex-shrink-0">
            <button
              type="button"
              onClick={() => setIsEditRoleModalOpen(true)}
              className="h-9 px-4 rounded-[6px] bg-surface text-text font-body text-body font-semibold border border-border-strong hover:bg-subtle transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px] text-text-secondary">edit</span>
              <span>Edit role</span>
            </button>
            <button
              type="button"
              onClick={() => setIsSourceModalOpen(true)}
              className="h-9 px-4 rounded-[6px] bg-accent text-on-accent font-body text-body font-semibold hover:bg-accent-hover transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px]">person_search</span>
              <span>Source candidates</span>
            </button>
          </div>
        </div>

        {/* Stage Tabs Navigation */}
        <div className="border-b border-border flex items-center justify-between overflow-x-auto select-none pt-2">
          <div className="flex items-center gap-space-lg flex-nowrap">
            {stageTabs.map((tab) => {
              const isActive = selectedStage === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedStage(tab.id)}
                  className={`pb-2.5 px-1 border-b-2 font-body text-body flex items-center gap-1.5 whitespace-nowrap transition-colors ${
                    isActive
                      ? 'border-accent text-accent font-semibold'
                      : 'border-transparent text-text-secondary hover:text-text'
                  }`}
                >
                  <span>{tab.label}</span>
                  <span
                    className={`font-score-numerals text-caption px-1.5 py-0.2 rounded font-medium ${
                      isActive
                        ? 'bg-success-tint text-accent font-semibold'
                        : 'bg-subtle text-text-secondary'
                    }`}
                  >
                    {tab.count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Closed Dropdown */}
          <div className="relative pb-2.5 flex-shrink-0">
            <button
              type="button"
              onClick={() => setClosedDropdownOpen((prev) => !prev)}
              className={`flex items-center gap-1.5 font-body text-body font-medium transition-colors ${
                selectedStage === 'closed' ? 'text-accent font-semibold' : 'text-text-secondary hover:text-text'
              }`}
            >
              <span>Closed</span>
              <span className="font-caption text-caption text-text-tertiary">
                (Hired {selectedRole.pipelineStages.hired} · Rejected {selectedRole.pipelineStages.rejected} · Stale {selectedRole.pipelineStages.stale})
              </span>
              <span className="material-symbols-outlined text-[16px] text-text-tertiary">
                keyboard_arrow_down
              </span>
            </button>

            {closedDropdownOpen && (
              <div className="absolute right-0 top-full mt-1 bg-surface border border-border py-1 z-30 min-w-[200px] shadow-[0_8px_24px_rgba(20,24,29,0.12)] rounded-lg">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedStage('closed');
                    setClosedDropdownOpen(false);
                  }}
                  className="w-full px-space-md py-1.5 text-text-secondary font-caption hover:bg-subtle flex justify-between items-center text-left"
                >
                  <span>All Closed Candidates</span>
                  <span className="font-score-numerals text-text font-semibold">14</span>
                </button>
                <div className="h-[1px] bg-border my-1"></div>
                <div className="px-space-md py-1 text-text-secondary font-caption flex justify-between">
                  <span>Hired</span>
                  <span className="font-score-numerals text-success font-semibold">{selectedRole.pipelineStages.hired}</span>
                </div>
                <div className="px-space-md py-1 text-text-secondary font-caption flex justify-between">
                  <span>Rejected</span>
                  <span className="font-score-numerals text-danger font-semibold">{selectedRole.pipelineStages.rejected}</span>
                </div>
                <div className="px-space-md py-1 text-text-secondary font-caption flex justify-between">
                  <span>Stale</span>
                  <span className="font-score-numerals text-warning font-semibold">{selectedRole.pipelineStages.stale}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stage Subheader Action Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm -mt-2">
          <div className="flex items-center gap-2 text-text-secondary font-body text-body">
            <span className="material-symbols-outlined text-[16px] text-text-tertiary">info</span>
            <span>
              Send outreach to {stageCandidates.length} {selectedStage} candidates
            </span>
          </div>

          <div className="flex items-center gap-space-sm flex-wrap relative">
            {/* Filter Toggle */}
            <button
              type="button"
              onClick={() => setIsFilterOpen((prev) => !prev)}
              className={`h-8 px-3 rounded-[6px] bg-surface font-body text-body font-medium border transition-colors flex items-center gap-1 ${
                filterConsent !== 'all' || filterQuery !== ''
                  ? 'border-accent text-accent bg-subtle'
                  : 'border-border text-text hover:bg-subtle'
              }`}
            >
              <span className="material-symbols-outlined text-[16px] text-text-secondary">tune</span>
              <span>Filter candidates</span>
              {(filterConsent !== 'all' || filterQuery !== '') && (
                <span className="w-1.5 h-1.5 rounded-full bg-accent ml-1"></span>
              )}
            </button>

            {/* Filter Dropdown Popover */}
            {isFilterOpen && (
              <div className="absolute right-0 top-10 bg-surface border border-border p-3 z-30 min-w-[260px] shadow-lg rounded-lg flex flex-col gap-2">
                <div className="flex items-center justify-between pb-1 border-b border-border">
                  <span className="font-caption text-caption text-text font-semibold">Filter candidates</span>
                  <button
                    type="button"
                    onClick={() => {
                      setFilterConsent('all');
                      setFilterQuery('');
                    }}
                    className="text-[11px] text-accent hover:underline"
                  >
                    Reset
                  </button>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-caption text-[11px] text-text-secondary font-medium">Search candidate</label>
                  <input
                    type="text"
                    value={filterQuery}
                    onChange={(e) => setFilterQuery(e.target.value)}
                    placeholder="Filter by name, location..."
                    className="h-8 px-2 text-caption bg-surface border border-border rounded text-text outline-none focus:border-accent"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-caption text-[11px] text-text-secondary font-medium">Consent Status</label>
                  <select
                    value={filterConsent}
                    onChange={(e) => setFilterConsent(e.target.value as any)}
                    className="h-8 px-2 text-caption bg-surface border border-border rounded text-text outline-none focus:border-accent"
                  >
                    <option value="all">All consent states</option>
                    <option value="recorded">Recorded only</option>
                    <option value="pending">Pending audit only</option>
                  </select>
                </div>
              </div>
            )}

            {/* Export Stage CSV */}
            <button
              type="button"
              onClick={exportStageCSV}
              className="h-8 px-3 rounded-[6px] bg-surface text-text font-body text-body font-medium border border-border hover:bg-subtle transition-colors flex items-center gap-1 shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px] text-text-secondary">file_download</span>
              <span>Export stage CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main 2-Column Split */}
      <div className="flex flex-col lg:flex-row gap-space-lg items-start relative pb-24">
        {/* Candidate Table (75%) */}
        <div className="w-full lg:w-[calc(100%-344px)] flex flex-col bg-surface border border-border rounded-none overflow-hidden shadow-sm">
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[760px]">
              <thead>
                <tr className="h-9 bg-subtle text-text-secondary font-caption text-caption border-b border-border select-none">
                  <th className="w-9 px-3 text-center" scope="col">
                    <input
                      aria-label="Select all"
                      type="checkbox"
                      checked={allSelectedInStage}
                      onChange={(e) => selectAllCandidates(e.target.checked)}
                      className="w-4 h-4 accent-accent rounded-[2px] cursor-pointer"
                    />
                  </th>
                  <th className="px-3 font-semibold uppercase tracking-wider text-[11px] text-text-secondary" scope="col">
                    Candidate
                  </th>
                  <th className="px-3 font-semibold uppercase tracking-wider text-[11px] text-text-secondary w-28" scope="col">
                    Score
                  </th>
                  <th className="px-3 font-semibold uppercase tracking-wider text-[11px] text-text-secondary" scope="col">
                    Location &amp; Confidence
                  </th>
                  <th className="px-3 font-semibold uppercase tracking-wider text-[11px] text-text-secondary" scope="col">
                    Source
                  </th>
                  <th className="px-3 font-semibold uppercase tracking-wider text-[11px] text-text-secondary" scope="col">
                    Last Action
                  </th>
                  <th className="px-3 font-semibold uppercase tracking-wider text-[11px] text-text-secondary" scope="col">
                    Consent
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-body font-body text-text">
                {stageCandidates.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-space-xl py-12 text-center text-text-secondary">
                      <span className="material-symbols-outlined text-[32px] text-text-tertiary mb-2 block">
                        person_search
                      </span>
                      <p className="font-semibold text-text">No candidates found in this stage matching filters</p>
                      <button
                        type="button"
                        onClick={() => {
                          setFilterConsent('all');
                          setFilterQuery('');
                        }}
                        className="mt-2 text-caption text-accent underline"
                      >
                        Clear filters
                      </button>
                    </td>
                  </tr>
                ) : (
                  stageCandidates.map((candidate) => {
                    const isSelected = selectedCandidateIds.includes(candidate.id);
                    return (
                      <tr
                        key={candidate.id}
                        onClick={() => openCandidateDrawer(candidate)}
                        className={`h-11 transition-colors cursor-pointer group ${
                          isSelected
                            ? 'bg-[#f0f7f5] dark:bg-[rgba(95,196,168,0.12)] hover:bg-[#e6f1ee] dark:hover:bg-[rgba(95,196,168,0.18)]'
                            : 'hover:bg-subtle'
                        }`}
                      >
                        {/* Checkbox column */}
                        <td 
                          className="px-3 text-center"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleCandidateSelection(candidate.id);
                          }}
                        >
                          <input
                            aria-label={`Select ${candidate.name}`}
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {}} // Handled by td onClick
                            className="w-4 h-4 accent-accent rounded-[2px] cursor-pointer"
                          />
                        </td>

                        {/* Candidate Name & Link */}
                        <td className="px-3 py-1.5">
                          <div className="flex flex-col">
                            <span className="font-semibold text-text leading-tight group-hover:text-accent transition-colors">
                              {candidate.name}
                            </span>
                            <span
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(`https://${candidate.publicProfiles.github}`, '_blank');
                              }}
                              className="font-code-inline text-code-inline text-text-tertiary hover:text-accent hover:underline truncate max-w-[150px]"
                            >
                              {candidate.publicProfiles.github}
                            </span>
                          </div>
                        </td>

                        {/* Score with bar & Why? */}
                        <td className="px-3 py-1.5">
                          <div className="flex flex-col gap-1 w-20">
                            <div className="flex items-center justify-between">
                              <span className="font-score-numerals text-score-numerals text-text leading-none font-semibold">
                                {candidate.matchScore}
                              </span>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  openCandidateDrawer(candidate);
                                }}
                                className="text-[11px] text-accent font-medium hover:underline leading-none"
                              >
                                Why?
                              </button>
                            </div>
                            <div className="w-full h-1 bg-subtle rounded-none overflow-hidden">
                              <div
                                className={`h-full ${candidate.matchScore >= 70 ? 'bg-accent' : 'bg-warning'}`}
                                style={{ width: `${candidate.matchScore}%` }}
                              ></div>
                            </div>
                          </div>
                        </td>

                        {/* Location & Confidence */}
                        <td className="px-3 py-1.5">
                          <div className="flex items-center gap-1.5">
                            <span className="px-2 py-0.5 rounded-full bg-subtle text-text text-caption font-caption border border-border">
                              {candidate.location}
                            </span>
                            <span
                              className={`text-[11px] font-semibold uppercase tracking-wider ${
                                candidate.locationConfidence === 'High' ? 'text-success' : 'text-warning'
                              }`}
                            >
                              {candidate.locationConfidence}
                            </span>
                          </div>
                        </td>

                        {/* Source */}
                        <td className="px-3 py-1.5 text-text-secondary font-caption text-caption">
                          {candidate.source}
                        </td>

                        {/* Last Action */}
                        <td className="px-3 py-1.5 text-text-secondary font-caption text-caption whitespace-nowrap">
                          <span className="text-text font-medium">{candidate.lastAction?.action || 'Sourced'}</span> · {candidate.lastAction?.timestamp || 'Recent'}
                        </td>

                        {/* Consent Status */}
                        <td className="px-3 py-1.5 whitespace-nowrap">
                          {candidate.consent.status === 'recorded' ? (
                            <div className="flex items-center gap-1.5">
                              <span className="material-symbols-outlined text-[16px] text-success">
                                check_circle
                              </span>
                              <div className="flex flex-col">
                                <span className="text-caption font-caption text-success font-medium leading-none">
                                  Recorded
                                </span>
                                <span className="text-[10px] text-text-tertiary leading-tight mt-0.5">
                                  {candidate.consent.recordedDate}
                                </span>
                              </div>
                            </div>
                          ) : candidate.consent.status === 'withdrawn' ? (
                            <div className="flex items-center gap-1.5">
                              <span className="material-symbols-outlined text-[16px] text-danger">
                                cancel
                              </span>
                              <span className="px-1.5 py-0.5 bg-danger-tint text-danger font-caption text-caption rounded font-medium">
                                Withdrawn
                              </span>
                            </div>
                          ) : (
                            <div 
                              className="flex items-center gap-1.5 cursor-pointer hover:opacity-80"
                              onClick={(e) => {
                                e.stopPropagation();
                                openRecordConsentModal(candidate);
                              }}
                              title="Click to record consent"
                            >
                              <span className="material-symbols-outlined text-[16px] text-warning">
                                warning
                              </span>
                              <span className="px-1.5 py-0.5 bg-warning-tint text-warning font-caption text-caption rounded font-medium">
                                Not recorded
                              </span>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Table Footer / Pagination Notice */}
          <div className="h-9 px-3 bg-surface border-t border-border flex items-center justify-between text-caption font-caption text-text-tertiary select-none">
            <div className="flex items-center gap-2">
              <span>Showing 1-{stageCandidates.length} of {stageCandidates.length} candidate records</span>
              <span>·</span>
              <span>Regulatory region: DPDP India Compliance Guard enabled</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                disabled
                className="p-1 text-text-tertiary opacity-40 cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-[16px]">chevron_left</span>
              </button>
              <span className="font-score-numerals text-text-secondary px-1 font-medium">
                1 / 1
              </span>
              <button
                type="button"
                disabled
                className="p-1 text-text-tertiary opacity-40 cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-[16px]">chevron_right</span>
              </button>
            </div>
          </div>
        </div>

        {/* Pipeline Health Rail (25% / 320px) */}
        <aside className="w-full lg:w-[320px] bg-surface border border-border flex-shrink-0 flex flex-col p-space-md shadow-sm">
          {/* Rail Header */}
          <div className="flex items-start justify-between pb-space-md border-b border-border">
            <div>
              <span className="font-subsection text-subsection text-text font-semibold block">
                Pipeline health
              </span>
              <span className="text-caption font-caption text-text-tertiary">
                Algorithmic velocity index
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-score-numerals text-[32px] leading-8 font-semibold text-text">
                {selectedRole.healthScore}
              </span>
              <span className="px-2 py-0.5 rounded-full bg-success-tint text-success font-caption text-caption font-semibold">
                {selectedRole.healthStatus}
              </span>
            </div>
          </div>

          {/* Health Breakdown / Weakest Measures */}
          <div className="py-space-md flex flex-col gap-space-sm border-b border-border">
            <span className="font-caption text-caption uppercase tracking-wider text-text-tertiary font-semibold">
              Weakest measures
            </span>
            <ol className="flex flex-col gap-2.5 text-body font-body text-text">
              <li className="flex items-start gap-2">
                <span className="font-score-numerals text-caption font-semibold text-warning bg-warning-tint px-1.5 py-0.2 rounded mt-0.5">
                  1
                </span>
                <div className="flex flex-col">
                  <span className="text-[13px] leading-tight text-text font-medium">
                    Outreach reply rate
                  </span>
                  <span className="font-score-numerals text-[12px] text-warning">
                    18% <span className="text-text-tertiary">vs 35% target</span>
                  </span>
                </div>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-score-numerals text-caption font-semibold text-text-secondary bg-subtle px-1.5 py-0.2 rounded mt-0.5">
                  2
                </span>
                <div className="flex flex-col">
                  <span className="text-[13px] leading-tight text-text font-medium">
                    Consent acquisition latency
                  </span>
                  <span className="font-score-numerals text-[12px] text-text-secondary">
                    avg 4.2 days
                  </span>
                </div>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-score-numerals text-caption font-semibold text-text-secondary bg-subtle px-1.5 py-0.2 rounded mt-0.5">
                  3
                </span>
                <div className="flex flex-col">
                  <span className="text-[13px] leading-tight text-text font-medium">
                    Time in Screened stage
                  </span>
                  <span className="font-score-numerals text-[12px] text-text-secondary">
                    avg 6.8 days
                  </span>
                </div>
              </li>
            </ol>
          </div>

          {/* Stage Distribution Micro-Metric */}
          <div className="py-space-md flex flex-col gap-space-xs border-b border-border">
            <div className="flex items-center justify-between text-caption font-caption text-text-secondary">
              <span>Screening Conversion Rate</span>
              <span className="font-score-numerals font-semibold text-text">66.7%</span>
            </div>
            <div className="w-full h-1.5 bg-subtle rounded-none flex overflow-hidden">
              <div className="h-full bg-accent" style={{ width: '66.7%' }}></div>
              <div className="h-full bg-border-strong" style={{ width: '33.3%' }}></div>
            </div>
            <span className="text-[11px] text-text-tertiary leading-tight">
              12 screened of 18 sourced candidates
            </span>
          </div>

          {/* Suggested Next Step Card */}
          <div className="mt-space-md p-space-md bg-subtle rounded-lg flex flex-col gap-space-sm border border-border">
            <div className="flex items-center gap-1.5 text-accent font-caption text-caption font-semibold">
              <span className="material-symbols-outlined text-[16px]">lightbulb</span>
              <span className="uppercase tracking-wider text-[11px]">Suggested next step</span>
            </div>
            <p className="font-body text-[13px] leading-snug text-text">
              Send outreach to 11 screened candidates with recorded consent to unblock pipeline flow.
            </p>
            <button
              type="button"
              onClick={() => setIsOutreachModalOpen(true)}
              className="mt-1 h-9 px-4 rounded-[6px] bg-accent text-on-accent font-body text-body font-semibold hover:bg-accent-hover transition-colors flex items-center justify-center gap-1.5 w-full shadow-sm"
            >
              <span>Review outreach</span>
              <span className="font-score-numerals text-caption bg-on-accent/20 px-1.5 py-0.5 rounded text-on-accent">
                11
              </span>
            </button>
          </div>
        </aside>
      </div>

      {/* Floating Sticky Bulk Action Bar */}
      {selectedCandidateIds.length > 0 && (
        <div className="fixed bottom-6 left-[256px] right-6 max-w-[1392px] z-30 pointer-events-none flex justify-center animate-in fade-in slide-in-from-bottom-2 duration-150">
          <div className="pointer-events-auto bg-surface border border-border-strong rounded-xl shadow-[0_8px_24px_rgba(20,24,29,0.14)] px-4 py-2 flex flex-wrap items-center justify-between gap-space-md w-full max-w-4xl">
            {/* Left side: Counter and actions */}
            <div className="flex items-center gap-space-md flex-wrap">
              <div className="flex items-center gap-2 pr-3 border-r border-border">
                <span className="font-score-numerals text-body font-semibold text-text">
                  {selectedCandidateIds.length}
                </span>
                <span className="font-body text-body text-text-secondary">selected</span>
              </div>

              <button
                type="button"
                onClick={async () => {
                  try {
                    for (const id of selectedCandidateIds) {
                      await screenCandidate(id);
                    }
                    await refreshCandidates();
                    await refreshRoles();
                    setSelectedStage('screened');
                    triggerToast({ message: `Successfully screened ${selectedCandidateIds.length} candidate(s)`, type: 'success' });
                  } catch (e: any) {
                    triggerToast({ message: e.message || 'Screening failed', type: 'danger' });
                  }
                }}
                className="h-8 px-3 rounded-[6px] bg-surface text-text font-body text-caption font-semibold border border-border-strong hover:bg-subtle transition-colors flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-text-secondary">visibility</span>
                <span>Screen</span>
                <span className="font-score-numerals">{selectedCandidateIds.length}</span>
              </button>

              {/* Consent-Gated Action Button with Warning */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsOutreachModalOpen(true)}
                  disabled={!!unconsentedCandidate}
                  title={unconsentedCandidate ? 'Outreach locked due to missing consent' : 'Send outreach'}
                  className={`h-8 px-3 rounded-[6px] font-body text-caption font-semibold flex items-center gap-1 transition-colors ${
                    unconsentedCandidate
                      ? 'bg-subtle border border-border text-text-secondary opacity-50 cursor-not-allowed'
                      : 'bg-accent text-on-accent hover:bg-accent-hover cursor-pointer shadow-sm'
                  }`}
                >
                  <span className="material-symbols-outlined text-[16px]">send</span>
                  <span>Send outreach</span>
                  <span className="font-score-numerals">{selectedCandidateIds.length}</span>
                </button>

                {unconsentedCandidate && (
                  <div 
                    onClick={() => openRecordConsentModal(unconsentedCandidate)}
                    className="flex items-center gap-1 text-[12px] font-caption text-warning bg-warning-tint px-2 py-1 rounded cursor-pointer hover:bg-warning-tint/80 border border-warning/20"
                    title="Click to record consent and unblock outreach"
                  >
                    <span className="material-symbols-outlined text-[14px]">lock</span>
                    <span className="font-medium">
                      Consent not recorded for 1 selected candidate ({unconsentedCandidate.name})
                    </span>
                    <span className="underline ml-1">Resolve</span>
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={async () => {
                  try {
                    const apiKey = sessionStorage.getItem('hirepath_api_key') || 'hirepath_dev_key_2026';
                    for (const id of selectedCandidateIds) {
                      const num = id.replace('#CAN-', '');
                      await fetch(`http://localhost:8000/api/candidates/${num}/stage`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json', 'X-Api-Key': apiKey },
                        body: JSON.stringify({ stage: 'stale' })
                      });
                    }
                    await refreshCandidates();
                    await refreshRoles();
                    clearCandidateSelection();
                    triggerToast({ message: `Marked ${selectedCandidateIds.length} candidate(s) as stale.`, type: 'info' });
                  } catch (e: any) {
                    triggerToast({ message: e.message || 'Failed to mark stale', type: 'danger' });
                  }
                }}
                className="h-8 px-3 rounded-[6px] bg-surface text-text font-body text-caption font-semibold border border-border-strong hover:bg-subtle transition-colors flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[16px] text-text-secondary">schedule</span>
                <span>Mark stale</span>
                <span className="font-score-numerals">{selectedCandidateIds.length}</span>
              </button>
            </div>

            {/* Right side: Clear link */}
            <div className="flex items-center pl-space-md">
              <button
                type="button"
                onClick={clearCandidateSelection}
                className="font-body text-caption font-medium text-text-secondary hover:text-text underline cursor-pointer"
              >
                Clear selection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
