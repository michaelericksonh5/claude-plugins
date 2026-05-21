#!/usr/bin/env node
/**
 * API key setup for ai-video-generator (Claude Code plugin)
 *
 * Writes keys to ~/.claude/settings.json under the "env" key — the official
 * Claude Code mechanism. Any plugin or MCP server installed through the
 * michaelericksonh5-plugins marketplace reads keys from this single location,
 * so you only ever need to set them once.
 *
 * Keys configured here:
 *   FAL_KEY         — fal.ai. Powers Veo 3.1, Happy Horse, Seedance 2.0.
 *                     https://fal.ai/dashboard/keys
 *   GEMINI_API_KEY  — Google Gemini. Powers Veo 3.1 via the Gemini API.
 *                     https://aistudio.google.com/app/apikey
 *
 * Usage:
 *   node setup-keys.mjs              # interactive
 *   node setup-keys.mjs --fal        # set FAL_KEY only
 *   node setup-keys.mjs --gemini     # set GEMINI_API_KEY only
 *   node setup-keys.mjs --both       # set both
 *   node setup-keys.mjs --check      # verify saved keys
 */

import * as fs from 'fs'
import * as path from 'path'
import * as readline from 'readline'
import * as os from 'os'

// ---------------------------------------------------------------------------
// ~/.claude/settings.json merge — touches only the "env" key
// ---------------------------------------------------------------------------

function mergeIntoClaudeSettings(envVars) {
  const settingsDir = path.join(os.homedir(), '.claude')
  const settingsPath = path.join(settingsDir, 'settings.json')

  let settings = {}
  if (fs.existsSync(settingsPath)) {
    try {
      settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'))
    } catch {
      console.warn('Warning: Could not parse ~/.claude/settings.json — will preserve file and merge carefully.')
      // Don't blow away the file; re-throw so the caller can decide
      throw new Error('Malformed settings.json')
    }
  } else {
    fs.mkdirSync(settingsDir, { recursive: true })
  }

  settings.env = { ...(settings.env ?? {}), ...envVars }
  fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n', 'utf8')
  return settingsPath
}

function readFromClaudeSettings() {
  const settingsPath = path.join(os.homedir(), '.claude', 'settings.json')
  if (!fs.existsSync(settingsPath)) return {}
  try {
    const s = JSON.parse(fs.readFileSync(settingsPath, 'utf8'))
    return s.env ?? {}
  } catch {
    return {}
  }
}

// ---------------------------------------------------------------------------
// Input helpers
// ---------------------------------------------------------------------------

async function hiddenInput(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: true,
    })
    process.stdout.write(question)

    let input = ''
    process.stdin.setRawMode?.(true)
    process.stdin.resume()
    process.stdin.setEncoding('utf8')

    const onData = (char) => {
      if (char === '\n' || char === '\r' || char === '') {
        process.stdin.setRawMode?.(false)
        process.stdin.pause()
        process.stdin.removeListener('data', onData)
        process.stdout.write('\n')
        rl.close()
        if (char === '') { process.exit(1) }
        resolve(input)
      } else if (char === '' || char === '\b') {
        input = input.slice(0, -1)
      } else {
        input += char
      }
    }

    process.stdin.on('data', onData)
  })
}

async function prompt(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout })
    rl.question(question, (a) => { rl.close(); resolve(a.trim()) })
  })
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

