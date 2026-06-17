"""End-to-end tests against the real VeriTrace engine, using offline responders."""
from secondopinion import SecondOpinion, FunctionResponder, Bucket


def build(claude, gemini, deepseek, source):
    so = SecondOpinion([
        FunctionResponder("Claude", lambda q: claude),
        FunctionResponder("Gemini", lambda q: gemini),
        FunctionResponder("DeepSeek", lambda q: deepseek),
    ])
    so.add_source(source, id="src", name="Cheat sheet", date="2025-01-01")
    return so


SOURCE = (
    "Delaware is the standard choice for venture-backed startups. "
    "The Delaware franchise tax minimum is 400 dollars per year plus a 50 dollar report fee. "
    "Wyoming has no state income tax and stronger owner privacy."
)


def test_summary_and_model_names():
    so = build(
        "Delaware is the standard choice for venture-backed startups.",
        "Delaware is the standard choice for venture-backed startups.",
        "Delaware is the standard choice for venture-backed startups.",
        SOURCE,
    )
    v = so.ask("Where should we incorporate?")
    assert v.model_names == ["Claude", "Gemini", "DeepSeek"]
    assert "3 models ->" in v.summary()


def test_agreed_when_all_models_share_a_grounded_claim():
    so = build(
        "Delaware is the standard choice for venture-backed startups.",
        "Delaware is the standard choice for venture-backed startups.",
        "Delaware is the standard choice for venture-backed startups.",
        SOURCE,
    )
    v = so.ask("Where should we incorporate?")
    assert len(v.agreed) == 1
    c = v.agreed[0]
    assert set(c.models) == {"Claude", "Gemini", "DeepSeek"}
    assert c.tier == "high"
    assert c.citation is not None


def test_contested_when_models_give_different_figures():
    so = build(
        "The Delaware franchise tax is about 450 dollars per year.",
        "The Delaware franchise tax is around 175 dollars plus fees.",
        "The Delaware franchise tax is roughly 300 dollars annually.",
        SOURCE,
    )
    v = so.ask("What is the Delaware franchise tax?")
    # three different figures => not a majority cluster => contested
    assert len(v.contested) >= 2
    assert not v.agreed


def test_unbackable_when_source_cannot_support_it():
    so = build(
        "Delaware is the standard choice for venture-backed startups.",
        "Delaware is the standard choice for venture-backed startups.",
        "Founders must personally guarantee all corporate debts under maritime law.",
        SOURCE,
    )
    v = so.ask("Where should we incorporate?")
    texts = " ".join(c.text for c in v.unbackable).lower()
    assert "maritime" in texts
    # the shared, grounded claim is still agreed
    assert any("standard choice" in c.text.lower() for c in v.agreed)


def test_agreement_isnt_truth_unbacked_consensus_is_flagged():
    # all three agree, but the source says nothing about it -> unbackable, not agreed
    fab = "The registration process always completes in exactly seven minutes by federal mandate."
    so = build(fab, fab, fab, SOURCE)
    v = so.ask("How long does registration take?")
    assert any("seven minutes" in c.text.lower() for c in v.unbackable)
    assert not v.agreed


def test_known_limitation_entity_reuse_grounds_medium_not_low():
    # honest limitation inherited from VeriTrace's lexical backend:
    # a fabrication that reuses real source entities scores MEDIUM, not LOW,
    # so it is not certified (not agreed) but also not fully rejected.
    so = build(
        "Delaware is the standard choice for venture-backed startups.",
        "Delaware is the standard choice for venture-backed startups.",
        "Delaware offers a 9000 dollar franchise tax rebate to every new startup.",
        SOURCE,
    )
    v = so.ask("Where should we incorporate?")
    rebate = [c for c in v.claims if "rebate" in c.text.lower()]
    assert rebate, "the rebate claim should appear somewhere in the verdict"
    # it must NOT be certified as agreed
    assert all(c.bucket is not Bucket.AGREED for c in rebate)


def test_requires_at_least_two_models():
    import pytest
    with pytest.raises(ValueError):
        SecondOpinion([FunctionResponder("Solo", lambda q: "hi")])
