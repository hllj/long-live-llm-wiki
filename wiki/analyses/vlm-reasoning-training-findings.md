# VLM Reasoning Training: Key Findings

A synthesis of what the wiki knows about how VLMs learn to reason visually — the root problems, what training approaches exist, and the critical negative findings that reframe how to interpret benchmark gains.

**Sources**: [[sources/covt-chain-of-visual-thought]], [[sources/whats-holding-back-latent-visual-reasoning]], [[sources/icot-interleaved-modal-chain-of-thought]], [[sources/why-spatial-reasoning-hard-vlms]], [[sources/mirage-machine-mental-imagery]], [[sources/modal-mixed-cot-latent-embeddings]], [[sources/pearl-predictive-embedding-alignment]], [[sources/valr-vision-aligned-latent-reasoning]], [[sources/lacot-latent-chain-of-thought]], [[sources/perception-cognition-survey]], [[sources/mcot-deep-thinking-survey]]

---

## The Root Problem

The mechanistic cause is well-established: **image tokens are ~90% of input but receive only ~10% of attention** — language pretraining priors dominate. It is not the *amount* of image attention that matters, but its *geometric distribution*: whether the model attends to the correct spatial locations predicts correctness (AUROC metric). Two failure modes: insufficient attention to referenced objects; misplaced attention on irrelevant regions. See [[concepts/visual-attention-in-vlms]].

**Training makes this worse for perception tasks**: Qwen3-VL-Thinking (text CoT) is 5%+ *worse* than Qwen3-VL-Instruct on spatial benchmarks — text-only CoT training can degrade visual performance.

---

## Critical Negative Finding: The Latent Bypass Problem

[[sources/whats-holding-back-latent-visual-reasoning]] (IST/CMU, May 2026) tested 4 latent VLM reasoning models (LVR, Monet, ILVR, LanteRn) at 3B/7B scale:

- Replacing generated latent tokens with **random subregions, zeros, or noise** left accuracy **unchanged**
- Even providing **oracle ground-truth latents** at inference produced minimal improvement
- Models learn to route around latent tokens entirely

**Root cause is training data**: these models use image subregion crops as intermediate steps. Since the original input already contains those subregions, the model has no incentive to attend to latents — zero marginal information.

**Representation collapse**:
- Cosine similarity *between* predicted latents: **0.8–0.98** (nearly identical across samples)
- Top-1 retrieval accuracy against ground-truth oracles: **3.3%**

**When latents do work**: with masked inputs or a synthetic Tetris rotation task (genuinely non-redundant intermediates), oracle tokens beat dummy tokens by 16–61 points.

**Implication**: Benchmark gains ≠ causal latent use. A model can improve via CoT training supervision without latents influencing inference at all.

---

## Training Approaches

### CoVT — External Expert Alignment (UC Berkeley, Nov 2025)
- Base: Qwen2.5-VL-7B with LoRA (rank=16, α=32); projection layers trained from scratch
- ~20 continuous tokens: SAM segmentation (×8) + DepthAnything depth (×4) + edges (×4) + DINO (×4)
- Results: **+5.5–14%** on vision-centric benchmarks (CV-Bench Depth +14%)
- Less bypass-prone than crop-based models because expert outputs are *transformations* (depth maps, segmentation masks) — genuinely non-redundant
- **Caveat**: bypass intervention not applied to CoVT directly; gains may reflect better training supervision rather than causal token use
- See [[concepts/chain-of-visual-thought]], [[concepts/continuous-visual-tokens]]

### Mirage — Two-Stage Distillation + GRPO (UMass/MIT, CVPR 2026)
No external experts — the VLM recasts its own hidden states as latent tokens:

