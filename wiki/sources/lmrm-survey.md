# Perception, Reason, Think, and Plan: A Survey on Large Multimodal Reasoning Models

**Paper**: Perception, Reason, Think, and Plan: A Survey on Large Multimodal Reasoning Models  
**Authors**: Yunxin Li, Zhenyu Liu, Zitao Li, Xuanyu Zhang et al.  
**Affiliation**: Harbin Institute of Technology  
**arXiv**: 2505.04921 (May 2025)  
**Repository**: https://github.com/HITsz-TMG/Awesome-Large-Multimodal-Reasoning-Models  
**Raw**: `raw/2505.04921.pdf`  
**Date ingested**: 2026-05-23

---

## Summary

This survey reviews the Large Multimodal Reasoning Model (LMRM) landscape across 540+ publications, proposing a **four-stage developmental roadmap** that traces the field's evolution from task-specific modular systems to prospective native multimodal reasoning agents. The roadmap is the paper's primary contribution: it provides a taxonomy that unifies the fragmented literature under a coherent developmental arc.

The four stages mirror a cognitive progression — from implicit perception-driven reasoning (Stage 1) through fast System-1 reasoning (Stage 2) and slow deliberative System-2 reasoning (Stage 3), toward autonomous agentic behavior (Stage 4). Each transition is driven by the limitations of the prior stage: modular systems couldn't generalize, short CoT couldn't handle abstraction, and current long-reasoning systems still lack genuine cross-modal integration and interactive adaptation.

The survey also covers 60+ benchmarks across five evaluation dimensions (multimodal understanding, generation, reasoning, planning, and evaluation methodology) and identifies four key research directions for the prospective Stage 4 systems. A companion GitHub repository tracks the literature.

---

## Key Points

### Four-Stage Roadmap

- **Stage 1 — Perception-Driven Modular Reasoning**: Task-specific modules with implicit reasoning (NMN, HieCoAtt, MCB, SANs, DMN). Later: dual-encoder contrastive (ViLBERT, CLIP) → single-transformer unified (VisualBERT, BLIP-2) → VLM-based implicit (LLaVA, MiniGPT-4, Qwen-VL). Reasoning remains largely implicit; requires separate task-specific modules.

- **Stage 2 — Language-Centric Short Reasoning (System-1)**: Multimodal CoT emerges. Three approaches: (1) prompt-based MCoT (VoT, PKRD-CoT, CoTDet), (2) structural reasoning — rationale construction (Multimodal-CoT, T-sciq), defined procedures (TextCoT, Audio-CoT), modality-specific grounding (DCoT, DDCoT), (3) externally augmented (RAG systems, visual experts like VISPROG). Fast, bounded-task reasoning.

- **Stage 3 — Language-Centric Long Reasoning (System-2)**: Extended deliberative chains. Sub-types: cross-modal reasoning (ICoT, FAST, MVoT), Multimodal-O1 (OpenAI-o1, Mulberry, LlamaV-o1), Multimodal-R1 (DeepSeek-R1 variants with RL). CoVT and Mirage are Stage 3 approaches keeping reasoning in non-text representational spaces.

- **Stage 4 — Native LMRMs (Prospective)**: Unified multimodal representation spaces; omni-modal understanding; agentic long-horizon planning. Current exemplars: OpenAI o3/o4, Gemini 2.0, Qwen2-Omni, MiniCPM-o 2.6, embodied systems (EmbodiedGPT, RAGEN).

### Core Insight: Language-Centric Designs Create Bottlenecks

Current LMRMs retrofit language models with auxiliary modality processors. Stage 4 requires natively unified representation and inference — not projecting everything into text space. This directly corroborates the wiki's core tension: the lossy bottleneck created by projecting visual signals into language token space is a *structural* property of Stages 1–3, not a fixable bug.

### Research Directions for N-LMRMs

1. **Unified representations and cross-modal fusion** — move beyond modality-specific encoders to a unified space for smooth cross-modal synthesis
2. **Interleaved multimodal long CoT** — reasoning traces integrating visual, auditory, and linguistic modalities within extended thought sequences
3. **Learning from world experiences** — closed-loop training through simulated or physical interaction for better generalization
4. **Data synthesis** — generating synthetic training data for holistic reasoning and planning across modalities

### Key Benchmarks Catalogued

| Category | Key Benchmarks |
|---|---|
| General visual understanding | VQA-v2, GQA, OK-VQA, MMBench, MMVet |
| Visual reasoning | ScienceQA, MathVista, ChartQA, CV-Bench |
| Document/OCR | DocVQA, TextVQA |
| Video | TVQA, ActivityNet-QA |
| Audio | MMAU, AudioSet |
| GUI/Embodied planning | WebShop, AI2-THOR, Habitat |

---

## Connections

- [[concepts/lmrm-roadmap]] — the four-stage roadmap as a standalone concept page
- [[concepts/visual-reasoning-in-vlms]] — wiki's existing paradigm taxonomy; now mappable to LMRM Stages 2–3
- [[analyses/visual-thinking-techniques]] — paradigm comparison; CoVT and Mirage are Stage 3 approaches
- [[sources/covt-chain-of-visual-thought]] — Stage 3 continuous visual token reasoning
- [[sources/mirage-machine-mental-imagery]] — Stage 3, moving toward Stage 4 (self-generated latents, no external experts)
- [[sources/icot-interleaved-modal-chain-of-thought]] — Stage 3 cross-modal reasoning (explicitly named in survey)
- [[sources/whats-holding-back-latent-visual-reasoning]] — explains why Stage 3 systems fail to use latent tokens causally
- [[analyses/vlm-reasoning-training-findings]] — training findings are now contextualized within Stage 3
