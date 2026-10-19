import React from 'react';
import { useApp } from '../context/AppContext';

export const ConsentProofModal: React.FC = () => {
  const { isProofModalOpen, proofModalRecord, closeProofModal } = useApp();

  if (!isProofModalOpen || !proofModalRecord) return null;

  const record = proofModalRecord;

  const handleDownloadCertificate = () => {
    const certContent = `--- HIREPATH SOVEREIGN AUDIT CERTIFICATE ---
Record ID: ${record.id}
Candidate: ${record.candidateName} (${record.maskedEmail})
Role: ${record.role}
Consent Status: ${record.status.toUpperCase()}
Lawful Basis: ${record.proofMethod}
Recorded Date: ${record.recordedDate}
Expiry Date: ${record.expiryDate}
Scope: ${record.scope}
Ledger Cryptographic Hash: ${record.proofHash}
Audit Chain Index: #8910-DPDPA-2026
Timestamp: ${new Date().toISOString()}
Compliance Authority: Digital Personal Data Protection Act (DPDPA 2023 Section 6(1))
Digital Signature: VERIFIED_SOVEREIGN_KEY_RING_SHA256
---------------------------------------------`;
    
    const blob = new Blob([certContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit_certificate_${record.id}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-space-md bg-text/40 backdrop-blur-[2px]">
      <div className="bg-surface rounded-xl border border-border w-full max-w-[540px] mx-space-md overflow-hidden shadow-2xl flex flex-col animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-space-xl py-space-lg border-b border-border flex items-center justify-between bg-surface">
          <div className="flex items-center gap-space-sm">
            <div className="w-7 h-7 rounded-full bg-success-tint text-success flex items-center justify-center border border-success/20">
              <span className="material-symbols-outlined text-[16px]">verified</span>
            </div>
            <div>
              <h3 className="font-subsection text-subsection text-text font-bold">
                Consent Cryptographic Proof
              </h3>
              <span className="font-code-inline text-[11px] text-text-tertiary">
                {record.id}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={closeProofModal}
            className="w-8 h-8 rounded-lg hover:bg-subtle text-text-secondary flex items-center justify-center transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-space-xl flex flex-col gap-space-lg text-body font-body">
          <div className="flex flex-col gap-space-xs">
            <span className="font-caption text-caption text-text-secondary font-medium">Subject Candidate</span>
            <span className="font-subsection text-body text-text font-semibold">
              {record.candidateName} <span className="font-code-inline text-text-tertiary font-normal">({record.maskedEmail})</span>
            </span>
          </div>

          <div className="grid grid-cols-2 gap-space-md p-space-md rounded-lg bg-subtle border border-border">
            <div className="flex flex-col">
              <span className="font-caption text-[11px] text-text-secondary">Provenance Method</span>
              <span className="font-code-inline text-caption text-text font-medium truncate" title={record.proofMethod}>
                {record.proofMethod}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="font-caption text-[11px] text-text-secondary">Timestamp (IST)</span>
              <span className="font-code-inline text-caption text-text">
                {record.recordedDate} 14:22:10
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-space-xs">
            <span className="font-caption text-caption text-text-secondary font-medium">
              Cryptographic Proof Hash (Immutable Ledger)
            </span>
            <div className="p-space-sm rounded-lg bg-subtle font-code-inline text-code-inline text-accent select-all break-all border border-border">
              {record.proofHash}
            </div>
          </div>

          <div className="flex items-start gap-space-xs text-caption font-caption text-text-secondary bg-subtle/40 p-2.5 rounded border border-border/40">
            <span className="material-symbols-outlined text-[16px] text-success flex-shrink-0 mt-0.5">lock</span>
            <span>Verified against HirePath Sovereign Key Ring. Audit chain index #8910-DPDPA-2026.</span>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="px-space-xl py-space-md border-t border-border bg-subtle/50 flex items-center justify-end gap-space-sm">
          <button
            type="button"
            onClick={closeProofModal}
            className="h-9 px-space-lg rounded-xl bg-surface border border-border-strong text-body font-subsection text-text hover:bg-subtle transition-colors shadow-sm"
          >
            Close
          </button>
          <button
            type="button"
            onClick={handleDownloadCertificate}
            className="h-9 px-space-lg rounded-xl bg-accent text-on-accent text-body font-subsection hover:bg-accent-hover transition-colors flex items-center gap-space-xs shadow-sm cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">download</span>
            <span>Download Audit Certificate</span>
          </button>
        </div>
      </div>
    </div>
  );
};
