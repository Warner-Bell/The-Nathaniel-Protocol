// cred.js - Node twin of scripts/cred.py: reach a credential by card, never by a hardcoded path.
//
// Reads the card registry (Nate's-kb/credential-registry.json, metadata only) and resolves a
// card's `resolver` block. Values are returned to the calling process only. Nothing here
// prints a value; callers must not either (pass values to Playwright fill() or a header).
//
//   const cred = require('./cred');
//   cred.card('cred-001')               -> card metadata
//   cred.loginCard('content360')        -> { id, file, dir } for a web-login card (resolver.site)
//   cred.readLoginCard('content360', 2) -> parsed KEY=value map, plus KEY_ALL arrays; pair N
//                                          (1-based) sets USERNAME/PASSWORD from the Nth pair
//   cred.resolve('cred-002')            -> value for an env card (resolver.key, or opts.key)
//
// Python side, audit, and the security contract: scripts/cred.py. Procedure:
// Nate's-kb/security-protocol.md section 2.

const fs = require('fs');
const path = require('path');
const os = require('os');

const ROOT = path.resolve(__dirname, '..');
const REGISTRY = process.env.NATE_CRED_REGISTRY || path.join(ROOT, "Nate's-kb", 'credential-registry.json');

function load() {
  return JSON.parse(fs.readFileSync(REGISTRY, 'utf8'));
}

function rel(p) {
  if (p.startsWith('~/')) p = path.join(os.homedir(), p.slice(2));
  return path.isAbsolute(p) ? p : path.join(ROOT, p);
}

function card(id) {
  const c = (load().cards || []).find(x => x.id === id);
  if (!c) throw new Error(`no card ${id} in credential-registry.json`);
  return c;
}

function loginCard(site) {
  const c = (load().cards || []).find(x => x.resolver && x.resolver.site === site && x.resolver.file);
  if (!c) throw new Error(`no web-login card with resolver.site=${site}; add one to the registry`);
  const file = rel(c.resolver.file);
  return { id: c.id, file, dir: path.dirname(file) };
}

// KEY=value lines only; every other line is skipped unread. First occurrence wins
// for KEY; every occurrence is kept in KEY_ALL for multi-account cards.
function parseEnv(file) {
  if (!fs.existsSync(file)) throw new Error(`card file missing: ${path.basename(file)}`);
  const out = {};
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^([A-Z][A-Z0-9_]*)=(.*)$/);
    if (!m) continue;
    const [k, v] = [m[1], m[2].trim()];
    (out[`${k}_ALL`] = out[`${k}_ALL`] || []).push(v);
    if (!(k in out)) out[k] = v;
  }
  return out;
}

function readLoginCard(site, pair) {
  const values = parseEnv(loginCard(site).file);
  if (pair && pair > 1) {
    values.USERNAME = (values.USERNAME_ALL || [])[pair - 1];
    values.PASSWORD = (values.PASSWORD_ALL || [])[pair - 1];
  }
  return values;
}

function resolve(id, opts = {}) {
  const r = card(id).resolver || {};
  if (r.type !== 'env') throw new Error(`${id}: cred.js resolves env cards only (type ${r.type}); use cred.py`);
  const key = opts.key || r.key;
  const vals = parseEnv(rel(r.file))[`${key}_ALL`] || [];
  const v = vals[(opts.pair || 1) - 1];
  if (!v) throw new Error(`${id}: ${key} is empty or absent`);
  return v;
}

module.exports = { REGISTRY, load, card, loginCard, readLoginCard, parseEnv, resolve };
