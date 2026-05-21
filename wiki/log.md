# Wiki Log

_Append-only activity log. Each entry: `## [YYYY-MM-DD] <type> | <title>`_

_Types: `ingest`, `query`, `lint`_

_Grep last 10 entries: `grep "^## \[" wiki/log.md | tail -10`_

---

## [2026-04-21] init | Project scaffold created

CLAUDE.md schema written. `wiki/index.md` and `wiki/log.md` bootstrapped. Ready to ingest sources.

## [2026-05-21] ingest | CoVT: Chain-of-Visual-Thought (arXiv 2511.19418v2)

Source: `raw/2511.19418v2.pdf` — UC Berkeley paper introducing Chain-of-Visual-Thought, a framework enabling VLMs to reason via continuous visual tokens (segmentation, depth, edge, DINO) rather than text-only CoT.

Pages touched:
- `wiki/sources/covt-chain-of-visual-thought.md` — created (full summary, results, ablations)
- `wiki/concepts/chain-of-visual-thought.md` — created
- `wiki/concepts/continuous-visual-tokens.md` — created (token types, alignment strategies, projection layer)
- `wiki/concepts/visual-reasoning-in-vlms.md` — created (paradigm taxonomy, benchmark landscape)
- `wiki/entities/qwen2-5-vl.md` — created
- `wiki/index.md` — updated

## [2026-05-22] query | Visual Thinking Techniques in VLMs

Answered question about techniques for visual thinking in VLMs. Synthesized all 6 reasoning paradigms (text CoT, tool-augmented, image gen, image interleaving, discrete latent, continuous visual tokens) with trade-offs and open problems. Filed result as `wiki/analyses/visual-thinking-techniques.md`.
