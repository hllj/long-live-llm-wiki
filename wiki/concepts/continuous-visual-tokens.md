# Continuous Visual Tokens

Compact latent representations that encode rich perceptual cues from vision expert models, designed to be generated autoregressively by a VLM as part of its reasoning chain. First introduced (in this form) by [[concepts/chain-of-visual-thought]].

**Sources**: [[sources/covt-chain-of-visual-thought]], [[sources/whats-holding-back-latent-visual-reasoning]]

> **Note (updated 2026-05-22):** [What's Holding Back Latent Visual Reasoning?](../sources/whats-holding-back-latent-visual-reasoning.md) raises a direct challenge: in 4 tested latent reasoning models, replacing generated latent tokens with uninformative dummy tokens leaves accuracy unchanged — the **latent bypass problem**. Models also exhibit **latent representation collapse** (predicted latents cluster together with 0.8–0.98 mutual similarity while diverging from ground-truth oracles; top-1 retrieval accuracy: 3.3%). The paper attributes this to training datasets that use subregion crops as intermediates (inherently redundant with the input). CoVT's expert-aligned tokens (SAM, DepthAnything, etc.) are a different architecture and were not directly tested, but the bypass concern applies to any latent token approach. The paper shows latents *can* work when training data provides genuinely non-redundant visual intermediates (masked inputs; Tetris synthetic task: oracle 86% vs. dummy 33%).  
> See [[sources/whats-holding-back-latent-visual-reasoning]] for the full analysis.

---

## What they are

A small set of continuous-valued embedding vectors (not discrete text tokens) that a VLM learns to produce within its `<think>` block. Each token group is supervised by a different lightweight vision expert and captures a distinct perceptual modality.

Total budget in CoVT: **~20 tokens** across 4 types. This is deliberately compact — enough to compress key perceptual signals without dominating the context.

---

## The four token types in CoVT

### Segmentation tokens (×8)
- **Expert**: SAM (ViT-H encoder + decoder)
- **Alignment**: Prompt-level — each token is projected into SAM's prompt space and used to decode one mask. Hungarian matching aligns predicted masks to SAM's quality-filtered ground-truth masks. Loss: Dice + Focal + CE.
- **Captures**: Instance-level position and shape; 2D spatial layout

### Depth tokens (×4)
- **Expert**: DepthAnything v2 (ViT-L)
- **Alignment**: Prompt-level — tokens interact with 4 intermediate encoder feature maps via Batch Matrix Multiplication (BMM) to reconstruct depth maps. Final map = average of 4. Loss: L1 + CE.
- **Captures**: Pixel-level depth, 3D spatial relationships

### Edge tokens (×4)
- **Expert**: PIDINet
- **Alignment**: Prompt-level — each token acts as a 1×1 convolutional kernel applied to PIDINet's dense features. Final map = sigmoid(average of 4). Loss: L1 + CE.
- **Captures**: Geometry-level structure, fine boundaries

### DINO tokens (×4)
- **Expert**: DINOv2 (ViT-L)
- **Alignment**: Feature-level — tokens are projected to match DINOv2's patch-level feature shape. Loss: MSE.
- **Captures**: Patch-level semantic representation; rich semantic information

---

## Two alignment strategies

| Strategy | Used for | How |
|---|---|---|
| Prompt-level (decoder alignment) | Task-oriented models (SAM, DepthAny, PIDINet) | Tokens projected to decoder prompt space; reconstruction losses backprop through tokens |
| Feature-level | Representation models (DINO) | Tokens projected to match encoder feature shape; MSE loss |

Task-oriented models need decoder-level alignment because their fine-grained spatial detail would be lost by direct MSE against encoder features. Ablation confirms: feature-level MSE for segmentation/depth loses ~1–2% across benchmarks.

---

## Projection layer architecture

For each token type:
1. Linear layer: projects VLM latent → prompt/feature space
2. Cross-attention: learnable query attends to the projected tokens (key and value)
3. Output: projected tokens used as prompts for the vision model decoder

---

## At inference

Visual tokens are **not decoded** by default — they exist only as latent vectors in the VLM's reasoning chain, conditioning subsequent token prediction. Dense prediction (mask, depth map, edge map) is only triggered when interpretability is desired. This keeps inference efficient.

---

## Design space notes

CoVT's 4 token types cover the 4 core vision-centric perceptual abilities identified in the literature: (i) instance recognition, (ii) 2D/3D spatial relationships, (iii) structure detection, (iv) deep semantic mining. The design space is not exhaustively explored — alternative or hybrid experts may yield better tokens for specific domains.

## Open question: causal effectiveness at inference

A key unresolved question raised by [[sources/whats-holding-back-latent-visual-reasoning]]: do generated latent tokens actually *causally* influence model predictions at inference, or does the model route around them? The paper showed this bypass occurs in crop-based latent approaches; CoVT's expert-aligned signal may avoid it, but the bypass intervention has not been applied to CoVT directly. Dataset design (ensuring intermediate tokens are genuinely non-redundant with the input image) is the primary lever the field now needs to pull.

**Mirage's answer** ([[sources/mirage-machine-mental-imagery]], CVPR 2026): explicitly ground latent tokens to visual representations in Stage 1 (cosine similarity to helper image embeddings) before removing supervision in Stage 2. t-SNE shows generated latents cluster near the visual manifold even after relaxation — architectural evidence against collapse. This is the first approach to directly engineer around the bypass/collapse failure mode at training time.

**Modal-Mixed CoT's answer** ([[sources/modal-mixed-cot-latent-embeddings]], UC San Diego, 2026): uses a **diffusion-based latent decoder** conditioned on VLM hidden states, with an explicit L2 reconstruction objective on compressed visual embeddings (256 → 32 tokens via average pooling). The diffusion decoder adds richer training signal than cosine similarity; ~2pp improvement over cosine loss variant in ablations. Bypass vulnerability is unverified — the VLM's own encoder is reused (not external expert transformations), so redundancy risk may be higher than CoVT.
