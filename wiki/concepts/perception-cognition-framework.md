# Perception-Cognition Framework for VLMs

A two-layer functional framework for analysing vision-language reasoning in MLLMs, proposed in [[sources/perception-cognition-survey]] (Sep 2025). Complements the historical [[concepts/lmrm-roadmap]] — where the roadmap asks "when did this approach appear?", this framework asks "what computation does it perform?".

**Core claim**: "The ability to process pixels does not yet confer the ability to construct a coherent, credible internal world model." Hallucination is a symptom of the perception-cognition disconnect, not an isolated defect.

---

## Two Layers

### Perception Layer
Foundational abilities that must be in place before cognition can succeed:
- Accurately extract visual information from images
- Encode raw visual data into semantically meaningful representations
- Recognize objects, attributes, spatial relationships, contextual associations
- Achieve fine-grained vision-text alignment
- Provide reliable visual evidence for subsequent reasoning steps

**Failure modes at this layer**: weak low-level visual extraction (CLIP-ViT optimized for global alignment, not fine-grained geometry); limited vision-text interaction (global relevance mapping rather than region-specific pixel mapping).

### Cognition Layer
Higher-order capabilities that require a reliable perception layer to function:
- Proactive, goal-oriented multi-step reasoning
- Determining *when* and *where* to examine visual information
- Dynamically assessing information sufficiency at each step
- Integrating textual and visual data iteratively
- Forming "observe-think-verify" closed-loop cycles

**Failure modes at this layer**: lacking executable task decomposition (single-step or fixed templates); static memory-based reasoning (single-pass visual encoding without revisiting images causes decoupling between final answer and visual facts, exacerbating hallucination in long-chain tasks).

---

## Hallucination as a Structural Symptom

Hallucination in MLLMs is typically treated as an isolated problem. This framework reframes it: hallucination emerges when the cognition layer operates on unreliable perceptual evidence, or when linguistic priors dominate over visual facts in long reasoning chains. The fix must target the perception-cognition interface, not just decoding.

---

## Evidence Injection Taxonomy (Category 4)

The most directly actionable part of the framework for wiki approaches. All methods that inject visual evidence into the reasoning chain are classified as either:

**Endogenous** (internal attention mechanisms, no external tools):
| Sub-type | Examples |
|---|---|
| Single forward pass | ICoT ([[sources/icot-interleaved-modal-chain-of-thought]]), CVC, MINT-CoT, Look-back |
| Multiple forward passes | DeepEyes, Pixel Reasoner, CogCoM, SIFThinker |

**Exogenous** (external tool calling):
| Sub-type | Examples |
|---|---|
| In-context learning | ViperGPT, MM-ReAct, CLOVA, Visual Sketchpad |
| Fine-tuning | LLaVA-Plus, TACO, VTool-R1 |

**CoVT** ([[sources/covt-chain-of-visual-thought]]) and **Mirage** ([[sources/mirage-machine-mental-imagery]]) are both endogenous single-forward-pass methods that go further than ICoT by generating *new perceptual signals* (expert tokens or self-generated latents) rather than re-using input patches.

**Key empirical finding**: dynamic evidence injection (multiple forward passes with targeted visual re-encoding) outperforms static single-pass encoding for complex reasoning tasks.

---

## Training Findings from This Framework

- **Process supervision > outcome supervision**: +4–10 percentage points from supervising intermediate step correctness (Best-of-N sampling)
- **Interleaved CoT > sequential**: jointly generating text and visual evidence outperforms text-then-vision or vision-then-text
- **Dynamic > static encoding**: multiple passes with re-encoding beats single static encoding

---

## Mapping Wiki Approaches

| Approach | Layer addressed | Evidence injection type |
|---|---|---|
| AdaptVis | Perception (attention distribution) | None (attention reshaping only) |
| ICoT | Perception → Cognition interface | Endogenous, single pass |
| CoVT | Perception → Cognition interface | Endogenous, single pass (expert tokens) |
| Mirage | Perception → Cognition interface | Endogenous, single pass (self-generated latents) |
| ViperGPT / Tool-augmented | Cognition (external delegation) | Exogenous |

---

## Relationship to Other Frameworks

| Framework | Organises by | Scope |
|---|---|---|
| LMRM Roadmap ([[concepts/lmrm-roadmap]]) | Historical development (4 stages) | Broad — all multimodal reasoning |
| Perception-Cognition Framework (this page) | Functional computation (2 layers) | VL interactive reasoning |
| Spatial Reasoning Taxonomy ([[concepts/spatial-reasoning-taxonomy]]) | Cognitive task type (3 dimensions) | Spatial reasoning specifically |

---

## Related Pages

- [[sources/perception-cognition-survey]] — source paper proposing this framework
- [[concepts/lmrm-roadmap]] — complementary historical taxonomy
- [[concepts/spatial-reasoning-taxonomy]] — complementary spatial-specific taxonomy
- [[sources/icot-interleaved-modal-chain-of-thought]] — endogenous single-pass evidence injection
- [[sources/covt-chain-of-visual-thought]] — endogenous single-pass with novel expert signal
- [[sources/mirage-machine-mental-imagery]] — endogenous single-pass with self-generated latents
- [[sources/whats-holding-back-latent-visual-reasoning]] — bypass problem is a cognition-layer failure: models skip the evidence the perception layer generated
- [[analyses/vlm-reasoning-training-findings]] — process supervision and dynamic encoding findings
