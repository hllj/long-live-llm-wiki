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

## [2026-05-22] ingest | Mirage: Machine Mental Imagery (arXiv 2506.17218, CVPR 2026)

Source: `raw/2506.17218.pdf` — CVPR 2026 paper (UMass+MIT) introducing Mirage: VLM recasts own hidden states as latent visual tokens via two-stage training (Stage 1: cosine grounding to visual manifold; Stage 2: relaxation with indirect gradient propagation) + GRPO. t-SNE confirms latents stay near visual subspace, addressing collapse concern from bypass paper. 89% VSP spatial reasoning vs. 85% CoT+GRPO baseline.
Pages created: `wiki/sources/mirage-machine-mental-imagery.md`
Pages updated: `wiki/concepts/visual-reasoning-in-vlms.md` (new Paradigm 9), `wiki/analyses/visual-thinking-techniques.md` (paradigm table), `wiki/analyses/covt-limitations-and-research-directions.md` (Limitations 1 + 6, Key Takeaway), `wiki/concepts/continuous-visual-tokens.md` (Mirage's answer to collapse), `wiki/concepts/visual-attention-in-vlms.md`, `wiki/sources/whats-holding-back-latent-visual-reasoning.md` (Mirage as partial answer), `wiki/entities/qwen2-5-vl.md`, `wiki/index.md`
Key additions: Mirage established as the first approach to architecturally address latent collapse via Stage 1 grounding; removes external expert model dependency; three complementary training-free/trained approaches (ICoT, AdaptVis, Mirage) now documented alongside CoVT.

## [2026-05-22] ingest | Why Is Spatial Reasoning Hard for VLMs? (arXiv 2503.01773, ICML 2025)

Source: `raw/2503.01773.pdf` — ICML 2025 paper revealing mechanistic root cause of VLM spatial reasoning failure: image tokens are ~90% of input but get ~10% of attention; attention geometric distribution (not quantity) determines correctness. AdaptVis: confidence-guided temperature scaling achieves +50 pts on LLaVA-1.6 Controlled_A, training-free.
Pages created: `wiki/sources/why-spatial-reasoning-hard-vlms.md`, `wiki/concepts/visual-attention-in-vlms.md`
Pages updated: `wiki/analyses/visual-thinking-techniques.md` (core tension + paradigm table), `wiki/concepts/visual-reasoning-in-vlms.md` (core tension + new paradigm 8), `wiki/analyses/covt-limitations-and-research-directions.md` (root problem grounded mechanistically), `wiki/index.md`
Key additions: Mechanistic explanation for spatial reasoning failure now links all paradigms in the wiki; AdaptVis documented as a third training-free approach complementary to ICoT and CoVT.

## [2026-05-22] ingest | ICoT: Interleaved-Modal Chain-of-Thought (arXiv 2411.19488, CVPR 2025)

Source: `raw/2411.19488.pdf` — CVPR 2025 paper introducing attention-driven patch re-injection (ADS) for truly interleaved visual–textual reasoning chains, plug-and-play with no training required; +11.7% on LLaVA-W, +6.4% on ScienceQA over best baselines on Chameleon-7B.
Pages created: `wiki/sources/icot-interleaved-modal-chain-of-thought.md`
Pages updated: `wiki/concepts/visual-reasoning-in-vlms.md` (new paradigm 7 + benchmark entries + open problem update), `wiki/analyses/covt-limitations-and-research-directions.md` (Limitation 1 and Direction 1 updated with ICoT), `wiki/analyses/visual-thinking-techniques.md` (paradigm table + open problem updated), `wiki/index.md`
Key additions: ICoT established as the concrete solution to CoVT's interleaving limitation; open gap noted as combining ICoT-style dynamic scheduling with CoVT-style expert tokens.

## [2026-05-22] ingest | What's Holding Back Latent Visual Reasoning? (arXiv 2605.18445)

Source: `raw/2605.18445.pdf` — IST/CMU paper (May 2026) finding that latent visual tokens in 4 VLM reasoning models are bypassed at inference (dummy tokens leave accuracy unchanged) due to uninformative crop-based training data and latent representation collapse (3.3% oracle retrieval accuracy, 0.8–0.98 self-similarity).
Pages created: `wiki/sources/whats-holding-back-latent-visual-reasoning.md`
Pages updated: `wiki/concepts/continuous-visual-tokens.md`, `wiki/concepts/chain-of-visual-thought.md`, `wiki/concepts/visual-reasoning-in-vlms.md`, `wiki/analyses/covt-limitations-and-research-directions.md`, `wiki/analyses/visual-thinking-techniques.md`, `wiki/index.md`
Key additions: Bypass problem and representation collapse added as open problems across all concept/analysis pages. CoVT scope caveat noted: expert-aligned tokens were not tested, and the paper's Tetris result shows the mechanism can work with non-redundant training data.

## [2026-05-22] query | CoVT Limitations and Research Directions

Answered question about current limitations of vision language reasoning with chain of visual thought. Identified 5 CoVT-specific limitations (no interleaved reasoning, narrow token design space, scale untested, commonsense+perception gap, fixed token budget) and 6 research directions (interleaved chains, adaptive budgets, domain-specific experts, temporal/video CoVT, scaling laws, self-supervised token learning). Filed result as `wiki/analyses/covt-limitations-and-research-directions.md`.

## [2026-05-23] lint
Issues found: 7 total — 0 contradictions, 0 orphans, 0 missing concept pages, 1 hub page flagged, 6 missing cross-references
Fixed: all 6 cross-references added (visual-attention-in-vlms.md linked from chain-of-visual-thought.md, covt-chain-of-visual-thought.md, icot-interleaved-modal-chain-of-thought.md, whats-holding-back-latent-visual-reasoning.md, mirage-machine-mental-imagery.md; concept page links added to qwen2-5-vl.md). Hub page flag is a monitoring note only.
Flagged for new sources: none

## [2026-05-23] ingest | OmniSpatial: Comprehensive Spatial Reasoning Benchmark for VLMs (arXiv 2506.03135)

Source: `raw/2506.03135.pdf` — Tsinghua/PKU benchmark (Jun 2025; v3 Feb 2026); 8,400 manually annotated QA pairs across 4 categories and 50 subcategories; Krippendorff's α = 0.84; human baseline 92.63% vs best model (o3) 56.33%. Key findings: geometric/pattern reasoning 20-40% (near-random); non-egocentric perspective-taking 32-48%; manual data (6.9K) → +7.82pp vs template data (200K) → +1.29pp.
Pages created: `wiki/sources/omnispatial-benchmark.md`
Pages updated: `wiki/concepts/spatial-reasoning-taxonomy.md` (benchmark gaps table updated with OmniSpatial coverage + empirical failure data), `wiki/concepts/visual-reasoning-in-vlms.md` (OmniSpatial added to benchmark table), `wiki/analyses/vlm-reasoning-training-findings.md` (manual >> template data finding added), `wiki/index.md`
Key additions: OmniSpatial provides the clearest quantitative picture of VLM spatial failure — geometric reasoning is near-random, non-egocentric perspective-taking is a major bottleneck, and the ~36pp human-AI gap shows how far current models are. The manual-vs-template data quality finding (6×) is the most actionable new training result.

## [2026-05-23] ingest | SpatialLadder: Progressive Training for Spatial Reasoning in VLMs (arXiv 2510.08531)

Source: `raw/2510.08531.pdf` — Zhejiang U. (Oct 2025) three-stage progressive training framework on Qwen2.5-VL-3B: Stage 1 localization SFT → Stage 2 multi-modal spatial understanding SFT → Stage 3 GRPO. Key finding: perception grounding is the bottleneck, not reasoning capacity (+5% from bounding box hints, +4.5% from directional cues). SpatialLadder-26kk dataset with 26,610 samples across single-image, multi-view, and video modalities.
Pages created: `wiki/sources/spatialladder.md`
Pages updated: `wiki/concepts/spatial-reasoning-taxonomy.md` (SpatialLadder added to training methods; perception-grounding-as-bottleneck finding added), `wiki/analyses/vlm-reasoning-training-findings.md` (SpatialLadder added as new training approach with full results), `wiki/concepts/visual-attention-in-vlms.md` (attention IoU improvement noted as training-time complement to AdaptVis inference-time fix), `wiki/index.md`
Key additions: SpatialLadder establishes the "perception-before-reasoning" principle with controlled evidence. It is the strongest training-time fix for spatial reasoning in the wiki, complementing AdaptVis (inference-time) and CoVT/Mirage (latent token approaches).

## [2026-05-23] ingest | From Perception to Reasoning: Deep Thinking Empowers MLLMs (arXiv 2511.12861)

Source: `raw/2511.12861.pdf` — HIT survey (Nov 2025) on Multimodal Chain-of-Thought (MCoT) reasoning. Three-dimensional framework: (1) CoT paradigms — chain/tree/graph topology; (2) post-training — SFT, RL, SFT+RL combined; (3) inference strategies — prompting, MCTS/beam search, self-refinement, RAG, agent assistance. Key findings: SFT+RL combined > either alone; inference-time scaling works without parameter updates; data annotation scarcity is primary bottleneck.
Pages created: `wiki/sources/mcot-deep-thinking-survey.md`
Pages updated: `wiki/analyses/vlm-reasoning-training-findings.md` (SFT+RL, inference-time scaling, data scarcity rows added to takeaways), `wiki/concepts/lmrm-roadmap.md` (MCoT topology detail added to Stage 3), `wiki/index.md`
Key additions: CoT topology (chain→tree→graph) and SFT+RL > either alone now documented; inference-time scaling via search and self-refinement established as a complementary improvement path alongside training-time approaches.

## [2026-05-23] ingest | From Perception to Cognition: A Survey of VL Interactive Reasoning in MLLMs (arXiv 2509.25373)

Source: `raw/2509.25373.pdf` — Renmin U. survey (Sep 2025) proposing a Perception-to-Cognition framework: two interdependent layers (perception = extraction/alignment; cognition = decomposition/evidence injection). Hallucination reframed as structural symptom of perception-cognition disconnect. Key findings: process supervision beats outcome supervision by +4–10pp; interleaved CoT beats sequential; dynamic multi-pass encoding beats static single-pass.
Pages created: `wiki/sources/perception-cognition-survey.md`, `wiki/concepts/perception-cognition-framework.md`
Pages updated: `wiki/analyses/vlm-reasoning-training-findings.md` (process supervision + dynamic encoding findings added; new takeaway rows), `wiki/sources/icot-interleaved-modal-chain-of-thought.md` (classified as endogenous single-pass evidence injection), `wiki/index.md`
Key additions: Evidence injection taxonomy (endogenous/exogenous) now documented, with ICoT, CoVT, and Mirage all placed as endogenous single-pass methods. Process supervision finding (+4–10pp) is the most actionable new training result added to the wiki.

## [2026-05-23] ingest | Spatial Reasoning in MLLMs: A Survey of Tasks, Benchmarks and Methods (arXiv 2511.15722)

Source: `raw/2511.15722.pdf` — U. Pittsburgh survey (Nov 2025) on spatial reasoning in MLLMs. Core contribution: a three-dimensional cognitive taxonomy (frame of reference × type × nature) with four complexity levels, plus identification of three root failure modes (projection bottleneck, statistical correlations over physical constraints, frame-of-reference instability).
Pages created: `wiki/sources/spatial-reasoning-survey.md`, `wiki/concepts/spatial-reasoning-taxonomy.md`
Pages updated: `wiki/concepts/visual-attention-in-vlms.md` (cognitive framing of 3 failure modes added), `wiki/concepts/visual-reasoning-in-vlms.md` (benchmark table extended with taxonomy column + new benchmarks), `wiki/index.md`
Key additions: Spatial reasoning failures now have both a mechanistic account (attention geometry, from AdaptVis paper) and a cognitive-architectural account (3 failure modes, from this survey). Benchmark table now annotated with taxonomy categories, revealing the current over-indexing on Extrinsic–Qualitative–Static tasks.

## [2026-05-23] ingest | Perception, Reason, Think, and Plan: A Survey on Large Multimodal Reasoning Models (arXiv 2505.04921)

Source: `raw/2505.04921.pdf` — Harbin IT survey (May 2025) reviewing 540+ publications across the LMRM landscape. Core contribution: a four-stage developmental roadmap (modular/implicit → System-1 short CoT → System-2 long CoT → Native LMRMs) that contextualises all approaches in the wiki within a historical arc.
Pages created: `wiki/sources/lmrm-survey.md`, `wiki/concepts/lmrm-roadmap.md`
Pages updated: `wiki/concepts/visual-reasoning-in-vlms.md` (LMRM stage mapping added), `wiki/analyses/visual-thinking-techniques.md` (roadmap positioning table added), `wiki/index.md`
Key additions: The LMRM roadmap establishes that all current wiki approaches (CoVT, ICoT, Mirage, AdaptVis) sit in Stages 2–3; Stage 4 (N-LMRMs with unified representations and agentic planning) is the prospective frontier. ICoT and MVoT are explicitly named in the survey as Stage 3 cross-modal reasoning. Mirage is the most Stage 4-adjacent approach currently in the wiki.

## [2026-05-23] ingest | LaCoT: Latent Chain-of-Thought for Visual Reasoning (arXiv 2510.23925)

Source: `raw/2510.23925.pdf` (fetched via arxiv HTML) — RIT/Snap/Rochester paper (Oct 2025) introducing LaCoT. Uses GFlowNets with Sub-Trajectory Balance to train a policy sampling text reasoning chains proportional to rewards — contrasting with GRPO's KL-penalized RL. Three contributions: (1) ISubTB token-level reward interpolation (λ=8, O(λ²) error bound); (2) RGFN reference-guided filtering avoiding catastrophic forgetting with no KL constraint; (3) BiN Bayesian Inference over N rationales replacing Best-of-N (no external reward model). Key findings: GRPO underperforms zero-shot baseline on MathVista/MathVerse/MMMU (KL penalty blocks exploration); RGFN beats GRPO by 5.7–6.5pp; BiN beats BoN by 13–18.8pp; 3B LaCoT beats LLaVA-CoT-11B on MathVerse. Scope note: "latent" here = text reasoning chains as latent variables, NOT visual latent tokens.
Pages created: `wiki/sources/lacot-latent-chain-of-thought.md`
Pages updated: `wiki/analyses/vlm-reasoning-training-findings.md` (LaCoT approach + GRPO-degrades and Diversity>greedy takeaways + sources), `wiki/concepts/lmrm-roadmap.md` (GFlowNet CoT training sub-type + table), `wiki/index.md`
Key additions: GRPO-can-degrade finding is now documented as a concrete failure case — important nuance given GRPO's widespread use (Mirage, Modal-Mixed CoT, SpatialLadder all use it). BiN as model-agnostic inference-time improvement (+1.7–1.9pp on any VLM without retraining) is a practical tool the wiki can recommend. GFlowNet positioned as an alternative to GRPO in the Stage 3 training landscape.

## [2026-05-23] ingest | VaLR: Vision-aligned Latent Reasoning for MLLMs (arXiv 2602.04476)

Source: `raw/2602.04476.pdf` (fetched via arxiv HTML) — paper (May 2026) introducing VaLR: per-step visual checkpointing via K=16 REPA-aligned latent tokens injected before each CoT reasoning step. Two-stage training: SFT on 450K CoT traces → REPA fine-tuning (ℒ_CE + 0.5·ℒ_REPA) against DINOv3, CLIP/SigLIPv2, and π³ encoders at middle layers. Key findings: (1) All existing latent models collapse on VSI-Bench multi-view tasks — CoVT 18.6%, Monet 14.0%, LVR 18.4%, all below base model 33.0%; VaLR-M 52.9%, exceeds GPT-4o by 18.9pp. (2) VaLR is the only approach enabling test-time scaling for visual reasoning (longer chains monotonically improve; baselines degrade). (3) REPA alignment is causally necessary: latents alone 34.0% → +REPA 52.9%. (4) >20× faster convergence than vanilla SFT.
Pages created: `wiki/sources/valr-vision-aligned-latent-reasoning.md`
Pages updated: `wiki/concepts/visual-reasoning-in-vlms.md` (paradigm 11 added), `wiki/analyses/vlm-reasoning-training-findings.md` (VaLR training approach + sources), `wiki/analyses/covt-limitations-and-research-directions.md` (VSI-Bench collapse finding noted), `wiki/sources/whats-holding-back-latent-visual-reasoning.md` (multi-view collapse link), `wiki/concepts/lmrm-roadmap.md` (per-step checkpointing sub-type + table), `wiki/index.md`
Key additions: Multi-view visual memory collapse is now documented as a critical failure mode for all static-injection latent approaches. VaLR is the first approach in the wiki to achieve test-time scaling for visual tasks — a Stage 3→4 boundary capability. The finding that CoVT scores below its base model on VSI-Bench is the sharpest existing evidence of static latent injection's limits.

## [2026-05-23] ingest | PEARL: Multimodal Latent Reasoning via Predictive Embeddings (arXiv 2604.08065)

Source: `raw/2604.08065.pdf` (fetched via arxiv HTML) — University of Edinburgh paper (Apr 2026) introducing PEARL (Predictive Embedding Alignment for Reasoning in Latent space). JEPA-inspired framework: K=4 [PRED] tokens predict expert tool-use trajectory embeddings during training; standard VLM decoding at inference with no latent tokens. Three-loss training: ℒ_VLM + λ(ℒ_JEPA + ℒ_NextLat). Results: V* 81.5%, MMVP 73.5% (single-type); ThinkMorph multi-tool: +31pp V*, +38pp MMVP. Key: PEARL's Figure 3 independently corroborates bypass paper (avg r=−0.12 between latent count and performance in reconstruction baselines). Training-inference mismatch exposed: >75% LVR training samples have >8 latents but inference uses 4–8.
Pages created: `wiki/sources/pearl-predictive-embedding-alignment.md`
Pages updated: `wiki/concepts/visual-reasoning-in-vlms.md` (paradigm 10 added), `wiki/analyses/vlm-reasoning-training-findings.md` (PEARL training approach + sources), `wiki/sources/whats-holding-back-latent-visual-reasoning.md` (PEARL as corroboration), `wiki/concepts/lmrm-roadmap.md` (JEPA trajectory distillation sub-type + mapping table), `wiki/index.md`
Key additions: PEARL is the first approach to eliminate latent tokens at inference entirely — structurally immune to bypass. Its correlation analysis independently corroborates the IST/CMU bypass paper. The "Stage 3 training → Stage 2 inference" framing is a new position in the roadmap taxonomy. ThinkMorph's +31–38pp over SFT confirms tool-trajectory knowledge can be distilled across heterogeneous tool types.

## [2026-05-23] ingest | Modal-Mixed CoT with Latent Embeddings (arXiv 2602.00574)

Source: `raw/2602.00574.pdf` (fetched via arxiv HTML) — UC San Diego paper introducing "modal-mixed CoT": interleaves text tokens with compact visual "sketch" embeddings generated by a diffusion-based latent decoder conditioned on VLM hidden states. VLM's own vision encoder is reused as semantic anchor; 256 → 32 compressed tokens via average pooling; `<START>`/`<END>` tokens trigger modal switching. Two-stage: SFT (joint text + diffusion L2 loss, λ=1.0) → GRPO. Results: V* Attribute 80.2%, Spatial 78.9%; +35–42pp over Qwen3-VL-4B baseline. Key finding: RL degrades abstract logic tasks (LogicVista Spatial 31.6% SFT → 25.3% RL). Bypass vulnerability unverified — uses own encoder not expert transformations.
Pages created: `wiki/sources/modal-mixed-cot-latent-embeddings.md`
Pages updated: `wiki/concepts/visual-reasoning-in-vlms.md` (paradigm 9 expanded with Modal-Mixed CoT), `wiki/analyses/vlm-reasoning-training-findings.md` (new training approach + sources), `wiki/concepts/continuous-visual-tokens.md` (diffusion decoder variant added), `wiki/concepts/lmrm-roadmap.md` (Stage 3 sub-types + mapping table), `wiki/sources/whats-holding-back-latent-visual-reasoning.md` (related page link), `wiki/index.md`
Key additions: Modal-Mixed CoT established as a parallel track to Mirage in self-generated latent reasoning — diffusion decoder vs cosine distillation. RL-degrading-abstract-logic finding is a new nuance in the RL training landscape. Bypass status remains open, adding to the growing need for causal verification across all latent approaches.

## [2026-05-23] query | VLM Reasoning Training: Key Findings

Answered question about findings for models and training VLMs with reasoning. Synthesized root problem (attention imbalance), latent bypass and collapse findings (4 models tested, accuracy unchanged with dummy tokens, 3.3% oracle retrieval), and 4 training approaches (CoVT, Mirage two-stage distillation+GRPO, ICoT, AdaptVis). Filed result as `wiki/analyses/vlm-reasoning-training-findings.md`.

## [2026-05-24] lint
Issues found: 5 total — 0 contradictions, 0 orphans, 1 stale analysis page, 3 missing cross-references, 1 stale entity
Fixed: all 5
- `analyses/visual-thinking-techniques.md`: added Modal-Mixed CoT, PEARL, VaLR paradigm rows to comparison table; added Modal-Mixed CoT, PEARL, VaLR, LaCoT rows to LMRM mapping table; updated Key Takeaway to reflect VaLR's 52.9% VSI-Bench result; added 4 new sources to header list
- `analyses/vlm-reasoning-training-findings.md:153`: linked OmniSpatial plaintext to `[[sources/omnispatial-benchmark]]`
- `sources/mcot-deep-thinking-survey.md`: added Note (updated 2026-05-24) after GRPO finding pointing to LaCoT's degradation result; added lacot cross-link to Connections
- `analyses/covt-limitations-and-research-directions.md`: added PEARL bypass-immune alternative paragraph to Limitation 0
- `entities/qwen2-5-vl.md`: added "Role in LaCoT" section; added Qwen3-VL-4B note to Notes; updated header to include lacot
Flagged for new sources: none — all gaps resolved with existing wiki content

## [2026-05-24] lint | Missing entity and concept pages
Issues found: 3 missing pages identified by entity audit (VSI-Bench, V*Bench, GRPO)
Fixed: all 3 created
- `entities/vsi-bench.md`: cross-paper leaderboard (VaLR-M 52.9% → Monet 14.0%); sub-task gains; explains why static injection collapses on multi-view
- `entities/v-star-bench.md`: Attribute + Spatial subtask results; PEARL 81.5%, Modal-Mixed CoT 80.2%/78.9%; bypass intervention results
- `concepts/grpo.md`: algorithm description; 14-page mention count; when it works (spatial) vs. degrades (abstract logic); GFlowNet alternative; task-dependency table
Back-links added to: `valr-vision-aligned-latent-reasoning`, `pearl-predictive-embedding-alignment`, `whats-holding-back-latent-visual-reasoning`, `lacot-latent-chain-of-thought`, `modal-mixed-cot-latent-embeddings`
Index updated with all 3 new pages
3 new + 7 updated files, 40 chunks re-embedded
