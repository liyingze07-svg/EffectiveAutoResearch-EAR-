export const meta = {
  name: 'harden',
  description: 'CLAIM-STRENGTH HARDENING (generalized from harden-eq-paper). Before a result is written up — and again whenever a reviewer panel flags an overclaim — stress-test every strong-form claim ("iff / tight / characterization / optimal / necessary and sufficient") by adversarially settling its CONVERSE: one offline Codex prover tries to PROVE the converse, another tries to REFUTE it with a counterexample, an online Codex skeptic adjudicates. Folds in reviewer blocker-findings as extra claims to settle. Emits corrected claims + the exact downgraded wording so the paper never ships an unproved iff. Bounded for a 2-core box + thin shared Codex quota: caps the number of claims settled, low concurrency, one focused pass per agent.',
  phases: [
    { title: 'Diagnose', detail: 'extract every strong-form claim from proofs/paper (+ reviewer blockers)' },
    { title: 'Settle', detail: 'per claim: prove-vs-refute the converse (offline Codex) → online skeptic adjudicates' },
    { title: 'Synthesize', detail: 'corrected claims + downgraded wording + HARDENING update' },
  ],
}

// args (JSON STRING) → parse. { dir, contextHint?, reviewerFindings?: [{point,fix}], maxClaims?: 3 }
const A = typeof args === 'string' ? (args ? JSON.parse(args) : {}) : (args || {})
const DIR = A.dir || '.'
const CONTEXT = A.contextHint || ''
const REVIEWER_FINDINGS = Array.isArray(A.reviewerFindings) ? A.reviewerFindings : []
const MAX_CLAIMS = A.maxClaims || 3
const STALL = 1800000

function codex(task, role, sandbox) {
  const sb = sandbox || 'read-only'
  return [
    role,
    '1. call ToolSearch with query exactly "select:mcp__codex__codex".',
    '2. Call mcp__codex__codex with: prompt = the TASK below verbatim, sandbox = "' + sb + '", cwd = "' + DIR + '". Do NOT pass model/config.'
      + (sb === 'read-only' ? ' The host must disable browsing tools and network egress for this prover role.' : ''),
    '3. If Codex returns a usage-limit / connection error, report exactly {"error":"codex-unavailable"}.',
    '4. Return the structured result faithfully.',
    '', 'TASK:', task,
  ].join('\n')
}

// ---------- Phase 1: Diagnose ----------
phase('Diagnose')
const DIAG_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['claims'],
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['claim', 'location', 'kind', 'currentEvidence', 'converseQuestion'],
        properties: {
          claim: { type: 'string', description: 'the strong-form claim as stated in the paper' },
          location: { type: 'string', description: 'file + quoted phrase' },
          kind: { type: 'string', enum: ['iff', 'tight', 'characterization', 'optimal', 'necessary', 'other'] },
          currentEvidence: { type: 'string', description: 'what the sources actually prove (e.g. "sufficiency + one witness")' },
          converseQuestion: { type: 'string', description: 'the precise converse/necessity statement that must be settled' },
        },
      },
    },
  },
}
const diag = await agent(
  `You are a theory-paper claim auditor (analysis only, no code). ${CONTEXT}
Read the campaign's source proofs in ${DIR}/proofs/ (all NN-*.md) and the paper main-text in ${DIR}/paper/sections/ (and ${DIR}/HARDENING.md, ${DIR}/STATUS.md if present).
Extract EVERY strong-form claim — any "iff / if and only if / exactly when / characterization / characterize(s) / dichotomy / tight / necessary and sufficient / optimal / matching / the exact dividing line". For each, quote it (location), classify (kind), say what the sources ACTUALLY prove (currentEvidence — e.g. only sufficiency + a single witness), and write the precise CONVERSE/necessity statement that would have to hold (converseQuestion).
${REVIEWER_FINDINGS.length ? 'ALSO add, as additional claims to settle, these reviewer blocker-findings:\n' + JSON.stringify(REVIEWER_FINDINGS) : ''}
Return the structured list, strongest/most load-bearing first.`,
  { label: 'diagnose', phase: 'Diagnose', stallMs: STALL, schema: DIAG_SCHEMA },
)
const claims = ((diag && diag.claims) || []).slice(0, MAX_CLAIMS)
log(`Diagnose: ${claims.length} strong claim(s) to settle (cap ${MAX_CLAIMS})`)

