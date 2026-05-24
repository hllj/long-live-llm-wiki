# LaCoT: Latent Chain-of-Thought for Visual Reasoning

**Paper**: Latent Chain-of-Thought for Visual Reasoning  
**Authors**: Guohao Sun, Hang Hua, Jian Wang, Jiebo Luo, Sohail Dianat, Majid Rabbani, Raghuveer Rao, Zhiqiang Tao  
**Affiliations**: Rochester Institute of Technology, Snap Inc., University of Rochester, DEVCOM Army Research Laboratory  
**arXiv**: 2510.23925  
**Code**: https://github.com/heliossun/LaCoT  

**Sources**: [[analyses/vlm-reasoning-training-findings]], [[concepts/visual-reasoning-in-vlms]], [[sources/mcot-deep-thinking-survey]]

> **Terminology note**: "Latent" here means *text reasoning chain sequences treated as latent variables in a probabilistic inference framework* — NOT visual latent tokens. LaCoT is a training algorithm for text CoT quality, distinct from CoVT/Mirage/VaLR/PEARL which generate latent *visual* tokens.

---

## Core Contribution

LaCoT reformulates visual reasoning as **posterior inference** over latent reasoning chains: given input X and desired answer Y, sample chain Z ~ P(Z|X,Y). Instead of the common approach of using RL with outcome rewards (GRPO) or supervised imitation (SFT), LaCoT trains a policy via **Generative Flow Networks (GFlowNets)** to sample reasoning chains proportional to their rewards — generating diverse, high-quality rationales.

**Key insight**: GRPO's KL penalty constrains exploration, preventing the model from discovering better-than-reference reasoning paths. GFlowNet's flow-matching objective has no such constraint — it samples from the full reward-proportional distribution.

---

## Three Technical Components

### 1. Interpolated SubTB (ISubTB) — Token-Level Reward Approximation
Computing exact rewards for all tokens in 700-token reasoning chains is prohibitively expensive. ISubTB uses linear interpolation within segments of length λ=8:

```
R̃(z₁:t+i) = R(z₁:t) + (i/λ)[R(z₁:t+λ) − R(z₁:t)]
```

**Theoretical guarantee**: O(λ²) approximation error under bounded second derivatives — flow consistency preserved when λ is small.

### 2. Reference-Guided GFlowNet Fine-tuning (RGFN) — Avoiding Catastrophic Forgetting
Unconstrained GFlowNet exploration generates high-probability but meaningless outputs. RGFN uses annealed reference filtering:

- Sample m=6 candidate rationales {Z₁, ..., Zₘ} from the current policy
- Filter: only keep Zᵢ where reward R(Zᵢ) > δₛ · R(Z_ref) (better than reference)
- Annealing schedule: δₛ = τ_max − (τ_max − τ_min) · min(1, s/50)
- Backpropagate only through passing candidates

**Result**: Free exploration within quality constraints — no KL penalty, no catastrophic forgetting.

### 3. Bayesian Inference over N (BiN) — Inference-Time Scaling Without Reward Models
Replaces Best-of-N (BoN) — which requires an external reward model to select the best of N answers — with probabilistic answer ranking via marginal likelihood:

1. Sample N latent rationales Zᵢ ~ qθ(Z|X)
2. Generate answers Y⁽ⁱ⁾ ~ πΦ(Y|X,Zᵢ) for each
3. Compute length-normalized joint likelihood: P(Yᵢ|X) ≈ (1/N)Σⱼ (1/|ZᵢYᵢ|) πΦ(ZᵢYᵢ|X)
4. Return answer with highest estimated marginal likelihood

**Advantages over BoN**: no external reward model, probabilistically grounded, interpretable.

---

## Results

### Main benchmarks (Qwen2.5-VL-7B, LaCoT-RGFN + BiN)
| Benchmark | Baseline | LaCoT-7B | Δ |
|---|---|---|---|
| MathVista | 63.7% | **68.4%** | +4.7pp |
| MathVerse | 38.2% | **43.3%** | +5.1pp |
| MMMU val | 50.0% | **54.9%** | +4.9pp |
| MMVet | 70.5% | **74.2%** | +3.7pp |

