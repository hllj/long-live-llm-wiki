# Why Is Spatial Reasoning Hard for VLMs? An Attention Mechanism Perspective

**Paper**: Why Is Spatial Reasoning Hard for VLMs? An Attention Mechanism Perspective on Focus Areas  
**Authors**: Shiqi Chen, Tongyao Zhu, Ruochen Zhou, Jinghan Zhang, Siyang Gao, Juan Carlos Niebles, Mor Geva, Junxian He, Jiajun Wu, Manling Li  
**Affiliation**: Northwestern University, NTU, Stanford, Google DeepMind, Tel Aviv University, HKUST  
**arXiv**: 2503.01773 (Mar 2025)  
**Venue**: ICML 2025  
**Code**: https://github.com/shiqichen17/AdaptVis  
**Raw**: `raw/2503.01773.pdf`  
**Date ingested**: 2026-05-22

---

## Summary

This paper answers a mechanistic question the rest of the wiki has described empirically: *why* do VLMs fail at spatial reasoning? Using mechanistic interpretability — tracing attention distributions layer by layer and correlating them with YOLO-detected object locations — the authors find a structural bottleneck: **image tokens make up ~90% of input but receive only ~10% of total attention**. Textual priors systematically dominate visual evidence.

Crucially, the fix is not to increase image attention uniformly — that doesn't help. What matters is the *geometric distribution* of attention: when the model attends to the right spatial locations, it gets the right answer. The solution, **AdaptVis**, uses the model's own generation confidence as a signal to either sharpen (high confidence) or smooth (low confidence) attention over image regions — achieving up to +50 percentage points on controlled spatial reasoning benchmarks, training-free.

---

## Core Mechanistic Findings

### 1. Sparse Image Attention
- Image tokens ≈ **90% of input tokens**, yet receive ≈ **10% of total attention**
- Text tokens receive ≈ 9× more attention per token than image tokens
- This imbalance is consistent across LLaVA-1.5, LLaVA-1.6, and Qwen2-VL

### 2. Quality Over Quantity
- Uniformly scaling up image attention (**ScalingVis** with α > 1) does not reliably improve spatial reasoning
- What predicts correct answers is *where* attention lands, not *how much* goes to images in aggregate
- Controlled datasets benefit from sharpening (α > 1); natural images sometimes benefit from smoothing (α < 1)

### 3. Attention–Correctness Correlation by Layer
- **Early layers (1–8)**: High absolute image attention, but low AUROC with correctness — global feature capture, not spatial reasoning
- **Middle layers (14–18)**: Peak AUROC between attention–object overlap and answer correctness; active spatial reasoning occurs here
- **Late layers (20+)**: AUROC declines; model shifts to output generation

### 4. Two Attention Failure Modes
- **Insufficient attention**: Model fails to focus on the spatial regions mentioned in the question
- **Misplaced attention**: Model attends to irrelevant image regions (distractors, background)

### 5. Familiarity Bias
- VLMs show strong confidence on familiar spatial relations (left/right) and low confidence on unfamiliar ones (in front of/behind)
- Confidence inversely tracks difficulty — a reliable proxy for when attention distribution can be trusted

---

## AdaptVis: Confidence-Guided Attention Scaling

A training-free inference-time intervention applied to image attention logits:

```
If model confidence > β:  apply α₁ > 1  (sharpen — concentrate on key regions)
If model confidence ≤ β:  apply α₂ < 1  (smooth — broaden context window)
```

- Targets attention from the **final input token** to image tokens, across all layers
- Typical values: α₁ = 1.5–2.0 (sharpening), α₂ = 0.5 (smoothing), β tuned on validation
- Compared to: DoLa (contrastive layers), VCD (visual contrastive decoding) — AdaptVis substantially outperforms both

---

## Results

### WhatsUp Dataset (LLaVA-1.5)

| Subset | Baseline | AdaptVis | Δ |
|---|---|---|---|
| Controlled_A | 60.3% | 84.9% | +24.6 pts |
| Controlled_B | 73.1% | 83.8% | +10.7 pts |
| COCO_one | 53.0% | 53.6% | +0.6 pts |
| VG_one | 35.9% | 42.7% | +6.8 pts |
| VG_two | 40.8% | 48.1% | +7.3 pts |

### Controlled Dataset (LLaVA-1.6) — Largest Gains

| Metric | Baseline | AdaptVis | Δ |
|---|---|---|---|
| Controlled_A accuracy | 48.2% | **98.2%** | **+50.0 pts** |
| Controlled_B accuracy | 63.0% | 73.4% | +10.4 pts |
| Pair accuracy (Cont_A) | 37.6% | 78.8% | +41.2 pts |
| Set accuracy (Cont_A) | 0.0% | 57.0% | +57.0 pts |

### VSR Dataset

| Model | Metric | Baseline | AdaptVis | Δ |
|---|---|---|---|---|
| LLaVA-1.5 | F1 | 51.3% | 62.5% | +11.2 pts |
| LLaVA-1.6 | F1 | 29.4% | 39.3% | +9.9 pts |

### Generalization: Qwen2-VL
- VG_two: +10.73 pts; COCO: +1.2–1.4 pts
- Confirms sparse attention and confidence–accuracy correlation hold cross-architecture

### General benchmarks (POPE, GQA, TextVQA)
- Gains: 0.08–0.82 pts — AdaptVis specifically targets spatial geometry, minimal side-effects

---

## Limitations

1. Cannot fix upstream vision **encoder** errors (e.g., CLIP failures on atypical images) — AdaptVis operates at attention level, downstream of the encoder
2. Optimal hyperparameters (α₁, α₂, β) vary by label distribution and prompt — requires validation set tuning per deployment
3. Minimal gain on general QA: the method is targeted at spatial geometry sensitivity, not general reasoning

---

## Connection to Other Work

This paper provides the **mechanistic root cause** for failures that CoVT, ICoT, and the bypass paper each address differently:

| Paper | What they do about the attention problem |
|---|---|
| **This paper (AdaptVis)** | Reshape existing attention distribution via confidence-guided temperature scaling |
| **CoVT** | Add new perceptual cues (expert tokens) that force the model to encode spatial info it was ignoring |
| **ICoT** | Re-inject image patches mid-chain at the positions the model is already attending to |
| **Bypass paper** | Asks whether any of these tokens actually influence predictions at inference |

---

## Related Pages

- [[concepts/visual-reasoning-in-vlms]] — paradigm taxonomy; this paper provides the mechanistic explanation for the core tension
- [[analyses/visual-thinking-techniques]] — the core tension section is now mechanistically grounded
- [[sources/covt-chain-of-visual-thought]] — CoVT addresses the same bottleneck via expert tokens
- [[sources/icot-interleaved-modal-chain-of-thought]] — ICoT addresses it via re-injection at attended regions
- [[sources/whats-holding-back-latent-visual-reasoning]] — bypass paper asks the next question: do added tokens even get used?
