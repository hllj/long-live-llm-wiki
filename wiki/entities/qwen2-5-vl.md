# Qwen2.5-VL

A Vision-Language Model from the Qwen team (Alibaba). Used as the primary base model in [[sources/covt-chain-of-visual-thought]].

**Variant tested**: Qwen2.5-VL-7B  
**Reference**: arXiv 2502.13923

---

## Role in CoVT

CoVT's main experiments use Qwen2.5-VL-7B as the backbone. The VLM is finetuned with LoRA (rank=16, alpha=32) while the projection layers are trained from scratch. The frozen visual encoder is supplemented by CoVT's continuous visual token mechanism.

**Baseline scores** (before CoVT):
- CV-Bench: 74.5
- CV-Bench Depth: 72.8
- HRBench8K: 64.9
- MME-RealWorld: 60.0
- MMVP: 56.0

All of these improve substantially with CoVT — see [[sources/covt-chain-of-visual-thought]] for full results.

---

## Notes

Qwen3-VL-Thinking (a later model with text CoT baked in) performs *worse* than Qwen3-VL-Instruct on spatial benchmarks, motivating CoVT's approach of continuous visual rather than text reasoning.
