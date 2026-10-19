import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

export const PrivacyPortalView: React.FC = () => {
  const { candidates, optOutCandidate, triggerToast } = useApp();
  const [candidateIdInput, setCandidateIdInput] = useState('#CAN-8821');
  const [inquiryType, setInquiryType] = useState('access');
  const [message, setMessage] = useState('');
  const [lookupResult, setLookupResult] = useState<any>(null);

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    const found = candidates.find(
      c => c.id.toLowerCase() === candidateIdInput.trim().toLowerCase() ||
           c.email.toLowerCase() === candidateIdInput.trim().toLowerCase() ||
           c.name.toLowerCase().includes(candidateIdInput.trim().toLowerCase())
    );

    if (found) {
      setLookupResult(found);
      triggerToast({
        title: 'Candidate Record Found',
        message: `Verified DPDPA consent provenance for ${found.name}.`,
        type: 'info'
      });
    } else {
      setLookupResult('NOT_FOUND');
    }
  };

  const handleOptOut = (id: string) => {
    optOutCandidate(id);
    triggerToast({
      title: 'Opt-Out Processed',
      message: 'Candidate marked Do-Not-Contact. Outreach blocked permanently.',
      type: 'warning'
    });
    setLookupResult((prev: any) => prev ? { ...prev, consentStatus: 'opted_out' } : null);
  };

  return (
    <div className="flex-1 min-h-screen bg-[var(--hp-canvas)] pb-16">
      {/* Header */}
      <div className="border-b border-[var(--hp-border)] bg-[var(--hp-surface)] px-8 py-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--hp-text-muted)] mb-1">
              <span>HIREPATH</span>
              <span>/</span>
              <span className="text-[var(--hp-text-secondary)] font-medium">CANDIDATE PRIVACY PORTAL</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--hp-text)]">
              DPDPA 2023 Candidate Rights & Transparency Portal
            </h1>
            <p className="text-sm text-[var(--hp-text-secondary)] mt-0.5">
              Public self-service interface for data principals to inspect consent provenance, exercise right to erasure, and manage preferences.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono bg-[var(--hp-success-bg)] text-[var(--hp-success)] border border-[var(--hp-success)]/20 font-medium">
              <span className="material-symbols-outlined text-[15px]">verified</span>
              DPDPA Sec. 11/12 Compliant
            </span>
          </div>
        </div>
      </div>

      <div className="px-8 py-6 max-w-6xl space-y-6">
        {/* Verification and lookup grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lookup tool */}
          <div className="lg:col-span-2 bg-[var(--hp-surface)] rounded-xl border border-[var(--hp-border)] p-6 shadow-xs">
            <h2 className="text-base font-bold text-[var(--hp-text)] mb-1">
              Candidate Rights Self-Service Verification
            </h2>
            <p className="text-xs text-[var(--hp-text-secondary)] mb-4">
              Enter your Candidate ID (from your outreach email header) or registered email address to view all collected data and lawful basis.
            </p>

            <form onSubmit={handleLookup} className="flex gap-2 mb-6">
              <input
                type="text"
                value={candidateIdInput}
                onChange={(e) => setCandidateIdInput(e.target.value)}
                placeholder="Enter #CAN-8821 or your developer email..."
                className="flex-1 px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] font-mono focus:outline-hidden focus:border-[var(--hp-accent)]"
              />
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold rounded-md bg-[var(--hp-accent)] text-white hover:bg-[var(--hp-accent-hover)] transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
              >
                <span className="material-symbols-outlined text-[16px]">search</span>
                Verify Provenance
              </button>
            </form>

            {lookupResult === 'NOT_FOUND' && (
              <div className="p-4 rounded-lg bg-[var(--hp-subtle)] border border-[var(--hp-border)] text-xs text-center text-[var(--hp-text-muted)]">
                No active records found matching this identifier. Under our retention policy, uncontacted data is expunged every 90 days.
              </div>
            )}

            {lookupResult && lookupResult !== 'NOT_FOUND' && (
              <div className="border border-[var(--hp-border)] rounded-lg p-5 bg-[var(--hp-canvas)] space-y-4 animate-in fade-in duration-150">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-sm font-bold text-[var(--hp-text)]">{lookupResult.name}</div>
                    <div className="text-xs text-[var(--hp-text-muted)] font-mono">{lookupResult.id} · {lookupResult.title}</div>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-medium ${
                    lookupResult.consentStatus === 'verified'
                      ? 'bg-[var(--hp-success-bg)] text-[var(--hp-success)] border border-[var(--hp-success)]/20'
                      : lookupResult.consentStatus === 'opted_out'
                      ? 'bg-[var(--hp-danger-bg)] text-[var(--hp-danger)] border border-[var(--hp-danger)]/20'
                      : 'bg-[var(--hp-warning-bg)] text-[var(--hp-warning)] border border-[var(--hp-warning)]/20'
                  }`}>
                    {lookupResult.consentStatus.toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs pt-2 border-t border-[var(--hp-border)]">
                  <div>
                    <span className="text-[var(--hp-text-muted)] block text-[11px]">Sourcing Provenance</span>
                    <span className="font-semibold text-[var(--hp-text)]">{lookupResult.locationProvenance.source}</span>
                  </div>
                  <div>
                    <span className="text-[var(--hp-text-muted)] block text-[11px]">Public GitHub Repository</span>
                    <a href={`https://${lookupResult.publicProfiles.github}`} target="_blank" rel="noreferrer" className="text-[var(--hp-accent)] underline font-mono">
                      {lookupResult.publicProfiles.github}
                    </a>
                  </div>
                  <div>
                    <span className="text-[var(--hp-text-muted)] block text-[11px]">Lawful Basis</span>
                    <span className="text-[var(--hp-text)] font-medium">Public Technical Profile + Voluntary Opt-in</span>
                  </div>
                  <div>
                    <span className="text-[var(--hp-text-muted)] block text-[11px]">Cryptographic Proof Ledger</span>
                    <span className="font-mono text-[10px] text-[var(--hp-text-muted)] truncate block">
                      SHA-256: 9b2d88fa71e...821c
                    </span>
                  </div>
                </div>

                <div className="pt-3 border-t border-[var(--hp-border)] flex items-center justify-between">
                  <div className="text-xs text-[var(--hp-text-muted)]">
                    Exercise statutory rights under DPDPA:
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleOptOut(lookupResult.id)}
                      disabled={lookupResult.consentStatus === 'opted_out'}
                      className="px-3 py-1.5 rounded text-xs font-semibold bg-[var(--hp-danger)] text-white hover:opacity-90 disabled:opacity-50 cursor-pointer transition-opacity flex items-center gap-1 shadow-xs"
                    >
                      <span className="material-symbols-outlined text-[14px]">block</span>
                      Revoke Consent & Opt-Out
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* DPDPA Principles Box */}
          <div className="bg-[var(--hp-surface)] rounded-xl border border-[var(--hp-border)] p-6 space-y-4 shadow-xs">
            <h3 className="text-sm font-bold text-[var(--hp-text)] flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px] text-[var(--hp-accent)]">shield</span>
              Statutory Fiduciary Guarantees
            </h3>

            <div className="space-y-3 text-xs text-[var(--hp-text-secondary)]">
              <div className="p-3 rounded-lg bg-[var(--hp-subtle)] border border-[var(--hp-border)]">
                <div className="font-bold text-[var(--hp-text)] mb-0.5">1. Purpose Limitation</div>
                <div>Data is exclusively used for technical evaluation against specific open requisitions. Never sold or rented.</div>
              </div>

              <div className="p-3 rounded-lg bg-[var(--hp-subtle)] border border-[var(--hp-border)]">
                <div className="font-bold text-[var(--hp-text)] mb-0.5">2. Storage Limitation</div>
                <div>Inactivity purge kicks in after 90 days. Uncontacted developer profiles are permanently deleted.</div>
              </div>

              <div className="p-3 rounded-lg bg-[var(--hp-subtle)] border border-[var(--hp-border)]">
                <div className="font-bold text-[var(--hp-text)] mb-0.5">3. Immutable Ledger</div>
                <div>Every recruiter access, search, and message is recorded on an append-only cryptographic ledger.</div>
              </div>
            </div>

            <div className="pt-2 text-[11px] text-[var(--hp-text-muted)] font-mono">
              Data Protection Officer Contact:<br />
              <strong className="text-[var(--hp-text)]">dpo@hirepath.internal</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
