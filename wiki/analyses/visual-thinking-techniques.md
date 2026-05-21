# Visual Thinking Techniques in VLMs

A synthesis of how Vision-Language Models can reason about visual content, covering all major paradigms, their trade-offs, and the current state of the art.

**Sources**: [[concepts/visual-reasoning-in-vlms]], [[concepts/chain-of-visual-thought]], [[concepts/continuous-visual-tokens]], [[sources/covt-chain-of-visual-thought]]

---

## The Core Tension

VLMs project visual input into a language-centric token space to leverage LLM reasoning capabilities. This works well for semantic and logical tasks but creates a fundamental **lossy bottleneck** for perception-intensive tasks: continuous visual signals (depth, edges, geometry, spatial layout) are poorly representable as discrete text tokens.

---

## Paradigm Comparison

| Paradigm | Example Systems | Key Advantage | Key Weakness |
|---|---|---|---|
| Text-only CoT | Qwen3-VL-Thinking, DeepSeek-R1 | Strong for math/logic; no extra components | Degrades vision tasks; continuous spatial info lost in verbalization |
| Tool-augmented | ViperGPT, Visual ChatGPT, ToolVQA | Restores spatial/geometric detail | Not differentiable; GPU overhead; ceiling bounded by tools |
| Image gen/crop in chain | MCoT | Rich visual mid-chain | High compute; images re-projected to text space, losing density |
| Image interleaving | VChain | Full image in chain | Same projection bottleneck at reasoning step |
| Discrete latent | Aurora | Better than text; compact | Quantization loses continuous info; no edge/semantic tokens |
| **Continuous visual tokens** | **CoVT** | End-to-end differentiable; no external tools; best on perception | Design space not fully explored; studied mostly at 7–13B scale |

---

## Deep Dive: The Winning Approach — CoVT

[Chain-of-Visual-Thought (CoVT)](../concepts/chain-of-visual-thought.md) replaces text-only thinking with a mixed reasoning chain:

```
Standard: <think> [text tokens only] </think> → <answer>
CoVT:     <think> [text tokens] + [visual tokens: seg, depth, edge, dino] </think> → <answer>
```

### The Four Continuous Token Types

See [[concepts/continuous-visual-tokens]] for full alignment details.

| Token | Expert | Count | Perceptual Capability |
|---|---|---|---|
| Segmentation | SAM (ViT-H) | ×8 | Instance localization, 2D spatial layout |
| Depth | DepthAnything v2 (ViT-L) | ×4 | 3D spatial relationships |
| Edge | PIDINet | ×4 | Structure, fine boundaries |
| DINO | DINOv2 (ViT-L) | ×4 | Patch-level semantic representation |

**~20 tokens total** — deliberately compact to compress key perceptual signals without dominating context.

### Why It Outperforms

- Keeps visual information in **continuous space** throughout reasoning — no quantization loss
- Visual tokens are generated **autoregressively** alongside text; trained end-to-end
- At inference: tokens live as latent vectors only; decoding to masks/maps is optional (interpretability only)
- Results: +5.5% on CV-Bench, +14% on its depth subtask, +4.5% on HRBench8K over Qwen2.5-VL-7B base

### Why Text-Only CoT Fails for Vision

Projecting continuous spatial/geometric information into discrete language tokens is lossy, and errors accumulate in long chains. Empirical evidence: Qwen3-VL-Thinking (text CoT) is 5%+ **worse** than Qwen3-VL-Instruct (no CoT) on spatial benchmarks (HRBench8K, VSI-Bench, V*Bench).

---

## Open Problems

1. **Interleaved multimodal reasoning** — seamlessly mixing text and visual thoughts mid-chain, not just one visual block followed by text answer
2. **Design space of token types** — only 4 expert combinations explored; hybrid or domain-specific experts may yield gains
3. **Frontier scale** — most work done at 7–13B; behavior at larger scales is unclear
4. **Commonsense + perception** — tasks requiring both simultaneously remain challenging

---

## Key Takeaway

For perception-heavy visual tasks (depth, counting, spatial layout, fine boundaries), the path is: **don't verbalize visual observations — keep them in latent space**. Text CoT is sufficient for semantic/logical vision tasks but harmful for geometric ones. The current best technique is continuous visual token reasoning (CoVT), which internalizes the role of external tools as learnable latent tokens trained end-to-end.