async function validateGemini(key) {
  if (!key || key.length < 20) return { ok: false, msg: 'Key too short.' }
  try {
    const resp = await fetch(
      `https://generativelanguage.googleapis.com/v1/models?key=${encodeURIComponent(key)}&pageSize=1`,
      { signal: AbortSignal.timeout(10000) }
    )
    if (resp.status === 200) return { ok: true, msg: 'Validated against Gemini API.' }
    if (resp.status === 401 || resp.status === 403)
      return { ok: false, msg: 'Gemini rejected the key (401/403). Check https://aistudio.google.com/app/apikey' }
    return { ok: false, msg: `Unexpected ${resp.status} from Gemini API.` }
  } catch (err) {
    return { ok: true, msg: `Network check skipped (${err.message}). Re-run --check to verify later.` }
  }
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

async function cmdSetFal() {
  console.log('\nfal.ai API key setup')
  console.log('--------------------')
  console.log('Get a key at https://fal.ai/dashboard/keys')
  console.log('Input is hidden — paste and press Enter.\n')

  const key = await hiddenInput('FAL_KEY: ')
  if (!key) { console.log('No key entered. Nothing saved.'); return 1 }
  if (key.length < 10) { console.log('Key looks too short. Aborting.'); return 1 }

  const saved = mergeIntoClaudeSettings({ FAL_KEY: key })
  console.log(`\nSaved to: ${saved}`)
  console.log('FAL_KEY is now available to all plugins in the michaelericksonh5-plugins marketplace.')
  return 0
}

async function cmdSetGemini() {
  console.log('\nGoogle Gemini API key setup')
  console.log('---------------------------')
  console.log('Get a key at https://aistudio.google.com/app/apikey')
  console.log('Input is hidden — paste and press Enter.\n')

  const key = await hiddenInput('GEMINI_API_KEY: ')
  if (!key) { console.log('No key entered. Nothing saved.'); return 1 }

  const { ok, msg } = await validateGemini(key)
  console.log(`${ok ? 'OK' : 'FAIL'}: ${msg}`)
  if (!ok) return 1

  // Write GEMINI_API_KEY and GOOGLE_API_KEY (same key — some Google APIs use either name)
  const saved = mergeIntoClaudeSettings({ GEMINI_API_KEY: key, GOOGLE_API_KEY: key })
  console.log(`\nSaved GEMINI_API_KEY + GOOGLE_API_KEY to: ${saved}`)
  console.log('Both key names are written since different Google APIs use different variable names.')
  console.log('These are now available to all plugins in the michaelericksonh5-plugins marketplace.')
  return 0
}

async function cmdCheck() {
  const env = readFromClaudeSettings()

  const falKey = env.FAL_KEY ?? ''
  const geminiKey = env.GEMINI_API_KEY ?? ''

  console.log('\nKey status in ~/.claude/settings.json:')
  console.log('---------------------------------------')

  if (falKey) {
    console.log(`FAL_KEY         OK: present (length ${falKey.length})`)
  } else {
    console.log('FAL_KEY         MISSING — run: node setup-keys.mjs --fal')
  }

  if (geminiKey) {
    const { ok, msg } = await validateGemini(geminiKey)
    console.log(`GEMINI_API_KEY  ${ok ? 'OK' : 'FAIL'}: ${msg}`)
  } else {
    console.log('GEMINI_API_KEY  MISSING — run: node setup-keys.mjs --gemini')
  }

  console.log('')
  if (!falKey && !geminiKey) {
    console.log('No keys set. At least one of FAL_KEY or GEMINI_API_KEY is required.')
    return 1
  }
  console.log('Keys are read from ~/.claude/settings.json and shared across all')
  console.log('plugins in the michaelericksonh5-plugins marketplace.')
  return 0
}

async function cmdInteractive() {
  console.log('\nai-video-generator — API key setup')
  console.log('===================================')
  console.log('Keys are written to ~/.claude/settings.json and shared across all')
  console.log('plugins in the michaelericksonh5-plugins marketplace.')
  console.log('')

  const choice = await prompt('Which key(s)? [1] FAL_KEY  [2] GEMINI_API_KEY  [3] both  > ')

  if (choice === '3') {
    await cmdSetFal()
    await cmdSetGemini()
  } else if (choice === '2') {
    await cmdSetGemini()
  } else {
    await cmdSetFal()
  }
  return 0
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const args = process.argv.slice(2)
let rc = 0

if (args.includes('--check')) {
  rc = await cmdCheck()
} else if (args.includes('--fal')) {
  rc = await cmdSetFal()
} else if (args.includes('--gemini')) {
  rc = await cmdSetGemini()
} else if (args.includes('--both')) {
  await cmdSetFal()
  rc = await cmdSetGemini()
} else {
  rc = await cmdInteractive()
}

process.exit(rc)
