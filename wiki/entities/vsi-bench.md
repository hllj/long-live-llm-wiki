# VSI-Bench

**Full name**: Visual Spatial Intelligence Benchmark  
**Wiki role**: Primary benchmark for multi-view spatial reasoning — every latent visual reasoning approach in this wiki reports results here; the clearest discriminator between static and per-step visual grounding.

---

## What It Tests

VSI-Bench evaluates spatial intelligence from **multi-view video inputs**: given frames from an indoor scene captured at multiple viewpoints, the model answers quantitative spatial questions. Tasks include:

- **Absolute Distance**: estimate metric distances between objects
- **Room Size**: estimate room dimensions
- **Object Size**: estimate object dimensions
- **Relative Direction / Depth**: identify spatial relationships across views
- **Route Planning**: navigate paths through the scene

The core challenge is **sustained cross-view visual grounding** — the model must integrate spatial information across multiple frames from different angles rather than reasoning from a single image. This directly stress-tests whether visual reasoning is maintained across a long chain or collapses to language statistics.

---

## Why It Matters for This Wiki

VSI-Bench has become the de facto discriminative benchmark for latent visual reasoning because:

1. **It exposes static injection failure**: models that inject visual information only once (CoVT, Monet, LVR) all score *below* their base model — the injected tokens cannot maintain grounding across a long multi-view chain.
2. **It rewards per-step grounding**: VaLR's per-step REPA checkpointing is the first approach to systematically improve on VSI-Bench beyond the GPT-4o baseline.
3. **It enables test-time scaling**: VaLR is the only approach where longer reasoning chains monotonically improve VSI-Bench performance — text-only CoT baselines degrade with more tokens.

---

## Cross-Paper Leaderboard

| Model | VSI-Bench | Notes |
|---|---|---|
| VaLR-M (multi-encoder) | **52.9%** | [[sources/valr-vision-aligned-latent-reasoning]]; per-step REPA; DINOv3+CLIP/SigLIPv2+π³ |
| VaLR-S (single-encoder) | 41.5% | [[sources/valr-vision-aligned-latent-reasoning]]; DINOv3 only |
| Spatial-MLLM (4B) | 47.3% | Specialised 3D encoders |
| SpatialLadder (3B) | 45.7% | [[sources/spatialladder]]; standard VLM architecture, no 3D encoders |
| GPT-4o | 34.0% | Closed-source baseline |
| Base Qwen2.5-VL | 33.0% | Unmodified baseline |
| CoVT | 18.6% | [[sources/covt-chain-of-visual-thought]]; **below base model** — static injection collapses |
| LVR | 18.4% | [[sources/whats-holding-back-latent-visual-reasoning]]; below base model |
| Monet | 14.0% | [[sources/whats-holding-back-latent-visual-reasoning]]; below base model |

**Key finding**: every static single-step latent injection model scores below the unmodified base model. VaLR's per-step checkpointing is the first approach to substantially exceed GPT-4o.

---

## VaLR Sub-Task Gains Over Base

| Task | Gain |
|---|---|
| Room Size | +35.9pp |
| Absolute Distance | +25.8pp |
| Object Size | +20.8pp |

---

## Related Pages

- [[sources/valr-vision-aligned-latent-reasoning]] — primary VSI-Bench paper; per-step REPA checkpointing; sub-task results
- [[sources/spatialladder]] — 3B model reaches 45.7% without specialised encoders; Stage 1 grounding key
- [[sources/covt-chain-of-visual-thought]] — 18.6% (below base); motivates per-step grounding
- [[sources/whats-holding-back-latent-visual-reasoning]] — static latent collapse (Monet 14%, LVR 18.4%); all below base model
- [[analyses/vlm-reasoning-training-findings]] — cross-cutting takeaways: static injection collapses on multi-view; test-time scaling requires visual grounding
- [[analyses/covt-limitations-and-research-directions]] — VaLR's VSI-Bench result is the sharpest evidence of CoVT's static injection limitation
- [[concepts/visual-attention-in-vlms]] — attention imbalance is the root mechanistic cause of spatial reasoning difficulty
