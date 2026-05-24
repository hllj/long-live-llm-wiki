# Machine Mental Imagery (Mirage)

**Paper**: Machine Mental Imagery: Empower Multimodal Reasoning with Latent Visual Tokens  
**Authors**: Zeyuan Yang, Xueyang Yu, Delin Chen, Maohao Shen, Chuang Gan  
**Affiliation**: University of Massachusetts Amherst, MIT  
**arXiv**: 2506.17218 (Jun 20, 2025)  
**Venue**: CVPR 2026  
**Project**: https://vlm-mirage.github.io/  
**Code**: https://github.com/UMass-Embodied-AGI/Mirage  
**Raw**: `raw/2506.17218.pdf`  
**Date ingested**: 2026-05-22

---

## Summary

Mirage is motivated by the same problem as CoVT and ICoT — text-only decoding forces VLMs to verbalize visual reasoning, which loses perceptual fidelity — but takes a fundamentally different architectural approach: instead of aligning tokens to external expert models (CoVT) or re-injecting image patches (ICoT), Mirage **recasts the VLM's own hidden states as next tokens**, creating compact latent vectors that stay on the visual representation manifold. No pixel-level image generation, no external experts. Pure internal imagination.

The name is deliberate: humans reason with *mental imagery* — internal visual constructions not tied to any specific pixel output. Mirage operationalizes this for VLMs via a two-stage training paradigm plus GRPO reinforcement learning.

---

## Architecture: How Mirage Generates Latent Visual Tokens

### Stage 1 — Latent Grounding via Distillation
Helper images (synthesized to reflect ground-truth solutions) are compressed into **k salient vectors** via average pooling over patch features. The model is trained jointly to:
- Predict text tokens (cross-entropy loss)
- Reconstruct the helper image's latent embeddings (cosine similarity loss, weight γ)

This anchors the latent token space to the visual representation manifold. The model learns to *produce* latent vectors that encode task-relevant visual information.

### Stage 2 — Latent Relaxation with Text-Only Supervision
Explicit latent supervision is removed. The model now autoregressively generates its own latent embeddings, which serve as **flexible priors** guiding subsequent text prediction. Gradients propagate through latent tokens via the textual token prediction loss — indirect supervision.

**Both stages are required**: Stage 1 alone = 46% on VSP Spatial Planning Level 5; Stage 2 alone = 16%; both combined = 53%.

### Stage 3 — Reinforcement Learning (GRPO)
Group Relative Policy Optimization with accuracy and format rewards allows diverse multimodal sequence exploration, pushing beyond the imitation ceiling of distillation.

### Data Generation Pipeline
1. Synthesize helper images that visually represent ground-truth solutions (task-specific)
2. Prompt a large reasoning VLM (Qwen2.5-VL 32B) with input + answer + helper image → step-by-step reasoning trace
3. Split traces into pre-image and post-image segments for two-stage supervision

### Hyperparameters
- **k = 6** latent tokens optimal (k=2: 86%, k=4: 87%, k=6: 88%, k=8: 75% — error accumulation at high k)
- **γ = 0.1** cosine loss weight optimal (γ=0.5: 84%, γ=1.0: 83%)
- Base model: Qwen2.5-VL 7B; hardware: single H100 GPU

---

## Results

### VSP (Visual-Spatial Planning) Benchmarks

| Task | Method | Accuracy |
|---|---|---|
| Spatial Reasoning | Direct SFT | 83% |
| Spatial Reasoning | CoT SFT + GRPO (baseline) | 85% |
| Spatial Reasoning | Mirage (CoT + GRPO) | **89%** |
| Spatial Planning | CoT SFT + GRPO (baseline) | 51% |
| Spatial Planning | Mirage (Direct) | 76% |
| Spatial Planning | Mirage (CoT + GRPO) | **60%** |

### vs. Unified Model Baselines (Spatial Reasoning)

| Model | Accuracy |
|---|---|
| Anole | 52% |
| MVoT | 61% |
| **Mirage (Direct)** | **86%** |

### Multi-Task (Table 2)

| Benchmark | Mirage Score |
|---|---|
| COMT | 0.77 |
| Jigsaw | 0.88 |
| SAT Synthetic | 0.98 |
| SAT Real | 0.72 |

### Smaller Model Generalization (Qwen2.5-VL 3B)
- Jigsaw: +5% over text-only baseline
- SAT Real: +10% over text-only baseline

---

## Key Insight: Addressing Latent Representation Collapse

The bypass paper ([[sources/whats-holding-back-latent-visual-reasoning]]) found that existing latent reasoning models generate tokens that collapse to a narrow cluster (0.8–0.98 mutual cosine similarity) while diverging from oracle representations. Mirage's **Stage 1 grounding** directly targets this:

- t-SNE visualization shows Mirage's latent embeddings **cluster near the visual representation subspace** — separated from pure text embeddings
- After Stage 2 (no explicit supervision), latents still remain anchored — indirect gradient propagation preserves the visual manifold alignment
- This is architectural evidence that Mirage avoids the collapse problem via explicit grounding before relaxation

The bypass paper's key insight was: models trained on uninformative crop-based intermediates learn to ignore latents because attending to them has no marginal value. Mirage sidesteps this by (a) using synthesized helper images that reflect actual ground-truth solutions (genuinely informative), and (b) Stage 1 supervision that forces latent grounding before the model learns to bypass.

---

## Architectural Comparison

| Dimension | CoVT | ICoT | Mirage |
|---|---|---|---|
| Visual source | External expert models (SAM, DepthAnything, etc.) | Original input image patches | VLM's own hidden states |
| Token type | Continuous expert-aligned vectors | Discrete image patches | Continuous self-generated latent vectors |
| Interleaving | Single visual block mid-chain | Multiple patch insertions (attention-driven) | Multiple latent blocks (per reasoning step) |
| Training | End-to-end LoRA (4 stages) | None (plug-and-play) | Two-stage distillation + GRPO |
| External dependency | Expert model library required | None | Synthesized helper image pipeline |
| Pixel generation | No | No (patches from input) | No |
| Bypass risk | Lower (non-redundant expert signal) | Different (pixel tokens, not latents) | Lower (Stage 1 grounding prevents collapse) |
| Best benchmark | CV-Bench depth (+14%) | LLaVA-W (+11.7%) | VSP Spatial Reasoning (89%) |

---

## Limitations

1. **Synthetic data quality**: Performance depends on helper image synthesis quality; careful curation is needed per task
2. **Unified model integration**: Framework focused on reasoning models; extending to unified image-text generation (Anole-style) is open
3. **Task scope**: Evaluated primarily on spatial reasoning benchmarks; generalization to other vision tasks unclear
4. **Scale**: Tested at 7B and 3B; frontier-scale behavior unknown

---

## Related Pages

- [[concepts/visual-reasoning-in-vlms]] — Mirage adds a new paradigm: self-generated hidden-state latent tokens
- [[concepts/continuous-visual-tokens]] — contrast: CoVT aligns to external experts; Mirage grounds to own visual manifold
- [[sources/whats-holding-back-latent-visual-reasoning]] — Mirage's two-stage training addresses both bypass and collapse problems
- [[analyses/covt-limitations-and-research-directions]] — Limitation 1 (no interleaving) and Limitation 6 (self-supervised tokens) addressed
- [[entities/qwen2-5-vl]] — Qwen2.5-VL 7B is Mirage's base model
- [[concepts/visual-attention-in-vlms]] — Mirage's Stage 1 grounding ensures latents stay on the visual manifold so the model attends to them; directly addresses the bypass failure mode
