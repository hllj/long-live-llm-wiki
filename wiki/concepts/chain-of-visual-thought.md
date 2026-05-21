# Chain-of-Visual-Thought (CoVT)

A framework that extends Chain-of-Thought reasoning from discrete text space into continuous visual latent space. Rather than forcing VLMs to verbalize visual observations as text, CoVT lets the model "think" by generating compact continuous visual tokens that encode perceptual cues directly in its reasoning chain.

**Source**: [[sources/covt-chain-of-visual-thought]]

---

## The core idea

Standard VLM reasoning chain:
```
<think> [text tokens only] </think> → <answer>
```

CoVT reasoning chain:
```
<think> [text tokens] + [visual tokens: seg, depth, edge, dino] </think> → <answer>
```

The visual tokens are compact latent representations (~20 total) that compress knowledge from lightweight vision expert models. They are generated autoregressively alongside text during the think phase. At inference they live entirely in latent space; decoding them to masks/maps is optional and only done for interpretability.

---

## Why text-only CoT fails for vision

Projecting continuous visual information (boundaries, depth, geometry) into discrete language tokens is lossy. Errors accumulate in long text chains. Empirical evidence: Qwen3-VL-Thinking (with text CoT) performs 5%+ *worse* than Qwen3-VL-Instruct (without CoT) on spatial benchmarks including HRBench8k, VSI-Bench, and V*.

CoVT directly addresses this by keeping visual information in continuous space throughout the reasoning process.

---

## Token types

See [[concepts/continuous-visual-tokens]] for details on each token type and its alignment strategy.

| Token | Expert | Count | Primary capability |
|---|---|---|---|
| Segmentation | SAM | 8 | Instance localization, 2D spatial |
| Depth | DepthAnything v2 | 4 | 3D spatial relationships |
| Edge | PIDINet | 4 | Structure, fine boundaries |
| DINO | DINOv2 | 4 | Semantic patch representation |

---

## Training curriculum

Four progressive stages prevent catastrophic forgetting of text capability:

1. **Comprehension** — VLM reads visual tokens inserted by the system; learns their semantics
2. **Generation** — VLM learns to produce visual tokens on demand
3. **Reasoning** — Visual tokens used inside `<think>` blocks to derive answers
4. **Efficient reasoning** — Random dropout of token types; VLM learns to select what it needs

---

## Relationship to related concepts

- **Chain-of-Thought (text)**: CoVT is a strict superset — it retains text CoT and adds visual tokens. The key claim is that for vision tasks, text CoT alone is insufficient or harmful.
- **Tool-augmented reasoning**: Tools are external, not differentiable, and their ceiling bounds final performance. CoVT internalizes "tools" as learnable latent tokens trained end-to-end.
- **Latent space reasoning (Coconut, CCoT)**: Those compress text CoT into continuous tokens. CoVT applies the same principle to visual perception specifically.
- **Aurora**: Uses VQ-VAE latents for depth/detection — discrete, not continuous. Lacks edge and semantic tokens. CoVT outperforms it substantially on counting and depth tasks.

---

## Key empirical findings

- +5.5% on CV-Bench, +14% on its depth subtask, +4.5% on HRBench8K over Qwen2.5-VL-7B
- Text-only CoT on the same data hurts or provides no benefit
- 8 segmentation tokens is the sweet spot; 32 degrades performance
- Decoder-level alignment (for task-oriented experts) outperforms feature-level MSE alignment
- All 4 training stages are necessary; skipping stages 1–2 notably hurts BLINK
