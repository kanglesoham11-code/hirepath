import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const EditRoleModal: React.FC = () => {
  const { isEditRoleModalOpen, setIsEditRoleModalOpen, selectedRole, updateExistingRole } = useApp();

  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('Core Platform');
  const [location, setLocation] = useState('Pune, Maharashtra (Hybrid)');
  const [hiringLead, setHiringLead] = useState('recruiter@company.com');
  const [requiredSkills, setRequiredSkills] = useState('');
  const [status, setStatus] = useState<'active' | 'paused' | 'closed'>('active');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (selectedRole && isEditRoleModalOpen) {
      setTitle(selectedRole.title || '');
      setDepartment(selectedRole.department || 'Core Platform');
      setLocation(selectedRole.location || 'Pune, Maharashtra (Hybrid)');
      setHiringLead(selectedRole.hiringLead || 'recruiter@company.com');
      setStatus((selectedRole.status as any) || 'active');
      const keywords = selectedRole.sourcingCriteria?.keywords;
      if (Array.isArray(keywords)) {
        setRequiredSkills(keywords.join(', '));
      } else {
        setRequiredSkills('Python, Kubernetes, Distributed Systems, Go');
      }
    }
  }, [selectedRole, isEditRoleModalOpen]);

  if (!isEditRoleModalOpen || !selectedRole) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      const keywords = requiredSkills
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);

      await updateExistingRole(selectedRole.id, {
        title: title.trim(),
        department,
        location,
        hiringLead,
        status,
        sourcingCriteria: {
          ...(selectedRole.sourcingCriteria || {}),
          keywords,
          location,
          targetTitles: [title.trim()]
        }
      });
      setIsEditRoleModalOpen(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
      <div 
        className="w-full max-w-lg bg-[var(--hp-surface)] rounded-xl border border-[var(--hp-border)] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-[var(--hp-border)] flex items-center justify-between bg-[var(--hp-subtle)]">
          <div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px] text-[var(--hp-accent)]">edit_document</span>
              <h2 className="text-base font-bold text-[var(--hp-text)]">Edit Requisition Parameters</h2>
            </div>
            <p className="text-xs text-[var(--hp-text-muted)] mt-0.5">
              {selectedRole.reqId || `REQ-${selectedRole.id}`} · Direct live database synchronization
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsEditRoleModalOpen(false)}
            className="p-1.5 rounded-lg text-[var(--hp-text-muted)] hover:text-[var(--hp-text)] hover:bg-[var(--hp-canvas)] transition-colors cursor-pointer"
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
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
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
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] focus:outline-hidden"
              >
                <option value="Core Platform">Core Platform</option>
                <option value="Infrastructure & SRE">Infrastructure & SRE</option>
                <option value="Product Engineering">Product Engineering</option>
                <option value="Security & Compliance">Security & Compliance</option>
                <option value="Machine Learning">Machine Learning</option>
                <option value="Frontend Engineering">Frontend Engineering</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as any)}
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] focus:outline-hidden"
              >
                <option value="active">Active (Sourcing Open)</option>
                <option value="paused">Paused</option>
                <option value="closed">Closed (Filled)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
                Target Location / Mode
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
                Hiring Lead Email
              </label>
              <input
                type="email"
                value={hiringLead}
                onChange={(e) => setHiringLead(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] focus:outline-hidden"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
              Required Skills & Sourcing Criteria (comma separated)
            </label>
            <input
              type="text"
              value={requiredSkills}
              onChange={(e) => setRequiredSkills(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] focus:outline-hidden"
            />
            <p className="text-[11px] text-[var(--hp-text-muted)] mt-1">
              Live GitHub and StackOverflow scouring agents use these keywords to evaluate candidates.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-[var(--hp-subtle)] border border-[var(--hp-border)] text-[11px] text-[var(--hp-text-secondary)] flex items-start gap-2">
            <span className="material-symbols-outlined text-[16px] text-[var(--hp-accent)] shrink-0 mt-0.5">verified_user</span>
            <div>
              Changes are immediately synchronized into the SQLite ledger and broadcast to all connected recruitment pipeline clients.
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[var(--hp-border)]">
            <button
              type="button"
              onClick={() => setIsEditRoleModalOpen(false)}
              className="px-4 py-2 text-xs font-medium rounded-md border border-[var(--hp-border)] bg-[var(--hp-surface)] hover:bg-[var(--hp-subtle)] text-[var(--hp-text)] cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-xs font-semibold rounded-md bg-[var(--hp-accent)] text-white hover:bg-[var(--hp-accent-hover)] cursor-pointer transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              {isSubmitting ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block"></span>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[15px]">save</span>
                  <span>Save Changes</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
