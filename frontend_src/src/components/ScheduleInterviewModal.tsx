import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const ScheduleInterviewModal: React.FC = () => {
  const { 
    isScheduleModalOpen, 
    setIsScheduleModalOpen, 
    scheduleCandidate, 
    selectedRole, 
    confirmScheduledInterview 
  } = useApp();

  const [round, setRound] = useState<string>('Technical Screen (Round 1)');
  const [duration, setDuration] = useState<string>('45 min');
  const [selectedSlot, setSelectedSlot] = useState<string>('11:00 – 11:45 IST');
  const [candidateNote, setCandidateNote] = useState<string>('');

  useEffect(() => {
    if (scheduleCandidate) {
      setCandidateNote(`Hi ${scheduleCandidate.name}, looking forward to discussing your background and the challenges we are solving at HirePath.`);
    }
  }, [scheduleCandidate]);

  if (!isScheduleModalOpen || !scheduleCandidate) return null;

  const candidate = scheduleCandidate;

  const handleCreateEvent = () => {
    confirmScheduledInterview(candidate.id, {
      round,
      duration,
      slot: selectedSlot,
      note: candidateNote
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-[rgba(20,24,29,0.24)] backdrop-blur-[2px] flex items-center justify-center p-space-md overflow-y-auto">
      {/* Centered Dialog Container (max-width: 560px) */}
      <div className="relative w-full max-w-[560px] my-auto bg-surface border border-border rounded-xl shadow-[0_8px_24px_rgba(20,24,29,0.14)] overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-space-xl pt-space-xl pb-space-md flex items-start justify-between bg-surface border-b border-border/40">
          <div className="flex flex-col gap-space-xs">
            <h2 className="font-section-title text-section-title text-text font-bold">
              Schedule interview
            </h2>
            <div className="flex items-center gap-space-xs font-caption text-caption text-text-secondary">
              <span>{selectedRole.title}</span>
              <span className="text-text-tertiary">·</span>
              <span className="font-code-inline text-code-inline text-text-tertiary">
                {selectedRole.reqId}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsScheduleModalOpen(false)}
            aria-label="Close dialog"
            className="w-8 h-8 rounded-lg flex items-center justify-center text-text-secondary hover:bg-subtle hover:text-text transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Dialog Body */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleCreateEvent();
          }}
          className="px-space-xl py-space-md flex flex-col gap-space-lg text-text max-h-[80vh] overflow-y-auto"
        >
          {/* Candidate Identity & Consent Banner */}
          <div className="bg-subtle rounded-lg p-space-md flex flex-col gap-space-sm border border-border/40">
            <div className="flex items-center justify-between gap-space-sm">
              <div className="flex items-center gap-space-sm min-w-0">
                <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-on-primary font-caption text-caption font-semibold flex-shrink-0">
                  {candidate.avatar}
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="font-subsection text-body font-semibold text-text truncate">
                    {candidate.name}
                  </span>
                  <span className="font-code-inline text-code-inline text-text-secondary truncate">
                    {candidate.email}
                  </span>
                </div>
              </div>
              <div className="inline-flex items-center gap-1.5 px-space-sm py-0.5 rounded-full bg-success-tint text-success font-caption text-caption border border-success/20 flex-shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-success"></span>
                <span>Consent recorded {candidate.consent.recordedDate || '12 Oct 2026'}</span>
              </div>
            </div>
            <div className="flex items-center justify-between pt-space-xs text-caption font-caption text-text-tertiary border-t border-border/30">
              <span>Location: {candidate.location}</span>
              <span className="font-score-numerals text-code-inline text-text-secondary">
                IST · UTC+05:30
              </span>
            </div>
          </div>

          {/* Round & Duration */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
            {/* Round */}
            <div className="flex flex-col gap-space-xs">
              <label className="font-caption text-caption text-text-secondary font-medium">
                Interview round
              </label>
              <div className="relative">
                <select
                  value={round}
                  onChange={(e) => setRound(e.target.value)}
                  className="w-full h-10 px-space-md pr-8 bg-surface text-body font-body text-text rounded-lg border border-border shadow-sm focus:outline-none focus:ring-1 focus:ring-accent appearance-none cursor-pointer"
                >
                  <option>Technical Screen (Round 1)</option>
                  <option>Systems &amp; Architecture (Round 2)</option>
                  <option>Leadership &amp; Values (Round 3)</option>
                </select>
                <span className="material-symbols-outlined text-[18px] text-text-tertiary absolute right-space-md top-1/2 -translate-y-1/2 pointer-events-none">
                  expand_more
                </span>
              </div>
            </div>

            {/* Duration Segmented */}
            <div className="flex flex-col gap-space-xs">
              <label className="font-caption text-caption text-text-secondary font-medium">
                Duration
              </label>
              <div className="grid grid-cols-3 h-10 p-0.5 bg-subtle rounded-lg text-caption font-caption border border-border">
                {['30 min', '45 min', '60 min'].map((dur) => (
                  <button
                    key={dur}
                    type="button"
                    onClick={() => setDuration(dur)}
                    className={`flex items-center justify-center rounded font-code-inline text-code-inline transition-colors ${
                      duration === dur
                        ? 'bg-surface text-accent font-semibold shadow-sm border border-border/50'
                        : 'text-text-secondary hover:text-text'
                    }`}
                  >
                    {dur}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Interviewers */}
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <label className="font-caption text-caption text-text-secondary font-medium">
                Interviewers
              </label>
              <button
                type="button"
                onClick={() => triggerToast({ title: "Interviewer Slot", message: "Added interviewer slot for swati.deshmukh@company.com", type: "info" })}
                className="font-caption text-caption text-accent hover:text-accent-hover font-semibold flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[15px]">add</span>
                <span>Add interviewer</span>
              </button>
            </div>
            <div className="flex items-center gap-space-sm p-space-sm bg-surface rounded-lg border border-border shadow-sm">
              <div className="w-6 h-6 rounded-full bg-primary-fixed text-primary flex items-center justify-center text-caption font-caption font-semibold flex-shrink-0">
                AR
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-body font-body text-text truncate">
                  anupama.rao@company.com <span className="text-text-tertiary text-caption font-caption">(Hiring Lead)</span>
                </p>
              </div>
              <span className="font-caption text-caption text-success bg-success-tint px-space-xs py-0.5 rounded border border-success/20">
                Lead
              </span>
            </div>
          </div>

          {/* Date & Slot Picker Section */}
          <div className="flex flex-col gap-space-sm">
            {/* Date Navigator Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs">
                <span className="font-subsection text-body font-semibold text-text">
                  Available slots
                </span>
                <span className="font-code-inline text-caption text-text-tertiary">
                  Wed 21 Oct 2026
                </span>
              </div>
              <div className="flex items-center gap-1 bg-subtle p-0.5 rounded-lg border border-border">
                <button
                  type="button"
                  aria-label="Previous day"
                  className="w-7 h-7 flex items-center justify-center rounded hover:bg-surface text-text-secondary"
                >
                  <span className="material-symbols-outlined text-[16px]">chevron_left</span>
                </button>
                <span className="font-code-inline text-caption px-space-xs text-text font-medium">
                  Today
                </span>
                <button
                  type="button"
                  aria-label="Next day"
                  className="w-7 h-7 flex items-center justify-center rounded hover:bg-surface text-text-secondary"
                >
                  <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                </button>
              </div>
            </div>

            {/* Timezone Notice */}
            <div className="flex items-center gap-space-xs px-space-md py-space-xs rounded-lg bg-subtle text-caption font-caption text-text-secondary border border-border/40">
              <span className="material-symbols-outlined text-[16px] text-accent">schedule</span>
              <span>Candidate is in Pune (UTC+05:30). Both participant calendars match IST.</span>
            </div>

            {/* Slots List */}
            <div className="flex flex-col gap-space-xs">
              {/* Slot 1 */}
              <label 
                className={`flex items-center justify-between p-space-md rounded-lg border transition-colors cursor-pointer ${
                  selectedSlot === '11:00 – 11:45 IST'
                    ? 'border-accent bg-subtle shadow-sm'
                    : 'border-border bg-surface hover:bg-subtle/50'
                }`}
              >
                <div className="flex items-center gap-space-md min-w-0">
                  <input
                    type="radio"
                    name="slot_choice"
                    checked={selectedSlot === '11:00 – 11:45 IST'}
                    onChange={() => setSelectedSlot('11:00 – 11:45 IST')}
                    className="w-4 h-4 text-accent accent-accent cursor-pointer"
                  />
                  <div className="flex flex-col">
                    <div className="flex items-center gap-space-sm">
                      <span className="font-score-numerals text-body font-semibold text-accent">
                        11:00 – 11:45 IST
                      </span>
                      <span className="px-space-xs py-0.5 rounded bg-accent/10 text-accent font-code-inline text-[11px] font-medium border border-accent/20">
                        Candidate matched
                      </span>
                    </div>
                    <span className="text-caption font-caption text-text-tertiary">
                      Interviewer: Available · Candidate local: 11:00 IST
                    </span>
                  </div>
                </div>
                <span className="w-2 h-2 rounded-full bg-success flex-shrink-0" title="Full availability"></span>
              </label>

              {/* Slot 2 */}
              <label 
                className={`flex items-center justify-between p-space-md rounded-lg border transition-colors cursor-pointer ${
                  selectedSlot === '14:30 – 15:15 IST'
                    ? 'border-accent bg-subtle shadow-sm'
                    : 'border-border bg-surface hover:bg-subtle/50'
                }`}
              >
                <div className="flex items-center gap-space-md min-w-0">
                  <input
                    type="radio"
                    name="slot_choice"
                    checked={selectedSlot === '14:30 – 15:15 IST'}
                    onChange={() => setSelectedSlot('14:30 – 15:15 IST')}
                    className="w-4 h-4 text-accent accent-accent cursor-pointer"
                  />
                  <div className="flex flex-col">
                    <span className="font-score-numerals text-body font-semibold text-text">
                      14:30 – 15:15 IST
                    </span>
                    <span className="text-caption font-caption text-text-tertiary">
                      Interviewer: Available · Candidate local: 14:30 IST
                    </span>
                  </div>
                </div>
                <span className="w-2 h-2 rounded-full bg-success flex-shrink-0" title="Full availability"></span>
              </label>

              {/* Slot 3 */}
              <label 
                className={`flex items-center justify-between p-space-md rounded-lg border transition-colors cursor-pointer ${
                  selectedSlot === '16:00 – 16:45 IST'
                    ? 'border-accent bg-subtle shadow-sm'
                    : 'border-border bg-surface hover:bg-subtle/50'
                }`}
              >
                <div className="flex items-center gap-space-md min-w-0">
                  <input
                    type="radio"
                    name="slot_choice"
                    checked={selectedSlot === '16:00 – 16:45 IST'}
                    onChange={() => setSelectedSlot('16:00 – 16:45 IST')}
                    className="w-4 h-4 text-accent accent-accent cursor-pointer"
                  />
                  <div className="flex flex-col">
                    <span className="font-score-numerals text-body font-semibold text-text">
                      16:00 – 16:45 IST
                    </span>
                    <span className="text-caption font-caption text-text-tertiary">
                      Interviewer: Available · Candidate local: 16:00 IST
                    </span>
                  </div>
                </div>
                <span className="w-2 h-2 rounded-full bg-success flex-shrink-0" title="Full availability"></span>
              </label>

              {/* Slot 4 (Tentative) */}
              <label 
                className={`flex items-center justify-between p-space-md rounded-lg border transition-colors cursor-pointer opacity-90 ${
                  selectedSlot === '17:30 – 18:15 IST'
                    ? 'border-accent bg-subtle shadow-sm'
                    : 'border-border bg-surface hover:bg-subtle/50'
                }`}
              >
                <div className="flex items-center gap-space-md min-w-0">
                  <input
                    type="radio"
                    name="slot_choice"
                    checked={selectedSlot === '17:30 – 18:15 IST'}
                    onChange={() => setSelectedSlot('17:30 – 18:15 IST')}
                    className="w-4 h-4 text-accent accent-accent cursor-pointer"
                  />
                  <div className="flex flex-col">
                    <div className="flex items-center gap-space-sm">
                      <span className="font-score-numerals text-body font-semibold text-text">
                        17:30 – 18:15 IST
                      </span>
                      <span className="px-space-xs py-0.5 rounded bg-warning-tint text-warning font-code-inline text-[11px] font-medium border border-warning/20">
                        1 soft conflict
                      </span>
                    </div>
                    <span className="text-caption font-caption text-text-tertiary">
                      Interviewer: Tentative · Candidate local: 17:30 IST
                    </span>
                  </div>
                </div>
                <span className="w-2 h-2 rounded-full bg-warning flex-shrink-0" title="Conflict flag"></span>
              </label>
            </div>
          </div>

          {/* Video meeting automatic generation */}
          <div className="flex items-center gap-space-sm text-caption font-caption text-text-secondary bg-surface rounded-lg p-space-sm border border-border shadow-sm">
            <span className="material-symbols-outlined text-[18px] text-accent flex-shrink-0">
              video_camera_front
            </span>
            <span className="truncate">Google Meet link will be generated and attached automatically</span>
          </div>

          {/* Note to candidate */}
          <div className="flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <label className="font-caption text-caption text-text-secondary font-medium">
                Note to candidate <span className="text-text-tertiary">(optional)</span>
              </label>
              <span className="font-code-inline text-code-inline text-text-tertiary">
                {candidateNote.length} / 500
              </span>
            </div>
            <textarea
              rows={3}
              maxLength={500}
              value={candidateNote}
              onChange={(e) => setCandidateNote(e.target.value)}
              className="w-full p-space-md bg-surface text-body font-body text-text placeholder:text-text-tertiary rounded-lg border border-border focus:outline-none focus:ring-1 focus:ring-accent resize-none shadow-sm"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-space-sm pb-space-xs flex flex-col gap-space-sm border-t border-border">
            <div className="flex items-center justify-end gap-space-md">
              <button
                type="button"
                onClick={() => setIsScheduleModalOpen(false)}
                className="h-9 px-space-md text-text-secondary hover:text-text font-body text-body transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="h-9 px-space-xl bg-accent text-on-accent hover:bg-accent-hover font-body text-body font-semibold rounded-lg shadow-sm transition-colors flex items-center gap-space-xs cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">event_available</span>
                <span>Create calendar event</span>
              </button>
            </div>
            <p className="text-right text-[12px] leading-[16px] text-text-tertiary font-caption">
              Sends calendar invites with Google Meet details to candidate and interviewer.
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};
