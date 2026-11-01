# BrewWise — Token Optimisation Strategy

> Estimated savings: **40–60% reduction** in per-scan token usage (from ~4,800 → ~2,000–2,800 output tokens) and **~90% total cost reduction** when combined with Gemini 2.5 Flash model tiering.

---

## Current Token Budget (Baseline)

| # | Module | Model | Est. Output Tokens | Calls/Scan |
|---|--------|-------|-------------------|------------|
| 1 | Vision extraction | Gemini Vision | ~1,500 | 1 |
| 2 | Evidence evaluation | Gemini Pro | ~800 | 1 |
| 3 | Recipe synthesis | Gemini Pro | ~2,000 | 1 |
| 4 | Recipe explanation | Gemini Pro | ~500 | 1 |
| 5 | Live recipe extraction | Gemini Flash | ~300 × N urls | 1–5 |
| 6 | Ingestion parser | Gemini Flash | ~400 | batch only |
| 7 | Reranker | Gemini Flash | ~200 | 1 |
| 8 | Feedback analyser | Gemini Pro | ~400 | on feedback |
| | **Core scan total** | | **~4,800** | **4** |
| | **With live discovery (5 URLs)** | | **~6,300** | **up to 9** |

---

## Optimisation Strategies (Ranked by Impact)

### 🔴 HIGH IMPACT — Architecture-Level Changes

#### 1. Merge Evidence Evaluation + Recipe Synthesis into a Single LLM Call

**Current:** Two separate calls — one to evaluate retrieval evidence (~800 tokens out), then a second to synthesise the recipe (~2,000 tokens out).

**Optimised:** A single call that receives the retrieval results, evaluates them inline, and directly produces the recipe with embedded provenance.

```python
# Before: 2 calls, ~2,800 output tokens
evidence = await llm.generate(evaluate_evidence_prompt, context)  # ~800 out
recipe = await llm.generate(generate_recipe_prompt, evidence)     # ~2,000 out

# After: 1 call, ~2,200 output tokens
recipe_with_provenance = await llm.generate(
    evaluate_and_synthesise_prompt,  # Combined prompt
    context
)  # ~2,200 out
```

**Savings:** ~600 output tokens + eliminates prompt overhead of the second call (~500 input tokens).

> [!IMPORTANT]
> This is the single highest-impact change. The evaluation outcome (A/B/C) can be a field within the recipe response schema rather than a separate call.

---

#### 2. Merge Recipe Explanation into the Synthesis Call

**Current:** Separate `explain_recipe.j2` call after recipe generation (~500 tokens out).

**Optimised:** Add `explanation` and `reasoning` fields directly into the recipe generation output schema.

```python
class PersonalisedRecipe(BaseModel):
    # ... all existing fields ...
    
    # Previously a separate LLM call — now part of generation schema
    explanation: RecipeExplanation
    reasoning_summary: str  # Why these parameters were chosen
```

**Savings:** ~300 output tokens + eliminates one entire LLM round-trip.

---

#### 3. Use Gemini Flash Everywhere (Not Pro)

**Current architecture** specifies Gemini Pro for synthesis/reasoning tasks.

**Optimised:** Use **Gemini 2.5 Flash** for ALL tasks. Flash models are:
- **Significantly cheaper** (often 10–20× per token)
- Fast enough for structured extraction
- With structured output mode, quality difference vs Pro is minimal for this domain

Reserve Pro only for edge cases where Flash quality is measurably worse (validate through evals).

| Task | Current Model | Optimised Model | Cost Reduction |
|------|--------------|-----------------|----------------|
| Vision extraction | Gemini Vision | Gemini Flash (multimodal) | ~10× cheaper |
| Evidence eval | Gemini Pro | Gemini Flash | ~10× cheaper |
| Recipe synthesis | Gemini Pro | Gemini Flash | ~10× cheaper |
| Explanation | Gemini Pro | Gemini Flash | ~10× cheaper |
| Feedback analysis | Gemini Pro | Gemini Flash | ~10× cheaper |

> [!TIP]
> Gemini 2.5 Flash supports multimodal input, structured JSON output, and function calling — everything BrewWise needs. Start with Flash and only upgrade to Pro if eval scores drop below threshold.

---

### 🟡 MEDIUM IMPACT — Prompt & Schema Optimisation

#### 4. Compress Prompt Templates

**Techniques:**
- Remove few-shot examples from production prompts (move to system instructions or fine-tuning)
- Use terse field names in JSON schemas (`dose_g` → `d`, `water_temperature_c` → `wt`) and map back in code
- Remove verbose instructional text; use structured output mode to enforce schema compliance instead

```python
# Before: verbose prompt with examples (~1,200 input tokens)
"""You are an expert barista... Given the following coffee profile, generate 
a complete pour-over recipe. The recipe must include... [500 words of instructions]
Here are some examples: [3 few-shot examples, ~400 tokens each]"""

# After: minimal prompt + schema enforcement (~300 input tokens)  
"""Generate pour-over recipe for this coffee. Use structured output schema.
Rules: only use visible bag data, no fabricated sources, mark unknowns as null."""
```

**Savings:** ~500–800 input tokens per call × 4 calls = ~2,000–3,200 input tokens.

---

#### 5. Slim Down the Output Schema

The current `PersonalisedRecipe` schema is very detailed (35+ fields). Not all fields need LLM generation.

