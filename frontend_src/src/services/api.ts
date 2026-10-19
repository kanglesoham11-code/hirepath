
function normalizeRole(r: any): any {
  if (!r) return r;
  const ps = r.pipeline_stages || r.pipelineStages || {};
  return {
    ...r,
    id: String(r.id || ''),
    reqId: r.req_id || r.reqId || ('REQ-' + r.id),
    title: r.title || 'Untitled Role',
    department: r.department || 'Engineering',
    location: r.location || 'Pune, Maharashtra',
    status: r.status || 'active',
    candidateCount: r.candidate_count ?? r.candidateCount ?? 0,
    healthScore: r.health_score ?? r.healthScore ?? 70,
    healthStatus: r.health_status || r.healthStatus || 'Healthy',
    hiringLead: r.hiring_lead || r.hiringLead || 'recruiter@company.com',
    auditVerifiedTime: r.audit_verified_time || r.auditVerifiedTime || 'Audit verified',
    pipelineStages: {
      sourced: ps.sourced || 0,
      screened: ps.screened || 0,
      outreach: ps.outreach || 0,
      replied: ps.replied || 0,
      interview: ps.interview || 0,
      offer: ps.offer || 0,
      hired: ps.hired || 0,
      rejected: ps.rejected || 0,
      stale: ps.stale || 0,
      closed: ps.closed || 0,
    }
  };
}
const API_BASE = 'http://localhost:8000/api';

let apiKey = sessionStorage.getItem('hirepath_api_key') || 'hirepath_dev_key_2026';

