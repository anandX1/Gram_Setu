/**
 * AI GramSetu — server.js
 * -----------------------
 * Run once with:  node server.js
 * Then open:      http://localhost:3000/index.html
 *
 * Auth routes (workers/admin):
 *   POST /auth/signup
 *   POST /auth/signin
 *
 * Employer routes:
 *   POST /employer/signup        — register employer account
 *   POST /employer/signin        — login employer
 *   POST /employer/jobs          — post a new job
 *   GET  /employer/jobs?id=      — get jobs for an employer
 *   POST /employer/jobs/complete — mark job as complete
 *   POST /employer/reviews       — submit worker review
 *   GET  /employer/workers?jobId= — get workers assigned to a job (from admin portal)
 *
 * Serves all static files automatically.
 */

const http = require('http');
const fs   = require('fs');
const path = require('path');
const nodemailer = require('nodemailer');

const PORT    = 3000;
const DB_FILE = path.join(__dirname, 'db.json');

// ── Communication Gateway ──────────────────────────────────────────────────────

let etherealTransporter = null;
nodemailer.createTestAccount((err, account) => {
  if (err) {
    console.error('Failed to create a testing account. ' + err.message);
    return;
  }
  console.log('Ethereal Email account created. Ready to send free simulated emails!');
  etherealTransporter = nodemailer.createTransport({
    host: account.smtp.host,
    port: account.smtp.port,
    secure: account.smtp.secure,
    auth: { user: account.user, pass: account.pass }
  });
});

function sendFreeEmail(to, subject, text) {
  if (!etherealTransporter) return;
  etherealTransporter.sendMail({
    from: '"AI GramSetu System" <admin@aigramsetu.org>',
    to: to,
    subject: subject,
    text: text
  }, (err, info) => {
    if (err) return console.log('Error occurred. ' + err.message);
    console.log('====================================');
    console.log('FREE EMAIL SENT (Preview URL): %s', nodemailer.getTestMessageUrl(info));
    console.log('====================================');
  });
}

function sendFreeSMS(to, text) {
  const smsLogFile = path.join(__dirname, 'sms_outbox.json');
  let logs = [];
  if (fs.existsSync(smsLogFile)) {
    try { logs = JSON.parse(fs.readFileSync(smsLogFile, 'utf8')); } catch(e){}
  }
  logs.push({ timestamp: new Date().toISOString(), to: to, message: text });
  fs.writeFileSync(smsLogFile, JSON.stringify(logs, null, 2));
  console.log('====================================');
  console.log(`[SIMULATED SMS to ${to}]: ${text}`);
  console.log('Saved to sms_outbox.json');
  console.log('====================================');
}

// ── DB helpers ────────────────────────────────────────────────────────────────

function readDB() {
  if (!fs.existsSync(DB_FILE)) {
    const empty = { users: [], sessions: [], employers: [], employer_jobs: [], reviews: [] };
    fs.writeFileSync(DB_FILE, JSON.stringify(empty, null, 2));
    return empty;
  }
  try {
    const db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    if (!db.employers)     db.employers     = [];
    if (!db.employer_jobs) db.employer_jobs = [];
    if (!db.reviews)       db.reviews       = [];
    return db;
  } catch {
    return { users: [], sessions: [], employers: [], employer_jobs: [], reviews: [] };
  }
}

function writeDB(db) {
  fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
}

function encodePassword(plain) { return Buffer.from(plain).toString('base64'); }
function checkPassword(plain, encoded) { return Buffer.from(plain).toString('base64') === encoded; }

// ── Parse POST body helper ────────────────────────────────────────────────────

function parseBody(req, cb) {
  let raw = '';
  req.on('data', chunk => raw += chunk);
  req.on('end', () => {
    try { cb(null, JSON.parse(raw)); }
    catch { cb(new Error('Bad JSON')); }
  });
}

function respond(res, status, obj) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(obj));
}

// ── Admin/worker auth ─────────────────────────────────────────────────────────

