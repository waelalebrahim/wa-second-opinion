# Second Opinion

**A multi-model second opinion that won't hide the disagreement.** Ask several AI models the same question. Instead of blending their answers into one confident reply, Second Opinion shows you what they **agree on**, what's **contested**, and what **none of them can back up** then grounds the claims against the documents you trust. If nothing can back a claim, it says so.

It's [VeriTrace](https://github.com/waelalebrahim/wa-VeriTrace-project), pointed at the gap between models the enforcement of [The I Don't Know Project](https://theidkproject.ai) applied across a council of models instead of one.

🔗 **Live demo:** *add your Cloudflare Pages URL here once deployed* runs entirely in the browser, no server, no keys.

- **The disagreement is the signal.** No blended "best answer" that buries where the models split.
- **Agreement is not truth.** Every claim — even one all models share is checked against your sources by VeriTrace.
- **It judges claims, not whole answers.** A model can be right on one line and flagged on the next.
- **Dependency-light.** Pure standard library plus the VeriTrace engine. Models are reached through OpenRouter (one key, many providers) or stubbed for offline runs and tests.

---

## The one idea

> **Agreement is not truth — so show the disagreement and ground the rest.**

Every other multi-model tool optimizes for a single, confident, synthesized answer, which quietly buries the places the models disagreed and the claims none of them could support. Second Opinion does the opposite. The models propose; the source disposes.

## Install

```
# Built on VeriTrace. Until both are on PyPI, install VeriTrace first:
pip install "git+https://github.com/waelalebrahim/wa-VeriTrace-project.git"
pip install -e .
pytest
```

## Quickstart

```python
from secondopinion import SecondOpinion, FunctionResponder

# Offline: canned answers, no API keys (this is what the tests and demo use)
so = SecondOpinion([
    FunctionResponder("Claude",   lambda q: "Delaware is the standard choice for startups. The franchise tax is about 450 dollars."),
    FunctionResponder("Gemini",   lambda q: "Delaware is the standard choice for startups. The franchise tax is around 175 dollars plus fees."),
    FunctionResponder("DeepSeek", lambda q: "Delaware is the standard choice for startups. Wyoming runs a 2500 dollar startup grant."),
])

so.add_source(
    "Delaware is the standard choice for venture-backed startups. "
    "The Delaware franchise tax minimum is 400 dollars per year plus a 50 dollar report fee.",
    id="cheat", name="Incorporation cheat-sheet", date="2025-01-01",
)

verdict = so.ask("Should we incorporate in Delaware or Wyoming?")
print(verdict.summary())              # 3 models -> 1 agreed, 3 contested, 0 unbackable
for c in verdict.agreed:     print("AGREED    ", c.tier, c.text)
for c in verdict.contested:  print("CONTESTED ", c.tier, c.text)
for c in verdict.unbackable: print("UNBACKABLE", c.tier, c.text)
```

For real models, swap in OpenRouter (one key, every provider):

```python
import os
from secondopinion import SecondOpinion, OpenRouterResponder
os.environ["OPENROUTER_API_KEY"] = "sk-or-..."

so = SecondOpinion([
    OpenRouterResponder("anthropic/claude-sonnet-4.5"),
    OpenRouterResponder("google/gemini-2.5-pro"),
    OpenRouterResponder("deepseek/deepseek-chat"),
])
so.add_source(open("my_document.txt").read(), id="doc", name="My document", date="2025-01-01")
print(so.ask("...").summary())
```

Run the example: `python examples/quickstart.py`

## How it works

```
question -> ask each model independently
         -> split every answer into claims (VeriTrace segmentation)
         -> cluster claims across models by content overlap
         -> ground each claim against your sources (VeriTrace)
         -> bucket it:
              LOW grounding              -> UNBACKABLE   (overrides — nobody can back it)
              shared by a majority + grounded -> AGREED
              otherwise                  -> CONTESTED    (the models diverge)
```

The grounding step is the real arbiter. A claim every model repeats still has to be backed by a source; if it can't be, it is flagged unknown, never asserted.

## The three buckets

| Bucket         | Meaning                                                        |
| -------------- | ------------------------------------------------------------- |
| `AGREED`       | Most/all models say it **and** a source can back it           |
| `CONTESTED`    | The models diverge — no single one is trustworthy yet         |
| `UNBACKABLE`   | No source supports it — flagged as unknown, never asserted    |

## Repo layout

```
secondopinion/  the Python library (the actual product)
tests/          test suite (runs against the real VeriTrace engine, offline)
examples/       runnable quickstart
web/            the browser demo (index.html) — deployed to Cloudflare Pages
```

## Live demo deployment (Cloudflare Pages)

The demo is a single static file with no build step. When connecting this repo in Cloudflare Pages:

- **Framework preset:** None
- **Build command:** *(leave empty)*
- **Build output directory:** `web`

Every push then auto-deploys the updated demo.

## Honest limitations

This is a V1, and the genuinely hard parts are deferred — not hidden.

- **Agreement is lexical, not semantic.** Models clustered as "agreeing" are matched on wording overlap, not deep meaning. Paraphrased agreement can be missed and split into `CONTESTED`.
- **Inherited from VeriTrace's lexical backend:** a fabrication that reuses real entities from your sources scores `MEDIUM`, not `LOW`. So it lands in `CONTESTED` (not certified) rather than `UNBACKABLE` (fully rejected). This is tested on purpose (`test_known_limitation_entity_reuse_grounds_medium_not_low`). A semantic/NLI backend is the fix.
- **Claim segmentation is sentence-level.**
- **It is only as good as the sources you ground against.** Models sharing a training blind spot can all be wrong; the source is the check.

## Roadmap

- [ ] Semantic / NLI grounding backend (the big quality unlock — also VeriTrace's roadmap)
- [ ] Detect direct contradictions on the same topic, not just divergence
- [ ] Parallel model calls
- [ ] Bring-your-own-source upload in the web demo
- [ ] Persist and share a verdict

## License & attribution

MIT — free to use, copy, modify, and redistribute. Per the MIT terms, the copyright and author notice must travel with the code.

Created by **Wael Alebrahim** — [website](https://waelalebrahim.com/) | [X](https://x.com/walebrahim_X) | [LinkedIn](https://www.linkedin.com/in/waelalebrahim) | [GitHub](https://github.com/waelalebrahim)

Use it, fork it, make it better. Best of luck.