### Training method comparison (7B, ablation Table 3)
| Method | MathVista | MathVerse | MMMU |
|---|---|---|---|
| Zero-shot | 63.7% | 38.2% | 50.0% |
| SFT | 62.7% | 38.7% | 50.6% |
| GRPO | 62.6% | 36.8% | 47.9% |
| **RGFN (LaCoT)** | **68.4%** | **43.3%** | **54.9%** |

**Critical finding**: GRPO *underperforms zero-shot and SFT* on these benchmarks — its KL penalty constrains exploration and degrades performance. RGFN outperforms by 5.7–6.5pp absolute.

### BiN vs Best-of-N (same policy, N=5–10)
| Model | Method | MathVerse | MathVista | MMMU | MMVet |
|---|---|---|---|---|---|
| 3B | BoN | 21.2% | 57.1% | 44.7% | 67.1% |
| 3B | BiN | **40.0%** | **63.2%** | **48.8%** | **69.6%** |
| 7B | BoN | 26.5% | 62.2% | 47.3% | 71.2% |
| 7B | BiN | **39.7%** | **68.4%** | **54.9%** | **74.2%** |

BiN outperforms BoN by **13–18.8pp** without external reward models. Remarkable gap on MathVerse (21.2% → 40.0% for 3B) — largest gains on complex multi-step reasoning.

### Small model comparison
**LaCoT-3B on MathVerse: 40.0% (vs. LLaVA-CoT-11B and LLaVA-OV-7B)** — a 3B model exceeds larger models purely via better training and inference strategy.

### BiN as general inference technique (Table 4)
Applied to standard Qwen2.5-VL-SFT (not LaCoT-trained) with N=5, T=0.7:
- 3B: +0.7–1.9pp across all benchmarks
- 7B: +1.7–1.9pp across all benchmarks

BiN is model-agnostic — improves any VLM at inference time without retraining.

---

## Implementation Details

- **Reward model (πΦ)**: fine-tuned LVLM on 250K mixed reasoning samples (LLaVA-CoT + R1-OneVision SFT); special `_Analyzer_` token
- **Policy (qθ)**: initialized from πΦ, LoRA-trained (r=64, α=128) on 3K visual reasoning samples using teacher-generated CoTs as reference rationales
- **Hardware**: 8×80GB GPUs; ~30h SFT, ~120h RGFN training
- **Inference**: N=5 → 30s avg; N=10 → 65s (batch k=5)
- **Optimal BiN temperature**: T=0.7; N=1 produces hallucinations on MMMU

---

## Key Findings for the Wiki

1. **GRPO can degrade reasoning**: On MathVista/MathVerse/MMMU, GRPO performs below zero-shot baseline. KL-penalty constraints block exploration to better reasoning paths — a concrete failure case for standard RL fine-tuning.
2. **GFlowNets beat GRPO for diverse exploration**: RGFN achieves +5.7–6.5pp over GRPO by sampling reward-proportionally without KL constraints.
3. **BiN > BoN by 13–18.8pp**: Probabilistic marginal likelihood ranking outperforms selecting highest-reward candidate — diversity in reasoning paths helps more than picking the greedy best.
4. **BiN is model-agnostic**: Works as a drop-in inference technique on any VLM (+1.7–1.9pp on standard Qwen2.5-VL without retraining).
5. **Diversity drives quality**: Higher temperature T=0.7 (more diverse rationales) outperforms greedy sampling; higher N consistently improves accuracy.

---

## LMRM Positioning

Stage 3 (System-2 long CoT with RL-based exploration). LaCoT represents a training paradigm between SFT and standard RL — GFlowNet occupies a novel position where it samples from the full reward distribution rather than optimizing a KL-penalized objective. See [[concepts/lmrm-roadmap]].

---

## Related Pages

- [[analyses/vlm-reasoning-training-findings]] — RGFN vs GRPO finding; BiN as inference-time scaling; diversity driving quality
- [[sources/mcot-deep-thinking-survey]] — MCoT survey's SFT+RL > either alone finding; LaCoT adds nuance: GRPO specifically can underperform, GFlowNet outperforms
- [[concepts/visual-reasoning-in-vlms]] — LaCoT improves text CoT quality without changing the reasoning paradigm; fits within Stage 3 text CoT approaches
- [[concepts/lmrm-roadmap]] — Stage 3 System-2 CoT with novel training algorithm
- [[concepts/grpo]] — GRPO concept page; LaCoT is the primary source for the GRPO degradation finding
