# BrewWise — Phase-Wise Implementation Plan

> **Version:** 1.0 · **Last Updated:** 2026-10-30
> **Source documents:** [architecture.md](file:///Users/shaguftagurmukhdas/Downloads/CoffeeC/architecture.md) · [problemstatement.md](file:///Users/shaguftagurmukhdas/Downloads/CoffeeC/problemstatement.md)

---

## Table of Contents

1. [Implementation Principles](#1-implementation-principles)
2. [Phase Overview](#2-phase-overview)
3. [Phase 1 — Functional MVP (Weeks 1–3)](#3-phase-1--functional-mvp-weeks-13)
4. [Phase 2 — RAG-Based Recipe Discovery (Weeks 4–6)](#4-phase-2--rag-based-recipe-discovery-weeks-46)
5. [Phase 3 — Inline Live Web Discovery (Weeks 7–9)](#5-phase-3--inline-live-web-discovery-weeks-79)
6. [Phase 4 — Personalisation & Iterative Brewing (Weeks 10–12)](#6-phase-4--personalisation--iterative-brewing-weeks-1012)
7. [Cross-Phase: Testing & Quality Gates](#7-cross-phase-testing--quality-gates)
8. [Cross-Phase: DevOps & Infrastructure](#8-cross-phase-devops--infrastructure)
9. [Risk Register & Mitigations](#9-risk-register--mitigations)
10. [Definition of Done — Full Project](#10-definition-of-done--full-project)

---

## 1. Implementation Principles

| Principle | Meaning |
|---|---|
| **End-to-end first** | Each phase delivers a working vertical slice. No phase produces only backend or only frontend code in isolation. |
| **No hardcoded demos** | Every pipeline step (OCR, retrieval, generation) must use real providers — never stubbed data in production paths. |
| **Test alongside build** | Tests are written in the same week as the feature, not deferred to a "testing phase". |
| **Provider abstraction from day 1** | Even in Phase 1, AI providers are behind ABCs so they can be mocked in tests and swapped later. |
| **Progressive enhancement** | Phase 1 recipes are AI-generated with no RAG. Phase 2 adds retrieval. Phase 3 adds live search. Phase 4 adds personalisation. Each layer enhances without rewriting prior work. |
| **Token & cost efficiency by design** | Default to Gemini 2.5 Flash (~90% cost reduction). Merge LLM calls (eval + synthesis + explanation in 1 call). Use compact schemas with short keys and compressed prompts. Handle deterministic fields in code, never wasting LLM tokens. |

---

## 2. Phase Overview

```
Week  1 ──── 2 ──── 3 ──── 4 ──── 5 ──── 6 ──── 7 ──── 8 ──── 9 ──── 10 ──── 11 ──── 12
      │             │             │             │             │              │
      ├─────────────┤             │             │             │              │
      │  PHASE 1    │             │             │             │              │
      │  MVP        │             │             │             │              │
      │             ├─────────────┤             │             │              │
      │             │  PHASE 2    │             │             │              │
      │             │  RAG        │             │             │              │
      │             │             ├─────────────┤             │              │
      │             │             │  PHASE 3    │             │              │
      │             │             │  Live Search│             │              │
      │             │             │             ├─────────────┤              │
      │             │             │             │  PHASE 4    │              │
      │             │             │             │  Personal.  │              │
      │             │             │             │             ├──────────────┤
      │             │             │             │             │  POLISH &    │
      │             │             │             │             │  EVAL        │
```

| Phase | Weeks | Goal | Key FR Coverage |
|---|---|---|---|
| **Phase 1** | 1–3 | Image → AI-generated recipe, working E2E | FR-1, FR-2, FR-6, FR-7 (basic), FR-10 |
| **Phase 2** | 4–6 | Knowledge base + hybrid RAG retrieval | FR-3 (batch), FR-4, FR-5, FR-9 |
| **Phase 3** | 7–9 | Inline live web discovery during scan | FR-3 (inline), FR-5 (live), FR-9 |
| **Phase 4** | 10–12 | User accounts, equipment profiles, brew history, feedback loop | FR-7 (full), FR-8, FR-10 (polish) |

---

## 3. Phase 1 — Functional MVP (Weeks 1–3)

### 3.1 Phase Goal

> A user can photograph a coffee bag, review extracted metadata, optionally select basic equipment, and receive a complete AI-generated pour-over recipe — all through a working, mobile-responsive UI.

### 3.2 Week 1: Project Foundation & Vision Pipeline

#### 1.1 — Project Scaffolding

| Item | Details |
|---|---|
| **Task** | Initialise the monorepo with backend (FastAPI) and frontend (React + Vite + TypeScript) |
| **Files created** | `brewwise/main.py`, `brewwise/config.py`, `brewwise/dependencies.py`, `frontend/src/main.tsx`, `docker-compose.yml`, `.env.example` |
| **Acceptance** | `docker compose up` starts backend (port 8000), frontend (port 3000), PostgreSQL, Redis, and MinIO. Health endpoint responds at `/api/v1/health`. |

**Subtasks:**

- [ ] Create `brewwise/` Python package with FastAPI app factory and lifespan handler
- [ ] Create `brewwise/config.py` with `Settings(BaseSettings)` — all env vars from architecture Appendix A
- [ ] Create `brewwise/api/v1/health.py` — `GET /api/v1/health` returns `{"status": "ok"}`
- [ ] Create `brewwise/api/v1/router.py` — aggregated v1 router
- [ ] Set up `pyproject.toml` with dependencies (fastapi, uvicorn, sqlalchemy, pydantic, etc.)
- [ ] Scaffold React app with Vite (`npx create-vite@latest ./ --template react-ts`)
- [ ] Set up CSS Modules structure in `frontend/src/styles/`
- [ ] Create `docker-compose.yml` with all 5 services (frontend, backend, postgres, redis, minio)
- [ ] Create `.env.example` with all documented environment variables
- [ ] Verify `docker compose up` runs cleanly end-to-end

#### 1.2 — Provider Abstraction Layer

| Item | Details |
|---|---|
| **Task** | Create ABC interfaces for all external providers |
| **Files created** | `brewwise/providers/llm/base.py`, `brewwise/providers/llm/gemini.py`, `brewwise/providers/embeddings/base.py`, `brewwise/providers/storage/base.py`, `brewwise/providers/storage/local.py`, `brewwise/services/vision/base.py` |
| **Acceptance** | Provider ABCs have typed method signatures. Gemini LLM provider passes a basic integration test. |

**Subtasks:**

- [ ] Define `LLMProvider` ABC with `generate_structured()` and `generate_text()` methods
- [ ] Implement `GeminiLLMProvider` using `google-genai` SDK (default model: `gemini-2.5-flash` with structured JSON output)
- [ ] Define `VisionProvider` ABC with `extract_coffee_profile()` method
- [ ] Define `StorageProvider` ABC with `upload()`, `get_url()`, `delete()` methods
- [ ] Implement `LocalStorageProvider` for dev environment
- [ ] Create `brewwise/dependencies.py` with dependency injection factory (reads `Settings` to instantiate providers)
- [ ] Write integration test: Gemini provider generates a simple structured response using Flash

#### 1.3 — Vision & Extraction Service (Token-Optimised)

| Item | Details |
|---|---|
| **Task** | Implement image upload, Gemini Flash Vision extraction with compact schema, and structured coffee profile output |
| **Files created** | `brewwise/services/vision/gemini_vision.py`, `brewwise/services/vision/extractor.py`, `brewwise/schemas/scan.py`, `brewwise/schemas/coffee_profile.py`, `brewwise/api/v1/scan.py` |
| **Acceptance** | `POST /api/v1/scan` extracts bag data using a compact schema (`v`, `c` short keys, ~600 output tokens vs ~1,500 baseline), inflates to `CoffeeProfileDraft` in code, and caches results by image SHA-256 hash. |

**Subtasks:**

- [ ] Define `ExtractedFieldCompact` Pydantic schema with short keys (`v`: value, `c`: confidence) to reduce output tokens by ~60%
- [ ] Define `ExtractedField` full Pydantic schema and post-processing mapper (`compact_to_full()`)
- [ ] Define `CoffeeProfileDraft` Pydantic schema (all fields from architecture §5.3)
- [ ] Write compressed Gemini Vision prompt (`prompts/v1/extract_coffee.j2`) — concise system instructions, schema enforcement, no bulky few-shot examples
- [ ] Implement `GeminiVisionProvider.extract_coffee_profile()` — sends image + prompt to `gemini-2.5-flash`, requests structured JSON output
- [ ] Implement image SHA-256 hash caching in Redis (TTL: 30 days) — skips vision call if identical image re-scanned
- [ ] Implement `Extractor` orchestrator — computes hash, checks cache, calls vision provider, inflates compact JSON, validates schema
- [ ] Implement `POST /api/v1/scan` endpoint — accepts `multipart/form-data`, validates file type (JPEG, PNG, WebP) and size (≤10 MB), calls extractor, returns `CoffeeProfileDraft`
- [ ] Handle edge case: non-coffee image → return error with descriptive message
- [ ] Handle edge case: blurry image → return partial extraction with low confidence
- [ ] Store uploaded image in object storage (with configurable retention)
- [ ] Write unit tests: compact schema parsing, field mapper, confidence scoring, cache hit/miss
- [ ] Write integration test: real coffee bag image → compact structured extraction (< 800 output tokens)

#### 1.4 — Coffee Identity Normalisation (Basic)

| Item | Details |
|---|---|
| **Task** | Normalise extracted fields into canonical forms |
| **Files created** | `brewwise/services/identity/normaliser.py`, `brewwise/services/identity/confidence.py` |
| **Acceptance** | "Natural Process" → "natural", "Light Roast" → "light", "Fully Washed" → "washed". Unicode and diacritics handled. |

**Subtasks:**

- [ ] Create process method normalisation map (natural, washed, honey, anaerobic, etc.)
- [ ] Create roast level normalisation map (light, medium_light, medium, dark, omni)
- [ ] Implement name normalisation: strip "Coffee Roasters", "Co.", normalise unicode
- [ ] Implement `normalise_profile()` — runs all normalisations on a `CoffeeProfileDraft`
- [ ] Write unit tests with 20+ normalisation cases

---

### 3.3 Week 2: Recipe Generation & Validation

#### 2.1 — Database Setup

| Item | Details |
|---|---|
| **Task** | Set up PostgreSQL schemas, ORM models, and migrations |
| **Files created** | `brewwise/models/coffee_profile.py`, `brewwise/models/recipe.py`, `brewwise/models/equipment.py`, `brewwise/db/session.py`, `brewwise/db/migrations/` |
| **Acceptance** | `alembic upgrade head` creates all tables. Async session factory works in tests. |

**Subtasks:**

- [ ] Create SQLAlchemy `Base` and async engine/session factory
- [ ] Define `CoffeeProfile` ORM model (all fields from architecture §12)
- [ ] Define `Recipe` ORM model (structured fields + JSONB for pour_schedule, instructions)
- [ ] Define `Equipment` ORM model (basic: grinder brand/model, dripper brand/model)
- [ ] Set up Alembic with async PostgreSQL driver (`asyncpg`)
- [ ] Create initial migration
- [ ] Write test: create and query a coffee profile

#### 2.2 — Recipe Synthesis & Explanation Service (Unified & Slim)

| Item | Details |
|---|---|
| **Task** | Implement single-call LLM recipe synthesis with integrated explanation, slim generation schema, and arithmetic validation |
| **Files created** | `brewwise/services/synthesis/recipe_generator.py`, `brewwise/services/synthesis/validator.py`, `brewwise/schemas/recipe.py`, `brewwise/prompts/v1/generate_recipe.j2` |
| **Acceptance** | In a single `gemini-2.5-flash` call, the system generates dynamic brew parameters AND inline reasoning/explanation (~2,000 output tokens total), while deterministic metadata (UUIDs, timestamps, equipment copying) is assembled in code. |

**Subtasks:**

- [ ] Define `PourStep` Pydantic schema (step_number, water_g, cumulative_water_g, timing, technique)
- [ ] Define `RecipeExplanation` Pydantic schema (reasoning_summary, parameter_rationale, assumptions)
- [ ] Define slim `RecipeGenerationOutput` Pydantic schema for LLM generation (only brew parameters + explanation; no deterministic fields)
- [ ] Define full `PersonalisedRecipe` schema with `@model_validator` for arithmetic checks (architecture §9.3)
- [ ] Write compressed recipe generation prompt (`prompts/v1/generate_recipe.j2`) — compact instructions, structured JSON mode, combines brew parameters + explanation in 1 call
- [ ] Implement `RecipeAssembler` — copies equipment from context, generates `recipe_id` UUID, sets `created_at`, attaches metadata in Python code
- [ ] Implement `RecipeGenerator.generate()` — single LLM call with prompt, checks 24h recipe cache (`coffee_id + equipment`), calls assembler, validates output
- [ ] Implement `RecipeValidator` — checks: `dose × ratio = water_total`, `Σ(pour_water) = water_total`, `bloom_water ≤ water_total`, temperature in range, pours chronologically ordered
- [ ] Implement retry logic: if validation fails, re-generate with error feedback (max 2 retries)
- [ ] Write unit tests: validator catches bad arithmetic, valid recipes pass, assembler correctly attaches deterministic fields
- [ ] Write integration test: coffee profile → generated recipe + explanation in single LLM call (< 2,200 output tokens)

#### 2.3 — Basic Equipment Module

| Item | Details |
|---|---|
| **Task** | Support dripper and grinder selection from a small seed catalogue |
| **Files created** | `brewwise/services/equipment/catalogue.py`, `brewwise/db/seed.py`, `brewwise/api/v1/equipment.py` |
| **Acceptance** | `GET /api/v1/equipment/grinders` and `GET /api/v1/equipment/drippers` return seeded catalogues. Equipment selection is optional — recipes generate with defaults if skipped. |

**Subtasks:**

- [ ] Seed 5 common grinders (Comandante C40, 1Zpresso JX, Baratza Encore, Fellow Ode, Timemore C2)
- [ ] Seed 5 common drippers (Hario V60, Kalita Wave, Origami, April, Fellow Stagg)
- [ ] Implement `GET /api/v1/equipment/grinders` — list with search/filter
- [ ] Implement `GET /api/v1/equipment/drippers` — list with search/filter
- [ ] Implement equipment-aware recipe generation: recipe prompt includes dripper flow characteristics and grinder type when selected
- [ ] Ensure recipe generates sensible defaults when equipment is not selected

#### 2.4 — Recipe Generation Endpoint

| Item | Details |
|---|---|
| **Task** | Create the API endpoint that ties extraction → normalisation → generation |
| **Files created** | `brewwise/api/v1/recipes.py` |
| **Acceptance** | `POST /api/v1/recipes/generate` with `profile_id` + optional equipment returns a validated `PersonalisedRecipe`. |

**Subtasks:**

- [ ] Implement `POST /api/v1/recipes/generate` — accepts profile_id + equipment, calls synthesis service
- [ ] Implement `GET /api/v1/recipes/{id}` — retrieve a saved recipe
- [ ] Implement CRUD for coffee profiles: `GET /api/v1/profiles/{id}`, `PUT /api/v1/profiles/{id}` (edit/correct)
- [ ] Save generated recipes to database
- [ ] Write API integration tests: full request → response validation

---

### 3.4 Week 3: Frontend MVP & Polish

#### 3.1 — Home & Image Capture Screen

| Item | Details |
|---|---|
| **Task** | Build the home screen with CTA and image capture/upload |
| **Files created** | `frontend/src/pages/Home.tsx`, `frontend/src/pages/Scan.tsx`, `frontend/src/components/ImageCapture.tsx` |
| **Acceptance** | User can access camera on mobile or drag-and-drop a file on desktop. Image preview shows immediately. |

**Subtasks:**

- [ ] Design and implement Home page with "Scan a Coffee Bag" hero CTA
- [ ] Implement `ImageCapture` component — camera viewfinder (MediaDevices API) + file drag-and-drop
- [ ] Client-side image compression (max 2048px, WebP conversion)
- [ ] EXIF stripping before upload
- [ ] Show image preview immediately while upload proceeds in background
- [ ] Set up React Router with routes: `/`, `/scan`, `/profile/:id`, `/recipe/:id`
- [ ] Set up Zustand stores: `scanStore`, `recipeStore`, `uiStore`
- [ ] Set up TanStack Query for server state management
- [ ] Implement API client module with base URL configuration

#### 3.2 — Coffee Profile Editor Screen

| Item | Details |
|---|---|
| **Task** | Display extracted profile with confidence badges and allow correction |
| **Files created** | `frontend/src/pages/CoffeeProfile.tsx`, `frontend/src/components/CoffeeProfileEditor.tsx` |
| **Acceptance** | Extracted fields show with ✅/⚠️/❓ confidence badges. User can edit any field. Corrections persist via `PUT /api/v1/profiles/{id}`. |

**Subtasks:**

- [ ] Implement `CoffeeProfileEditor` with per-field editing
- [ ] Show confidence badges: ✅ green (≥0.9), ⚠️ amber (0.6–0.89), ❓ red (<0.6), 🔲 grey (null/unknown)
- [ ] Tag each field as "read from bag" / "inferred" / "unknown"
- [ ] Allow user to correct any field before proceeding
- [ ] "Continue to Recipe" button → sends confirmed profile to recipe generation
- [ ] Optional equipment selection inline (collapsible section)

#### 3.3 — Recipe Display Screen

| Item | Details |
|---|---|
| **Task** | Display the generated recipe in a brew-friendly format |
| **Files created** | `frontend/src/pages/RecipeView.tsx`, `frontend/src/components/RecipeCard.tsx` |
| **Acceptance** | Recipe shows all parameters (dose, water, ratio, temperature, grind, pour schedule) with clear typography. Step-by-step instructions are readable during brewing on a mobile device. |

**Subtasks:**

- [ ] Display recipe header: dripper, dose, water, ratio, temperature, grind
- [ ] Display pour schedule as a visual timeline (step number, water amount, timing, technique)
- [ ] Display step-by-step instructions in a numbered, scrollable list
- [ ] Display expected flavour profile (labelled as prediction)
- [ ] Display troubleshooting tips (expandable section)
- [ ] Display source type badge: "AI Generated" (Phase 1 only shows this)
- [ ] Mobile-responsive layout optimised for use during brewing
- [ ] Metric units throughout (grams, °C, seconds)

#### 3.4 — Progress Indicators & Loading States

| Item | Details |
|---|---|
| **Task** | Implement SSE-based progress streaming from backend |
| **Files created** | `brewwise/api/v1/scan.py` (SSE endpoint), `frontend/src/hooks/useScanProgress.ts` |
| **Acceptance** | During the scan-to-recipe pipeline, the UI shows: "Uploading..." → "Reading your coffee bag..." → "Coffee identified!" → "Crafting your recipe..." → "Recipe ready!" |

**Subtasks:**

- [ ] Implement SSE endpoint on `/api/v1/scan/stream` that emits progress events
- [ ] Create `useScanProgress` hook that subscribes to SSE and updates UI state
- [ ] Design animated progress stepper component
- [ ] Handle error states gracefully (LLM timeout, extraction failure)

#### 3.5 — Phase 1 Testing & Validation

| Item | Details |
|---|---|
| **Task** | Comprehensive testing of the MVP pipeline |
| **Acceptance** | All unit tests pass. 3 coffee bag images produce valid recipes with correct arithmetic. Non-coffee images are rejected. |

**Subtasks:**

- [ ] Prepare 5 test coffee bag images (varied origins, layouts, quality)
- [ ] Run extraction on each → verify field accuracy manually
- [ ] Verify generated recipes have correct water totals for each
- [ ] Verify recipes with equipment vs. without equipment both work
- [ ] Verify non-coffee image produces appropriate error
- [ ] Run all backend unit tests (`pytest`)
- [ ] Run frontend component tests
- [ ] Manual E2E walkthrough on mobile browser

### 3.5 Phase 1 Exit Criteria

| Criterion | Metric |
|---|---|
| Extraction accuracy | ≥80% of visible fields correctly extracted on 5 test images |
| Recipe arithmetic | 100% of generated recipes pass arithmetic validation |
| Missing field handling | No hallucinated fields — unknowns are `null` |
| End-to-end time | Image upload to recipe display < 25 seconds |
| Mobile usability | Full flow completable on mobile viewport (375px) |
| Non-coffee rejection | Non-coffee images produce clear error, not a fake recipe |

---

## 4. Phase 2 — RAG-Based Recipe Discovery (Weeks 4–6)

### 4.1 Phase Goal

> The system searches a curated knowledge base of real recipes, presents source-attributed matches, distinguishes exact vs. related coffees, and uses retrieval evidence to ground its recommendations.

### 4.2 Week 4: Knowledge Base & Ingestion Pipeline

#### 4.1 — pgvector Setup & Recipe Source Schema

| Item | Details |
|---|---|
| **Task** | Enable vector search in PostgreSQL and create recipe source tables |
| **Files created** | `brewwise/models/recipe_source.py`, new Alembic migration, `brewwise/db/seed.py` (extended) |
| **Acceptance** | `recipe_sources` and `recipe_embeddings` tables exist. pgvector extension enabled. IVFFlat index created. |

**Subtasks:**

- [ ] Enable pgvector extension in PostgreSQL (`CREATE EXTENSION vector`)
- [ ] Define `RecipeSource` ORM model (url, title, author, raw_content, content_hash, retrieval_date, is_accessible, extraction_method, etc.)
- [ ] Define `RecipeEmbedding` ORM model (recipe_source_id FK, embedding vector(768), chunk_text, chunk_index, metadata JSONB)
- [ ] Create Alembic migration for new tables
- [ ] Create GIN indexes on `recipe_sources(raw_content)` for FTS
- [ ] Create IVFFlat index on `recipe_embeddings(embedding)` for ANN search
- [ ] Create B-tree index on `recipe_sources(content_hash)` for dedup

#### 4.2 — Embedding Provider

| Item | Details |
|---|---|
| **Task** | Implement the embedding provider using Gemini text-embedding-004 |
| **Files created** | `brewwise/providers/embeddings/gemini_embed.py` |
| **Acceptance** | `EmbeddingProvider.embed()` returns 768-dim vectors. Batch embedding works. |

**Subtasks:**

- [ ] Define `EmbeddingProvider` ABC with `embed(text) → list[float]` and `embed_batch(texts) → list[list[float]]`
- [ ] Implement `GeminiEmbeddingProvider` using text-embedding-004
- [ ] Write integration test: embed a recipe text, verify dimensions

#### 4.3 — Batch Ingestion Pipeline

| Item | Details |
|---|---|
| **Task** | Build the pipeline that ingests recipe data from curated sources |
| **Files created** | `brewwise/services/ingestion/pipeline.py`, `brewwise/services/ingestion/parser.py`, `brewwise/services/ingestion/deduplicator.py`, `brewwise/services/ingestion/indexer.py`, `brewwise/services/ingestion/scrapers/base.py` |
| **Acceptance** | Given a list of URLs, the pipeline fetches content, extracts recipe fields via LLM, deduplicates, generates embeddings, and stores in the knowledge base. |

**Subtasks:**

- [ ] Define `ScraperProvider` ABC with `fetch(url) → RawContent`
- [ ] Implement HTML → Markdown content extraction (strip nav, ads, scripts)
- [ ] Implement `RecipeParser` — sends cleaned content to LLM with extraction prompt, gets structured recipe fields
- [ ] Write extraction prompt (`prompts/v1/extract_source_recipe.j2`) — extract recipe parameters, coffee identity, equipment, source metadata
- [ ] Implement `Deduplicator` — SHA-256 content hash, check existing `content_hash` in DB
- [ ] Implement `Indexer` — chunk text (512 tokens, 64 overlap), generate embeddings, write to pgvector, update FTS index
- [ ] Implement `IngestionPipeline.ingest(urls)` — orchestrates fetch → parse → dedup → index
- [ ] Write unit tests: dedup catches duplicates, parser extracts fields correctly
- [ ] Write integration test: ingest 3 real recipe URLs, verify stored in DB with embeddings

#### 4.4 — Curated Recipe Dataset

| Item | Details |
|---|---|
| **Task** | Curate and ingest 50–100 real pour-over recipes |
| **Files created** | `data/curated_sources.json`, `scripts/ingest_curated.py` |
| **Acceptance** | 50+ real recipe sources ingested with full provenance. Covers varied origins, processes, roast levels, and drippers. |

**Subtasks:**

- [ ] Curate 50–100 URLs of publicly accessible pour-over recipe pages/blog posts
- [ ] Ensure coverage: V60, Kalita Wave, Origami recipes; washed, natural, honey coffees; light, medium roasts; India, Ethiopia, Colombia, Kenya, Guatemala origins
- [ ] Create `data/curated_sources.json` with URL list and metadata
- [ ] Run ingestion pipeline on curated list
- [ ] Verify 80%+ URLs successfully ingested with extracted recipe fields
- [ ] Manual spot-check: 10 random sources have accurate recipe extraction

---

### 4.3 Week 5: Hybrid Retrieval & Evidence Evaluation

#### 5.1 — Query Builder

| Item | Details |
|---|---|
| **Task** | Build retrieval queries from a confirmed coffee profile |
| **Files created** | `brewwise/services/retrieval/query_builder.py` |
| **Acceptance** | Given a coffee profile, the builder produces multiple query variants (exact, producer, characteristic, equipment). |

**Subtasks:**

- [ ] Implement `QueryBuilder.build_queries(profile, equipment)` → returns a list of query strings
- [ ] Exact query: `"{brand} {estate} {product_name}"`
- [ ] Producer query: `"{estate} {origin} {process}"`
- [ ] Characteristic query: `"{process} {roast} {varietal} {origin} pour-over"`
- [ ] Equipment query: `"{dripper} recipe"` (when specified)
- [ ] Write unit tests: verify query construction for various profile completeness levels

#### 5.2 — Hybrid Retrieval (FTS + Vector)

| Item | Details |
|---|---|
| **Task** | Implement parallel full-text and vector search with RRF merging |
| **Files created** | `brewwise/services/retrieval/hybrid_retriever.py` |
| **Acceptance** | Retrieval returns ranked candidate recipes from both FTS and vector search, merged via Reciprocal Rank Fusion. |

**Subtasks:**

- [ ] Implement FTS search using PostgreSQL `ts_query` on `recipe_sources.raw_content`
- [ ] Implement vector search using pgvector `cosine_distance` on `recipe_embeddings.embedding`
- [ ] Implement RRF (Reciprocal Rank Fusion) to merge and deduplicate results from both sources
- [ ] Return top-K candidates (default K=20) with scores
- [ ] Write integration test: query against curated KB, verify relevant results surface

#### 5.3 — Reranking & Match Classification

| Item | Details |
|---|---|
| **Task** | Rerank candidates and classify match type (exact/strong/related/analogous/general) |
| **Files created** | `brewwise/services/retrieval/reranker.py`, `brewwise/services/retrieval/relevance.py` |
| **Acceptance** | Candidates are reranked by relevance. Each result has a match classification. Non-recipe and non-pour-over results are filtered out. |

**Subtasks:**

- [ ] Implement LLM-based reranker — scores each candidate on: coffee identity match, recipe completeness, brewing method match, equipment compatibility
- [ ] Implement `MatchClassifier` — classifies each result as EXACT / STRONG / RELATED / ANALOGOUS / GENERAL using configurable thresholds (0.92 / 0.85 / 0.70 / 0.55)
- [ ] Filter out results below analogous threshold
- [ ] Filter out non-recipe documents (pages with no brewing recipe)
- [ ] Filter out non-pour-over methods (espresso, French press, etc.)
- [ ] Write unit tests: classification thresholds, filtering logic

#### 5.4 — Evidence Evaluation (Deterministic in Code)

| Item | Details |
|---|---|
| **Task** | Assess retrieved evidence quality and assemble an EvidencePackage deterministically in code |
| **Files created** | `brewwise/services/retrieval/evidence_evaluator.py` |
| **Acceptance** | The evaluator produces an `EvidencePackage` in code with match_outcome (A/B/C), ranked recipes, detected parameter conflicts, and coverage summary without consuming LLM tokens. |

**Subtasks:**

- [ ] Define `EvidencePackage` schema (matched_recipes, match_outcome, conflicts, coverage_summary)
- [ ] Define `RankedRecipe` schema (recipe data + source reference + match type + relevance score)
- [ ] Define `ParameterConflict` schema (field, values, sources — for when recipes disagree)
- [ ] Implement code-level evidence evaluation: verify each retained result contains a valid recipe, is pour-over, and has an identifiable source
- [ ] Classify outcome deterministically in Python: A (≥1 EXACT/STRONG), B (≥1 RELATED/ANALOGOUS), C (nothing above threshold)
- [ ] Detect parameter conflicts programmatically (e.g., two recipes disagree on temperature by >5°C or ratio by >1.0)
- [ ] Assemble compact evidence context string to inject into the unified synthesis prompt (no separate evaluation LLM call)
- [ ] Write unit tests: deterministic outcome classification, conflict detection, compact context serialization

---

### 4.4 Week 6: Evidence-Grounded Synthesis & Frontend (Single Unified Call)

#### 6.1 — Unified Grounded Recipe Synthesis & Provenance

| Item | Details |
|---|---|
| **Task** | Update recipe generation to use retrieval evidence in a single unified LLM call (Outcome A/B/C routing + embedded provenance) |
| **Files updated** | `brewwise/services/synthesis/recipe_generator.py`, `brewwise/prompts/v1/generate_grounded_recipe.j2` |
| **Acceptance** | A single `gemini-2.5-flash` call receives the coffee profile and evidence package, evaluates inline, generates the adapted recipe, and produces the complete explanation/provenance (~2,000 output tokens, 1 call vs 3 previously). |

**Subtasks:**

- [ ] Write unified grounded synthesis prompt (`prompts/v1/generate_grounded_recipe.j2`):
  - Outcome A path: present strongest source recipe, adapt to user's equipment
  - Outcome B path: synthesize optimal parameters using related recipes as reference
  - Outcome C path: generate grounded recipe from core brewing principles
  - Embedded explanation: trace every parameter directly to bag text, retrieved source, or brewing physics
- [ ] Implement single-call grounded generation in `RecipeGenerator.generate_grounded()`:
  - Consolidates evaluation + generation + explanation into 1 LLM request
  - Sets `source_type`: "exact_match", "adapted_from_related", "ai_generated"
  - Attaches verified `source_recipes` in code from the evidence package
- [ ] Strictly validate citations in Python: ensure any referenced URL exists in `recipe_sources` DB; reject hallucinated URLs
- [ ] Write unit tests: prompt rendering with/without evidence, citation validator
- [ ] Write integration test: retrieval results → single unified LLM call → recipe with verified provenance (< 2,200 output tokens)

#### 6.2 — Provenance & Explainability Verification (Code Layer)

| Item | Details |
|---|---|
| **Task** | Verify and format recipe explanations tracing every parameter to its source |
| **Files created/updated** | `brewwise/services/synthesis/provenance_verifier.py` |
| **Acceptance** | Every recipe includes verified provenance distinguishing: extracted from bag, adapted from source, or AI calculated. Zero fabricated citations allowed. |

**Subtasks:**

- [ ] Define `RecipeExplanation` schema (reasoning_summary, parameter_rationale, source_attributions, assumptions)
- [ ] Implement `ProvenanceVerifier`: cross-checks LLM source attributions against retrieved database URLs
- [ ] Ensure: if LLM attempts to cite an ungrounded or fabricated source, flag and replace with clear "Calculated from coffee principles" attribution
- [ ] Write unit tests: provenance verification against real vs fabricated source URLs

#### 6.3 — Recipe Search Endpoint

| Item | Details |
|---|---|
| **Task** | Create the search endpoint that runs the full RAG pipeline |
| **Files created** | `brewwise/api/v1/recipes.py` (extended) |
| **Acceptance** | `POST /api/v1/recipes/search` returns matched recipes with source attributions and match type labels. |

**Subtasks:**

- [ ] Implement `POST /api/v1/recipes/search` — accepts profile_id, runs query builder → hybrid retrieval → reranking → evidence evaluation → returns EvidencePackage
- [ ] Update `POST /api/v1/recipes/generate` to first run search, then synthesise based on evidence
- [ ] Return evidence alongside recipe in response

#### 6.4 — Evidence Panel UI

| Item | Details |
|---|---|
| **Task** | Show retrieval evidence, sources, and match types in the recipe view |
| **Files created** | `frontend/src/components/EvidencePanel.tsx`, `frontend/src/components/MatchTypeBadge.tsx` |
| **Acceptance** | Recipe view shows collapsible evidence panel with source links, match type badges (exact/related/analogous/generated), and match explanations. |

**Subtasks:**

- [ ] Implement `EvidencePanel` — collapsible section showing retrieval results
- [ ] Implement `MatchTypeBadge` — colour-coded badges for each match type
- [ ] Display source recipe cards with: title, author, URL, match type, key parameters
- [ ] Highlight similarities and conflicts between retrieved recipes
- [ ] Update recipe source badge: "Based on {source}" / "Inspired by related coffee" / "AI Generated"
- [ ] Display provenance explanation text
- [ ] Link to original source URLs (open in new tab)

#### 6.5 — Phase 2 Testing

**Subtasks:**

- [ ] Test retrieval precision: query 5 known coffees, verify correct sources surface
- [ ] Test match classification: verify exact matches are not labelled as related
- [ ] Test Outcome A: known coffee → source recipe presented with attribution
- [ ] Test Outcome B: related coffee → recommendation references source but is labelled appropriately
- [ ] Test Outcome C: unknown coffee → fallback generated, no fabricated sources
- [ ] Test provenance: verify every cited URL is a real, accessible page
- [ ] Retrieval quality metrics: Precision@5 ≥ 0.6 on test queries

### 4.5 Phase 2 Exit Criteria

| Criterion | Metric |
|---|---|
| Knowledge base size | ≥50 real recipe sources ingested with embeddings |
| Retrieval precision | Precision@5 ≥ 0.6 on test coffee profiles |
| Match classification | Exact matches never misclassified as related |
| Source attribution | 100% of cited sources have valid, accessible URLs |
| Outcome routing | A/B/C paths tested and working correctly |
| No fabricated sources | Zero fictional URLs or author attributions |
| Evidence panel | UI displays sources, match types, and explanations |

---

## 5. Phase 3 — Inline Live Web Discovery (Weeks 7–9)

### 5.1 Phase Goal

> Given a never-before-seen coffee, the system searches the web inline during the scan, fetches full pages, extracts real recipes, and uses them in its recommendation — all within a single scan request.

### 5.2 Week 7: Search Provider & Page Fetcher

#### 7.1 — SearchProvider Integration

| Item | Details |
|---|---|
| **Task** | Implement the search provider abstraction and Google/Tavily integrations |
| **Files created** | `brewwise/providers/search/base.py`, `brewwise/providers/search/google_search.py`, `brewwise/providers/search/tavily.py` |
| **Acceptance** | `SearchProvider.search(query)` returns a list of URLs with titles and snippets. Rate limiting enforced. |

**Subtasks:**

- [ ] Define `SearchProvider` ABC with `search(query, max_results) → list[SearchResult]`
- [ ] Define `SearchResult` schema (url, title, snippet, position)
- [ ] Implement `GoogleSearchProvider` using Google Custom Search API
- [ ] Implement `TavilySearchProvider` using Tavily Search API
- [ ] Implement per-provider rate limiting (`LIVE_DISCOVERY_RATE_LIMIT`)
- [ ] Configure via environment variables (`SEARCH_PROVIDER`, `SEARCH_API_KEY`)
- [ ] Write integration test: search for a known coffee, verify URLs returned

#### 7.2 — Access Checker & Page Fetcher

| Item | Details |
|---|---|
| **Task** | Fetch full page content with robots.txt compliance, timeouts, and access control |
| **Files created** | `brewwise/services/discovery/access_checker.py`, `brewwise/services/discovery/page_fetcher.py` |
| **Acceptance** | Pages are fetched respecting robots.txt, auth walls are detected and skipped, timeouts are enforced. |

**Subtasks:**

- [ ] Implement `AccessChecker` — fetches and parses robots.txt, checks if URL is allowed for our user-agent
- [ ] Implement auth-wall detection — check for login forms, 401/403 responses, paywall markers
- [ ] Implement `PageFetcher` — HTTP GET with configurable timeout (`LIVE_DISCOVERY_TIMEOUT_SECONDS`), follows redirects, validates content-type (HTML/text only)
- [ ] Strip HTML → clean Markdown (remove nav, ads, scripts, footers)
- [ ] Implement per-domain rate limiting (max 2 concurrent fetches per domain)
- [ ] Sanitise fetched content for LLM prompt safety (strip potential injection patterns)
- [ ] Write unit tests: robots.txt parsing, auth-wall detection, timeout handling

#### 7.3 — Live Recipe Extractor (Batched)

| Item | Details |
|---|---|
| **Task** | Extract structured recipe data from fetched pages via a single batched LLM call |
| **Files created** | `brewwise/services/discovery/recipe_extractor.py`, `brewwise/prompts/v1/extract_web_recipes_batch.j2` |
| **Acceptance** | Batches all cleaned page contents into a single `gemini-2.5-flash` call (~800 output tokens for up to 5 pages, vs ~1,500 across 5 individual calls). Search snippets are never treated as recipe content. |

**Subtasks:**

- [ ] Write batched web recipe extraction prompt (`prompts/v1/extract_web_recipes_batch.j2`) — accepts pages separated by delimiter (`---PAGE_BREAK---`), extracts list of recipes with source URLs
- [ ] Implement `LiveRecipeExtractor.extract_batch(cleaned_pages)`:
  - Checks 30-day Redis cache for each URL hash (`url_hash → extracted_recipe`)
  - Batches uncached pages into a single Gemini Flash request
  - Returns parsed `list[DiscoveredRecipe]` with per-URL extraction status
- [ ] Reject pages with no brewing recipe
- [ ] Reject pages where brewing method ≠ pour-over
- [ ] Preserve source attribution: title, author, URL, publication date
- [ ] **Critical: Never use search snippets as recipe data** — only fully fetched page content
- [ ] Write unit tests: batch parsing, cache hit/miss on URLs, filtering non-recipes

---

### 5.3 Week 8: Discovery Orchestrator & Pipeline Integration

#### 8.1 — Discovery Orchestrator (With Skip Rule)

| Item | Details |
|---|---|
| **Task** | Coordinate search → filter → fetch → batched extract → index → merge workflow with intelligent skip |
| **Files created** | `brewwise/services/discovery/orchestrator.py`, `brewwise/services/discovery/result_merger.py` |
| **Acceptance** | Given a confirmed profile, checks if KB already has ≥3 high-quality recipes; if so, skips live discovery entirely (saving ~1,500 tokens). Otherwise executes within time budget. |

**Subtasks:**

- [ ] Implement KB sufficiency check: if `kb_recipe_count >= 3` and `avg_confidence >= 0.8`, skip live discovery and return `LiveDiscoveryResult(status="skipped_sufficient_kb")`
- [ ] Implement `DiscoveryOrchestrator.discover(profile, timeout_budget)`:
  1. Check KB sufficiency skip rule
  2. Build search query from profile metadata
  3. Call SearchProvider (with Redis query cache check)
  4. Filter URLs (skip already-indexed, check robots.txt, skip auth-walled)
  5. Fetch pages in parallel (with per-URL timeout)
  6. Batch extract recipes via `LiveRecipeExtractor.extract_batch()`
  7. Dedup against existing KB
  8. Generate embeddings for new content
  9. Optionally persist in KB (`LIVE_DISCOVERY_PERSIST`)
  10. Return `LiveDiscoveryResult`
- [ ] Define `LiveDiscoveryResult` schema (discovered_recipes, search_status, urls_attempted, urls_yielded_recipes, errors)
- [ ] Implement `search_status` logic:
  - `"skipped_sufficient_kb"` — sufficient local KB evidence exists, discovery skipped to conserve tokens
  - `"success"` — search completed (recipes may or may not be found)
  - `"partial"` — search ran but timed out before processing all URLs
  - `"failed"` — search API error or network failure
  - `"disabled"` — no SearchProvider configured
- [ ] Implement fallback query: if first query returns no results, try broader query
- [ ] Implement timeout enforcement: `LIVE_DISCOVERY_TOTAL_TIMEOUT` (default 15s) — use partial results if exceeded
- [ ] Log timed-out URLs for later batch ingestion
- [ ] Implement `ResultMerger.merge(live_results, local_results)` — combines live discovery results into the retrieval candidate set

#### 8.2 — Outcome Distinction (No Results vs. Failure)

| Item | Details |
|---|---|
| **Task** | Ensure the system clearly distinguishes "no results found" from "search failed" |
| **Files updated** | `brewwise/services/discovery/orchestrator.py`, response schemas |
| **Acceptance** | User-facing messages match the architecture specification for all four outcomes (success+recipes, success+no results, failed, disabled). |

**Subtasks:**

- [ ] Implement user-facing messages for each search status:
  - `"skipped_sufficient_kb"`: "Found expert recipes in the BrewWise Knowledge Base"
  - `"success"` + recipes: "Found {N} recipe(s) from online sources"
  - `"success"` + no recipes: "No matching recipes were found in online sources for this coffee. This does not mean none exist — it means none were found in this search."
  - `"failed"`: "Online recipe search was unavailable. Results are based on the existing knowledge base only."
  - `"disabled"`: "Online search is not configured. Results are from the local knowledge base."
- [ ] A lack of results is **never** presented as proof that no recipe exists online
- [ ] Write unit tests: verify all message paths

#### 8.3 — Pipeline Integration

| Item | Details |
|---|---|
| **Task** | Wire live discovery into the scan-to-recipe pipeline as step 4 (between profile confirmation and RAG retrieval) |
| **Files updated** | `brewwise/api/v1/recipes.py`, `brewwise/services/retrieval/hybrid_retriever.py` |
| **Acceptance** | `POST /api/v1/recipes/generate` now runs live discovery in parallel with local retrieval, merges results, and uses the combined evidence for synthesis. |

**Subtasks:**

- [ ] Update recipe generation endpoint to run live discovery + local retrieval in parallel (`asyncio.gather`)
- [ ] Merge live discovery results into local retrieval candidate set before reranking
- [ ] Update SSE progress: add "🌐 Searching the web for recipes..." step
- [ ] Update evidence response to include `search_status` and `discovery_summary`
- [ ] Ensure graceful degradation: if discovery fails, local KB results are still used
- [ ] Ensure: if `LIVE_DISCOVERY_ENABLED=false`, discovery is skipped entirely

#### 8.4 — Search & Recipe Result Caching

| Item | Details |
|---|---|
| **Task** | Cache search results and extracted web recipes in Redis to avoid redundant API calls and token spend |
| **Files updated** | `brewwise/services/discovery/orchestrator.py` |
| **Acceptance** | Identical search queries within 1 hour hit the Redis cache. Extracted recipes from previously fetched URLs are served from Redis (TTL: 30 days) with 0 LLM calls. |

**Subtasks:**

- [ ] Cache search API results in Redis keyed by query hash (TTL: 1 hour)
- [ ] Cache extracted web recipes in Redis keyed by URL SHA-256 (TTL: 30 days)
- [ ] Cache URL fetch results in KB (persisted URLs skip re-fetch)
- [ ] Implement cache invalidation: configurable TTL, manual flush endpoint (admin)
- [ ] Write integration test: duplicate query → second hits Redis search cache; repeat URL → zero LLM extraction calls

---

### 5.4 Week 9: Frontend Integration, Safety & Testing

#### 9.1 — Frontend: Discovery Status in Evidence Panel

| Item | Details |
|---|---|
| **Task** | Show live discovery status, discovered sources, and outcome distinction in the UI |
| **Files updated** | `frontend/src/components/EvidencePanel.tsx`, `frontend/src/pages/RecipeView.tsx` |
| **Acceptance** | UI shows discovery status (searching/found/not found/failed/disabled). Discovered sources show with "discovered online" badge. |

**Subtasks:**

- [ ] Display live discovery status indicator during scan
- [ ] Show discovery outcome message (matching the 4 defined messages)
- [ ] Tag discovered recipes with "🌐 Discovered online" badge vs. "📚 From knowledge base" badge
- [ ] Display number of URLs searched, pages yielded recipes
- [ ] Show error details (if any) in expandable section

#### 9.2 — Safety & Trust Controls

| Item | Details |
|---|---|
| **Task** | Implement all safety controls from architecture §8.4.3 |
| **Acceptance** | Content is sanitised, snippets are never used as recipes, robots.txt is enforced, no fictional URLs are generated. |

**Subtasks:**

- [ ] Verify: fetched page content is wrapped in data delimiters in LLM prompts
- [ ] Verify: system prompt instructs model to treat retrieved content as data, not instructions
- [ ] Verify: snippet content is used only for URL prioritisation, never for recipe extraction
- [ ] Verify: only actually fetched and validated URLs appear in source citations
- [ ] Verify: auth-walled and blocked URLs are skipped and logged
- [ ] Penetration test: include prompt injection patterns in test pages, verify they don't affect extraction

#### 9.3 — Phase 3 Testing & Acceptance Test

| Item | Details |
|---|---|
| **Task** | Comprehensive testing including the key acceptance criterion |
| **Acceptance** | Given a newly scanned coffee that has not been pre-indexed, the application attempts live web search, processes accessible results, and uses any relevant discovered recipes in its recommendation. |

**Subtasks:**

- [ ] **Acceptance test:** Scan a real coffee bag for a coffee NOT in the knowledge base → verify system searches the web, fetches pages, and either uses discovered recipes or explicitly reports no results
- [ ] Test: search provider unavailable → system reports limitation, uses local KB, generates fallback
- [ ] Test: all discovered pages have no recipe → "no matching recipes found" message (not "search failed")
- [ ] Test: discovered page has auth wall → skipped, other pages still processed
- [ ] Test: robots.txt blocks access → URL skipped, logged
- [ ] Test: timeout exceeded → partial results used, status is "partial"
- [ ] Test: page contains prompt injection → extraction ignores injected instructions
- [ ] Performance test: full pipeline with live discovery < 30 seconds

### 5.5 Phase 3 Exit Criteria

| Criterion | Metric |
|---|---|
| Live discovery works | Unindexed coffee triggers web search inline |
| Snippet safety | Recipes extracted only from full page content |
| Outcome distinction | "No results" and "search failed" produce different messages |
| Robots.txt compliance | Blocked URLs are skipped, not fetched |
| Timeout handling | Pipeline completes even if some URLs time out |
| Acceptance test passes | Acceptance criterion from problem statement verified |
| No fabricated URLs | Zero fictional source citations |
| Performance | Full pipeline with discovery < 30 seconds |

---

## 6. Phase 4 — Personalisation & Iterative Brewing (Weeks 10–12)

### 6.1 Phase Goal

> Users can create accounts, save equipment profiles, log brews, record feedback, and receive targeted adjustments — creating a complete iterative brewing experience.

### 6.2 Week 10: Authentication & Equipment Profiles

#### 10.1 — User Authentication

| Item | Details |
|---|---|
| **Task** | Implement JWT-based authentication with optional anonymous access |
| **Files created** | `brewwise/models/user.py`, `brewwise/api/v1/auth.py`, `brewwise/services/auth/` |
| **Acceptance** | Users can register and login. Authenticated endpoints require JWT. Scan and recipe generation work for anonymous users. |

**Subtasks:**

- [ ] Define `User` ORM model (id, email, display_name, password_hash, created_at)
- [ ] Implement `POST /api/v1/auth/register` — email + password → JWT
- [ ] Implement `POST /api/v1/auth/login` — email + password → JWT
- [ ] Implement JWT middleware — validate token, inject user into request context
- [ ] Make authentication optional for scan/recipe endpoints (anonymous users get temporary sessions)
- [ ] Make authentication required for: equipment profiles, brew history, feedback
- [ ] Implement password hashing with bcrypt
- [ ] Write tests: registration, login, token validation, auth-required endpoints

#### 10.2 — Equipment Profiles (Full)

| Item | Details |
|---|---|
| **Task** | Allow users to save, manage, and reuse equipment profiles |
| **Files created** | `brewwise/models/equipment_profile.py`, `brewwise/api/v1/equipment.py` (extended) |
| **Acceptance** | Users can create named equipment profiles (e.g., "My Home Setup"), set a default, and select profiles when generating recipes. |

**Subtasks:**

- [ ] Define `UserEquipmentProfile` ORM model (architecture §10.3)
- [ ] Implement `POST /api/v1/equipment/profiles` — create profile
- [ ] Implement `GET /api/v1/equipment/profiles` — list user's profiles
- [ ] Implement `PUT /api/v1/equipment/profiles/{id}` — update profile
- [ ] Implement `DELETE /api/v1/equipment/profiles/{id}` — delete profile
- [ ] Implement default profile selection (one profile flagged as `is_default`)
- [ ] Support free-text grinder/dripper (for models not in catalogue)
- [ ] Include experience_level, preferred_dose, preferred_ratio in profile
- [ ] Frontend: equipment profile management in Settings page
- [ ] Frontend: quick profile selector in recipe generation flow

#### 10.3 — Expanded Equipment Catalogue

| Item | Details |
|---|---|
| **Task** | Expand grinder and dripper catalogues to 20+ models with grind size mapping |
| **Files updated** | `brewwise/db/seed.py`, `brewwise/services/equipment/grinder_guide.py`, `brewwise/services/equipment/dripper_guide.py` |
| **Acceptance** | Catalogue has 20+ grinders and 10+ drippers. Grind size mapping works for supported grinders. Unsupported grinders get relative descriptions. |

**Subtasks:**

- [ ] Expand grinder catalogue to 20+ models with burr type, grind range, pour-over range, reference settings
- [ ] Expand dripper catalogue to 10+ models with flow characteristics and technique notes
- [ ] Implement grind size mapping: relative description → grinder-specific setting (architecture §10.2)
  - E.g., "Medium-fine" → Comandante C40: 22 clicks / 1Zpresso JX: 2.4.0 / Baratza Encore: 12
- [ ] Implement dripper-specific technique notes in recipe generation
- [ ] Fallback for unknown grinders: relative description + adjustment guidance
- [ ] Write unit tests: grind mapping for each supported grinder

---

### 6.3 Week 11: Brew History & Feedback Loop

#### 11.1 — Brew Logging

| Item | Details |
|---|---|
| **Task** | Allow users to log brew attempts with actual parameters used |
| **Files created** | `brewwise/models/brew_log.py`, `brewwise/api/v1/brews.py`, `brewwise/schemas/brew.py` |
| **Acceptance** | Users can log a brew against a recipe, recording actual dose, water, grind setting, brew time, and sensory feedback. |

**Subtasks:**

- [ ] Define `BrewLog` ORM model (architecture §11.1 — all fields)
- [ ] Implement `POST /api/v1/brews` — log a brew attempt
- [ ] Implement `GET /api/v1/brews` — list brew history (paginated, filterable by coffee)
- [ ] Implement `GET /api/v1/brews/{id}` — get a specific brew log
- [ ] Frontend: post-brew feedback form with:
  - Actual parameters used (dose, water, grind setting, temp, brew time)
  - Sensory feedback sliders (sourness 1–5, bitterness 1–5, body 1–5, sweetness 1–5, overall 1–5)
  - Drawdown speed (fast / normal / slow / stalled)
  - Free-text flavour notes
  - Overall satisfaction rating

#### 11.2 — Feedback → Adjustment Engine

| Item | Details |
|---|---|
| **Task** | Analyse brew feedback and suggest targeted adjustments |
| **Files created** | `brewwise/services/feedback/analyser.py`, `brewwise/prompts/v1/feedback_adjust.j2` |
| **Acceptance** | Given brew feedback, the system suggests 1–2 variable changes (architecture §11.2 diagnosis logic). |

**Subtasks:**

- [ ] Implement `FeedbackAnalyser.analyse(brew_log)` → `AdjustmentRecommendation`
- [ ] Implement diagnosis logic (architecture §11.2):
  - High sourness + low bitterness → under-extracted → finer grind / higher temp
  - High bitterness + low sourness → over-extracted → coarser grind / lower temp
  - Both sour + bitter → channelling → more even pours, check grind distribution
  - Stalled drawdown → coarser grind, less agitation, different filter
  - Weak/watery → higher ratio, finer grind, or higher dose
- [ ] Rule: suggest changing only 1–2 variables at a time
- [ ] Write adjustment prompt (`prompts/v1/feedback_adjust.j2`) for more nuanced recommendations
- [ ] Implement `POST /api/v1/brews/{id}/feedback` — submit feedback, get adjustments
- [ ] Implement `GET /api/v1/brews/{id}/adjustments` — retrieve saved adjustments
- [ ] Store adjustments in brew_log record
- [ ] Write unit tests: each diagnosis path produces correct adjustment direction

#### 11.3 — Brew History & Comparison UI

| Item | Details |
|---|---|
| **Task** | Display brew history with comparison between attempts |
| **Files created** | `frontend/src/pages/BrewHistory.tsx`, `frontend/src/components/RecipeComparison.tsx`, `frontend/src/components/FeedbackForm.tsx` |
| **Acceptance** | Users can view all past brews, compare two brew attempts side-by-side, and see how adjustments improved their coffee. |

**Subtasks:**

- [ ] Implement Brew History page — list of past brews with key metrics (date, coffee, satisfaction)
- [ ] Implement `RecipeComparison` component — side-by-side diff view of two brew attempts
  - Highlight what changed between attempts (grind, temp, etc.)
  - Show satisfaction trend
- [ ] Implement `FeedbackForm` component — structured sliders + free text
- [ ] Display adjustment recommendations after feedback submission
- [ ] Link from brew history to original recipe and coffee profile

---

### 6.4 Week 12: Brew Timer, PWA & Final Polish

#### 12.1 — Brew Timer

| Item | Details |
|---|---|
| **Task** | Build a step-by-step pour timer for use during brewing |
| **Files created** | `frontend/src/pages/BrewTimer.tsx`, `frontend/src/components/BrewTimerStepper.tsx` |
| **Acceptance** | Timer walks through each pour step with countdown, water quantity, and technique. Haptic feedback on mobile. |

**Subtasks:**

- [ ] Implement `BrewTimerStepper` — countdown timer per pour stage
- [ ] Display current step: water amount, pouring technique, target time
- [ ] Display upcoming steps in queue
- [ ] Display cumulative water poured vs. total
- [ ] Vibration alert at step transitions (Vibration API)
- [ ] Audio alert option (configurable)
- [ ] Swipe-to-advance to next step
- [ ] Start/pause/reset controls
- [ ] Keep screen awake during brew (Wake Lock API)
- [ ] Post-brew: prompt for feedback form

#### 12.2 — PWA & Offline Support

| Item | Details |
|---|---|
| **Task** | Enable PWA installation and offline recipe viewing |
| **Files created** | `frontend/public/manifest.json`, `frontend/src/sw.ts` |
| **Acceptance** | App is installable on mobile. Saved recipes are viewable offline. Static assets cached for instant load. |

**Subtasks:**

- [ ] Create PWA manifest with app name, icons, theme colours
- [ ] Implement service worker: cache static assets (1 year, hashed filenames)
- [ ] Cache saved recipes in IndexedDB/localStorage for offline viewing
- [ ] Implement offline indicator in UI
- [ ] Test: airplane mode → saved recipes and brew timer still work

#### 12.3 — Settings & User Preferences

| Item | Details |
|---|---|
| **Task** | Build settings page with user preferences, equipment management, and data controls |
| **Files created** | `frontend/src/pages/Settings.tsx` |
| **Acceptance** | Users can manage equipment profiles, set defaults, toggle dark mode, and export/delete their data. |

**Subtasks:**

- [ ] Equipment profile management (CRUD)
- [ ] Default equipment profile selection
- [ ] Theme toggle (light/dark)
- [ ] Data export (download all user data as JSON)
- [ ] Account deletion (GDPR-aligned)
- [ ] Notification preferences (brew timer alerts)

#### 12.4 — Comprehensive E2E Testing

| Item | Details |
|---|---|
| **Task** | Full end-to-end test suite covering all critical paths |
| **Files created** | `tests/e2e/` (Playwright) |
| **Acceptance** | 5–10 Playwright tests cover the complete user journey from scan to brew feedback. |

**Subtasks:**

- [ ] E2E test: Image upload → profile → recipe (no RAG) → success
- [ ] E2E test: Image upload → profile → recipe with RAG evidence → source attribution shown
- [ ] E2E test: Image upload → profile → live discovery → discovered recipe used
- [ ] E2E test: Equipment profile creation → used in recipe generation
- [ ] E2E test: Brew logging → feedback → adjustment recommendation
- [ ] E2E test: Non-coffee image → error message
- [ ] E2E test: Offline recipe viewing
- [ ] Performance test: full scan-to-recipe pipeline < 30 seconds
- [ ] Mobile viewport test: complete flow on 375px width

#### 12.5 — Documentation & README

| Item | Details |
|---|---|
| **Task** | Complete project documentation |
| **Files created** | `README.md`, `docs/evaluation.md`, `docs/api-reference.md` |
| **Acceptance** | README contains setup instructions, env vars, running locally, running tests, deployment. |

**Subtasks:**

- [ ] Write README.md: project overview, setup, env vars, running with Docker Compose, running tests
- [ ] Document API reference (or link to auto-generated OpenAPI docs)
- [ ] Document evaluation procedure and dataset
- [ ] Document model configuration and provider swapping
- [ ] Document data ingestion CLI commands
- [ ] Create example E2E demonstrations: exact match, related match, fallback generation

### 6.5 Phase 4 Exit Criteria

| Criterion | Metric |
|---|---|
| Authentication | Registration, login, JWT validation working |
| Equipment profiles | Create, save, set default, use in generation |
| Grind mapping | ≥20 grinders with pour-over range mappings |
| Brew logging | Log a brew with all parameters and feedback |
| Feedback adjustments | Each diagnosis path suggests correct adjustment |
| Brew comparison | Side-by-side view of two attempts |
| Brew timer | Step-by-step timer with haptic feedback |
| PWA | Installable, offline recipe viewing works |
| E2E tests | All Playwright tests pass |
| Documentation | README complete with setup instructions |

---

## 7. Cross-Phase: Testing & Quality Gates

### 7.1 Continuous Testing Requirements

| Test Type | Tool | When | Gate |
|---|---|---|---|
| **Static analysis** | mypy (backend), eslint + TypeScript (frontend) | Every commit | CI blocks merge on failure |
| **Linting** | ruff (backend), prettier (frontend) | Every commit | CI blocks merge on failure |
| **Unit tests** | pytest | Every commit | CI blocks merge on failure |
| **Integration tests** | pytest + Docker Compose | Every PR | CI blocks merge on failure |
| **E2E tests** | Playwright | Every PR (from Phase 4) | CI blocks merge on failure |
| **Recipe validation** | Custom validator | Every recipe generation | Generation retries on failure |
| **Token budget gate** | Custom test assertion (`test_token_budget.py`) | Every PR | CI verifies core scan ≤ 2 calls & ≤ 2,800 out tokens |

### 7.2 Evaluation Dataset

Build progressively across phases:

| Phase | Dataset Size | Content |
|---|---|---|
| Phase 1 | 5 images | Basic extraction accuracy testing |
| Phase 2 | 15 images | + retrieval testing (exact match, related, no match) |
| Phase 3 | 20 images | + live discovery testing (unindexed coffees) |
| Phase 4 | 25–30 images | Full evaluation dataset with ground-truth annotations |

**Dataset dimensions:**

| Dimension | Coverage |
|---|---|
| Origins | India, Ethiopia, Kenya, Colombia, Guatemala, Brazil, Indonesia |
| Processes | Washed, natural, honey, anaerobic |
| Roast levels | Light, medium-light, medium, dark |
| Image quality | Sharp, slightly blurry, angled, partial, low-light |
| Layouts | Minimal text, dense text, multi-language, artistic |
| Recipe availability | Exact match, related only, no match |

### 7.3 Quality Metrics Tracked Per Phase

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| Extraction accuracy (visible fields) | ≥80% | ≥80% | ≥80% | ≥85% |
| Recipe arithmetic validity | 100% | 100% | 100% | 100% |
| Retrieval Precision@5 | — | ≥0.6 | ≥0.6 | ≥0.7 |
| Source attribution accuracy | — | 100% | 100% | 100% |
| Zero fabricated citations | ✓ | ✓ | ✓ | ✓ |
| Scan-to-recipe latency | <20s | <20s | <25s | <25s |
| Core scan LLM calls | ≤2 | ≤2 | ≤2 | ≤2 |
| Core scan output tokens | ≤2,800 | ≤2,800 | ≤2,600 | ≤2,600 |
| Live discovery LLM calls | — | — | ≤1 (batched) | ≤1 (batched) |
| Mobile usability | ✓ | ✓ | ✓ | ✓ |

---

## 8. Cross-Phase: DevOps & Infrastructure

### 8.1 CI/CD Pipeline (Set up in Week 1, evolves each phase)

```
┌──────────────────────────────────────────────────────────┐
│                   GitHub Actions CI/CD                    │
│                                                          │
│  On Pull Request:                                        │
│  ├── lint (ruff + eslint + prettier)                     │
│  ├── type-check (mypy + TypeScript)                      │
│  ├── unit-tests (pytest)                                 │
│  ├── integration-tests (pytest + Docker Compose)         │
│  └── e2e-tests (Playwright, Phase 4+)                    │
│                                                          │
│  On Merge to main:                                       │
│  ├── All above checks                                    │
│  ├── Build Docker images                                 │
│  ├── Push to container registry                          │
│  └── Deploy to staging (optional)                        │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Environment Promotion

| Environment | Purpose | Infrastructure |
|---|---|---|
| **Local** | Development | Docker Compose (all services) |
| **CI** | Automated testing | GitHub Actions + Docker Compose |
| **Staging** | Pre-production validation | Cloud Run / single VM (optional) |
| **Production** | User-facing | Cloud Run or GKE (per architecture §18) |

### 8.3 Infrastructure Milestones

| Milestone | Phase | Description |
|---|---|---|
| Docker Compose working | 1.1 | All services start with `docker compose up` |
| CI pipeline running | 1.1 | GitHub Actions runs lint + test on PRs |
| PostgreSQL + pgvector | 2.1 | Vector search enabled in database |
| Redis caching | 3.4 | Search result and discovery caching |
| Celery worker | 2.4 | Background ingestion task processing |
| PWA service worker | 4.4 | Offline support, installability |

---

## 9. Risk Register & Mitigations

| **Risk** | **Likelihood** | **Impact** | **Mitigation** |
|---|---|---|---|
| **LLM token usage / API costs exceed budget** | Medium | High | Default to `gemini-2.5-flash` (~10× cheaper). Merge calls (eval + synthesis + explanation into 1 call). Use compact schemas with short keys. Batch live discovery calls. Aggressive Redis caching. Enforce token budget regression tests in CI. |
| **Gemini Vision extraction accuracy is low** | Medium | High | Prompt iteration with compressed rules. Tesseract OCR fallback. User correction UI always available. |
| **LLM generates recipes with invalid arithmetic** | Medium | High | Pydantic `@model_validator` catches all violations. Retry with error feedback. Validator runs before every response. |
| **LLM fabricates source URLs or authors** | Medium | High | Structured output mode with schema enforcement. Post-generation check: every cited URL exists in `recipe_sources` table. |
| **Search API rate limits exceeded** | Medium | Medium | Redis-backed rate limiter. Configurable per-hour cap. Search result caching (1h TTL). Graceful degradation to local KB. |
| **Fetched pages contain prompt injection** | Low | High | Content wrapped in data delimiters. System prompt instructs model to treat retrieved text as data. Content sanitisation before prompt inclusion. |
| **Search API costs exceed budget** | Medium | Medium | Configurable rate limits. Search result caching. Batch ingestion for known sources reduces per-scan search calls. |
| **pgvector search is too slow at scale** | Low | Medium | IVFFlat index with tuned `lists` parameter. Dataset expected to be <10K documents. Can upgrade to HNSW index. |
| **Live discovery adds too much latency** | Medium | Medium | Strict 15-second timeout budget. Partial results accepted. Parallel fetch. Discovery runs concurrently with local retrieval. |
| **Coffee bag images vary too much in layout** | High | Medium | Vision-capable LLM handles layout variation well. Low-confidence fields flagged for user correction. Prompt designed for varied layouts. |
| **Curated recipe sources go offline** | Medium | Low | Periodic accessibility checks (batch ingestion). `is_accessible` flag on sources. `last_verified` timestamp. Stale sources noted in evidence. |

---

## 10. Definition of Done — Full Project

The project is complete when ALL of the following are demonstrated:

### User Journey Verification

- [ ] **1.** User photographs a real coffee bag → extraction succeeds
- [ ] **2.** Extracted fields displayed with confidence indicators → user can correct
- [ ] **3.** User optionally selects grinder and dripper → equipment profile saved
- [ ] **4.** System searches knowledge base AND live web for recipes → sources displayed
- [ ] **5.** Original sources shown with match type (exact/related/analogous) → links work
- [ ] **6.** Personalised recipe generated based on evidence + equipment → arithmetic correct
- [ ] **7.** Fallback recipe generated when no evidence found → labelled as AI-generated
- [ ] **8.** Recipe displayed with clear quantities, timings, step-by-step instructions → brew timer works
- [ ] **9.** User records brew outcome → targeted adjustment recommended → changes only 1–2 variables

### Technical Verification

- [ ] **10.** No hardcoded example results — all pipeline steps use real providers
- [ ] **11.** No fabricated citations — every cited source is a real, verified URL
- [ ] **12.** Recipe arithmetic passes validation 100% of the time
- [ ] **13.** Provider abstraction works — can swap LLM/vision/search via config
- [ ] **14.** Live discovery runs inline during scan, not only as background task
- [ ] **15.** "No results found" distinguished from "search failed" in UI
- [ ] **16.** All unit tests, integration tests, and E2E tests pass
- [ ] **17.** README documents setup, env vars, running, testing, and deployment
- [ ] **18.** Evaluation dataset covers varied origins, processes, roasts, image quality, and recipe availability

### Deliverables Checklist

| # | Deliverable | Status |
|---|---|---|
| 1 | Working application — complete coffee-bag-to-recipe flow | ☐ |
| 2 | Documented system architecture | ☐ |
| 3 | Structured data model (profiles, recipes, equipment, history) | ☐ |
| 4 | Functioning image extraction pipeline | ☐ |
| 5 | RAG pipeline with retrieval evaluation and provenance | ☐ |
| 6 | Recipe recommendation and fallback generation | ☐ |
| 7 | Intuitive interface for recipe discovery and brewing | ☐ |
| 8 | Unit tests and integration tests | ☐ |
| 9 | Evaluation dataset and procedure | ☐ |
| 10 | README with setup and deployment instructions | ☐ |
| 11 | E2E demonstrations (exact match, related, fallback) | ☐ |
