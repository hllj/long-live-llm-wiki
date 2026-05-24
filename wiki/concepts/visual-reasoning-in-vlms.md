# Visual Reasoning in VLMs

An overview of how Vision-Language Models reason about visual content, the dominant paradigms, and their trade-offs. This page tracks the evolving landscape of approaches.

**Sources**: [[sources/covt-chain-of-visual-thought]], [[sources/whats-holding-back-latent-visual-reasoning]], [[sources/icot-interleaved-modal-chain-of-thought]], [[sources/why-spatial-reasoning-hard-vlms]], [[sources/mirage-machine-mental-imagery]], [[sources/lmrm-survey]]

---

## The core tension

VLMs project visual input into a language-centric token space to leverage LLM reasoning capabilities. This works well for semantic and logical tasks but creates a fundamental lossy bottleneck for perception-intensive tasks: continuous visual signals (depth, edges, geometry, spatial layout) are poorly representable as discrete text tokens.

**Mechanistic root cause** (ICML 2025, [[sources/why-spatial-reasoning-hard-vlms]]): image tokens are ~90% of input but receive only ~10% of attention — language pretraining priors dominate. The *geometric distribution* of attention determines spatial reasoning success, not the aggregate amount. Two failure modes: insufficient attention to referenced objects; misplaced attention on irrelevant regions. Attention–correctness correlation peaks in middle transformer layers (14–18). See [[concepts/visual-attention-in-vlms]].

---

## Paradigm taxonomy

### 1. Text-only Chain-of-Thought
Generate structured intermediate reasoning steps in language before answering. Strong for math, logic, knowledge — inherited from LLM CoT literature (Wei et al. 2022; DeepSeek-R1).

**Problem for vision**: Forces verbalization of continuous spatial/geometric relations. Empirically degrades performance on vision-centric tasks. Qwen3-VL-Thinking (with text CoT) is 5%+ worse than Qwen3-VL-Instruct on spatial benchmarks. Error accumulation in long text chains compounds this.

### 2. Tool-augmented reasoning
Delegate perception to external specialized models (SAM, depth estimators, etc.) and inject their outputs into context (ViperGPT, Visual ChatGPT, ToolVQA).

**Trade-offs**: Restores some spatial/geometric information, but introduces GPU overhead, architectural complexity, and an inherent performance ceiling bounded by each tool's ability. Not end-to-end differentiable.

### 3. Image generation/cropping in reasoning chain
Generate or crop images during the thinking process (MCoT).

**Trade-offs**: High compute cost; the generated images are still ultimately projected back into text space for reasoning, losing dense information.

### 4. Image interleaving (VChain)
Interleave full images and text in the reasoning chain.

**Trade-offs**: Still projects images into text space at the reasoning step; loses dense visual information.

### 5. Discrete latent reasoning (Aurora)
Use VQ-VAE latents of depth/detection signals as discrete tokens.

**Trade-offs**: Discrete quantization loses continuous information. No edge or semantic tokens. Substantially outperformed by CoVT on counting and depth tasks.

### 6. Continuous visual token reasoning (CoVT)
Generate compact continuous latent tokens encoding perceptual cues from vision experts, interleaved with text in the reasoning chain. End-to-end differentiable; self-contained; no external tools at inference.

**Current best on perception tasks** — see [[concepts/chain-of-visual-thought]] and [[sources/covt-chain-of-visual-thought]] for details.

**Open concern**: Latent tokens in several implementations are bypassed at inference (accuracy unchanged when replaced with dummies). CoVT's expert-aligned tokens may be less susceptible, but the bypass intervention has not been applied to CoVT directly. See [[sources/whats-holding-back-latent-visual-reasoning]].

### 9. Self-generated hidden-state latent tokens (Mirage, Modal-Mixed CoT)
The VLM recasts its own hidden states as latent tokens in a multimodal trajectory — no external expert models, no pixel generation. Two main implementations:

**Mirage** (CVPR 2026): Two-stage training — Stage 1 grounds latent tokens to visual representations via cosine similarity distillation from synthesized helper images; Stage 2 relaxes explicit supervision and trains via text-only loss with indirect gradient propagation through latents. GRPO reinforcement learning refines further. Results: 89% VSP Spatial Reasoning (vs. 85% CoT+GRPO baseline). t-SNE confirms latents cluster near visual manifold, addressing collapse concern. See [[sources/mirage-machine-mental-imagery]].

