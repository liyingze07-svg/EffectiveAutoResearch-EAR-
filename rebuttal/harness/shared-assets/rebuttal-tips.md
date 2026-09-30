# rebuttal-tips.md — concern taxonomy + response handbook (paper-agnostic)

Distilled from four sources (28 MLNLP Paper-Rebuttal-Tips / awesome-rebuttal / Paper2Rebuttal / Devi Parikh). r2 uses it for classification, and r6 injects it during writing. **Core creed: Good rebuttal = Respect + Evidence + Clarity. Action, not promises (Tip 12).**

---

## Taxonomy (for r2 tagging)

### Class I — Novelty / Motivation / Theory / Boundaries
| concern | Poor Response (prohibited) | Recommended (warrant direction for the argument DAG) |
|---|---|---|
| insufficient novelty / merely a combination | "We acknowledge that it is a combination, but..." (accepting the framing) | Present the ablation: a naive combination fails → the combination is nontrivial → our mechanism is the contribution |
| unclear contribution | repeat the abstract | anchor the single core contribution in one sentence + point to the evidence |
| weak motivation | discuss importance in the abstract | use a specific failure case/gap to prove that the problem genuinely exists |
| shallow theory | pile up formulas | identify the theorem's boundaries + state clearly what it guarantees |
| shallow discussion of limitations | add a disclaimer paragraph | delineate the boundaries precisely (holds within X), turning the limitation into scope |

### Class II — Presentation / Related Work / Communication
| concern | Poor | Recommended |
|---|---|---|
| unclear writing | "We will revise it" | provide a clear version directly in the rebuttal + point to the location in § |
| missing related work | list citations | differentiate: identify the axis on which we differ from them (with warrant) |
| **reviewer misreading** | rebut word by word | politely point out that the paper already explains this in §X + quote the original text; do not assign blame |

### Class III — Experimental Evidence
| concern | Poor | Recommended |
|---|---|---|
| missing baseline / no comparison with Z | "Z is not comparable" | add a real baseline (with fair tuning) or point to an existing comparison; if we genuinely cannot beat it, make an honest concession + state the scope |
| insufficient ablation | "It is already sufficient" | add the key ablation to prove that every component is necessary |
| compute cost | evade it | provide real numbers + compare with similar methods |
| generalization | "It should work" | add one held-out/cross-domain result |
| statistical significance | report only the mean | add variance/significance tests |
| data leakage | deny it | explain the split protocol clearly |
| reproducibility | promise to release code | provide the key details/pseudocode now |

---

## General response rules (warrant selection during writing)
1. **Misreading** (misread) → Class II response mode: point to the location + quote the original text; do not add anything new.
2. **Real gap** (gap) → Class III: add real experiments/literature, or make an honest concession + delineate the scope.
3. **frame-lock** → do not respond point by point; first use the strongest evidence to break the framing (e.g., use an ablation to refute "merely a combination").

## Devi Parikh principles (excerpt, writing Avoid list)
- Do not be defensive/emotional; assume reviewer goodwill.
- Do not use "future work / add it in camera-ready" to brush off P0 (empty promise = ammunition).
- Answer the most important issue (P0) first; do not mechanically follow reviewer order.
- Make every response self-contained: the reviewer should not have to look back through the paper to understand it.
- Give the AC one sentence explaining why this paper should be accepted (confidential comment).

## per-reviewer strategy matrix(awesome-rebuttal)
Use a distinct posture for each reviewer rather than a uniform one: a low-score, high-confidence P0 reviewer is the main battleground (raising that reviewer's score improves the overall score the most); simply maintain a high-score reviewer, and do not create unnecessary complications that open new attack surfaces.
