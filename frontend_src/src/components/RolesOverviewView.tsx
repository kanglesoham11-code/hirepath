import React, { useState, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { Role } from '../types';

export const RolesOverviewView: React.FC = () => {
  const { 
    roles, 
    setCurrentView, 
    selectRole, 
    candidates, 
    setIsSourceModalOpen, 
    setIsNewRoleModalOpen 
  } = useApp();

  const [searchQuery, setSearchQuery] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const departments = useMemo(() => {
    const deps = new Set(roles.map(r => r.department));
    return ['ALL', ...Array.from(deps)];
  }, [roles]);

  const filteredRoles = useMemo(() => {
    return roles.filter(role => {
      const matchesSearch = 
        role.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        role.reqId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        role.location.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesDept = departmentFilter === 'ALL' || role.department === departmentFilter;
      const matchesStatus = statusFilter === 'ALL' || role.status === statusFilter;
      return matchesSearch && matchesDept && matchesStatus;
    });
  }, [roles, searchQuery, departmentFilter, statusFilter]);

  const stats = useMemo(() => {
    const total = roles.length;
    const active = roles.filter(r => r.status === 'active').length;
    const totalCandidates = candidates.length;
    const attentionNeeded = roles.filter(r => 
      r.healthStatus === 'Needs attention' || 
      r.healthStatus === 'At risk' ||
      r.healthStatus === 'needs_attention' || 
      r.healthStatus === 'at_risk'
    ).length;
    return { total, active, totalCandidates, attentionNeeded };
  }, [roles, candidates]);

  const handleOpenRole = (role: Role) => {
    selectRole(role.id);
    setCurrentView('roles');
  };

  const handleQuickSource = (e: React.MouseEvent, role: Role) => {
    e.stopPropagation();
    selectRole(role.id);
    setIsSourceModalOpen(true);
  };

  return (
    <div className="flex-1 min-h-screen bg-[var(--hp-canvas)] pb-16">
      {/* Page Header */}
      <div className="border-b border-[var(--hp-border)] bg-[var(--hp-surface)] px-8 py-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--hp-text-muted)] mb-1">
              <span>HIREPATH</span>
              <span>/</span>
              <span className="text-[var(--hp-text-secondary)] font-medium">REQUISITIONS DIRECTORY</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--hp-text)]">
              Open Roles & Pipeline Overview
            </h1>
            <p className="text-sm text-[var(--hp-text-secondary)] mt-0.5">
              Active engineering requisitions, candidate distributions, and DPDPA consent pipeline health.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsNewRoleModalOpen(true)}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-md bg-[var(--hp-accent)] text-white hover:bg-[var(--hp-accent-hover)] transition-colors shadow-xs cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">add</span>
              Create New Requisition
            </button>
          </div>
        </div>

        {/* Stats Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-[var(--hp-border)]">
          <div className="p-3.5 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-canvas)]">
            <div className="text-xs font-medium text-[var(--hp-text-muted)]">Active Requisitions</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-xl font-bold font-mono text-[var(--hp-text)]">{stats.active}</span>
              <span className="text-xs text-[var(--hp-text-muted)]">of {stats.total} total</span>
            </div>
          </div>

          <div className="p-3.5 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-canvas)]">
            <div className="text-xs font-medium text-[var(--hp-text-muted)]">Total Candidates In Flow</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-xl font-bold font-mono text-[var(--hp-text)]">{stats.totalCandidates}</span>
              <span className="text-xs text-[var(--hp-success)] flex items-center font-mono">
                <span className="material-symbols-outlined text-[13px] mr-0.5">verified</span>
                DPDPA tracked
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-canvas)]">
            <div className="text-xs font-medium text-[var(--hp-text-muted)]">Roles Needing Action</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-xl font-bold font-mono ${stats.attentionNeeded > 0 ? 'text-[var(--hp-warning)]' : 'text-[var(--hp-text)]'}`}>
                {stats.attentionNeeded}
              </span>
              <span className="text-xs text-[var(--hp-text-muted)]">latency or consent stall</span>
            </div>
          </div>

          <div className="p-3.5 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-canvas)]">
            <div className="text-xs font-medium text-[var(--hp-text-muted)]">Compliance Gate</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-xl font-bold font-mono text-[var(--hp-success)]">100%</span>
              <span className="text-xs text-[var(--hp-text-muted)]">ISO 27701 audited</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="px-8 py-6 space-y-6 max-w-7xl">
        {/* Filters & Search Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[var(--hp-surface)] p-3.5 rounded-lg border border-[var(--hp-border)]">
          <div className="flex flex-1 items-center gap-2.5">
            <div className="relative flex-1 max-w-md">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-[var(--hp-text-muted)]">
                search
              </span>
              <input
                type="text"
                placeholder="Search by role title, REQ-ID, or location..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] placeholder-[var(--hp-text-muted)] focus:outline-hidden focus:border-[var(--hp-accent)] transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-2 text-[var(--hp-text-muted)] hover:text-[var(--hp-text)] cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[14px]">close</span>
                </button>
              )}
            </div>

            <div className="h-5 w-px bg-[var(--hp-border)] hidden sm:block" />

            <div className="flex items-center gap-2">
              <select
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] cursor-pointer"
              >
                {departments.map(dept => (
                  <option key={dept} value={dept}>
                    {dept === 'ALL' ? 'All Departments' : dept}
                  </option>
                ))}
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] cursor-pointer"
              >
                <option value="ALL">All Statuses</option>
                <option value="active">Active Only</option>
                <option value="paused">Paused Only</option>
                <option value="closed">Closed / Filled</option>
              </select>
            </div>
          </div>

          <div className="text-xs font-mono text-[var(--hp-text-muted)] self-center">
            Showing {filteredRoles.length} of {roles.length} roles
          </div>
        </div>

        {/* Roles Grid / Table */}
        <div className="border border-[var(--hp-border)] rounded-lg bg-[var(--hp-surface)] overflow-hidden shadow-xs">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[var(--hp-border)] bg-[var(--hp-subtle)] text-[var(--hp-text-secondary)] font-medium">
                <th className="py-3 px-4 w-32 font-mono">REQ ID</th>
                <th className="py-3 px-4">ROLE TITLE & TEAM</th>
                <th className="py-3 px-4">LOCATION</th>
                <th className="py-3 px-4 text-center">STATUS</th>
                <th className="py-3 px-4">CANDIDATES</th>
                <th className="py-3 px-4">PIPELINE HEALTH</th>
                <th className="py-3 px-4 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--hp-border)]">
              {filteredRoles.map(role => {
                const roleCandidates = candidates.filter(c => c.roleId === role.id);
                const screenedCount = roleCandidates.filter(c => c.stage === 'screened' || c.stage === 'interview' || c.stage === 'outreach').length;

                return (
                  <tr
                    key={role.id}
                    onClick={() => handleOpenRole(role)}
                    className="hover:bg-[var(--hp-subtle)]/60 cursor-pointer transition-colors group"
                  >
                    <td className="py-3.5 px-4 font-mono font-medium text-[var(--hp-text-muted)] text-[11px]">
                      {role.reqId}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-[var(--hp-text)] group-hover:text-[var(--hp-accent)] transition-colors">
                        {role.title}
                      </div>
                      <div className="text-[11px] text-[var(--hp-text-muted)] flex items-center gap-2 mt-0.5">
                        <span>{role.department}</span>
                        <span>•</span>
                        <span>Created {role.createdAt ? new Date(role.createdAt).toLocaleDateString() : 'Active'}</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-[var(--hp-text-secondary)]">
                      <div className="flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[14px] text-[var(--hp-text-muted)]">
                          location_on
                        </span>
                        <span>{role.location}</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-medium ${
                        role.status === 'active'
                          ? 'bg-[var(--hp-success-bg)] text-[var(--hp-success)] border border-[var(--hp-success)]/20'
                          : role.status === 'paused'
                          ? 'bg-[var(--hp-warning-bg)] text-[var(--hp-warning)] border border-[var(--hp-warning)]/20'
                          : 'bg-neutral-100 dark:bg-neutral-800 text-[var(--hp-text-muted)] border border-[var(--hp-border)]'
                      }`}>
                        {role.status.toUpperCase()}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-baseline gap-1.5 font-mono">
                        <span className="font-semibold text-sm text-[var(--hp-text)]">{roleCandidates.length}</span>
                        <span className="text-[11px] text-[var(--hp-text-muted)]">({screenedCount} screened)</span>
                      </div>
                      {/* Mini stage bar */}
                      <div className="w-24 h-1.5 bg-[var(--hp-border)] rounded-full overflow-hidden flex mt-1">
                        <div 
                          className="bg-blue-500 h-full" 
                          style={{ width: `${Math.min(100, (roleCandidates.length / 15) * 100)}%` }} 
                        />
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      {(role.healthStatus === 'Healthy' || role.healthStatus === 'Optimal' || role.healthStatus === 'healthy') ? (
                        <div className="flex items-center gap-1.5 text-[var(--hp-success)] font-medium text-[11px]">
                          <span className="material-symbols-outlined text-[15px]">check_circle</span>
                          <span>Healthy ({role.healthScore}%)</span>
                        </div>
                      ) : (role.healthStatus === 'Needs attention' || role.healthStatus === 'needs_attention') ? (
                        <div className="flex items-center gap-1.5 text-[var(--hp-warning)] font-medium text-[11px]">
                          <span className="material-symbols-outlined text-[15px]">warning</span>
                          <span>Needs Attention ({role.healthScore}%)</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-[var(--hp-danger)] font-medium text-[11px]">
                          <span className="material-symbols-outlined text-[15px]">error</span>
                          <span>At Risk ({role.healthScore}%)</span>
                        </div>
                      )}
                      <div className="text-[10px] text-[var(--hp-text-muted)] font-mono mt-0.5">
                        Latency: {role.pipelineLatencyDays ?? 1.4}d
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={(e) => handleQuickSource(e, role)}
                          className="px-2 py-1 text-[11px] font-medium rounded border border-[var(--hp-border)] bg-[var(--hp-surface)] hover:bg-[var(--hp-subtle)] text-[var(--hp-text)] flex items-center gap-1 cursor-pointer transition-colors"
                          title="Source candidates for this requisition"
                        >
                          <span className="material-symbols-outlined text-[13px]">bolt</span>
                          Source
                        </button>

                        <button
                          onClick={() => handleOpenRole(role)}
                          className="px-2 py-1 text-[11px] font-medium rounded bg-[var(--hp-accent)]/10 text-[var(--hp-accent)] hover:bg-[var(--hp-accent)]/20 flex items-center gap-1 cursor-pointer transition-colors"
                        >
                          <span>Workspace</span>
                          <span className="material-symbols-outlined text-[13px]">arrow_forward</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}

              {filteredRoles.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[var(--hp-text-muted)]">
                    <span className="material-symbols-outlined text-4xl mb-2 text-[var(--hp-text-muted)]/50 block">
                      work_off
                    </span>
                    <p className="font-medium text-sm text-[var(--hp-text)]">No matching requisitions found</p>
                    <p className="text-xs text-[var(--hp-text-muted)] mt-1">
                      Try adjusting your search criteria or create a new requisition.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
