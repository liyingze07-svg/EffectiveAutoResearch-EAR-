// Compatibility filename for the original expanded hardening workflow.
// Pass the mathematical context and findings explicitly; no private paper is embedded.
export const meta = {
  name: 'harden-eq-paper',
  description: 'Expanded theory-paper hardening: diagnose exact scope and conventions, adversarially settle missing converses, repair secondary findings, and synthesize corrected claims.',
  phases: [
    { title: 'Diagnose', detail: 'precise claims, quantifiers, conventions and proof gaps' },
    { title: 'Necessity', detail: 'prove versus refute missing directions; independent adjudication' },
    { title: 'Secondary', detail: 'definitions, boundary cases, computation and examples' },
    { title: 'Synthesize', detail: 'corrected claims and prioritized HARDENING report' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args || '{}') : (args || {})
if (!A.dir || !A.context) throw new Error('Pass dir and complete mathematical context')
const STALL = 1800000
const findings = A.reviewerFindings || []
const resultSchema = {
  type: 'object', additionalProperties: false,
  required: ['reportMarkdown'], properties: { reportMarkdown: { type: 'string' } },
}

function delegate(task, online) {
  return [
    'Delegate the bounded task to the configured Codex MCP backend.',
    'Load select:mcp__codex__codex using ToolSearch, then pass only prompt, sandbox and cwd.',
    `sandbox="${online ? 'danger-full-access' : 'read-only'}", cwd=${JSON.stringify(A.dir)}.`,
    online ? 'Online READ-ONLY research mission; verify original sources and assumptions.'
      : 'Prover role: browsing tools and network egress must be disabled by the host.',
    'On quota or connection failure, return an honest failure and preserve the checkpoint.',
    'Return full mathematics faithfully in reportMarkdown.', task,
  ].join('\n')
}

const diagnosis = await agent(
  `Read proofs and paper in ${A.dir}. Context: ${A.context}\nFindings: ${JSON.stringify(findings)}\n` +
  'Identify the exact central claim, quantifiers, fixed-instance versus worst-case scope, and missing directions. ' +
  'Turn each finding into a precise prioritized proof or definition repair. Do not edit files.',
  { label: 'diagnose', phase: 'Diagnose', stallMs: STALL, schema: resultSchema },
)
if (!diagnosis) throw new Error('Hardening diagnosis failed')

const [prove, refute] = await parallel([
  () => agent(delegate(`Context: ${A.context}\nDiagnosis: ${diagnosis.reportMarkdown}\n` +
    'Prove each missing necessity/converse direction. One focused attempt; if unsuccessful report the complete proved scope.', false),
    { label: 'necessity:prove', phase: 'Necessity', stallMs: STALL, schema: resultSchema }),
  () => agent(delegate(`Context: ${A.context}\nDiagnosis: ${diagnosis.reportMarkdown}\n` +
    'Refute unsupported necessity/converse directions with explicit counterexamples. Verify all hypotheses; do not change quantifiers.', false),
    { label: 'necessity:refute', phase: 'Necessity', stallMs: STALL, schema: resultSchema }),
])
if (!prove || !refute) throw new Error('Hardening proof/refutation unavailable; checkpoint required')

const adjudication = await agent(delegate(
  `Context: ${A.context}\nPROVE: ${prove.reportMarkdown}\nREFUTE: ${refute.reportMarkdown}\n` +
  'Hostile independent adjudication: verify every step and source. Decide proven/refuted/inconclusive; give the exact supported claim.', true),
  { label: 'necessity:adjudicate', phase: 'Necessity', stallMs: STALL, schema: resultSchema },
)
if (!adjudication) throw new Error('Hardening adjudication unavailable; checkpoint required')

const fixes = await agent(
  `Context: ${A.context}\nDiagnosis: ${diagnosis.reportMarkdown}\nFindings: ${JSON.stringify(findings)}\n` +
  'Repair conventions, definitions, small/boundary cases, computability assumptions and illustrative examples. ' +
  'Do not invent stronger claims or conceal unresolved steps. Report exact fixes; do not edit files.',
  { label: 'secondary', phase: 'Secondary', stallMs: STALL, schema: resultSchema },
)
const report = await agent(
  `Diagnosis: ${diagnosis.reportMarkdown}\nAdjudication: ${adjudication.reportMarkdown}\nSecondary: ${JSON.stringify(fixes)}\n` +
  'Synthesize HARDENING.md: prioritized gaps, exact corrected claim, proved directions, rejected directions, paper edits and remaining work. ' +
  'If necessity is refuted or unresolved, downgrade the iff to the established one-way result; preserve scientific scope.',
  { label: 'synthesize', phase: 'Synthesize', stallMs: STALL, schema: resultSchema },
)
return { diagnose: diagnosis, necessity: { prove, refute, adjudication }, fixes, report }
