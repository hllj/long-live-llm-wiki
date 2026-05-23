# From Perception to Reasoning: Deep Thinking Empowers MLLMs

**Paper**: From Perception to Reasoning: Deep Thinking Empowers Multimodal Large Language Models  
**Authors**: Wenxin Zhu, Andong Chen, Yuchen Song, Kehai Chen, Conghui Zhu, Ziyan Chen, Tiejun Zhao  
**Affiliation**: Harbin Institute of Technology (Shenzhen), Global Tone Communication Technology  
**arXiv**: 2511.12861 (Nov 17, 2025; revised Nov 27, 2025)  
**Raw**: `raw/2511.12861.pdf`  
**Date ingested**: 2026-05-23

---

## Summary

A systematic 44-page review of **Multimodal Chain-of-Thought (MCoT)** reasoning, covering how CoT extends from language models to the multimodal domain to address two core MLLM limitations: implicit reasoning without interpretable steps, and a perception-reasoning disconnect requiring cross-modal integration.

The survey organises MCoT methods along three dimensions: (1) **CoT paradigms** — the topological structure of the reasoning chain (chain, tree, graph); (2) **post-training approaches** — SFT, RL, and their combination; (3) **inference strategies** — prompting, search (MCTS/beam), self-refinement, RAG, and agent assistance.

The theoretical lens is the System 1 → System 2 shift: CoT moves reasoning from fast intuitive pattern matching to slow deliberative step decomposition, activating latent capabilities from pretraining. Process supervision — extending the supervisory signal across the full reasoning chain rather than only the final answer — is the key mechanism enabling this shift.

---

## Key Points

### Three-Dimensional MCoT Framework

**Dimension 1 — CoT Paradigms (topology)**

| Structure | Approach | Trade-off |
|---|---|---|
| **Chain** (linear) | Sequential steps; most common | Efficient but brittle — errors propagate |
| **Chain-of-Thought Self-Consistency** | Multiple independent chains; scoring selects best | Reduces compounding errors; higher compute |
| **Tree of Thoughts (ToT)** | Expandable solution space; backtracking | Enables error correction; search overhead |
| **Graph of Thoughts (GoT)** | Concepts as nodes; multi-parent, cycles | Aggregates parallel reasoning; most expressive |

Multimodal-specific variants: **ICoT** (images as intermediate reasoning content; hybrid text-image semantic spaces), **MVoT/Visual Sketchpad** (generate visual representations to reduce linguistic reasoning load), **VoT** (video CoT over temporal checkpoints), **CoCoT** (multi-image comparison chains).

**Dimension 2 — Post-Training Approaches**

| Paradigm | Mechanism | Limitation |
|---|---|---|
| **SFT only** | Behavioral cloning of expert reasoning | Stable; may not generalise beyond training patterns |
| **RL only** | Goal-driven exploration with reward signals (DPO, GRPO) | Exploratory; needs stable initialisation |
| **SFT + RL combined** | SFT establishes patterns; RL optimises them | Best results; ARES alternates stages |

Curriculum learning (easy-to-hard: LlamaV-o1) improves SFT. Vision-R1's Progressive Thinking Suppression Training restricts reasoning length initially then relaxes — forces conciseness first.

**Key finding**: Combined SFT+RL outperforms either alone. Data quality is the primary bottleneck — few explicitly annotated multimodal CoT datasets exist.

> **Note (updated 2026-05-24):** [[sources/lacot-latent-chain-of-thought]] adds an important nuance: **GRPO specifically can underperform zero-shot and SFT** on complex visual reasoning benchmarks (MathVista/MathVerse/MMMU). Its KL penalty constrains exploration, blocking the model from discovering better-than-reference reasoning paths. GFlowNet training (RGFN) — which samples reward-proportionally without KL constraints — outperforms GRPO by 5.7–6.5pp. The "RL beats SFT" finding is robust, but the choice of RL algorithm matters more than this survey indicates.

