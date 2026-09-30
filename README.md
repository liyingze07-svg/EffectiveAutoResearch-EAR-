# EAR — Effective Auto Research

An automation toolkit for the full research workflow. It currently contains two independent, standalone subprojects:

| Subdirectory | What it does |
|---|---|
| **[`autovibeidea/`](autovibeidea/)** | **From research direction to proposal.** Literature survey → critical analysis → idea generation → multidimensional screening → in-depth refinement, producing an actionable, venue-ready proposal |
| **[`rebuttal/`](rebuttal/)** | **From reviews to responses.** Given a paper and its reviews, produces a response to each reviewer and a comment to the AC. Designed for EMNLP / ACL Rolling Review |

Together they cover both ends of the research cycle—topic selection and plan development **before submission**, and responding to reviews **after submission**. They share the design principles of "independent review by an external model + traceable evidence + no fabricated numbers or citations," but do not share code and can each be cloned and used separately.

---

## Quick Start

### autovibeidea — Find Ideas

```bash
cd autovibeidea
./run.sh --daemon "your research direction" NeurIPS   # run the full pipeline in the background
./run.sh --status                                     # check progress
```

Produces `outputs/LANDSCAPE.md` (literature map + gap matrix), `outputs/CRITICAL_ANALYSIS.md` (critique list),
`outputs/SCREENING_RANKED.md` (multidimensional score ranking), and `refine-logs/FINAL_PROPOSAL.md` (final proposal).

See [`autovibeidea/README.md`](autovibeidea/README.md) for details.

### rebuttal — Write a Rebuttal

Given a paper and its reviews, runs an 18-stage materialized pipeline and passes four gates to produce the responses.
See [`rebuttal/README.md`](rebuttal/README.md) for details.

---

## Shared Design Principles

- **External models serve as reviewers.** Generation and review are separated to prevent inflated self-evaluation.
- **Evidence is traceable.** Every claim must point back to literature, code, or experimental records.
- **No fabrication.** Do not invent experimental numbers or citations; if a search finds nothing, record that it found nothing.
- **Degrade without stopping.** When an external dependency is unavailable, automatically degrade and record the event; the pipeline does not stop to wait for a person.

---

## License

MIT. Copyright (c) 2026 Yingze Li, Dong Wang, Ben Wu.
See [LICENSE](LICENSE).
