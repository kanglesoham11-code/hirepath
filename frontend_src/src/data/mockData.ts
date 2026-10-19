import { Role, Candidate, AuditEvent, ConsentRecord } from '../types';

export const initialRoles: Role[] = [
  {
    id: 'pune-backend',
    reqId: 'REQ-ENG-4092',
    title: 'Senior Backend Engineer, Pune',
    department: 'Core Platform',
    location: 'Pune, Maharashtra',
    status: 'active',
    candidateCount: 42,
    pipelineStages: {
      sourced: 18,
      screened: 12,
      outreach: 6,
      replied: 3,
      interview: 2,
      offer: 0,
      hired: 2,
      rejected: 8,
      stale: 4
    },
    healthScore: 68,
    healthStatus: 'Healthy',
    lastActivity: {
      action: 'Screened Asha Rao (score 72)',
      timestamp: '20 Oct 2026, 11:38 IST'
    },
    hiringLead: 'Anupama Rao',
    auditVerifiedTime: 'Audit verified 2 hours ago'
  },
  {
    id: 'bengaluru-dist-arch',
    reqId: 'REQ-ENG-4088',
    title: 'Staff Distributed Systems Architect',
    department: 'Infrastructure',
    location: 'Bengaluru, Karnataka',
    status: 'active',
    candidateCount: 28,
    pipelineStages: {
      sourced: 10,
      screened: 9,
      outreach: 5,
      replied: 2,
      interview: 2,
      offer: 0,
      hired: 1,
      rejected: 4,
      stale: 2
    },
    healthScore: 74,
    healthStatus: 'Healthy',
    lastActivity: {
      action: 'Outreach sent to Nikhil Verma',
      timestamp: '20 Oct 2026, 10:14 IST'
    },
    hiringLead: 'Rajesh Kulkarni',
    auditVerifiedTime: 'Audit verified 3 hours ago'
  },
  {
    id: 'remote-devops-lead',
    reqId: 'REQ-OPS-2911',
    title: 'Lead DevOps & Reliability Engineer',
    department: 'Cloud Platform',
    location: 'Remote (India)',
    status: 'active',
    candidateCount: 36,
    pipelineStages: {
      sourced: 14,
      screened: 11,
      outreach: 7,
      replied: 2,
      interview: 2,
      offer: 0,
      hired: 0,
      rejected: 6,
      stale: 3
    },
    healthScore: 58,
    healthStatus: 'Needs attention',
    lastActivity: {
      action: 'Opt-out recorded: Sneha Patil',
      timestamp: '20 Oct 2026, 09:40 IST'
    },
    hiringLead: 'Vikrant Mehta',
    auditVerifiedTime: 'Audit verified 4 hours ago'
  },
  {
    id: 'pune-frontend-eng',
    reqId: 'REQ-ENG-4105',
    title: 'Senior Frontend Engineer (React/TypeScript)',
    department: 'Design Systems & Apps',
    location: 'Pune, Maharashtra',
    status: 'active',
    candidateCount: 24,
    pipelineStages: {
      sourced: 8,
      screened: 6,
      outreach: 6,
      replied: 2,
      interview: 2,
      offer: 0,
      hired: 0,
      rejected: 3,
      stale: 2
    },
    healthScore: 62,
    healthStatus: 'Needs attention',
    lastActivity: {
      action: 'Interview scheduled: Devansh K',
      timestamp: '19 Oct 2026, 16:30 IST'
    },
    hiringLead: 'Swati Deshmukh',
    auditVerifiedTime: 'Audit verified 1 day ago'
  },
  {
    id: 'bengaluru-data-sec',
    reqId: 'REQ-SEC-1092',
    title: 'Data Platform Security Lead',
    department: 'Infosec',
    location: 'Bengaluru, Karnataka',
    status: 'paused',
    candidateCount: 12,
    pipelineStages: {
      sourced: 6,
      screened: 4,
      outreach: 2,
      replied: 0,
      interview: 0,
      offer: 0,
      hired: 0,
      rejected: 1,
      stale: 3
    },
    healthScore: 32,
    healthStatus: 'At risk',
    lastActivity: {
      action: 'Sourcing paused (rate limit waiting)',
      timestamp: '18 Oct 2026, 14:15 IST'
    },
    hiringLead: 'Anand Shrestha',
    auditVerifiedTime: 'Audit paused'
  },
  {
    id: 'pune-principal-prod-sec',
    reqId: 'REQ-SEC-0994',
    title: 'Principal Product Security Engineer',
    department: 'Security Operations',
    location: 'Pune, Maharashtra',
    status: 'filled',
    candidateCount: 54,
    pipelineStages: {
      sourced: 22,
      screened: 18,
      outreach: 9,
      replied: 4,
      interview: 2,
      offer: 1,
      hired: 1,
      rejected: 12,
      stale: 5
    },
    healthScore: 92,
    healthStatus: 'Optimal',
    lastActivity: {
      action: 'Candidate hired · Offer accepted',
      timestamp: '15 Oct 2026, 18:00 IST'
    },
    hiringLead: 'Anupama Rao',
    auditVerifiedTime: 'Archived record'
  }
];

