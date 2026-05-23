# PEARL: Multimodal Latent Reasoning via Predictive Embeddings

**Paper**: Multimodal Latent Reasoning via Predictive Embeddings  
**Authors**: Ashutosh Adhikari, Mirella Lapata  
**Affiliation**: School of Informatics, University of Edinburgh  
**arXiv**: 2604.08065v1 (April 9, 2026)  

**Sources**: [[concepts/visual-reasoning-in-vlms]], [[concepts/continuous-visual-tokens]], [[sources/whats-holding-back-latent-visual-reasoning]], [[sources/mirage-machine-mental-imagery]]

---

## Core Contribution

**PEARL** (Predictive Embedding Alignment for Reasoning in Latent space) takes a fundamentally different approach to latent visual reasoning: **no latent tokens exist at inference**. Instead of training the VLM to autoregressively generate latent tokens during reasoning, PEARL uses a JEPA-inspired (Joint Embedding Predictive Architecture) objective to internalize what expert tool-use trajectories would produce — then uses standard VLM decoding at inference with zero tools, zero latent tokens, and zero training-inference mismatch.

**The key insight**: expert tool trajectories tell the model *what to attend to and how* — this knowledge can be baked into model weights during training without needing the tool or explicit latent representations at test time.

---

## Architecture

- **Trajectory encoding**: the VLM's own hidden states encode the expert reasoning trajectory (tool calls + visual outputs)
- **Predictor**: K=4 learnable `[PRED]` tokens; lightweight cross-attention head maps from input → trajectory embedding space
- **Inference**: standard VLM decoding — no tools, no latent tokens, no extra compute

**Three training objectives** (combined loss: ℒ_PEARL = ℒ_VLM + λ(ℒ_JEPA + ℒ_NextLat), λ=0.2):

| Loss | Purpose |
|---|---|
| ℒ_VLM | Standard autoregressive next-token prediction on reasoning steps |
| ℒ_JEPA | SmoothL1 alignment of predicted embedding to stop-gradient trajectory encoding |
| ℒ_NextLat | Next-latent prediction regularizer — encourages hidden states to act as belief states |

**LoRA adapter only** (rank=64, α=128) — full fine-tuning not needed.

---

## Relationship to the Bypass Problem

PEARL sidesteps the bypass problem entirely: **there are no latent tokens at inference to bypass**. The approach is structurally immune to the latent bypass failure mode documented by [[sources/whats-holding-back-latent-visual-reasoning]].

**PEARL also provides independent empirical corroboration of the bypass finding** (Figure 3 correlation analysis across reconstruction-based baselines):
- BLINK: r = −0.35, R² = 0.12
- V*: r = 0.72, R² = 0.51
- MMVP: r = −0.56, R² = 0.32
- **Average across benchmarks**: r = −0.12, R² = 0.02

Near-zero average correlation confirms that latent token count does not predict performance in reconstruction-based methods — consistent with the bypass paper's finding that tokens are ignored. Additionally, >75% of LVR training examples contain >8 latent tokens, but inference uses only 4–8 → training-inference mismatch is structural.

---

## Results

**Base model**: Qwen2.5-VL-7B-Instruct across all settings.

### Single-type, single tool call (LVR data, 450K+ samples)
| Benchmark | SFT | LVR | PEARL |
|---|---|---|---|
| V* | 79.1 | 80.1 | **81.5** |
| MMVP | 65.7 | 72.0 | **73.5** |
| Spatial Relation | — | 89.5 | 89.5 |
| Jigsaw | — | 51.3 | **53.1** |

### Multiple-type, single tool call (ThinkMorph, 24K samples, 4 tool types)
| Benchmark | SFT | PEARL |
|---|---|---|
| V* | 42.4 | **73.8** (+31pp) |
| MMVP | 36.7 | **75.3** (+38pp) |
| Spatial Relation | 60.1 | **88.8** (+29pp) |