function handleSignup(body, res) {
  const db = readDB();
  const { name, email, phone, password, method } = body;
  if (!name) return respond(res, 400, { ok: false, error: 'Name is required.' });

  if (method === 'email') {
    if (!email || !password) return respond(res, 400, { ok: false, error: 'Email and password required.' });
    if (db.users.find(u => u.email === email))
      return respond(res, 400, { ok: false, error: 'Email already registered.' });
    db.users.push({ id: 'u_' + Date.now(), name, email, password: encodePassword(password), method: 'email', createdAt: new Date().toISOString() });
  } else if (method === 'sms') {
    if (!phone) return respond(res, 400, { ok: false, error: 'Phone required.' });
    if (db.users.find(u => u.phone === phone))
      return respond(res, 400, { ok: false, error: 'Phone already registered.' });
    db.users.push({ id: 'u_' + Date.now(), name, phone, method: 'sms', createdAt: new Date().toISOString() });
  } else return respond(res, 400, { ok: false, error: 'Invalid method.' });

  const user = db.users[db.users.length - 1];
  db.sessions = [{ userId: user.id, name, loginAt: new Date().toISOString() }, ...db.sessions].slice(0, 50);
  writeDB(db);
  console.log(`[signup] ${name} (${method})`);

  if (method === 'email') sendFreeEmail(email, 'Welcome to AI GramSetu', `Hello ${name}, welcome to AI GramSetu!`);
  if (method === 'sms') sendFreeSMS(phone, `Hello ${name}, welcome to AI GramSetu! Your account is active.`);

  respond(res, 200, { ok: true, name });
}

function handleSignin(body, res) {
  const db = readDB();
  const { email, phone, password, method } = body;
  let user;
  if (method === 'email') {
    if (!email || !password) return respond(res, 400, { ok: false, error: 'Email and password required.' });
    user = db.users.find(u => u.email === email);
    if (!user) return respond(res, 401, { ok: false, error: 'No account found for this email.' });
    if (!checkPassword(password, user.password)) return respond(res, 401, { ok: false, error: 'Incorrect password.' });
  } else if (method === 'sms') {
    if (!phone) return respond(res, 400, { ok: false, error: 'Phone required.' });
    user = db.users.find(u => u.phone === phone);
    if (!user) return respond(res, 401, { ok: false, error: 'No account found for this number.' });
  } else return respond(res, 400, { ok: false, error: 'Invalid method.' });
  db.sessions = [{ userId: user.id, name: user.name, loginAt: new Date().toISOString() }, ...db.sessions].slice(0, 50);
  writeDB(db);
  console.log(`[signin] ${user.name} (${method})`);
  respond(res, 200, { ok: true, name: user.name });
}

// ── Employer routes ───────────────────────────────────────────────────────────

// POST /employer/signup
function handleEmployerSignup(body, res) {
  const db = readDB();
  const { name, email, password, company, phone } = body;
  if (!name || !email || !password) return respond(res, 400, { ok: false, error: 'Name, email and password are required.' });
  if (db.employers.find(e => e.email === email))
    return respond(res, 400, { ok: false, error: 'An employer account with this email already exists.' });

  const employer = {
    id       : 'emp_' + Date.now(),
    name, email, company: company || '', phone: phone || '',
    password : encodePassword(password),
    createdAt: new Date().toISOString()
  };
  db.employers.push(employer);
  writeDB(db);
  console.log(`[employer signup] ${name} — ${company}`);

  sendFreeEmail(email, 'Welcome Employer', `Hello ${name}, welcome to AI GramSetu! You can now post jobs for ${company}.`);

  respond(res, 200, { ok: true, employer: { id: employer.id, name, email, company: employer.company } });
}

// POST /employer/signin
function handleEmployerSignin(body, res) {
  const db = readDB();
  const { email, password } = body;
  if (!email || !password) return respond(res, 400, { ok: false, error: 'Email and password required.' });
  const employer = db.employers.find(e => e.email === email);
  if (!employer) return respond(res, 401, { ok: false, error: 'No employer account found for this email.' });
  if (!checkPassword(password, employer.password)) return respond(res, 401, { ok: false, error: 'Incorrect password.' });
  console.log(`[employer signin] ${employer.name}`);
  respond(res, 200, { ok: true, employer: { id: employer.id, name: employer.name, email, company: employer.company } });
}

// POST /employer/jobs  — post a new job
function handlePostJob(body, res) {
  const db = readDB();
  const { employerId, title, location, skillRequired, workersNeeded, payRate, startDate, description } = body;
  if (!employerId || !title || !location)
    return respond(res, 400, { ok: false, error: 'employerId, title and location are required.' });
  if (!db.employers.find(e => e.id === employerId))
    return respond(res, 401, { ok: false, error: 'Unknown employer.' });

  const job = {
    id            : 'ejob_' + Date.now(),
    employerId, title, location,
    skillRequired : skillRequired || '',
    workersNeeded : workersNeeded || 1,
    payRate       : payRate || 0,
    startDate     : startDate || '',
    description   : description || '',
    status        : 'Open',       // Open | Assigned | Completed
    assignedWorkers: [],
    completedAt   : null,
    createdAt     : new Date().toISOString()
  };
  db.employer_jobs.push(job);
  writeDB(db);
  console.log(`[job posted] "${title}" by employer ${employerId}`);
  respond(res, 200, { ok: true, job });
}