**Fields the LLM should generate:**
```
dose_g, water_g, ratio, water_temperature_c, grind_description, 
bloom_water_g, bloom_time_seconds, pour_schedule (3-5 steps),
target_brew_time_seconds, expected_flavour, explanation
```

**Fields that should be computed/copied, NOT generated by LLM:**
```
recipe_id          → UUID generated in code
coffee_profile_id  → passed from context
source_type        → determined by evidence evaluation logic
source_recipes     → assembled from retrieval results in code
generation_model   → set from config
created_at         → datetime.now()
confidence         → computed from evidence + extraction confidence
dripper            → copied from user's equipment profile
grinder            → copied from user's equipment profile  
filter_type        → copied from user's equipment profile
```

**Savings:** ~400 output tokens per recipe generation.

---

#### 6. Reduce Vision Extraction Output

Current extraction returns per-field confidence, source, and raw_text for 13+ fields.

**Optimised:** Use a compact extraction schema:
```python
# Before: ~1,500 output tokens
class ExtractedField(BaseModel):
    value: str | None
    confidence: float
    source: Literal["bag_text", "inferred", "unknown"]
    raw_text: str | None  # ← often duplicates `value`

# After: ~600 output tokens  
class ExtractedField(BaseModel):
    v: str | None       # value
    c: float            # confidence (0-1)
    # source is always "bag_text" (enforce in prompt), remove field
    # raw_text removed — only include if c < 0.7
```

Map short keys back to full names in a post-processing step. The LLM generates fewer tokens, you expand in code.

**Savings:** ~900 output tokens on vision extraction.

---

### 🟢 LOWER IMPACT — Caching & Dedup

#### 7. Aggressive Result Caching

Already in the architecture, but emphasise these:

| Cache Key | TTL | Saves |
|-----------|-----|-------|
| `image_hash → CoffeeProfile` | 30 days | Entire vision call if same image re-scanned |
| `coffee_identity → retrieval_results` | 7 days | Evidence eval + retrieval for same coffee |
| `coffee_identity + equipment → recipe` | 24 hours | Full recipe generation for same combo |
| `url_hash → extracted_recipe` | 30 days | Live discovery extraction for known URLs |

#### 8. Skip Live Discovery for Known Coffees

If the coffee identity resolves to an existing profile in the KB with ≥3 high-quality recipes, **skip live discovery entirely**.

```python
if kb_recipe_count >= 3 and avg_confidence >= 0.8:
    # Skip live discovery — we have enough evidence
    live_result = LiveDiscoveryResult(status="skipped_sufficient_kb")
else:
    live_result = await discovery_service.search(coffee_profile)
```

**Savings:** Up to 5 LLM calls (1,500 tokens) for repeat/popular coffees.

---

#### 9. Batch Live Discovery Extraction

Instead of calling the LLM once per fetched URL, batch all cleaned page contents into a single call:

```python
# Before: N separate calls (one per URL)
for url, content in fetched_pages:
    recipe = await llm.generate(extract_recipe_prompt, content)  # 300 tokens × N

# After: Single batched call
all_content = "\n---PAGE_BREAK---\n".join(cleaned_pages)
recipes = await llm.generate(
    batch_extract_recipes_prompt, 
    all_content
)  # ~800 tokens total for up to 5 pages
```

**Savings:** ~700 tokens for 5 URLs (800 vs 1,500).

---

## Optimised Token Budget

| # | Module | Change | New Est. Output Tokens |
|---|--------|--------|----------------------|
| 1 | Vision extraction | Slim schema (short keys) | **~600** (was 1,500) |
| 2+3 | Evidence eval + Recipe synthesis | **Merged** into single call | **~2,000** (was 2,800) |
| 4 | Recipe explanation | **Merged** into synthesis | **0** (was 500) |
| 5 | Live discovery extraction | Batched | **~800** (was 1,500 for 5 URLs) |
| | **Optimised core scan** | | **~2,600** |
| | **With live discovery** | | **~3,400** |

### Summary

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Core LLM calls per scan | 4 | **2** | 50% fewer calls |
| Core output tokens | ~4,800 | **~2,600** | **46% reduction** |
| With live discovery (calls) | up to 9 | **3** | 67% fewer calls |
| With live discovery (tokens) | ~6,300 | **~3,400** | **46% reduction** |
| Input token overhead (prompts) | ~4,000 | **~1,500** | **62% reduction** |
| Model cost (Flash vs Pro) | baseline | **~10× cheaper** | ~90% cost reduction |

---

## Implementation Priority

| Priority | Change | Effort | Impact |
|----------|--------|--------|--------|
| 🥇 P0 | Switch all calls to Gemini Flash | Config change | Huge cost savings |
| 🥈 P1 | Merge eval + synthesis + explanation into 1 call | Prompt rewrite + schema update | Cuts 2 calls |
| 🥉 P2 | Slim extraction schema (short keys) | Schema change + mapper | ~900 tokens saved |
| P3 | Compress prompt templates | Prompt rewrite | ~2,000 input tokens saved |
| P4 | Aggressive caching (image hash, recipe cache) | Backend implementation | Eliminates repeat calls |
| P5 | Skip live discovery for well-known coffees | Logic check | Up to 5 calls eliminated |
| P6 | Batch live discovery extraction | Prompt + logic change | ~700 tokens saved |

> [!NOTE]
> **P0 alone** (switching to Flash) reduces **cost by ~90%** even without reducing token count. Combined with P1–P2, you get both fewer tokens *and* cheaper tokens.
