import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

export const OutreachReviewModal: React.FC = () => {
  const { 
    isOutreachModalOpen, 
    setIsOutreachModalOpen, 
    selectedRole, 
    dispatchOutreach,
    openRecordConsentModal,
    candidates,
    selectedCandidateIds
  } = useApp();

  const [previewMode, setPreviewMode] = useState<'merge' | 'edit'>('merge');
  const [safeguardChecked, setSafeguardChecked] = useState<boolean>(true);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [activePreviewId, setActivePreviewId] = useState<string>('');

  const [subjectText, setSubjectText] = useState<string>(
    `${selectedRole?.title || 'Engineering Role'} at HirePath - conversation about your open source work`
  );

  const targetCandidates = candidates.filter(c => 
    selectedCandidateIds.length > 0 ? selectedCandidateIds.includes(c.id) : true
  );

  React.useEffect(() => {
    if (isOutreachModalOpen) {
      const consentedIds = targetCandidates
        .filter(c => c.consent?.status === 'recorded')
        .map(c => c.id);
      setSelectedIds(consentedIds);
      if (targetCandidates.length > 0) {
        setActivePreviewId(targetCandidates[0].id);
      }
    }
  }, [isOutreachModalOpen, candidates, selectedCandidateIds]);

  if (!isOutreachModalOpen) return null;

  const previewCandidate = targetCandidates.find(c => c.id === activePreviewId) || targetCandidates[0];

  const handleToggle = (id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleSendDispatch = () => {
    if (selectedIds.length === 0) return;
    dispatchOutreach(selectedIds);
  };

  const consentedCount = targetCandidates.filter(c => c.consent?.status === 'recorded').length;
  const unconsentedCount = targetCandidates.length - consentedCount;

  return (
    <div className="fixed inset-0 z-50 bg-[#14181D]/[0.24] backdrop-blur-[1px] flex items-center justify-center p-space-xl overflow-y-auto">
      <div className="relative w-full max-w-[780px] my-auto bg-surface border border-border rounded-xl shadow-[0_8px_24px_rgba(20,24,29,0.14)] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[92vh]">
        <div className="px-space-xl py-space-lg border-b border-border bg-surface flex items-start justify-between">
          <div className="flex flex-col gap-0.5">
            <div className="flex items-center gap-space-sm">
              <h2 className="font-section-title text-section-title text-text font-bold">
                Outreach review
              </h2>
              <span className="px-space-sm py-0.5 rounded-full bg-subtle text-text-secondary font-caption text-caption border border-border">
                Live Recipient Gate
              </span>
            </div>
            <p className="font-caption text-caption text-text-tertiary">
              Role: {selectedRole?.title} — <span className="font-score-numerals text-text font-semibold">{targetCandidates.length}</span> live candidate(s)
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsOutreachModalOpen(false)}
            className="w-8 h-8 rounded flex items-center justify-center text-text-tertiary hover:text-text hover:bg-subtle transition-colors cursor-pointer"
            title="Close"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <div className="p-space-xl flex flex-col gap-space-xl overflow-y-auto">
          <div className="flex flex-col gap-space-sm">
            <div className="flex items-baseline justify-between">
              <span className="font-subsection text-subsection text-text font-semibold">
                Recipients ({targetCandidates.length})
              </span>
              <span className="font-caption text-caption text-text-tertiary">
                DPDPA Section 6(1) requires consent verification before outreach dispatch.
              </span>
            </div>

            <div className="border border-border rounded-lg overflow-hidden divide-y divide-border max-h-[260px] overflow-y-auto">
              {targetCandidates.length === 0 ? (
                <div className="p-space-md text-center text-text-tertiary text-caption">
                  No candidates found for this role yet. Use the "Source candidates" button to scrape live candidates.
                </div>
              ) : (
                targetCandidates.map(c => {
                  const hasConsent = c.consent?.status === 'recorded';
                  const isChecked = selectedIds.includes(c.id);

                  return (
                    <div 
                      key={c.id} 
                      className={`p-space-md transition-colors flex items-center justify-between gap-space-md ${
                        hasConsent ? 'bg-surface hover:bg-subtle/50' : 'bg-subtle/60'
                      }`}
                    >
                      <div className="flex items-center gap-space-md min-w-0">
                        <input
                          id={`recip-${c.id}`}
                          type="checkbox"
                          disabled={!hasConsent}
                          checked={isChecked}
                          onChange={() => handleToggle(c.id)}
                          className={`w-4 h-4 rounded border-border-strong text-accent accent-accent flex-shrink-0 ${
                            hasConsent ? 'cursor-pointer' : 'opacity-40 cursor-not-allowed'
                          }`}
                        />
                        <div className="flex flex-col min-w-0">
                          <div className="flex items-center gap-space-xs truncate">
                            <label 
                              htmlFor={`recip-${c.id}`} 
                              className={`font-body text-body font-semibold text-text ${hasConsent ? 'cursor-pointer' : 'opacity-70'}`}
                            >
                              {c.name}
                            </label>
                            <span className="font-code-inline text-code-inline text-text-tertiary">
                              {c.publicProfiles?.github ? `github.com/${c.publicProfiles.github.replace('github.com/', '')}` : c.id}
                            </span>
                          </div>
                          <span className="font-caption text-caption text-text-secondary flex items-center gap-1">
                            {c.maskedEmail || (c.isEmailRevealed && c.email) || 'Public GitHub profile'}
                            <span className="inline-block w-1 h-1 rounded-full bg-border-strong"></span>
                            <span className={hasConsent ? 'text-success font-medium' : 'text-text-tertiary'}>
                              {c.location || 'Maharashtra, India'}
                            </span>
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-space-md flex-shrink-0">
                        {hasConsent ? (
                          <span className="inline-flex items-center gap-1 px-space-sm py-0.5 rounded-full bg-success-tint text-success font-caption text-caption border border-success/20">
                            <span className="material-symbols-outlined text-[14px]">check_circle</span>
                            <span>Consent recorded</span>
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => {
                              setIsOutreachModalOpen(false);
                              openRecordConsentModal(c);
                            }}
                            className="inline-flex items-center gap-1 font-caption text-caption text-accent hover:underline font-semibold cursor-pointer"
                          >
                            <span className="material-symbols-outlined text-[14px]">add_task</span>
                            <span>Record consent</span>
                          </button>
                        )}
                        <span className="font-caption text-caption text-text-secondary w-24 text-right">
                          {hasConsent && isChecked ? 'Ready to send' : hasConsent ? 'Unselected' : 'Locked'}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {previewCandidate && (
            <div className="flex flex-col gap-space-md">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-space-xs text-caption font-caption text-text-secondary">
                  <span className="text-text-tertiary">Previewing context for:</span>
                  <div className="inline-flex items-center gap-1 px-space-sm py-1 bg-subtle rounded border border-border text-text font-medium">
                    <span className="w-2 h-2 rounded-full bg-success"></span>
                    <select
                      value={activePreviewId}
                      onChange={(e) => setActivePreviewId(e.target.value)}
                      className="bg-transparent font-medium text-text outline-none cursor-pointer"
                    >
                      {targetCandidates.map(c => (
                        <option key={c.id} value={c.id} className="bg-surface text-text">
                          {c.name} ({c.publicProfiles?.github || c.id})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex items-center bg-subtle p-0.5 rounded border border-border">
                  <button
                    type="button"
                    onClick={() => setPreviewMode('merge')}
                    className={`px-space-sm py-0.5 text-caption font-caption rounded transition-colors ${
                      previewMode === 'merge'
                        ? 'bg-surface text-accent font-semibold shadow-sm'
                        : 'text-text-secondary hover:text-text'
                    }`}
                  >
                    Preview with merge data
                  </button>
                  <button
                    type="button"
                    onClick={() => setPreviewMode('edit')}
                    className={`px-space-sm py-0.5 text-caption font-caption rounded transition-colors ${
                      previewMode === 'edit'
                        ? 'bg-surface text-accent font-semibold shadow-sm'
                        : 'text-text-secondary hover:text-text'
                    }`}
                  >
                    Edit per-recipient
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="email-subject" className="font-caption text-caption text-text-secondary font-medium">
                  Subject
                </label>
                <input
                  id="email-subject"
                  type="text"
                  value={subjectText}
                  onChange={(e) => setSubjectText(e.target.value)}
                  className="w-full h-10 px-space-md bg-surface text-body font-body text-text border border-border-strong rounded-lg focus:outline-none focus:ring-1 focus:ring-accent shadow-sm"
                />
              </div>

              <div className="w-full bg-surface border border-border rounded-lg p-space-lg flex flex-col gap-space-md font-body text-body text-text leading-relaxed shadow-sm">
                <p>
                  Hi <span className="font-code-inline bg-subtle text-accent px-1.5 py-0.5 rounded font-medium border border-border">{previewCandidate.name}</span>,
                </p>
                <p>
                  I came across your open source profile on GitHub (<span className="font-code-inline bg-subtle text-accent px-1.5 py-0.5 rounded font-medium border border-border">{previewCandidate.publicProfiles?.github || 'GitHub'}</span>) and noticed your work and verified background in <span className="font-code-inline bg-subtle text-accent px-1.5 py-0.5 rounded font-medium border border-border">{previewCandidate.location || selectedRole?.location || 'Maharashtra, India'}</span>.
                </p>
                <p>
                  We are currently expanding our team for the <span className="font-code-inline bg-subtle text-accent px-1.5 py-0.5 rounded font-medium border border-border">{selectedRole?.title}</span> position ({selectedRole?.location || 'Pune / Hybrid'}).
                </p>
                <p>
                  Given your background, I'd welcome a brief 20-minute conversation this week to introduce the team and discuss mutual fit. If you're open to exploring, let me know what times work best for you.
                </p>
                <div className="pt-space-sm border-t border-border flex flex-col text-text-secondary text-caption font-caption">
                  <span className="font-semibold text-text">{selectedRole?.hiringLead || 'Hiring Lead'}</span>
                  <span>Recruitment Ops — HirePath Team</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="px-space-xl py-space-md bg-subtle/50 border-t border-border flex flex-col gap-space-md">
          <div className="flex items-start gap-space-sm">
            <input
              id="safeguard-consent"
              type="checkbox"
              checked={safeguardChecked}
              onChange={(e) => setSafeguardChecked(e.target.checked)}
              className="w-4 h-4 rounded border-border-strong text-accent accent-accent cursor-pointer mt-0.5"
            />
            <div className="flex flex-col">
              <label htmlFor="safeguard-consent" className="font-body text-body font-semibold text-text cursor-pointer leading-tight">
                I have verified these recipients and their recorded consent compliance.
              </label>
              <span className="font-caption text-caption text-text-secondary mt-0.5">
                <strong className="text-text font-semibold">{selectedIds.length}</strong> candidate(s) selected for dispatch. {unconsentedCount > 0 && <span className="text-warning font-semibold">{unconsentedCount} candidate(s) require consent first.</span>}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-space-xs">
            <div className="flex items-center gap-1 text-caption font-caption text-text-tertiary">
              <span className="material-symbols-outlined text-[14px]">lock</span>
              <span>Tamper-evident audit ledger updated on dispatch</span>
            </div>

            <div className="flex items-center gap-space-sm">
              <button
                type="button"
                onClick={() => setIsOutreachModalOpen(false)}
                className="h-9 px-space-md bg-surface border border-border-strong text-text hover:bg-subtle font-body text-body font-semibold rounded-lg transition-colors flex items-center justify-center shadow-sm cursor-pointer"
              >
                Cancel
              </button>

              <button
                type="button"
                disabled={!safeguardChecked || selectedIds.length === 0}
                onClick={handleSendDispatch}
                className={`h-9 px-space-md font-body text-body font-semibold rounded-lg transition-colors flex items-center gap-space-xs shadow-sm ${
                  safeguardChecked && selectedIds.length > 0
                    ? 'bg-accent text-on-accent hover:bg-accent-hover cursor-pointer'
                    : 'bg-accent/40 text-on-accent cursor-not-allowed'
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">send</span>
                <span>Send {selectedIds.length} email{selectedIds.length === 1 ? '' : 's'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