- **Stage 1 (Grounding)**: cosine similarity distillation from synthesized helper images → anchors latents to visual manifold. Alone: 46% on VSP Spatial Planning L5.
- **Stage 2 (Relaxation)**: explicit latent supervision removed; gradients propagate via text loss only. Alone: 16%. *Both stages together required*: 53%.
- **Stage 3 (GRPO)**: accuracy + format rewards push beyond imitation ceiling. Final: **89% VSP Spatial Reasoning** (vs. 85% CoT+GRPO baseline; 52% Anole; 61% MVoT).
- Optimal hyperparameters: k=6 latent tokens; γ=0.1 cosine loss weight (k=8 causes error accumulation)
- t-SNE confirms latents cluster near visual manifold after Stage 2 — Stage 1 grounding persists through relaxation; avoids collapse
- See [[sources/mirage-machine-mental-imagery]]

### ICoT — No Training Required (CVPR 2025)
Plug-and-play at inference: at designated reasoning chain positions, re-inject top-k image patches by attention score. **+11.7% on LLaVA-W** with zero fine-tuning. Higher bypass risk than expert-aligned tokens (patches are subregions of input). See [[sources/icot-interleaved-modal-chain-of-thought]].

### SpatialLadder — Progressive Curriculum + GRPO (Zhejiang U., Oct 2025)
Three-stage training on Qwen2.5-VL-3B targeting the spatial perception-reasoning gap:

- **Stage 1 (Localization SFT)**: object localization only; builds visual grounding before any reasoning
- **Stage 2 (Spatial Understanding SFT)**: single-image + multi-view + video spatial tasks across 7 dimensions
- **Stage 3 (GRPO)**: dual reward (format + accuracy); cold-start with 1,255 rejection-sampled CoT samples
- Results: **+23.4% avg over base; beats GPT-4o by 20.8%** on in-domain spatial benchmarks; 45.7% VSI-Bench (vs. 34.0% GPT-4o)
- Key ablation: Stage 2 removal = −9.4%; multi-view data removal = −16.4% (largest contributors)
- Controlled experiment: +5% from bounding box hints, +4.5% from directional cues → proves perception grounding is the bottleneck, not reasoning capacity
- Attention IoU improves 33.8% → 37.7%; entropy drops 0.193 → 0.176 (more concentrated on task-relevant regions)
- See [[sources/spatialladder]]

### Modal-Mixed CoT — Diffusion Decoder + GRPO (UC San Diego, 2026)
A parallel track to Mirage: uses a **diffusion-based latent decoder** conditioned on VLM hidden states to generate compact visual sketch embeddings (256 → 32 tokens via average pooling):

- **Architecture**: VLM's own vision encoder reused as semantic anchor; `<START>`/`<END>` special tokens trigger text↔latent switching; diffusion model adds ~50 denoising steps
- **Stage 1 (SFT)**: Joint loss — next-token prediction + diffusion L2 reconstruction; λ=1.0 optimal
- **Stage 2 (GRPO)**: Binary accuracy reward on VisuLogic; fixed LR 5e-6
- **Results**: V* Attribute 80.2%, Spatial 78.9% (SFT); generalization to Qwen3-VL-4B: +35pp Attribute, +42pp Spatial
- **Ablation**: Diffusion decoder 46.7% vs cosine loss 44.7% vs text-only 40.6% — diffusion adds ~2pp over cosine, both beat text-only
- **RL limitation**: GRPO degrades abstract logic tasks (LogicVista Spatial: 31.6% SFT → 25.3% RL) — a new nuance not seen in Mirage
- **Bypass status**: not tested; uses VLM's own encoder (higher redundancy risk than CoVT's expert transformations)
- See [[sources/modal-mixed-cot-latent-embeddings]]

### LaCoT — GFlowNet + Bayesian Inference (RIT/Snap/Rochester, arXiv 2510.23925)
Reformulates text CoT as posterior inference over latent reasoning chains. Uses GFlowNets with reference-guided filtering (RGFN) instead of GRPO to sample reward-proportional reasoning chains without KL-penalty constraints:

- **RGFN**: samples m=6 candidates, filters to those with reward > δₛ·R(reference); no backpropagation through failures; annealing schedule prevents catastrophic forgetting
- **ISubTB**: token-level reward interpolation (λ=8) reduces compute while preserving flow consistency (O(λ²) error bound)
- **BiN** (Bayesian Inference over N): replaces Best-of-N with marginal likelihood ranking — no external reward model, +13–18.8pp over BoN
- **GRPO finding**: GRPO *underperforms zero-shot and SFT* on MathVista/MathVerse/MMMU — KL penalty blocks exploration to better reasoning paths
- **Results**: MathVista 68.4% (vs 63.7% baseline, +4.7pp), MathVerse 43.3% (+5.1pp), MMMU 54.9% (+4.9pp); 3B model beats 11B LLaVA-CoT on MathVerse
- **BiN generality**: +1.7–1.9pp on standard Qwen2.5-VL without retraining — model-agnostic inference improvement
- See [[sources/lacot-latent-chain-of-thought]]

> **Scope note**: "Latent" here means *text reasoning chains as latent variables* (probabilistic inference), NOT visual latent tokens. LaCoT is about text CoT quality, not visual perception.

### VaLR — Per-step REPA Checkpointing (arXiv 2602.04476, May 2026)
Per-step visual checkpointing: injects K=16 latent tokens before each reasoning step, aligned via REPA (patch-wise cosine similarity) to pre-trained vision encoders (DINOv3, CLIP/SigLIPv2, π³):

- **Stage 1**: SFT on 450K CoT traces (Zebra-CoT, CogCoM, ReFocus, Visual-CoT, GCoT)
- **Stage 2**: REPA fine-tuning — ℒ = ℒ_CE + 0.5·ℒ_REPA; alignment at middle layers (12th of 27)
- **VSI-Bench results**: VaLR-S 41.5%, VaLR-M 52.9% vs CoVT 18.6% / Monet 14.0% / LVR 18.4% / base 33.0% / GPT-4o 34.0%
- **Collapse finding**: all prior latent models *perform below base model* on multi-view tasks — static injection cannot sustain visual grounding in long chains
- **Test-time scaling**: only approach where longer reasoning chains monotonically improve performance; baselines degrade (Ocean-R1: 62.7% → 56.5% at 300 tokens)
- **Convergence**: >20× faster than vanilla SFT on V*; REPA alignment to pre-trained encoders is causally necessary (w/o: 34.0% vs 52.9%)
- See [[sources/valr-vision-aligned-latent-reasoning]]

### PEARL — JEPA-style Trajectory Prediction (U. Edinburgh, Apr 2026)
Eliminates latent tokens at inference entirely: trains a JEPA-inspired predictor to internalize what expert tool-use trajectories would produce, then uses standard VLM decoding at test time.

- **Architecture**: K=4 `[PRED]` tokens predict trajectory embedding; dual forward pass during training (input + trajectory encoded separately); LoRA rank=64
- **Loss**: ℒ_PEARL = ℒ_VLM + λ(ℒ_JEPA + ℒ_NextLat), λ=0.2; ℒ_JEPA = SmoothL1 alignment to stop-gradient trajectory; ℒ_NextLat = belief-state regularizer
- **Results**: V* 81.5%, MMVP 73.5% (single-type, LVR data); ThinkMorph 4-tool: **+31pp V*, +38pp MMVP** over SFT; PixelReasoner multi-step: MMVP 70.0% (vs 67.0%)
- **Bypass immunity**: no latent tokens at inference → structurally avoids the latent bypass problem
- **Corroborates bypass finding**: Figure 3 correlation analysis across reconstruction-based baselines: avg r=−0.12, R²=0.02 — near-zero correlation between latent count and performance; independent confirmation that reconstruction models don't use latents causally
- **Training-inference mismatch exposed**: >75% of LVR training samples have >8 latents; inference uses 4–8 → structural mismatch in competing methods
- See [[sources/pearl-predictive-embedding-alignment]]