export const initialCandidates: Candidate[] = [
  {
    id: '#CAN-8821',
    name: 'Asha Rao',
    roleId: 'pune-backend',
    roleTitle: 'Senior Backend Engineer, Pune',
    title: 'Senior Python & Distributed Systems Engineer',
    avatar: 'AR',
    publicProfiles: {
      github: 'github.com/asharao',
      stackoverflow: 'stackoverflow.com/users/asharao'
    },
    reposCount: 42,
    followersCount: '1.2k',
    rep: 4820,
    email: 'asha.rao@workmail.io',
    maskedEmail: 'ash****@workmail.io',
    isEmailRevealed: false,
    matchScore: 72,
    scoreBreakdown: {
      coreStack: {
        score: 28,
        max: 30,
        label: 'Core Stack (Python & FastAPI)',
        desc: "Found 14 public repositories with FastAPI/AsyncIO. Top repo 'fast-broker' with 340 stars.",
        evidence: 'https://github.com/asharao/fast-broker'
      },
      distributedSystems: {
        score: 22,
        max: 25,
        label: 'Distributed Systems & Docker',
        desc: 'Dockerfiles & compose specs across 8 repos; commits in open-source kafka-python.',
        evidence: 'https://github.com/asharao/distributed-ledger-kit'
      },
      experience: {
        score: 14,
        max: 25,
        label: 'Years of Experience & Seniority',
        desc: 'First public commit Oct 2018 (8 years). Tech lead contributor on 2 active orgs.',
        evidence: 'Commit history from 2018 verified'
      },
      recency: {
        score: 8,
        max: 20,
        label: 'Recent Activity Recency',
        desc: 'Last pushed 3 days ago. 142 contributions in past 12 months.',
        evidence: 'GitHub streak verification'
      }
    },
    location: 'Pune, Maharashtra',
    locationConfidence: 'High',
    rawLocationSignals: {
      locationString: 'Pune, MH, India',
      company: 'Independent Consultant · Pune',
      timezone: 'UTC+05:30 (Matches role territory)',
      note: 'Candidate verified within 50 km boundary of Pune territory.'
    },
    source: 'GitHub',
    stage: 'screened',
    lastAction: {
      action: 'Screened',
      timestamp: '18 Oct, 14:20 IST'
    },
    consent: {
      status: 'recorded',
      recordedDate: '12 Oct 2026',
      expiryDate: '12 Oct 2027',
      daysRemaining: 358,
      channel: 'Direct LinkedIn outreach opt-in verified',
      recordedBy: 'recruiter@company.com',
      proofHash: 'SHA256:7f9a882e3b1c4d5e90a88b1f23c907a',
      proofSnippet: 'Direct confirmation via LinkedIn candidate opt-in form #CF-9821.',
      proofMethod: 'LinkedIn Candidate Opt-in Form #CF-9821'
    },
    activityTimeline: [
      {
        action: 'Screened: score 72 calculated automatically',
        timestamp: '18 Oct 2026, 14:20 IST',
        actor: 'HirePath System',
        type: 'system'
      },
      {
        action: 'Consent recorded by recruiter@company.com via LinkedIn direct verification',
        timestamp: '12 Oct 2026, 10:15 IST',
        actor: 'recruiter@company.com',
        type: 'consent'
      },
      {
        action: 'Sourced: matched public profile from GitHub',
        timestamp: '11 Oct 2026, 16:42 IST',
        actor: 'HirePath System',
        type: 'system'
      }
    ]
  },
  {
    id: '#CAN-8822',
    name: 'Vikram Joshi',
    roleId: 'pune-backend',
    roleTitle: 'Senior Backend Engineer, Pune',
    title: 'Staff Backend & Kafka Engineer',
    avatar: 'VJ',
    publicProfiles: {
      github: 'github.com/vjoshi'
    },
    reposCount: 26,
    followersCount: '580',
    email: 'vikram.joshi@techcorp.in',
    maskedEmail: 'v****@techcorp.in',
    isEmailRevealed: false,
    matchScore: 61,
    scoreBreakdown: {
      coreStack: {
        score: 22,
        max: 30,
        label: 'Core Stack (Python & Async)',
        desc: '6 public Python repositories. Strong asyncio event loop patterns.',
        evidence: 'https://github.com/vjoshi/async-pipeline'
      },
      distributedSystems: {
        score: 20,
        max: 25,
        label: 'Message Queues & Kafka',
        desc: 'Extensive Kafka partition handling repositories and schema registry use.',
        evidence: 'https://github.com/vjoshi/kafka-streamer'
      },
      experience: {
        score: 11,
        max: 25,
        label: 'Seniority & Track Record',
        desc: 'First public commit 2020 (6 years). Solid production history.',
        evidence: 'GitHub activity check'
      },
      recency: {
        score: 8,
        max: 20,
        label: 'Activity Recency',
        desc: 'Active last week with 3 merged PRs in private enterprise mirrors.',
        evidence: 'GitHub public telemetry'
      }
    },
    location: 'Pune',
    locationConfidence: 'Medium',
    rawLocationSignals: {
      locationString: 'Pune, India',
      company: 'TechCorp India',
      timezone: 'UTC+05:30',
      note: 'Location string matches target metropolitan region.'
    },
    source: 'GitHub',
    stage: 'screened',
    lastAction: {
      action: 'Screened',
      timestamp: '18 Oct, 11:05 IST'
    },
    consent: {
      status: 'pending',
      proofMethod: 'GitHub Public Activity (Awaiting reply)',
      proofSnippet: 'Candidate sourced via public indexing. Direct written consent pending verification under Section 6(1).'
    },
    activityTimeline: [
      {
        action: 'Screened: score 61 calculated',
        timestamp: '18 Oct 2026, 11:05 IST',
        actor: 'HirePath System',
        type: 'system'
      },
      {
        action: 'Outreach gate locked: pending DPDPA consent proof',
        timestamp: '18 Oct 2026, 11:05 IST',
        actor: 'Policy Engine',
        type: 'audit'
      },
      {
        action: 'Sourced from GitHub search location="Pune" AND "python"',
        timestamp: '18 Oct 2026, 11:02 IST',
        actor: 'HirePath System',
        type: 'system'
      }
    ]
  },
  {
    id: '#CAN-8823',
    name: 'Priya Sharma',
    roleId: 'pune-backend',
    roleTitle: 'Senior Backend Engineer, Pune',
    title: 'Lead Distributed Systems Architect',
    avatar: 'PS',
    publicProfiles: {
      github: 'github.com/psharma-dev'
    },
    reposCount: 38,
    followersCount: '2.1k',
    email: 'priya.sharma@techlead.co',
    maskedEmail: 'p****@domain.dev',
    isEmailRevealed: false,
    matchScore: 84,
    scoreBreakdown: {
      coreStack: {
        score: 29,
        max: 30,
        label: 'Core Stack (FastAPI & Rust)',
        desc: 'Top 1% contributor on asynchronous networking libraries with high test coverage.',
        evidence: 'https://github.com/psharma-dev/rust-fast-net'
      },
      distributedSystems: {
        score: 24,
        max: 25,
        label: 'Consensus & Raft',
        desc: 'Built custom Raft consensus implementation in Python/Rust.',
        evidence: 'https://github.com/psharma-dev/paxos-raft'
      },
      experience: {
        score: 18,
        max: 25,
        label: 'Industry Longevity',
        desc: '10+ years engineering track record across high-scale fintech systems.',
        evidence: 'Open source provenance verified'
      },
      recency: {
        score: 13,
        max: 20,
        label: 'Code Contributions',
        desc: 'Pushed code yesterday, continuous commits throughout 2026.',
        evidence: 'Public commit log'
      }
    },
    location: 'Pune, Maharashtra',
    locationConfidence: 'High',
    rawLocationSignals: {
      locationString: 'Kalyani Nagar, Pune',
      company: 'TechLead Co',
      timezone: 'UTC+05:30',
      note: 'Verified local residence in Pune east tech corridor.'
    },
    source: 'StackOverflow',
    stage: 'screened',
    lastAction: {
      action: 'Screened',
      timestamp: '17 Oct, 16:45 IST'
    },
    consent: {
      status: 'recorded',
      recordedDate: '14 Oct 2026',
      expiryDate: '14 Oct 2027',
      daysRemaining: 360,
      channel: 'Verified InMail written consent response',
      recordedBy: 'anupama.rao@company.com',
      proofHash: 'SHA256:3a110cb849182d77ef4e0a6d51c08fe',
      proofSnippet: 'Candidate confirmed opt-in to technical leadership opportunities at HirePath on 14 Oct.',
      proofMethod: 'Verified InMail consent'
    },
    activityTimeline: [
      {
        action: 'Screened: score 84 calculated automatically',
        timestamp: '17 Oct 2026, 16:45 IST',
        actor: 'HirePath System',
        type: 'system'
      },
      {
        action: 'Consent verified by anupama.rao@company.com',
        timestamp: '14 Oct 2026, 09:15 IST',
        actor: 'anupama.rao@company.com',
        type: 'consent'
      }
    ]
  },
  {
    id: '#CAN-8824',
    name: 'Rohan Kulkarni',
    roleId: 'pune-backend',
    roleTitle: 'Senior Backend Engineer, Pune',
    title: 'Senior Cloud Platform & Data Engineer',
    avatar: 'RK',
    publicProfiles: {
      github: 'github.com/rohank'
    },
    reposCount: 31,
    followersCount: '890',
    email: 'rohan.kulkarni@fastmail.com',
    maskedEmail: 'r****@fastmail.com',
    isEmailRevealed: false,
    matchScore: 78,
    scoreBreakdown: {
      coreStack: {
        score: 26,
        max: 30,
        label: 'Core Stack (Python & gRPC)',
        desc: 'Microservices in Python with Protobuf and high-throughput gRPC servers.',
        evidence: 'https://github.com/rohank/py-grpc-core'
      },
      distributedSystems: {
        score: 22,
        max: 25,
        label: 'Docker & Kubernetes',
        desc: 'Certified CKA with Helm charts and operator code in production.',
        evidence: 'https://github.com/rohank/k8s-operator'
      },
      experience: {
        score: 16,
        max: 25,
        label: 'Seniority',
        desc: '7 years backend experience with focus on telemetry and databases.',
        evidence: 'Verified profile'
      },
      recency: {
        score: 14,
        max: 20,
        label: 'Activity',
        desc: 'Active 2 days ago.',
        evidence: 'GitHub verified'
      }
    },
    location: 'Pune, Maharashtra',
    locationConfidence: 'High',
    rawLocationSignals: {
      locationString: 'Baner, Pune',
      company: 'Platform Works',
      timezone: 'UTC+05:30',
      note: 'Verified residence in Pune west corridor.'
    },
    source: 'GitHub',
    stage: 'screened',
    lastAction: {
      action: 'Screened',
      timestamp: '17 Oct, 09:15 IST'
    },
    consent: {
      status: 'recorded',
      recordedDate: '09 Oct 2026',
      expiryDate: '09 Oct 2027',
      daysRemaining: 355,
      channel: 'Direct written referral consent letter signed via DocuSign',
      recordedBy: 'recruiter@company.com',
      proofHash: 'SHA256:d84fe982b610c14479e001ba924b102',
      proofSnippet: 'Referral consent letter DocuSign #DOC-8921-RK.',
      proofMethod: 'Direct referral written consent'
    },
    activityTimeline: [
      {
        action: 'Screened: score 78 calculated',
        timestamp: '17 Oct 2026, 09:15 IST',
        actor: 'HirePath System',
        type: 'system'
      }
    ]
  },
  {
    id: '#CAN-8825',
    name: 'Ananya Deshmukh',
    roleId: 'pune-backend',
    roleTitle: 'Senior Backend Engineer, Pune',
    title: 'Senior API & Database Engineer',
    avatar: 'AD',
    publicProfiles: {
      github: 'github.com/adeshmukh'
    },
    reposCount: 22,
    followersCount: '440',
    email: 'ananya.deshmukh@cloudtech.in',
    maskedEmail: 'a****@cloudtech.in',
    isEmailRevealed: false,
    matchScore: 69,
    scoreBreakdown: {
      coreStack: {
        score: 24,
        max: 30,
        label: 'Core Stack (FastAPI & PostgreSQL)',
        desc: 'Strong SQL query optimization and SQLAlchemy AsyncIO code.',
        evidence: 'https://github.com/adeshmukh/pg-async'
      },
      distributedSystems: {
        score: 18,
        max: 25,
        label: 'Distributed Architecture',
        desc: 'Redis caching and Celery task broker configurations.',
        evidence: 'Repository inspection'
      },
      experience: {
        score: 14,
        max: 25,
        label: 'Seniority',
        desc: '6 years experience.',
        evidence: 'Profile verified'
      },
      recency: {
        score: 13,
        max: 20,
        label: 'Activity',
        desc: 'Active last week.',
        evidence: 'GitHub streak'
      }
    },
    location: 'Pune',
    locationConfidence: 'Medium',
    rawLocationSignals: {
      locationString: 'Pune, Maharashtra',
      company: 'CloudTech',
      timezone: 'UTC+05:30',
      note: 'Location confirmed in Maharashtra state.'
    },
    source: 'GitHub',
    stage: 'screened',
    lastAction: {
      action: 'Screened',
      timestamp: '16 Oct, 18:30 IST'
    },
    consent: {
      status: 'pending',
      proofMethod: 'GitHub Public Activity (Consent not recorded)',
      proofSnippet: 'Candidate sourced via automated batch #14. Consent verification required before email contact.'
    },
    activityTimeline: [
      {
        action: 'Screened: score 69 calculated',
        timestamp: '16 Oct 2026, 18:30 IST',
        actor: 'HirePath System',
        type: 'system'
      }
    ]
  },
  {
    id: '#CAN-8826',
    name: 'Karthik Nair',
    roleId: 'pune-backend',
    roleTitle: 'Senior Backend Engineer, Pune',
    title: 'Distributed Systems & Go/Python Engineer',
    avatar: 'KN',
    publicProfiles: {
      github: 'github.com/knair-code'
    },
    reposCount: 35,
    followersCount: '670',
    email: 'karthik.nair@devmesh.io',
    maskedEmail: 'k****@devmesh.io',
    isEmailRevealed: false,
    matchScore: 65,
    scoreBreakdown: {
      coreStack: {
        score: 23,
        max: 30,
        label: 'Core Stack (Python & Docker)',
        desc: 'Containerized Python microservices with robust health checks.',
        evidence: 'https://github.com/knair-code/dock-py'
      },
      distributedSystems: {
        score: 19,
        max: 25,
        label: 'Message Queues',
        desc: 'RabbitMQ integration and event-driven patterns.',
        evidence: 'Repository inspection'
      },
      experience: {
        score: 13,
        max: 25,
        label: 'Seniority',
        desc: '5+ years experience.',
        evidence: 'Profile check'
      },
      recency: {
        score: 10,
        max: 20,
        label: 'Activity',
        desc: 'Active within past 10 days.',
        evidence: 'Public commit log'
      }
    },
    location: 'Mumbai (Relocating)',
    locationConfidence: 'Medium',
    rawLocationSignals: {
      locationString: 'Mumbai (Open to Pune relocation)',
      company: 'DevMesh Solutions',
      timezone: 'UTC+05:30',
      note: 'Profile explicitly notes Pune relocation preference.'
    },
    source: 'StackOverflow',
    stage: 'screened',
    lastAction: {
      action: 'Screened',
      timestamp: '16 Oct, 12:10 IST'
    },
    consent: {
      status: 'recorded',
      recordedDate: '11 Oct 2026',
      expiryDate: '11 Oct 2027',
      daysRemaining: 357,
      channel: 'Direct email opt-in confirmed',
      recordedBy: 'recruiter@company.com',
      proofHash: 'SHA256:5a990cd21b44e019f8721cc0981a3',
      proofSnippet: 'Direct candidate application from recruitment fair.',
      proofMethod: 'Direct written consent'
    },
    activityTimeline: [
      {
        action: 'Screened: score 65 calculated',
        timestamp: '16 Oct 2026, 12:10 IST',
        actor: 'HirePath System',
        type: 'system'
      }
    ]
  }
];