// GET /employer/jobs?employerId=xxx
function handleGetJobs(query, res) {
  const db = readDB();
  const employerId = query.get('employerId');
  if (!employerId) return respond(res, 400, { ok: false, error: 'employerId required.' });

  const jobs = db.employer_jobs.filter(j => j.employerId === employerId);

  // For each job, attach review info and worker details from admin portal workers
  const enriched = jobs.map(j => {
    const reviews = db.reviews.filter(r => r.jobId === j.id);
    const workers = (j.assignedWorkers || []).map(wid => {
      // Look up in admin workers list
      const w = (db.workers || []).find(w => String(w.id) === String(wid));
      return w ? { id: w.id, name: w.name, skill: w.skill, phone: w.phone } : { id: wid, name: 'Unknown' };
    });
    return { ...j, reviews, workerDetails: workers };
  });

  respond(res, 200, { ok: true, jobs: enriched });
}

// POST /employer/jobs/complete
function handleCompleteJob(body, res) {
  const db = readDB();
  const { jobId, employerId } = body;
  if (!jobId || !employerId) return respond(res, 400, { ok: false, error: 'jobId and employerId required.' });
  const job = db.employer_jobs.find(j => j.id === jobId && j.employerId === employerId);
  if (!job) return respond(res, 404, { ok: false, error: 'Job not found.' });
  if (job.status === 'Completed') return respond(res, 400, { ok: false, error: 'Job already completed.' });
  job.status      = 'Completed';
  job.completedAt = new Date().toISOString();
  writeDB(db);
  console.log(`[job completed] ${jobId}`);
  respond(res, 200, { ok: true, job });
}

// POST /employer/reviews
function handlePostReview(body, res) {
  const db = readDB();
  const { jobId, employerId, workerId, workerName, rating, feedback } = body;
  if (!jobId || !employerId || !workerId || !rating)
    return respond(res, 400, { ok: false, error: 'jobId, employerId, workerId and rating required.' });
  const job = db.employer_jobs.find(j => j.id === jobId && j.employerId === employerId);
  if (!job) return respond(res, 404, { ok: false, error: 'Job not found.' });
  if (job.status !== 'Completed') return respond(res, 400, { ok: false, error: 'Can only review completed jobs.' });

  // Prevent duplicate review for same worker+job
  const existing = db.reviews.find(r => r.jobId === jobId && r.workerId === workerId);
  if (existing) {
    existing.rating   = rating;
    existing.feedback = feedback || '';
    existing.updatedAt = new Date().toISOString();
  } else {
    db.reviews.push({
      id: 'rev_' + Date.now(),
      jobId, employerId, workerId,
      workerName: workerName || '',
      rating, feedback: feedback || '',
      createdAt: new Date().toISOString()
    });
  }
  writeDB(db);
  console.log(`[review] job ${jobId}, worker ${workerId}, rating ${rating}`);
  respond(res, 200, { ok: true });
}

// GET /employer/workers?jobId=xxx  — workers assigned to a job in admin portal
function handleGetWorkers(query, res) {
  const db    = readDB();
  const jobId = query.get('jobId');
  // Look for the job in admin jobs (db.jobs) by matching title if jobId is employer job id
  // But employer can also manually add workers. We just return admin workers for reference.
  // Here we return ALL admin-registered workers so employer can pick who worked for them.
  const workers = (db.workers || []).map(w => ({
    id: w.id, name: w.name, skill: w.skill, phone: w.phone,
    availability: w.availability, experience: w.experience
  }));
  respond(res, 200, { ok: true, workers });
}

