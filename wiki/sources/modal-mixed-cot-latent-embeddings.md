# Learning Modal-mixed Chain-of-thought Reasoning with Latent Embeddings

**Paper**: Learning Modal-mixed Chain-of-thought Reasoning with Latent Embeddings  
**Authors**: Yifei Shao, Kun Zhou, Ziming Xu, Mohammad Atif Quamar, Shibo Hao, Zhen Wang, Zhiting Hu, Biwei Huang  
**Affiliation**: University of California, San Diego  
**arXiv**: 2602.00574  

**Sources**: [[concepts/continuous-visual-tokens]], [[concepts/visual-reasoning-in-vlms]], [[sources/mirage-machine-mental-imagery]], [[sources/whats-holding-back-latent-visual-reasoning]]

---

## Core Contribution

Introduces **modal-mixed CoT** — interleaving textual reasoning tokens with compact visual "sketch" embeddings inside the reasoning chain. Unlike CoVT (external expert encoders) and Mirage (cosine distillation of hidden states), this approach uses a **diffusion-based latent decoder** to generate fine-grained visual details conditioned on the VLM's own hidden states, while reusing the VLM's vision encoder as the semantic anchor.

**Special tokens** `<START>` and `<END>` trigger transitions between text-generation and latent-generation modes, making the modality switch an explicit learned decision.

---

## Architecture

- **Encoder**: VLM's own vision encoder + connector — reused at no extra cost, ensures semantic alignment
- **Compression**: average pooling reduces 256 visual tokens → **32 latent tokens** (compact reasoning budget)
- **Decoder**: diffusion model (L2 denoising loss, ~50 denoising steps) conditioned on VLM hidden states
- **Modal switching**: `<START>` / `<END>` tokens; VLM learns when to switch modalities via RL

**Distinction from Mirage**: Mirage grounds latents via cosine similarity distillation from synthesized helper images; this paper uses a diffusion decoder with explicit reconstruction supervision. Both reuse no external expert models.

**Distinction from CoVT**: CoVT generates tokens from external expert models (SAM, DepthAnything) — genuinely non-redundant transformations. This paper uses the VLM's own encoder, so redundancy risk is higher.

---

## Training Strategy

### Stage 1: Supervised Fine-tuning (SFT)
Joint loss: next-token prediction (cross-entropy) + latent reconstruction (diffusion L2 loss):

```
L = L_text + λ · L_diffusion
```

- λ = 1.0 selected as optimal (λ = 0.1 over-weights text; λ = 10 degrades both)
- Trained on interleaved text-latent reasoning traces

### Stage 2: Reinforcement Learning (GRPO)
- Binary reward: 1 for correct answer, 0 otherwise
- Trained on VisuLogic (1,000 visual reasoning problems)
- Fixed learning rate: 5e-6
- **RL degrades abstract logic** (LogicVista Spatial: SFT 31.6% → RL 25.3%): attributed to lengthy output patterns not well captured by RL training signal

---

## Results

### Vision-intensive Reasoning (VCog-Bench, LogicVista, MM-IQ)
| Model | Average |
|---|---|
| Ours (SFT) | 26.7% |
| Ours (RL) | 25.7% |
| Best subtask: VCog-Bench CVR (SFT) | 42.4% |
| Best subtask: LogicVista Inductive (SFT) | 31.6% |

### Vision-intensive Perception (V* Benchmark, MME-Unify)
| Subtask | SFT | RL |
|---|---|---|
| V* Attribute | 80.2% | 77.8% |
| V* Spatial | 78.9% | 76.3% |

### Generalization (Qwen3-VL-4B)
| Subtask | Baseline | Ours |
|---|---|---|
| V* Attribute | 41.7% | 76.7% (+35pp) |
| V* Spatial | 35.5% | 77.6% (+42pp) |

Demonstrates cross-model scalability — approach is not tied to a specific base model.

### Key Ablations
- **Diffusion decoder vs cosine similarity loss**: 46.7% vs 44.7% average — diffusion adds ~2pp
- **Text-only baseline**: 40.6% vs diffusion 46.7% — latent embeddings help
- **Catastrophic forgetting check**: language-only performance 21.6% vs baseline 22.5% — preserved
- **Latent token budget**: optimal 32–64 tokens; spatial peaks at 64 (80.3%)
- **Efficiency**: latent generation 3.10s vs text-only 1.03s vs tool-based 8.36s

---

## Relationship to Bypass Problem

This paper does not directly test bypass vulnerability. Key signals:
- Uses VLM's **own vision encoder** (not expert transformations) → embeddings may contain information already in the input → bypass risk similar to crop-based models
- **Diffusion decoder** adds a non-trivial reconstruction objective → richer training signal than simple cosine loss or crop re-injection
- The VCog-Bench / LogicVista gains are modest (26–27%), so causal role of latents vs training supervision is unverified
- Contrasts with CoVT (expert outputs = genuine transformations, likely less bypass-prone) and Mirage (Stage 1 grounding explicitly prevents collapse)

---

## LMRM Positioning

Stage 3 (System-2 long CoT) in [[concepts/lmrm-roadmap]]. Modal-mixed CoT with latent embeddings is a parallel track to ICoT (patch re-injection) and Mirage (hidden-state recasting) — all sit in Stage 3 multi-modal deliberative reasoning.

---

## Related Pages

- [[sources/mirage-machine-mental-imagery]] — closest comparison: also generates latents from hidden states; cosine distillation vs diffusion decoder
- [[sources/covt-chain-of-visual-thought]] — external expert tokens vs self-generated latents; bypass risk contrast
- [[sources/whats-holding-back-latent-visual-reasoning]] — bypass and collapse framework; applies here; bypass not tested
- [[sources/icot-interleaved-modal-chain-of-thought]] — similar interleaved motivation; patches vs latent embeddings; no training vs two-stage
- [[concepts/continuous-visual-tokens]] — latent token design space; this paper adds diffusion decoder variant
- [[concepts/visual-reasoning-in-vlms]] — paradigm taxonomy; fits as a variant of paradigm 9 (self-generated latent tokens)
- [[analyses/vlm-reasoning-training-findings]] — SFT+RL finding; RL degrading abstract logic is a new nuance
- [[entities/v-star-bench]] — cross-paper V*Bench leaderboard; Attribute 80.2%, Spatial 78.9% (SFT); +35–42pp on Qwen3-VL-4B
- [[concepts/grpo]] — GRPO degradation on abstract logic (LogicVista Spatial: 31.6% SFT → 25.3% RL)
