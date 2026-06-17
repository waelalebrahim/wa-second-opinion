"""The Second Opinion engine.

Ask several models the same question, then sort every claim into:
  AGREED       — most/all models say it and a source can back it
  CONTESTED    — the models diverge; no single one is trustworthy yet
  UNBACKABLE   — no source supports it; flagged as unknown, never asserted

Grounding is delegated to VeriTrace. Agreement is computed by lexical clustering
across models — deterministic, no extra model, and honest about its limits.
"""
from __future__ import annotations

from typing import Union

from .grounding import Grounder, VeriTraceGrounder
from .responders import Responder
from .text import cluster_claims, split_claims
from .types import Bucket, Claim, Verdict


class SecondOpinion:
    def __init__(
        self,
        models: list[Responder],
        grounder: Grounder | None = None,
        similarity_threshold: float = 0.6,
        agreement: Union[str, int] = "majority",
        **veritrace_kwargs,
    ):
        if len(models) < 2:
            raise ValueError("Second Opinion needs at least two models to compare.")
        self.models = list(models)
        self.grounder: Grounder = grounder or VeriTraceGrounder(**veritrace_kwargs)
        self.similarity_threshold = similarity_threshold
        self.agreement = agreement

    # ---- sources (forwarded to the grounder / VeriTrace) ----
    def add_source(self, text: str, **meta) -> "SecondOpinion":
        self.grounder.add_source(text, **meta)
        return self

    # ---- model querying ----
    def gather(self, question: str) -> list[tuple[str, str]]:
        """Ask every model independently. Returns (model_name, answer) pairs."""
        return [(m.name, m.answer(question)) for m in self.models]

    def _min_support(self) -> int:
        n = len(self.models)
        if self.agreement == "all":
            return n
        if self.agreement == "any":
            return 1
        if isinstance(self.agreement, int):
            return max(1, min(self.agreement, n))
        return n // 2 + 1  # "majority"

    # ---- the verdict ----
    def ask(self, question: str) -> Verdict:
        answers = self.gather(question)

        per_model: list[tuple[str, str]] = []
        for name, text in answers:
            for claim in split_claims(text):
                per_model.append((name, claim))

        clusters = cluster_claims(per_model, self.similarity_threshold)
        min_support = self._min_support()

        claims: list[Claim] = []
        for cl in clusters:
            g = self.grounder.ground(cl.text)
            if g.tier == "low":
                bucket = Bucket.UNBACKABLE      # source can't back it — overrides
            elif len(cl.models) >= min_support:
                bucket = Bucket.AGREED          # shared and at least partly grounded
            else:
                bucket = Bucket.CONTESTED       # the models diverge here
            claims.append(
                Claim(
                    text=cl.text,
                    models=cl.models,
                    bucket=bucket,
                    tier=g.tier,
                    score=g.score,
                    citation=g.citation,
                )
            )

        order = {Bucket.AGREED: 0, Bucket.CONTESTED: 1, Bucket.UNBACKABLE: 2}
        claims.sort(key=lambda c: (order[c.bucket], -c.score))
        return Verdict(question=question, model_names=[m.name for m in self.models], claims=claims)
