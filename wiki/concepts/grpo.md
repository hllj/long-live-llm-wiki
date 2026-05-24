# GRPO

**Full name**: Group Relative Policy Optimization  
**Type**: Reinforcement learning training algorithm  
**Origin**: Introduced in DeepSeek-Math; widely adopted across multimodal reasoning research after DeepSeek-R1

---

## What It Is

GRPO is a policy gradient RL algorithm that eliminates the need for a separate critic model (unlike PPO). For each prompt, it samples a **group of G candidate responses**, uses the group's mean reward as the value baseline, and computes per-response advantages by normalizing within the group:

```
Advantage(i) = (reward(i) − mean(group rewards)) / std(group rewards)
```

A **KL divergence penalty** against a frozen reference policy constrains drift during training — stabilizing learning but limiting how far the model can explore from its initialization.

**Common reward signals in VLM research**: binary accuracy (correct/incorrect), format compliance, or a combination of both.

---

## Why It's Widely Used

- No external critic model required — simpler than PPO
- Works with sparse binary rewards — doesn't require dense process supervision
- Group normalization stabilizes training on language model outputs
- Strong results on math/code reasoning tasks motivated broad adoption after DeepSeek-R1

---

## Where It Appears in This Wiki

GRPO is the dominant RL method across VLM reasoning approaches — mentioned in 14 content pages:

| Approach | Role of GRPO | Outcome |
|---|---|---|
| Mirage | Stage 3 — refines latent tokens after two-stage distillation | 89% VSP Spatial Reasoning (+4pp over CoT+GRPO baseline) |
| SpatialLadder | Stage 3 — dual reward (format + accuracy) | +23.4% avg over base; beats GPT-4o by 20.8% |
| Modal-Mixed CoT | Stage 2 — binary accuracy on VisuLogic | V* Attribute 80.2%, Spatial 78.9% (SFT); degrades abstract logic (see below) |
| CoVT | Not used | — |
| VaLR | Not primary | — |
| PEARL | Not used | — |
| LaCoT | Ablation baseline | **Underperforms zero-shot** (see Critical Nuance below) |

---

## Critical Nuance: GRPO Can Degrade Performance

[[sources/lacot-latent-chain-of-thought]] (RIT/Snap, Oct 2025) is the most important GRPO finding in this wiki:

**On complex visual reasoning benchmarks, GRPO underperforms zero-shot**:

| Method | MathVista | MathVerse | MMMU |
|---|---|---|---|
| Zero-shot | 63.7% | 38.2% | 50.0% |
| SFT | 62.7% | 38.7% | 50.6% |
| **GRPO** | **62.6%** | **36.8%** | **47.9%** |
| GFlowNet (RGFN) | **68.4%** | **43.3%** | **54.9%** |

**Root cause**: the KL penalty prevents exploration of reasoning paths that diverge significantly from the reference policy, blocking discovery of better-than-reference solutions.

**Alternative**: LaCoT's GFlowNet (RGFN) samples reward-proportionally without KL constraints — no catastrophic forgetting, free exploration within quality bounds. Outperforms GRPO by **5.7–6.5pp**.

[[sources/modal-mixed-cot-latent-embeddings]] independently corroborates this on a different benchmark: GRPO degrades abstract logic tasks (LogicVista Spatial: 31.6% SFT → 25.3% RL).

---

## When GRPO Works vs. When It Degrades

The wiki's evidence suggests the failure mode is **task-dependent**:

| Task type | GRPO outcome | Evidence |
|---|---|---|
| Spatial/visual perception tasks | Works well | Mirage (+4pp), SpatialLadder (+23.4% avg) |
| Abstract multi-step logical reasoning | Degrades | LaCoT (−1.1% to −2.1pp vs zero-shot); Modal-Mixed CoT on LogicVista |

**Likely reason**: spatial perception tasks have clear visual reward signals; abstract logic tasks require diverse exploration that KL penalty blocks.

---

## Related Pages

- [[sources/lacot-latent-chain-of-thought]] — primary source for GRPO degradation finding; GFlowNet (RGFN) as alternative
- [[sources/mirage-machine-mental-imagery]] — GRPO Stage 3 successfully applied to spatial reasoning
- [[sources/spatialladder]] — GRPO Stage 3 successfully applied to spatial perception
- [[sources/modal-mixed-cot-latent-embeddings]] — GRPO degrades abstract logic (LogicVista); independent corroboration
- [[sources/mcot-deep-thinking-survey]] — "SFT+RL > either alone" general finding; nuanced by LaCoT's result
- [[analyses/vlm-reasoning-training-findings]] — "GRPO can degrade reasoning" cross-cutting takeaway
- [[concepts/lmrm-roadmap]] — Stage 3 training paradigms context
