import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const RecordConsentModal: React.FC = () => {
  const { 
    isRecordConsentModalOpen, 
    closeRecordConsentModal, 
    recordConsentCandidate, 
    recordCandidateConsent 
  } = useApp();

  const [channelSource, setChannelSource] = useState<string>('Direct written consent (InMail / Email)');
  const [consentDate, setConsentDate] = useState<string>('18 Oct 2026');
  const [consentTime, setConsentTime] = useState<string>('14:30 IST');
  const [proofSnippet, setProofSnippet] = useState<string>('');

  useEffect(() => {
    if (recordConsentCandidate) {
      setProofSnippet(`Candidate ${recordConsentCandidate.name} (${recordConsentCandidate.id}) confirmed direct written consent for recruitment outreach.`);
    }
  }, [recordConsentCandidate]);
  const [attestChecked, setAttestChecked] = useState<boolean>(true);

  if (!isRecordConsentModalOpen || !recordConsentCandidate) return null;

  const candidate = recordConsentCandidate;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!attestChecked) return;

    recordCandidateConsent(candidate.id, {
      channelSource,
      date: consentDate,
      time: consentTime,
      proofSnippet
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-[rgba(0,0,0,0.24)] backdrop-blur-[1px] flex items-center justify-center p-space-md overflow-y-auto">
      {/* Modal Card (max-width: 520px) */}
      <div className="w-full max-w-[520px] bg-surface rounded-xl shadow-[0_8px_24px_rgba(20,24,29,0.14)] my-auto flex flex-col overflow-hidden border border-border animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-space-xl pt-space-xl pb-space-md bg-surface flex items-start justify-between gap-space-md border-b border-border/30">
          <div className="flex flex-col gap-1 min-w-0">
            <div className="flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-[20px] text-accent">
                verified_user
              </span>
              <h2 className="font-section-title text-section-title text-text font-bold tracking-tight">
                Record candidate consent
              </h2>
            </div>
            <p className="font-caption text-caption text-text-tertiary leading-[16px]">
              Verify lawful consent basis before initiating candidate outreach under DPDPA 2023 Section 6(1).
            </p>
          </div>
          <button
            type="button"
            onClick={closeRecordConsentModal}
            aria-label="Close dialog"
            className="w-7 h-7 rounded-lg flex items-center justify-center text-text-tertiary hover:bg-subtle hover:text-text transition-colors flex-shrink-0"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        {/* Candidate Reference Banner */}
        <div className="px-space-xl py-space-sm bg-subtle flex flex-col gap-space-xs border-b border-border/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-space-xs">
              <span className="font-body font-semibold text-body text-text">
                {candidate.name}
              </span>
              <span className="font-code-inline text-code-inline text-text-tertiary">
                {candidate.id}
              </span>
              <span className="text-caption font-caption text-text-tertiary">
                · {candidate.location}
              </span>
            </div>
            <span className="inline-flex items-center gap-1 px-space-xs py-0.5 rounded-full bg-warning-tint text-warning font-caption text-caption border border-warning/20">
              <span className="w-1.5 h-1.5 rounded-full bg-warning"></span>
              <span>Pending audit</span>
            </span>
          </div>
          <p className="font-caption text-caption text-text-secondary leading-[17px]">
            Candidate was sourced from GitHub public activity. Direct outreach is locked until valid consent proof is recorded.
          </p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-space-xl flex flex-col gap-space-lg text-body font-body max-h-[75vh] overflow-y-auto">
          {/* Field 1: Lawful Basis / Channel Source */}
          <div className="flex flex-col gap-space-xs">
            <label className="font-caption text-caption text-text-secondary font-medium">
              Lawful Basis / Channel Source
            </label>
            <div className="grid grid-cols-1 gap-1.5">
              {[
                { id: 'inmail', label: 'Direct written consent (InMail / Email)', tag: 'Primary' },
                { id: 'event', label: 'Recruitment event / Career fair registration' },
                { id: 'referral', label: 'Employee referral with candidate agreement' },
                { id: 'inbound', label: 'Inbound platform application' }
              ].map((opt) => (
                <label
                  key={opt.id}
                  className={`flex items-center justify-between p-space-sm rounded-lg cursor-pointer transition-colors border ${
                    channelSource === opt.label
                      ? 'bg-subtle border-accent/40 shadow-sm'
                      : 'bg-surface border-border/50 hover:bg-subtle'
                  }`}
                >
                  <div className="flex items-center gap-space-sm">
                    <input
                      type="radio"
                      name="channel_source"
                      checked={channelSource === opt.label}
                      onChange={() => setChannelSource(opt.label)}
                      className="w-4 h-4 text-accent accent-accent focus:ring-accent"
                    />
                    <span className="font-body text-body font-medium text-text">{opt.label}</span>
                  </div>
                  {opt.tag && (
                    <span className="font-code-inline text-code-inline text-accent bg-surface px-1.5 py-0.5 rounded border border-border shadow-sm">
                      {opt.tag}
                    </span>
                  )}
                </label>
              ))}
            </div>
          </div>

          {/* Field 2: Date & Time Obtained (IST) */}
          <div className="grid grid-cols-2 gap-space-md">
            <div className="flex flex-col gap-1">
              <label htmlFor="consentDate" className="font-caption text-caption text-text-secondary font-medium">
                Date Consent Obtained
              </label>
              <div className="relative flex items-center">
                <input
                  id="consentDate"
                  type="text"
                  value={consentDate}
                  onChange={(e) => setConsentDate(e.target.value)}
                  className="w-full h-10 px-space-md bg-surface text-body font-body text-text rounded-lg border border-border shadow-sm focus:outline-none focus:ring-1 focus:ring-accent"
                />
                <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-space-md pointer-events-none">
                  calendar_today
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="consentTime" className="font-caption text-caption text-text-secondary font-medium">
                Time (Strictly IST)
              </label>
              <div className="relative flex items-center">
                <input
                  id="consentTime"
                  type="text"
                  value={consentTime}
                  onChange={(e) => setConsentTime(e.target.value)}
                  className="w-full h-10 px-space-md bg-surface font-code-inline text-code-inline text-text rounded-lg border border-border shadow-sm focus:outline-none focus:ring-1 focus:ring-accent"
                />
                <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-space-md pointer-events-none">
                  schedule
                </span>
              </div>
            </div>
          </div>

          {/* Field 3: Consent Proof Excerpt */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <label htmlFor="proofSnippet" className="font-caption text-caption text-text-secondary font-medium">
                Consent proof excerpt or message ID <span className="text-danger">*</span>
              </label>
              <span className="font-code-inline text-[11px] text-text-tertiary">#INM-94821</span>
            </div>
            <textarea
              id="proofSnippet"
              rows={3}
              value={proofSnippet}
              onChange={(e) => setProofSnippet(e.target.value)}
              className="w-full p-space-md bg-surface text-body font-body text-text rounded-lg border border-border shadow-sm focus:outline-none focus:ring-1 focus:ring-accent leading-[20px] resize-none"
            />
            <span className="font-caption text-caption text-text-tertiary">
              Provide message permalink, InMail response ID (#INM-94821), or upload verification screenshot.
            </span>
          </div>

          {/* Attached Proof Artifact Pill */}
          <div className="p-space-sm rounded-lg bg-subtle flex items-center justify-between border border-border/50">
            <div className="flex items-center gap-space-sm min-w-0">
              <span className="material-symbols-outlined text-[18px] text-text-secondary flex-shrink-0">
                attach_file
              </span>
              <div className="flex flex-col min-w-0">
                <span className="font-code-inline text-code-inline text-text truncate">
                  linkedin-consent-inmail-94821.pdf
                </span>
                <span className="font-caption text-[11px] text-text-tertiary">
                  240 KB · SHA256 verified
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1.5 flex-shrink-0 px-2 py-0.5 rounded bg-success-tint text-success font-caption text-caption border border-success/20">
              <span className="material-symbols-outlined text-[14px]">check_circle</span>
              <span className="font-code-inline text-[11px]">Valid SHA-256</span>
            </div>
          </div>

          {/* Scope & Validity Metadata */}
          <div className="grid grid-cols-2 gap-space-md p-space-md rounded-lg bg-subtle border border-border/40">
            <div className="flex flex-col gap-0.5">
              <span className="font-caption text-[11px] text-text-tertiary uppercase tracking-wider font-semibold">
                Validity Period
              </span>
              <span className="font-body text-caption font-semibold text-text">Valid for 365 days</span>
              <span className="font-code-inline text-[11px] text-text-secondary">Expires: 18 Oct 2027 IST</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="font-caption text-[11px] text-text-tertiary uppercase tracking-wider font-semibold">
                Regulatory Scope
              </span>
              <div className="flex items-center gap-1 pt-0.5">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-surface text-text font-caption text-[11px] font-semibold border border-border shadow-sm">
                  India · DPDPA 2023 Sec 6
                </span>
              </div>
              <span className="font-caption text-[11px] text-text-tertiary">Jurisdiction: IN / Maharashtra</span>
            </div>
          </div>

          {/* Attestation Checkbox */}
          <div className="pt-space-xs">
            <label className="flex items-start gap-space-sm cursor-pointer select-none">
              <input
                id="attestCheckbox"
                type="checkbox"
                checked={attestChecked}
                onChange={(e) => setAttestChecked(e.target.checked)}
                className="mt-0.5 w-4 h-4 text-accent accent-accent rounded focus:ring-accent"
              />
              <span className="font-caption text-caption text-text leading-[18px]">
                I confirm this candidate explicitly consented to being contacted for this role. This record will be cryptographically logged to the immutable audit trail.
              </span>
            </label>
          </div>

          {/* Actions */}
          <div className="pt-space-sm flex flex-col gap-space-xs border-t border-border">
            <div className="flex items-center justify-end gap-space-md">
              <button
                type="button"
                onClick={closeRecordConsentModal}
                className="h-9 px-space-lg rounded-lg bg-surface text-text font-body text-body font-semibold hover:bg-subtle transition-colors border border-border-strong shadow-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!attestChecked}
                className={`h-9 px-space-lg rounded-lg font-body text-body font-semibold transition-colors flex items-center gap-1.5 shadow-sm ${
                  attestChecked
                    ? 'bg-accent text-on-accent hover:bg-accent-hover cursor-pointer'
                    : 'bg-accent/40 text-on-accent cursor-not-allowed'
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">check</span>
                <span>Record consent</span>
              </button>
            </div>
            <div className="flex items-center justify-end gap-1 text-right">
              <span className="material-symbols-outlined text-[14px] text-text-tertiary">lock</span>
              <span className="font-caption text-[11px] text-text-tertiary">
                Unlocks email outreach and creates immutable audit record <span className="font-code-inline text-text-secondary">#CR-2026-9812</span>.
              </span>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
