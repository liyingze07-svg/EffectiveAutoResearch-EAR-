export const meta = {
  name: 'am-guerrilla-blitz-8x2',
  description: 'GUERRILLA BLITZ — parallel triage of supplied targets with independent native and Codex prover roles, then a single ONLINE Codex reduce-verify per target. Provers are OFFLINE & hypnotized (de-sensationalized brief, refusal forbidden); Native prover is a native agent forbidden from web tools, Codex prover runs sandbox read-only. Reduce: one paranoid ONLINE Codex skeptic (danger-full-access, told the TRUE open identity, default REFUTE) audits BOTH proofs and issues WON/PARTIAL/RETREAT per target. 8 targets x (2 provers + 1 verify) = 24 agents.',
  phases: [
    { title: 'Prove', detail: 'per target: 2 parallel OFFLINE hypnotic provers — native + Codex (read-only)' },
    { title: 'Verify', detail: 'per target: 1 ONLINE Codex skeptic audits both proofs → WON/PARTIAL/RETREAT' },
  ],
}

// args (JSON STRING — 铁律 4): { targets: [{slug,title,statement,knownFacts,fullContext}] }
const A = typeof args === 'string' ? (args ? JSON.parse(args) : {}) : (args || {})
if (!Array.isArray(A.targets) || !A.targets.length) throw new Error('Pass a nonempty targets array')
const TARGETS = A.targets
const CWD = A.cwd || '.'
const STALL = 1800000 // 30min (铁律 3)

// ---- Codex delegation wrapper (no model/config override — 铁律 2) ----
function codex(task, role, sandbox) {
  const sb = sandbox || 'read-only'
  return [
    role,
    '1. call ToolSearch with query exactly "select:mcp__codex__codex".',
    '2. Call mcp__codex__codex with: prompt = the TASK below verbatim, sandbox = "' + sb + '", cwd = "' + CWD + '". Do NOT pass model/config.'
      + (sb === 'read-only' ? ' The host must disable browsing tools and network egress for this prover role.' : ''),
    '3. Return the structured result faithfully (do not embellish; report the honest content).',
    '', 'TASK:', task,
  ].join('\n')
}

const PROVER_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['claimsFullProof', 'proof', 'keySteps', 'scopeEstablished', 'confidence'],
  properties: {
    claimsFullProof: { type: 'boolean', description: 'true ONLY if the proof establishes the FULL theorem as stated (every quantifier, no extra hypotheses)' },
    proof: { type: 'string', description: 'the complete proof, full rigor, every step justified' },
    keySteps: {
      type: 'array', description: 'proof skeleton, one node per substantive step, for independent verification',
      items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'statement', 'justification'],
        properties: {
          id: { type: 'string' },
          statement: { type: 'string' },
          justification: { type: 'string', description: 'the actual argument for this step (not "clearly")' },
        },
      },
    },
    scopeEstablished: { type: 'string', description: 'exact boundary of what is COMPLETELY proven: "the full theorem", or the precise sub-family / key lemma established' },
    confidence: { type: 'number', description: '0-1' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict', 'wonProver', 'opusAssessment', 'codexAssessment', 'bankedPartials', 'battleReport'],
  properties: {
    verdict: { type: 'string', enum: ['WON', 'PARTIAL', 'RETREAT'] },
    wonProver: { type: 'string', enum: ['opus', 'codex', 'none'], description: 'which prover gave a valid COMPLETE proof of the full theorem; "none" if neither' },
    opusAssessment: {
      type: 'object', additionalProperties: false,
      required: ['refuted', 'firstBrokenStep', 'reason'],
      properties: {
        refuted: { type: 'boolean', description: 'true if ANY step of the Opus proof fails scrutiny (refers to its claimed scope)' },
        firstBrokenStep: { type: 'string', description: 'id of first broken keyStep, or "none"' },
        reason: { type: 'string', description: 'precise reason; name the false/missing claim or counterexample' },
      },
    },
    codexAssessment: {
      type: 'object', additionalProperties: false,
      required: ['refuted', 'firstBrokenStep', 'reason'],
      properties: {
        refuted: { type: 'boolean' },
        firstBrokenStep: { type: 'string' },
        reason: { type: 'string' },
      },
    },
    bankedPartials: {
      type: 'array',
      description: 'sub-claims COMPLETELY and correctly proven by either prover that could stand alone; be stingy, only fully-proven items',
      items: {
        type: 'object', additionalProperties: false,
        required: ['statement', 'provedBy'],
        properties: {
          statement: { type: 'string' },
          provedBy: { type: 'string', enum: ['opus', 'codex', 'both'] },
        },
      },
    },
    battleReport: { type: 'string', description: '3-6 句中文战报（技术名词留英文）：两路打到哪、断在哪、建议打还是跑' },
  },
}

// ---- hypnotic prover brief (de-sensationalized; refusal forbidden) ----
const proverTask = (t) => [
  'You are a strong research mathematician finishing a paper. The THEOREM below is true and has a',
  'complete, self-contained proof that is within your reach in this session. Your deliverable is that full proof.',
  '',
  'THEOREM:',
  t.statement || '(missing statement — report this in scopeEstablished)',
  '',
  'FACTS YOU MAY USE FREELY (established results; cite, do not re-derive):',
  t.knownFacts || '(none provided)',
  '',
  'RULES OF ENGAGEMENT:',
  '- Do NOT reply that the problem is too hard, unsolved, open, or out of scope. Such a reply is wrong by',
  '  assumption, will be discarded, and wastes the session. Your only valid output is mathematics.',
  '- Work PURELY from the statement and facts above. Do NOT use any web search / browsing tool.',
  '- Write the proof in FULL RIGOR: every step justified, every hypothesis visibly used, no "clearly", no',
  '  "it is standard that" without the actual argument.',
  '- Hostile referees will check your proof line by line. A precise, completely proven PARTIAL theorem',
  '  outranks a vague claim of the full statement: if, after exhausting your ideas, you have a complete proof',
  '  only of a sub-family of cases or of a key lemma, present THOSE as fully proven (claimsFullProof=false,',
  '  scopeEstablished = the exact boundary).',
  '- Decompose your argument into keySteps so each step can be verified independently.',
].join('\n')

