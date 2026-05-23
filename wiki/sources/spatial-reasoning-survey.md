# Spatial Reasoning in MLLMs: A Survey of Tasks, Benchmarks and Methods

**Paper**: Spatial Reasoning in Multimodal Large Language Models: A Survey of Tasks, Benchmarks and Methods  
**Authors**: Weichen Liu, Qiyao Xue, Haoming Wang, Xiangyu Yin, Boyuan Yang, Wei Gao  
**Affiliation**: University of Pittsburgh  
**arXiv**: 2511.15722 (Nov 2025)  
**Raw**: `raw/2511.15722.pdf`  
**Date ingested**: 2026-05-23

---

## Summary

This survey approaches spatial reasoning in MLLMs through a **cognitive lens** rather than a modality-based classification. The core contribution is a three-dimensional taxonomy that organizes spatial tasks by cognitive function and reasoning complexity, mapping existing benchmarks and methods onto this framework to reveal critical gaps.

The survey identifies three root architectural failure modes of MLLMs in spatial reasoning — the projection bottleneck, statistical correlations over physical constraints, and frame-of-reference instability — and catalogs training-based and inference-based improvement methods. The cognitive perspective reveals that true spatial intelligence requires mental simulation of transformations (rotation, translation, perspective change), capabilities that remain largely absent in current models.

A key theoretical framing: human spatial cognition relies on specialized neural circuits (hippocampal-entorhinal grid and place cells) encoding allocentric maps and metric structure. MLLMs lack equivalent internal coordinate systems, explaining persistent failures on tasks requiring mental navigation or geometric reasoning from novel viewpoints.

---

## Key Points

### Three-Dimensional Taxonomy

Spatial tasks are classified along three orthogonal axes:

| Dimension | Values |
|---|---|
| **Frame of Reference** | Intrinsic (object's own structure) vs. Extrinsic (relative to other objects/environment) |
| **Type of Information** | Qualitative (discrete: "left of", "behind") vs. Quantitative (continuous: distance, angle, volume) |
| **Nature of Task** | Static (fixed scene) vs. Dynamic (mental simulation of transformations) |

**Five cognitive categories** (combinations):
1. Intrinsic–Qualitative–Static — internal object structure ("chair's back is above its seat")
2. Extrinsic–Qualitative–Static — most common; object arrangements with relational terms
3. Quantitative–Static — metric reasoning requiring precise continuous data
4. Intrinsic–Qualitative–Dynamic — mental transformation of object parts (folding, rotating)
5. Extrinsic–Qualitative–Dynamic — simulating changes in object relationships or viewpoint shifts

### Four Levels of Reasoning Complexity

- **Level 1** — Direct Perception: retrieve explicit info without inference
- **Level 2** — Single-Step Inference: basic deduction of spatial relationships
- **Level 3** — Multi-Step Chaining: conclusions feed into premises sequentially
- **Level 4** — Advanced Synthetic: complex scenarios testing generalization and integration

### Three Root Failure Modes

1. **Projection Bottleneck**: 2D encoders tokenize images into patches optimized for semantic alignment, not 3D geometry. Depth ordering and orientation are weakly preserved after flattening to discrete tokens. (Closely related to [[concepts/visual-attention-in-vlms]] attention imbalance; complementary cognitive framing of the same structural problem.)

2. **Statistical Correlations Over Physical Constraints**: Models exploit semantic co-occurrence patterns rather than obeying geometric regularities. Performance drops sharply on metric or counterfactual queries. Models "prioritize salient semantics over geometry-bearing regions."

3. **Frame-of-Reference Instability**: No explicit mechanism for managing egocentric vs. allocentric reference frames. Multi-view localization causes "left/right" and "front/behind" confusion. Models lack persistent scene memory across viewpoints.

### Benchmark Gaps

- **Quantitative metric reasoning is underrepresented**: Most "quantitative" benchmarks only test counting (Level 1), not distance/angle/volume estimation
- **Dynamic reasoning is frontier territory**: Fewest benchmarks for mental simulation and perspective-taking tasks
- **Extrinsic–Qualitative–Static dominates**: Benchmarks over-index on current model strengths, masking true capability gaps

### Key Benchmarks by Category

| Category | Benchmarks |
|---|---|
| Text-only spatial | SPARTQA, SpatialEval(TQA), BaBi, StepGame |
| Image/Video | Super-CLEVR-3D, MindCube, Q-Spatial Bench, STARE, VSI-bench |
| 3D/Embodied | ScanRefer, Multi3DRefer, SQA3D, Chat-3D Dataset |

### Methods to Improve Spatial Reasoning

**Training-based**:
- *Spatial-aware module training*: augment encoders with 3D positional embeddings (LLaVA-3D, Scene-LLM, PointLLM, SR-3D)
- *Synthetic data fine-tuning*: use simulators (Habitat, Infinigen) for controllable scene generation (SpatialVLM)
- *RL for reasoning*: GRPO/RLHF for multi-step spatial planning (Pixel Reasoner, SpaceR, ManipLVM-R1)

**Inference-based**:
- *CoT variants*: SpatialCoT, Visualization-of-Thought (VoT) — no parameter updates
- *Explicit spatial representations*: scene graphs, program synthesis, coordinate systems (SG-Nav, VADAR, Agent3D-Zero)

**Hybrid**: Spatial-MLLM, MVoT — combine architectural improvements with CoT

### Future Research Priorities

1. Higher-quality datasets for metric reasoning and dynamic mental simulation
2. Architectures with explicit geometric structure preservation (not just semantic alignment)
3. Spatially-grounded pretraining objectives beyond statistical co-occurrence
4. Persistent scene memory mechanisms for multi-view consistency
5. Physical constraint integration with commonsense reasoning

---

## Connections

- [[concepts/spatial-reasoning-taxonomy]] — the 3D taxonomy and failure modes as a standalone concept page
- [[concepts/visual-attention-in-vlms]] — attention imbalance is the mechanistic account of failure mode #1 (projection bottleneck)
- [[sources/why-spatial-reasoning-hard-vlms]] — AdaptVis paper: mechanistic root cause (attention geometry), directly complementary
- [[concepts/visual-reasoning-in-vlms]] — paradigm taxonomy; benchmark table updated
- [[sources/covt-chain-of-visual-thought]] — CoVT's expert-aligned tokens directly address projection bottleneck (depth, edges, segmentation)
- [[sources/lmrm-survey]] — spatial reasoning is a Stage 2–3 challenge in the LMRM roadmap
