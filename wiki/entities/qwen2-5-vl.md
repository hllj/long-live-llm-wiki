# Qwen2.5-VL

A Vision-Language Model from the Qwen team (Alibaba). Used as the primary base model in [[sources/covt-chain-of-visual-thought]], [[sources/mirage-machine-mental-imagery]], and [[sources/lacot-latent-chain-of-thought]].

**Variant tested**: Qwen2.5-VL-7B  
**Reference**: arXiv 2502.13923

---

## Role in CoVT

CoVT's main experiments use Qwen2.5-VL-7B as the backbone. The VLM is finetuned with LoRA (rank=16, alpha=32) while the projection layers are trained from scratch. The frozen visual encoder is supplemented by the [[concepts/continuous-visual-tokens|continuous visual token mechanism]] defined in [[concepts/chain-of-visual-thought|CoVT]].

**Baseline scores** (before CoVT):
- CV-Bench: 74.5
- CV-Bench Depth: 72.8
- HRBench8K: 64.9
- MME-RealWorld: 60.0
- MMVP: 56.0

All of these improve substantially with CoVT — see [[sources/covt-chain-of-visual-thought]] for full results.

---

## Role in Mirage

Mirage ([[sources/mirage-machine-mental-imagery]]) uses Qwen2.5-VL-7B as its base model. Unlike CoVT which freezes the backbone and adds projection layers, Mirage trains the full model through two stages (distillation grounding + relaxation) and GRPO RL, using a single H100 GPU (~18h total).

A 3B variant was also tested, showing +5% on Jigsaw and +10% on SAT Real over text-only baselines — confirming smaller models benefit more from latent visual reasoning.

---

## Role in LaCoT

LaCoT ([[sources/lacot-latent-chain-of-thought]]) uses Qwen2.5-VL-7B both as the base policy model (qθ, LoRA-trained) and to initialize the reward model (πΦ, fine-tuned on 250K reasoning samples). LaCoT training achieves MathVista 68.4%, MathVerse 43.3%, MMMU 54.9% from the Qwen2.5-VL-7B baseline.

---

## Notes

Qwen3-VL-Thinking (a later model with text CoT baked in) performs *worse* than Qwen3-VL-Instruct on spatial benchmarks, motivating CoVT's approach of continuous visual rather than text reasoning. [[sources/modal-mixed-cot-latent-embeddings]] tests generalization of its latent approach to Qwen3-VL-4B, achieving +35pp Attribute and +42pp Spatial on V* over that baseline.
