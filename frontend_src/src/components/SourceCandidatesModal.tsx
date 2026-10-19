import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';

interface SourcingLog {
  time: string;
  message: string;
  type?: 'info' | 'success' | 'warn' | 'error';
}

export const SourceCandidatesModal: React.FC = () => {
  const { isSourceModalOpen, setIsSourceModalOpen, selectedRole, refreshCandidates, refreshRoles, triggerToast, setSelectedStage } = useApp();
  
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [targetCount, setTargetCount] = useState<number>(10);
  const [customKeywords, setCustomKeywords] = useState<string>('python, fastapi, docker, postgresql');
  const [evaluatedCount, setEvaluatedCount] = useState<number>(0);
  const [stagedCount, setStagedCount] = useState<number>(0);
  const [rejectedCount, setRejectedCount] = useState<number>(0);
  const [logs, setLogs] = useState<SourcingLog[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-fill keywords from role when modal opens
  useEffect(() => {
    if (isSourceModalOpen && selectedRole) {
      const title = (selectedRole.title || '').toLowerCase();
      const existingKws = selectedRole.sourcingCriteria?.keywords;
      let defaultKws = '';

      if (Array.isArray(existingKws) && existingKws.length > 0) {
        defaultKws = existingKws.join(', ');
      } else if (title.includes('product') || title.includes('manager')) {
        defaultKws = 'product, agile, scrum, roadmap';
      } else if (title.includes('frontend') || title.includes('react') || title.includes('ui')) {
        defaultKws = 'react, typescript, nextjs, tailwind';
      } else if (title.includes('devops') || title.includes('cloud') || title.includes('sre')) {
        defaultKws = 'docker, kubernetes, aws, cicd';
      } else if (title.includes('ai') || title.includes('ml') || title.includes('machine')) {
        defaultKws = 'python, pytorch, llm, machine learning';
      } else if (title.includes('data')) {
        defaultKws = 'python, sql, spark, postgresql';
      } else if (title.includes('backend') || title.includes('engineer') || title.includes('developer')) {
        defaultKws = 'python, fastapi, docker, postgresql';
      } else {
        // Fallback: derive keywords directly from role title
        const words = title.split(/[^a-z0-9]+/i).filter(w => w.length >= 3);
        defaultKws = words.length > 0 ? words.join(', ') : 'developer, software';
      }
      setCustomKeywords(defaultKws);
    }
  }, [isSourceModalOpen, selectedRole]);

  const addLog = (message: string, type: 'info' | 'success' | 'warn' | 'error' = 'info') => {
    const timeStr = new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false });
    setLogs(prev => [...prev, { time: `[${timeStr} IST]`, message, type }]);
  };

  const handleStartSourcing = async () => {
    setIsRunning(true);
    setLogs([]);
    setEvaluatedCount(0);
    setStagedCount(0);
    setRejectedCount(0);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const keywords = customKeywords.split(',').map(s => s.trim()).filter(Boolean);
    const roleId = selectedRole.id;

    addLog(`Initiating live GitHub sourcing for ${selectedRole.title}...`, 'info');

    try {
      const apiKey = sessionStorage.getItem('hirepath_api_key') || 'hirepath_dev_key_2026';
      const response = await fetch('http://localhost:8000/api/scout/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Api-Key': apiKey
        },
        body: JSON.stringify({
          role_id: parseInt(roleId),
          keywords,
          max_candidates: targetCount
        }),
        signal: abortController.signal
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${await response.text()}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const dataStr = line.replace(/^data:\s*/, '').trim();
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);
              if (data.event === 'candidate_found' && data.candidate) {
                setStagedCount(c => c + 1);
                setEvaluatedCount(c => c + 1);
                addLog(`Staged candidate: ${data.candidate.name} (${data.candidate.location || 'Maharashtra'}) · Score ${Math.round(data.candidate.score)}/100`, 'success');
              } else if (data.event === 'completed') {
                addLog(data.message || 'Live sourcing run completed.', 'success');
              } else if (data.event === 'done') {
                addLog('Live agent stdout stream closed.', 'info');
              } else if (data.message) {
                const isReject = data.message.includes('Rejected') || data.message.includes('Skipped') || data.message.includes('mismatch');
                if (isReject) {
                  setRejectedCount(c => c + 1);
                  setEvaluatedCount(c => c + 1);
                  addLog(data.message, 'warn');
                } else {
                  addLog(data.message, 'info');
                }
              }
            } catch (err) {
              // Non-json chunk
            }
          }
        }
      }

      await refreshRoles();
      await refreshCandidates();
      setSelectedStage('sourced');
      triggerToast({ message: 'Live candidate scouting completed! Loaded into pipeline.', type: 'success' });
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        addLog(`Error: ${e.message}`, 'error');
        triggerToast({ message: `Scouting failed: ${e.message}`, type: 'danger' });
      } else {
        addLog('Sourcing cancelled by user.', 'warn');
      }
    } finally {
      setIsRunning(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsRunning(false);
  };

  const handleFinish = async () => {
    setIsSourceModalOpen(false);
    await refreshRoles();
    await refreshCandidates();
    // New candidates are added to 'sourced' stage - show them immediately
    setSelectedStage('sourced');
  };

  if (!isSourceModalOpen) return null;

  const progressPercent = Math.min(100, targetCount > 0 ? Math.round((stagedCount / targetCount) * 100) : 0);

  return (
    <div className="fixed inset-0 z-50 bg-[#14181D]/40 backdrop-blur-[1px] flex items-center justify-center p-space-md overflow-y-auto">
      <div className="w-full max-w-[760px] bg-surface rounded-xl shadow-[0_8px_24px_rgba(20,24,29,0.14)] border border-border flex flex-col overflow-hidden max-h-[92vh] my-auto animate-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="p-space-xl pb-space-md bg-surface flex flex-col gap-space-sm border-b border-border">
          <div className="flex items-start justify-between">
            <div className="flex flex-col gap-0.5">
              <h2 className="font-section-title text-section-title text-text font-bold">
                Source candidates (Live GitHub Agent)
              </h2>
              <p className="font-caption text-caption text-text-secondary">
                {selectedRole.title} · Live public profile scouting
              </p>
            </div>
            <button
              type="button"
              onClick={handleFinish}
              aria-label="Close modal and view candidates"
              className="w-8 h-8 rounded-lg flex items-center justify-center text-text-tertiary hover:text-text hover:bg-subtle transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-space-xl overflow-y-auto space-y-space-md">
          {/* Active parameters & search settings */}
          <div className="bg-subtle rounded-lg p-space-md flex flex-col gap-space-sm border border-border/40">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs text-text-secondary font-caption text-caption uppercase tracking-wider font-semibold">
                <span className="material-symbols-outlined text-[14px]">tune</span>
                Live search criteria
              </div>
              <div className="flex items-center gap-2">
                <span className="text-caption text-text-tertiary font-caption">Target:</span>
                <input
                  type="number"
                  min="1"
                  max="30"
                  disabled={isRunning}
                  value={targetCount}
                  onChange={(e) => setTargetCount(Math.max(1, parseInt(e.target.value) || 10))}
                  className="w-16 h-7 px-2 text-center text-caption font-semibold bg-surface border border-border rounded text-text outline-none focus:border-accent"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[12px] font-caption text-text-tertiary">Keywords (comma separated):</label>
              <input
                type="text"
                disabled={isRunning}
                value={customKeywords}
                onChange={(e) => setCustomKeywords(e.target.value)}
                placeholder="python, fastapi, docker, postgresql"
                className="h-8 px-3 text-caption bg-surface border border-border rounded text-text outline-none focus:border-accent"
              />
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-text-tertiary">
                Location: <strong className="text-text">{selectedRole.location || 'Pune / Maharashtra'}</strong> · Source: <strong className="text-text">GitHub Public API</strong>
              </span>
              {!isRunning ? (
                <button
                  type="button"
                  onClick={handleStartSourcing}
                  className="h-8 px-4 rounded bg-accent text-on-accent text-caption font-semibold hover:bg-accent-hover transition-colors flex items-center gap-1 shadow-sm cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[14px]">play_arrow</span>
                  <span>Start Live Sourcing</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleStop}
                  className="h-8 px-4 rounded bg-danger text-white text-caption font-semibold hover:bg-red-700 transition-colors flex items-center gap-1 shadow-sm cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[14px]">stop</span>
                  <span>Stop Sourcing</span>
                </button>
              )}
            </div>
          </div>

          {/* Metrics Counter Bento Grid */}
          <div className="grid grid-cols-3 gap-space-sm">
            <div className="bg-subtle p-space-md rounded-lg flex flex-col border border-border/40">
              <span className="font-caption text-caption text-text-tertiary">Profiles Evaluated</span>
              <span className="font-score-numerals text-[20px] leading-tight font-bold text-text mt-1">
                {evaluatedCount}
              </span>
              <span className="text-[11px] leading-tight text-text-secondary mt-0.5">Scanned from GitHub</span>
            </div>

            <div className="bg-success-tint p-space-md rounded-lg flex flex-col border border-success/20">
              <span className="font-caption text-caption text-success font-medium flex items-center justify-between">
                <span>Staged (Accepted)</span>
                <span className="material-symbols-outlined text-[14px]">check_circle</span>
              </span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="font-score-numerals text-[20px] leading-tight font-bold text-success">
                  {stagedCount}
                </span>
                <span className="font-score-numerals text-caption text-success">/ {targetCount} target</span>
              </div>
              <span className="text-[11px] leading-tight text-success mt-0.5">Saved into live DB</span>
            </div>

            <div className="bg-subtle p-space-md rounded-lg flex flex-col border border-border/40">
              <span className="font-caption text-caption text-text-tertiary">Excluded</span>
              <span className="font-score-numerals text-[20px] leading-tight font-bold text-text-secondary mt-1">
                {rejectedCount}
              </span>
              <span className="text-[11px] leading-tight text-text-tertiary mt-0.5">Location / skill mismatch</span>
            </div>
          </div>

          {/* Progress bar */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-caption font-caption">
              <span className="text-text-secondary font-medium">Scouting Progress</span>
              <span className="font-score-numerals text-accent font-semibold">{progressPercent}%</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-subtle overflow-hidden relative border border-border/30">
              <div
                className="h-full bg-accent rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progressPercent}%` }}
              ></div>
            </div>
          </div>

          {/* Realtime Live Terminal Log */}
          <div className="bg-[#17191C] rounded-lg overflow-hidden flex flex-col shadow-inner border border-dark-border">
            <div className="px-space-md py-2 bg-[#1E2226] flex items-center justify-between border-b border-dark-border">
              <div className="flex items-center gap-space-xs text-[#E6E8EB] font-caption text-caption font-semibold">
                <span className="material-symbols-outlined text-[14px] text-dark-accent">terminal</span>
                <span>Live agent stdout stream</span>
              </div>
              <div className="flex items-center gap-1.5 font-code-inline text-[11px] text-dark-text-secondary">
                <span className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-dark-success animate-pulse' : 'bg-gray-500'}`}></span>
                <span>{isRunning ? 'Realtime (Streaming)' : 'Ready'}</span>
              </div>
            </div>

            <div className="p-space-md font-code-inline text-[12px] leading-relaxed text-[#A7AFB8] space-y-1 max-h-[160px] overflow-y-auto">
              {logs.length === 0 ? (
                <div className="text-[#5F6873] py-4 text-center">
                  Click 'Start Live Sourcing' to initiate real-time GitHub public profile scouting.
                </div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className="text-[#5F6873] flex-shrink-0">{log.time}</span>
                    <span className={
                      log.type === 'success' ? 'text-dark-success' :
                      log.type === 'warn' ? 'text-warning' :
                      log.type === 'error' ? 'text-danger font-semibold' : 'text-[#E6E8EB]'
                    }>
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-space-xl py-space-md bg-surface border-t border-border flex items-center justify-between gap-space-lg">
          <div className="flex items-center gap-space-xs font-caption text-caption text-text-tertiary">
            <span className="material-symbols-outlined text-[16px]">person</span>
            <span><strong className="text-text font-semibold">{stagedCount}</strong> candidates staged</span>
          </div>

          <div className="flex items-center gap-space-md">
            <button
              type="button"
              onClick={handleFinish}
              className="h-9 px-space-lg rounded-lg bg-surface hover:bg-subtle text-text font-body text-body font-semibold transition-colors flex items-center gap-space-xs border border-border-strong shadow-sm cursor-pointer"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={handleFinish}
              className="h-9 px-space-lg rounded-lg bg-accent text-on-accent font-body text-body font-semibold hover:bg-accent-hover transition-colors flex items-center gap-space-xs shadow-sm cursor-pointer"
            >
              <span>View candidates</span>
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