### Single-type, multiple tool calls (PixelReasoner, ~4K samples)
| Benchmark | PixelReasoner | PEARL |
|---|---|---|
| MMVP | 67.0 | **70.0** |
| Counting | 66.7 | **70.0** |
| Spatial Relation | 88.1 | **89.5** |

### Cross-model generalization
| Model | Benchmark | Baseline | PEARL |
|---|---|---|---|
| Qwen2.5-VL-3B | V* | 64.9 | **73.8** |
| Qwen2.5-VL-3B | MMVP | 54.7 | **68.7** |
| Qwen3-VL-4B | V* | 81.2 | **81.7** |
| Qwen3-VL-4B | MMVP | 75.7 | **80.0** |

**Largest gains on ThinkMorph's diverse multi-tool setting**: +31–38pp suggest trajectory-level embeddings are tool-type agnostic — PEARL generalizes across heterogeneous tool types without needing all of them at inference.

---

## Ablations

**Without ℒ_NextLat** (belief-state regularizer):
- V*: 80.1 vs 81.5 (−1.4pp)
- MMVP: 69.3 vs 73.5 (−4.2pp)
- VDA: 83.5 vs 86.1 (−2.6pp)

Consistent degradation across tasks confirms belief-state regularization improves trajectory embedding quality — the model needs to learn to maintain an implicit "what would tools show me" belief state through the chain.

---

## Key Findings

1. **No bypass possible**: no latent tokens at inference → structurally avoids the core failure mode of reconstruction-based methods
2. **Training-inference alignment**: PEARL's inference matches its training setup exactly; reconstruction methods have structural mismatch (train on 8+ latents, infer with 4–8)
3. **Tool heterogeneity robustness**: ThinkMorph +31–38pp shows PEARL can internalize multi-type tool effects better than SFT
4. **Multi-step capability**: naturally handles sequential tool calls (PixelReasoner data) without special architecture changes
5. **LoRA sufficiency**: rank=64 LoRA outperforms full fine-tuning baselines

---

## LMRM Positioning

Sits at a unique position: **Stage 3 training → Stage 2 inference behavior**. PEARL uses tool-augmented expert trajectories (Stage 2 tool-augmented) as supervision during training, but internalizes this into model weights so inference is clean single-pass VLM decoding. The approach is a form of *knowledge distillation from tool trajectories into VLM parameters*.

---

## Limitations

- No explicit planning over learned embeddings at inference
- Trajectory representations lack interpretability (continuous, not human-readable)
- Dependent on availability of expert trajectory datasets (LVR, ThinkMorph, PixelReasoner)
- Doubled training compute from dual forward passes
- ThinkMorph gains sensitive to model capacity in smaller variants

---

## Related Pages

- [[sources/whats-holding-back-latent-visual-reasoning]] — PEARL provides independent empirical corroboration; solves bypass by eliminating latent tokens at inference
- [[sources/mirage-machine-mental-imagery]] — contrast: Mirage keeps latent tokens at inference (with Stage 1 grounding to avoid collapse); PEARL eliminates them entirely
- [[sources/modal-mixed-cot-latent-embeddings]] — contrast: Modal-Mixed CoT also generates latents at inference via diffusion decoder; PEARL avoids this entirely
- [[sources/covt-chain-of-visual-thought]] — contrast: CoVT generates expert-aligned tokens at inference; PEARL internalizes equivalent knowledge
- [[concepts/continuous-visual-tokens]] — PEARL is a fundamentally alternative design: zero latent tokens at inference
- [[concepts/visual-reasoning-in-vlms]] — new paradigm: JEPA-style trajectory prediction
- [[analyses/vlm-reasoning-training-findings]] — PEARL as training approach; corroboration of bypass finding
- [[entities/v-star-bench]] — cross-paper V*Bench leaderboard; PEARL achieves 81.5% (single-type) and +31pp via ThinkMorph
