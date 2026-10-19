import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

export const LockScreenModal: React.FC = () => {
  const { isLocked, setIsLocked, triggerToast } = useApp();
  const [accessKey, setAccessKey] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  if (!isLocked) return null;

  const handleUnlock = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!accessKey.trim()) {
      setErrorMsg('Please enter an authorization key or click "Use Demo Master Key" below');
      return;
    }

    setIsLocked(false);
    triggerToast({
      title: 'Workspace Decrypted',
      message: 'PII access authorized under DPDPA Session #SEC-2026-DP.',
      type: 'success'
    });
  };

  const handleDemoUnlock = () => {
    setAccessKey('HP-MASTER-2026-AES256-KEY');
    setTimeout(() => {
      setIsLocked(false);
      triggerToast({
        title: 'Master Key Authenticated',
        message: 'Decrypted 18 candidate PII records and audit verification ledger.',
        type: 'success'
      });
    }, 200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
      <div 
        className="w-full max-w-md bg-[var(--hp-surface)] rounded-xl border border-[var(--hp-border)] shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top security banner */}
        <div className="bg-neutral-900 text-white px-6 py-5 border-b border-neutral-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[var(--hp-accent)]/20 border border-[var(--hp-accent)]/30 flex items-center justify-center text-[var(--hp-accent)]">
                <span className="material-symbols-outlined text-[18px]">lock</span>
              </div>
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide">Encrypted Security Gate</h3>
                <div className="text-[10px] font-mono text-neutral-400">HIREPATH PII VAULT</div>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
              PROTECTED
            </span>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div className="text-xs text-[var(--hp-text-secondary)] leading-relaxed">
            In compliance with <strong className="text-[var(--hp-text)]">DPDPA 2023</strong> data fiduciary rules, candidate email addresses, contact identifiers, and outbound communication logs are encrypted at rest with AES-256-GCM.
          </div>

          <form onSubmit={handleUnlock} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-[var(--hp-text)] mb-1">
                Recruiter Access Key / Security Token
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-[var(--hp-text-muted)]">
                  key
                </span>
                <input
                  type="password"
                  value={accessKey}
                  onChange={(e) => {
                    setAccessKey(e.target.value);
                    if (errorMsg) setErrorMsg('');
                  }}
                  placeholder="Enter access key (e.g. HP-MASTER-2026-KEY)"
                  className="w-full pl-9 pr-3 py-2 text-xs font-mono rounded-md bg-[var(--hp-canvas)] border border-[var(--hp-border)] text-[var(--hp-text)] focus:outline-hidden focus:border-[var(--hp-accent)]"
                  autoFocus
                />
              </div>
              {errorMsg && (
                <p className="text-[11px] text-[var(--hp-danger)] mt-1 flex items-center gap-1 font-mono">
                  <span className="material-symbols-outlined text-[13px]">error</span>
                  {errorMsg}
                </p>
              )}
            </div>

            <div className="flex gap-2 pt-1">
              <button
                type="submit"
                className="flex-1 py-2 px-3 rounded-md bg-[var(--hp-accent)] hover:bg-[var(--hp-accent-hover)] text-white text-xs font-semibold transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-xs"
              >
                <span className="material-symbols-outlined text-[15px]">lock_open</span>
                Authorize Access
              </button>
            </div>
          </form>

          <div className="pt-2 border-t border-[var(--hp-border)] flex flex-col gap-2">
            <button
              onClick={handleDemoUnlock}
              type="button"
              className="w-full py-2 px-3 rounded-md border border-dashed border-[var(--hp-accent)] bg-[var(--hp-accent)]/5 hover:bg-[var(--hp-accent)]/10 text-[var(--hp-accent)] text-xs font-semibold transition-colors cursor-pointer flex items-center justify-center gap-1.5"
            >
              <span className="material-symbols-outlined text-[15px]">flash_on</span>
              Quick Demo Unlock (Pre-fill Master Key)
            </button>

            <div className="flex items-center justify-between text-[10px] text-[var(--hp-text-muted)] font-mono pt-2">
              <span>Standard: AES-256-GCM</span>
              <span>Ledger: SHA-256</span>
              <span>ISO 27701</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
