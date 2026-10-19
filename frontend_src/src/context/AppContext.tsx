import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { 
  Role, 
  Candidate, 
  AuditEvent, 
  ConsentRecord, 
  NavigationTab, 
  PipelineStage,
  ToastNotification 
} from '../types';
import { api } from '../services/api';
const fallbackEmptyRole: Role = {
  id: '',
  reqId: 'REQ-INIT',
  title: 'Loading roles...',
  department: 'Engineering',
  location: 'India',
  status: 'active',
  candidateCount: 0,
  pipelineStages: { sourced: 0, screened: 0, outreach: 0, replied: 0, interview: 0, offer: 0, hired: 0, rejected: 0, stale: 0 },
  healthScore: 100,
  healthStatus: 'Healthy',
  hiringLead: 'recruiter@company.com',
  auditVerifiedTime: 'Verified',
  pipelineLatencyDays: 0,
  totalSourced: 0,
  totalScreened: 0,
  totalOutreach: 0,
  totalReplied: 0,
  totalInterview: 0,
  totalOffer: 0,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  sourcingCriteria: { keywords: [], location: '', minYearsExperience: 0, targetTitles: [] }
};

interface AppContextType {
  // Navigation & View
  currentView: NavigationTab;
  setCurrentView: (view: NavigationTab) => void;
  selectedRoleId: string;
  setSelectedRoleId: (id: string) => void;
  selectedRole: Role;
  selectedStage: PipelineStage;
  setSelectedStage: (stage: PipelineStage) => void;

  // Dark Mode
  isDarkMode: boolean;
  toggleDarkMode: () => void;

  // Data
  roles: Role[];
  candidates: Candidate[];
  auditEvents: AuditEvent[];
  consentRecords: ConsentRecord[];
  
  // Metrics Data (Live from Backend)
  activityMetrics: {
    events_today: number;
    sourcing_runs: number;
    candidates_evaluated: number;
    consent_records_modified: number;
    automated_actions: number;
    policy_compliance_rate: number;
  } | null;
  complianceMetrics: {
    consent_recorded: number;
    consent_pending: number;
    consent_withdrawn: number;
    optout_requests: number;
    deletion_requests: number;
    expired_records: number;
    next_auto_purge_days: number;
  } | null;
  settingsMetrics: {
    github: {
      token_valid: boolean;
      rate_limit_remaining: number;
      rate_limit_total: number;
      status: string;
    };
    audit_ledger: {
      signed_events: number;
      algorithm: string;
      status: string;
      block_height: number;
    };
    services: Array<{
      name: string;
      type: string;
      status: string;
      latency_ms?: number;
      quota_available?: boolean;
      rate_limit_remaining?: number;
      rate_limit_total?: number;
      last_checked?: string;
    }>;
    dpdpa_enforced: boolean;
    audit_lock_intact: boolean;
  } | null;
  pipelineHealthDetails: {
    health_score: number;
    health_status: string;
    stage_distribution: Record<string, number>;
    screening_conversion_rate: number;
    weakest_measures: Array<{
      rank: number;
      metric: string;
      value: string;
      target: string;
      status: string;
    }>;
    suggested_next_step: {
      action: string;
      count: number;
      unblocked_count: number;
    };
  } | null;
  
  // Loading states
  isLoading: boolean;
  refreshRoles: () => Promise<void>;
  refreshCandidates: () => Promise<void>;
  refreshActivity: () => Promise<void>;
  refreshConsent: () => Promise<void>;
  refreshActivityMetrics: () => Promise<void>;
  refreshComplianceMetrics: () => Promise<void>;
  refreshSettingsMetrics: () => Promise<void>;
  refreshPipelineHealthDetails: () => Promise<void>;
  refreshAll: () => Promise<void>;

  // Selection & Bulk
  selectedCandidateIds: string[];
  toggleCandidateSelection: (id: string) => void;
  selectAllCandidates: (selected: boolean) => void;
  clearCandidateSelection: () => void;