### AdaptVis — Inference-Only Attention Reshaping (ICML 2025)
Confidence-guided temperature scaling of image attention logits: high confidence → sharpen (amplify focused regions); low confidence → smooth (broaden context). **+50 points on controlled spatial benchmarks** (LLaVA-1.6: 48.2% → 98.2%). No training. See [[sources/why-spatial-reasoning-hard-vlms]].

---

## Training Supervision Findings (from Perception-Cognition Survey)

[[sources/perception-cognition-survey]] (Sep 2025) adds three cross-cutting training findings relevant to all approaches above:

1. **Process supervision > outcome supervision**: supervising correctness of intermediate reasoning steps yields **+4–10 percentage points** over outcome-only supervision. Implication: training objectives that reward correct intermediate visual evidence (not just final answer correctness) are more effective.
2. **Interleaved CoT > sequential**: generating text reasoning and visual evidence jointly outperforms text-then-vision or vision-then-text isolation.
3. **Dynamic > static encoding**: methods using multiple forward passes with targeted visual re-encoding (DeepEyes, Pixel Reasoner) outperform single-pass static encoding for complex tasks — directly validates the direction CoVT and Mirage are pursuing.

See [[concepts/perception-cognition-framework]] for the endogenous/exogenous evidence injection taxonomy.

---

## Cross-Cutting Takeaways

| Finding | Implication |
|---|---|
| Benchmark gains ≠ causal latent use | CoT training supervision alone can drive gains without latents influencing inference |
| Dataset design is the bottleneck | Intermediates must be non-redundant transformations, not crops |
| Two-stage training is necessary (Mirage) | Stage 1 grounding + Stage 2 relaxation together; neither alone reaches the same result |
| Attention distribution beats attention amount | Increasing image attention uniformly doesn't help; geometric correctness of attention does |
| Process supervision > outcome supervision | +4–10pp from supervising intermediate step correctness, not just final answer |
| Dynamic > static encoding | Multiple re-encoding passes outperform single-pass for complex reasoning |
| SFT + RL > either alone | Combined training establishes patterns (SFT) then optimises them (RL); best results across MCoT paradigms |
| GRPO can degrade reasoning | On MathVista/MathVerse/MMMU, GRPO underperforms zero-shot — KL penalty blocks exploration; GFlowNet (RGFN) avoids this and outperforms by 5.7–6.5pp (LaCoT) |
| Diversity > greedy in inference-time scaling | BiN (marginal likelihood over N diverse chains) outperforms BoN (best of N by reward) by 13–18.8pp; higher temperature T=0.7 beats greedy |
| Static latent injection collapses on multi-view | CoVT, Monet, LVR all score below their base model on VSI-Bench — single-step injection can't sustain visual grounding; per-step checkpointing (VaLR) required |
| Test-time scaling requires visual grounding | Text CoT baselines degrade with longer chains on spatial tasks; VaLR is the first approach where longer reasoning monotonically helps |
| Inference-time scaling works | MCTS, beam search, self-refinement improve robustness without parameter updates |
| Data annotation is the bottleneck | Few high-quality multimodal CoT datasets exist; construction is labour-intensive |
| Manual data >> template data (6×) | [[sources/omnispatial-benchmark\|OmniSpatial]]: 6.9K manual samples → +7.82pp; 200K template samples → +1.29pp; curation quality dominates scale |
| Scale is an open question | Most results at 7B–13B; frontier-scale behavior unknown across all approaches |

---

## Open Problems

1. Bypass intervention not yet applied to CoVT — causal role of expert tokens unverified
2. Mirage evaluated primarily on spatial reasoning; generalization to other vision tasks unclear
3. No training approach has been tested beyond 13B scale
4. Non-perception tasks (commonsense + perception simultaneously) remain hard across all paradigms

See also: [[concepts/visual-reasoning-in-vlms]], [[analyses/visual-thinking-techniques]], [[analyses/covt-limitations-and-research-directions]]
