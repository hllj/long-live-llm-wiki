# CoVT: Limitations and Research Directions

A synthesis of the current limitations of vision language reasoning with Chain-of-Visual-Thought, and the open research directions they suggest.

**Sources**: [[concepts/chain-of-visual-thought]], [[concepts/visual-reasoning-in-vlms]], [[concepts/continuous-visual-tokens]], [[sources/covt-chain-of-visual-thought]], [[analyses/visual-thinking-techniques]], [[sources/whats-holding-back-latent-visual-reasoning]], [[sources/icot-interleaved-modal-chain-of-thought]], [[sources/why-spatial-reasoning-hard-vlms]], [[sources/mirage-machine-mental-imagery]]

---

## Limitation 0: The Latent Bypass Problem — Do Visual Tokens Actually Work?

> **New finding (2026-05-22):** [What's Holding Back Latent Visual Reasoning?](../sources/whats-holding-back-latent-visual-reasoning.md) (arXiv 2605.18445)

This is the most structurally important challenge to the entire paradigm. Across 4 latent visual reasoning models (LVR, Monet, ILVR, LanteRn) tested on BLINK and V*Bench, replacing generated latent tokens with uninformative dummy tokens (zeros, noise, random subregions) **left accuracy unchanged**. Even providing ground-truth oracle latents at inference produced minimal improvement.

Two compounding failures:
- **Latent bypass**: Models route around latent tokens in their final prediction — the tokens exist in the reasoning chain but are ignored.
- **Latent representation collapse**: Predicted latents cluster tightly (cosine similarity 0.8–0.98 to each other) while diverging from oracle representations (3.3% top-1 retrieval accuracy). The model generates essentially the same latent regardless of the input.

**Root cause**: These models were trained on datasets using subregion crops as intermediate images — information already present in the input. No incentive to use latents.

**When latents do work**: On masked-input training (where the latent is the only source of occluded information) and on a synthetic Tetris rotation task, oracle latents achieved 86% vs. 33% for dummy tokens — proving the mechanism can work when training data demands it.

**CoVT scope caveat**: The 4 tested models all use image-crop-based intermediates. CoVT's expert-aligned tokens (SAM, DepthAnything, DINOv2) provide genuinely non-redundant signals and were *not directly tested*. CoVT's +14% depth gains may reflect this difference — or may reflect better training supervision rather than causal token use. The bypass intervention on CoVT is an important open experiment.

**Bypass-immune alternative**: [[sources/pearl-predictive-embedding-alignment]] (U. Edinburgh, Apr 2026) takes a structurally different approach — **no latent tokens at inference at all**. PEARL's JEPA-style training internalizes what expert tool-use trajectories would produce into model weights, so the model reasons with standard token generation at test time. It independently corroborates the bypass finding (avg r=−0.12 between latent count and performance across reconstruction-based baselines) and achieves +31pp V*, +38pp MMVP over SFT on ThinkMorph multi-tool tasks. The bypass problem may be avoidable by design, not just by better training data.

> **New finding (2026-05-23, [[sources/valr-vision-aligned-latent-reasoning]]):** VaLR directly benchmarks CoVT on VSI-Bench (multi-view video spatial): **CoVT scores 18.6%** (vs. VaLR-M 52.9%, base Qwen2.5-VL 33.0%). Single-step latent injection cannot maintain visual grounding across extended multi-view reasoning — CoVT performs *below the base model* on this benchmark. This is the sharpest empirical evidence that static latent injection is insufficient for long-context visual tasks.

---

## The Root Problem (All Approaches)

Every VLM paradigm hits the same fundamental bottleneck: visual input must ultimately be projected into a token space designed for language. Continuous spatial signals — depth gradients, boundary geometry, 3D relationships — are poorly representable as discrete tokens.

The sharpest empirical evidence: **Qwen3-VL-Thinking (text CoT) is 5%+ worse than Qwen3-VL-Instruct (no CoT) on spatial benchmarks** (HRBench8K, VSI-Bench, V*Bench). Forcing verbalization of visual observations actively causes error accumulation.

**Mechanistic explanation** (ICML 2025, [[sources/why-spatial-reasoning-hard-vlms]]): image tokens are ~90% of input but receive only ~10% of attention. Language priors dominate. Spatial reasoning success correlates with *whether* attention lands on the right image regions (AUROC peak in middle layers 14–18), not with the total amount of image attention. CoVT's expert tokens address this by injecting signals the model was underweighting; AdaptVis addresses it directly by confidence-guided attention reshaping (up to +50 pts on controlled spatial benchmarks, training-free). See [[concepts/visual-attention-in-vlms]].

---

## Paradigm Landscape: Core Limitations

| Approach | Core Limitation |
|---|---|
| Text-only CoT | Lossy verbalization; degrades spatial tasks empirically |
| Tool-augmented (ViperGPT, etc.) | Not differentiable; GPU overhead; hard ceiling at tool capability |
| Image gen in chain (MCoT) | High compute; images re-projected to text space, losing density |
| Image interleaving (VChain) | Still hits the projection bottleneck at reasoning steps |
| Discrete latents (Aurora) | Quantization discards continuous info; no edge/semantic tokens |
| **CoVT** | Design space unexplored; no interleaving; scale unknown; commonsense gap |

---

## CoVT-Specific Limitations (Current SOTA)

### 1. No True Interleaved Reasoning

CoVT's visual thoughts are a single block: `<think> [text] → [visual tokens] → [more text] </think>`. Visual and text thoughts are **not alternated mid-chain**. The model can't do iterative visual reasoning — look, think, look again with updated attention, reason more. It's one perceptual check-in followed by text continuation.

> **Partially addressed (2026-05-22):** [ICoT — Interleaved-Modal Chain-of-Thought](../sources/icot-interleaved-modal-chain-of-thought.md) (CVPR 2025) solves this via **Attention-driven Selection (ADS)**: at each newline in the reasoning chain, the top-64 image patches by attention score are re-injected into context. No training required. Gains up to +11.7% on LLaVA-W (long-form visual QA), +6.4% on ScienceQA. Key trade-off: ICoT uses subregion patches from the original image (not novel perceptual transformations like CoVT's expert tokens), so the bypass concern from [[sources/whats-holding-back-latent-visual-reasoning]] applies differently — ICoT injects actual pixel tokens into context, which the model can directly attend to, rather than learned latent representations the model may ignore.

### 2. Narrow Design Space of Token Types

Only 4 expert cue types were explored: segmentation (SAM), depth (DepthAnything v2), edge (PIDINet), and semantic patches (DINOv2). These were chosen by intuition, not ablation against a wide grid. The optimal combination for different task domains (medical imaging, remote sensing, video, 3D scenes) is unknown. Hybrid experts, motion tokens, texture tokens, or material tokens may yield gains.

### 3. Scale Untested

All CoVT results are at **7B–13B parameter scale**. Behavior at 70B+ (frontier models) is completely unknown. Larger models may need fewer visual tokens, more, or different types entirely.

### 4. Commonsense + Perception Gap

Tasks requiring both geometric perception *and* commonsense reasoning remain challenging. Perceptual tokens help with geometry but don't bridge to world-knowledge grounded reasoning (e.g., "which chair would be hard to sit in given the person's height?").

### 5. Fixed Token Budget, Static Allocation

Token counts per type are fixed (~20 total: 8 seg, 4 depth, 4 edge, 4 DINO). Stage 4 dropout training teaches *type* selection, but not dynamic *count* allocation. Ablations show 1 token = significant drop; 32 tokens = worse + 220% overhead — so budget matters, but optimal allocation is not adaptive to the query.

---

## Research Directions

### 1. Fully Interleaved Multimodal Reasoning Chains

Enable the model to generate visual tokens *multiple times* within one think chain, with text tokens between each visual block. Requires training on examples where perceptual re-inspection actually changes the answer — likely synthetic reasoning traces with explicit iterative inspection steps.

**Existing solutions**: ICoT (CVPR 2025) achieves this training-free via attention-driven patch re-injection (+11.7% LLaVA-W). Mirage (CVPR 2026) achieves it via self-generated hidden-state latent tokens with two-stage distillation+GRPO (89% VSP spatial reasoning). **Open gap**: combining ICoT's dynamic scheduling with CoVT's expert-aligned tokens, or composing Mirage's grounding approach with CoVT's expert signal. See [[sources/icot-interleaved-modal-chain-of-thought]], [[sources/mirage-machine-mental-imagery]].

### 2. Adaptive Visual Token Budget

Learn a *dynamic allocation* per query: how many segmentation vs. depth tokens to generate, based on what the question requires. Could be framed as a lightweight routing policy (small MLP deciding budget given question embedding + image features) extending Stage 4 dropout from type selection to count selection.

### 3. Domain-Specific and Hybrid Visual Expert Tokens

Current experts cover general photographic scenes. Domain-specific signals likely matter: optical flow / temporal motion (video), material/texture (product reasoning), keypoints (pose/action), anomaly maps (medical/industrial). Systematically benchmark which expert combos matter per task domain, then train domain-specialized CoVT variants.

### 4. Temporal CoVT for Video Reasoning

CoVT is evaluated only on static images. Extending continuous visual token reasoning to video — generating optical flow tokens, temporal depth tokens, or object-track tokens inside the think chain — is an open area. Training would require temporal reasoning traces where spatial relationships change across frames.

### 5. Scaling Laws for Visual Token Reasoning

A systematic study: does CoVT's benefit diminish, scale, or qualitatively change at 70B+? Does the optimal number of visual tokens change with model size? Do larger models adequately verbalize spatial reasoning without visual tokens? Infrastructure-heavy but would determine whether CoVT is a workaround for small models or a fundamental architectural pattern.

### 6. Self-Supervised Visual Token Learning

CoVT's visual tokens are aligned to external expert models — a hard dependency that caps quality at what those experts encode. A more ambitious direction: learn visual reasoning tokens self-supervisedly from the VLM's own prediction errors, encoding *whatever the model is currently getting wrong perceptually* rather than what SAM or DepthAnything was trained to produce. Could discover novel perceptual representations not tied to human-designed expert tasks.

**Existing approach**: Mirage (CVPR 2026) removes the external expert dependency by recasting the VLM's own hidden states as latent tokens, grounded via cosine similarity distillation from synthesized helper images. Stage 1 grounding prevents collapse; Stage 2 relaxation enables flexible self-generation; GRPO refines further. t-SNE confirms latents stay on the visual manifold. **Open gap**: fully unsupervised discovery with no helper images — tokens that emerge purely from prediction error signals. See [[sources/mirage-machine-mental-imagery]].

---

## Key Takeaway

The field has established that **text verbalization of visual observations is actively harmful for spatial tasks**, and continuous latent tokens fix the core bottleneck. CoVT is strong but narrow — 4 expert types, 7B scale, static images, no mid-chain interleaving. Three complementary approaches now exist:

- **ICoT** (CVPR 2025): training-free interleaved reasoning via attention-driven patch re-injection
- **AdaptVis** (ICML 2025): training-free attention reshaping via confidence-guided temperature scaling
- **Mirage** (CVPR 2026): self-generated hidden-state latents with two-stage grounding, avoiding collapse

The remaining open frontiers are scaling to frontier models (70B+), temporal/video reasoning, and fully unsupervised token discovery without helper images or external experts.