**Modal-Mixed CoT** (UC San Diego, 2602.00574): Uses a **diffusion-based latent decoder** (not cosine distillation) to generate 32 compressed latent embeddings from VLM hidden states. Special `<START>`/`<END>` tokens trigger modal switching; learned via GRPO. V* Attribute: 80.2%, Spatial: 78.9%; +35–42pp over baseline on Qwen3-VL-4B. RL degrades on abstract logic tasks. Bypass vulnerability unverified — uses own encoder (higher redundancy risk than CoVT). See [[sources/modal-mixed-cot-latent-embeddings]].

### 8. Inference-time attention reshaping (AdaptVis)
Confidence-guided temperature scaling of image attention logits: when model confidence is high, sharpen attention (α > 1) to amplify the regions already being focused on; when confidence is low, smooth attention (α < 1) to broaden context. No training, no new tokens. Targets attention from the final input token to all image tokens across all layers.

**Results**: LLaVA-1.6 Controlled_A: 48.2% → 98.2% (+50 pts). Consistent across LLaVA-1.5, LLaVA-1.6, Qwen2-VL. Outperforms DoLa and VCD. Minimal gain on general QA. See [[concepts/visual-attention-in-vlms]] and [[sources/why-spatial-reasoning-hard-vlms]].

### 11. Per-step visual checkpointing (VaLR)
Injects K=16 latent tokens **before each CoT reasoning step** — creating visual checkpoints that re-ground the model at every deliberative step. Aligned via REPA (patch-wise cosine similarity) to multiple pre-trained encoders (DINOv3, CLIP/SigLIP, π³). Two-stage training: SFT on 450K CoT traces → REPA alignment fine-tuning (ℒ_CE + 0.5·ℒ_REPA). Inference: standard VLM decoding but with K latent tokens generated before each reasoning step.

**Key finding**: all existing latent approaches (CoVT 18.6%, Monet 14.0%, LVR 18.4%) collapse on VSI-Bench (multi-view video spatial); VaLR-M achieves 52.9% — exceeds GPT-4o by 18.9pp. The only approach in the wiki to enable **test-time scaling**: longer reasoning chains monotonically improve performance.

**Bypass**: REPA alignment to pre-trained encoder features (non-redundant, unlike crops); ablation confirms alignment is causal (w/o REPA: 34.0% vs 52.9%). Bypass intervention not directly applied. See [[sources/valr-vision-aligned-latent-reasoning]].

### 10. JEPA-style trajectory prediction (PEARL)
Encodes expert tool-use trajectories during training via a predictive embedding objective (JEPA-inspired); K=4 learnable `[PRED]` tokens predict what a trajectory would produce. **No latent tokens at inference** — uses standard VLM decoding. Three training losses: ℒ_VLM + λ(ℒ_JEPA + ℒ_NextLat). Structurally immune to the latent bypass problem.

**Results**: V* 81.5%, MMVP 73.5% (Qwen2.5-VL-7B, LVR data); ThinkMorph multi-tool: V* +31pp, MMVP +38pp over SFT. Cross-model: works on 3B, 7B, and Qwen3-VL-4B. LoRA-only (rank=64) sufficient.

**Key corroboration**: PEARL's Figure 3 shows near-zero average correlation (r=−0.12, R²=0.02) between latent token count and performance in reconstruction-based baselines — independent empirical confirmation of [[sources/whats-holding-back-latent-visual-reasoning]]'s bypass finding. See [[sources/pearl-predictive-embedding-alignment]].

### 7. Attention-driven interleaved image patches (ICoT)
At designated points in the reasoning chain (newline tokens), select the top-k image patches by current attention score and re-inject them into the context. Creates truly interleaved visual–textual reasoning chains with no training required.

**Trade-offs**: Plug-and-play (no fine-tuning), but uses subregion patches from the original image rather than new perceptual transformations — potentially limited by what the input already contains. Memory overhead from attention score storage. Gains largest on long-form visual QA (+11.7% on LLaVA-W). See [[sources/icot-interleaved-modal-chain-of-thought]].