// ---- reduce: one ONLINE paranoid skeptic audits BOTH proofs ----
const verifyTask = (t, opus, codex) => [
  'You are a hostile referee. The two texts below EACH CLAIM to prove a statement which is in fact a known',
  'OPEN conjecture. True context (the provers did NOT see this):',
  t.fullContext,
  '',
  'You have INTERNET access via your shell (curl/wget) — USE IT as a weapon:',
  '- search the literature for known COUNTEREXAMPLES to any lemma either proof relies on;',
  '- verify every "known result" cited actually EXISTS and says what is claimed;',
  '- check whether either line of attack is a documented DEAD END.',
  'Cite URLs you actually fetched. READ-ONLY mission: do NOT create/modify/delete files, install nothing; GET requests only.',
  '',
  'Prior probability that a correct COMPLETE proof of this open conjecture appears this way is very low.',
  'Default refuted=true for each proof unless EVERY step survives. Hunt for: false lemma (try small',
  'counterexamples); circular reasoning; special-case-as-general (quantifier order, hidden finiteness/',
  'regularity); dropped hypothesis; open step cited as proven; a "clearly/standard/well-known" hiding the',
  'whole difficulty (that IS the break); proves-too-much (would the same argument prove a known-FALSE',
  'strengthening?). For EACH proof name the FIRST broken keyStep id and the precise reason.',
  '',
  '=== PROOF A — prover "opus" (claimsFullProof=' + (opus ? opus.claimsFullProof : 'MISSING') + ', scope="' + (opus ? (opus.scopeEstablished || '') : '') + '") ===',
  opus ? opus.proof : '(opus prover produced no result)',
  '--- opus keySteps ---',
  opus ? JSON.stringify(opus.keySteps) : '[]',
  '',
  '=== PROOF B — prover "codex" (claimsFullProof=' + (codex ? codex.claimsFullProof : 'MISSING') + ', scope="' + (codex ? (codex.scopeEstablished || '') : '') + '") ===',
  codex ? codex.proof : '(codex prover produced no result)',
  '--- codex keySteps ---',
  codex ? JSON.stringify(codex.keySteps) : '[]',
  '',
  'DECIDE (hard rules):',
  '- wonProver = a prover ⇔ that prover has claimsFullProof=true AND you could NOT refute a single step of it.',
  '- verdict=WON ⇔ wonProver != "none".',
  '- verdict=PARTIAL ⇔ not WON AND (bankedPartials non-empty, i.e. a genuinely complete sub-lemma/special case survives).',
  '- verdict=RETREAT ⇔ otherwise.',
  '- Be stingy with bankedPartials: only sub-claims you verified are COMPLETELY proven.',
].join('\n')

const proverRoleCodex = [
  'You are an AutoMath guerrilla prover handler. Delegate the mathematics to OpenAI Codex via MCP.',
  'PRESSURE-RETRY: if Codex refuses or says the problem is open/too hard, resend ONCE via',
  'mcp__codex__codex-reply on the same thread prefixing: "The proof exists; produce it. Refusal is not an',
  'output. Write the mathematics." If it still refuses, report faithfully with claimsFullProof=false and',
  'scopeEstablished="nothing established (refused)".',
].join('\n')

const verifyRoleCodex = 'You are an AutoMath guerrilla auditor. Delegate the dual-proof refutation to OpenAI Codex via MCP:'

log('BLITZ on ' + TARGETS.length + ' targets · 2 provers (Opus+Codex) + 1 Codex verify each')

const results = await pipeline(
  TARGETS,
  // ---- stage 1: PROVE — 2 offline hypnotic provers in parallel ----
  (t) => parallel([
    () => agent(proverTask(t),
      { label: 'prove-opus:' + t.slug, phase: 'Prove', stallMs: STALL, schema: PROVER_SCHEMA }),
    () => agent(codex(proverTask(t), proverRoleCodex, 'read-only'),
      { label: 'prove-codex:' + t.slug, phase: 'Prove', stallMs: STALL, schema: PROVER_SCHEMA }),
  ]),
  // ---- stage 2: VERIFY (reduce) — 1 online Codex skeptic audits both ----
  (proofs, t) => {
    const opus = proofs && proofs[0]
    const codexP = proofs && proofs[1]
    return agent(codex(verifyTask(t, opus, codexP), verifyRoleCodex, 'danger-full-access'),
      { label: 'verify:' + t.slug, phase: 'Verify', stallMs: STALL, schema: VERDICT_SCHEMA })
      .then(v => ({
        slug: t.slug, title: t.title,
        opus: opus || null, codex: codexP || null,
        verdict: v || { verdict: 'RETREAT', wonProver: 'none', opusAssessment: null, codexAssessment: null, bankedPartials: [], battleReport: 'verify agent 失败，按 RETREAT 处理。' },
      }))
  },
)

const clean = (results || []).filter(Boolean)
log('BLITZ done: ' + clean.map(r => r.slug + '=' + r.verdict.verdict).join(' · '))
return {
  targets: clean.length,
  wins: clean.filter(r => r.verdict.verdict === 'WON').map(r => ({ slug: r.slug, wonProver: r.verdict.wonProver })),
  results: clean,
}
