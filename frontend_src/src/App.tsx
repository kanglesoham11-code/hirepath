import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { RoleWorkspaceView } from './components/RoleWorkspaceView';
import { RolesOverviewView } from './components/RolesOverviewView';
import { ActivityView } from './components/ActivityView';
import { ComplianceView } from './components/ComplianceView';
import { SettingsView } from './components/SettingsView';
import { PrivacyPortalView } from './components/PrivacyPortalView';
import { CandidateDetailDrawer } from './components/CandidateDetailDrawer';
import { SourceCandidatesModal } from './components/SourceCandidatesModal';
import { OutreachReviewModal } from './components/OutreachReviewModal';
import { ScheduleInterviewModal } from './components/ScheduleInterviewModal';
import { RecordConsentModal } from './components/RecordConsentModal';
import { ConsentProofModal } from './components/ConsentProofModal';
import { NewRoleModal } from './components/NewRoleModal';
import { EditRoleModal } from './components/EditRoleModal';
import { LockScreenModal } from './components/LockScreenModal';
import { CommandPaletteModal } from './components/CommandPaletteModal';
import { KeyboardShortcutsModal } from './components/KeyboardShortcutsModal';

const MainContent: React.FC = () => {
  const { currentView, undoToast, dismissToast } = useApp();
  const [roleViewMode, setRoleViewMode] = useState<'workspace' | 'overview'>('workspace');

  return (
    <div className="min-h-screen bg-[var(--hp-canvas)] text-[var(--hp-text)] flex">
      {/* 240px Fixed Sidebar */}
      <Sidebar />

      {/* Main Workspace Frame */}
      <div className="flex-1 ml-[240px] flex flex-col min-h-screen min-w-0">
        {/* Fixed Top Header */}
        <Header />

        {/* Content View Container with 56px top offset */}
        <main className="flex-1 mt-14 flex flex-col min-w-0">
          {/* Sub-navigation bar when on Roles view to easily switch between Directory and Role Workspace */}
          {currentView === 'roles' && (
            <div className="bg-[var(--hp-surface)] border-b border-[var(--hp-border)] px-8 py-2 flex items-center justify-between text-xs">
              <div className="flex items-center gap-1 bg-[var(--hp-subtle)] p-0.5 rounded-lg border border-[var(--hp-border)]">
                <button
                  onClick={() => setRoleViewMode('workspace')}
                  className={`px-3 py-1 rounded-md font-medium cursor-pointer transition-all flex items-center gap-1.5 ${
                    roleViewMode === 'workspace'
                      ? 'bg-[var(--hp-surface)] text-[var(--hp-accent)] shadow-xs font-semibold'
                      : 'text-[var(--hp-text-secondary)] hover:text-[var(--hp-text)]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[15px]">work</span>
                  Role Workspace (Pune Backend)
                </button>
                <button
                  onClick={() => setRoleViewMode('overview')}
                  className={`px-3 py-1 rounded-md font-medium cursor-pointer transition-all flex items-center gap-1.5 ${
                    roleViewMode === 'overview'
                      ? 'bg-[var(--hp-surface)] text-[var(--hp-accent)] shadow-xs font-semibold'
                      : 'text-[var(--hp-text-secondary)] hover:text-[var(--hp-text)]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[15px]">list_alt</span>
                  All Requisitions Directory
                </button>
              </div>

              <div className="hidden sm:flex items-center gap-2 text-[11px] font-mono text-[var(--hp-text-muted)]">
                <span className="w-2 h-2 rounded-full bg-[var(--hp-success)] inline-block animate-pulse"></span>
                <span>DPDPA 2023 Live Audit Ledger Enabled</span>
              </div>
            </div>
          )}

          {/* Active View Router */}
          {currentView === 'roles' && (
            roleViewMode === 'workspace' ? <RoleWorkspaceView /> : <RolesOverviewView />
          )}
          {currentView === 'activity' && <ActivityView />}
          {currentView === 'compliance' && <ComplianceView />}
          {currentView === 'settings' && <SettingsView />}
          {currentView === 'privacy' && <PrivacyPortalView />}
        </main>
      </div>

      {/* Global Modals & Drawers */}
      <CandidateDetailDrawer />
      <SourceCandidatesModal />
      <OutreachReviewModal />
      <ScheduleInterviewModal />
      <RecordConsentModal />
      <ConsentProofModal />
      <NewRoleModal />
      <EditRoleModal />
      <LockScreenModal />
      <CommandPaletteModal />
      <KeyboardShortcutsModal />

      {/* Toast Notification with Undo */}
      {undoToast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-lg bg-neutral-900 text-white shadow-2xl border border-neutral-700 animate-in slide-in-from-bottom-5 duration-200">
          <span className="material-symbols-outlined text-[20px] text-[var(--hp-accent)]">
            {undoToast.type === 'success' ? 'check_circle' : (undoToast.type === 'danger' || undoToast.type === 'warning') ? 'error' : 'info'}
          </span>
          <div className="text-xs">
            {undoToast.title && <div className="font-semibold text-white">{undoToast.title}</div>}
            <div className="text-neutral-300 text-[11px] mt-0.5">{undoToast.message}</div>
          </div>
          {undoToast.onUndo && (
            <button
              onClick={() => {
                undoToast.onUndo?.();
                dismissToast();
              }}
              className="ml-2 px-2.5 py-1 rounded bg-white/20 hover:bg-white/30 text-white text-xs font-semibold cursor-pointer transition-colors"
            >
              Undo
            </button>
          )}
          <button
            onClick={dismissToast}
            className="p-1 text-neutral-400 hover:text-white cursor-pointer ml-1"
          >
            <span className="material-symbols-outlined text-[15px]">close</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <MainContent />
    </AppProvider>
  );
}