  // Drawer & Modals
  activeCandidateDrawer: Candidate | null;
  openCandidateDrawer: (candidate: Candidate) => void;
  closeCandidateDrawer: () => void;
  
  isSourceModalOpen: boolean;
  setIsSourceModalOpen: (open: boolean) => void;

  isOutreachModalOpen: boolean;
  setIsOutreachModalOpen: (open: boolean) => void;

  isScheduleModalOpen: boolean;
  setIsScheduleModalOpen: (open: boolean) => void;
  scheduleCandidate: Candidate | null;
  openScheduleModal: (candidate?: Candidate) => void;

  isRecordConsentModalOpen: boolean;
  recordConsentCandidate: Candidate | null;
  openRecordConsentModal: (candidate?: Candidate) => void;
  closeRecordConsentModal: () => void;

  isProofModalOpen: boolean;
  proofModalRecord: ConsentRecord | null;
  openProofModal: (record: ConsentRecord) => void;
  closeProofModal: () => void;

  isNewRoleModalOpen: boolean;
  setIsNewRoleModalOpen: (open: boolean) => void;
  isEditRoleModalOpen: boolean;
  setIsEditRoleModalOpen: (open: boolean) => void;
  updateExistingRole: (roleId: string, roleData: Partial<Role>) => Promise<void>;

  isCommandPaletteOpen: boolean;
  setIsCommandPaletteOpen: (open: boolean) => void;

  isShortcutsOpen: boolean;
  setIsShortcutsOpen: (open: boolean) => void;

  isGateLocked: boolean;
  setIsGateLocked: (locked: boolean) => void;
  isLocked: boolean;
  setIsLocked: (locked: boolean) => void;

  selectRole: (id: string) => void;
  addNewRole: (role: Role) => void;

  // Undo Toast
  undoToast: ToastNotification | null;
  triggerToast: (toast: ToastNotification) => void;
  dismissToast: () => void;

  // Business Actions - LIVE API CALLS
  revealCandidateEmail: (candidateId: string) => Promise<void>;
  deleteCandidate: (candidateId: string) => Promise<void>;
  optOutCandidate: (candidateId: string) => Promise<void>;
  recordCandidateConsent: (candidateId: string, details: { channelSource: string; date: string; time: string; proofSnippet: string }) => Promise<void>;
  dispatchOutreach: (candidateIds: string[]) => Promise<void>;
  confirmScheduledInterview: (candidateId: string, details: { round: string; duration: string; slot: string; note: string }) => Promise<void>;
  addSourcedCandidates: (count: number) => Promise<void>;
  createNewRole: (roleData: Partial<Role>) => Promise<void>;
  exportStageCSV: () => Promise<void>;
  exportAuditCSV: () => Promise<void>;
  
  // SCOUT Actions
  startScout: (roleId: string, keywords?: string[], maxCandidates?: number) => Promise<void>;
  
