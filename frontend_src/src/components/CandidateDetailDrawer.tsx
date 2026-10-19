import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Candidate } from '../types';

export const CandidateDetailDrawer: React.FC = () => {
  const { 
    activeCandidateDrawer, 
    closeCandidateDrawer,
    revealCandidateEmail,
    deleteCandidate,
    optOutCandidate,
    setIsOutreachModalOpen,
    openScheduleModal,
    openRecordConsentModal
  } = useApp();

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState<string>('');

  if (!activeCandidateDrawer) return null;

  const candidate = activeCandidateDrawer;

  const handleDeleteSubmit = () => {
    if (deleteConfirmText.trim() === candidate.name) {
      deleteCandidate(candidate.id);
      setIsDeleteModalOpen(false);
      setDeleteConfirmText('');
    }
  };

  return (
    <>
      {/* Exact 24% Backdrop Scrim */}
      <div 
        onClick={closeCandidateDrawer}
        className="fixed inset-0 left-[240px] top-14 bg-text/25 z-40 backdrop-blur-[0.5px] transition-opacity"
      />

      {/* Slide-out Drawer Panel (480px width) */}
      <div className="fixed top-14 right-0 bottom-0 w-full sm:w-[480px] bg-surface z-50 flex flex-col shadow-[-4px_0_24px_rgba(20,24,29,0.12)] border-l border-border overflow-hidden animate-in slide-in-from-right duration-200">
        {/* 1. Header */}
        <div className="h-14 px-space-xl bg-surface border-b border-border flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-space-sm">
            <span className="px-space-sm py-0.5 rounded-full bg-subtle text-text-secondary text-caption font-caption font-medium capitalize border border-border">
              {candidate.stage} stage
            </span>
            <span className="font-score-numerals text-caption text-text-tertiary">
              {candidate.id}
            </span>
          </div>

          <div className="flex items-center gap-space-xs">
            <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-code-inline text-text-tertiary bg-subtle rounded border border-border">
              ESC
            </kbd>
            <button
              type="button"
              onClick={closeCandidateDrawer}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-text-secondary hover:text-text hover:bg-subtle transition-colors"
              title="Close panel"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto px-space-xl py-space-lg flex flex-col gap-space-xl">
          {/* Identity Section */}
          <section className="flex flex-col gap-space-md">
            <div className="flex items-start justify-between gap-space-md">
              <div className="flex flex-col">
                <h2 className="font-page-title text-page-title text-text font-bold tracking-tight">
                  {candidate.name}
                </h2>
                <p className="font-body text-body text-text-secondary mt-0.5">
                  {candidate.title}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-primary-fixed flex items-center justify-center text-primary font-section-title text-section-title font-semibold flex-shrink-0">
                {candidate.avatar}
              </div>
            </div>

            {/* Public Profile Links */}
            <div className="flex flex-col gap-space-xs pt-space-xs">
              <a
                href={candidate.publicProfiles.github?.startsWith('http') ? candidate.publicProfiles.github : `https://${candidate.publicProfiles.github}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between p-space-sm bg-subtle rounded-lg text-caption font-caption hover:bg-border/30 transition-colors group border border-border/50"
              >
                <div className="flex items-center gap-space-sm truncate">
                  <span className="material-symbols-outlined text-[18px] text-text-secondary">code</span>
                  <span className="font-code-inline text-code-inline text-text group-hover:text-accent font-medium truncate">
                    {candidate.publicProfiles.github}
                  </span>
                </div>
                <div className="flex items-center gap-space-xs text-text-tertiary flex-shrink-0">
                  <span className="font-score-numerals">
                    {candidate.reposCount || 42} repos · {candidate.followersCount || '1.2k'} followers
                  </span>
                  <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                </div>
              </a>

              {candidate.publicProfiles.stackoverflow && (
                <a
                  href={candidate.publicProfiles.stackoverflow?.startsWith('http') ? candidate.publicProfiles.stackoverflow : `https://${candidate.publicProfiles.stackoverflow}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-space-sm bg-subtle rounded-lg text-caption font-caption hover:bg-border/30 transition-colors group border border-border/50"
                >
                  <div className="flex items-center gap-space-sm truncate">
                    <span className="material-symbols-outlined text-[18px] text-text-secondary">forum</span>
                    <span className="font-code-inline text-code-inline text-text group-hover:text-accent font-medium truncate">
                      {candidate.publicProfiles.stackoverflow}
                    </span>
                  </div>
                  <div className="flex items-center gap-space-xs text-text-tertiary flex-shrink-0">
                    <span className="font-score-numerals">{candidate.rep || 4820} rep</span>
                    <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                  </div>
                </a>
              )}
            </div>

            {/* Audited Email Reveal Row */}
            <div className="p-space-md bg-subtle/70 rounded-lg flex flex-col gap-space-xs border border-border">
              <div className="flex items-center justify-between">
                <span className="text-caption font-caption text-text-secondary font-medium">Verified candidate email</span>
                <span className="text-[11px] font-caption text-text-tertiary flex items-center gap-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${candidate.isEmailRevealed ? 'bg-success' : 'bg-border-strong'}`}></span>
                  {candidate.isEmailRevealed ? (
                    <span className="text-success font-medium">Audit logged (recruiter@company.com)</span>
                  ) : (
                    <span>Masked for privacy</span>
                  )}
                </span>
              </div>

              <div className="flex items-center justify-between gap-space-sm">
                <span className="font-code-inline text-body text-text tracking-wide font-medium">
                  {candidate.isEmailRevealed ? candidate.email : candidate.maskedEmail}
                </span>
                {!candidate.isEmailRevealed ? (
                  <button
                    type="button"
                    onClick={() => revealCandidateEmail(candidate.id)}
                    className="h-8 px-space-md bg-surface text-text hover:bg-subtle text-caption font-caption font-semibold rounded-[6px] border border-border-strong shadow-sm transition-colors flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[16px] text-text-secondary">visibility</span>
                    <span>Show email</span>
                  </button>
                ) : (
                  <span className="text-caption font-caption text-success font-medium flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px]">verified</span>
                    <span>Logged</span>
                  </span>
                )}
              </div>
              <span className="text-[11px] leading-[15px] text-text-tertiary">
                Viewing records an audit log entry visible in compliance reports.
              </span>
            </div>
          </section>

          {/* Score Breakdown Section */}
          <section className="flex flex-col gap-space-md pt-space-xs border-t border-border">
            <div className="flex flex-col gap-space-xs">
              <div className="flex items-baseline gap-space-xs">
                <span className="font-score-numerals text-[28px] leading-[32px] font-semibold text-text">
                  {candidate.matchScore}
                </span>
                <span className="font-score-numerals text-caption text-text-tertiary">/ 100</span>
              </div>
              <p className="text-caption font-caption text-text-secondary font-medium">
                Match score against {candidate.roleTitle}
              </p>
              <div className="w-full h-1.5 bg-subtle rounded-none overflow-hidden mt-1">
                <div
                  className={`h-full ${candidate.matchScore >= 70 ? 'bg-accent' : 'bg-warning'}`}
                  style={{ width: `${candidate.matchScore}%` }}
                ></div>
              </div>
            </div>

            {/* Explainable Factors */}
            <div className="flex flex-col gap-space-sm">
              <div className="text-caption font-caption font-semibold text-text uppercase tracking-wider text-[11px]">
                Score breakdown &amp; provenance
              </div>

              {Object.entries(candidate.scoreBreakdown).map(([key, factor]) => (
                <div key={key} className="p-space-md bg-subtle rounded-lg flex flex-col gap-1.5 border border-border/40">
                  <div className="flex items-center justify-between">
                    <span className="text-body font-body font-semibold text-text">{factor.label}</span>
                    <span className="font-score-numerals text-caption font-semibold text-accent">
                      {factor.score} / {factor.max} pts
                    </span>
                  </div>
                  <p className="text-caption font-caption text-text-secondary">{factor.desc}</p>
                  <div className="pt-0.5">
                    <span 
                      onClick={() => {
                        const evUrl = factor.evidence || (candidate.publicProfiles.github?.startsWith('http') ? candidate.publicProfiles.github : `https://${candidate.publicProfiles.github}`);
                        window.open(evUrl, '_blank');
                      }}
                      className="text-[11px] font-caption text-accent hover:text-accent-hover font-semibold inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>View evidence</span>
                      <span className="material-symbols-outlined text-[13px]">arrow_forward</span>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Location Provenance Section */}
          <section className="flex flex-col gap-space-md pt-space-xs border-t border-border">
            <div className="text-caption font-caption font-semibold text-text uppercase tracking-wider text-[11px]">
              Location provenance &amp; territory match
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-[18px] text-accent">location_on</span>
                <span className="text-body font-body font-semibold text-text">{candidate.location}</span>
              </div>
              <span className="px-space-sm py-0.5 rounded-full bg-success-tint text-success font-caption text-[11px] font-semibold tracking-wide">
                {candidate.locationConfidence} confidence
              </span>
            </div>
            <p className="text-caption font-caption text-text-secondary">
              Matched <strong className="font-medium text-text">"{candidate.location}"</strong> in public profile bio &amp; company field.
            </p>

            {/* Raw signals box */}
            <div className="p-space-md bg-subtle rounded-lg flex flex-col gap-space-sm border border-border/40">
              <div className="flex items-center justify-between text-caption font-caption font-semibold text-text-secondary">
                <span>Raw verified profile signals</span>
                <span className="text-[11px] text-accent font-medium">Automated resolution</span>
              </div>
              <div className="p-space-sm bg-surface rounded font-code-inline text-code-inline text-text flex flex-col gap-1 border border-border">
                <div><span className="text-text-tertiary">Location string:</span> "{candidate.rawLocationSignals.locationString}"</div>
                <div><span className="text-text-tertiary">Company:</span> "{candidate.rawLocationSignals.company}"</div>
                <div><span className="text-text-tertiary">Timezone match:</span> {candidate.rawLocationSignals.timezone}</div>
              </div>
              <p className="text-[11px] leading-[15px] text-text-tertiary">
                {candidate.rawLocationSignals.note}
              </p>
            </div>
          </section>

          {/* Regulatory & DPDPA Consent Section */}
          <section className="flex flex-col gap-space-md pt-space-xs border-t border-border">
            <div className="text-caption font-caption font-semibold text-text uppercase tracking-wider text-[11px]">
              Regulatory status &amp; DPDPA compliance
            </div>

            {candidate.consent.status === 'recorded' ? (
              <div className="flex items-center gap-space-xs px-space-md py-space-sm rounded-lg bg-success-tint text-success text-body font-body font-medium">
                <span className="material-symbols-outlined text-[20px]">check_circle</span>
                <span>Recorded on {candidate.consent.recordedDate}</span>
              </div>
            ) : candidate.consent.status === 'withdrawn' ? (
              <div className="flex items-center gap-space-xs px-space-md py-space-sm rounded-lg bg-danger-tint text-danger text-body font-body font-medium">
                <span className="material-symbols-outlined text-[20px]">block</span>
                <span>Candidate opted out · Outreach permanently blocked</span>
              </div>
            ) : (
              <div className="flex items-center gap-space-xs px-space-md py-space-sm rounded-lg bg-warning-tint text-warning text-body font-body font-medium">
                <span className="material-symbols-outlined text-[20px]">warning</span>
                <span>Pending audit · Outreach locked under Section 6(1)</span>
              </div>
            )}

            <div className="p-space-md bg-subtle rounded-lg flex flex-col gap-space-sm border border-border/40">
              <div className="flex flex-col gap-0.5">
                <span className="text-caption font-caption text-text-secondary">Channel</span>
                <span className="text-body font-body font-semibold text-text">
                  {candidate.consent.channel || candidate.consent.proofMethod || 'Public search indexing'}
                </span>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-caption font-caption text-text-secondary">Recorded by</span>
                <span className="text-caption font-caption font-code-inline text-text">
                  {candidate.consent.recordedBy || 'System policy'}
                </span>
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-caption font-caption text-text-secondary">Consent expiration</span>
                <span className="text-caption font-caption text-text">
                  {candidate.consent.expiryDate || '1 year standard window under DPDPA India'}
                </span>
              </div>
              <div className="pt-space-xs">
                <button
                  type="button"
                  onClick={() => openRecordConsentModal(candidate)}
                  className="h-8 px-space-md bg-surface text-text hover:bg-subtle rounded-[6px] text-caption font-caption font-semibold border border-border-strong shadow-sm transition-colors"
                >
                  Update consent record
                </button>
              </div>
            </div>
          </section>

          {/* Activity Timeline */}
          <section className="flex flex-col gap-space-md pt-space-xs border-t border-border">
            <div className="text-caption font-caption font-semibold text-text uppercase tracking-wider text-[11px]">
              Candidate activity audit trail
            </div>
            <div className="relative pl-6 flex flex-col gap-space-lg before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-[1px] before:bg-border">
              {candidate.activityTimeline.map((item, index) => (
                <div key={index} className="relative flex flex-col gap-0.5">
                  <span className={`absolute -left-6 top-1 w-2.5 h-2.5 rounded-full ring-4 ring-surface ${
                    item.type === 'consent' ? 'bg-success' : item.type === 'system' ? 'bg-accent' : 'bg-text-tertiary'
                  }`} />
                  <span className="text-body font-body font-medium text-text leading-snug">
                    {item.action}
                  </span>
                  <span className="font-code-inline text-[11px] text-text-tertiary">
                    {item.timestamp}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* Danger Zone */}
          <section className="p-space-md bg-danger-tint rounded-lg flex flex-col gap-space-md border border-danger/20">
            <div className="flex items-center gap-space-xs text-danger font-subsection text-subsection font-semibold">
              <span className="material-symbols-outlined text-[18px]">warning</span>
              <span>Danger zone</span>
            </div>

            {/* Opt out */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm pt-space-xs">
              <div className="flex flex-col">
                <span className="text-body font-body font-semibold text-text">Opt out candidate</span>
                <span className="text-[12px] leading-[17px] text-text-secondary">
                  Mark candidate as opted out. No future outreach allowed.
                </span>
              </div>
              <button
                type="button"
                onClick={() => optOutCandidate(candidate.id)}
                className="h-8 px-space-md bg-surface text-danger hover:bg-danger hover:text-white rounded-[6px] text-caption font-caption font-semibold border border-danger/30 shadow-sm transition-colors flex-shrink-0"
              >
                Opt out
              </button>
            </div>

            <div className="h-[1px] bg-danger/10 w-full"></div>

            {/* Delete Data */}
            <div className="flex flex-col gap-space-sm">
              <div className="flex flex-col">
                <span className="text-body font-body font-semibold text-danger">Delete candidate data</span>
                <span className="text-[12px] leading-[17px] text-text-secondary">
                  Permanently delete candidate records, scores, and activity history. Requires typing '{candidate.name}' to confirm.
                </span>
              </div>
              <div>
                <button
                  type="button"
                  onClick={() => setIsDeleteModalOpen(true)}
                  className="h-8 px-space-md bg-surface text-danger hover:bg-danger hover:text-white rounded-[6px] text-caption font-caption font-semibold border border-danger/30 shadow-sm transition-colors"
                >
                  Delete data
                </button>
              </div>
            </div>
          </section>
        </div>

        {/* Pinned Bottom Actions */}
        <div className="p-space-md bg-surface border-t border-border flex flex-col gap-space-sm shadow-[0_-4px_16px_rgba(20,24,29,0.04)] flex-shrink-0">
          <div className="flex items-center gap-space-sm">
            <button
              type="button"
              onClick={() => {
                if (candidate.consent.status !== 'recorded') {
                  openRecordConsentModal(candidate);
                } else {
                  setIsOutreachModalOpen(true);
                }
              }}
              className="flex-1 h-9 bg-accent text-on-accent text-body font-body font-semibold rounded-[6px] hover:bg-accent-hover transition-colors flex items-center justify-center gap-1 shadow-sm"
            >
              <span className="material-symbols-outlined text-[18px]">send</span>
              <span>Send outreach</span>
            </button>
            <button
              type="button"
              onClick={() => openScheduleModal(candidate)}
              className="h-9 px-space-md bg-surface text-text hover:bg-subtle text-body font-body font-semibold rounded-[6px] border border-border-strong shadow-sm transition-colors flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[18px] text-text-secondary">calendar_today</span>
              <span>Schedule</span>
            </button>
          </div>
          <div className="flex items-center justify-between text-caption font-caption text-text-secondary px-space-xs">
            <span>Current: <strong className="text-text capitalize">{candidate.stage}</strong></span>
            <button
              type="button"
              onClick={() => openScheduleModal(candidate)}
              className="text-accent hover:text-accent-hover font-semibold flex items-center gap-0.5"
            >
              <span>Move to Interviewed</span>
              <span className="material-symbols-outlined text-[14px]">chevron_right</span>
            </button>
          </div>
        </div>
      </div>

      {/* Delete Data Confirmation Modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-space-md bg-text/40 backdrop-blur-[1px]">
          <div className="w-full max-w-[480px] bg-surface rounded-xl p-space-xl shadow-2xl flex flex-col gap-space-md border border-border">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2 text-danger">
                <span className="material-symbols-outlined text-[24px]">delete_forever</span>
                <h3 className="font-section-title text-section-title font-semibold text-text">
                  Permanently delete candidate?
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsDeleteModalOpen(false)}
                className="text-text-tertiary hover:text-text"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <p className="text-body font-body text-text-secondary leading-relaxed">
              This will immediately remove <strong className="text-text">{candidate.name}</strong> ({candidate.id}), purge all automated score calculations, and invalidate the active DPDPA consent record. This action cannot be reversed.
            </p>

            <div className="flex flex-col gap-1.5 pt-space-xs">
              <label className="text-caption font-caption font-semibold text-text-secondary">
                Type candidate full name <code className="font-code-inline text-text bg-subtle px-1 rounded">{candidate.name}</code> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder={candidate.name}
                className="h-10 px-space-md bg-surface text-text text-body font-body rounded-[6px] border border-border-strong shadow-sm focus:outline-none focus:ring-2 focus:ring-danger"
              />
            </div>

            <div className="flex items-center justify-end gap-space-sm pt-space-sm">
              <button
                type="button"
                onClick={() => {
                  setIsDeleteModalOpen(false);
                  setDeleteConfirmText('');
                }}
                className="h-9 px-space-md bg-surface text-text hover:bg-subtle text-body font-body font-semibold rounded-[6px] border border-border-strong shadow-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleteConfirmText.trim() !== candidate.name}
                onClick={handleDeleteSubmit}
                className={`h-9 px-space-md text-white text-body font-body font-semibold rounded-[6px] transition-all ${
                  deleteConfirmText.trim() === candidate.name
                    ? 'bg-danger hover:bg-red-700 cursor-pointer shadow-sm'
                    : 'bg-danger/40 cursor-not-allowed'
                }`}
              >
                Permanently delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