// POST /employer/jobs/assign  — admin assigns workers to an employer job
function handleAssignWorkers(body, res) {
  const db = readDB();
  const { jobId, workerIds } = body;
  if (!jobId || !Array.isArray(workerIds))
    return respond(res, 400, { ok: false, error: 'jobId and workerIds[] required.' });

  const job = db.employer_jobs.find(j => j.id === jobId);
  if (!job) return respond(res, 404, { ok: false, error: 'Employer job not found.' });

  // Free workers that are being unassigned
  const prev = job.assignedWorkers || [];
  prev.forEach(wid => {
    if (!workerIds.includes(wid)) {
      const w = (db.workers || []).find(w => String(w.id) === String(wid));
      if (w && w.availability === 'Busy') w.availability = 'Available';
    }
  });

  // Assign new workers
  job.assignedWorkers = workerIds;
  if (workerIds.length > 0 && job.status === 'Open') job.status = 'Assigned';
  if (workerIds.length === 0 && job.status === 'Assigned') job.status = 'Open';

  // Mark assigned workers as Busy in admin workers list
  workerIds.forEach(wid => {
    const w = (db.workers || []).find(w => String(w.id) === String(wid));
    if (w) w.availability = 'Busy';
  });

  writeDB(db);
  console.log();
  respond(res, 200, { ok: true, job });
}

// GET /employer/jobs-all  — all employer jobs (for admin portal display)
function handleGetAllJobs(res) {
  const db = readDB();
  // Enrich with worker details from admin workers list
  const jobs = (db.employer_jobs || []).map(j => {
    const workerDetails = (j.assignedWorkers || []).map(wid => {
      const w = (db.workers || []).find(w => String(w.id) === String(wid));
      return w ? { id: w.id, name: w.name, skill: w.skill, phone: w.phone } : { id: wid, name: 'Unknown' };
    });
    const reviews = (db.reviews || []).filter(r => r.jobId === j.id);
    return { ...j, workerDetails, reviews };
  });
  respond(res, 200, { ok: true, jobs });
}

function handleBroadcastSMS(body, res) {
  const { phone, message } = body;
  if (!phone || !message) return respond(res, 400, { ok: false, error: 'Phone and message required.' });
  sendFreeSMS(phone, message);
  respond(res, 200, { ok: true });
}

function handleBroadcastEmail(body, res) {
  const { email, subject, message } = body;
  if (!email || !message) return respond(res, 400, { ok: false, error: 'Email and message required.' });
  sendFreeEmail(email, subject || 'AI GramSetu Notification', message);
  respond(res, 200, { ok: true });
}

function handleVoiceCheckin(body, res) {
  const { workerName, dateStr } = body;
  if (!workerName || !dateStr) return respond(res, 400, { ok: false, error: 'workerName and dateStr required.' });

  // Simulate Voice Biometric matching
  const fraudDetected = Math.random() < 0.10; // 10% chance of proxy fraud

  if (fraudDetected) {
    console.log(`🚨 [FRAUD ALERT] Voice mismatch detected for ${workerName} on ${dateStr}. Potential proxy attendance.`);
    return respond(res, 200, { 
      ok: true, 
      verified: false, 
      message: 'Fraud Detected: Voice print mismatch. Proxy attendance suspected.' 
    });
  }

  // If verified, mark as present
  const db = readDB();
  if (!db.attendance) db.attendance = {};
  if (!db.attendance[dateStr]) db.attendance[dateStr] = {};
  
  db.attendance[dateStr][workerName] = { 
    status: 'Present', 
    time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) 
  };
  
  writeDB(db);
  console.log(`📞 [VOICE VERIFIED] ${workerName} marked present via voice check-in on ${dateStr}.`);
  
  respond(res, 200, { 
    ok: true, 
    verified: true, 
    message: 'Identity Verified. Attendance marked Present.' 
  });
}

