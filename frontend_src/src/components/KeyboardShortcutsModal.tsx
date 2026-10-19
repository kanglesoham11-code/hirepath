import React from 'react';
import { useApp } from '../context/AppContext';

export const KeyboardShortcutsModal: React.FC = () => {
  const { isShortcutsOpen, setIsShortcutsOpen } = useApp();

  if (!isShortcutsOpen) return null;

  const shortcutGroups = [
    {
      title: 'Global & Navigation',
      shortcuts: [
        { key: '⌘ K / Ctrl K', desc: 'Open Command Palette' },
        { key: '?', desc: 'Open this Keyboard Shortcuts cheat sheet' },
        { key: 'ESC', desc: 'Close open modal, drawer, or clear selection' },
        { key: 'G then R', desc: 'Jump to Roles Directory' },
        { key: 'G then A', desc: 'Jump to Activity & Audit Log' },
        { key: 'G then C', desc: 'Jump to Compliance & Consent' },
        { key: 'G then S', desc: 'Jump to System Settings' },
      ]
    },
    {
      title: 'Candidate Actions',
      shortcuts: [
        { key: 'S', desc: 'Launch Sourcing Engine for current role' },
        { key: 'C', desc: 'Record Lawful DPDPA Consent modal' },
        { key: 'O', desc: 'Review & Dispatch Outreach' },
        { key: 'E', desc: 'Export Immutable SHA-256 Audit CSV' },
        { key: 'L', desc: 'Lock & encrypt workspace (Mask PII)' },
        { key: 'T', desc: 'Toggle Dark / Light Mode' },
      ]
    },
    {
      title: 'List & Drawer Navigation',
      shortcuts: [
        { key: 'J / ↓', desc: 'Navigate to next candidate in table' },
        { key: 'K / ↑', desc: 'Navigate to previous candidate in table' },
        { key: 'Space', desc: 'Toggle selection of current row' },
        { key: 'Enter', desc: 'Open Candidate Detail Drawer' },
      ]
    }
  ];

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
      onClick={() => setIsShortcutsOpen(false)}
    >
      <div 
        className="w-full max-w-lg bg-[var(--hp-surface)] rounded-xl border border-[var(--hp-border)] shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-[var(--hp-border)] flex items-center justify-between bg-[var(--hp-subtle)]">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px] text-[var(--hp-accent)]">
              keyboard
            </span>
            <h2 className="text-sm font-bold text-[var(--hp-text)]">Keyboard Shortcuts</h2>
          </div>
          <button
            onClick={() => setIsShortcutsOpen(false)}
            className="p-1 rounded text-[var(--hp-text-muted)] hover:text-[var(--hp-text)] cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {shortcutGroups.map(group => (
            <div key={group.title}>
              <h3 className="text-xs font-bold text-[var(--hp-text-muted)] uppercase tracking-wider mb-2.5 font-mono">
                {group.title}
              </h3>
              <div className="space-y-2">
                {group.shortcuts.map(item => (
                  <div key={item.key} className="flex items-center justify-between text-xs py-1">
                    <span className="text-[var(--hp-text-secondary)]">{item.desc}</span>
                    <kbd className="px-2 py-0.5 rounded font-mono text-[11px] font-semibold bg-[var(--hp-canvas)] text-[var(--hp-text)] border border-[var(--hp-border)] shadow-2xs">
                      {item.key}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="px-6 py-3 border-t border-[var(--hp-border)] bg-[var(--hp-subtle)] flex items-center justify-between text-xs text-[var(--hp-text-muted)]">
          <span>Press <kbd className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[var(--hp-canvas)] border border-[var(--hp-border)]">ESC</kbd> to dismiss</span>
          <span className="font-mono">HirePath Pro Shortcuts</span>
        </div>
      </div>
    </div>
  );
};
