export const meta = {
  name: 'am-guerrilla-seek',
  description: 'GUERRILLA SEEK — ONLINE recon for winnable open conjectures. Phase Recon: 5 parallel scouts sweep distinct hunting grounds: TCS combinatorics, AI/ML theory (AAAI-publishable), Erdős problems, fresh arXiv leftover conjectures, micro-conjectures. Scout backend (args.scout): "codex" (default — ONLINE Codex via sandbox danger-full-access, browses with curl/wget) | "claude" (WebSearch/WebFetch subagents) | "both". Hard filters: no flagship problems (P vs NP class), every target needs dated still-open evidence URLs, statement precise enough to be a raid brief. Phase Merge: dedup, re-verify openness of top targets via WebFetch, score = winOdds × value, rank. Returns the ranked target list; the USER picks what to raid (interactive circle-selection happens in the skill, not here).',
  phases: [
    { title: 'Recon', detail: '5 parallel scouts, one hunting ground each (default: ONLINE Codex, danger-full-access)' },
    { title: 'Merge', detail: 'dedup + re-verify openness of top targets + score & rank' },
  ],
}

// args: { exclude?: string[] (slugs already raided/listed), perRoute?: 4, scout?: 'codex'|'claude'|'both', routes?: [...], model?: 'sonnet'|'haiku'|'opus' }
// The harness delivers args as a JSON STRING — parse it (铁律 4).
const A = typeof args === 'string' ? (args ? JSON.parse(args) : {}) : (args || {})
const EXCLUDE = Array.isArray(A.exclude) ? A.exclude : []
const PER_ROUTE = A.perRoute || 4
const BACKEND = A.scout || 'codex' // 'codex' = 联网 Codex 侦察(默认, codex-online 模式) | 'claude' = WebSearch/WebFetch 子 agent | 'both'
const MODEL = A.model // undefined → inherit main-loop model; recon is mechanical web-sweeping, sonnet is plenty
const GW = A.cwd || '.'
const STALL = 1800000 // 30min: multi-round web recon is slow (铁律 3)

const ROUTES = A.routes || [
  { id: 'M1', name: 'learning-theory', grounds: 'COLT/ALT open-problem papers and current arXiv cs.LG/stat.ML', prey: 'PAC, online learning, sample complexity and precise open rate questions' },
  { id: 'M2', name: 'optimization-for-ML', grounds: 'Original optimization-theory papers for ML', prey: 'Convergence, last-iterate, acceleration and lower-bound questions' },
  { id: 'M3', name: 'bandits-RL-theory', grounds: 'Original bandit/RL-theory and COLT papers', prey: 'Regret, minimax rates, exploration and sample complexity' },
  { id: 'M4', name: 'generalization-theory', grounds: 'Current ML-theory papers with dated open-problem sections', prey: 'Generalization, feature learning, representation and expression thresholds' },
  { id: 'M5', name: 'stat-info-theory', grounds: 'Original statistical/information-theory papers with genuine ML interfaces', prey: 'Estimation, testing, privacy and statistical-computational gaps' },
]

const TARGET_SCHEMA_ITEMS = {
  type: 'object', additionalProperties: false,
  required: ['slug', 'title', 'statement', 'plainStory', 'whyPublishable', 'stillOpenEvidence',
    'field', 'difficulty', 'winOdds', 'value', 'knownPartials', 'pitfalls', 'sourceUrls'],
  properties: {
    slug: { type: 'string', description: 'unique kebab-case id, e.g. "frankl-small-width"' },
    title: { type: 'string' },
    statement: { type: 'string', description: 'PRECISE mathematical statement — all quantifiers and definitions included, usable verbatim as a raid brief' },
    plainStory: { type: 'string', description: '通俗中文讲明白：这题问什么、背景是什么、卡在哪（给用户圈选看，技术名词留英文）' },
    whyPublishable: { type: 'string', description: '解决/部分进展能投哪（AAAI/COLT/期刊）、为什么有人关心' },
    stillOpenEvidence: {
      type: 'array', items: { type: 'string' },
      description: 'URLs (with the date you checked) showing the problem is STILL OPEN as of today. NO evidence = do NOT include the target.',
    },
    field: { type: 'string', description: 'TCS / AI-theory / erdos / combinatorics / number-theory / …' },
    difficulty: { type: 'number', description: '1-5; 5 = flagship program. Anything you would rate >= 4.5 should not be submitted at all.' },
    winOdds: { type: 'number', description: '0-1 — your honest probability that a strong prover finds a complete informal proof within ~2 focused attempts' },
    value: { type: 'number', description: '1-5 publication/impact value' },
    knownPartials: { type: 'string', description: 'known partial results / best bounds — this becomes the raid AMMO, be thorough' },
    pitfalls: { type: 'string', description: 'why it has survived so far / how previous attempts died' },
    sourceUrls: { type: 'array', items: { type: 'string' } },
  },
}

