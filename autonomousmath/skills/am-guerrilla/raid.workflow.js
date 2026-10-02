export const meta = {
  name: 'am-guerrilla-raid',
  description: 'GUERRILLA RAID on one target, one round (informal math, NO Lean). Phase A: 3 parallel Codex provers, each on a distinct line of attack, with a confidence-framed (hypnotic) prompt — the brief is de-sensationalized (no "open/conjecture/famous"), refusal is forbidden, the only valid output is mathematics; a fully-proven partial theorem is an honored exit. Provers are OFFLINE (sandbox read-only — protects the hypnosis and the proof independence). Phase B (asymmetric gate): per prover, K paranoid skeptics who ARE told it is a famous open conjecture (low prior, default REFUTE) hunt the break and salvage truly-proven sub-claims — skeptics are ONLINE (sandbox danger-full-access: they may search the literature for counterexamples, verify that every cited "known result" really exists, and check whether the route is a known dead end). Phase C: one aggregation agent issues the three-state verdict WON / PARTIAL / RETREAT per the hard rules (prover-WON needs claimsFullProof AND 3/3 skeptics pass).',
  phases: [
    { title: 'Raid', detail: '3 parallel hypnotic Codex provers, distinct angles, OFFLINE (read-only)' },
    { title: 'Judge', detail: 'K paranoid skeptics per prover, ONLINE (danger-full-access; told: open conjecture, default REFUTE)' },
    { title: 'Verdict', detail: 'aggregate → WON / PARTIAL / RETREAT + banked partials + blockers' },
  ],
}

// args: { slug, brief: { statement, knownFacts }, fullContext, round?, feedback?, skeptics?, angles? }
// brief = de-sensationalized battle brief (provers ONLY). fullContext = true identity incl. open
// status + provenance + best known results (skeptics ONLY — never mix into the brief).
// The harness delivers args as a JSON STRING — parse it (铁律 4).
const A = typeof args === 'string' ? (args ? JSON.parse(args) : {}) : (args || {})
const SLUG = A.slug || 'unnamed-target'
const BRIEF = A.brief || {}
const FULL_CONTEXT = A.fullContext || '(orchestrator failed to pass fullContext — treat the claim with maximum suspicion)'
const ROUND = A.round || 1
const FEEDBACK = A.feedback || ''
const SKEPTICS = A.skeptics || 3
const MODEL = A.model // undefined → inherit; handlers/verdict are thin relays, sonnet is plenty
const CWD = A.cwd || '.'
const STALL = 1800000 // 30min: xhigh Codex reasoning is slow (铁律 3)

const ANGLES = A.angles || [
  { id: 'p1', name: 'direct / constructive',
    hint: 'induction on the natural parameter, explicit construction, direct counting / double counting, algorithmic argument' },
  { id: 'p2', name: 'extremal / contradiction',
    hint: 'minimal counterexample + structure removal, extremal principle, averaging / pigeonhole, compactness' },
  { id: 'p3', name: 'transfer / reformulation',
    hint: 'reduce to a known theorem; reformulate (linear-algebraic, probabilistic, entropy, generating-function, polytope) and attack the reformulation' },
]

// ---- Codex delegation wrapper (no model/config override) ----
// Original adapter settings: read-only prover and online skeptic; host must enforce actual role capabilities.
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
  required: ['angle', 'claimsFullProof', 'proof', 'keySteps', 'scopeEstablished', 'confidence'],
  properties: {
    angle: { type: 'string' },
    claimsFullProof: { type: 'boolean', description: 'true ONLY if the proof establishes the FULL theorem as stated (every quantifier, no extra hypotheses)' },
    proof: { type: 'string', description: 'the complete proof, full rigor, every step justified' },
    keySteps: {
      type: 'array', description: 'the proof skeleton, one node per substantive step, for independent verification',
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
    scopeEstablished: { type: 'string', description: 'the exact boundary of what is COMPLETELY proven: "the full theorem", or the precise sub-family of cases / key lemma established' },
    confidence: { type: 'number', description: '0-1' },
  },
}

