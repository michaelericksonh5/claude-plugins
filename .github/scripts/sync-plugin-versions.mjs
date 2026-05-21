#!/usr/bin/env node
// Sync each plugin entry's `version` in .claude-plugin/marketplace.json
// to the version declared by that plugin's upstream plugin.json.
//
// - URL git sources       : fetch raw plugin.json from main/master (or `ref`)
// - GitHub shorthand src  : same, derived from owner/repo
// - Vendored ./plugins/X  : read the local copy in this repo
// - SHA-pinned sources    : skipped on purpose (pinning is intentional)
//
// The script uses a line-based, minimal-diff replacement so the existing
// JSON formatting is preserved exactly when no version changes.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const MARKETPLACE_PATH = path.join(REPO_ROOT, '.claude-plugin', 'marketplace.json');

const raw = fs.readFileSync(MARKETPLACE_PATH, 'utf8');
const data = JSON.parse(raw);

if (!Array.isArray(data.plugins)) {
  console.error('marketplace.json has no plugins array');
  process.exit(2);
}

const updates = new Map(); // pluginName -> newVersion
const errors = [];

for (const plugin of data.plugins) {
  const label = plugin.name ?? '<unnamed>';
  try {
    const upstream = await resolveUpstreamVersion(plugin);
    if (!upstream) {
      console.log(`[skip]    ${label}: upstream version not available`);
      continue;
    }
    if (upstream === plugin.version) {
      console.log(`[ok]      ${label}: ${plugin.version}`);
    } else {
      console.log(`[update]  ${label}: ${plugin.version} -> ${upstream}`);
      updates.set(plugin.name, upstream);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.log(`[error]   ${label}: ${msg}`);
    errors.push(`${label}: ${msg}`);
  }
}

if (updates.size === 0) {
  console.log('');
  console.log(errors.length > 0 ? 'No version changes (with errors above).' : 'No version changes.');
  process.exit(errors.length > 0 ? 1 : 0);
}

const updatedText = applyVersionUpdates(raw, updates);
if (updatedText === raw) {
  console.error('FATAL: computed updates but produced no text change. Refusing to write.');
  process.exit(3);
}

// Sanity: the result must still parse and the in-memory versions must match.
const reparsed = JSON.parse(updatedText);
for (const [name, want] of updates.entries()) {
  const entry = reparsed.plugins.find((p) => p.name === name);
  if (!entry || entry.version !== want) {
    console.error(`FATAL: post-edit verification failed for ${name} (expected ${want}, got ${entry?.version}).`);
    process.exit(4);
  }
}

fs.writeFileSync(MARKETPLACE_PATH, updatedText);
console.log('');
console.log(`Wrote ${updates.size} version update(s) to ${path.relative(REPO_ROOT, MARKETPLACE_PATH)}.`);
process.exit(errors.length > 0 ? 1 : 0);

// ---------------------------------------------------------------------------

async function resolveUpstreamVersion(plugin) {
  const src = plugin.source;

  if (typeof src === 'string') {
    // Relative-path (vendored) source. Resolve against the repo root.
    if (!src.startsWith('./') && !src.startsWith('../')) {
      throw new Error(`unsupported string source: ${src}`);
    }
    const local = path.join(REPO_ROOT, src, '.claude-plugin', 'plugin.json');
    if (!fs.existsSync(local)) {
      throw new Error(`vendored plugin.json missing at ${path.relative(REPO_ROOT, local)}`);
    }
    const pj = JSON.parse(fs.readFileSync(local, 'utf8'));
    return typeof pj.version === 'string' ? pj.version : null;
  }

  if (!src || typeof src !== 'object') {
    throw new Error(`source missing or unsupported: ${JSON.stringify(src)}`);
  }

  if (src.sha) {
    throw new Error(`source is SHA-pinned (${src.sha.slice(0, 7)}); not auto-syncing`);
  }

  let owner;
  let repo;
  if (src.source === 'url' && typeof src.url === 'string') {
    const parsed = parseGithubUrl(src.url);
    if (!parsed) throw new Error(`cannot parse github url: ${src.url}`);
    ({ owner, repo } = parsed);
  } else if (src.source === 'github' && typeof src.repo === 'string') {
    const parts = src.repo.split('/');
    if (parts.length !== 2) throw new Error(`invalid github repo: ${src.repo}`);
    [owner, repo] = parts;
  } else {
    throw new Error(`unsupported source type: ${JSON.stringify(src)}`);
  }

  const branches = src.ref ? [src.ref] : ['main', 'master'];
  let lastErr;
  for (const branch of branches) {
    const url = `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/.claude-plugin/plugin.json`;
    try {
      const resp = await fetch(url, { headers: { 'cache-control': 'no-cache' } });
      if (resp.status === 404) {
        lastErr = new Error(`404 on ${branch}`);
        continue;
      }
      if (!resp.ok) throw new Error(`HTTP ${resp.status} on ${branch}`);
      const pj = JSON.parse(await resp.text());
      if (typeof pj.version !== 'string') return null;
      return pj.version;
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr ?? new Error('upstream fetch failed');
}

function parseGithubUrl(url) {
  // matches https://github.com/owner/repo(.git)? or git@github.com:owner/repo(.git)?
  const m = /github\.com[:/]([^/]+)\/([^/.\s]+)(?:\.git)?\/?$/.exec(url);
  if (!m) return null;
  return { owner: m[1], repo: m[2] };
}

// Replace the `version` field for the named plugins using a line-based scan.
// Preserves all surrounding whitespace and formatting.
function applyVersionUpdates(text, updates) {
  const lines = text.split('\n');
  const remaining = new Map(updates); // plugins still awaiting their version line
  const nameRe = /^(\s+)"name":\s*"([^"]+)"\s*,?\s*$/;
  const versionRe = /^(\s+)"version":\s*"([^"]+)"(\s*,?\s*)$/;

  // After a `"name": "X"` line, the very next `"version": "..."` line
  // (within a small window) belongs to that plugin entry.
  const LOOKAHEAD = 8;
  let currentName = null;
  let nameLine = -Infinity;

  for (let i = 0; i < lines.length; i++) {
    const nameMatch = nameRe.exec(lines[i]);
    if (nameMatch) {
      currentName = nameMatch[2];
      nameLine = i;
      continue;
    }
    const verMatch = versionRe.exec(lines[i]);
    if (verMatch && currentName && i - nameLine <= LOOKAHEAD) {
      const want = remaining.get(currentName);
      if (want !== undefined && verMatch[2] !== want) {
        lines[i] = `${verMatch[1]}"version": "${want}"${verMatch[3]}`;
        remaining.delete(currentName);
      }
      // Clear so we don't accidentally edit a later "version" field in the same entry.
      currentName = null;
    }
  }

  if (remaining.size > 0) {
    throw new Error(`Could not locate version line(s) for: ${[...remaining.keys()].join(', ')}`);
  }
  return lines.join('\n');
}
