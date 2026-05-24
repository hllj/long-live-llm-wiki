# Spatial Reasoning Taxonomy for VLMs

A cognitive taxonomy for classifying spatial reasoning tasks in MLLMs, proposed in [[sources/spatial-reasoning-survey]] (University of Pittsburgh, Nov 2025). Provides a principled framework for diagnosing model failures and identifying benchmark gaps.

---

## Three Dimensions

Spatial tasks vary along three orthogonal cognitive axes:

### 1. Frame of Reference
- **Intrinsic**: Focus on an object's internal structure/properties (e.g., "the chair's back is above its seat")
- **Extrinsic**: Focus on relationships between objects or relative to the environment (e.g., "the chair is left of the table")

### 2. Type of Information
- **Qualitative**: Discrete, abstract spatial relations — "left of," "behind," "inside"
- **Quantitative**: Continuous, precise measurements — distance (metres), volume (cm³), angle (degrees)

### 3. Nature of Task
- **Static**: Fixed scene understanding; no transformation required
- **Dynamic**: Mental simulation of changes — rotation, translation, folding, perspective shift

---

## Five Cognitive Categories (Combinations)

| Category | Description | Example |
|---|---|---|
| Intrinsic–Qualitative–Static | Internal structure of a single object | "Which part of the chair is highest?" |
| Extrinsic–Qualitative–Static | Relational arrangement in fixed scenes | "Is the mug to the left of the book?" |
| Quantitative–Static | Metric reasoning with precise data | "How far is the car from the tree?" |
| Intrinsic–Qualitative–Dynamic | Mental transformation of object parts | "If you fold this net, which face is opposite the red one?" |
| Extrinsic–Qualitative–Dynamic | Simulating changes in object relationships or viewpoints | "After you rotate 90° left, what is now in front of you?" |

**Current benchmark distribution is heavily skewed toward Extrinsic–Qualitative–Static** — the category most aligned with current model strengths, which masks true capability gaps.

---

## Four Levels of Reasoning Complexity

- **Level 1 — Direct Perception**: Retrieve explicitly available spatial information without inference (e.g., counting objects)
- **Level 2 — Single-Step Inference**: Basic deduction (e.g., "A is left of B; is B right of A?")
- **Level 3 — Multi-Step Chaining**: Sequential reasoning where each conclusion feeds into the next premise
- **Level 4 — Advanced Synthetic**: Complex scenarios requiring generalization and integration across multiple spatial concepts

Most benchmarks cluster at Levels 1–2. Level 3–4 tasks remain poorly covered.

---

## Three Root Failure Modes

These are architectural/cognitive explanations for why MLLMs fail at spatial reasoning. They complement the mechanistic attention imbalance finding from [[sources/why-spatial-reasoning-hard-vlms]] and [[concepts/visual-attention-in-vlms]].

### 1. Projection Bottleneck
2D encoders tokenize images into patches optimized for **semantic alignment with language**, not faithful 3D geometry. Depth ordering and orientation are weakly preserved after flattening into discrete sequential tokens. "The physical world is characterized by continuous geometric structures; LLMs encode information as discrete, sequential tokens."

**Wiki connection**: this is the cognitive/representational framing of the same structural problem that [[sources/why-spatial-reasoning-hard-vlms]] explains mechanistically (attention geometry) and that [[sources/covt-chain-of-visual-thought]] addresses with continuous expert tokens.

### 2. Statistical Correlations Over Physical Constraints
Models exploit **semantic co-occurrence patterns** rather than obeying geometric regularities. Performance drops sharply on metric or counterfactual queries — scenarios where co-occurrence statistics don't help. Models "prioritize salient semantics over geometry-bearing regions."

**Wiki connection**: explains why benchmark gains don't transfer to novel spatial configurations; also relates to the bypass problem in [[sources/whats-holding-back-latent-visual-reasoning]] — models learn statistical shortcuts instead of relying on intermediate perceptual signals.

### 3. Frame-of-Reference Instability
No explicit mechanism for managing **egocentric vs. allocentric reference frames**. Multi-view localization causes "left/right" and "front/behind" confusion. Models lack persistent scene memory across viewpoints. Human cognition relies on hippocampal-entorhinal grid/place cells for allocentric maps — MLLMs have no equivalent internal coordinate system.

---

## Benchmark Gaps Revealed by the Taxonomy

| Gap | Why It Matters | Status |
|---|---|---|
| Quantitative metric tasks underrepresented | Most "quantitative" benchmarks only test counting (Level 1), not distance/angle/volume | Still open |
| Dynamic reasoning benchmarks scarce | Mental simulation tasks are frontier research with few evaluation resources | Partially addressed by OmniSpatial ([[sources/omnispatial-benchmark]]) |
| Non-egocentric perspective-taking rare | Allocentric/hypothetical viewpoints untested at scale | Addressed by OmniSpatial — models score only 32-48% here |
| Intrinsic structure tasks rare | Models seldom tested on object-internal spatial structure | Still open |
| Evaluation metrics inadequate | BLEU/ROUGE fail to capture semantic equivalence (e.g., "A left of B" ≡ "B right of A") | Still open |

**OmniSpatial empirical findings** ([[sources/omnispatial-benchmark]], 8,400 QA pairs, human baseline 92.63%):
- Best model (o3): 56.33% — **~36pp gap from human**
- Geometric/pattern reasoning: **20–40%** (near-random across all models — critical gap)
- Non-egocentric perspective-taking: **32–48%** (major bottleneck)
- Specialized spatial models fail to outperform general-purpose models on comprehensive benchmarks
- Manual training data (6.9K): **+7.82pp**; template data (200K): only **+1.29pp** — 6× quality advantage

---

## Improvement Methods

**Training-based**:
- Spatial-aware module training with 3D positional embeddings (LLaVA-3D, PointLLM)
- Synthetic data fine-tuning via simulators (SpatialVLM, Habitat)
- RL for multi-step spatial reasoning chains (SpaceR, Pixel Reasoner, ManipLVM-R1)
- **Progressive curriculum (SpatialLadder, [[sources/spatialladder]])**: Stage 1 localization → Stage 2 multi-modal spatial understanding → Stage 3 GRPO. Directly addresses projection bottleneck (grounding first) and frame-of-reference instability (multi-view training). Controlled experiment: +5% from bounding box hints, +4.5% from directional cues — proving perception grounding is the bottleneck, not reasoning capacity. 3B model beats GPT-4o by 20.8% on in-domain spatial benchmarks.

**Inference-based**:
- Spatial CoT prompting (SpatialCoT, Visualization-of-Thought)
- Explicit spatial scaffolds — scene graphs, coordinate systems (VADAR, SG-Nav)

---

## Related Pages

- [[sources/spatial-reasoning-survey]] — source paper proposing this taxonomy
- [[concepts/visual-attention-in-vlms]] — mechanistic account of failure mode #1 (attention imbalance; geometric distribution of attention determines correctness)
- [[sources/why-spatial-reasoning-hard-vlms]] — AdaptVis paper; mechanistic root cause analysis; directly complementary
- [[sources/covt-chain-of-visual-thought]] — expert-aligned continuous tokens address the projection bottleneck (depth, edges, segmentation)
- [[sources/whats-holding-back-latent-visual-reasoning]] — statistical-correlation failure mode explains why latent tokens trained on redundant data are bypassed
- [[concepts/visual-reasoning-in-vlms]] — paradigm taxonomy; all paradigms can be evaluated against this taxonomy
- [[sources/spatialladder]] — three-stage progressive training that directly operationalises "fix perception before reasoning"; ablations confirm multi-view diversity and Stage 2 understanding are most critical
