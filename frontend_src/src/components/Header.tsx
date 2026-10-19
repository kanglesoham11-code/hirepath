import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const Header: React.FC = () => {
  const { 
    currentView, 
    setCurrentView, 
    selectedRole, 
    setIsCommandPaletteOpen,
    isDarkMode,
    toggleDarkMode
  } = useApp();

  const [currentTime, setCurrentTime] = useState<string>('11:42');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      // IST time formatting
      const hours = now.getHours().toString().padStart(2, '0');
      const minutes = now.getMinutes().toString().padStart(2, '0');
      setCurrentTime(`${hours}:${minutes}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 30000);
    return () => clearInterval(interval);
  }, []);

  const renderBreadcrumb = () => {
    switch (currentView) {
      case 'roles':
        return (
          <div className="flex items-center gap-space-sm text-body font-body min-w-0 flex-shrink-0">
            <span className="text-text font-semibold">Roles</span>
            <span className="text-text-tertiary">/</span>
            <span 
              onClick={() => setCurrentView('roles')}
              className="text-text font-medium truncate cursor-pointer hover:text-accent"
            >
              {selectedRole?.title || 'Roles'}
            </span>
          </div>
        );
      case 'activity':
        return (
          <div className="flex items-center gap-space-sm text-body font-body min-w-0 flex-shrink-0">
            <span className="text-text-tertiary cursor-pointer hover:text-text" onClick={() => setCurrentView('roles')}>Roles</span>
            <span className="text-text-tertiary">/</span>
            <span className="text-text truncate font-semibold">Global Audit Feed</span>
          </div>
        );
      case 'compliance':
        return (
          <div className="flex items-center gap-space-sm text-body font-body min-w-0 flex-shrink-0">
            <span className="text-text-tertiary cursor-pointer hover:text-text" onClick={() => setCurrentView('roles')}>Compliance</span>
            <span className="text-text-tertiary">/</span>
            <span className="text-text font-medium truncate">Consent &amp; Audit Records</span>
          </div>
        );
      case 'settings':
        return (
          <div className="flex items-center gap-space-sm text-body font-body min-w-0 flex-shrink-0">
            <span className="text-text-tertiary cursor-pointer hover:text-text" onClick={() => setCurrentView('roles')}>Settings</span>
            <span className="text-text-tertiary">/</span>
            <span className="text-text font-medium truncate">System Integrations &amp; Health</span>
          </div>
        );
      case 'privacy':
        return (
          <div className="flex items-center gap-space-sm text-body font-body min-w-0 flex-shrink-0">
            <span className="text-text-tertiary cursor-pointer hover:text-text" onClick={() => setCurrentView('roles')}>Compliance</span>
            <span className="text-text-tertiary">/</span>
            <span className="text-text font-medium truncate">Candidate Privacy Portal</span>
          </div>
        );
      default:
        return <span className="text-text font-semibold">HirePath</span>;
    }
  };

  return (
    <header className="fixed top-0 left-[240px] right-0 h-14 bg-surface z-30 px-space-xl flex items-center justify-between gap-space-lg border-b border-border shadow-[0_1px_8px_rgba(0,0,0,0.04)] select-none">
      {/* Left Breadcrumb */}
      {renderBreadcrumb()}

      {/* Middle Command Bar Search */}
      <div className="flex-1 max-w-[480px] mx-space-lg hidden md:block">
        <div 
          onClick={() => setIsCommandPaletteOpen(true)}
          className="relative w-full flex items-center cursor-pointer group"
        >
          <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute left-space-md pointer-events-none group-hover:text-text transition-colors">
            search
          </span>
          <input
            readOnly
            className="w-full h-10 pl-9 pr-space-md bg-surface text-body font-body text-text placeholder:text-text-tertiary rounded-lg border border-border shadow-[0_1px_8px_rgba(0,0,0,0.04)] focus:outline-none focus:ring-1 focus:ring-accent cursor-pointer group-hover:border-border-strong transition-all"
            placeholder="Search or run an action (⌘K)"
            type="text"
          />
          <kbd className="absolute right-3 px-1.5 py-0.5 rounded bg-subtle text-[11px] font-code-inline text-text-secondary border border-border">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right Telemetry & Profile */}
      <div className="flex items-center gap-space-lg flex-shrink-0">
        {/* Status indicator */}
        {currentView === 'settings' ? (
          <div className="flex items-center gap-space-xs px-space-md py-space-xs rounded-full bg-danger-tint text-danger text-caption font-caption">
            <span className="w-1.5 h-1.5 rounded-full bg-danger"></span>
            <span>1 service degraded</span>
          </div>
        ) : (
          <div className="flex items-center gap-space-xs px-space-md py-space-xs rounded-full bg-success-tint text-success text-caption font-caption">
            <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
            <span>Connected</span>
          </div>
        )}

        {/* Live Clock IST */}
        <span className="font-score-numerals text-caption text-text-secondary tracking-normal">
          IST · {currentTime}
        </span>

        {/* Dark Mode Quick Switcher */}
        <button
          type="button"
          onClick={toggleDarkMode}
          title={isDarkMode ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          className="w-8 h-8 rounded-lg flex items-center justify-center text-text-secondary hover:text-text hover:bg-subtle transition-colors"
        >
          <span className="material-symbols-outlined text-[18px]">
            {isDarkMode ? 'light_mode' : 'dark_mode'}
          </span>
        </button>

        {/* Profile Avatar */}
        <div 
          onClick={() => setCurrentView('settings')}
          className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary cursor-pointer hover:opacity-90 transition-opacity"
          title="Recruitment Ops (recruiter@company.com)"
        >
          <span className="material-symbols-outlined text-on-primary text-[18px]">
            person
          </span>
        </div>
      </div>
    </header>
  );
};
