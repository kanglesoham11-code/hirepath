import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Role } from '../types';

export const NewRoleModal: React.FC = () => {
  const { isNewRoleModalOpen, setIsNewRoleModalOpen, addNewRole } = useApp();

  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('Core Platform');
  const [location, setLocation] = useState('Pune, Maharashtra (Hybrid)');
  const [targetHeadcount, setTargetHeadcount] = useState(2);
  const [requiredSkills, setRequiredSkills] = useState('Go, PostgreSQL, Kafka, Distributed Systems, Redis');
  const [minExpYears, setMinExpYears] = useState(5);

  if (!isNewRoleModalOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const reqNum = Math.floor(1000 + Math.random() * 9000);
    const newRole: Role = {
      id: title.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
      reqId: `REQ-ENG-${reqNum}`,
      title: title.trim(),
      department,
      location,
      status: 'active',
      healthStatus: 'Healthy',
      healthScore: 92,
      candidateCount: 0,
      pipelineStages: {
        sourced: 0,
        screened: 0,
        outreach: 0,
        replied: 0,
        interview: 0,
        offer: 0,
        hired: 0,
        rejected: 0,
        stale: 0
      },
      pipelineLatencyDays: 1.2,
      totalSourced: 0,
      totalScreened: 0,
      totalOutreach: 0,
      totalReplied: 0,
      totalInterview: 0,
      totalOffer: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      sourcingCriteria: {
        keywords: requiredSkills.split(',').map(s => s.trim()).filter(Boolean),
        location,
        minYearsExperience: minExpYears,
        targetTitles: [title.trim()]
      }
    };

    addNewRole(newRole);
    setIsNewRoleModalOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
      <div 
        className="w-full max-w-lg bg-[var(--hp-surface)] rounded-xl border border-[var(--hp-border)] shadow-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-[var(--hp-border)] flex items-center justify-between bg-[var(--hp-subtle)]">
          <div>
            <h2 className="text-base font-bold text-[var(--hp-text)]">Create New Requisition</h2>
            <p className="text-xs text-[var(--hp-text-muted)] mt-0.5">
              DPDPA compliant hiring workspace with automated candidate sourcing
            </p>
          </div>
          <button
            onClick={() => setIsNewRoleModalOpen(false)}
            className="p-1 rounded text-[var(--hp-text-muted)] hover:text-[var(--hp-text)] hover:bg-[var(--hp-canvas)] transition-colors cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
              Role Title *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Senior Distributed Systems Engineer"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] focus:outline-hidden focus:border-[var(--hp-accent)]"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
                Department
              </label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)]"
              >
                <option value="Core Platform">Core Platform</option>
                <option value="Infrastructure & SRE">Infrastructure & SRE</option>
                <option value="Product Engineering">Product Engineering</option>
                <option value="Security & Compliance">Security & Compliance</option>
                <option value="Machine Learning">Machine Learning</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
              Required Skills & Technologies (comma separated)
            </label>
            <input
              type="text"
              value={requiredSkills}
              onChange={(e) => setRequiredSkills(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)]"
            />
            <p className="text-[11px] text-[var(--hp-text-muted)] mt-1">
              Used by the Sourcing Engine to query GitHub and developer repositories.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
                Min. Years Experience
              </label>
              <input
                type="number"
                min="0"
                max="20"
                value={minExpYears}
                onChange={(e) => setMinExpYears(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
                Target Headcount
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={targetHeadcount}
                onChange={(e) => setTargetHeadcount(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)]"
              />
            </div>
          </div>

          <div className="p-3 rounded-lg bg-[var(--hp-subtle)] border border-[var(--hp-border)] text-[11px] text-[var(--hp-text-secondary)] space-y-1">
            <div className="font-semibold flex items-center gap-1.5 text-[var(--hp-accent)]">
              <span className="material-symbols-outlined text-[15px]">verified_user</span>
              DPDPA Automated Compliance Protection Active
            </div>
            <div>
              Every sourced candidate will be recorded in the immutable SHA-256 ledger before outreach.
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[var(--hp-border)]">
            <button
              type="button"
              onClick={() => setIsNewRoleModalOpen(false)}
              className="px-4 py-2 text-xs font-medium rounded-md border border-[var(--hp-border)] bg-[var(--hp-surface)] hover:bg-[var(--hp-subtle)] text-[var(--hp-text)] cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold rounded-md bg-[var(--hp-accent)] text-white hover:bg-[var(--hp-accent-hover)] cursor-pointer transition-colors"
            >
              Initialize Requisition
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