---

## Key benchmarks for vision-centric reasoning

| Benchmark | What it tests | Taxonomy category |
|---|---|---|
| CV-Bench (Count, Depth, Distance subtasks) | Counting, depth ordering, spatial distance | Quantitative–Static |
| BLINK | Perceptual reasoning (relative depth, visual correspondence, etc.) | Extrinsic–Qualitative–Static |
| RealWorldQA | Real-world visual question answering | Mixed |
| HRBench (4K, 8K) | High-resolution image perception | Extrinsic–Qualitative–Static |
| MMVP | Visual perception and reasoning | Mixed |
| MME-RealWorld | Real-world multimodal evaluation | Mixed |
| V* Bench | Guided visual search | Extrinsic–Qualitative–Static |
| MMStar-P (Coarse/Fine-grained Perception, Instance Reasoning) | Perception-aligned subsets | Mixed |
| M3CoT | Multi-domain multimodal CoT (science, math, commonsense; 267 categories) | Mixed |
| ScienceQA | Science visual question answering | Mixed |
| LLaVA-W | Long-form visual QA requiring detailed descriptions (ROUGE-L vs GPT-4V) | Extrinsic–Qualitative–Static |
| SPARTQA / SpatialEval(TQA) | Text-only spatial reasoning | Extrinsic–Qualitative–Static |
| VSI-bench | Video spatial intelligence | Extrinsic–Qualitative–Dynamic |
| ScanRefer / SQA3D | 3D grounding and embodied QA | Quantitative–Static |
| Super-CLEVR-3D / MindCube | Metric 3D reasoning | Quantitative–Static |
| OmniSpatial (8.4K QA, 50 subtasks) | Dynamic reasoning, geometric logic, perspective-taking | All categories; hardest — best model 56% vs human 93% |

The taxonomy column uses the [[concepts/spatial-reasoning-taxonomy]] framework from [[sources/spatial-reasoning-survey]]. Most benchmarks fall in the Extrinsic–Qualitative–Static category — the easiest for current models. Quantitative–Static and Dynamic tasks are underrepresented.

---

## LMRM Roadmap positioning

The [[sources/lmrm-survey]] (2025, 540+ papers) provides a four-stage developmental framework that contextualizes all paradigms above — see [[concepts/lmrm-roadmap]] for full details. In brief:

- **Stage 1** (modular/implicit): LLaVA-family, CLIP — reasoning hidden inside perception modules
- **Stage 2** (System-1 short CoT): Multimodal-CoT, TextCoT, tool-augmented approaches — explicit but bounded
- **Stage 3** (System-2 long CoT): CoVT, ICoT, Mirage, Multimodal-R1 — extended deliberative chains; where most current active research sits
- **Stage 4** (N-LMRMs, prospective): unified representation spaces, agentic reasoning, omni-modal — where the field is heading

---

## Open problems

1. **Latent bypass problem**: Latent tokens in several VLM reasoning models are bypassed at inference — replacing them with dummy tokens leaves accuracy unchanged. Root cause: training data using image subregion crops is redundant with the input, so models learn to ignore latents. Genuinely non-redundant intermediates (masked inputs, expert-model outputs) are required. See [[sources/whats-holding-back-latent-visual-reasoning]].
2. **Latent representation collapse**: Generated latent tokens cluster tightly (0.8–0.98 mutual cosine similarity) while diverging from ground-truth oracle representations (3.3% top-1 retrieval accuracy). Dataset design and training objectives need to explicitly prevent collapse.
3. **Interleaved multimodal reasoning**: Partially addressed by ICoT (CVPR 2025) via attention-driven patch re-injection — plug-and-play, no training required, +11.7% on LLaVA-W. Open question: whether patch subregions carry genuinely new information vs. what the model already had from the full image. See [[sources/icot-interleaved-modal-chain-of-thought]].
4. **Design space of visual token types**: Only a few expert combinations explored; hybrid or domain-specific experts may help
5. **Scaling**: Most work done at 7–13B scale; behaviour at frontier scale is unclear
6. **Non-perception tasks**: Visual reasoning that requires commonsense + perception simultaneously remains challenging