async function fetchWithAuth(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('X-Api-Key', apiKey);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  
  if (response.status === 401) {
    const newKey = window.prompt('Invalid or expired API key. Enter HirePath API key:', apiKey || '');
    if (newKey) {
      apiKey = newKey;
      sessionStorage.setItem('hirepath_api_key', apiKey);
      headers.set('X-Api-Key', apiKey);
      return fetch(`${API_BASE}${path}`, { ...options, headers });
    }
  }
  
  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json() : await response.text();
  
  if (!response.ok) {
    if (response.status === 401) sessionStorage.removeItem('hirepath_api_key');
    const detail = typeof data === 'object' ? data.detail || data.message : data;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return data;
}

export const api = {
  // Health
  health: () => fetchWithAuth('/health'),

  // Roles
  getRoles: async () => { const data = await fetchWithAuth('/roles'); return Array.isArray(data) ? data.map(normalizeRole) : []; },
  getRole: async (id: string) => { const data = await fetchWithAuth(`/roles/${id}`); return normalizeRole(data); },
  createRole: (data: any) => fetchWithAuth('/roles', { method: 'POST', body: JSON.stringify(data) }),
  updateRole: (id: string, data: any) => fetchWithAuth(/roles/, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteRole: (id: string) => fetchWithAuth(`/roles/${id}`, { method: 'DELETE' }),

  // Candidates
  getCandidates: (roleId: string, stage?: string) => 
    fetchWithAuth(`/roles/${roleId}/candidates${stage ? `?stage=${stage}` : ''}`),
  getCandidate: (id: string) => fetchWithAuth(`/candidates/${id}`),
  updateStage: (id: string, stage: string) => 
    fetchWithAuth(`/candidates/${id}/stage`, { method: 'PATCH', body: JSON.stringify({ stage }) }),
  revealEmail: (id: string) => fetchWithAuth(`/candidates/${id}/reveal-email`, { method: 'POST' }),
  optOutCandidate: (id: string) => fetchWithAuth(`/candidates/${id}/opt-out`, { method: 'POST' }),
  recordConsent: (id: string, data: any) => 
    fetchWithAuth(`/candidates/${id}/consent`, { method: 'POST', body: JSON.stringify(data) }),
  deleteCandidate: (id: string) => fetchWithAuth(`/candidates/${id}`, { method: 'DELETE' }),

  // SCOUT
  startScout: (roleId: string, keywords?: string[], maxCandidates?: number) => 
    fetchWithAuth('/scout', { method: 'POST', body: JSON.stringify({ role_id: parseInt(roleId), keywords, max_candidates: maxCandidates || 20 }) }),
  scoutStream: (roleId: string, keywords?: string[], maxCandidates?: number) => 
    fetchWithAuth('/scout/stream', { method: 'POST', body: JSON.stringify({ role_id: parseInt(roleId), keywords, max_candidates: maxCandidates || 20 }) }),

  // SCREEN
  screenCandidate: (id: string) => fetchWithAuth(`/screen/${id}`, { method: 'POST' }),
  screenRole: (roleId: string) => fetchWithAuth(`/screen/role/${roleId}`, { method: 'POST' }),

  // OUTREACH
  dispatchOutreach: (candidateIds: string[]) => 
    fetchWithAuth('/outreach', { method: 'POST', body: JSON.stringify({ candidate_ids: candidateIds.map(id => parseInt(id.replace('#CAN-', ''))) }) }),
  engageBulk: (candidateIds: string[]) => 
    fetchWithAuth('/engage', { method: 'POST', body: JSON.stringify({ candidate_ids: candidateIds.map(id => parseInt(id.replace('#CAN-', ''))) }) }),

  // SCHEDULE
  scheduleInterview: (data: { candidate_id: string; round: string; duration: string; slot: string; note?: string }) =>
    fetchWithAuth('/schedule', { method: 'POST', body: JSON.stringify(data) }),

  // CONSENT
  getConsentRecords: () => fetchWithAuth('/consent/records'),
  createConsentRecord: (data: any) => fetchWithAuth('/consent/records', { method: 'POST', body: JSON.stringify(data) }),

  // PRIVACY
  privacyPortal: () => fetchWithAuth('/privacy/portal'),
  privacyOptOut: (token: string) => fetchWithAuth('/privacy/opt-out', { method: 'POST', body: JSON.stringify({ token }) }),
  privacyDelete: (token: string) => fetchWithAuth('/privacy/delete', { method: 'POST', body: JSON.stringify({ token }) }),

  // COMPLIANCE
  complianceStatus: () => fetchWithAuth('/compliance/status'),

  // EXPORTS
  exportCandidates: (roleId: string, stage?: string) => 
    fetchWithAuth(`/export/candidates?role_id=${roleId}${stage ? `&stage=${stage}` : ''}`),
  exportAudit: () => fetchWithAuth('/export/audit'),

  // STATS
  getStats: () => fetchWithAuth('/stats'),

  // ACTIVITY LOGS
  getLogs: (params?: { agent?: string; role_id?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.agent) q.set('agent', params.agent);
    if (params?.role_id) q.set('role_id', params.role_id);
    if (params?.limit) q.set('limit', params.limit.toString());
    return fetchWithAuth(`/activity?${q.toString()}`);
  },

  // PIPELINE
  runPipeline: (roleId: string, keywords?: string[], maxCandidates?: number) =>
    fetchWithAuth('/pipeline/run', { method: 'POST', body: JSON.stringify({ role_id: parseInt(roleId), keywords, max_candidates: maxCandidates || 20 }) }),

  // ACTIVITY METRICS
  getActivityMetrics: () => fetchWithAuth('/activity/metrics'),

  // COMPLIANCE METRICS
  getComplianceMetrics: () => fetchWithAuth('/compliance/metrics'),

  // SETTINGS METRICS
  getSettingsMetrics: () => fetchWithAuth('/settings/metrics'),

  // PIPELINE HEALTH DETAILS
  getPipelineHealthDetails: (roleId: string) => fetchWithAuth(`/pipeline/health/details/${roleId}`),
};

export function setApiKey(key: string) {
  apiKey = key;
  sessionStorage.setItem('hirepath_api_key', key);
}

export function getApiKey() {
  return apiKey;
}