const SCOUT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['route', 'targets'],
  properties: {
    route: { type: 'string' },
    targets: { type: 'array', items: TARGET_SCHEMA_ITEMS },
  },
}

const MERGE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['targets', 'droppedStale', 'droppedTooHard'],
  properties: {
    targets: { type: 'array', items: { ...TARGET_SCHEMA_ITEMS, required: [...TARGET_SCHEMA_ITEMS.required, 'score'], properties: { ...TARGET_SCHEMA_ITEMS.properties, score: { type: 'number', description: 'winOdds × value, 3 decimals' } } } },
    droppedStale: { type: 'array', items: { type: 'string' }, description: 'slugs dropped because openness evidence failed re-verification (solved / 404 / stale)' },
    droppedTooHard: { type: 'array', items: { type: 'string' }, description: 'slugs dropped by the hard filters (difficulty >= 4.5, winOdds < 0.03, no evidence)' },
  },
}

// ===== Phase Recon: 5 parallel scouts — backend 'codex' (ONLINE Codex) / 'claude' (WebSearch) / 'both' =====
phase('Recon')
log('Launching ' + ROUTES.length + ' scouts (backend=' + BACKEND + ', ' + PER_ROUTE + ' targets each)...')

// shared recon brief (backend-agnostic)
const scoutBrief = (r) => [
  'You are guerrilla scout ' + r.id + ' (' + r.name + '). Find OPEN math conjectures worth raiding:',
  'we only fight winnable battles (打得赢就打，打不赢就跑) and want results publishable at AI/theory venues (AAAI etc.).',
  '',
  'Sweep YOUR hunting ground (multiple searches + fetches, dig into actual pages, not just snippets):',
  'GROUNDS: ' + r.grounds,
  'PREY: ' + r.prey,
  '',
  'HARD FILTERS (violating any = do not submit the target):',
  '- NO flagship/millennium problems (P vs NP, Riemann, Unique Games, …) and nothing you would rate difficulty >= 4.5.',
  '- EVERY target needs stillOpenEvidence: >= 1 URL with the date you checked, clearly showing it is still open NOW. No evidence, no entry.',
  '- statement must be PRECISE (all quantifiers, all definitions) — it will be handed verbatim to a prover.',
  '- knownPartials must be substantive (best known bounds / solved special cases) — it becomes the raid ammunition.',
  '- Skip problems ALREADY IN OUR REPOSITORY (known slugs/titles, incl. previously rejected ones — do not re-scout them): ' + (EXCLUDE.length ? EXCLUDE.join(', ') : '(none)'),
  '',
  'Calibrate winOdds HONESTLY: most truly-open problems deserve <= 0.15; reserve >= 0.3 for "author left it as future work and it looks routine".',
  'Submit your best ' + PER_ROUTE + ' targets (fewer is fine if the ground is dry — quality over quantity).',
].join('\n')

// backend A: Claude subagent with WebSearch/WebFetch
const claudeScoutPrompt = (r) =>
  'FIRST call ToolSearch with query exactly "select:WebSearch,WebFetch" to load your tools, then use them for every search/fetch below.\n\n' + scoutBrief(r)

