# Visual Attention in VLMs

The study of how Vision-Language Models internally allocate attention between image tokens and text tokens, and how that allocation determines spatial reasoning success or failure.

**Sources**: [[sources/why-spatial-reasoning-hard-vlms]], [[sources/spatial-reasoning-survey]]

---

## The Attention Imbalance

Despite image tokens comprising **~90% of input sequences**, VLMs allocate only **~10% of total attention** to them. Text tokens receive approximately 9× more attention per token.

This is not a bug in how VLMs are built — it reflects the dominance of language pretraining priors. The model has learned that text is usually more informative than image patches for next-token prediction. For semantic and logical tasks this is fine; for spatial reasoning it is the root cause of failure.

---

## Quality vs. Quantity

Uniformly increasing image attention (scaling all image logits by a constant factor α > 1) does **not** reliably improve spatial reasoning. This is a key finding: the bottleneck is not the *amount* of attention given to images but the *geometric distribution* of that attention.

**What predicts correctness**: whether attention lands on the image regions that contain the objects referenced in the question, as measured by overlap with YOLO-detected object bounding boxes (AUROC in middle transformer layers).

---

## Layer-Wise Dynamics

| Layer range | Attention behaviour | Spatial reasoning role |
|---|---|---|
| Early (1–8) | High image attention in absolute terms; low AUROC | Global feature capture, not spatial reasoning |
| Middle (14–18) | Peak AUROC between attention–object overlap and correctness | Active spatial reasoning; where the model processes "left of / in front of" |
| Late (20+) | AUROC declines | Output generation mode |

The middle-layer AUROC result shows the model *does* have the machinery for spatial reasoning — it's a matter of whether attention is directed correctly at those layers.

---

## Two Failure Modes

1. **Insufficient attention**: Model allocates too little attention to the image regions containing the referenced objects
2. **Misplaced attention**: Model attends to irrelevant regions (background, distractors) rather than the spatially relevant entities

Both lead to incorrect spatial predictions. Crucially, they call for opposite fixes: insufficient attention needs sharpening; misplaced attention needs broadening.

---

## Familiarity Bias

VLMs exhibit a strong **familiarity bias** in spatial reasoning:
- High generation confidence on familiar relations: *left*, *right*
- Low generation confidence on unfamiliar relations: *in front of*, *behind*

This confidence signal tracks task difficulty and can be used diagnostically. It also explains the systematic failure pattern: models learn spatial relation statistics from language (left/right dominate text corpora) and default to these when visual evidence is ambiguous.

---

## AdaptVis: Confidence-Guided Attention Scaling

A training-free inference-time fix that uses generation confidence to choose between two interventions:

```
High confidence (> β) → sharpen image attention (α > 1): model "knows" where to look, amplify it
Low confidence (≤ β)  → smooth image attention (α < 1): model is uncertain, broaden the window
```

Applied to attention logits from the **final input token** to all image tokens, across all layers. Results:
- LLaVA-1.6 Controlled_A: **48.2% → 98.2%** (+50 percentage points)
- LLaVA-1.5 Controlled_A: 60.3% → 84.9% (+24.6 pts)
- Cross-architecture: similar gains on Qwen2-VL

Outperforms DoLa and VCD (prior contrastive decoding approaches) substantially.

**Limitation**: requires per-dataset hyperparameter tuning (α₁, α₂, β); minimal gain on general QA tasks; cannot fix upstream vision encoder errors.

---

## Implications for Other Approaches

The attention imbalance finding mechanistically grounds several other papers in the wiki:

- **CoVT** [[sources/covt-chain-of-visual-thought]]: expert-aligned continuous tokens force the model to encode spatial cues it was underweighting — a training-time fix to the same attention imbalance
- **ICoT** [[sources/icot-interleaved-modal-chain-of-thought]]: re-injects image patches at the locations the model is already attending to — works *with* the existing attention pattern rather than reshaping it
- **Bypass concern** [[sources/whats-holding-back-latent-visual-reasoning]]: if image tokens only get 10% of attention normally, there's a risk that added latent tokens also get ignored — the bypass problem may be a downstream consequence of the same attention imbalance
- **Mirage** [[sources/mirage-machine-mental-imagery]]: addresses the collapse side of the bypass problem via Stage 1 grounding — latents stay near the visual manifold, meaning the model has reason to attend to them

---

## Cognitive Framing: Three Root Failure Modes

[[sources/spatial-reasoning-survey]] (U. Pittsburgh, Nov 2025) provides a complementary **cognitive-level** account of why spatial reasoning fails, sitting above the mechanistic attention-level explanation above:

1. **Projection Bottleneck** — 2D encoders optimized for semantic alignment, not 3D geometry; depth/orientation weakly preserved in discrete tokens. (Same structural problem; this is the architectural framing, attention imbalance is the mechanistic one.)
2. **Statistical Correlations Over Physical Constraints** — models learn spatial co-occurrence statistics rather than geometric regularity; breaks on metric/counterfactual tasks.
3. **Frame-of-Reference Instability** — no explicit egocentric/allocentric switching mechanism; multi-view localization causes left/right confusion; no persistent scene memory.

See [[concepts/spatial-reasoning-taxonomy]] for the full taxonomy and benchmark gap analysis.

---

## Open Questions

1. Does AdaptVis compose with CoVT or ICoT? Combining attention reshaping with expert token addition or patch re-injection could be additive.
2. Do the middle-layer attention patterns generalize across model families beyond LLaVA and Qwen2-VL?
3. Can the familiarity bias be reduced through training data rebalancing (more in-front-of/behind examples) rather than inference-time patching?

**Note**: [[sources/spatialladder]] provides a training-time answer to the attention geometry problem. Its progressive curriculum (localization → spatial understanding → GRPO) raises attention IoU from 33.8% → 37.7% and lowers attention entropy from 0.193 → 0.176, confirming that training on localization-first tasks improves geometric attention distribution — not just accuracy.
