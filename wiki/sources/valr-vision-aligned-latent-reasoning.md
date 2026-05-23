# VaLR: Vision-aligned Latent Reasoning for MLLMs

**Paper**: Vision-aligned Latent Reasoning for Multi-modal Large Language Model  
**Authors**: Byungwoo Jeon, Yoonwoo Jeong, Hyunseok Lee, Minsu Cho, Jinwoo Shin  
**Affiliation**: POSTECH (implied by author affiliations)  
**arXiv**: 2602.04476v2 (published May 12, 2026)  

**Sources**: [[concepts/visual-reasoning-in-vlms]], [[concepts/continuous-visual-tokens]], [[sources/whats-holding-back-latent-visual-reasoning]], [[sources/mirage-machine-mental-imagery]], [[sources/covt-chain-of-visual-thought]]

---

## Core Contribution

**VaLR** (Vision-aligned Latent Reasoning) addresses a failure mode not previously documented: existing latent reasoning models (CoVT, Monet, LVR) **collapse on multi-view tasks** requiring sustained visual memory across extended reasoning chains. The solution: inject K=16 latent tokens **before each CoT reasoning step** — acting as "visual checkpoints" that re-ground the model to visual representations at each deliberative step.

Unlike other approaches that generate latent tokens once (CoVT, Mirage) or not at all at inference (PEARL), VaLR continuously refreshes visual grounding throughout the chain. This is the **only approach in the wiki that enables test-time scaling for visual reasoning** — longer chains improve performance rather than degrade it.

---

## Problem: Multi-view Visual Memory Collapse

Prior latent reasoning models fail catastrophically on VSI-Bench (multi-view video spatial intelligence), a benchmark requiring extended visual reasoning across multiple views:

| Model | VSI-Bench |
|---|---|
| CoVT | 18.6% |
| Monet | 14.0% |
| LVR | 18.4% |
| GPT-4o | 34.0% |
| Qwen2.5-VL (base) | 33.0% |
| **VaLR-S (single encoder)** | **41.5%** |
| **VaLR-M (multi-encoder)** | **52.9%** |

**Root cause**: static single-injection latent approaches cannot maintain visual grounding as sequence length grows. VaLR-M exceeds GPT-4o by **18.9pp** on this benchmark.

---

## Architecture

### REPA (Representation Alignment)
Extracts patch-wise features from pre-trained vision encoders and trains the MLLM to align its latent token representations to them via patch-wise cosine similarity loss. Unlike CoVT's external expert models (SAM, DepthAnything) that produce non-redundant *transformations*, VaLR aligns to the *feature space* of existing encoders — no new expert at inference.

**Encoder options**:
- **DINOv3**: fine-grained appearance and spatial relationships (strongest single encoder)
- **CLIP / SigLIPv2**: semantic understanding
- **π³**: 3D spatial structure

**Multi-encoder (VaLR-M)**: all three used simultaneously; complementary signals produce the best results (52.9% VSI-Bench vs 41.5-52.4% for any single encoder).

### Latent token injection
Before each reasoning step boundary (`<latent>` / `</latent>` control tokens), the model generates K latent tokens using previous hidden states. Default K=16; performance plateaus at K=16–25; K=1 severely degrades (33.9% VSI-Bench).

**Optimal alignment layer**: middle transformer layers (12th of 27) — same layer range where attention-correctness correlation peaks per [[sources/why-spatial-reasoning-hard-vlms]].

---

## Training

**Stage 1 (SFT baseline)**:
- 450K CoT samples: Zebra-CoT, CogCoM, ReFocus, Visual-CoT, OneThinker-SFT, GCoT (125K interleaved + 325K non-interleaved)
- Standard language modeling loss; native vision encoder frozen
- LR: 1e-5; batch: 2/GPU; AdamW with 16-step gradient accumulation

**Stage 2 (VaLR fine-tuning)**:
- Injects K latent tokens before each reasoning step + REPA alignment
- Loss: ℒ = ℒ_CE + λ · ℒ_REPA, λ=0.5 optimal (λ=1.0 degrades to 40.0%)
- LR: 2e-6 (model), 1e-5 (MLP projection); warm-up 3%
- **>20× faster convergence** on V* vs vanilla SFT

---

## Results