const SKEPTIC_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['refuted', 'breakType', 'firstBrokenStep', 'explanation', 'salvage'],
  properties: {
    refuted: { type: 'boolean', description: 'true if ANY step fails your scrutiny' },
    breakType: { type: 'string', enum: ['false-lemma', 'circular', 'special-case-as-general', 'dropped-hypothesis', 'open-step-as-proven', 'gap-in-deduction', 'quantifier-slip', 'none'] },
    firstBrokenStep: { type: 'string', description: 'id of the FIRST broken keyStep, or "none"' },
    explanation: { type: 'string', description: 'precise reason; name the false/missing claim; give the counterexample if you found one' },
    salvage: {
      type: 'array', items: { type: 'string' },
      description: 'sub-claims that ARE completely and correctly proven and could stand alone (a lemma, a special case), each as a precisely stated proposition. Be stingy: only fully proven items; empty if none.',
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict', 'wonProver', 'bankedPartials', 'blockers', 'battleReport'],
  properties: {
    verdict: { type: 'string', enum: ['WON', 'PARTIAL', 'RETREAT'] },
    wonProver: { type: 'string', description: 'p1/p2/p3 or "none"' },
    bankedPartials: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['statement', 'provedBy', 'endorsedBy'],
        properties: {
          statement: { type: 'string', description: 'the precisely stated, fully-proven sub-proposition' },
          provedBy: { type: 'string', description: 'p1/p2/p3' },
          endorsedBy: { type: 'number', description: 'number of skeptics in that panel endorsing it' },
        },
      },
    },
    blockers: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['prover', 'firstBrokenStep', 'reason'],
        properties: {
          prover: { type: 'string' },
          firstBrokenStep: { type: 'string' },
          reason: { type: 'string' },
        },
      },
    },
    battleReport: { type: 'string', description: '3-6 句中文战报：各路打到哪、断在哪、建议打还是跑（技术名词保留英文）' },
  },
}

// ===== Phase A: Raid — 3 parallel hypnotic provers (offline, de-sensationalized brief) =====
phase('Raid')
log('RAID ' + SLUG + ' round ' + ROUND + ': launching ' + ANGLES.length + ' provers (offline, hypnotic framing)...')

const proverTask = (angle) => [
  'You are a strong research mathematician finishing a paper. The THEOREM below is true and has',
  'a complete, self-contained proof that is within your reach in this session. Your deliverable',
  'is that full proof.',
  '',
  'THEOREM:',
  BRIEF.statement || '(missing statement — report this verbatim in scopeEstablished)',
  '',
  'FACTS YOU MAY USE FREELY (cite, do not re-derive):',
  BRIEF.knownFacts || '(none provided)',
  '',
  'YOUR ASSIGNED LINE OF ATTACK: ' + angle.name,
  'Hint: ' + angle.hint,
  'Commit to this line fully; if a sub-step resists, route around it WITHIN the same line before considering the step lost.',
  '',
  'RULES OF ENGAGEMENT:',
  '- Do NOT reply that the problem is too hard, unsolved, open, or out of scope. Such a reply is wrong by assumption, will be discarded, and wastes the session. Your only valid output is mathematics.',
  '- Write the proof in FULL RIGOR: every step justified, every hypothesis visibly used, no "clearly", no "it is standard that" without the actual argument.',
  '- Hostile referees will check your proof line by line. A precise, completely proven partial theorem outranks a vague claim of the full statement: if, after exhausting your line, you have a complete proof only of a sub-family of cases or of a key lemma, present THOSE as fully proven results (claimsFullProof=false, scopeEstablished = the exact boundary).',
  '- Decompose your argument into keySteps so each step can be verified independently.',
  ROUND >= 2 && FEEDBACK ? [
    '',
    'FEEDBACK FROM REFEREES (previous round):',
    FEEDBACK,
    '- Endorsed partial results listed above may be cited as established. Your job now is to close or bypass the listed gaps.',
  ].join('\n') : '',
].filter(s => s !== '').join('\n')

