# Interleaved-Modal Chain-of-Thought (ICoT)

**Paper**: Interleaved-Modal Chain-of-Thought  
**Authors**: Jun Gao, Yongqi Li, Ziqiang Cao, Wenjie Li  
**Affiliation**: Soochow University; The Hong Kong Polytechnic University  
**arXiv**: 2411.19488 (Nov 2024, revised Mar 2025)  
**Venue**: CVPR 2025  
**Code**: https://github.com/jungao1106/ICoT  
**Raw**: `raw/2411.19488.pdf`  
**Date ingested**: 2026-05-22

> **Note (updated 2026-05-23):** [[sources/perception-cognition-survey]] classifies ICoT as an **endogenous, single-forward-pass evidence injection** method — internal attention mechanisms, no external tools. It sits alongside CVC and MINT-CoT in this taxonomy. CoVT and Mirage go further by generating *new* perceptual signals rather than re-using input patches.

---

## Summary

ICoT directly addresses the CoT interleaving limitation in VLMs: standard multimodal CoT produces text-only rationales, which are too coarse for fine-grained visual tasks (e.g., "at the top" fails to distinguish spatially adjacent objects). ICoT generates reasoning chains that alternate between text rationales and cropped image patches — truly interleaved, multiple times per chain.

The key contribution is **Attention-driven Selection (ADS)**: a plug-and-play, training-free mechanism that piggybacks on the model's own attention maps to select *which* image patches to insert at each reasoning step. No new parameters, no fine-tuning required — ADS generalizes across VLM families.

---

## Method: Attention-Driven Selection (ADS)

Standard reasoning chain:
```
r₁ → r₂ → r₃ → ... → answer   (text only)
```

ICoT reasoning chain:
```
r₁ → [visual patches₁] → r₂ → [visual patches₂] → ... → answer
```

**How ADS works at inference:**
1. At each newline token (`\n`, the designated signal), extract current attention scores over the input image tokens
2. Select the top-k image token positions by attention score (k=64 by default)
3. Retrieve the corresponding image patches, preserving spatial layout
4. Append them to the generation context before continuing

No training, no extra parameters. The selection is dynamic — different patches are inserted at different reasoning steps based on where the model is actually looking.

### Key design choices
- **Signal token**: newline (`\n`) — fires at natural reasoning boundaries
- **Patch count**: 64 tokens optimal (32 = underfitting; 128+ = dispersed selection, worse performance)
- **Attention implementation**: "eager" (not FlashAttention) to retain score access
- **KV cache**: inserting patches at input position outperforms copying KV cache (position-agnostic cached states degrade quality)

---

## Results

Tested on Chameleon-7B and Qwen2-VL-7B-Instruct across M3CoT, ScienceQA, and LLaVA-W:

| Model | Benchmark | ICoT | Best Baseline | Δ |
|---|---|---|---|---|
| Chameleon-7B | M3CoT (ACC) | 32.3 | 31.1 (SCAFFOLD) | +3.9% |
| Chameleon-7B | ScienceQA (ACC) | 53.4 | 50.2 (CCoT) | +6.4% |
| Chameleon-7B | LLaVA-W (ROUGE-L) | 27.6 | 24.7 (CCoT) | +11.7% |
| Qwen2-VL-7B | M3CoT (ACC) | 46.0 | 45.7 (DDCoT) | +0.7% |
| Qwen2-VL-7B | ScienceQA (ACC) | 65.4 | 64.9 (DDCoT) | +0.8% |
| Qwen2-VL-7B | LLaVA-W (ROUGE-L) | 35.7 | 33.9 (CCoT) | +5.3% |

Largest gains are on LLaVA-W (long-form visual QA requiring detailed descriptions), consistent with the value of iterative re-grounding during complex reasoning.

### Ablation: component contributions (Chameleon-7B)

| Configuration | M3CoT | ScienceQA | LLaVA-W |
|---|---|---|---|
| Full ICoT | 32.3 | 53.4 | 27.6 |
| w/o ADS | 29.2 (−3.1) | 52.4 (−1.0) | 24.5 (−3.1) |
| w/o fine-grained visual in demos | 30.6 (−1.7) | 52.8 (−0.6) | 25.9 (−1.7) |
| Neither | 29.1 (−3.2) | 51.0 (−2.4) | 23.0 (−4.6) |

ADS contributes more than the demonstration design, confirming that the dynamic patch insertion mechanism — not just the few-shot format — drives the gains.

---

## Failure Modes Fixed

Three systematic failure patterns in text-only CoT that ICoT addresses:

1. **Misunderstanding**: Text-only CoT conflates spatially adjacent objects; re-injected patches disambiguate at the step where confusion occurs
2. **Overgeneralization**: Text reasoning extends beyond image evidence; visual grounding at each step constrains inference to what's actually visible
3. **Hallucination**: Language models fabricate unattested details; iterative patch re-injection keeps generation anchored to the image

---

## Limitations

- Memory overhead from storing attention scores at each generation step
- Fixed patch count (64) is suboptimal for variable visual information density
- Newline-based trigger can fire too frequently (unintended activations)
- Noise in automatic demonstration generation from discrete patch boundaries
- Evaluated at 7B scale; scaling behavior unknown

---

## Relationship to Other Approaches

| Dimension | CoVT | ICoT |
|---|---|---|
| Visual representation | Continuous latent tokens from expert models | Discrete image patches from original input |
| Interleaving | Single visual block in chain | Multiple patch insertions mid-chain |
| Training required | Yes (4-stage LoRA fine-tuning) | No (plug-and-play ADS) |
| Differentiable | End-to-end | No (patch selection is argmax) |
| Information source | New perceptual transformations (depth, edges, etc.) | Subregions of original input image |
| Bypass risk | Lower (expert tokens provide novel signal) | Higher (patches are recoverable from input; see [[sources/whats-holding-back-latent-visual-reasoning]]) |

**Key distinction vs. bypass concern**: ICoT injects *actual image tokens* into context (not learned latent representations). The model attends to these directly as pixels — this is architecturally different from the latent bypass problem. Whether ADS-selected patches carry marginally more information than the original full image is a separate empirical question.

---

## Related Pages

- [[concepts/visual-reasoning-in-vlms]] — ICoT adds a new paradigm: attention-driven interleaved image patches
- [[concepts/chain-of-visual-thought]] — CoVT's Limitation 1 (no interleaving) is directly addressed by ICoT
- [[analyses/covt-limitations-and-research-directions]] — Limitation 1 now has a concrete solution
- [[sources/whats-holding-back-latent-visual-reasoning]] — bypass concern applies to patch-based approaches differently than to latent tokens
- [[concepts/visual-attention-in-vlms]] — ADS selects patches based on the model's own attention maps; this page explains the imbalance ADS works around
