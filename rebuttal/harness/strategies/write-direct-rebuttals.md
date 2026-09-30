# write-direct-rebuttals — r6 Primary Method for External Presentation(Argument Compilation Paradigm)

> Distilled from `campaigns/01-wdData/lyzHandCraft/skills/write-direct-rebuttals/`(ground truth manually edited and validated by the user,01-wdData).
>
> **Paradigm**:rebuttal = compilation of the **minimal, literal, honest direct response** to each question slot from the reviewer. **Directness overrides all rhetoric——never allow narrative polishing to dilute directness.**
>
> **Division of responsibilities**:`CRAFT.md`(§0–5:diagnosing the real concern / three-way position routing / 14 concern playbooks)provides the **internal logic**(determine "which real concern to answer and what evidence to use");**this file governs external presentation**——produce the final reviewer-facing draft accordingly. Two passes:first achieve atomic precision,then compile into continuous W prose.

## Two-Pass Workflow

1. **Atomic responses**:break every reviewer question down into "one answer slot",and answer each slot literally and directly(the internal working draft uses the `Direct answer / Why / Camera-ready change` scaffold).
2. **Compilation**:merge related atomic responses into **continuous prose** with one paragraph per W,remove the scaffold labels,and run the deletion + ammunition tests.

## Lock the Sources
- reviewer original text = **the only source for quotations**(verbatim,with no fabricated ellipses).
- Manuscript = verify definitions/assumptions/formulas/existing results.
- Technical notes/experiment summaries = evidence,not prose to copy.
- Required format + revision tense.
- **Exclude old rebuttal drafts from the first writing pass**(old indirect/risky language will anchor and contaminate the writing).

## Atomized Decomposition + Literal Mapping(Hard Rules)
Break each unit down into one answer slot,retaining the reviewer’s **subject/verb/object**. **Every clause in a multipart question must be answered**,splitting it into blocks when necessary. **Do not treat politeness as a separate question**(merge "Can you speak to this?" into the substantive question that follows it;do not answer "Yes, we can speak to this").

| Reviewer slot | Direct-answer opening(the first sentence must begin this way) |
|---|---|
| `What is X?` | `X is …` |
| `What is the input for X?` | `The input for X is …` |
| `Is it A, B, or both?` | `It is …`(answer A/B/both respectively) |
| `Do you think X works for Y?` | `Yes, we think X works for Y when …` |
| `How many n are needed?` | `The required n is …`(give the rule + a supported operating point) |
| `How would it hold under Z?` | `The method holds under Z by …` |
| `Could X cause harm Y?` | `X did / did not cause measured Y …` |
| `Please define/change/add X` | `In the camera-ready version, we will define/change/add X …` |

**If the direct-answer opening cannot immediately follow the quotation → the question is still too broad,or the answer is evasive.**

## Rules for Each Atomic Response
- **Answer first**,then context/nuance/formulas/evidence.
- Use a formula only when it "proves the answer or eliminates an explicitly stated misunderstanding";use a number only when it "answers the quantity/result requested by the reviewer".
- **Three-way tense rule(hard)**:existing theory = present tense;completed experiments = past/present perfect tense;**manuscript edits = future tense `In the camera-ready version, we will …`**.
- **State technical boundaries as positive conditions,not as apologies/limitations**:write "The theorem applies **when** the composition is inherited across rounds",not "limitation: we did not cover X".

## Compile into W Blocks
Use one paragraph of continuous prose per W(not a checklist):
```
**W1 (“minimal verbatim reviewer quotation”):** <immediate direct answer> <necessary explanation and evidence> In the camera-ready version, we will <specific change>.
```
Within each block:①preserve the literal direct-answer opening → ②order premise → mechanism → evidence → camera-ready action → ③merge duplicate definitions/evidence → ④express distinct answer slots as consecutive explicit sentences → ⑤**remove working labels such as `Core question/Direct answer/Why/Camera-ready change`**.
**Never add a generic thank-you paragraph or restate the reviewer’s praise before W1.**

