// Optional host adapter for theory-to-paper Phase B. The caller supplies all results.
// Runtime must provide args, agent and pipeline; this is not a standalone Node CLI.
export const meta = {
  name: 'iclr-technical-core',
  description: 'Draft technical sections and full appendix proofs from locked, hardened results',
  phases: [
    { title: 'Main sections', detail: 'one agent per supplied result writes its section' },
    { title: 'Appendix proofs', detail: 'same result context writes its complete proof' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args || '{}') : (args || {})
if (!A.dir || !A.skills || !Array.isArray(A.results) || !A.results.length) {
  throw new Error('Pass dir, skills (references directory), and a nonempty results array')
}
const DIR = A.dir
const SKILLS = A.skills
const COMMON = `
Read ${DIR}/paper/NOTATION.md and ${DIR}/HARDENING.md in full.
Read ${SKILLS}/first_principles_writing.md and ${SKILLS}/paper_front_matter_discipline.md.
Each paragraph performs one logical job, starts with its concrete claim, and gives the necessary reasoning.
Introduce concepts before labels. Ground claims in established results, evidence or correct citations.
Use only locked notation, theorem labels and bib keys. Match all constants, constructions, hypotheses and claim directions to the source.
Remove defensive repetition; keep required assumptions, unresolved proof gaps and verification status accurate.
Write complete numbered proof steps with justifications, including domains, boundary cases and nonzero denominators.
Output a LaTeX fragment directly to the assigned file. Do not leave draft remarks or change other agents' files.
Return only a manifest: file path, theorem statement, paragraph count.
`

for (const r of A.results) {
  for (const key of ['key', 'proof', 'secFile', 'appFile', 'thm', 'job', 'appJob']) {
    if (typeof r[key] !== 'string' || !r[key].trim()) throw new Error(`Result missing ${key}`)
  }
}

const out = await pipeline(
  A.results,
  (r) => agent(
    `${COMMON}\nSOURCE PROOF: ${r.proof}\nWRITE SECTION: ${r.secFile}\n${r.thm}\n${r.job}`,
    { label: `main:${r.key}`, phase: 'Main sections', stallMs: 1800000 },
  ).then(mainManifest => ({ ...r, mainManifest })),
  (r) => agent(
    `${COMMON}\nSOURCE PROOF: ${r.proof}\nWRITE COMPLETE APPENDIX: ${r.appFile}\n` +
    `MAIN MANIFEST: ${r.mainManifest}\n${r.appJob}`,
    { label: `appendix:${r.key}`, phase: 'Appendix proofs', stallMs: 1800000 },
  ).then(appManifest => ({ key: r.key, mainManifest: r.mainManifest, appManifest })),
)
return out
