# Visual Thinking Techniques in VLMs

A synthesis of how Vision-Language Models can reason about visual content, covering all major paradigms, their trade-offs, and the current state of the art.

**Sources**: [[concepts/visual-reasoning-in-vlms]], [[concepts/chain-of-visual-thought]], [[concepts/continuous-visual-tokens]], [[sources/covt-chain-of-visual-thought]], [[sources/icot-interleaved-modal-chain-of-thought]], [[sources/why-spatial-reasoning-hard-vlms]], [[sources/mirage-machine-mental-imagery]], [[sources/lmrm-survey]], [[sources/modal-mixed-cot-latent-embeddings]], [[sources/pearl-predictive-embedding-alignment]], [[sources/valr-vision-aligned-latent-reasoning]], [[sources/lacot-latent-chain-of-thought]]

---

## The Core Tension

VLMs project visual input into a language-centric token space to leverage LLM reasoning capabilities. This works well for semantic and logical tasks but creates a fundamental **lossy bottleneck** for perception-intensive tasks: continuous visual signals (depth, edges, geometry, spatial layout) are poorly representable as discrete text tokens.

**Mechanistic root cause** (ICML 2025): image tokens are ~90% of input but receive only ~10% of attention — language priors dominate. The geometric *distribution* of attention matters more than the total amount: whether the model attends to the right spatial locations predicts correctness (AUROC peaks in middle layers 14–18). Two failure modes: insufficient attention to relevant objects, and misplaced attention on irrelevant regions. See [[concepts/visual-attention-in-vlms]] and [[sources/why-spatial-reasoning-hard-vlms]].

---

## Paradigm Comparison

| Paradigm | Example Systems | Key Advantage | Key Weakness |
|---|---|---|---|
| Text-only CoT | Qwen3-VL-Thinking, DeepSeek-R1 | Strong for math/logic; no extra components | Degrades vision tasks; continuous spatial info lost in verbalization |
| Tool-augmented | ViperGPT, Visual ChatGPT, ToolVQA | Restores spatial/geometric detail | Not differentiable; GPU overhead; ceiling bounded by tools |
| Image gen/crop in chain | MCoT | Rich visual mid-chain | High compute; images re-projected to text space, losing density |
| Image interleaving | VChain | Full image in chain | Same projection bottleneck at reasoning step |
| Discrete latent | Aurora | Better than text; compact | Quantization loses continuous info; no edge/semantic tokens |
| **Continuous visual tokens** | **CoVT** | End-to-end differentiable; no external tools; best on perception | Design space not fully explored; studied mostly at 7–13B scale |
| **Attention-driven patch interleaving** | **ICoT** | No training required; truly interleaved; grounded in real pixels | Uses input subregions (not novel signal); memory overhead; patch count fixed |
| **Inference-time attention reshaping** | **AdaptVis** | Training-free; up to +50 pts on controlled spatial tasks; no new tokens | Requires validation tuning per dataset; minimal gain on general QA; can't fix encoder errors |
| **Self-generated hidden-state latents** | **Mirage** | No external experts; addresses collapse via Stage 1 grounding; GRPO refinement | Depends on synthesized helper image quality; task scope limited so far |
| **Diffusion-decoded latent embeddings** | **Modal-Mixed CoT** | Compact 32-token visual sketches; end-to-end with GRPO; generalizes across model families | Bypass status untested; RL degrades abstract logic tasks |
| **JEPA-style trajectory distillation** | **PEARL** | Structurally bypass-immune (no latent tokens at inference); internalizes expert tool-use into weights | Dual-forward-pass training overhead; evaluated on fewer benchmarks than other approaches |
| **Per-step visual checkpointing** | **VaLR** | Only approach enabling test-time scaling; 52.9% VSI-Bench (vs. CoVT 18.6%); REPA alignment causally necessary | K=16 tokens per reasoning step increases inference cost |

---

## Deep Dive: The Winning Approach — CoVT

[Chain-of-Visual-Thought (CoVT)](../concepts/chain-of-visual-thought.md) replaces text-only thinking with a mixed reasoning chain:

```
Standard: <think> [text tokens only] </think> → <answer>
CoVT:     <think> [text tokens] + [visual tokens: seg, depth, edge, dino] </think> → <answer>
```

### The Four Continuous Token Types

See [[concepts/continuous-visual-tokens]] for full alignment details.

