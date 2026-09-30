# strategies.md — r6's 3 Hybrid Parallel Strategies (MoE Pool)

r6 runs these **3 strategies** in parallel (not 7——the lesson from eval:complexity≠better,multi-agent/point-by-point approaches placed last in empirical testing). Each goes through argument compilation;the three **are deliberately differentiated and cover the risk spectrum**,allowing MoE to select strategies that genuinely explore different zones. verify selects the highest score → clear the gate → if it does not clear the gate, carry-forward and roll again( / moe_loop.py).

Hybridized from the 7 experts in `LZQ/.../agent_rebuttal_eval` (retaining their strengths and removing their weaknesses).

---

## ① Evidence-Locked · Structured (Low-Risk Anchor)
Hybridizes:EvidenceLocked_CriticRevise + argument compilation + evidence first.

- **Factual safety first**:never claim experiments that were not conducted;missing results must always be `[TBD]` + action item;do not write numbers without raw support.
- **Argument compilation**:build a DAG for each concern;each sentence = one claim node whose warrant is tied to real evidence.
- **Evidence first**:open each paragraph with the strongest evidence to reclaim the framing;do not begin by restating the reviewer's attack.
- **Positioning**:EvidenceLocked ranked 1st in our pool (the only one to clear bar). It has the best ammunition control and serves as the fallback anchor.

## ② Reviewer Persuasion · Discussion Anticipation (High raise Potential)
Hybridizes:RebuttalAgent_TSR + AgentReview_AuthorReviewerAC.

- **First infer internally**(hidden analysis,do not include it in the response):what does this reviewer actually want? Which concerns are **fundamental**,and which are **resolvable**? What can genuinely persuade TA?
- **Simulate discussion**:anticipate how reviewer-author-AC will proceed during the discussion stage,and focus effort on "the one point that will change TA's view."
- **Most willing to answer boldly**(highest raise rate in eval),but also the highest risk → **enforce a hard constraint through the ammunition gate grep==0**;do not hand over ammunition merely to answer boldly.

## ③ Supplementary-Evidence Planning · Multi-Stage (Turnaround for Weak Papers)
Hybridizes:Paper2Rebuttal_MultiStage + honest concession.

- **Multi-stage**:first consolidate the concern → **list "what additional experiments/evidence are needed"** → hand it to the experiment execution module (see shared-assets/experiment-ladder.md) to produce real results → then write a targeted response.
- **Integration with the experiment module**:this strategy is naturally a consumer of the r4a experiment branch——the only path for a weak paper to turn things around (pure writing cannot clear the gate;real evidence must be added).
- **Graceful honest concession**:for a genuine weakness that cannot be remedied,acknowledge it + define the scope;make no empty promise ("we will" is ammunition).

---

## Three Shared Iron Rules
1. All use argument compilation;every sentence has a traceable warrant.
2. Final draft ammunition grep==0 (monitor strategy② especially;it is the most willing to answer boldly).
3. Write only experiment results that were actually produced by running the experiments (especially strategy③);use `[TBD]` rather than an empty promise.
