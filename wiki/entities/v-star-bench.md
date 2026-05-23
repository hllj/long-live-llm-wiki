# V*Bench

**Full name**: V* Benchmark (Visual-Star Benchmark)  
**Wiki role**: Primary benchmark for fine-grained visual grounding and attribute/spatial understanding — used by PEARL, Modal-Mixed CoT, and the bypass paper as the main evaluation surface for causal latent token use.

---

## What It Tests

V*Bench evaluates precise visual grounding across two subtasks:

- **Attribute**: attribute recognition and object property questions requiring accurate localization (e.g., color, texture, material of a specific object)
- **Spatial**: spatial relationship understanding between named objects

The benchmark requires the model to accurately identify specific image regions and reason about their properties — testing whether visual reasoning is genuinely grounded in the right pixels or driven by text statistics.

---

## Why It Matters for This Wiki

V*Bench appears across divergent approaches (bypass paper, PEARL, Modal-Mixed CoT) because it is sensitive to whether latent reasoning tokens are causally contributing. If a model achieves high V* scores whether or not its latent tokens are present, those tokens are not influencing inference. This makes V*Bench an implicit test of the bypass problem in addition to a grounding benchmark.

---

## Cross-Paper Results

### Single-model V* (combined or per-subtask)

| Model / Approach | V* Attribute | V* Spatial | Notes |
|---|---|---|---|
| PEARL (single-type, LVR data) | — | — | **81.5%** combined; [[sources/pearl-predictive-embedding-alignment]] |
| Modal-Mixed CoT (SFT) | **80.2%** | **78.9%** | [[sources/modal-mixed-cot-latent-embeddings]] |

### PEARL ThinkMorph (4-tool multi-step)

| Model | V* |
|---|---|
| SFT baseline | ~42.4% |
| PEARL | **~73.8%** (+31pp) |

Source: [[sources/pearl-predictive-embedding-alignment]]

### Modal-Mixed CoT generalization to Qwen3-VL-4B

| Subtask | Baseline | With latent embeddings | Gain |
|---|---|---|---|
| V* Attribute | 41.7% | 76.7% | **+35pp** |
| V* Spatial | 35.5% | 77.6% | **+42pp** |

Source: [[sources/modal-mixed-cot-latent-embeddings]]

### Bypass paper intervention (LVR, Monet, ILVR, LanteRn)

[[sources/whats-holding-back-latent-visual-reasoning]] tested 4 latent models on V*Bench and found accuracy was **unchanged** when generated latent tokens were replaced with zeros, noise, or random subregions. V*Bench (alongside BLINK) was the primary evaluation surface for the latent bypass intervention.

---

## Related Pages

- [[sources/pearl-predictive-embedding-alignment]] — 81.5% combined V*; ThinkMorph +31pp over SFT; bypass-immune design
- [[sources/modal-mixed-cot-latent-embeddings]] — V* Attribute 80.2%, Spatial 78.9%; Qwen3-VL-4B generalization +35–42pp
- [[sources/whats-holding-back-latent-visual-reasoning]] — bypass intervention on V*Bench; latent tokens shown to be causally unused
- [[analyses/vlm-reasoning-training-findings]] — bypass finding and causal token use discussion
- [[concepts/visual-reasoning-in-vlms]] — paradigm taxonomy with V* as benchmark reference
- [[entities/vsi-bench]] — the other primary benchmark in this wiki; tests multi-view spatial reasoning (distinct task type)
