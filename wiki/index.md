# Wiki Index

_Maintained by Claude. Updated on every ingest and when new pages are created._

## Sources

- [Perception, Reason, Think, and Plan: LMRM Survey](sources/lmrm-survey.md) — Harbin IT survey (May 2025, 540+ papers) proposing a four-stage roadmap: modular → System-1 CoT → System-2 long reasoning → Native LMRMs
- [Spatial Reasoning in MLLMs: A Survey](sources/spatial-reasoning-survey.md) — U. Pittsburgh survey (Nov 2025); 3D cognitive taxonomy, 3 root failure modes, benchmark gap analysis; covers training and inference-based methods
- [From Perception to Cognition: VL Interactive Reasoning Survey](sources/perception-cognition-survey.md) — Renmin U. survey (Sep 2025); Perception-Cognition framework, endogenous/exogenous evidence injection taxonomy, process supervision finding (+4–10pp)
- [From Perception to Reasoning: Deep Thinking in MLLMs (MCoT Survey)](sources/mcot-deep-thinking-survey.md) — HIT survey (Nov 2025); 3D MCoT framework (paradigm topology × post-training × inference); SFT+RL > either alone; inference-time scaling works
- [SpatialLadder: Progressive Training for Spatial Reasoning](sources/spatialladder.md) — Zhejiang U. (Oct 2025); 3-stage curriculum (localize→understand→GRPO); 3B model beats GPT-4o by 20.8%; perception grounding is bottleneck not reasoning capacity
- [OmniSpatial Benchmark](sources/omnispatial-benchmark.md) — Tsinghua/PKU (Jun 2025); 8.4K QA pairs, 50 subtasks; best model 56% vs human 93%; geometric reasoning ~30-40% (near-random); manual 6.9K data → +7.82pp vs template 200K → +1.29pp
- [LaCoT: Latent Chain-of-Thought for Visual Reasoning](sources/lacot-latent-chain-of-thought.md) — RIT/Snap (Oct 2025); GFlowNet training (RGFN) beats GRPO by 5.7–6.5pp; BiN inference beats BoN by 13–18.8pp without reward models; GRPO shown to degrade complex visual reasoning
- [VaLR: Vision-aligned Latent Reasoning](sources/valr-vision-aligned-latent-reasoning.md) — (May 2026); REPA-aligned latent checkpoints before every reasoning step; VaLR-M 52.9% VSI-Bench vs CoVT 18.6% (all static latent models collapse on multi-view); only approach enabling test-time scaling
- [PEARL: Multimodal Latent Reasoning via Predictive Embeddings](sources/pearl-predictive-embedding-alignment.md) — U. Edinburgh (Apr 2026); JEPA-style trajectory distillation; no latent tokens at inference → bypass-immune; ThinkMorph multi-tool: +31pp V*, +38pp MMVP; independently corroborates bypass finding (avg r=−0.12 latent-count vs performance)
- [Modal-Mixed CoT with Latent Embeddings](sources/modal-mixed-cot-latent-embeddings.md) — UC San Diego (2026); diffusion decoder generates 32 compressed latent "sketch" embeddings from VLM hidden states; `<START>`/`<END>` modal-switching; +35–42pp on V* over Qwen3-VL-4B baseline; RL degrades abstract logic
- [CoVT: Chain-of-Visual-Thought](sources/covt-chain-of-visual-thought.md) — UC Berkeley paper (Nov 2025) introducing continuous visual tokens for VLM reasoning; +5.5–14% on vision-centric benchmarks over Qwen2.5-VL-7B
- [What's Holding Back Latent Visual Reasoning?](sources/whats-holding-back-latent-visual-reasoning.md) — IST/CMU paper (May 2026) revealing the latent bypass problem and representation collapse in 4 latent VLM reasoning models; shows latents can work with non-redundant training data
- [ICoT: Interleaved-Modal Chain-of-Thought](sources/icot-interleaved-modal-chain-of-thought.md) — CVPR 2025 paper; plug-and-play attention-driven patch re-injection for truly interleaved visual–textual reasoning; +11.7% on LLaVA-W, no training required
- [Why Is Spatial Reasoning Hard for VLMs?](sources/why-spatial-reasoning-hard-vlms.md) — ICML 2025 paper; mechanistic root cause: image tokens get ~10% of attention despite being ~90% of input; AdaptVis confidence-guided scaling achieves +50 pts on controlled spatial benchmarks
- [Mirage: Machine Mental Imagery](sources/mirage-machine-mental-imagery.md) — CVPR 2026 paper (UMass+MIT); VLM recasts own hidden states as latent visual tokens via two-stage distillation+GRPO; avoids collapse; 89% VSP spatial reasoning

## Entities

- [Qwen2.5-VL](entities/qwen2-5-vl.md) — Alibaba VLM used as CoVT's primary base model (7B variant)
- [VSI-Bench](entities/vsi-bench.md) — multi-view video spatial intelligence benchmark; cross-paper leaderboard: VaLR-M 52.9%, GPT-4o 34.0%, CoVT 18.6% (below base); primary discriminator for static vs. per-step latent grounding
- [V*Bench](entities/v-star-bench.md) — visual grounding benchmark (Attribute + Spatial subtasks); used by PEARL (81.5%), Modal-Mixed CoT (80.2%/78.9%), and bypass paper for causal latent use testing

## Concepts

- [GRPO](concepts/grpo.md) — Group Relative Policy Optimization; dominant RL method (14 pages); KL penalty limits exploration; LaCoT shows it underperforms zero-shot on MathVista/MathVerse/MMMU; GFlowNet (RGFN) outperforms by 5.7–6.5pp
- [LMRM Developmental Roadmap](concepts/lmrm-roadmap.md) — four-stage framework (modular → System-1 → System-2 → N-LMRMs) mapping all wiki approaches to their historical position; from the LMRM survey
- [Spatial Reasoning Taxonomy](concepts/spatial-reasoning-taxonomy.md) — 3D cognitive taxonomy (frame of reference × type × nature), 4 complexity levels, 3 root failure modes, benchmark gaps; from the spatial reasoning survey
- [Perception-Cognition Framework](concepts/perception-cognition-framework.md) — two-layer functional framework (perception layer → cognition layer); endogenous/exogenous evidence injection taxonomy; hallucination as structural symptom
- [Visual Attention in VLMs](concepts/visual-attention-in-vlms.md) — mechanistic analysis: attention imbalance (90% image tokens → 10% attention), two failure modes, layer-wise dynamics, AdaptVis
- [Chain-of-Visual-Thought (CoVT)](concepts/chain-of-visual-thought.md) — framework for reasoning with continuous visual tokens inside a VLM's think chain
- [Continuous Visual Tokens](concepts/continuous-visual-tokens.md) — the ~20-token latent mechanism: segmentation (×8), depth (×4), edge (×4), DINO (×4) with two alignment strategies
- [Visual Reasoning in VLMs](concepts/visual-reasoning-in-vlms.md) — taxonomy of VLM visual reasoning paradigms and their trade-offs; benchmark landscape

## Analyses

- [Visual Thinking Techniques in VLMs](analyses/visual-thinking-techniques.md) — comparison of all 6 VLM visual reasoning paradigms with trade-offs; CoVT deep dive and open problems
- [CoVT: Limitations and Research Directions](analyses/covt-limitations-and-research-directions.md) — structured breakdown of CoVT's 5 current limitations and 6 research directions addressing them
- [VLM Reasoning Training: Key Findings](analyses/vlm-reasoning-training-findings.md) — synthesis of root problems, training approaches (CoVT, Mirage, ICoT, AdaptVis), and the latent bypass finding across 5 papers