**Key datasets**: MathV360K (360K), LLaVA-CoT-100K (834K), MMathCoT1M (1M), Visual CoT (438K), Emma-X (60K embodied trajectories).

**Dimension 3 — Inference Strategies**

| Strategy | Examples | Mechanism |
|---|---|---|
| **CoT Prompting** | "Let's think step by step", BBA, ICoT | Zero-parameter; activates pre-trained reasoning |
| **Beam Search** | LLaVA-CoT (stage-level) | Retains top-k paths; misses global optima |
| **MCTS** | AR-MCTS, CoMCTS, AStar | Selection→expansion→simulation→backprop cycle |
| **Best-of-N** | SPECULATIVE REJECTION | Generates N outputs; halts low-scorers early |
| **Self-Refinement** | R3V, EVLM | think→output→review→refine cycles; no param updates |
| **RAG/Knowledge** | KAM-CoT, MR-MKG | Knowledge graph integration; reduces hallucination |
| **Agent Assistance** | Insight-V, InfiGUIAgent | Multi-agent roles (planner/executor/verifier) |

**Inference-time scaling finding**: Search (MCTS, beam) and self-refinement substantially improve robustness *without parameter updates* — reasoning capability can be unlocked at inference time.

### Process Supervision Mechanism

CoT enables **process-based supervision** throughout training and inference — supervisory signal extends across the full chain, not just the final answer:
- *Training*: detailed reasoning paths in CoT-annotated datasets
- *Inference*: CoT prompting (soft supervision), Process Reward Models, self-optimisation

This directly corroborates the +4–10pp process supervision finding in [[sources/perception-cognition-survey]].

### Evaluation Benchmarks (6 categories)

| Category | Key Benchmarks |
|---|---|
| Mathematical/Logical | MathVista, MATH-Vision, We-Math, LogicVista, MuCR |
| Spatiotemporal/Directional | PulseCheck457, GSR-BENCH, CDR, TOMATO, DriveLMM-o1 |
| Vision-Language Transformation | Scene understanding, cross-modal grounding |
| Sequential/Multi-Image | Compositional reasoning across visual inputs |
| Multimodal Integrated | Commonsense, knowledge integration |
| Reasoning Process Quality | Intermediate step quality, not just final answer |

### Limitations Identified

1. Data scarcity — few high-quality CoT annotation datasets; construction is labour-intensive
2. Computational cost — MCTS/ToT are expensive at inference; practical deployment constraint
3. Single-chain brittleness — linear structures remain vulnerable to step-level errors
4. Modality imbalance — most work is vision-language only; audio/video/point cloud limited
5. Evaluation gaps — process-quality metrics underdeveloped vs. outcome-based
6. Domain generalization — models trained on math/science struggle with novel domains

---

## Connections

- [[concepts/visual-reasoning-in-vlms]] — CoT topology (chain/tree/graph) adds structure to existing paradigm taxonomy
- [[concepts/lmrm-roadmap]] — this paper is the detailed account of Stage 3 (System-2 long reasoning); SFT/RL training paradigms fill in the stage
- [[sources/lmrm-survey]] — Stage 3 of the LMRM roadmap; this paper provides the granular MCoT view
- [[analyses/vlm-reasoning-training-findings]] — SFT+RL > either alone; data scarcity bottleneck; inference-time scaling added
- [[sources/icot-interleaved-modal-chain-of-thought]] — ICoT classified as chain-paradigm method creating hybrid text-image semantic spaces
- [[sources/perception-cognition-survey]] — process supervision finding (+4–10pp) corroborated by this paper's mechanism analysis
- [[concepts/perception-cognition-framework]] — problem decomposition (Dimension 2 of this survey) maps to cognition layer; evidence injection via inference strategies
- [[sources/lacot-latent-chain-of-thought]] — nuances the GRPO finding: GRPO underperforms zero-shot on MathVista/MathVerse/MMMU; GFlowNet (RGFN) outperforms by 5.7–6.5pp; BiN replaces Best-of-N without external reward models
