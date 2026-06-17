"""Grounding — delegated to VeriTrace.

Second Opinion does not invent its own grounding. It sorts what the models say;
VeriTrace decides what the source can actually back up. The model proposes, the
source disposes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


@dataclass
class GroundResult:
    tier: str                       # "high" | "medium" | "low"
    score: float
    citation: Optional[dict] = None


@runtime_checkable
class Grounder(Protocol):
    def add_source(self, text: str, **meta) -> None: ...
    def ground(self, claim: str) -> GroundResult: ...


class VeriTraceGrounder:
    """Adapter around the VeriTrace engine (github.com/waelalebrahim/wa-VeriTrace-project)."""

    def __init__(self, veritrace=None, **veritrace_kwargs):
        if veritrace is None:
            from veritrace import VeriTrace  # imported lazily so tests can stub
            veritrace = VeriTrace(**veritrace_kwargs)
        self._vt = veritrace

    def add_source(self, text: str, **meta) -> None:
        self._vt.add_source(text, **meta)

    def ground(self, claim: str) -> GroundResult:
        report = self._vt.verify(claim)
        if not report.claims:
            return GroundResult(tier="low", score=0.0, citation=None)
        # a single claim string segments to one (sometimes more) results;
        # take the best-supported one as this claim's grounding
        best = max(report.claims, key=lambda c: c.score)
        cit = None
        if best.citation is not None:
            c = best.citation
            cit = {
                "source": getattr(c, "source_name", None),
                "passage": getattr(c, "passage", None),
                "date": getattr(c, "doc_date", None),
            }
        return GroundResult(tier=best.tier.value, score=float(best.score), citation=cit)
