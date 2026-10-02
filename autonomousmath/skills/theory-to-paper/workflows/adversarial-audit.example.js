// WORKED EXAMPLE — Phase D of theory-to-paper (see ../SKILL.md §1, §3).
// Reuse: edit DIR/MAIN/APP and the file lists; ADD a sixth "claim-strength / converse-checker"
// auditor per SKILL.md §3 (hunts every iff/exactly/characterizes/tight/necessary-and-sufficient
// and asks whether the converse is actually proved — the one error this pipeline is blind to).
// Auditors RETURN findings {file, locator, severity, issue, fix}; the orchestrator applies them
// (default CUT). math-faithfulness checks TRANSCRIPTION ONLY, never correctness.

export const meta = {
  name: 'iclr-adversarial-audit',
  description: 'Independent auditors over a theory-paper draft: ammunition, research-writing quality, logic-chain, front-matter, math-faithfulness (+ claim-strength)',
  phases: [{ title: 'Audit' }],
}

// args (JSON STRING) → parse. { dir, skills?, mainfiles? (comma-joined absolute paths) }
const A = typeof args === 'string' ? (args ? JSON.parse(args) : {}) : (args || {})
const DIR = A.dir || '.'
if (!A.skills) throw new Error('Pass the bundled writing references directory')
const SK = A.skills
const MAIN = `${DIR}/paper/sections`
const APP = `${DIR}/paper/appendix`

// Default file list matches the worked example; override via args.mainfiles for other papers.
const MAINFILES = A.mainfiles || `${MAIN}/*.tex`

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['file', 'locator', 'severity', 'issue', 'fix'],
        properties: {
          file: { type: 'string', description: 'file name, e.g. intro.tex' },
          locator: { type: 'string', description: 'quote the exact offending phrase/sentence so it can be found' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          issue: { type: 'string', description: 'what rule it violates and why' },
          fix: { type: 'string', description: 'concrete surgical fix — prefer CUT; give replacement text only if a rewrite is needed' },
        },
      },
    },
  },
}

const AUDITORS = [
  {
    label: 'ammunition',
    prompt: `Read ${SK}/scientific_claims_and_scope.md in full. Then read every MAIN-TEXT file: ${MAINFILES}.
Your job: find every sentence/phrase that hands a reviewer ammunition — any redundant self-commentary, defensive claims against absent objections, empty importance markers or repeated prose. Preserve substantive assumptions, proof gaps, verification status and required limitations. Grep the landmine patterns in the skill. For each hit return file, the exact quoted phrase (locator), severity, the rule, and the fix (default: CUT; or rewrite as a positive claim). Return findings only; do not edit files. If clean, return empty findings.`,
  },
  {
    label: 'writing-quality',
    prompt: `Read ${SK}/research_writing_checklist.md and ${SK}/sentence_paragraph_checks.md in full. Then read: ${MAINFILES}.
Audit across the general research-writing dimensions: terminology exactness (no vague/self-invented terms; one concept one name), mechanism-not-surface (no empty "X enables Y" without the how), redundancy (title vs text, table vs prose, sentence earns its place), structure-serves-logic (conclusion first), overclaim (attackable absolute wording), citation loop-closure (no dangling "this/both/see X"). Return file, exact quoted locator, severity, the dimension+why, and a surgical fix. If clean, return empty findings.`,
  },
  {
    label: 'logic-chain',
    prompt: `Read ${SK}/first_principles_writing.md in full. Then read: ${MAINFILES}.
Audit the paragraph chain: does each paragraph do exactly one job; is the first sentence a job-stating claim (not a transition); does it inherit from the previous paragraph; does it close on the strongest form of the claim (not a recap or bare forward-pointer); are there implicit logical jumps a reader cannot follow; any floating claim without grounding; any concept used before it is introduced. Check the logical dependencies across setup, results, proofs and related work. Return file, quoted locator, severity, the issue, and a surgical fix. If clean, return empty findings.`,
  },
  {
    label: 'frontmatter',
    prompt: `Read ${SK}/paper_front_matter_discipline.md in full. Then read the front-matter files only: ${MAIN}/abstract.tex, ${MAIN}/intro.tex, ${MAIN}/results.tex, ${MAIN}/related.tex, ${MAIN}/discussion.tex.
Audit against the 10 anti-patterns and the hard rules: relocate-instead-of-delete, trivial corollary, defending absent objections, methodology self-narration, formula wall (intro narrative budget = at most 2 formulas, 0 theorem cites), list-as-argument, circular paragraph, repeating-earlier-section, hedge words (importantly/notably/we argue/it is worth noting), author-blind logic gaps. Also: no phone-number hooks, no naming ceremonies, no forward-pointer closers, no bullet lists except the intro contributions list. Return file, quoted locator, severity, the anti-pattern, and the fix. If clean, return empty findings.`,
  },
  {
    label: 'math-faithfulness',
    prompt: `You are checking transcription fidelity ONLY — do NOT re-derive or re-verify the mathematics, and do NOT flag the proofs as needing verification. Compare the LaTeX against the source markdown for SAME constants, construction, logic, theorem statements.
Read the theorem-to-source map in ${DIR}/paper/NOTATION.md. Compare each main theorem and its complete appendix proof against the mapped source under ${DIR}/proofs/ and the corrections in ${DIR}/HARDENING.md.
Flag any discrepancy: wrong constants, altered construction, dropped hypotheses, mis-stated theorem, or a claim in the LaTeX not supported by the source. Also flag any internal inconsistency between a main-text theorem statement and its appendix restatement. Return file, quoted locator, severity, the discrepancy, and the fix. If faithful, return empty findings.`,
  },
  {
    // ⭐ 6th auditor — claim-strength / converse-checker. THE lesson from the worked example:
    // math-faithfulness checks transcription, not truth, so an inherited "iff/tight/characterization"
    // overclaim sails through. This auditor hunts every such claim and demands the converse be proved.
    label: 'claim-strength',
    prompt: `You are the claim-strength / converse adversary. Read every MAIN-TEXT file: ${MAINFILES}. Also read the source proofs in ${DIR}/proofs/ and any ${DIR}/HARDENING.md / ${DIR}/STATUS.md if present.
Hunt EVERY strong-form claim word: "iff", "if and only if", "exactly when", "characterization", "characterize(s)", "dichotomy", "tight", "necessary and sufficient", "the exact dividing line", "precisely", "optimal", "matching". For each occurrence ask the decisive question: IS THE CONVERSE / NECESSITY DIRECTION ACTUALLY PROVED in a source proof, or is only one direction (sufficiency) + a single witness established?
- If only sufficiency + a witness exists, the claim is an OVERCLAIM (severity=blocker): downgrade to the exact established one-way statement or separation. Do not assert that necessity is false unless a valid counterexample establishes that; mark an unresolved direction accurately.
- Also flag "tight"/"optimal"/"matching" where only one of the upper/lower bound is in the sources.
Return file, the exact quoted claim (locator), severity, why the converse is unsupported, and the precise downgraded wording. If every strong claim has both directions proved in the sources, return empty findings.`,
  },
]

const results = await parallel(AUDITORS.map(a => () =>
  agent(a.prompt, { label: a.label, phase: 'Audit', stallMs: 1800000, schema: SCHEMA })
    .then(r => ({ auditor: a.label, findings: (r && r.findings) || [] }))
))

return results.filter(Boolean)
