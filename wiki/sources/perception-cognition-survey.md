# From Perception to Cognition: A Survey of Vision-Language Interactive Reasoning in MLLMs

**Paper**: From Perception to Cognition: A Survey of Vision-Language Interactive Reasoning in Multimodal Large Language Models  
**Authors**: Chenyue Zhou, Mingxuan Wang, Yanbiao Ma et al.  
**Affiliation**: Renmin University of China, Xiamen University, HKUST, NTU  
**arXiv**: 2509.25373 (Sep 28, 2025)  
**Raw**: `raw/2509.25373.pdf`  
**Date ingested**: 2026-05-23

---

## Summary

This survey argues that current MLLMs suffer from a fundamental disconnect between **perception** (visual information extraction) and **cognition** (reasoning): "the ability to process pixels does not yet confer the ability to construct a coherent, credible internal world model." Hallucination is reframed as a symptom of this deeper gap rather than an isolated defect.

The core contribution is a **Perception-to-Cognition framework** that deconstructs interactive reasoning into two explicitly interconnected layers. Unlike the LMRM four-stage roadmap ([[sources/lmrm-survey]]) which organizes the field historically, this framework is functional — it asks what computation a model must perform (extract → align → decompose → inject evidence) rather than when a method appeared. The two taxonomies are complementary.

Methods are organized into four categories: (1) low-level visual perception enhancement, (2) vision-language alignment, (3) problem decomposition, and (4) dynamic reasoning with evidence injection. Category 4 — evidence injection — is the most directly relevant to the wiki's existing content, distinguishing endogenous methods (internal attention mechanisms, no external tools) from exogenous methods (tool-calling).

---

## Key Points

### Perception-to-Cognition Framework

**Perception Layer** — foundational abilities:
- Accurately extract visual information from images
- Encode raw visual data into semantically meaningful representations
- Recognize objects, attributes, spatial relationships, contextual associations
- Achieve fine-grained vision-text alignment
- Provide reliable visual evidence for subsequent reasoning

**Cognition Layer** — higher-order capabilities:
- Proactive, goal-oriented, multi-step reasoning
- Determining *when* and *where* to examine visual information
- Dynamically assessing information sufficiency at each step
- Forming "observe-think-verify" closed-loop cycles

**Hallucination root cause**: traced to decoupling between perception and cognition — linguistic priors dominate over visual facts, especially in long-chain reasoning. Not an isolated defect.

### Four Method Categories

**1. Low-Level Visual Perception Enhancement**
- Single-encoder optimization: EVA-CLIP, SigLip, DINOv2, DIVA
- Multi-encoder integration: static fusion (Eyes Wide Shut, Prismatic VLMs, SPHINX), MoE routing (MoME, MoVA), knowledge distillation (Radio, UNIC)

**2. Vision-Language Alignment**
- Projection layer improvements: Honeybee, Ovis2.5, LLaVA-ST
- Task-specific fine-tuning: MATCHA, LLaVA-Med, ChartInstruct
- Dynamic visual search: V*, DyFo, FaST

**3. Problem Decomposition**
- Imitation learning: Multimodal-CoT, Visual CoT, Visual Grounded Reasoning
- Curriculum learning (easy-to-hard): LLaVA-CoT, LlamaV-o1
- Preference learning: V-DPO, VLM-R1, Visual-RFT (GRPO)
- Inference-time search: Tree of Thoughts variants, VisuoThink, Socratic-MCTS

**4. Dynamic Reasoning with Evidence Injection** ← most wiki-relevant
- *Endogenous (internal attention)*:
  - Single forward pass: CVC, **ICoT**, MINT-CoT, Look-back
  - Multiple forward passes: CogCoM, **DeepEyes**, **Pixel Reasoner**, SIFThinker, CMMCoT
- *Exogenous (external tool calling)*:
  - In-context learning: MM-ReAct, **ViperGPT**, CLOVA, **Visual Sketchpad**
  - Fine-tuning: LLaVA-Plus, TACO, VTool-R1

### Critical Findings

1. **Process supervision > outcome supervision**: supervising correctness of intermediate reasoning steps yields **+4–10 percentage points** over outcome-only supervision (Best-of-N sampling experiments)
2. **Interleaved CoT > sequential**: generating text reasoning and visual evidence jointly outperforms text-then-vision or vision-then-text approaches
3. **Dynamic > static encoding**: multiple forward passes with targeted visual re-encoding outperforms single static encoding for complex reasoning
4. **Evidence grounding is necessary**: intermediate reasoning steps grounded in verifiable visual evidence (coordinates, boxes, masks) significantly reduce hallucination

### Failure Modes

- Decoupling between linguistic priors and visual facts in long-chain reasoning
- Over-reliance on language patterns without visual grounding
- Inability to adjust reasoning strategy based on problem complexity
- Loss of fine-grained visual detail when decomposition happens at text level only
- Insufficient handling of symbolic/structured content (geometry, charts, diagrams)

### Benchmarks Highlighted

| Domain | Key Benchmarks |
|---|---|
| General VQA | VQA-v2, GQA, VCR, OK-VQA |
| Math/Science | ScienceQA, MathVista, MMMU, MathVerse, MDK12-Bench |
| Charts/Docs | ChartQA, ChartGemma |
| Medical | MedFutureBench, PathQA |

Performance leaders: Gemini 2.5 Pro (proprietary), InternVL3 and Qwen2.5-VL (open-source).

### Future Directions

1. Latent space reasoning beyond pixel space
2. Generative reasoning for richer perceptual representations
3. Unified tool-augmented reasoning APIs
4. Bridging perception-cognition gap architecturally (perceptual quality as prerequisite for cognition)
5. Robustness under distribution shift
6. Efficiency / compute trade-offs

---

## Connections

- [[concepts/perception-cognition-framework]] — the two-layer framework as a standalone concept page
- [[sources/lmrm-survey]] — complementary taxonomy: LMRM roadmap is historical (4 stages); this is functional (perception → cognition)
- [[sources/icot-interleaved-modal-chain-of-thought]] — ICoT classified here as endogenous single-forward-pass evidence injection
- [[concepts/visual-reasoning-in-vlms]] — paradigm taxonomy; evidence injection sub-taxonomy (endogenous/exogenous) added
- [[analyses/vlm-reasoning-training-findings]] — process supervision and dynamic encoding findings add to training section
- [[sources/covt-chain-of-visual-thought]] — CoVT is endogenous single-forward-pass in this survey's terms
- [[sources/mirage-machine-mental-imagery]] — Mirage addresses the latent space reasoning future direction
- [[concepts/spatial-reasoning-taxonomy]] — frame-of-reference instability failure mode maps onto this survey's "linguistic priors over visual facts"
