# LMRM Developmental Roadmap

A four-stage framework for understanding how Large Multimodal Reasoning Models (LMRMs) have evolved and where the field is heading. Proposed in [[sources/lmrm-survey]] (Harbin Institute of Technology, 2025), covering 540+ publications.

---

## Overview

The roadmap parallels a cognitive progression: implicit perception → fast System-1 → slow deliberative System-2 → autonomous agentic reasoning. Each stage is defined by where reasoning happens (modules, language, unified space) and how it is structured (implicit, short-chain, long-chain, interactive).

---

## Stage 1 — Perception-Driven Modular Reasoning

**Era**: ~2016–2022  
**Characteristic**: reasoning is implicit, embedded in specialized perception modules. No explicit intermediate reasoning steps.

**Modular networks**: NMN (dynamically assembled task-specific modules), HieCoAtt, MCB, SANs, DMN, MAC, MuRel, MCAN — required "separate, task-specific reasoning modules" with limited cross-task generalizability.

**VLM evolution within Stage 1** (three sub-paradigms):
1. **Dual-encoder contrastive** — parallel streams with cross-modal attention (ViLBERT, LXMERT, CLIP)
2. **Single-transformer unified** — multimodal inputs in one architecture (VisualBERT, UNITER, BLIP-2)
3. **MLLM implicit reasoning** — vision-encoder + LLM projection (LLaVA, MiniGPT-4, Qwen-VL family)

**Limitation**: reasoning remains largely implicit; models excel at bounded tasks but struggle with abstraction, compositionality, and multi-step planning.

---

## Stage 2 — Language-Centric Short Reasoning (System-1)

**Era**: ~2022–2024  
**Characteristic**: Multimodal Chain-of-Thought (MCoT) externalizes implicit reasoning into explicit intermediate steps in language. Fast, intuitive, bounded.

**Three approaches**:

1. **Prompt-based MCoT** — VoT (spatial-temporal graphs for video), PKRD-CoT (autonomous driving), CoTDet (multi-level object detection prompting)

2. **Structural reasoning**:
   - *Rationale construction*: Multimodal-CoT (decoupled rationale + answer), T-sciq (teacher LLM with varying complexity), G-CoT (driving rationale → visual signal)
   - *Defined procedures*: TextCoT (overview → localization → fine-grained), Audio-CoT (multi-paradigm audio)
   - *Modality-specific grounding*: DCoT (bounding-box + semantic retrieval), DDCoT (query decomposition), AVQA-CoT

3. **Externally augmented** — RAG systems (KAM-CoT, Chain-of-Action), visual experts (VISPROG, CVR-LLM), search algorithms (HoT, AGoT)

**Limitation**: short chains "struggle with abstraction, compositionality, and planning." Unstructured prompting hits diminishing returns.

---

## Stage 3 — Language-Centric Long Reasoning (System-2)

**Era**: 2024–present  
**Characteristic**: extended deliberative chains; reinforcement learning; cross-modal representations in the reasoning chain. Still fundamentally language-centric but augmented.

**Sub-types**:

- **Cross-modal reasoning**: ICoT (attention-driven patch re-injection, [[sources/icot-interleaved-modal-chain-of-thought]]), FAST, MVoT — leverage visual or auditory signals as joint reasoning substrates alongside text
- **Continuous visual token reasoning**: CoVT ([[sources/covt-chain-of-visual-thought]]) — generates compact expert-aligned continuous tokens (seg, depth, edge, DINO) interleaved with text in the think chain
- **Self-generated latent tokens**: Mirage ([[sources/mirage-machine-mental-imagery]]) — VLM recasts own hidden states as latent visual tokens via two-stage distillation + GRPO; most Stage 4-adjacent approach; Modal-Mixed CoT ([[sources/modal-mixed-cot-latent-embeddings]]) — parallel approach using a diffusion decoder instead of cosine distillation; 32 compressed latent tokens; `<START>`/`<END>` modal-switching tokens learned via GRPO
- **JEPA-style trajectory distillation**: PEARL ([[sources/pearl-predictive-embedding-alignment]]) — Stage 3 training, Stage 2 inference; internalizes expert tool-use trajectories into model weights via predictive embedding alignment; no latent tokens at inference → structurally immune to bypass problem; unique position in the roadmap
- **Per-step visual checkpointing**: VaLR ([[sources/valr-vision-aligned-latent-reasoning]]) — REPA-aligned latent tokens injected before every reasoning step; only approach enabling test-time scaling for visual reasoning; Stage 3→4 boundary
- **GFlowNet CoT training**: LaCoT ([[sources/lacot-latent-chain-of-thought]]) — GFlowNets with reference-guided filtering (RGFN) to sample reward-proportional text reasoning chains; BiN (Bayesian Inference over N) replaces BoN; GRPO shown to degrade on complex visual reasoning
- **Multimodal-O1**: OpenAI-o1, Mulberry, LlamaV-o1, RedStar — near-human-level performance on cognitively demanding tasks through extended deliberation
- **Multimodal-R1**: DeepSeek-R1 variants with RL-enhanced reasoning — agentic data, iterative feedback, improved planning robustness