| Token | Expert | Count | Perceptual Capability |
|---|---|---|---|
| Segmentation | SAM (ViT-H) | ×8 | Instance localization, 2D spatial layout |
| Depth | DepthAnything v2 (ViT-L) | ×4 | 3D spatial relationships |
| Edge | PIDINet | ×4 | Structure, fine boundaries |
| DINO | DINOv2 (ViT-L) | ×4 | Patch-level semantic representation |

**~20 tokens total** — deliberately compact to compress key perceptual signals without dominating context.

### Why It Outperforms

- Keeps visual information in **continuous space** throughout reasoning — no quantization loss
- Visual tokens are generated **autoregressively** alongside text; trained end-to-end
- At inference: tokens live as latent vectors only; decoding to masks/maps is optional (interpretability only)
- Results: +5.5% on CV-Bench, +14% on its depth subtask, +4.5% on HRBench8K over Qwen2.5-VL-7B base

### Why Text-Only CoT Fails for Vision

Projecting continuous spatial/geometric information into discrete language tokens is lossy, and errors accumulate in long chains. Empirical evidence: Qwen3-VL-Thinking (text CoT) is 5%+ **worse** than Qwen3-VL-Instruct (no CoT) on spatial benchmarks (HRBench8K, VSI-Bench, V*Bench).

---

## Open Problems

1. **Interleaved multimodal reasoning** — partially solved by ICoT (CVPR 2025): attention-driven patch re-injection at each reasoning step, no training required, +11.7% on LLaVA-W. Open gap: combining ICoT's dynamic interleaving with CoVT's non-redundant expert tokens. See [[sources/icot-interleaved-modal-chain-of-thought]].
2. **Design space of token types** — only 4 expert combinations explored; hybrid or domain-specific experts may yield gains
3. **Frontier scale** — most work done at 7–13B; behavior at larger scales is unclear
4. **Commonsense + perception** — tasks requiring both simultaneously remain challenging

---

## Where These Paradigms Sit in the LMRM Roadmap

The [[sources/lmrm-survey]] (540+ papers) provides a four-stage framework that historically contextualises all the above. Every paradigm in the table maps to Stage 2 or Stage 3:

| Paradigm | LMRM Stage |
|---|---|
| Text-only CoT | Stage 2–3 |
| Tool-augmented | Stage 2 (external augmentation) |
| Image gen/crop in chain | Stage 2–3 boundary |
| Image interleaving (VChain) | Stage 2–3 boundary |
| Discrete latent (Aurora) | Stage 3 (early) |
| Continuous visual tokens (CoVT) | Stage 3 |
| Attention patch interleaving (ICoT) | Stage 3 (cross-modal) |
| Inference-time attention reshaping (AdaptVis) | Stage 2–3 boundary |
| Self-generated hidden-state latents (Mirage) | Stage 3 → Stage 4 |
| Diffusion-decoded latent embeddings (Modal-Mixed CoT) | Stage 3 (self-generated latent) |
| JEPA-style trajectory distillation (PEARL) | Stage 3 training / Stage 2 inference |
| Per-step visual checkpointing (VaLR) | Stage 3 → Stage 4 boundary |
| GFlowNet CoT training (LaCoT) | Stage 3 (System-2 text CoT — not a visual paradigm) |

The prospective **Stage 4 (N-LMRMs)** — unified multimodal representation spaces, agentic long-horizon planning, omni-modal understanding — is where none of the current approaches fully land yet. Mirage is the closest. See [[concepts/lmrm-roadmap]].

---

## Key Takeaway

For perception-heavy visual tasks (depth, counting, spatial layout, fine boundaries), the path is: **don't verbalize visual observations — keep them in latent space**. Text CoT is sufficient for semantic/logical vision tasks but harmful for geometric ones. The frontier is now per-step visual grounding: VaLR (52.9% VSI-Bench) substantially outperforms single-step approaches like CoVT (18.6%) on multi-view spatial tasks — and is the only approach where longer reasoning chains monotonically improve performance. For bypass immunity, PEARL demonstrates a fundamentally different path: internalize expert trajectories into weights during training so no latent tokens are needed at inference. CoVT remains the most studied baseline, but the design space has expanded significantly.

> **Note (updated 2026-05-22):** [What's Holding Back Latent Visual Reasoning?](../sources/whats-holding-back-latent-visual-reasoning.md) complicates the "keep it in latent space" takeaway: in 4 tested models, latent tokens are bypassed at inference and show representation collapse. The critical variable is whether training data provides **genuinely non-redundant** visual intermediates. Expert-aligned tokens (as in CoVT) may satisfy this; crop-based intermediates do not. The field's next challenge is not just what tokens to use, but ensuring models actually learn to depend on them.