// ---------- Phase 2: Settle (per claim: prove vs refute converse, then adjudicate) ----------
phase('Settle')
const PROVE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['direction', 'argument', 'confidence'],
  properties: {
    direction: { type: 'string', enum: ['proves-converse', 'refutes-converse', 'partial', 'neither'] },
    argument: { type: 'string', description: 'the proof of the converse, OR the explicit counterexample (with the construction and why it kills the claim), OR the strongest partial' },
    confidence: { type: 'number' },
  },
}
const ADJ_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict', 'correctedClaim', 'downgradedWording'],
  properties: {
    verdict: { type: 'string', enum: ['converse-holds', 'converse-refuted', 'inconclusive'] },
    correctedClaim: { type: 'string', description: 'the claim the paper SHOULD make (a true iff if the converse holds, else the honest sufficiency/separation downgrade + the open dividing line)' },
    downgradedWording: { type: 'string', description: 'concrete replacement text for the paper (abstract/intro/results) — what to say instead of the overclaim' },
  },
}
const settled = await pipeline(
  claims,
  // stage 1: two offline provers, opposite directions
  (c) => parallel([
    () => agent(codex(`${CONTEXT}\nPROVE THE CONVERSE of this claim (rescue the strong form). CONVERSE TO PROVE: ${c.converseQuestion}\nThe claim: "${c.claim}". Currently established: ${c.currentEvidence}. BOUNDED: one focused pass, no grinding; if you cannot prove it, say so and pivot to refuting.`,
      'You are a guerrilla prover handler; delegate to Codex (offline).', 'read-only'),
      { label: `prove:${c.kind}`, phase: 'Settle', stallMs: STALL, schema: PROVE_SCHEMA }),
    () => agent(codex(`${CONTEXT}\nREFUTE THE CONVERSE of this claim (downgrade it). Find an explicit counterexample to: ${c.converseQuestion}\nThe claim: "${c.claim}". Currently established: ${c.currentEvidence}. A clean counterexample kills the strong form. BOUNDED: one focused pass, no grinding.`,
      'You are a guerrilla prover handler; delegate to Codex (offline).', 'read-only'),
      { label: `refute:${c.kind}`, phase: 'Settle', stallMs: STALL, schema: PROVE_SCHEMA }),
  ]).then(([pv, rf]) => ({ c, pv, rf })),
  // stage 2: online skeptic adjudicates
  ({ c, pv, rf }) => agent(codex(`${CONTEXT}\nAdjudicate (online; you may check the literature, READ-ONLY GET only) whether the CONVERSE of this claim holds.\nClaim: "${c.claim}"\nConverse to settle: ${c.converseQuestion}\nCurrently established: ${c.currentEvidence}\nPROVE-attempt: ${JSON.stringify(pv)}\nREFUTE-attempt: ${JSON.stringify(rf)}\nIf the refutation exhibits a genuine counterexample, the strong claim is FALSE and must be downgraded; verify it. If the converse proof is valid, the strong form stands. Output the corrected claim and the exact downgraded wording for the paper.`,
    'You are a guerrilla auditor; delegate the adjudication to Codex (online).', 'danger-full-access'),
    { label: `adjudicate:${c.kind}`, phase: 'Settle', stallMs: STALL, schema: ADJ_SCHEMA })
    .then(adj => ({ claim: c, prove: pv, refute: rf, adjudication: adj })),
)
const clean = (settled || []).filter(Boolean)
log('Settle: ' + clean.map(s => s.claim.kind + '=' + (s.adjudication ? s.adjudication.verdict : 'null')).join(' · '))

// ---------- Phase 3: Synthesize ----------
phase('Synthesize')
const REPORT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['anyDowngrade', 'correctedClaims', 'paperEdits', 'reportMarkdown'],
  properties: {
    anyDowngrade: { type: 'boolean', description: 'true if any strong claim had to be downgraded' },
    correctedClaims: { type: 'array', items: { type: 'string' } },
    paperEdits: {
      type: 'array', description: 'concrete edits the orchestrator should apply to the paper',
      items: {
        type: 'object', additionalProperties: false,
        required: ['file', 'find', 'replaceWith'],
        properties: { file: { type: 'string' }, find: { type: 'string' }, replaceWith: { type: 'string' } },
      },
    },
    reportMarkdown: { type: 'string', description: 'a complete HARDENING.md: claims tested, converse verdicts + proofs/counterexamples, corrected claims, remaining open questions' },
  },
}
const synth = await agent(
  `You are the lead author hardening the campaign. ${CONTEXT}
Settled claims (with prove/refute attempts and the online adjudication): ${JSON.stringify(clean.map(s => ({ claim: s.claim.claim, location: s.claim.location, verdict: s.adjudication && s.adjudication.verdict, correctedClaim: s.adjudication && s.adjudication.correctedClaim, downgradedWording: s.adjudication && s.adjudication.downgradedWording })))}
TASK (writeup only): for every claim whose converse was REFUTED or left inconclusive, the corrected claim MUST be the honest downgrade (sufficiency + separation + the open dividing line), NOT an iff. Produce concrete paperEdits (file + exact find-text + replaceWith) the orchestrator can apply, and a complete HARDENING.md reportMarkdown.`,
  { label: 'synthesize', phase: 'Synthesize', stallMs: STALL, schema: REPORT_SCHEMA },
)

return { claims, settled: clean, report: synth }