**MCoT topology within Stage 3** ([[sources/mcot-deep-thinking-survey]]): reasoning chains vary in topological complexity — Chain (linear, most common, brittle) → Tree of Thoughts (backtracking, error correction) → Graph of Thoughts (multi-parent nodes, parallel aggregation). Training paradigm: SFT+RL combined outperforms either alone. Inference-time scaling (MCTS, self-refinement) improves robustness without parameter updates.

**Key failure mode in Stage 3**: [[sources/whats-holding-back-latent-visual-reasoning]] shows that in 4 tested Stage 3 latent models, latent tokens are causally bypassed at inference — accuracy unchanged with dummy tokens. Root cause: crop-based training data provides no marginal information value. Non-redundant intermediates (expert transformations, masked inputs) are required for latent tokens to be genuinely used.

---

## Stage 4 — Native LMRMs (N-LMRMs, Prospective)

**Era**: emerging 2025+  
**Characteristic**: unified multimodal representation spaces; omni-modal understanding; agentic long-horizon planning; environment-driven interactive reasoning. Reasoning is no longer retrofitted onto language models.

**Current exemplars** (partial):
- OpenAI o3/o4, Gemini 2.0 Flash
- Kimi-VL-Thinking, Qwen2-Omni, MiniCPM-o 2.6
- Embodied: EmbodiedGPT, ManipLLM, RAGEN

**Research directions needed**:
1. Unified representations and cross-modal fusion — beyond modality-specific encoders
2. Interleaved multimodal long CoT — visual + audio + text within extended thought sequences
3. Learning from world experiences — closed-loop training via simulated/physical interaction
4. Data synthesis — holistic reasoning/planning data across all modalities

---

## Mapping Wiki Approaches to the Roadmap

| Approach | Stage | Notes |
|---|---|---|
| Text-only CoT (Qwen3-VL-Thinking) | Stage 2–3 | Stage 2 if short; Stage 3 if extended with RL |
| Tool-augmented (ViperGPT) | Stage 2 (external augmentation) | Not end-to-end; ceiling bounded by tools |
| ICoT | Stage 3 (cross-modal) | Explicitly named in survey; plug-and-play |
| CoVT | Stage 3 (continuous visual) | Expert-aligned; non-redundant intermediates |
| Mirage | Stage 3 → Stage 4 boundary | Self-generated latents; most N-LMRM-adjacent |
| Modal-Mixed CoT | Stage 3 (self-generated latent) | Diffusion decoder variant; parallel track to Mirage |
| PEARL | Stage 3 training / Stage 2 inference | JEPA trajectory distillation; no latent tokens at inference; bypass-immune |
| VaLR | Stage 3 → Stage 4 boundary | Per-step REPA checkpointing; enables test-time scaling; beats GPT-4o on VSI-Bench |
| LaCoT | Stage 3 (System-2 CoT training) | GFlowNet training for diverse CoT; GRPO can degrade; BiN beats BoN by 13–18pp |
| AdaptVis | Stage 2–3 boundary | Inference-time; no new representation space |
| Aurora (discrete latent) | Stage 3 (early) | Discrete quantization limits information density |

---

## Related Pages

- [[sources/lmrm-survey]] — source paper proposing this roadmap
- [[concepts/visual-reasoning-in-vlms]] — wiki's paradigm taxonomy; now mappable to Stages 2–3
- [[analyses/visual-thinking-techniques]] — paradigm comparison; all approaches sit in Stages 2–3
- [[sources/whats-holding-back-latent-visual-reasoning]] — explains the key Stage 3 failure mode
- [[sources/mirage-machine-mental-imagery]] — most Stage 4-adjacent approach currently in wiki
