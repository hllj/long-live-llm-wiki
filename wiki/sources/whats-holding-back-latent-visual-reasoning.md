# What's Holding Back Latent Visual Reasoning?

**Paper**: What's Holding Back Latent Visual Reasoning?  
**Authors**: André G. Viveiros, Nuno Gonçalves, André F. T. Martins, Matthias Lindemann  
**Affiliation**: Instituto Superior Técnico, Instituto de Telecomunicações, TransPerfect, Carnegie Mellon University  
**arXiv**: 2605.18445 (May 18, 2026)  
**Raw**: `raw/2605.18445.pdf`  
**Date ingested**: 2026-05-22

---

## Summary

This paper directly interrogates whether latent visual tokens in VLM reasoning chains are *causally* responsible for improved performance, or whether models simply learn to bypass them. Through controlled causal interventions on four existing latent visual reasoning models (LVR, Monet, ILVR, LanteRn), the authors find a striking result: **model accuracy is unaffected when latent tokens are replaced with uninformative dummy alternatives** — random image subregions, zeros, or noise.

The paper identifies two root failures: the **latent bypass problem** (models ignore latent tokens during inference) and **latent representation collapse** (predicted latents collapse to a narrow cluster, failing to encode the right task-specific information). It then diagnoses *why* these failures occur: training datasets using subregion crops as intermediate images are inherently uninformative, because the original input image already contains those subregions. When training is redesigned around genuinely non-redundant visual intermediates — masked inputs, or a synthetic Tetris rotation task — models do learn to use latents and show large performance gaps between oracle and dummy tokens.

---

## Key Findings

### Latent Bypass Problem
- Tested 4 models: LVR, Monet, ILVR, LanteRn (at 3B and 7B scale)
- Benchmarks: BLINK, V*Bench
- Replacing generated latent tokens with: (1) random image subregions, (2) zeros, (3) noise, (4) skipped latents → accuracy **unchanged** in all conditions
- Even **providing oracle latent tokens** at inference (ground-truth representations from the expert model) produced **minimal improvement**
- Conclusion: models largely route around latent tokens in their final prediction

### Latent Representation Collapse
- Cosine similarity *between* predicted latents: **0.8–0.98** across samples (nearly identical to each other)
- Cosine similarity *between* predicted latents and their ground-truth oracles: **0.22–0.96** (highly variable, often poor)
- Top-1 retrieval accuracy of generated latents against oracles: **3.3%** (on 300 VisCoT holdout samples)
- USP (Unrelated Self-Generated Preference) metric: predicted latents are almost always closer to other predictions than to their corresponding oracles

### Root Cause: Uninformative Training Data
- Most existing datasets use **subregion crops of the input image** as intermediate visual steps
- Oracle latents for these crops add little information beyond what the model already has from the full image → no incentive to attend to them
- This is the structural reason bypass is learned: attending to latents has no marginal value given the training signal

### When Latents *Do* Work (the fix signal)
- **Masked training**: relevant image regions masked in input, forcing reliance on latents
  - Oracle latents: 75% accuracy | Dummy tokens: 59–80% → clear causal gap
- **Tetris synthetic dataset** (polyomino rotations — non-trivial transformation):
  - Oracle latents: **86% accuracy** | Standard inference: **33%** | Dummy tokens: 25–34%
  - Large causal gap proves latent mechanisms *can* work when training data actually requires them

---

## Critical Scope Note

**The 4 models studied (LVR, Monet, ILVR, LanteRn) all use image-crop-based intermediate representations.** [[concepts/continuous-visual-tokens|CoVT-style expert-aligned tokens]] (SAM, DepthAnything, DINOv2) are a *different* architecture and were **not directly tested** by this paper. CoVT's alignment to external expert models that produce non-redundant perceptual signals (depth maps, segmentation masks) may make it less susceptible to the bypass problem — but this is untested. The paper's Tetris finding suggests that genuinely informative, non-redundant intermediates do produce causal latent reliance; CoVT's expert tokens may satisfy this requirement.

---

## Implications for the Field

1. **Benchmark gains ≠ causal latent use**: A model can achieve strong benchmark improvements from CoT-style training without actually using latent tokens at inference; the signal may come from training supervision alone.
2. **Dataset design is the bottleneck**: The field needs intermediate visual steps that provide genuinely non-redundant information relative to the input — not crops, but transformations, segmentations, depth maps, or synthetic constructions.
3. **Diagnostic metric**: Monitor cosine similarity of predicted latents to oracles (and to each other) during training as a proxy for whether latent collapse is occurring.
4. **CoVT implications**: CoVT's +14% depth gains may reflect a better training signal rather than causal token use at inference — testing this with the bypass intervention on CoVT is an important open experiment.

---

## Related Pages

- [[concepts/continuous-visual-tokens]] — the latent token mechanism; directly challenged by this paper
- [[concepts/chain-of-visual-thought]] — CoVT framework; raises unresolved questions
- [[concepts/visual-reasoning-in-vlms]] — broader paradigm; latent reasoning column needs updating
- [[analyses/covt-limitations-and-research-directions]] — bypass problem is Limitation 0
- [[sources/mirage-machine-mental-imagery]] — Mirage's two-stage training (Stage 1 cosine grounding + Stage 2 relaxation) directly addresses both bypass and collapse; t-SNE shows latents stay on visual manifold
- [[sources/modal-mixed-cot-latent-embeddings]] — another self-generated latent approach (diffusion decoder); bypass not tested; uses VLM encoder (not expert transformations) so redundancy risk is unverified
- [[sources/pearl-predictive-embedding-alignment]] — PEARL sidesteps bypass entirely (no latent tokens at inference); independently corroborates this paper's findings via Figure 3 correlation analysis (avg r=−0.12, R²=0.02 between latent count and performance in reconstruction baselines)
- [[sources/valr-vision-aligned-latent-reasoning]] — VaLR benchmarks existing latent models on VSI-Bench: CoVT 18.6%, Monet 14.0%, LVR 18.4% — all collapse on multi-view tasks (perform below base model 33.0%); per-step REPA checkpointing fixes this to 52.9%
- [[concepts/visual-attention-in-vlms]] — bypass is partly an attention problem: models fail to attend to latent tokens; this page documents the imbalance and approaches to correct it
- [[entities/vsi-bench]] — CoVT 18.6%, Monet 14.0%, LVR 18.4% all below base model 33.0%; multi-view collapse leaderboard
- [[entities/v-star-bench]] — bypass intervention tested on V*Bench; accuracy unchanged with dummy tokens
