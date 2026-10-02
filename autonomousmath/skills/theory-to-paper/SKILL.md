---
name: theory-to-paper
description: Turn verified informal theoretical results into a complete LaTeX paper through locked notation, technical and front-matter drafting, six independent audits, and revision; used after AutonomousMath hardening.
---

# theory-to-paper — proofs to a complete paper

Write a path from the reader's starting knowledge to the established contribution. Each paragraph performs one logical job; every claim has prior evidence, common knowledge, or a correct citation. Preserve the research story and established mathematics rather than inventing a stronger result during writing.

Read these bundled guides before drafting:

- `references/first_principles_writing.md`: logical spine, paragraph roles, concepts before labels, faithful claims.
- `references/paper_front_matter_discipline.md`: concise front matter and the seven-step paragraph audit.
- `references/scientific_claims_and_scope.md`: match claim scope and evidence while keeping required scientific assumptions and limitations accurate.
- `references/sentence_paragraph_checks.md`: sentence and paragraph checks.
- `references/research_writing_checklist.md`: seven general quality dimensions; no personal reviewer imitation.

## Five phases

**A — Architecture.** Read all `proofs/*.md` and `HARDENING.md`. Lock a central contrast, contribution order, section jobs, theorem-to-source/label map, notation macros and bib keys in `paper/NOTATION.md`. Set up `paper/main.tex` from the template and copy the bundled ICLR style assets from `templates/iclr-style/`. Establish numbered full proofs and ≥7 pages of main text without padding. Check actual citation metadata online.

**B — Technical core.** One drafting item per result writes a main section and its appendix proof in the same context. Follow the locked notation and exact corrected claims. Distinct writers own disjoint files; return a manifest of paths and theorem statement. `workflows/technical-core.example.js` is an optional adapter accepting `{dir,skills,results}`; it contains no private result defaults.

**C — Front matter.** Write Setting → Results → Introduction → Abstract → Related Work → Discussion in dependency order. Introduce concepts before labels, avoid repeated contributions and formula walls, and make title/abstract claims exactly match proven results. Definitions, assumptions and precise scope belong in the formal setup; required limitations and unresolved proof gaps remain explicit and truthful.

**D — Six independent audits.** Each audit returns `{file,locator,severity,issue,fix}`; the coordinator owns edits:

1. Unnecessary defensive rhetoric/repetition (“ammunition”).
2. General research-writing quality: exact terminology, mechanisms, information gain, structure, claim strength, citations, and reader reasoning.
3. Logical chain and paragraph jobs.
4. Front matter structure and narrative formula budget.
5. Mathematical transcription fidelity to proofs and Harden: constants, hypotheses, construction, theorem restatements and labels.
6. Claim strength and converse: every iff/tight/characterization must have both directions actually proved.

Transcription fidelity checks representation, not mathematical truth. The sixth audit is required even when transcription is flawless. `workflows/adversarial-audit.example.js` is an optional host adapter; pass file lists and the bundled references directory.

**E — Revise and assemble.** Apply locatable findings surgically. Cut redundant prose rather than moving it around. Recompile with pdflatex/bibtex as needed. Require zero errors, undefined references and duplicate labels; a stable notation; no `TODO/FIXME/Wait.../no, rearrange...` remnants; precise boundary cases, domains and nonzero denominators. Review every retained mathematical limitation rather than concealing it to improve a score. Assemble the full paper for independent final review.

## Host adaptation

Workflow scripts need the host's `agent/parallel/pipeline/log` runtime. Without it, the coordinating model writes the same files and runs bounded independent audits through native tools. Never stop at HARDENED merely because Workflow is unavailable. All writing templates and reference guides are bundled; no private parent project is required. Use the workspace/campaign supplied by the caller rather than a user-specific default path.