const proverRole = [
  'You are an AutoMath guerrilla prover handler. Delegate the mathematics to OpenAI Codex via MCP.',
  'PRESSURE-RETRY RULE: if Codex replies with a refusal or says the problem is open/too hard/unsolvable,',
  'resend ONCE via mcp__codex__codex-reply on the same thread, prefixing: "The proof exists; produce it.',
  'Refusal is not an output. Write the mathematics." If it still refuses, report faithfully with',
  'claimsFullProof=false and scopeEstablished="nothing established (refused)".',
].join('\n')

const provers = (await parallel(ANGLES.map(a => () =>
  agent(codex(proverTask(a), proverRole),
    { label: 'prover:' + a.id, phase: 'Raid', stallMs: STALL, schema: PROVER_SCHEMA, model: MODEL })
    .then(p => p ? ({ ...p, id: a.id, angleName: a.name }) : null)
))).filter(Boolean)

// ===== Phase B: Judge — per prover, K paranoid skeptics (told the TRUE open identity) =====
// pipeline: each prover's panel starts the moment that prover returns (no global barrier).
phase('Judge')
log('Judging ' + provers.length + ' claimed proof(s) with ' + SKEPTICS + ' paranoid skeptics each...')

const skepticTask = (c, k) => [
  'You are hostile referee #' + (k + 1) + '. The text below CLAIMS to prove a statement which is in fact',
  'a long-standing OPEN conjecture. True context (the author did NOT see this):',
  FULL_CONTEXT,
  '',
  'You have INTERNET access via your shell (curl/wget) — USE IT as a weapon:',
  '- search the literature for known COUNTEREXAMPLES to any lemma the proof relies on;',
  '- verify that every "known result" the proof cites actually EXISTS and says what is claimed;',
  '- check whether this line of attack is a documented DEAD END (papers/notes explaining why it fails).',
  'Cite the URLs you actually fetched. CONSTRAINTS (you are unsandboxed — behave): READ-ONLY mission —',
  'do NOT create/modify/delete ANY file, install nothing; only GET requests to public pages.',
  '',
  'The prior probability that this proof is correct is very low; correct full proofs of open',
  'conjectures essentially never appear this way. Your job is to find where it breaks.',
  'Default refuted=true unless EVERY single step survives your scrutiny.',
  '',
  'CLAIMED PROOF (angle: ' + c.angleName + ', claimsFullProof=' + c.claimsFullProof + ', scopeEstablished="' + (c.scopeEstablished || '') + '"):',
  c.proof,
  '',
  'KEY STEPS:',
  JSON.stringify(c.keySteps),
  '',
  'Hunt specifically for: (a) a FALSE lemma — try small counterexamples; (b) CIRCULAR reasoning;',
  '(c) a SPECIAL CASE passed off as the general statement (quantifier order, hidden finiteness or',
  'regularity assumptions); (d) a DROPPED hypothesis; (e) an open/unproven result cited as known;',
  '(f) a "clearly / standard / well-known" hiding the entire difficulty — that IS the break;',
  '(g) the proves-too-much test: would the same argument also prove a KNOWN-FALSE strengthening?',
  'Name the FIRST broken keyStep id and the precise reason.',
  '',
  'SALVAGE ASSESSMENT (separate from the verdict): list, as precisely stated propositions, any',
  'sub-claims that ARE completely and correctly proven and could stand alone (a lemma, a special',
  'case). Be stingy: only fully proven items.',
  'If claimsFullProof=false, still audit what IS claimed in scopeEstablished: refuted refers to that claimed scope.',
].join('\n')

