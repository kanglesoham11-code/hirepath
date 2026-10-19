import React from 'react';
import { useApp } from '../context/AppContext';
import { NavigationTab } from '../types';

export const Sidebar: React.FC = () => {
  const { 
    currentView, 
    setCurrentView, 
    setIsShortcutsOpen, 
    isDarkMode, 
    toggleDarkMode, 
    setIsGateLocked 
  } = useApp();

  const navItems: Array<{ id: NavigationTab; label: string; icon: string }> = [
    { id: 'roles', label: 'Roles', icon: 'work_outline' },
    { id: 'activity', label: 'Activity', icon: 'history' },
    { id: 'compliance', label: 'Compliance', icon: 'verified_user' },
    { id: 'settings', label: 'Settings', icon: 'tune' }
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-[240px] bg-surface z-40 flex flex-col justify-between border-r border-border shadow-[0_1px_8px_rgba(0,0,0,0.04)] select-none">
      <div className="flex flex-col">
        {/* Brand header */}
        <div className="h-14 px-space-xl flex items-center justify-between bg-surface border-b border-border/40">
          <div 
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => setCurrentView('roles')}
          >
            <span className="font-section-title text-section-title text-text tracking-tight font-bold">
              HirePath
            </span>
          </div>
          {/* Subtle Theme Toggle in Brand Bar */}
          <button 
            type="button" 
            onClick={toggleDarkMode}
            title={isDarkMode ? 'Switch to Light mode' : 'Switch to Dark mode'}
            className="w-7 h-7 rounded flex items-center justify-center text-text-tertiary hover:text-text hover:bg-subtle transition-colors"
          >
            <span className="material-symbols-outlined text-[17px]">
              {isDarkMode ? 'light_mode' : 'dark_mode'}
            </span>
          </button>
        </div>

        {/* Primary Navigation */}
        <nav className="flex flex-col gap-space-xs px-space-sm pt-space-md">
          {navItems.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setCurrentView(item.id)}
                className={`flex items-center gap-space-md px-space-md py-space-sm rounded-lg transition-colors text-body font-body text-left ${
                  isActive
                    ? 'bg-subtle text-accent font-semibold shadow-sm'
                    : 'text-text-secondary hover:bg-subtle hover:text-text'
                }`}
              >
                <span className={`material-symbols-outlined text-[18px] ${isActive ? 'text-accent' : 'text-text-secondary'}`}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}

          {/* Privacy Portal Link */}
          <div className="pt-space-xs px-1">
            <div className="h-[1px] bg-border my-2"></div>
            <button
              type="button"
              onClick={() => setCurrentView('privacy')}
              className={`w-full flex items-center gap-space-md px-space-md py-space-sm rounded-lg transition-colors text-body font-body text-left ${
                currentView === 'privacy'
                  ? 'bg-subtle text-accent font-semibold'
                  : 'text-text-tertiary hover:bg-subtle hover:text-text'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">
                shield
              </span>
              <span className="text-[13px]">Privacy Portal</span>
              <span className="ml-auto text-[10px] font-caption bg-subtle px-1.5 py-0.5 rounded border border-border">
                Public
              </span>
            </button>
          </div>
        </nav>
      </div>

      {/* Footer Items */}
      <div className="p-space-lg bg-surface border-t border-border/40 flex flex-col gap-space-sm">
        {/* Shortcuts row */}
        <div 
          onClick={() => setIsShortcutsOpen(true)}
          className="flex items-center justify-between text-caption font-caption text-text-tertiary cursor-pointer hover:text-text transition-colors"
        >
          <span>Shortcuts</span>
          <kbd className="px-space-xs py-0.5 rounded bg-subtle font-code-inline text-code-inline text-text-secondary shadow-[0_1px_8px_rgba(0,0,0,0.04)] border border-border">
            ?
          </kbd>
        </div>

        {/* User Card */}
        <div className="flex items-center justify-between pt-space-xs group">
          <div className="flex items-center gap-space-sm min-w-0">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 text-on-primary">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-caption font-caption text-text font-medium truncate">
                recruiter@company.com
              </span>
              <span className="text-[11px] leading-[14px] text-text-tertiary truncate">
                Recruitment Ops
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsGateLocked(true)}
            title="Lock Console (Gate v2.4)"
            className="w-7 h-7 rounded opacity-60 hover:opacity-100 hover:bg-subtle text-text-secondary flex items-center justify-center transition-all"
          >
            <span className="material-symbols-outlined text-[16px]">lock</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
