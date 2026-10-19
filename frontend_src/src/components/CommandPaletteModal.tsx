import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';

interface ActionItem {
  id: string;
  title: string;
  category: 'Navigation' | 'Actions' | 'Roles' | 'Security';
  icon: string;
  shortcut?: string;
  action: () => void;
}

export const CommandPaletteModal: React.FC = () => {
  const {
    isCommandPaletteOpen,
    setIsCommandPaletteOpen,
    setCurrentView,
    roles,
    selectRole,
    setIsSourceModalOpen,
    openRecordConsentModal,
    setIsNewRoleModalOpen,
    exportAuditCSV,
    toggleDarkMode,
    setIsLocked,
    setIsShortcutsOpen
  } = useApp();

  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isCommandPaletteOpen) {
      setSearch('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isCommandPaletteOpen]);

  const actions: ActionItem[] = [
    {
      id: 'nav-roles',
      title: 'Go to Requisitions Directory',
      category: 'Navigation',
      icon: 'dashboard',
      shortcut: 'G R',
      action: () => setCurrentView('roles')
    },
    {
      id: 'nav-activity',
      title: 'Go to Activity & Audit Feed',
      category: 'Navigation',
      icon: 'receipt_long',
      shortcut: 'G A',
      action: () => setCurrentView('activity')
    },
    {
      id: 'nav-compliance',
      title: 'Go to Compliance & Consent Records',
      category: 'Navigation',
      icon: 'verified_user',
      shortcut: 'G C',
      action: () => setCurrentView('compliance')
    },
    {
      id: 'nav-settings',
      title: 'Go to Settings & System Integrations',
      category: 'Navigation',
      icon: 'settings',
      shortcut: 'G S',
      action: () => setCurrentView('settings')
    },
    {
      id: 'act-source',
      title: 'Launch Candidate Sourcing Engine',
      category: 'Actions',
      icon: 'bolt',
      shortcut: 'S',
      action: () => setIsSourceModalOpen(true)
    },
    {
      id: 'act-record-consent',
      title: 'Record Candidate Lawful Consent',
      category: 'Actions',
      icon: 'assignment_turned_in',
      shortcut: 'C',
      action: () => openRecordConsentModal()
    },
    {
      id: 'act-new-role',
      title: 'Create New Requisition',
      category: 'Actions',
      icon: 'add_box',
      shortcut: 'N',
      action: () => setIsNewRoleModalOpen(true)
    },
    {
      id: 'act-export',
      title: 'Export Immutable Audit CSV',
      category: 'Actions',
      icon: 'download',
      shortcut: 'E',
      action: () => exportAuditCSV()
    },
    {
      id: 'sec-lock',
      title: 'Lock Workspace & Mask PII',
      category: 'Security',
      icon: 'lock',
      shortcut: 'L',
      action: () => setIsLocked(true)
    },
    {
      id: 'sec-theme',
      title: 'Toggle Dark / Light Theme',
      category: 'Actions',
      icon: 'dark_mode',
      shortcut: 'T',
      action: () => toggleDarkMode()
    },
    {
      id: 'sec-shortcuts',
      title: 'View Keyboard Shortcuts',
      category: 'Navigation',
      icon: 'keyboard',
      shortcut: '?',
      action: () => setIsShortcutsOpen(true)
    },
    ...roles.map(role => ({
      id: `role-${role.id}`,
      title: `Switch to ${role.title} (${role.reqId})`,
      category: 'Roles' as const,
      icon: 'badge',
      action: () => {
        selectRole(role.id);
        setCurrentView('roles');
      }
    }))
  ];

  const filteredActions = actions.filter(action =>
    action.title.toLowerCase().includes(search.toLowerCase()) ||
    action.category.toLowerCase().includes(search.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  if (!isCommandPaletteOpen) return null;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % (filteredActions.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + (filteredActions.length || 1)) % (filteredActions.length || 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredActions[selectedIndex]) {
        filteredActions[selectedIndex].action();
        setIsCommandPaletteOpen(false);
      }
    } else if (e.key === 'Escape') {
      setIsCommandPaletteOpen(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/60 backdrop-blur-xs"
      onClick={() => setIsCommandPaletteOpen(false)}
    >
      <div 
        className="w-full max-w-xl bg-[var(--hp-surface)] rounded-xl border border-[var(--hp-border)] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-100"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-[var(--hp-border)]">
          <span className="material-symbols-outlined text-[20px] text-[var(--hp-text-muted)] mr-3">
            search
          </span>
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search roles, actions..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-transparent text-sm text-[var(--hp-text)] placeholder-[var(--hp-text-muted)] focus:outline-hidden"
          />
          <kbd className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[var(--hp-canvas)] text-[var(--hp-text-muted)] border border-[var(--hp-border)]">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 divide-y divide-transparent">
          {filteredActions.length > 0 ? (
            filteredActions.map((action, index) => {
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={action.id}
                  onClick={() => {
                    action.action();
                    setIsCommandPaletteOpen(false);
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                    isSelected 
                      ? 'bg-[var(--hp-accent)] text-white' 
                      : 'hover:bg-[var(--hp-subtle)] text-[var(--hp-text)]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={`material-symbols-outlined text-[18px] ${
                      isSelected ? 'text-white' : 'text-[var(--hp-text-muted)]'
                    }`}>
                      {action.icon}
                    </span>
                    <span className="text-xs font-medium">{action.title}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] uppercase font-mono px-1.5 py-0.5 rounded ${
                      isSelected ? 'bg-white/20 text-white' : 'bg-[var(--hp-canvas)] text-[var(--hp-text-muted)] border border-[var(--hp-border)]'
                    }`}>
                      {action.category}
                    </span>
                    {action.shortcut && (
                      <kbd className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        isSelected ? 'bg-white/20 text-white' : 'bg-[var(--hp-canvas)] text-[var(--hp-text-muted)] border border-[var(--hp-border)]'
                      }`}>
                        {action.shortcut}
                      </kbd>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-8 text-center text-xs text-[var(--hp-text-muted)]">
              No matching commands or actions found
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="px-4 py-2 border-t border-[var(--hp-border)] bg-[var(--hp-subtle)] flex items-center justify-between text-[11px] text-[var(--hp-text-muted)] font-mono">
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Dismiss</span>
          </div>
          <span>HirePath v2.4</span>
        </div>
      </div>
    </div>
  );
};
