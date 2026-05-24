# CoVT: Chain-of-Visual-Thought

**Paper**: Chain-of-Visual-Thought: Teaching VLMs to See and Think Better with Continuous Visual Tokens  
**Authors**: Yiming Qin, Bomin Wei, Jiaxin Ge, Konstantinos Kallidromitis, Stephanie Fu, Trevor Darrell, XuDong Wang  
**Affiliation**: UC Berkeley, UCLA, Panasonic AI Research  
**arXiv**: 2511.19418v2 (Nov 30, 2025)  
**Code**: https://github.com/Wakals/CoVT

---

## Core Problem

VLMs excel at text reasoning but struggle with dense perceptual tasks (counting, depth estimation, spatial correspondence). The root cause: projecting continuous visual information into discrete text tokens is inherently lossy — boundaries, depth, and geometry are poorly represented in language space.

Critically, text-only Chain-of-Thought **degrades** visual reasoning. Qwen3-VL-Thinking is 5%+ worse than Qwen3-VL-Instruct on spatial benchmarks (HRBench8k, VSI-Bench, V*). Error accumulation in long text chains makes this worse.

---

## Solution: Continuous Visual Tokens

CoVT inserts compact **continuous visual tokens** into the reasoning chain alongside text tokens. These tokens encode rich perceptual cues from lightweight vision expert models. The VLM learns to generate these tokens autoregressively during its `<think>` phase.

At inference, the tokens exist only in latent space (efficient). Optionally, they can be decoded into human-readable maps (segmentation masks, depth maps, edge maps) for interpretability.

---

## Token Types (~20 tokens total)

| Token type | Expert model | Count | Alignment | Captures |
|---|---|---|---|---|
| Segmentation | SAM (ViT-H) | 8 | Prompt-level via SAM decoder | Instance position & shape, 2D spatial |
| Depth | DepthAnything v2 (ViT-L) | 4 | Prompt-level via BMM + decoder | 3D spatial relationships |
| Edge | PIDINet | 4 | Prompt-level via 1×1 conv | Structure, geometry, fine boundaries |
| DINO | DINOv2 (ViT-L) | 4 | Feature-level via MSE | Patch-level semantic representation |

**Alignment strategy split**: Task-oriented models (SAM, DepthAny, PIDINet) → aligned through decoders at prompt level (preserves fine-grained detail). Representation models (DINO) → aligned at encoder feature level (less fine-grained, no decoder needed).

**Projection layer**: Linear → Cross-Attention (learnable query) → projected tokens as decoder prompts.

---

## Training Pipeline (4 stages)

1. **Comprehension**: Visual tokens inserted after `<image>` — VLM learns their semantics
2. **Generation**: VLM learns to generate visual tokens precisely (question asks for segmentation/depth/etc.)
3. **Reasoning**: Chain-of-visual-thought format introduced — visual tokens inside `<think>` blocks
4. **Efficient reasoning**: Random dropout of visual token types — VLM learns to select which tokens are useful

LoRA finetuning (rank=16, alpha=32, lr=5e-5; projection layer lr=1e-5). Batch size=4. Hardware: 1×A100 or 4×A6000. Base model: Qwen2.5-VL-7B.

**Training loss**: Cross-entropy loss + weighted sum of visual reconstruction losses (seg: Dice+Focal+CE; depth: L1+CE; edge: L1+CE; DINO: MSE).

---

## Dataset (~774.6k samples)

- Vision-centric subsets of LLaVA-OneVision (TallyQA, CLEVR, ShareGPT4V, ADE20K-Depth, etc.)
- Filtered TallyQA (150k — reduced zero-count samples)
- ADE20K-Depth (5k samples for relative depth, following Aurora)

---

## Results

**Vision-centric benchmarks** (vs Qwen2.5-VL-7B baseline, 3 visual tokens):

| Benchmark | Baseline | CoVT | Δ |
|---|---|---|---|
| CV-Bench | 74.5 | 80.0 | +5.5% |
| CV-Bench Depth subtask | 72.8 | 86.8 | +14.0% |
| CV-Bench Distance | 75.5 | 82.5 | +7.0% |
| MME-RealWorld | 60.0 | 63.7 | +3.7% |
| HRBench8K | 64.9 | 69.4 | +4.5% |
| MMVP | 56.0 | 58.7 | +2.7% |

**4 visual tokens** add ~0.5% more on depth (+16.4% total) at cost of slight regression elsewhere.

**Non-vision-centric**: +1.2% average improvement — CoVT does not hurt general capability.

**vs Aurora** (on LLaVA-v1.5-13B): CoVT with depth tokens beats Aurora-depth by +12.9% on BLINK relative-depth; CoVT with segmentation tokens beats Aurora-count by +26.6% on BLINK-count.

---

## Key Ablations

- **Text-only CoT**: Hurts or provides no benefit on vision-centric tasks. CoVT consistently helps.
- **Token count**: 8 segmentation tokens optimal. 1 token = performance drop; 32 tokens = worse performance + 220% compute overhead.
- **Alignment strategy**: Decoder-level alignment (task-oriented) > direct feature MSE alignment. ~1-2% difference across benchmarks.
- **Training stages**: Skipping stages 1–2 causes notable degradation on BLINK; the comprehension and generation stages are not optional.
- **Empty tokens**: 16 unaligned tokens add no benefit — the visual alignment is essential, not just additional capacity.

---

## Comparison with Prior Methods

| Method | No external tools | Continuous visual space | Dense visual info | 3D-aware |
|---|---|---|---|---|
| VCoT | ✓ | ✗ | ✗ | ✗ |
| MCoT | ✗ | ✓ | ✓ | ✗ |
| VChain | ✓ | ✓ | ✗ | ✗ |
| Aurora | ✓ | ✗ | ✓ | ✓ |
| **CoVT** | **✓** | **✓** | **✓** | **✓** |

---

## Limitations

1. Design space of visual token types not exhaustively explored (only 4 expert types tested)
2. No fully interleaved multimodal reasoning — visual thoughts and text thoughts are not seamlessly mixed mid-chain

---

## Related pages

- [[concepts/chain-of-visual-thought]] — the CoVT framework concept
- [[concepts/visual-reasoning-in-vlms]] — broader context of VLM visual reasoning
- [[concepts/continuous-visual-tokens]] — the key technical mechanism
- [[concepts/visual-attention-in-vlms]] — mechanistic root cause that motivates CoVT: image tokens receive only ~10% of attention; CoVT's expert tokens directly address this
