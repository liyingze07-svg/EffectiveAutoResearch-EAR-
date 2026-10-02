export const meta = {
  name: 'reviewer-panel',
  description: 'TERMINAL GATE of the AutonomousMath pipeline. Runs the NIPS Senior Area Chair simulator (SAC_PROMPT.md: 3 reviewers — Applied / Empiricist / Theoretician — + a Meta Review with an Accept/Reject recommendation) over the assembled paper, as SEVERAL INDEPENDENT panel instances spread across Codex (online, may check novelty/literature) and Claude (native) subagents. Aggregates: ACCEPTED iff at least `acceptThreshold` independent instances return a Meta recommendation of Accept (Poster/Oral). Returns the accept boolean + merged reviewer findings so the orchestrator can loop (harden + rewrite) on a reject. Bounded for a 2-core box + thin shared Codex quota: low concurrency, one focused review per agent.',
  phases: [
    { title: 'Review', detail: 'N independent SAC panels across Codex(online)+Claude(native) subagents' },
    { title: 'Aggregate', detail: 'ACCEPT iff >= acceptThreshold instances recommend Accept; merge findings' },
  ],
}

// args (JSON STRING) → parse (iron rule 4).
// { dir: <campaign root>, paperDir?: <dir/paper>, round?: 1, instances?: 2, acceptThreshold?,
//   codex?: true, claude?: true, sacPrompt?: <path to SAC_PROMPT.md> }
const A = typeof args === 'string' ? (args ? JSON.parse(args) : {}) : (args || {})
const DIR = A.dir || '.'
const PAPER = A.paperDir || `${DIR}/paper`
const ROUND = A.round || 1
const INSTANCES = A.instances || 2
const USE_CODEX = A.codex !== false
const USE_CLAUDE = A.claude !== false
if (!A.sacPrompt) throw new Error('Pass the frozen referee SAC prompt path')
const SAC = A.sacPrompt
const ACCEPT_THRESHOLD = A.acceptThreshold || Math.max(2, Math.ceil(INSTANCES / 2))
const STALL = 1800000

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['litmus', 'reviewer1Verdict', 'reviewer2Verdict', 'reviewer3Verdict', 'metaRecommendation', 'coreConflict', 'topWeaknesses', 'roadmap', 'reportMarkdown'],
  properties: {
    litmus: { type: 'string', enum: ['Breakthrough', 'Solid', 'Incremental', 'Trivial'] },
    reviewer1Verdict: { type: 'string', enum: ['Strong Reject', 'Reject', 'Weak Reject', 'Weak Accept', 'Accept', 'Strong Accept'] },
    reviewer2Verdict: { type: 'string', enum: ['Strong Reject', 'Reject', 'Weak Reject', 'Weak Accept', 'Accept', 'Strong Accept'] },
    reviewer3Verdict: { type: 'string', enum: ['Strong Reject', 'Reject', 'Weak Reject', 'Weak Accept', 'Accept', 'Strong Accept'] },
    metaRecommendation: { type: 'string', enum: ['Reject', 'Accept (Poster)', 'Accept (Oral)'] },
    coreConflict: { type: 'string', description: 'the disagreement between reviewers, if any' },
    topWeaknesses: {
      type: 'array', description: 'the decisive weaknesses to fix (the Roadmap Top-3), each actionable',
      items: {
        type: 'object', additionalProperties: false,
        required: ['point', 'severity', 'fix'],
        properties: {
          point: { type: 'string' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          fix: { type: 'string', description: 'concrete change to the paper / proof that would address it' },
        },
      },
    },
    roadmap: { type: 'string', description: 'the SAC roadmap-to-acceptance (or best-paper advice if accepted)' },
    reportMarkdown: { type: 'string', description: 'the full Chinese SAC review report in the required 5-section format' },
  },
}

const readInstr = (online) => online
  ? 'Read the paper by running shell commands: `cat ' + PAPER + '/sections/*.tex ' + PAPER + '/appendix/*.tex ' + PAPER + '/main.tex`. You also have internet — you MAY check whether the central claim is novel / already resolved (READ-ONLY: GET requests only, no writes/installs).'
  : 'Read the paper with the Read tool: every file under ' + PAPER + '/sections/ plus ' + PAPER + '/main.tex and every appendix proof under ' + PAPER + '/appendix/.'