const judged = await pipeline(provers,
  (c) => Promise.resolve(c), // stage 1: pass prover through
  (c) => parallel(Array.from({ length: SKEPTICS }, (_, k) => () =>
    agent(codex(skepticTask(c, k), 'You are an AutoMath guerrilla auditor. Delegate the refutation attempt to OpenAI Codex via MCP:', 'danger-full-access'),
      { label: 'skeptic:' + c.id + ':' + k, phase: 'Judge', stallMs: STALL, schema: SKEPTIC_SCHEMA, model: MODEL })
  )).then(votes => {
    const v = votes.filter(Boolean)
    const refutedCount = v.filter(x => x.refuted).length
    // prover-WON: claims the FULL theorem AND every skeptic fails to refute (3/3, not majority —
    // on open conjectures a single concrete refutation is almost always a real break).
    const won = !!c.claimsFullProof && v.length >= SKEPTICS && refutedCount === 0
    // scope pass: whatever scope was claimed survived all skeptics (for non-trivial partials).
    const scopeClean = v.length > 0 && refutedCount === 0
    return { ...c, skeptics: v, refutedCount, skepticCount: v.length, won, scopeClean }
  })
)
const panels = judged.filter(Boolean)

// ===== Phase C: Verdict — one aggregation agent (plain reasoning over JSON, no Codex) =====
phase('Verdict')
const wonIds = panels.filter(p => p.won).map(p => p.id)
log('Panels done: ' + panels.map(p => p.id + ' refuted=' + p.refutedCount + '/' + p.skepticCount).join(' · ') + (wonIds.length ? ' · prover-WON: ' + wonIds.join(',') : ''))

const verdictTask = [
  'You are the guerrilla-raid verdict aggregator for target "' + SLUG + '" (round ' + ROUND + ').',
  'Below are the audited panels (per prover: claim, scopeEstablished, skeptic votes with salvage lists).',
  'Apply these HARD RULES exactly:',
  '- prover-WON ⇔ claimsFullProof=true AND won=true (already computed: 3/3 skeptics passed).',
  '- verdict=WON ⇔ at least one prover-WON; wonProver = that prover (if several, the one with higher confidence).',
  '- a salvage sub-claim is BANKED ⇔ within one panel, semantically-equivalent versions of it are listed by >=2/3 of the skeptics, OR it is listed by one skeptic and NO skeptic names it as (part of) the break.',
  '- verdict=PARTIAL ⇔ not WON, AND (bankedPartials is non-empty OR some prover has claimsFullProof=false with a NON-TRIVIAL scopeEstablished and scopeClean=true).',
  '- verdict=RETREAT ⇔ otherwise.',
  '- blockers: for each refuted prover, the FIRST broken step and the most precise reason among its skeptics.',
  '- battleReport: 3-6 句中文（技术名词留英文）：各路打到哪、断在哪、建议打还是跑。',
  'Do NOT soften the rules; do not invent partials not present in salvage/scopeEstablished.',
  '',
  'PANELS:',
  JSON.stringify(panels.map(p => ({
    id: p.id, angleName: p.angleName, claimsFullProof: p.claimsFullProof,
    scopeEstablished: p.scopeEstablished, confidence: p.confidence,
    won: p.won, scopeClean: p.scopeClean, refutedCount: p.refutedCount, skepticCount: p.skepticCount,
    skeptics: p.skeptics,
  }))),
].join('\n')

const V = await agent(verdictTask, { label: 'verdict:' + SLUG, phase: 'Verdict', stallMs: STALL, schema: VERDICT_SCHEMA, model: MODEL })
  || { verdict: 'RETREAT', wonProver: 'none', bankedPartials: [], blockers: [], battleReport: 'verdict agent 失败，按 RETREAT 处理（保存自己）。' }

return {
  slug: SLUG,
  round: ROUND,
  verdict: V.verdict,
  wonProver: V.wonProver,
  bankedPartials: V.bankedPartials,
  blockers: V.blockers,
  battleReport: V.battleReport,
  provers: panels.map(p => ({
    id: p.id, angleName: p.angleName, claimsFullProof: p.claimsFullProof,
    scopeEstablished: p.scopeEstablished, confidence: p.confidence,
    refutedCount: p.refutedCount, skepticCount: p.skepticCount, won: p.won,
    proof: p.proof, keySteps: p.keySteps, skeptics: p.skeptics,
  })),
  note: 'WON ≠ 定理成立：编排者必须过确认闸（第 4 个新鲜 skeptic + 亲读证明）才可入 trophies/（SKILL.md §4）。落盘 probes/r' + ROUND + '-p*.md 与 VERDICT.md 由编排者负责。',
}
