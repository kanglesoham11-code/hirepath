import React from 'react';
import { useApp } from '../context/AppContext';
import { PipelineStage } from '../types';

interface EmptyStateGuideProps {
  stage: PipelineStage;
}

export const EmptyStateGuide: React.FC<EmptyStateGuideProps> = ({ stage }) => {
  const { 
    selectedRole, 
    setIsSourceModalOpen, 
    openRecordConsentModal, 
    candidates,
    setSelectedStage 
  } = useApp();

  const stageLabels: Record<PipelineStage, string> = {
    sourced: 'Sourced Pool',
    screened: 'Screened & Qualified',
    outreach: 'Outreach Dispatched',
    replied: 'Replied & Interested',
    interview: 'In Technical Interview',
    offer: 'Offer Extended',
    closed: 'Closed / Hired'
  };

  return (
    <div className="py-16 px-6 max-w-3xl mx-auto text-center">
      {/* Empty Illustration / Icon */}
      <div className="w-16 h-16 rounded-2xl bg-[var(--hp-subtle)] border border-[var(--hp-border)] flex items-center justify-center mx-auto mb-4 text-[var(--hp-accent)] shadow-xs">
        <span className="material-symbols-outlined text-[32px]">folder_open</span>
      </div>

      <h3 className="text-lg font-bold text-[var(--hp-text)]">
        No candidates currently in {stageLabels[stage]}
      </h3>
      <p className="text-xs text-[var(--hp-text-secondary)] mt-1.5 max-w-md mx-auto">
        There are currently no engineering profiles staged in this pipeline phase for{' '}
        <span className="font-semibold text-[var(--hp-text)]">{selectedRole?.title}</span>.
      </p>

      {/* Suggested Next Steps Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left mt-8">
        <div className="p-4 rounded-lg bg-[var(--hp-surface)] border border-[var(--hp-border)] hover:border-[var(--hp-accent)] transition-all group flex flex-col justify-between">
          <div>
            <div className="w-8 h-8 rounded-md bg-[var(--hp-accent)]/10 text-[var(--hp-accent)] flex items-center justify-center font-mono text-xs font-bold mb-3">
              01
            </div>
            <h4 className="text-xs font-bold text-[var(--hp-text)] group-hover:text-[var(--hp-accent)] transition-colors">
              Run Sourcing Engine
            </h4>
            <p className="text-[11px] text-[var(--hp-text-muted)] mt-1 leading-relaxed">
              Scan public technical repositories, GitHub commits, and code contributors matching Pune location criteria.
            </p>
          </div>
          <button
            onClick={() => setIsSourceModalOpen(true)}
            className="mt-4 w-full py-1.5 px-3 rounded-md bg-[var(--hp-accent)] text-white hover:bg-[var(--hp-accent-hover)] text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition-colors shadow-xs"
          >
            <span className="material-symbols-outlined text-[15px]">bolt</span>
            Launch Sourcing
          </button>
        </div>

        <div className="p-4 rounded-lg bg-[var(--hp-surface)] border border-[var(--hp-border)] hover:border-[var(--hp-accent)] transition-all group flex flex-col justify-between">
          <div>
            <div className="w-8 h-8 rounded-md bg-[var(--hp-success)]/10 text-[var(--hp-success)] flex items-center justify-center font-mono text-xs font-bold mb-3">
              02
            </div>
            <h4 className="text-xs font-bold text-[var(--hp-text)] group-hover:text-[var(--hp-accent)] transition-colors">
              Record Lawful Consent
            </h4>
            <p className="text-[11px] text-[var(--hp-text-muted)] mt-1 leading-relaxed">
              Directly ingest a referral or inbound application with verified DPDPA written consent proof.
            </p>
          </div>
          <button
            onClick={() => openRecordConsentModal()}
            className="mt-4 w-full py-1.5 px-3 rounded-md border border-[var(--hp-border)] bg-[var(--hp-canvas)] hover:bg-[var(--hp-subtle)] text-[var(--hp-text)] text-xs font-medium flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
          >
            <span className="material-symbols-outlined text-[15px]">verified_user</span>
            Record Consent
          </button>
        </div>

        <div className="p-4 rounded-lg bg-[var(--hp-surface)] border border-[var(--hp-border)] hover:border-[var(--hp-accent)] transition-all group flex flex-col justify-between">
          <div>
            <div className="w-8 h-8 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center font-mono text-xs font-bold mb-3">
              03
            </div>
            <h4 className="text-xs font-bold text-[var(--hp-text)] group-hover:text-[var(--hp-accent)] transition-colors">
              View All Candidates
            </h4>
            <p className="text-[11px] text-[var(--hp-text-muted)] mt-1 leading-relaxed">
              Check other stages in this role pipeline to move candidates forward or review screening scores.
            </p>
          </div>
          <button
            onClick={() => setSelectedStage('screened')}
            className="mt-4 w-full py-1.5 px-3 rounded-md border border-[var(--hp-border)] bg-[var(--hp-canvas)] hover:bg-[var(--hp-subtle)] text-[var(--hp-text)] text-xs font-medium flex items-center justify-center gap-1.5 cursor-pointer transition-colors"
          >
            <span className="material-symbols-outlined text-[15px]">visibility</span>
            View Screened ({candidates.filter(c => c.roleId === selectedRole?.id && c.stage === 'screened').length})
          </button>
        </div>
      </div>

      {/* DPDPA Notice */}
      <div className="mt-8 p-3 rounded-lg bg-[var(--hp-subtle)] border border-[var(--hp-border)] max-w-xl mx-auto flex items-center gap-2.5 text-left">
        <span className="material-symbols-outlined text-[18px] text-[var(--hp-accent)] shrink-0">
          shield
        </span>
        <div className="text-[11px] text-[var(--hp-text-secondary)]">
          <span className="font-semibold text-[var(--hp-text)]">Zero Dark Patterns Policy:</span>{' '}
          All automated pipeline actions adhere to DPDPA 2023 regulations. Unsolicited outreach without verifiable public provenance or documented consent is blocked by system governance.
        </div>
      </div>
    </div>
  );
};
