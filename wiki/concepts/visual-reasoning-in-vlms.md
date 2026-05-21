# Visual Reasoning in VLMs

An overview of how Vision-Language Models reason about visual content, the dominant paradigms, and their trade-offs. This page tracks the evolving landscape of approaches.

**Primary source**: [[sources/covt-chain-of-visual-thought]]

---

## The core tension

VLMs project visual input into a language-centric token space to leverage LLM reasoning capabilities. This works well for semantic and logical tasks but creates a fundamental lossy bottleneck for perception-intensive tasks: continuous visual signals (depth, edges, geometry, spatial layout) are poorly representable as discrete text tokens.

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

---

## Key benchmarks for vision-centric reasoning

| Benchmark | What it tests |
|---|---|
| CV-Bench (Count, Depth, Distance subtasks) | Counting, depth ordering, spatial distance |
| BLINK | Perceptual reasoning (relative depth, visual correspondence, etc.) |
| RealWorldQA | Real-world visual question answering |
| HRBench (4K, 8K) | High-resolution image perception |
| MMVP | Visual perception and reasoning |
| MME-RealWorld | Real-world multimodal evaluation |
| V* Bench | Guided visual search |
| MMStar-P (Coarse/Fine-grained Perception, Instance Reasoning) | Perception-aligned subsets |

---

## Open problems

1. **Interleaved multimodal reasoning**: Seamlessly mixing text and visual thoughts mid-chain (not just one visual block followed by text answer)
2. **Design space of visual token types**: Only a few expert combinations explored; hybrid or domain-specific experts may help
3. **Scaling**: Most work done at 7–13B scale; behaviour at frontier scale is unclear
4. **Non-perception tasks**: Visual reasoning that requires commonsense + perception simultaneously remains challenging