const reviewTask = (online) => [
  'You are simulating a full NIPS Senior Area Chair review panel. FIRST read the role/calibration/committee/output spec:',
  online ? ('run `cat ' + SAC + '`') : ('Read the file ' + SAC + ' in full'),
  'and follow it EXACTLY (3 reviewers with dynamically-calibrated attitude + a Meta Review with a final Accept/Reject recommendation, Chinese report).',
  '',
  'THE SUBMISSION:',
  readInstr(online),
  '',
  'This is a THEORY paper (it may have no experiments) — apply the theory-paper note at the bottom of the SAC spec: Theoretician is the primary lens; do NOT reject solely for absence of experiments; the Empiricist instead checks proof rigor, controlled definitions, and whether every "iff/tight/characterization" claim has its converse actually proved.',
  '',
  'Be a harsh, calibrated reviewer — do not rubber-stamp. Produce the full 5-section report in reportMarkdown, and ALSO fill the structured fields (litmus, the three reviewer verdicts, metaRecommendation, coreConflict, topWeaknesses = the roadmap Top-3 as actionable items, roadmap).',
].join('\n')

function codex(task) {
  return [
    'You are an AutoMath reviewer handler. Delegate the FULL review to OpenAI Codex via MCP:',
    '1. call ToolSearch with query exactly "select:mcp__codex__codex".',
    '2. Call mcp__codex__codex with: prompt = the TASK below verbatim, sandbox = "danger-full-access", cwd = "' + DIR + '". Do NOT pass model/config.',
    '3. Return Codex\'s review faithfully, formatted into the required schema.',
    '', 'TASK:', task,
  ].join('\n')
}

// Build the instance list, alternating Codex(online) / Claude(native) per availability.
const backends = []
for (let i = 0; i < INSTANCES; i++) {
  const online = USE_CODEX && (!USE_CLAUDE || i % 2 === 0)
  backends.push(online ? 'codex' : 'claude')
}

const verdicts = (await parallel(backends.map((b, i) => () => {
  const online = b === 'codex'
  const prompt = online ? codex(reviewTask(true)) : reviewTask(false)
  return agent(prompt, { label: `review:${ROUND}:${b}${i}`, phase: 'Review', stallMs: STALL, schema: VERDICT_SCHEMA })
    .then(v => v ? ({ ...v, backend: b, instance: i }) : null)
}))).filter(Boolean)

// Aggregate.
const isAccept = (v) => v.metaRecommendation === 'Accept (Poster)' || v.metaRecommendation === 'Accept (Oral)'
const accepts = verdicts.filter(isAccept).length
const accepted = verdicts.length > 0 && accepts >= ACCEPT_THRESHOLD
// Merge findings (dedupe-light by point text); blockers first.
const mergedFindings = []
const seen = new Set()
for (const v of verdicts) for (const w of (v.topWeaknesses || [])) {
  const k = (w.point || '').slice(0, 80).toLowerCase()
  if (seen.has(k)) continue
  seen.add(k); mergedFindings.push(w)
}
mergedFindings.sort((x, y) => ({ blocker: 0, major: 1, minor: 2 }[x.severity] - { blocker: 0, major: 1, minor: 2 }[y.severity]))

log(`Panel round ${ROUND}: ${accepts}/${verdicts.length} instances Accept (threshold ${ACCEPT_THRESHOLD}) → ${accepted ? 'ACCEPTED' : 'REJECT'}`)

return {
  round: ROUND,
  accepted,
  accepts,
  instances: verdicts.length,
  acceptThreshold: ACCEPT_THRESHOLD,
  verdicts: verdicts.map(v => ({ backend: v.backend, litmus: v.litmus, metaRecommendation: v.metaRecommendation, r1: v.reviewer1Verdict, r2: v.reviewer2Verdict, r3: v.reviewer3Verdict, coreConflict: v.coreConflict })),
  findings: mergedFindings,
  reports: verdicts.map(v => ({ backend: v.backend, reportMarkdown: v.reportMarkdown })),
}