## Readability(Prose Craft,Hard Rules)
Argument compilation is a reasoning task that must be "logically rigorous",but **the rendered result must sound like a normal person speaking**——rigorous ≠ awkward. Check sentence by sentence:
- **One quantity per sentence**:one sentence carries only one claim/one quantity. **Never** pack three or four parallel quantities(lower bound / exchange rate / slope band …)into a single sentence by stringing them together with parenthetical theorem numbers. Multiple quantities → split them into "The first is … The second is … The third is …".
- **Never use an em dash(em-dash `—` / double em dash `——`)as a clause connector**. It is the leading source of awkward and "nonhuman" prose. Fix:when the sentence should stop,use a **period** and start a new sentence;use a **colon** for an explanation;use a comma or "and" for coordination.
- **Never correct the reviewer with a "not X but Y" contrast construction**(`not…but` / `rather than` / `instead of`;English `not X but Y` / `rather than` / `instead of` / `X, not Y`). Such contrasts sound like **arguing with/correcting** the other party and appear especially confrontational to an aggressive reviewer. Fix:**state only the intended Y positively**,allowing X to fall away naturally——"The contribution lies not in the theorem but in the protocol"→"The contribution lies in the protocol it supports";"IC does not measure faithfulness;it measures behavioral coupling"→"IC measures behavioral coupling,and that is all";"Do not trust the scalar;read the two coordinates"→"Read the two coordinates;the scalar is wrong 46% of the time here". **Exception**:a `rather than` in the reviewer’s original sentence is a verbatim quotation;preserve it unchanged.
- **Use theorem/proposition numbers only as tail notes**:write the sentence’s natural claim first,then end with a parenthetical `(Thm 2, see Thm 3 for the structural form)`. **Do not** let the number interrupt the main sentence structure.
- **Write numerical ranges in prose as "from X to Y"**,not with an in-sentence hyphenated range such as `7.0–31.0%`(a range mark in body text reads like an em dash). Parenthetical CIs `[0.39, 0.53]` and compound-word hyphens(`sign-mismatch`,`e-SNLI`,`camera-ready`)are unaffected.
- **Self-check**:**read every paragraph aloud**. Any sentence that "cannot be read in one breath / requires rereading to recover the subject,verb,and object" is overloaded;split it.

## deletion test + ammunition test(Run Sentence by Sentence Before Delivery)
**deletion test**:every sentence must serve **exactly** one function——①answer a slot ②define a necessary term/condition ③connect a premise to the answer ④provide evidence ⑤specify a camera-ready edit. **Delete every sentence outside these functions.**

**ammunition test**:ask "Can the reviewer copy this sentence directly into a new criticism?" Rewrite or delete:
- volunteer weaknesses that were not asked about;
- `we do not claim / we did not test / future work / our sample is limited`;
- extending a claim beyond the evidence(over-claim);
- unsupported claims of real-world generality;
- **describing a substantive objection as "only a clarity issue"**;
- introducing a **new promise / metric / setting / assumption** that the answer does not require.
> However,**never conceal facts necessary to answer the reviewer**;state necessary boundaries as positive technical conditions.

## Pre-Delivery 8-Item Acceptance Check(Internal Q-A audit)
1. Every quotation **matches the original review exactly**.
2. Every substantive question has a direct answer.
3. Every direct-answer opening **must mirror the reviewer’s subject/verb/object**.
4. Politeness has not been answered as a separate question.
5. Every quantitative claim maps to a manuscript result or the supplied evidence.
6. Every manuscript edit uses the **camera-ready future tense**.
7. Every atomic answer appears **exactly once** in the final W blocks.
8. Every sentence passes the deletion + ammunition tests.
9. Every sentence passes the **readability** check:one quantity per sentence / 0 em dashes(`—`,`——`)/ **0 "not X but Y" contrast constructions**(`not…but`,`rather than`,`instead of`,`not X but Y`,`rather than`,except within reviewer quotations)/ theorem numbers only as tail notes / can be read aloud in one breath.

## Submission Draft and Internal Logic
English submission draft = continuous prose;a separate English `Logic:` file records for each W block:literal answer slot / answer after mirror / necessary evidence chain / camera-ready change / whether it creates an attack surface. (**Logic stays internal,directness stays external**——this is argument compilation,with the scaffold kept internal.)

## One Incorrect and One Correct Example
- ✗ Asked "input for X?"→ Answered "The key distinction is between identity and composition."(reframe,no direct answer)
- ✓ Asked "input for X?"→ Answered "The input for the admission filter is the current-round candidate pool. The composition inherited by the next round is …"
- ✗ Asked "…would it work for a low-resource language?"→ "Yes, we can speak to this."(answered the politeness)
- ✓ Same question → "Yes, we think the approach would work for a low-resource language when …"