### Long-context spatial (VSI-Bench)
See table above; VaLR-M at 52.9% is the highest result in the wiki for this benchmark. Key spatial sub-tasks:
| Sub-task | Base | VaLR-M |
|---|---|---|
| Absolute Distance | 14.8% | 40.6% (+25.8pp) |
| Room Size | 20.7% | 56.6% (+35.9pp) |
| Object Size | 43.4% | 64.2% (+20.8pp) |

### Perception benchmarks (Qwen2.5-VL-7B, VaLR-M)
| Benchmark | Base | VaLR-M |
|---|---|---|
| BLINK | 55.7% | 64.7% |
| MMVP | 56.0% | 60.3% |
| MMStar | 67.1% | 72.3% |
| V* | 76.4% | 86.9% |
| CVBench | 74.5% | 87.6% |

### Test-time scaling (Figure 2)
Unlike all baselines:
- Ocean-R1 drops from 62.7% → 56.5% at 300 tokens (longer reasoning hurts)
- VaLR shows **monotonic improvement** with reasoning length across MathVista, MathVision, MMVP, MMhalu

---

## Key Ablations

| Condition | VSI-Bench |
|---|---|
| Base (no VaLR) | 33.0% |
| w/o alignment (latents only) | 34.0% |
| + Qwen encoder alignment | 39.6% |
| + DINOv3 alignment | 41.5% |
| + all three encoders (VaLR-M) | 52.9% |

Alignment is critical: without it, latents alone add only 1pp. REPA alignment provides the remaining 18.9pp gain.

---

## Relationship to Bypass Problem

VaLR is less bypass-prone than crop-based models because:
1. REPA aligns to **pre-trained encoder features** (not image subregion crops) — provides richer, less redundant targets
2. Alignment is applied at **every reasoning step**, not just at initialization — stronger gradient signal throughout training
3. Ablation confirms latent tokens are causally necessary (w/o alignment: 34.0% vs 52.9%)

Direct bypass intervention not applied. However, the 18.9pp gap between VaLR and VaLR without alignment provides indirect evidence that the latent tokens carry meaningful signal.

---

## Relationship to Dynamic Encoding

Directly validates the **dynamic > static encoding** principle from [[sources/perception-cognition-survey]]: re-encoding visual information before each reasoning step outperforms single static encoding. VaLR makes this operational at scale: 450K training samples, >20× faster convergence.

---

## Limitations

- No explicit planning over latent checkpoints at inference
- Doubles compute per reasoning step (latent generation + alignment at each step)
- Dependent on quality of 450K CoT training traces
- Multi-encoder combination adds compute; single DINOv3 gets 41.5% (still strong)
- Bypass intervention not applied

---

## LMRM Positioning

Stage 3 (System-2 long CoT with per-step visual checkpointing). The test-time scaling finding places VaLR at the Stage 3→4 boundary: it is the first wiki approach to make visual reasoning benefit from longer computation, a prerequisite for Stage 4 (N-LMRMs with agentic long-horizon planning).

---

## Related Pages

- [[sources/covt-chain-of-visual-thought]] — CoVT collapses on VSI-Bench (18.6%); VaLR's per-step checkpointing addresses this directly
- [[sources/whats-holding-back-latent-visual-reasoning]] — VaLR's ablation (latents without REPA → only 34.0%) confirms alignment is necessary; REPA to pre-trained encoders is non-redundant
- [[sources/mirage-machine-mental-imagery]] — Mirage generates latents once (at a single think step); VaLR generates before every step — complementary approaches
- [[sources/pearl-predictive-embedding-alignment]] — PEARL eliminates latents at inference; VaLR keeps them at every step; contrast in inference-time compute vs alignment quality
- [[sources/why-spatial-reasoning-hard-vlms]] — middle layer alignment (12th of 27) mirrors AdaptVis finding that attention-correctness peaks in middle layers
- [[concepts/continuous-visual-tokens]] — VaLR is a per-step checkpointing variant; adds to the design space
- [[concepts/visual-reasoning-in-vlms]] — new paradigm: step-wise visual checkpointing with REPA alignment
- [[analyses/vlm-reasoning-training-findings]] — VaLR as training approach; multi-view collapse finding; test-time scaling result
- [[analyses/covt-limitations-and-research-directions]] — CoVT's multi-view collapse (18.6%) documented as a concrete failure case
- [[entities/vsi-bench]] — cross-paper VSI-Bench leaderboard; VaLR-M holds top position