export const initialAuditEvents: AuditEvent[] = [
  {
    id: 'EV-1084',
    timestamp: '20 Oct 2026, 11:38',
    category: 'screening',
    actorCategory: 'HirePath System',
    eventDescription: 'HirePath screened 12 sourced candidates for Senior Backend Engineer, Pune: average score 68, top candidate Asha Rao (score 72)',
    targetEntity: 'Senior Backend Engineer, Pune',
    auditHash: 'b83f...921a',
    status: 'success'
  },
  {
    id: 'EV-1083',
    timestamp: '20 Oct 2026, 11:24',
    category: 'consent',
    actorCategory: 'Recruiter Ops',
    eventDescription: 'Recruiter recorded direct written consent for Vikram Joshi (#CAN-8822) via verified LinkedIn InMail',
    targetEntity: 'Vikram Joshi (#CAN-8822)',
    auditHash: '79ac...410f',
    status: 'success'
  },
  {
    id: 'EV-1082',
    timestamp: '20 Oct 2026, 11:15',
    category: 'outreach',
    actorCategory: 'Policy Engine',
    eventDescription: 'Outreach blocked for Vikram Joshi: outreach gate enforced under DPDPA 2023 Section 6(1) pending consent audit',
    targetEntity: 'Vikram Joshi (#CAN-8822)',
    auditHash: '91a0...8ce2',
    status: 'blocked'
  },
  {
    id: 'EV-1081',
    timestamp: '20 Oct 2026, 10:52',
    category: 'screening',
    actorCategory: 'anupama.rao',
    eventDescription: 'Interview scheduled with Asha Rao for Technical Screen (Round 1) on 21 Oct 2026, 11:00 IST by anupama.rao@company.com',
    targetEntity: 'Asha Rao (#CAN-8821)',
    auditHash: '4f2a...10bc',
    status: 'success'
  },
  {
    id: 'EV-1080',
    timestamp: '20 Oct 2026, 10:30',
    category: 'optout',
    actorCategory: 'Privacy Portal',
    eventDescription: 'Candidate opt-out recorded: Sneha Patil (#CAN-8790) requested communication suppression via Public Privacy Portal',
    targetEntity: 'Sneha Patil (#CAN-8790)',
    auditHash: '89e2...c411',
    status: 'success'
  },
  {
    id: 'EV-1079',
    timestamp: '20 Oct 2026, 09:44',
    category: 'sourcing',
    actorCategory: 'HirePath System',
    eventDescription: 'HirePath paused sourcing run #SR-4092: waiting for GitHub rate limit, resumed after 42 s',
    targetEntity: 'Sourcing Run #SR-4092',
    auditHash: '10df...bb99',
    status: 'rate_limited'
  },
  {
    id: 'EV-1078',
    timestamp: '20 Oct 2026, 09:41',
    category: 'sourcing',
    actorCategory: 'HirePath System',
    eventDescription: 'HirePath completed sourcing run #SR-4092: found 84 profiles, accepted 19 candidates matching Pune location criteria',
    targetEntity: 'Senior Backend Engineer, Pune',
    auditHash: '3a21...ef02',
    status: 'success'
  },
  {
    id: 'EV-1077',
    timestamp: '20 Oct 2026, 09:12',
    category: 'outreach',
    actorCategory: 'Recruiter Ops',
    eventDescription: 'Recruiter sent outreach batch #OB-104: 3 emails queued with 10 s undo window for Senior Backend Engineer, Pune',
    targetEntity: 'Outreach Batch #OB-104',
    auditHash: '67ff...d019',
    status: 'success'
  },
  {
    id: 'EV-1076',
    timestamp: '20 Oct 2026, 09:12',
    category: 'outreach',
    actorCategory: 'Mail Gateway',
    eventDescription: 'Undo window expired for outreach batch #OB-104: 3 messages dispatched via verified company mail gateway',
    targetEntity: 'Outreach Batch #OB-104',
    auditHash: 'ee99...3841',
    status: 'success'
  },
  {
    id: 'EV-1075',
    timestamp: '20 Oct 2026, 08:50',
    category: 'screening',
    actorCategory: 'HirePath System',
    eventDescription: 'Candidate Asha Rao moved from Sourced to Screened: score 72 with High confidence location match (Pune, Maharashtra)',
    targetEntity: 'Asha Rao (#CAN-8821)',
    auditHash: '92df...bb44',
    status: 'success'
  },
  {
    id: 'EV-1074',
    timestamp: '20 Oct 2026, 08:32',
    category: 'inspection',
    actorCategory: 'Recruiter Ops',
    eventDescription: 'Recruiter viewed masked email for Asha Rao: audit record logged under regulatory inspection policy',
    targetEntity: 'Asha Rao (#CAN-8821)',
    auditHash: '552e...11af',
    status: 'success'
  },
  {
    id: 'EV-1073',
    timestamp: '20 Oct 2026, 08:10',
    category: 'system',
    actorCategory: 'Audit Ledger',
    eventDescription: 'Cryptographic proof hash generated for suppression entry #SP-9912: 89e27c1...c411 written to immutable ledger',
    targetEntity: 'Suppression #SP-9912',
    auditHash: '89e2...c411',
    status: 'success'
  }
];