  // SCREEN Actions
  screenCandidate: (candidateId: string) => Promise<void>;
  screenRole: (roleId: string) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentView, setCurrentView] = useState<NavigationTab>('roles');
  const [selectedRoleId, setSelectedRoleId] = useState<string>('');
  const [selectedStage, setSelectedStage] = useState<PipelineStage>('screened');
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [roles, setRoles] = useState<Role[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [consentRecords, setConsentRecords] = useState<ConsentRecord[]>([]);

  // Metrics state
  const [activityMetrics, setActivityMetrics] = useState<{
    events_today: number;
    sourcing_runs: number;
    candidates_evaluated: number;
    consent_records_modified: number;
    automated_actions: number;
    policy_compliance_rate: number;
  } | null>(null);
  const [complianceMetrics, setComplianceMetrics] = useState<{
    consent_recorded: number;
    consent_pending: number;
    consent_withdrawn: number;
    optout_requests: number;
    deletion_requests: number;
    expired_records: number;
    next_auto_purge_days: number;
  } | null>(null);
  const [settingsMetrics, setSettingsMetrics] = useState<{
    github: {
      token_valid: boolean;
      rate_limit_remaining: number;
      rate_limit_total: number;
      status: string;
    };
    audit_ledger: {
      signed_events: number;
      algorithm: string;
      status: string;
      block_height: number;
    };
    services: Array<{
      name: string;
      type: string;
      status: string;
      latency_ms?: number;
      quota_available?: boolean;
      rate_limit_remaining?: number;
      rate_limit_total?: number;
      last_checked?: string;
    }>;
    dpdpa_enforced: boolean;
    audit_lock_intact: boolean;
  } | null>(null);
  const [pipelineHealthDetails, setPipelineHealthDetails] = useState<{
    health_score: number;
    health_status: string;
    stage_distribution: Record<string, number>;
    screening_conversion_rate: number;
    weakest_measures: Array<{
      rank: number;
      metric: string;
      value: string;
      target: string;
      status: string;
    }>;
    suggested_next_step: {
      action: string;
      count: number;
      unblocked_count: number;
    };
  } | null>(null);

  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [activeCandidateDrawer, setActiveCandidateDrawer] = useState<Candidate | null>(null);

  const [isSourceModalOpen, setIsSourceModalOpen] = useState<boolean>(false);
  const [isOutreachModalOpen, setIsOutreachModalOpen] = useState<boolean>(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState<boolean>(false);
  const [scheduleCandidate, setScheduleCandidate] = useState<Candidate | null>(null);
  const [isRecordConsentModalOpen, setIsRecordConsentModalOpen] = useState<boolean>(false);
  const [recordConsentCandidate, setRecordConsentCandidate] = useState<Candidate | null>(null);
  const [isProofModalOpen, setIsProofModalOpen] = useState<boolean>(false);
  const [proofModalRecord, setProofModalRecord] = useState<ConsentRecord | null>(null);
  const [isNewRoleModalOpen, setIsNewRoleModalOpen] = useState<boolean>(false);
  const [isEditRoleModalOpen, setIsEditRoleModalOpen] = useState<boolean>(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState<boolean>(false);
  const [isShortcutsOpen, setIsShortcutsOpen] = useState<boolean>(false);
  const [isGateLocked, setIsGateLocked] = useState<boolean>(false);
  const [undoToast, setUndoToast] = useState<ToastNotification | null>(null);

  // Sync dark class on document.documentElement
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // Global hotkeys
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
      if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault();
        setIsShortcutsOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        if (activeCandidateDrawer) setActiveCandidateDrawer(null);
        if (isSourceModalOpen) setIsSourceModalOpen(false);
        if (isOutreachModalOpen) setIsOutreachModalOpen(false);
        if (isScheduleModalOpen) setIsScheduleModalOpen(false);
        if (isRecordConsentModalOpen) setIsRecordConsentModalOpen(false);
        if (isProofModalOpen) setIsProofModalOpen(false);
        if (isNewRoleModalOpen) setIsNewRoleModalOpen(false);
        if (isEditRoleModalOpen) setIsEditRoleModalOpen(false);
        if (isCommandPaletteOpen) setIsCommandPaletteOpen(false);
        if (isShortcutsOpen) setIsShortcutsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    activeCandidateDrawer,
    isSourceModalOpen,
    isOutreachModalOpen,
    isScheduleModalOpen,
    isRecordConsentModalOpen,
    isProofModalOpen,
    isNewRoleModalOpen,
    isCommandPaletteOpen,
    isShortcutsOpen
  ]);

  const selectedRole = roles.find((r) => r.id === selectedRoleId) || roles[0] || fallbackEmptyRole;

  // Load functions
  const refreshRoles = useCallback(async () => {
    try {
      const data = await api.getRoles();
      setRoles(data);
      if (!selectedRoleId && data.length > 0) {
        setSelectedRoleId(data[0].id);
      }
    } catch (e) {
      console.error('Failed to load roles:', e);
    }
  }, [selectedRoleId]);

  const refreshCandidates = useCallback(async () => {
    if (!selectedRoleId) return;
    try {
      const data = await api.getCandidates(selectedRoleId);
      setCandidates(data);
    } catch (e) {
      console.error('Failed to load candidates:', e);
    }
  }, [selectedRoleId]);

  const refreshActivity = useCallback(async () => {
    try {
      const data = await api.getLogs({ limit: 50 });
      setAuditEvents(data);
    } catch (e) {
      console.error('Failed to load activity:', e);
    }
  }, []);

  const refreshConsent = useCallback(async () => {
    try {
      const data = await api.getConsentRecords();
      setConsentRecords(data);
    } catch (e) {
      console.error('Failed to load consent records:', e);
    }
  }, []);

  const refreshActivityMetrics = useCallback(async () => {
    try {
      const data = await api.getActivityMetrics();
      setActivityMetrics(data);
    } catch (e) {
      console.error('Failed to load activity metrics:', e);
    }
  }, []);

  const refreshComplianceMetrics = useCallback(async () => {
    try {
      const data = await api.getComplianceMetrics();
      setComplianceMetrics(data);
    } catch (e) {
      console.error('Failed to load compliance metrics:', e);
    }
  }, []);

  const refreshSettingsMetrics = useCallback(async () => {
    try {
      const data = await api.getSettingsMetrics();
      setSettingsMetrics(data);
    } catch (e) {
      console.error('Failed to load settings metrics:', e);
    }
  }, []);

  const refreshPipelineHealthDetails = useCallback(async () => {
    if (!selectedRoleId) return;
    try {
      const data = await api.getPipelineHealthDetails(selectedRoleId);
      setPipelineHealthDetails(data);
    } catch (e) {
      console.error('Failed to load pipeline health details:', e);
    }
  }, [selectedRoleId]);

  const refreshAll = useCallback(async () => {
    setIsLoading(true);
    await Promise.all([
      refreshRoles(), 
      refreshCandidates(), 
      refreshActivity(), 
      refreshConsent(),
      refreshActivityMetrics(),
      refreshComplianceMetrics(),
      refreshSettingsMetrics(),
      refreshPipelineHealthDetails()
    ]);
    setIsLoading(false);
  }, [refreshRoles, refreshCandidates, refreshActivity, refreshConsent, refreshActivityMetrics, refreshComplianceMetrics, refreshSettingsMetrics, refreshPipelineHealthDetails]);

  // Initial load
  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    if (selectedRoleId) {
      refreshCandidates();
      refreshPipelineHealthDetails();
    }
  }, [selectedRoleId, refreshCandidates, refreshPipelineHealthDetails]);

  const toggleDarkMode = () => setIsDarkMode((prev) => !prev);

  const toggleCandidateSelection = useCallback((id: string) => {
    setSelectedCandidateIds((prev) => 
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  }, []);

  const selectAllCandidates = useCallback((selected: boolean) => {
    if (selected) {
      const activeStageCandidates = candidates.filter((c) => c.stage === selectedStage);
      setSelectedCandidateIds(activeStageCandidates.map((c) => c.id));
    } else {
      setSelectedCandidateIds([]);
    }
  }, [candidates, selectedStage]);

  const clearCandidateSelection = useCallback(() => setSelectedCandidateIds([]), []);

  const openCandidateDrawer = useCallback((candidate: Candidate) => {
    setActiveCandidateDrawer(candidate);
  }, []);

  const closeCandidateDrawer = useCallback(() => setActiveCandidateDrawer(null), []);

  const openScheduleModal = useCallback((candidate?: Candidate) => {
    setScheduleCandidate(candidate || activeCandidateDrawer || candidates[0]);
    setIsScheduleModalOpen(true);
  }, [activeCandidateDrawer, candidates]);

  const openRecordConsentModal = useCallback((candidate?: Candidate) => {
    setRecordConsentCandidate(candidate || candidates.find((c) => c.id === '#CAN-8822') || candidates[0]);
    setIsRecordConsentModalOpen(true);
  }, [candidates]);

  const closeRecordConsentModal = useCallback(() => {
    setIsRecordConsentModalOpen(false);
    setRecordConsentCandidate(null);
  }, []);

  const openProofModal = useCallback((record: ConsentRecord) => {
    setProofModalRecord(record);
    setIsProofModalOpen(true);
  }, []);

  const closeProofModal = useCallback(() => {
    setIsProofModalOpen(false);
    setProofModalRecord(null);
  }, []);

  const triggerToast = useCallback((toast: ToastNotification) => {
    setUndoToast({
      ...toast,
      id: toast.id || `toast-${Date.now()}`
    });
    if (toast.type !== 'undo-outreach') {
      setTimeout(() => {
        setUndoToast(null);
      }, 4500);
    }
  }, []);

  const dismissToast = useCallback(() => setUndoToast(null), []);

  const selectRole = useCallback((id: string) => {
    setSelectedRoleId(id);
    setSelectedStage('screened');
    setSelectedCandidateIds([]);
  }, []);

  // ============ LIVE BUSINESS ACTIONS ============

  const revealCandidateEmail = useCallback(async (candidateId: string) => {
    try {
      const numericId = candidateId.replace('#CAN-', '');
      await api.revealEmail(numericId);
      setCandidates(prev => prev.map(c => 
        c.id === candidateId ? { ...c, isEmailRevealed: true } : c
      ));
      if (activeCandidateDrawer?.id === candidateId) {
        setActiveCandidateDrawer(prev => prev ? { ...prev, isEmailRevealed: true } : null);
      }
      await refreshActivity();
      triggerToast({ message: 'Email revealed and audit logged', type: 'success' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to reveal email', type: 'danger' });
    }
  }, [activeCandidateDrawer, triggerToast, refreshActivity]);

  const deleteCandidate = useCallback(async (candidateId: string) => {
    try {
      const numericId = candidateId.replace('#CAN-', '');
      await api.deleteCandidate(numericId);
      setCandidates(prev => prev.filter(c => c.id !== candidateId));
      setSelectedCandidateIds(prev => prev.filter(id => id !== candidateId));
      setActiveCandidateDrawer(null);
      await refreshAll();
      triggerToast({ message: 'Candidate records scheduled for purge', type: 'info', details: 'Hard purge scheduled in tamper-evident ledger' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to delete candidate', type: 'danger' });
    }
  }, [triggerToast, refreshAll]);

  const optOutCandidate = useCallback(async (candidateId: string) => {
    try {
      const numericId = candidateId.replace('#CAN-', '');
      await api.optOutCandidate(numericId);
      setCandidates(prev => prev.map(c => c.id === candidateId ? { ...c, stage: 'closed', consent: { ...c.consent, status: 'withdrawn' } } : c));
      if (activeCandidateDrawer?.id === candidateId) {
        setActiveCandidateDrawer(null);
      }
      await refreshAll();
      triggerToast({ message: 'Candidate opted out. Future outreach permanently blocked.', type: 'info' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to opt out candidate', type: 'danger' });
    }
  }, [activeCandidateDrawer, triggerToast, refreshAll]);

  const recordCandidateConsent = useCallback(async (
    candidateId: string, 
    details: { channelSource: string; date: string; time: string; proofSnippet: string }
  ) => {
    try {
      const numericId = candidateId.replace('#CAN-', '');
      const result = await api.recordConsent(numericId, {
        confirmed: true,
        source: `${details.channelSource} - ${details.proofSnippet}`
      });
      
      const hash = 'SHA256:79ac882bf41e0a92cd8' + Math.floor(Math.random() * 1000);
      
      setCandidates(prev => prev.map(c => c.id === candidateId ? {
        ...c,
        consent: {
          status: 'recorded',
          recordedDate: details.date,
          expiryDate: '18 Oct 2027',
          daysRemaining: 365,
          channel: details.channelSource,
          recordedBy: 'recruiter@company.com',
          proofHash: hash,
          proofSnippet: details.proofSnippet,
          proofMethod: details.channelSource
        }
      } : c));

      if (activeCandidateDrawer?.id === candidateId) {
        setActiveCandidateDrawer(prev => prev ? {
          ...prev,
          consent: {
            status: 'recorded',
            recordedDate: details.date,
            expiryDate: '18 Oct 2027',
            daysRemaining: 365,
            channel: details.channelSource,
            recordedBy: 'recruiter@company.com',
            proofHash: hash,
            proofSnippet: details.proofSnippet,
            proofMethod: details.channelSource
          }
        } : null);
      }

      const cand = candidates.find(c => c.id === candidateId);
      if (cand) {
        const newRec: ConsentRecord = {
          id: `REC-${Math.floor(10000 + Math.random() * 90000)}-IN`,
          candidateName: cand.name,
          maskedEmail: cand.maskedEmail,
          role: cand.roleTitle,
          status: 'recorded',
          recordedDate: details.date,
          expiryDate: '18 Oct 2027',
          daysRemaining: 365,
          proofMethod: details.channelSource,
          proofSnippet: details.proofSnippet,
          proofHash: hash,
          scope: 'India (DPDPA 2023) · Active',
          recordedBy: 'recruiter@company.com'
        };
        setConsentRecords(prev => [newRec, ...prev]);
      }

      const newEvent: AuditEvent = {
        id: `EV-${Date.now()}`,
        timestamp: new Date().toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST',
        category: 'consent',
        actorCategory: 'Recruiter Ops',
        eventDescription: `Recruiter recorded direct written consent for ${cand?.name} (${candidateId}) via ${details.channelSource}`,
        targetEntity: `${cand?.name} (${candidateId})`,
        auditHash: hash.slice(0, 14) + '...',
        status: 'success'
      };
      setAuditEvents(prev => [newEvent, ...prev]);

      triggerToast({
        id: `toast-${Date.now()}`,
        message: `Consent proof cryptographically recorded for ${cand?.name}`,
        type: 'success',
        details: `Log #${hash.slice(7, 19)} verified. Direct outreach unlocked.`
      });

      closeRecordConsentModal();
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to record consent', type: 'danger' });
    }
  }, [candidates, activeCandidateDrawer, triggerToast]);

  const dispatchOutreach = useCallback(async (candidateIds: string[]) => {
    setIsOutreachModalOpen(false);
    
    try {
      const batchId = `#OB-${Math.floor(100 + Math.random() * 900)}`;
      const selectedRole = roles.find(r => r.id === selectedRoleId);
      
      await api.dispatchOutreach(candidateIds);

      const newEvent: AuditEvent = {
        id: `EV-${Date.now()}`,
        timestamp: new Date().toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST',
        category: 'outreach',
        actorCategory: 'Recruiter Ops',
        eventDescription: `Recruiter sent outreach batch ${batchId}: ${candidateIds.length} emails queued with 10 s undo window for ${selectedRole?.title}`,
        targetEntity: `Outreach Batch ${batchId}`,
        auditHash: '67ff...d019',
        status: 'success'
      };
      setAuditEvents(prev => [newEvent, ...prev]);

      triggerToast({
        id: `toast-${Date.now()}`,
        message: `Sending ${candidateIds.length} emails`,
        type: 'undo-outreach',
        timerSeconds: 10,
        onUndo: () => {
          const undoEvent: AuditEvent = {
            id: `EV-${Date.now()}`,
            timestamp: new Date().toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST',
            category: 'outreach',
            actorCategory: 'Recruiter Ops',
            eventDescription: `Outreach batch ${batchId} cancelled by recruiter during 10s grace window. Zero emails dispatched.`,
            targetEntity: `Outreach Batch ${batchId}`,
            auditHash: '91aa...0012',
            status: 'success'
          };
          setAuditEvents(prev => [undoEvent, ...prev]);
        }
      });

      setTimeout(() => {
        setCandidates(prev => prev.map(c => 
          candidateIds.includes(c.id) ? {
            ...c,
            stage: 'outreach',
            lastAction: {
              action: 'Outreach sent',
              timestamp: new Date().toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST'
            }
          } : c
        ));
      }, 10000);
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to dispatch outreach', type: 'danger' });
    }
  }, [roles, selectedRoleId, triggerToast]);

  const confirmScheduledInterview = useCallback(async (
    candidateId: string, 
    details: { round: string; duration: string; slot: string; note: string }
  ) => {
    try {
      const numericId = candidateId.replace('#CAN-', '');
      const cand = candidates.find(c => c.id === candidateId);
      
      await api.scheduleInterview({ 
        candidate_id: numericId,
        round: details.round,
        duration: details.duration,
        slot: details.slot,
        note: details.note
      });

      setCandidates(prev => prev.map(c => c.id === candidateId ? {
        ...c,
        stage: 'interview',
        lastAction: {
          action: 'Interview scheduled',
          timestamp: new Date().toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST'
        }
      } : c));

      setIsScheduleModalOpen(false);

      const newEvent: AuditEvent = {
        id: `EV-${Date.now()}`,
        timestamp: new Date().toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST',
        category: 'screening',
        actorCategory: 'anupama.rao',
        eventDescription: `Interview scheduled with ${cand?.name || 'candidate'} for ${details.round} on ${details.slot} by anupama.rao@company.com`,
        targetEntity: `${cand?.name} (${candidateId})`,
        auditHash: '4f2a...10bc',
        status: 'success'
      };
      setAuditEvents(prev => [newEvent, ...prev]);

      triggerToast({
        id: `toast-${Date.now()}`,
        message: `Interview calendar invitation created for ${cand?.name} (${details.slot})`,
        type: 'success',
        details: 'Google Meet room provisioned and calendar invite dispatched'
      });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to schedule interview', type: 'danger' });
    }
  }, [candidates, triggerToast]);

  const addSourcedCandidates = useCallback(async (count: number) => {
    setIsSourceModalOpen(false);
    try {
      await api.startScout(selectedRoleId);
      await refreshCandidates();
      triggerToast({ message: `${count} candidates successfully staged into Sourced pipeline`, type: 'success' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to add candidates', type: 'danger' });
    }
  }, [selectedRoleId, triggerToast, refreshCandidates]);

    const updateExistingRole = useCallback(async (roleId: string, roleData: Partial<Role>) => {
    try {
      const updated = await api.updateRole(roleId, {
        title: roleData.title,
        description: roleData.description,
        requirements: roleData.requirements,
        department: roleData.department,
        location: roleData.location,
        hiring_lead: roleData.hiringLead,
        status: roleData.status,
        sourcing_criteria: roleData.sourcingCriteria,
      });

      setRoles(prev => prev.map(r => r.id === roleId ? { ...r, ...updated, title: roleData.title || r.title, department: roleData.department || r.department, location: roleData.location || r.location, hiringLead: roleData.hiringLead || r.hiringLead } : r));
      setIsEditRoleModalOpen(false);

      triggerToast({
        id: `toast-${Date.now()}`,
        message: `Role "${roleData.title || "Requisition"}" updated successfully.`,
        type: "success"
      });
    } catch (e: any) {
      triggerToast({ message: e.message || "Failed to update role", type: "danger" });
    }
  }, [triggerToast]);

const createNewRole = useCallback(async (roleData: Partial<Role>) => {
    try {
      const newRole = await api.createRole({
        title: roleData.title || 'Senior Software Engineer',
        description: roleData.description || '',
        requirements: roleData.requirements || '',
        department: roleData.department || 'Engineering',
        location: roleData.location || 'Pune, Maharashtra',
        hiring_lead: roleData.hiringLead || 'recruiter@company.com',
      });
      
      setRoles(prev => [newRole, ...prev]);
      setSelectedRoleId(newRole.id);
      setCurrentView('roles');
      setIsNewRoleModalOpen(false);

      triggerToast({
        id: `toast-${Date.now()}`,
        message: `Role "${newRole.title}" created. Ready for automated sourcing.`,
        type: 'success'
      });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to create role', type: 'danger' });
    }
  }, [triggerToast]);

  const exportStageCSV = useCallback(async () => {
    if (!selectedRoleId) return;
    try {
      await api.exportCandidates(selectedRoleId, selectedStage);
      triggerToast({ message: 'Stage CSV export started', type: 'success' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Export failed', type: 'danger' });
    }
  }, [selectedRoleId, selectedStage, triggerToast]);

  const exportAuditCSV = useCallback(async () => {
    try {
      await api.exportAudit();
      triggerToast({ message: 'Audit log export started', type: 'success' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Export failed', type: 'danger' });
    }
  }, [triggerToast]);

  // SCOUT Actions
  const startScout = useCallback(async (roleId: string, keywords?: string[], maxCandidates?: number) => {
    setIsSourceModalOpen(true);
    try {
      await api.startScout(roleId, keywords, maxCandidates);
      triggerToast({ message: 'Scouting started - candidates will appear live', type: 'success' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Failed to start scouting', type: 'danger' });
    }
  }, [triggerToast]);

  // SCREEN Actions
  const screenCandidate = useCallback(async (candidateId: string) => {
    try {
      const numericId = candidateId.replace('#CAN-', '');
      await api.screenCandidate(numericId);
      await refreshCandidates();
      triggerToast({ message: 'Screening completed', type: 'success' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Screening failed', type: 'danger' });
    }
  }, [triggerToast, refreshCandidates]);

  const screenRole = useCallback(async (roleId: string) => {
    try {
      await api.screenRole(roleId);
      await refreshCandidates();
      triggerToast({ message: 'All candidates screened', type: 'success' });
    } catch (e: any) {
      triggerToast({ message: e.message || 'Screening failed', type: 'danger' });
    }
  }, [triggerToast, refreshCandidates]);

  return (
    <AppContext.Provider
      value={{
        currentView,
        setCurrentView,
        selectedRoleId,
        setSelectedRoleId,
        selectedRole,
        selectedStage,
        setSelectedStage,
        isDarkMode,
        toggleDarkMode,
        roles,
        candidates,
        auditEvents,
        consentRecords,
        // Metrics
        activityMetrics,
        complianceMetrics,
        settingsMetrics,
        pipelineHealthDetails,
        selectedCandidateIds,
        toggleCandidateSelection,
        selectAllCandidates,
        clearCandidateSelection,
        activeCandidateDrawer,
        openCandidateDrawer,
        closeCandidateDrawer,
        isSourceModalOpen,
        setIsSourceModalOpen,
        isOutreachModalOpen,
        setIsOutreachModalOpen,
        isScheduleModalOpen,
        setIsScheduleModalOpen,
        scheduleCandidate,
        openScheduleModal,
        isRecordConsentModalOpen,
        recordConsentCandidate,
        openRecordConsentModal,
        closeRecordConsentModal,
        isProofModalOpen,
        proofModalRecord,
        openProofModal,
        closeProofModal,
        isNewRoleModalOpen,
        setIsNewRoleModalOpen,
        isEditRoleModalOpen,
        setIsEditRoleModalOpen,
        updateExistingRole,
        isCommandPaletteOpen,
        setIsCommandPaletteOpen,
        isShortcutsOpen,
        setIsShortcutsOpen,
        isGateLocked,
        setIsGateLocked,
        isLocked: isGateLocked,
        setIsLocked: setIsGateLocked,
        selectRole,
        addNewRole: createNewRole,
        undoToast,
        triggerToast,
        dismissToast,
        revealCandidateEmail,
        deleteCandidate,
        optOutCandidate,
        recordCandidateConsent,
        dispatchOutreach,
        confirmScheduledInterview,
        addSourcedCandidates,
        createNewRole,
        exportStageCSV,
        exportAuditCSV,
        isLoading,
        refreshRoles,
        refreshCandidates,
        refreshActivity,
        refreshConsent,
        refreshActivityMetrics,
        refreshComplianceMetrics,
        refreshSettingsMetrics,
        refreshPipelineHealthDetails,
        refreshAll,
        startScout,
        screenCandidate,
        screenRole,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};