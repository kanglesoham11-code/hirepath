export type NavigationTab = 'roles' | 'activity' | 'compliance' | 'settings' | 'privacy';

export type PipelineStage = 
  | 'sourced' 
  | 'screened' 
  | 'outreach' 
  | 'replied' 
  | 'interview' 
  | 'offer' 
  | 'closed';

export interface ScoreBreakdownFactor {
  score: number;
  max: number;
  label: string;
  desc: string;
  evidence: string;
}

export interface Candidate {
  id: string; // e.g. '#CAN-8821'
  name: string; // e.g. 'Asha Rao'
  roleId: string;
  roleTitle: string;
  title: string; // e.g. 'Senior Python & Distributed Systems Engineer'
  avatar: string; // e.g. 'AR'
  publicProfiles: {
    github: string;
    stackoverflow?: string;
  };
  reposCount?: number;
  followersCount?: string;
  rep?: number;
  email: string;
  maskedEmail: string;
  isEmailRevealed: boolean;
  matchScore: number;
  scoreBreakdown: {
    coreStack: ScoreBreakdownFactor;
    distributedSystems: ScoreBreakdownFactor;
    experience: ScoreBreakdownFactor;
    recency: ScoreBreakdownFactor;
  };
  location: string;
  locationConfidence: 'High' | 'Medium' | 'Low';
  rawLocationSignals: {
    locationString: string;
    company: string;
    timezone: string;
    note: string;
  };
  source: 'GitHub' | 'StackOverflow' | 'Direct Referral' | 'LinkedIn';
  stage: PipelineStage;
  lastAction: {
    action: string;
    timestamp: string;
  };
  consent: {
    status: 'recorded' | 'pending' | 'withdrawn';
    recordedDate?: string;
    expiryDate?: string;
    daysRemaining?: number;
    channel?: string;
    recordedBy?: string;
    proofHash?: string;
    proofSnippet?: string;
    proofMethod?: string;
  };
  activityTimeline: Array<{
    action: string;
    timestamp: string;
    actor: string;
    type: 'system' | 'consent' | 'recruiter' | 'audit';
  }>;
}

export interface Role {
  id: string; // e.g. 'pune-backend'
  reqId: string; // e.g. 'REQ-ENG-4092'
  title: string; // e.g. 'Senior Backend Engineer, Pune'
  department: string; // e.g. 'Core Platform'
  location: string; // e.g. 'Pune, Maharashtra'
  status: 'active' | 'paused' | 'filled';
  candidateCount: number;
  pipelineStages: {
    sourced: number;
    screened: number;
    outreach: number;
    replied: number;
    interview: number;
    offer: number;
    hired: number;
    rejected: number;
    stale: number;
  };
  healthScore: number; // e.g. 68
  healthStatus: 'Healthy' | 'Needs attention' | 'At risk' | 'Optimal' | 'healthy' | 'needs_attention' | 'at_risk';
  lastActivity?: {
    action: string;
    timestamp: string;
  };
  hiringLead?: string;
  auditVerifiedTime?: string;
  createdAt?: string;
  updatedAt?: string;
  totalSourced?: number;
  totalScreened?: number;
  totalOutreach?: number;
  totalReplied?: number;
  totalInterview?: number;
  totalOffer?: number;
  pipelineLatencyDays?: number;
  sourcingCriteria?: {
    keywords: string[];
    location: string;
    minYearsExperience: number;
    targetTitles: string[];
  };
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  category: 'sourcing' | 'screening' | 'consent' | 'outreach' | 'optout' | 'inspection' | 'system';
  actorCategory: 'HirePath System' | 'Recruiter Ops' | 'Policy Engine' | 'anupama.rao' | 'Privacy Portal' | 'Mail Gateway' | 'Audit Ledger';
  eventDescription: string;
  targetEntity: string;
  auditHash: string;
  status: 'success' | 'blocked' | 'rate_limited' | 'pending';
}

export interface ConsentRecord {
  id: string;
  candidateName: string;
  maskedEmail: string;
  role: string;
  status: 'recorded' | 'pending' | 'withdrawn';
  recordedDate: string;
  expiryDate: string;
  daysRemaining: number;
  proofMethod: string;
  proofSnippet: string;
  proofHash: string;
  scope: string;
  recordedBy: string;
}

export interface ToastNotification {
  id?: string;
  title?: string;
  message: string;
  type: 'undo-outreach' | 'success' | 'info' | 'danger' | 'warning';
  timerSeconds?: number;
  onUndo?: () => void;
  details?: string;
}