export const initialConsentRecords: ConsentRecord[] = [
  {
    id: 'REC-90812-IN',
    candidateName: 'Asha Rao',
    maskedEmail: 'a***@workmail.io',
    role: 'Senior Backend Engineer',
    status: 'recorded',
    recordedDate: '12 Oct 2026',
    expiryDate: '12 Oct 2027',
    daysRemaining: 358,
    proofMethod: 'LinkedIn Candidate Opt-in Form #CF-9821',
    proofSnippet: 'Opted in via verified candidate form for backend roles in Pune territory.',
    proofHash: 'SHA256:7f9a882e3b1c4d5e90a88b1f23c907a',
    scope: 'India (DPDPA 2023) · Active',
    recordedBy: 'Recruiter ops'
  },
  {
    id: 'REC-90814-IN',
    candidateName: 'Priya Sharma',
    maskedEmail: 'p***@domain.dev',
    role: 'Senior Backend Engineer',
    status: 'recorded',
    recordedDate: '14 Oct 2026',
    expiryDate: '14 Oct 2027',
    daysRemaining: 360,
    proofMethod: 'Verified InMail consent',
    proofSnippet: 'Candidate confirmed opt-in via InMail thread response on 14 Oct 09:15 IST.',
    proofHash: 'SHA256:3a110cb849182d77ef4e0a6d51c08fe',
    scope: 'India (DPDPA 2023) · Active',
    recordedBy: 'anupama.rao@company.com'
  },
  {
    id: 'REC-90819-PEND',
    candidateName: 'Vikram Joshi',
    maskedEmail: 'v***@techcorp.in',
    role: 'Senior Backend Engineer',
    status: 'pending',
    recordedDate: '18 Oct 2026',
    expiryDate: 'Pending verification',
    daysRemaining: 0,
    proofMethod: 'GitHub (Awaiting reply)',
    proofSnippet: 'Candidate sourced via public activity. No verified direct written consent logged yet.',
    proofHash: 'SHA256:pending_consent_signature_vj',
    scope: 'India (DPDPA 2023) · Pending',
    recordedBy: 'System auto-flag'
  },
  {
    id: 'REC-90799-IN',
    candidateName: 'Rohan Kulkarni',
    maskedEmail: 'r***@fastmail.com',
    role: 'Senior Backend Engineer',
    status: 'recorded',
    recordedDate: '09 Oct 2026',
    expiryDate: '09 Oct 2027',
    daysRemaining: 355,
    proofMethod: 'Direct referral written consent',
    proofSnippet: 'Signed referral agreement via DocuSign #DOC-8921-RK.',
    proofHash: 'SHA256:d84fe982b610c14479e001ba924b102',
    scope: 'India (DPDPA 2023) · Active',
    recordedBy: 'Recruiter ops'
  },
  {
    id: 'REC-89211-REVOKED',
    candidateName: 'Sneha Patil',
    maskedEmail: 's***@cloudscale.io',
    role: 'Lead DevOps Engineer',
    status: 'withdrawn',
    recordedDate: '16 Oct 2026',
    expiryDate: 'Suppressed permanently',
    daysRemaining: 0,
    proofMethod: 'Candidate opt-out request',
    proofSnippet: 'Candidate triggered self-service opt-out form on Public Privacy Portal on 16 Oct.',
    proofHash: 'SHA256:000a7b45f1e892c901844ac114eb',
    scope: 'Global · Revoked',
    recordedBy: 'Self-service portal'
  }
];