function handleUpskillRecommend(body, res) {
  const { workerId, currentSkill } = body;
  if (!workerId || !currentSkill) return respond(res, 400, { ok: false, error: 'workerId and currentSkill required.' });

  // AI Skill Mapping Matrix
  const upskillMatrix = {
    'Farming': {
      targetSkill: 'Drip Irrigation Technician',
      wageIncrease: '+45% Daily Wage',
      modules: [
        'Module 1: Intro to Micro-Irrigation (Audio - 4 mins)',
        'Module 2: Pipe Laying & Water Pressure (Audio - 5 mins)',
        'Module 3: Troubleshooting Leaks (Interactive Voice Quiz)'
      ]
    },
    'Construction': {
      targetSkill: 'Solar Panel Mounter',
      wageIncrease: '+60% Daily Wage',
      modules: [
        'Module 1: Safety Gear for Roof Work (Audio - 3 mins)',
        'Module 2: Solar Panel Bracketing Basics (Audio - 6 mins)',
        'Module 3: Angle Alignment Practical (Video Guide - 5 mins)'
      ]
    },
    'Plumbing': {
      targetSkill: 'Rainwater Harvesting Installer',
      wageIncrease: '+35% Daily Wage',
      modules: [
        'Module 1: Filtration Systems (Audio - 5 mins)',
        'Module 2: Tank Connectivity (Audio - 4 mins)'
      ]
    },
    'Electrical': {
      targetSkill: 'Smart Grid Repair Tech',
      wageIncrease: '+80% Daily Wage',
      modules: [
        'Module 1: Smart Meter Basics (Audio - 6 mins)',
        'Module 2: Identifying Fault Codes (Audio - 4 mins)'
      ]
    }
  };

  // Fallback for skills not in the explicit matrix
  const defaultPathway = {
    targetSkill: `${currentSkill} Supervisor`,
    wageIncrease: '+30% Daily Wage',
    modules: [
      'Module 1: Team Leadership Basics (Audio - 5 mins)',
      'Module 2: Job Site Safety Management (Audio - 5 mins)'
    ]
  };

  const pathway = upskillMatrix[currentSkill] || defaultPathway;
  console.log(`[UPSKILL AI] Generated pathway for ${currentSkill} -> ${pathway.targetSkill}`);
  
  respond(res, 200, { ok: true, pathway });
}

// ── Static file server ────────────────────────────────────────────────────────

const MIME = {
  '.html':'text/html', '.css':'text/css', '.js':'application/javascript',
  '.json':'application/json', '.png':'image/png', '.jpg':'image/jpeg',
  '.jpeg':'image/jpeg', '.svg':'image/svg+xml', '.ico':'image/x-icon',
  '.woff':'font/woff', '.woff2':'font/woff2', '.ttf':'font/ttf',
};

function serveStatic(req, res) {
  let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
  if (path.basename(filePath) === 'db.json') { res.writeHead(403); res.end('Forbidden'); return; }
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404, { 'Content-Type': 'text/plain' }); res.end('404 Not Found: ' + req.url); return; }
    const ext  = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
}

// ── Main server ───────────────────────────────────────────────────────────────

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  const urlObj  = new URL(req.url, `http://localhost:${PORT}`);
  const urlPath = urlObj.pathname;
  const query   = urlObj.searchParams;

  // ── ML Server Proxy ──
  if (urlPath.startsWith('/ml/')) {
    const proxyReq = http.request(`http://localhost:5000${req.url}`, {
      method: req.method,
      headers: { ...req.headers, host: 'localhost:5000' }
    }, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });
    proxyReq.on('error', (e) => {
      res.writeHead(500); res.end(JSON.stringify({ ok: false, error: 'ML Server Proxy Error: ' + e.message }));
    });
    req.pipe(proxyReq);
    return;
  }

  // ── GET routes ──
  if (req.method === 'GET') {
    if (urlPath === '/employer/jobs')     return handleGetJobs(query, res);
    if (urlPath === '/employer/jobs-all') return handleGetAllJobs(res);
    if (urlPath === '/employer/workers')  return handleGetWorkers(query, res);
    return serveStatic(req, res);
  }

  // ── POST routes ──
  if (req.method === 'POST') {
    const POST_ROUTES = {
      '/auth/signup'           : handleSignup,
      '/auth/signin'           : handleSignin,
      '/employer/signup'       : handleEmployerSignup,
      '/employer/signin'       : handleEmployerSignin,
      '/employer/jobs'         : handlePostJob,
      '/employer/jobs/complete': handleCompleteJob,
      '/employer/jobs/assign'  : handleAssignWorkers,
      '/employer/reviews'      : handlePostReview,
      '/api/broadcast/sms'     : handleBroadcastSMS,
      '/api/broadcast/email'   : handleBroadcastEmail,
      '/api/attendance/voice-checkin': handleVoiceCheckin,
      '/api/upskill/recommend' : handleUpskillRecommend,
    };
    const handler = POST_ROUTES[urlPath];
    if (handler) {
      parseBody(req, (err, body) => {
        if (err) { res.writeHead(400); res.end('Bad JSON'); return; }
        handler(body, res);
      });
      return;
    }
  }

  serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log('');
  console.log('  AI GramSetu server running!');
  console.log(`  Open      → http://localhost:${PORT}/index.html`);
  console.log(`  Employer  → http://localhost:${PORT}/employer.html`);
  console.log(`  DB        → ${DB_FILE}`);
  console.log('');
});