// backend B: ONLINE Codex (sandbox danger-full-access → internet via curl/wget; codex-online 模式)
const codexOnlineScoutPrompt = (r) => [
  'You are a guerrilla scout handler. Delegate the ONLINE recon to OpenAI Codex via MCP:',
  '1. call ToolSearch with query exactly "select:mcp__codex__codex".',
  '2. Call mcp__codex__codex with: prompt = the TASK below verbatim, sandbox = "danger-full-access", cwd = "' + GW + '". Do NOT pass model/config.',
  '3. Return the structured result faithfully.',
  '',
  'TASK:',
  'You have INTERNET access via your shell (curl/wget). Research ONLINE: fetch real pages, do not answer from memory alone; cite the URLs you actually fetched.',
  'CONSTRAINTS (you are unsandboxed — behave): READ-ONLY mission — do NOT create, modify, or delete ANY file; install nothing; only GET requests to public pages (arXiv, erdosproblems.com, MathOverflow, blogs, …); no logins, no posting.',
  '',
  scoutBrief(r),
].join('\n')

const scoutThunks = []
for (const r of ROUTES) {
  if (BACKEND !== 'claude') scoutThunks.push(() =>
    agent(codexOnlineScoutPrompt(r), { label: 'scout-codex:' + r.id, phase: 'Recon', stallMs: STALL, schema: SCOUT_SCHEMA, model: MODEL }))
  if (BACKEND !== 'codex') scoutThunks.push(() =>
    agent(claudeScoutPrompt(r), { label: 'scout-claude:' + r.id, phase: 'Recon', stallMs: STALL, schema: SCOUT_SCHEMA, model: MODEL }))
}
const scouted = (await parallel(scoutThunks)).filter(Boolean)
const raw = scouted.flatMap(s => s.targets || [])
log('Recon done: ' + raw.length + ' raw targets from ' + scouted.length + '/' + scoutThunks.length + ' scouts.')

// ===== Phase Merge: dedup + re-verify openness + score & rank (needs ALL targets → barrier OK) =====
phase('Merge')
const mergeTask = [
  'You are the guerrilla intelligence officer. Consolidate the raw scouted targets below into a final ranked target list.',
  'FIRST call ToolSearch with query exactly "select:WebFetch,WebSearch" to load your tools.',
  'Steps:',
  '1. DEDUP: merge entries that are the same problem (by slug or semantics); keep the richer knownPartials/evidence.',
  '2. RE-VERIFY: for the top ~8 by winOdds*value, WebFetch one stillOpenEvidence URL each (or WebSearch "<title> solved 2025 2026").',
  '   If the page 404s, shows the problem solved, or contradicts openness → DROP the target into droppedStale.',
  '3. HARD FILTERS: drop difficulty >= 4.5, winOdds < 0.03, or empty stillOpenEvidence → droppedTooHard.',
  '4. SCORE: score = round(winOdds * value, 3). Sort descending; tie-break lower difficulty first, then fresher evidence.',
  '5. Also drop anything matching this repository exclude list (slugs/titles; treat a semantic match — same problem under a different name — as a match): ' + (EXCLUDE.length ? EXCLUDE.join(', ') : '(none)'),
  'Return ALL surviving targets ranked (preserve every field, add score).',
  '',
  'RAW TARGETS:',
  JSON.stringify(raw),
].join('\n')

const merged = await agent(mergeTask, { label: 'merge-rank', phase: 'Merge', stallMs: STALL, schema: MERGE_SCHEMA, model: MODEL })
  || { targets: [], droppedStale: [], droppedTooHard: [] }
log('Merge done: ' + merged.targets.length + ' targets ranked · dropped ' + merged.droppedStale.length + ' stale / ' + merged.droppedTooHard.length + ' too-hard.')

return {
  targets: merged.targets,
  dropped: { stale: merged.droppedStale, tooHard: merged.droppedTooHard },
  rawCount: raw.length,
  note: '编排者须再抽验 top3 的 stillOpenEvidence（铁律 6）后才写 TARGETS.md/targets.json；圈选权在用户（SKILL.md §2）。',
}
