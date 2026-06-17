# Second Opinion — Specification (V1)

The contract this tool keeps. If a change would break one of these, it is a breaking change.

## Purpose

Given one question and two or more models, produce a **verdict** that separates:

- what the models **agree on**,
- what is **contested** between them, and
- what **none of them can back up** against the provided sources.

Second Opinion never merges the models into a single confident answer. The disagreement is preserved on purpose.

## Inputs

- **Models** — two or more responders, each turning a question into a text answer.
- **Sources** — zero or more documents added via `add_source(text, id=, name=, date=)`, forwarded verbatim to VeriTrace.
- **Question** — a single string.

## Pipeline

1. **Gather.** Each model answers the question independently. No model sees another's answer.
2. **Segment.** Each answer is split into claims using VeriTrace's `split_into_claims`.
3. **Cluster.** Claims are grouped across models by content-token overlap (Jaccard ≥ `similarity_threshold`, default 0.6). A cluster's `models` is the set of models that asserted it.
4. **Ground.** Each cluster's representative claim is verified by VeriTrace against the sources, yielding a tier (`high` / `medium` / `low`), a score, and a citation when grounded.
5. **Bucket**, in this precedence:
   1. tier == `low` → **UNBACKABLE** (the source cannot back it — overrides everything, including consensus).
   2. else, supported by ≥ the agreement threshold of models → **AGREED**.
   3. else → **CONTESTED**.

Agreement threshold defaults to a simple majority (`"majority"`); `"all"`, `"any"`, or an integer are also accepted.

## Guarantees

- **No fabrication is ever certified.** A claim VeriTrace grades `low` is always `UNBACKABLE`, regardless of how many models agree.
- **Consensus alone never promotes a claim.** Agreement plus grounding is required for `AGREED`.
- **Every grounded claim carries its citation** (source name, passage, date).
- **Determinism.** Given the same model answers and sources, the verdict is identical (the engine itself adds no randomness).

## Non-goals (on purpose)

- **No synthesized "best answer."** Merging the models would hide the split.
- **No majority-vote truth.** Three models repeating a claim does not verify it; only a source does.
- **No scoring or ranking of the models.** This locates agreement and grounding, not a winner.
- **No live/market data, math, or predictions.** It compares and grounds claims.

## Known limitations (V1)

- Clustering and grounding are **lexical**, not semantic. Paraphrased agreement may split; entity-reuse fabrications grade `medium` (→ `CONTESTED`) rather than `low` (→ `UNBACKABLE`). A semantic/NLI backend is the fix and is on the roadmap of both this tool and VeriTrace.
- Claim segmentation is sentence-level.
- Model calls are sequential in V1.

Created by **Wael Alebrahim**. MIT licensed.
EOF
echo "SPEC written"