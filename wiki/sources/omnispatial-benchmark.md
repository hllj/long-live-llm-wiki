# OmniSpatial: Comprehensive Spatial Reasoning Benchmark for VLMs

**Paper**: OmniSpatial: Towards Comprehensive Spatial Reasoning Benchmark for Vision Language Models  
**Authors**: Mengdi Jia, Zekun Qi, Shaochen Zhang, Wenyao Zhang, Xinqiang Yu, Jiawei He, He Wang, Li Yi  
**Affiliation**: Tsinghua University, Xi'an Jiaotong University, SJTU, Peking University, Shanghai Qi Zhi Institute, Galbot  
**arXiv**: 2506.03135 (Jun 2025; v3 Feb 2026)  
**Project**: https://qizekun.github.io/omnispatial/  
**Dataset**: https://huggingface.co/datasets/qizekun/OmniSpatial  
**Raw**: `raw/2506.03135.pdf`  
**Date ingested**: 2026-05-23

---

## Summary

OmniSpatial addresses a saturation problem: state-of-the-art VLMs already exceed 90% on basic spatial tasks (left/right, proximity, counting), so existing benchmarks no longer discriminate model quality. The benchmark targets the complex spatial capabilities demanded by embodied AI and robotics — dynamic reasoning, geometric transformations, multi-viewpoint relationships — where even the best models (o3: 56.33%) fall ~36 percentage points below the human baseline (92.63%).

The 4-category, 50-subcategory taxonomy with 8,400 manually annotated QA pairs (Krippendorff's α = 0.84) is the most comprehensive spatial reasoning benchmark in the wiki. Its empirical results provide the clearest current picture of where VLMs fail hardest: geometric/pattern reasoning (30-40%) and non-egocentric perspective-taking (32-48%).

The training comparison is the most actionable new finding: fine-tuning on 6,900 manual OmniSpatial samples yields **+7.82pp**, while training on 200K template-generated examples yields only **+1.29pp** — a 6× quality advantage for curated data, directly corroborating the data scarcity bottleneck finding from [[sources/mcot-deep-thinking-survey]].

---

## Key Points

### Four-Category Taxonomy (50 Subcategories)

| Category | Subtasks | What it tests |
|---|---|---|
| **Dynamic Reasoning** | Manipulation, Motion Analysis | Infer motion and temporal change from visual evidence |
| **Complex Spatial Logic** | Pattern Recognition, Geometric Reasoning | Higher-order relations, transformations, geometric structures |
| **Spatial Interaction** | Traffic Analysis, Localization, Geospatial Strategy | Reasoning guided by environmental constraints and task goals |
| **Perspective Taking** | Egocentric, Allocentric, Hypothetical | Adopt alternative viewpoints; mental rotation |

Maps onto the [[concepts/spatial-reasoning-taxonomy]] framework: Dynamic Reasoning ≈ Extrinsic–Qualitative–Dynamic; Complex Spatial Logic ≈ Quantitative–Static + Intrinsic–Qualitative–Dynamic; Perspective Taking ≈ Frame-of-Reference instability failure mode.

### Dataset Statistics

- **Total**: 8,400 QA pairs (1,500 test, 6,900 train)
- **Format**: Multiple-choice (binary and four-option); conversational phrasing
- **Annotation**: 6 trained annotators; Krippendorff's α = 0.84
- **Sources**: web images, cognitive tests, driving scenarios, MME, HOI4D

### Performance Results (Overall Accuracy)

| Model | Accuracy |
|---|---|
| **Human baseline** | **92.63%** |
| o3-2025-04-16 | 56.33% |
| Gemini-2.5-pro-preview | 55.19% |
| Gemini-2.5-flash-thinking | 53.16% |
| o4-mini | 52.77% |
| InternVL3-78B | 49.33% |
| Qwen-VL2.5-72B | 47.85% |
| SoFar-Qwen2.5VL-3B | 45.14% |
| Qwen-VL2.5-3B (baseline) | 40.30% |

**Gap**: ~36pp between best model and human. All models well below human performance.

### Category-Specific Failure Modes

| Category | Top Model Score | Pattern |
|---|---|---|
| Traffic Analysis | 60–77% | Strongest — familiar scenario |
| Dynamic Reasoning | o3: 71.89% | Proprietary reasoning models excel |
| Egocentric Perspective | 59–77% | Manageable |
| **Geometric/Pattern Reasoning** | **20–40%** | **Near-random — critical gap** |
| Allocentric Perspective | 32–48% | Major bottleneck |
| Hypothetical Perspective | 32–48% | Major bottleneck |

**Key finding**: models are near-random on geometric and pattern reasoning, and fail significantly on any perspective that isn't first-person egocentric.

### Training Data Quality Finding

| Training setup | Qwen-VL2.5-3B accuracy | Δ |
|---|---|---|
| Zero-shot baseline | 40.30% | — |
| + OmniSpatial-train (6.9K manual) | 48.12% | **+7.82pp** |
| + Template corpus (200K generated) | 41.59% | +1.29pp |

**6× quality advantage** for manually curated data over template-generated data at 29× the scale. Cross-benchmark: OmniSpatial training also improves VSI-Bench (41.68% → 43.68%), showing transfer.

### Improvement Strategies

**PointGraph** (scene graph augmentation):
- Florence-2 extracts object localizations, centers, bounding boxes → JSON spatial description
- Consistent +1.63–2.91pp across models on dynamic reasoning and perspective-taking tasks

**SpatialCoT** (multi-view chain-of-thought):
- InstantMesh generates 6 additional perspectives per image → composed as CoT input
- GPT-4.1-mini: +2.02pp on perspective-taking; Qwen-VL2.5-3B: +2.01pp
- Provides geometric priors for viewpoint disambiguation

**Specialized spatial models** (SpatialBot, RoboPoint, SpaceMantis): fail to substantially outperform general-purpose models on comprehensive tasks — training on narrow spatial datasets doesn't generalize.

---

## Connections

- [[concepts/spatial-reasoning-taxonomy]] — OmniSpatial fills the "dynamic reasoning benchmarks scarce" and "perspective-taking underrepresented" gaps; its 4-category taxonomy is a concrete implementation of the 3D cognitive framework
- [[sources/spatial-reasoning-survey]] — survey identified these benchmark gaps; OmniSpatial is the most comprehensive answer to date
- [[analyses/vlm-reasoning-training-findings]] — manual data >> template data (+7.82pp vs +1.29pp); strongest evidence yet for data quality over quantity
- [[sources/spatialladder]] — complementary: SpatialLadder trains on multi-view and video spatial tasks; OmniSpatial evaluates dynamic and perspective-taking; the two together cover the hardest spatial categories
- [[sources/why-spatial-reasoning-hard-vlms]] — attention geometry is the mechanistic root cause; OmniSpatial quantifies how severe the failures are at the task level
- [[concepts/visual-reasoning-in-vlms]] — benchmark landscape expanded with OmniSpatial
