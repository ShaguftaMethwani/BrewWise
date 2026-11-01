# BrewWise — System Architecture

> **Version:** 1.2 · **Status:** Proposed · **Last Updated:** 2026-10-31

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [High-Level System Diagram](#2-high-level-system-diagram)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend API Architecture](#4-backend-api-architecture)
5. [Vision & Extraction Service](#5-vision--extraction-service)
6. [Coffee Identity Resolution Service](#6-coffee-identity-resolution-service)
7. [Recipe Ingestion Pipeline](#7-recipe-ingestion-pipeline)
8. [Retrieval Service (RAG)](#8-retrieval-service-rag)
9. [Recipe Synthesis Service](#9-recipe-synthesis-service)
10. [Equipment Personalisation Module](#10-equipment-personalisation-module)
11. [Feedback & Brew History Service](#11-feedback--brew-history-service)
12. [Data Layer & Schema Design](#12-data-layer--schema-design)
13. [API Contract Reference](#13-api-contract-reference)
14. [Security & Privacy Architecture](#14-security--privacy-architecture)
15. [Observability & Monitoring](#15-observability--monitoring)
16. [Performance & Caching Strategy](#16-performance--caching-strategy)
17. [Cost Optimisation Strategy](#17-cost-optimisation-strategy)
18. [Deployment Architecture](#18-deployment-architecture)
19. [Testing Strategy](#19-testing-strategy)
20. [Phased Implementation Roadmap](#20-phased-implementation-roadmap)
21. [Key Architectural Decisions](#21-key-architectural-decisions)
22. [Appendix](#22-appendix)

---

## 1. Architecture Overview

### 1.1 Design Philosophy

BrewWise is designed around four architectural tenets:

| Tenet | Description |
|---|---|
| **Modularity** | Every AI provider (vision model, LLM, embedding model, search provider) is behind an abstraction layer and can be swapped independently. |
| **Transparency-first** | Every piece of data in a recommendation carries provenance metadata — sourced, inferred, or generated — so the user always knows *why*. |
| **Graceful degradation** | The system produces useful output even when OCR fails partially, retrieval returns nothing, or external search is unavailable. |
| **Incremental complexity** | The MVP works end-to-end with minimal infrastructure; advanced features (live search, personalisation) layer on without rewriting the core. |

### 1.2 Architectural Style

The system follows a **modular monolith** pattern for the backend (single deployable, internally decomposed into service modules), with a clear separation between:

- **Frontend** — React-based SPA / PWA
- **Backend API** — Python FastAPI application
- **Data Layer** — PostgreSQL (with pgvector), Redis, Object Storage
- **External Services** — Vision/LLM providers, Search APIs

This avoids premature micro-service complexity while keeping each concern independently testable and replaceable.

### 1.3 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React 18+ with TypeScript, Vite | Fast build tooling, strong ecosystem, PWA support |
| Styling | Vanilla CSS + CSS Modules | Full control, no framework lock-in |
| Backend | Python 3.12+, FastAPI | Async-first, excellent typing, OpenAPI auto-docs |
| ORM / DB | SQLAlchemy 2.0 + Alembic | Mature async ORM, migration support |
| Database | PostgreSQL 16 + pgvector | Relational + vector search in one engine |
| Cache | Redis 7 | Session cache, rate limiting, result caching |
| Object Storage | S3-compatible (MinIO for local dev) | Coffee bag images, ingested documents |
| Task Queue | Celery + Redis broker | Async ingestion, batch embedding jobs |
| Vision / OCR | Google Gemini Flash (multimodal, primary), Tesseract (fallback) | Multimodal extraction + offline fallback; Flash is 10× cheaper than Pro with comparable quality for structured extraction |
| LLM | Google Gemini 2.5 Flash (primary), configurable | Structured output, function calling; upgrade to Pro only if eval scores drop below threshold |
| Embeddings | `text-embedding-004` (primary), configurable | High-quality semantic retrieval |
| Search | Google Custom Search API / Tavily (optional) | Live recipe discovery |
| Testing | pytest, Playwright, pytest-asyncio | Backend + E2E + async testing |
| CI/CD | GitHub Actions | Automated test, lint, deploy pipeline |
| Containerisation | Docker + Docker Compose | Reproducible local and production environments |

---

## 2. High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (PWA)                             │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐ ┌──────────┐ │
│  │  Camera/  │ │  Coffee   │ │ Equipment │ │ Recipe │ │  Brew    │ │
│  │  Upload   │ │  Profile  │ │  Config   │ │ View   │ │ History  │ │
│  └────┬─────┘ └─────┬─────┘ └─────┬─────┘ └───┬────┘ └────┬─────┘ │
│       │              │             │            │           │       │
└───────┼──────────────┼─────────────┼────────────┼───────────┼───────┘
        │              │             │            │           │
        ▼              ▼             ▼            ▼           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   API Router │  │  Auth / Rate │  │   Request Validation     │  │
│  │   Layer      │  │  Limiting    │  │   (Pydantic v2)          │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────────┘  │
│         │                                                           │
│  ┌──────┴──────────────────────────────────────────────────────┐    │
│  │                   SERVICE MODULES                           │    │
│  │                                                             │    │
│  │  ┌───────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │    │
│  │  │  Vision & │ │  Identity  │ │ Retrieval  │ │  Recipe  │  │    │
│  │  │ Extraction│ │ Resolution │ │  Service   │ │ Synthesis│  │    │
│  │  └─────┬─────┘ └─────┬──────┘ └─────┬──────┘ └────┬─────┘  │    │
│  │        │              │              │             │         │    │
│  │  ┌─────┴─────┐ ┌─────┴──────┐ ┌─────┴──────┐ ┌───┴───────┐ │    │
│  │  │ Equipment │ │  Feedback  │ │  Ingestion  │ │ Provenance│ │    │
│  │  │ Module    │ │  Service   │ │  Pipeline   │ │ Tracker   │ │    │
│  │  └───────────┘ └────────────┘ └─────────────┘ └───────────┘ │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PROVIDER ABSTRACTION LAYER                │   │
│  │   VisionProvider  │  LLMProvider  │  EmbeddingProvider       │   │
│  │   SearchProvider  │  StorageProvider                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
┌──────────────────┐ ┌───────────┐ ┌──────────────────┐
│   PostgreSQL     │ │   Redis   │ │  Object Storage  │
│   + pgvector     │ │           │ │  (S3 / MinIO)    │
│                  │ │           │ │                  │
│ • Users          │ │ • Cache   │ │ • Coffee bag     │
│ • Coffee profiles│ │ • Sessions│ │   images         │
│ • Recipes        │ │ • Rate    │ │ • Ingested       │
│ • Equipment      │ │   limits  │ │   documents      │
│ • Brew history   │ │           │ │                  │
│ • Embeddings     │ │           │ │                  │
└──────────────────┘ └───────────┘ └──────────────────┘
```

---

## 3. Frontend Architecture

### 3.1 Application Type

Progressive Web App (PWA) built with React 18+ and TypeScript, served via Vite.

- **Offline capability:** Service worker caches static assets and saved recipes for offline viewing during brewing.
- **Camera access:** Uses the `MediaDevices` API for direct camera capture on mobile.
- **Responsive design:** Mobile-first layout optimised for single-handed use during brewing.

### 3.2 Page / Screen Structure

| Screen | Route | Purpose |
|---|---|---|
| Home | `/` | Hero CTA: "Scan a Coffee Bag", recent brews |
| Image Capture | `/scan` | Camera viewfinder + file upload |
| Coffee Profile | `/profile/:id` | Editable extracted metadata with confidence indicators |
| Equipment Setup | `/equipment` | Grinder + dripper selection, saved profiles |
| Recipe Results | `/recipe/:id` | Retrieved recipes, evidence panel, recommended recipe |
| Brew Timer | `/brew/:id` | Step-by-step pour timer with haptic feedback |
| Brew History | `/history` | Saved brews, comparison view |
| Settings | `/settings` | User preferences, equipment profiles, theme |

### 3.3 State Management

```
┌──────────────────────────────────────────────┐
│               React Context / Zustand        │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  Scan    │  │ Equipment│  │   Recipe    │ │
│  │  State   │  │  State   │  │   State     │ │
│  └──────────┘  └──────────┘  └────────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  User    │  │  Brew    │  │   UI       │ │
│  │  State   │  │  History │  │   State    │ │
│  └──────────┘  └──────────┘  └────────────┘ │
└──────────────────────────────────────────────┘
```

- **Zustand** for lightweight global state (no boilerplate overhead of Redux).
- **React Query (TanStack Query)** for server state, caching, and optimistic updates.
- **Local Storage** for persisting equipment profiles and saved recipes offline.

### 3.4 Key UI Components

| Component | Description |
|---|---|
| `ImageCapture` | Camera viewfinder with overlay guides, file drag-and-drop |
| `CoffeeProfileEditor` | Form with field-level confidence badges (✅ read, ⚠️ inferred, ❓ unknown) |
| `EquipmentSelector` | Searchable dropdown with saved profiles, add-custom option |
| `RecipeCard` | Displays recipe with source badge, match-type indicator |
| `EvidencePanel` | Collapsible panel showing retrieval sources, relevance scores, match explanations |
| `BrewTimerStepper` | Countdown timer per pour stage, vibration alerts, swipe-to-advance |
| `FeedbackForm` | Structured sliders (sourness ↔ bitterness, strength, overall satisfaction) |
| `RecipeComparison` | Side-by-side diff view of two brew attempts |

### 3.5 Image Handling

1. Client-side image compression (max 2048px longest edge, WebP conversion) before upload to reduce bandwidth.
2. EXIF stripping for privacy.
3. Preview shown immediately while upload + extraction proceeds in the background.
4. Upload via `multipart/form-data` to the backend.

---

## 4. Backend API Architecture

### 4.1 Module Structure

```
brewwise/
├── main.py                     # FastAPI app factory, middleware, lifespan
├── config.py                   # Pydantic Settings (env-based config)
├── dependencies.py             # Dependency injection container
│
├── api/                        # API route layer
│   ├── v1/
│   │   ├── scan.py             # POST /scan — image upload & extraction
│   │   ├── profiles.py         # CRUD for coffee profiles
│   │   ├── equipment.py        # CRUD for equipment profiles
│   │   ├── recipes.py          # Recipe search, generation, retrieval
│   │   ├── brews.py            # Brew logging, feedback, history
│   │   └── health.py           # Health & readiness probes
│   └── router.py               # Aggregated v1 router
│
├── services/                   # Business logic layer
│   ├── vision/
│   │   ├── base.py             # VisionProvider ABC
│   │   ├── gemini_vision.py    # Gemini multimodal implementation
│   │   ├── tesseract.py        # Tesseract OCR fallback
│   │   └── extractor.py        # Structured field extraction orchestrator
│   │
│   ├── identity/
│   │   ├── resolver.py         # Coffee identity normalisation & matching
│   │   ├── normaliser.py       # Name, process, roast normalisation
│   │   └── confidence.py       # Confidence scoring for identity fields
│   │
│   ├── retrieval/
│   │   ├── base.py             # RetrieverProvider ABC
│   │   ├── hybrid_retriever.py # Combines keyword + vector search
│   │   ├── reranker.py         # Cross-encoder or LLM-based reranking
│   │   ├── relevance.py        # Evidence evaluation (match type classification)
│   │   └── query_builder.py    # Builds retrieval queries from coffee profile
│   │
│   ├── synthesis/
│   │   ├── recipe_generator.py # LLM-powered recipe generation
│   │   ├── adapter.py          # Equipment-aware recipe adaptation
│   │   ├── validator.py        # Arithmetic & constraint validation
│   │   └── explainer.py        # Generates provenance explanations
│   │
│   ├── equipment/
│   │   ├── catalogue.py        # Equipment catalogue management
│   │   ├── grinder_guide.py    # Grinder-specific grind size mapping
│   │   └── dripper_guide.py    # Dripper-specific flow/technique guidance
│   │
│   ├── feedback/
│   │   ├── analyser.py         # Feedback → adjustment recommendation
│   │   └── history.py          # Brew history queries & comparisons
│   │
│   ├── ingestion/
│   │   ├── pipeline.py         # Orchestrates ingestion workflow
│   │   ├── scrapers/           # Source-specific extractors
│   │   │   ├── base.py         # ScraperProvider ABC
│   │   │   ├── blog_scraper.py
│   │   │   └── rss_scraper.py
│   │   ├── parser.py           # Extracts recipe fields from raw content
│   │   ├── deduplicator.py     # Content-hash + semantic dedup
│   │   └── indexer.py          # Writes to DB + generates embeddings
│   │
│   └── discovery/              # Live web discovery (inline during scan)
│       ├── orchestrator.py     # Coordinates search → fetch → ingest → merge
│       ├── page_fetcher.py     # HTTP fetch with robots.txt, timeouts, sanitisation
│       ├── recipe_extractor.py # LLM-based recipe extraction from fetched pages
│       ├── access_checker.py   # Robots.txt parser, auth-wall detection
│       └── result_merger.py    # Merges live results into local retrieval set
│
├── providers/                  # External service abstraction
│   ├── llm/
│   │   ├── base.py             # LLMProvider ABC
│   │   ├── gemini.py           # Google Gemini implementation
│   │   └── openai_compat.py    # OpenAI-compatible fallback
│   │
│   ├── embeddings/
│   │   ├── base.py             # EmbeddingProvider ABC
│   │   └── gemini_embed.py     # text-embedding-004
│   │
│   ├── search/
│   │   ├── base.py             # SearchProvider ABC
│   │   ├── google_search.py    # Google Custom Search
│   │   └── tavily.py           # Tavily search API
│   │
│   └── storage/
│       ├── base.py             # StorageProvider ABC
│       ├── s3.py               # S3-compatible storage
│       └── local.py            # Local filesystem (dev)
│
├── models/                     # SQLAlchemy ORM models
│   ├── user.py
│   ├── coffee_profile.py
│   ├── recipe.py
│   ├── equipment.py
│   ├── brew_log.py
│   └── recipe_source.py
│
├── schemas/                    # Pydantic request/response schemas
│   ├── scan.py
│   ├── coffee_profile.py
│   ├── recipe.py
│   ├── equipment.py
│   ├── brew.py
│   └── common.py
│
├── db/
│   ├── session.py              # Async session factory
│   ├── migrations/             # Alembic migrations
│   └── seed.py                 # Seed data (equipment catalogue, baseline recipes)
│
├── prompts/                    # Versioned LLM prompts (Jinja2 templates)
│   ├── v1/
│   │   ├── extract_coffee.j2
│   │   ├── generate_recipe.j2
│   │   ├── evaluate_evidence.j2
│   │   ├── adapt_recipe.j2
│   │   ├── explain_recipe.j2
│   │   └── feedback_adjust.j2
│   └── registry.py            # Prompt version management
│
└── utils/
    ├── validators.py           # Recipe arithmetic validation
    ├── normalisation.py        # Text normalisation helpers
    └── logging.py              # Structured logging config
```

### 4.2 Request Lifecycle

The following diagram illustrates the complete lifecycle of a "scan and recommend" request:

```
User uploads image
        │
        ▼
┌───────────────────┐
│  1. SCAN ENDPOINT │ POST /api/v1/scan
└────────┬──────────┘
         │  Accepts multipart image, validates format/size
         ▼
┌───────────────────────────┐
│  2. VISION & EXTRACTION   │
│  ─────────────────────    │
│  • Send image to Gemini   │
│    Vision (or Tesseract)  │
│  • Extract structured     │
│    coffee metadata        │
│  • Assign confidence per  │
│    field                  │
│  • Mark unknowns          │
└────────┬──────────────────┘
         │  Returns: CoffeeProfile (draft)
         ▼
┌───────────────────────────┐
│  3. IDENTITY RESOLUTION   │
│  ─────────────────────    │
│  • Normalise names,       │
│    process, roast terms   │
│  • Attempt dedup against  │
│    known coffees in DB    │
│  • Flag ambiguities       │
└────────┬──────────────────┘
         │  Returns: ResolvedCoffeeProfile
         ▼
   ┌─────┴──────┐
   │ User edits │  (Frontend: profile correction screen)
   │ & confirms │
   └─────┬──────┘
         │  User optionally selects equipment
         ▼
┌───────────────────────────────┐
│  4. LIVE WEB DISCOVERY        │
│  ─────────────────────────    │
│  (runs in parallel with       │
│   local retrieval)            │
│  • Build search query from    │
│    confirmed profile          │
│  • Call SearchProvider API    │
│  • For each result URL:       │
│    - Check if already indexed │
│    - Fetch full page content  │
│      (not just snippets)      │
│    - Respect robots.txt,      │
│      auth walls, timeouts     │
│    - Extract recipe fields    │
│      via LLM                  │
│    - Validate & dedup         │
│    - Index into knowledge     │
│      base (optional persist)  │
│  • If search fails → report   │
│    limitation, continue with  │
│    local KB only              │
│  • Merge live results into    │
│    retrieval candidate set    │
└────────┬──────────────────────┘
         │  Returns: LiveDiscoveryResult
         ▼
┌───────────────────────────────┐
│  5. RETRIEVAL (RAG)           │
│  ─────────────────────────    │
│  • Hybrid search on local     │
│    knowledge base:            │
│    keyword + vector           │
│  • Merge with live discovery  │
│    results                    │
│  • Rerank all candidates      │
│  • Classify match type:       │
│    exact / related /          │
│    analogous / general        │
│  • Evaluate evidence quality  │
└────────┬──────────────────────┘
         │  Returns: EvidencePackage
         ▼
┌───────────────────────────────┐
│  6. RECIPE SYNTHESIS          │
│  ─────────────────────────    │
│  • Route by evidence:         │
│    A (exact) / B (related)    │
│    / C (fallback)             │
│  • Generate or adapt          │
│    recipe via LLM             │
│  • Apply equipment            │
│    personalisation            │
│  • Validate arithmetic        │
│  • Generate explanation       │
│  • Attach provenance          │
└────────┬──────────────────────┘
         │  Returns: PersonalisedRecipe
         ▼
   Response to Frontend
```

### 4.3 Provider Abstraction Layer

Every external AI/search service is accessed through an abstract base class (ABC). This enables:

- **Swappability:** Switch from Gemini to OpenAI or a local model without touching business logic.
- **Testing:** Mock providers in unit tests.
- **Multi-provider:** Use different models for different tasks if needed (default: Gemini Flash for all tasks; upgrade individual modules to Pro only when evals justify it).

```python
# Example: providers/llm/base.py
from abc import ABC, abstractmethod
from typing import Any

class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: type,  # Pydantic model
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Any:
        """Generate a response conforming to a Pydantic schema."""
        ...

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate free-form text."""
        ...
```

Provider registry (configured via environment variables):

```python
# config.py
class Settings(BaseSettings):
    # Vision
    VISION_PROVIDER: str = "gemini"   # "gemini" | "tesseract"
    # LLM
    LLM_PROVIDER: str = "gemini"     # "gemini" | "openai"
    LLM_MODEL: str = "gemini-2.5-flash"  # Flash by default; set to "gemini-2.5-pro" only if eval quality requires it
    # Embeddings
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "text-embedding-004"
    # Search — enabled by default; set to None to disable
    SEARCH_PROVIDER: str | None = "google"  # "google" | "tavily" | None

    # Live discovery settings
    LIVE_DISCOVERY_ENABLED: bool = True
    LIVE_DISCOVERY_MAX_URLS: int = 5          # Max URLs to fetch per scan
    LIVE_DISCOVERY_TIMEOUT_SECONDS: int = 10  # Per-URL fetch timeout
    LIVE_DISCOVERY_TOTAL_TIMEOUT: int = 15    # Overall discovery budget
    LIVE_DISCOVERY_PERSIST: bool = True        # Persist discovered recipes in KB
    LIVE_DISCOVERY_RATE_LIMIT: int = 30       # Max search API calls per hour
    LIVE_DISCOVERY_RETRY_LIMIT: int = 2       # Retries on transient failures
```

---

## 5. Vision & Extraction Service

### 5.1 Purpose

Convert a photograph of a coffee bag into a structured `CoffeeProfile` with per-field confidence scores.

### 5.2 Extraction Pipeline

```
Image Upload
     │
     ▼
┌────────────────────┐
│ Image Preprocessing│
│ • Validate format  │
│ • Resize if needed │
│ • Store in object  │
│   storage          │
└────────┬───────────┘
         │
         ▼
┌────────────────────────────────┐
│ Primary: Gemini Vision         │
│ • Send image + extraction      │
│   prompt                       │
│ • Request structured JSON      │
│   output conforming to         │
│   CoffeeProfileSchema          │
│ • Prompt instructs model to:   │
│   - Extract only visible text  │
│   - Mark missing fields as     │
│     null / "unknown"           │
│   - NOT infer or guess values  │
│   - Assign confidence per      │
│     field                      │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Schema Validation (Pydantic)   │
│ • Validate all fields          │
│ • Check confidence values      │
│ • Ensure no hallucinated       │
│   fields                       │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Fallback: Tesseract OCR        │
│ (if Gemini unavailable or      │
│  returns low-confidence        │
│  results)                      │
│ • Raw text extraction          │
│ • Regex-based field parsing    │
│ • Lower confidence baseline    │
└────────┬───────────────────────┘
         │
         ▼
   CoffeeProfile (draft)
```

### 5.3 Extraction Output Schema

```python
# Compact LLM output schema — short keys reduce output tokens by ~60%
# The LLM generates this compact form; code expands to full field names post-extraction
class ExtractedFieldCompact(BaseModel):
    """Compact schema sent to/from LLM. Expanded to ExtractedField in post-processing."""
    v: str | None              # value
    c: float                   # confidence (0.0 – 1.0)
    # 'source' omitted — always "bag_text" (enforced by prompt); only flag exceptions
    # 'raw_text' omitted — only include via separate debug mode if c < 0.7

class ExtractedField(BaseModel):
    """Full schema used internally after expansion from compact form."""
    value: str | None
    confidence: float          # 0.0 – 1.0
    source: Literal["bag_text", "inferred", "unknown"]
    raw_text: str | None       # Original OCR text that produced this value

    @classmethod
    def from_compact(cls, compact: ExtractedFieldCompact, source: str = "bag_text") -> "ExtractedField":
        return cls(value=compact.v, confidence=compact.c, source=source, raw_text=None)

class CoffeeProfileDraftCompact(BaseModel):
    """Compact LLM output schema (~600 output tokens vs ~1,500 with full schema)."""
    brand: ExtractedFieldCompact
    name: ExtractedFieldCompact         # product_name
    estate: ExtractedFieldCompact
    country: ExtractedFieldCompact
    region: ExtractedFieldCompact
    varietal: ExtractedFieldCompact
    process: ExtractedFieldCompact
    roast: ExtractedFieldCompact        # roast_level
    roast_date: ExtractedFieldCompact
    notes: ExtractedFieldCompact        # tasting_notes
    altitude: ExtractedFieldCompact
    dose: ExtractedFieldCompact | None  # dose_recommendation
    extra: list[ExtractedFieldCompact]

class CoffeeProfileDraft(BaseModel):
    """Full internal schema — expanded from CoffeeProfileDraftCompact after LLM call."""
    brand: ExtractedField
    product_name: ExtractedField
    estate: ExtractedField
    country: ExtractedField
    region: ExtractedField
    varietal: ExtractedField
    process: ExtractedField
    roast_level: ExtractedField
    roast_date: ExtractedField
    tasting_notes: ExtractedField
    altitude: ExtractedField
    dose_recommendation: ExtractedField | None
    additional_info: list[ExtractedField]
    image_id: str
    extraction_model: str
    extraction_timestamp: datetime

    @classmethod
    def from_compact(cls, compact: CoffeeProfileDraftCompact, image_id: str, model: str) -> "CoffeeProfileDraft":
        """Expand compact LLM output to full internal schema."""
        return cls(
            brand=ExtractedField.from_compact(compact.brand),
            product_name=ExtractedField.from_compact(compact.name),
            estate=ExtractedField.from_compact(compact.estate),
            # ... expand all fields similarly
            image_id=image_id,
            extraction_model=model,
            extraction_timestamp=datetime.utcnow(),
        )
```

### 5.4 Confidence Handling

| Confidence | Interpretation | UI Indicator |
|---|---|---|
| 0.9 – 1.0 | High confidence, clearly legible | ✅ Green badge |
| 0.6 – 0.89 | Moderate confidence, may need review | ⚠️ Amber badge |
| 0.0 – 0.59 | Low confidence or partially legible | ❓ Red badge |
| `null` | Field not found on the bag | 🔲 Grey "Unknown" |

### 5.5 Edge Case Handling

| Scenario | Behaviour |
|---|---|
| Non-coffee product uploaded | Return error with message: "This doesn't appear to be a coffee bag" |
| Very blurry image | Return partial extraction with low confidence scores across all fields |
| Multiple coffee bags in frame | Extract the most prominent one, warn user |
| Non-English text | Attempt extraction (Gemini supports multilingual); flag language in metadata |

---

## 6. Coffee Identity Resolution Service

### 6.1 Purpose

Normalise extracted coffee metadata into a canonical form suitable for retrieval matching, while tracking confidence and disambiguation status.

### 6.2 Normalisation Rules

```
┌────────────────────────────────────────────────┐
│          NORMALISATION PIPELINE                │
│                                                │
│  1. Process Method Normalisation               │
│     "Natural Process" → "natural"              │
│     "Fully Washed"   → "washed"               │
│     "Honey Process"  → "honey"                 │
│     "Anaerobic Nat"  → "anaerobic_natural"     │
│                                                │
│  2. Roast Level Normalisation                  │
│     "Light Roast"    → "light"                 │
│     "Medium-Light"   → "medium_light"          │
│     "Omni Roast"     → "omni"                  │
│     "Filter Roast"   → "light"  (with note)    │
│                                                │
│  3. Name Normalisation                         │
│     Strip "Coffee Roasters", "Co.", etc.       │
│     Normalise unicode, diacritics              │
│     Handle common abbreviations                │
│                                                │
│  4. Origin Normalisation                       │
│     Expand abbreviations: "SHB" → "Strictly   │
│       Hard Bean"                               │
│     Normalise region names to canonical forms  │
│     Map known estate aliases                   │
│                                                │
│  5. Deduplication Check                        │
│     Query existing coffee_profiles table       │
│     Fuzzy match on brand + estate + process    │
│     If match found, link rather than duplicate  │
└────────────────────────────────────────────────┘
```

### 6.3 Ambiguity Resolution

When ambiguity materially affects recipe retrieval (e.g., "Riverdale" could be two estates in different countries), the system:

1. Returns candidate matches ranked by likelihood.
2. Flags the ambiguity to the user on the profile editing screen.
3. Uses the user's selection (or the top candidate if unresolved) for retrieval.

---

## 7. Recipe Ingestion Pipeline

### 7.1 Purpose

Populate the recipe knowledge base with real, attributed, structured recipe data from permitted sources. The ingestion pipeline operates in two modes:

- **Batch mode** — Periodic background ingestion from curated sources (RSS, URL lists, APIs).
- **Inline mode** — Real-time ingestion triggered during a user's scan workflow when live web discovery finds new URLs. This is a first-class pipeline mode, not an afterthought.

### 7.2 Pipeline Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  SOURCE DISCOVERY                        │
│                                                          │
│  BATCH MODE (background)    INLINE MODE (during scan)    │
│  ──────────────────────     ──────────────────────────   │
│  • RSS feeds                • Live web search results    │
│  • Curated URL lists        • URLs from SearchProvider   │
│  • API pulls                • Triggered per-scan,        │
│  • User submissions           not manually               │
└──────────────┬──────────────────────┬────────────────────┘
               │                      │
               ▼                      ▼
┌──────────────────────────────────────────────────────────┐
│  PAGE FETCHING & ACCESS CONTROL                          │
│  ──────────────────────────────                          │
│  • HTTP fetch with configurable timeout                  │
│  • robots.txt compliance check                           │
│  • Auth-wall / paywall detection → skip + log            │
│  • Content-type validation (HTML, text only)             │
│  • Rate limiting per domain                              │
│  • Respect source terms and access restrictions          │
│                                                          │
│  ⚠ CRITICAL: Search snippets are NEVER treated as       │
│    complete recipes. The full page MUST be fetched and    │
│    inspected before any recipe data is extracted.         │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  CONTENT EXTRACTION & RECIPE PARSING                     │
│  ────────────────────────────────                        │
│  • HTML → Markdown conversion (strip nav, ads, scripts)  │
│  • LLM-based structured recipe extraction                │
│  • Schema validation against RecipeSource model          │
│  • Reject pages that contain no brewing recipe           │
│  • Reject pages where brewing method ≠ pour-over         │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  DEDUP & ENRICHMENT                                      │
│  ──────────────────                                      │
│  • Content-hash dedup (SHA-256) against existing KB      │
│  • Metadata enrichment (coffee identity, equipment)      │
│  • Freshness tracking (retrieval_date, last_verified)    │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  INDEXING & EMBEDDING                                    │
│  ────────────────────                                    │
│  • Generate embeddings via EmbeddingProvider             │
│  • Write to pgvector index                               │
│  • Update FTS tsvector index                             │
│  • Persist in KB if LIVE_DISCOVERY_PERSIST=true          │
│  • Otherwise, hold in-memory for current request only    │
└──────────────────────────────────────────────────────────┘
```

### 7.3 Source Record Schema

Each ingested source is stored with full provenance:

```python
class RecipeSource(Base):
    __tablename__ = "recipe_sources"

    id: Mapped[uuid.UUID]
    url: Mapped[str]
    title: Mapped[str | None]
    author: Mapped[str | None]
    site_name: Mapped[str | None]
    raw_content: Mapped[str]           # Original extracted text
    content_hash: Mapped[str]          # SHA-256 for dedup
    retrieval_date: Mapped[datetime]
    publication_date: Mapped[datetime | None]
    is_accessible: Mapped[bool]        # Last-checked accessibility
    last_verified: Mapped[datetime | None]
    extraction_method: Mapped[str]     # "rss", "manual", "api", "live_search"
    discovery_context: Mapped[str | None]  # Search query that discovered this source
    recipes: Mapped[list["Recipe"]]    # One source may contain multiple recipes
```

### 7.4 Ingestion Modes

| Mode | Trigger | Timeout | Persistence | Priority |
|---|---|---|---|---|
| **Batch** | Celery periodic task (daily) | None (async) | Always persisted | Background |
| **Inline** | User scan → live web discovery | `LIVE_DISCOVERY_TOTAL_TIMEOUT` (default 15s) | Configurable (`LIVE_DISCOVERY_PERSIST`) | Real-time, per-request |
| **Manual** | Admin CLI or curation interface | None | Always persisted | On-demand |

**Inline mode constraints:**
- Must complete within the per-request timeout budget.
- Partial results are used if the timeout fires — the system does not wait for all URLs.
- Failed fetches are logged but do not block the scan pipeline.
- Results are merged into the current retrieval set regardless of persistence setting.

---

## 8. Retrieval Service (RAG)

### 8.1 Purpose

Given a confirmed `CoffeeProfile` and optional equipment, find the most relevant existing recipes from the knowledge base.

### 8.2 Hybrid Retrieval Pipeline

```
CoffeeProfile + Equipment
         │
         ▼
┌─────────────────────────────┐
│  1. QUERY CONSTRUCTION      │
│  ─────────────────────      │
│  Build multiple queries:    │
│  • Exact: brand + estate +  │
│    product name             │
│  • Producer: estate +       │
│    origin + process         │
│  • Characteristic: process  │
│    + roast + varietal +     │
│    origin                   │
│  • Equipment: dripper +     │
│    grinder model            │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  2. PARALLEL SEARCH                         │
│  ─────────────────                          │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │ Full-Text    │    │ Vector Search    │   │
│  │ Search (FTS) │    │ (pgvector)       │   │
│  │              │    │                  │   │
│  │ PostgreSQL   │    │ cosine_distance  │   │
│  │ tsvector     │    │ on recipe        │   │
│  │              │    │ embeddings       │   │
│  └──────┬───────┘    └────────┬─────────┘   │
│         │                     │             │
│         └──────────┬──────────┘             │
│                    ▼                        │
│         ┌──────────────────┐                │
│         │ Merge & Dedup    │                │
│         │ (RRF - Reciprocal│                │
│         │  Rank Fusion)    │                │
│         └────────┬─────────┘                │
└──────────────────┼──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. RERANKING                               │
│  ─────────                                  │
│  • Cross-encoder or LLM-based reranker      │
│  • Score on:                                │
│    - Coffee identity match                  │
│    - Recipe completeness                    │
│    - Brewing method match (pour-over only)  │
│    - Equipment compatibility                │
│  • Filter out non-recipe documents          │
│  • Filter out non-pour-over methods         │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  4. MATCH CLASSIFICATION                    │
│  ────────────────────                       │
│  For each result, classify:                 │
│                                             │
│  • EXACT     — same coffee, same producer   │
│  • STRONG    — same lot/release, alt name   │
│  • RELATED   — same producer or estate,     │
│                different coffee             │
│  • ANALOGOUS — similar characteristics      │
│                (process + roast + origin)    │
│  • GENERAL   — equipment guidance only      │
│                                             │
│  Apply configurable thresholds:             │
│  • exact_threshold: 0.92                    │
│  • strong_threshold: 0.85                   │
│  • related_threshold: 0.70                  │
│  • analogous_threshold: 0.55               │
│  • Below analogous → discard               │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  5. EVIDENCE EVALUATION                     │
│  ──────────────────────                     │
│  For each retained result, verify:          │
│  ✓ Contains an actual brewing recipe        │
│  ✓ Recipe is pour-over method               │
│  ✓ Recipe is sufficiently complete          │
│  ✓ Source is identifiable                   │
│  ✓ Equipment is compatible (if specified)   │
│  ✓ No conflicting safety concerns           │
│                                             │
│  Produce: EvidencePackage                   │
│  • matched_recipes: list[RankedRecipe]      │
│  • match_outcome: A | B | C                │
│  • conflicts: list[ParameterConflict]       │
│  • coverage_summary: str                    │
└─────────────────────────────────────────────┘
```

### 8.3 Evidence Outcome Classification

| Outcome | Trigger Condition | Downstream Behaviour |
|---|---|---|
| **A — Exact/Strong match** | ≥1 result classified as EXACT or STRONG | Present source recipes directly; adapt to user equipment |
| **B — Related match** | No EXACT/STRONG, but ≥1 RELATED or ANALOGOUS | Present as reference recipes; generate adapted recommendation |
| **C — Insufficient** | No results above analogous threshold | Generate fallback recipe from brewing principles |

### 8.4 Live Web Discovery Service

Live discovery is a **first-class step** in the scan-to-recipe pipeline, not an optional extension. It runs as part of the normal coffee-scanning workflow whenever a `SearchProvider` is configured (`LIVE_DISCOVERY_ENABLED=true`).

#### 8.4.1 Discovery Flow

```
Confirmed CoffeeProfile
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  1. QUERY CONSTRUCTION                                  │
│  • Build search query from extracted metadata:          │
│    "{brand} {estate} {product_name} pour-over recipe"   │
│  • Build fallback query if first returns no results:    │
│    "{estate} {origin} {process} V60 recipe"             │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  2. SEARCH API CALL                                     │
│  • Call SearchProvider (Google/Tavily) with query       │
│  • Retrieve top-N URLs (default: 5)                     │
│  • Apply rate limiting (LIVE_DISCOVERY_RATE_LIMIT)      │
│  • ⚠ Search snippets are metadata only — NEVER         │
│    treated as recipe content                            │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  3. URL FILTERING                                       │
│  • Check each URL against knowledge base (content_hash  │
│    or URL match) → skip already-indexed sources         │
│  • Check robots.txt compliance via access_checker       │
│  • Skip URLs requiring authentication or login          │
│  • Skip non-HTML content types (PDF fallback optional)  │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  4. FULL PAGE FETCH & EXTRACTION                        │
│  (parallel, with per-URL timeout)                       │
│  • HTTP GET with LIVE_DISCOVERY_TIMEOUT_SECONDS         │
│  • Strip navigation, ads, scripts → clean markdown      │
│  • Send cleaned content to LLM for structured           │
│    recipe extraction                                    │
│  • Validate extracted recipe against schema             │
│  • Reject pages with no pour-over recipe                │
│  • Sanitise content before any LLM prompt inclusion     │
│    (prompt injection defence)                           │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  5. DEDUP, INDEX & MERGE                                │
│  • Dedup against existing KB (content hash)             │
│  • Generate embedding for new content                   │
│  • Optionally persist in KB (LIVE_DISCOVERY_PERSIST)    │
│  • Merge validated recipes into the current retrieval   │
│    candidate set alongside local KB results             │
│  • Tag source as extraction_method="live_search"        │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
   LiveDiscoveryResult
   • discovered_recipes: list[DiscoveredRecipe]
   • search_status: "success" | "partial" | "failed" | "disabled"
   • urls_attempted: int
   • urls_yielded_recipes: int
   • errors: list[DiscoveryError]
```

#### 8.4.2 Outcome Distinction: No Results vs. Search Failure

The system explicitly distinguishes three outcomes:

| Outcome | Meaning | User-Facing Message |
|---|---|---|
| **`success` — recipes found** | Search ran, relevant recipes discovered | "Found {N} recipe(s) from online sources" |
| **`success` — no relevant results** | Search ran, but no pages contained relevant pour-over recipes | "No matching recipes were found in online sources for this coffee. This does not mean none exist — it means none were found in this search." |
| **`failed`** | Search API error, network failure, or timeout | "Online recipe search was unavailable. Results are based on the existing knowledge base only." |
| **`disabled`** | No SearchProvider configured | "Online search is not configured. Results are from the local knowledge base." |

A lack of results is **never** presented as proof that no recipe exists online.

#### 8.4.3 Safety & Trust Controls

| Control | Implementation |
|---|---|
| **No fabricated sources** | Only URLs actually returned by the search API and successfully fetched are cited. The system never generates fictional URLs, authors, or recipe attributions. |
| **Content treated as untrusted** | Fetched page content is wrapped in data delimiters in LLM prompts and treated as data, not instructions. The system prompt explicitly instructs the model to ignore embedded instructions in retrieved content. |
| **Snippet ≠ recipe** | Search result snippets are used only for URL prioritisation. Structured recipe data is extracted only from fully fetched page content. |
| **Access restrictions respected** | robots.txt is checked before fetch. Auth-walled, paywalled, or terms-restricted content is skipped and logged. |
| **Configurable via env vars** | Search provider, API keys, rate limits, timeouts, and persistence are all configured through environment variables — never hardcoded. |

#### 8.4.4 Latency Budget

Live discovery runs under a strict time budget to avoid degrading the user experience:

```
┌─────────────────────────────────────────────────────┐
│  LIVE DISCOVERY LATENCY BUDGET                       │
│                                                      │
│  Search API call .............. max 3 seconds        │
│  URL filtering + robots.txt ... max 1 second         │
│  Page fetches (parallel) ...... max 10 seconds each  │
│  Recipe extraction (LLM) ...... max 5 seconds each   │
│  ─────────────────────────────────────────            │
│  TOTAL BUDGET ................. max 15 seconds        │
│                                                      │
│  If budget exceeded:                                 │
│  • Use whatever results are ready                    │
│  • Mark search_status as "partial"                   │
│  • Log timed-out URLs for later batch ingestion      │
│  • Continue with local KB + partial live results     │
└─────────────────────────────────────────────────────┘
```

#### 8.4.5 Caching & Rate Limiting

- **Search result caching:** Identical search queries are cached in Redis (TTL: 1 hour) to avoid redundant API calls when multiple users scan the same coffee.
- **Per-domain rate limiting:** Max 2 concurrent fetches per domain to avoid overwhelming any single site.
- **Global search rate limiting:** `LIVE_DISCOVERY_RATE_LIMIT` (default: 30/hour) caps total search API calls.
- **URL-level caching:** Successfully fetched and parsed URLs are stored in the KB, so subsequent scans of the same coffee hit the local index instead of re-fetching.

---

## 9. Recipe Synthesis Service

### 9.1 Purpose

Produce a complete, validated, personalised pour-over recipe using the evidence package, coffee profile, and equipment.

> **Token optimisation (v1.1):** Evidence evaluation, recipe synthesis, and explanation generation are **merged into a single LLM call**. This reduces core LLM calls per scan from 4 → 2 and output tokens from ~4,800 → ~2,600. The match outcome (A/B/C) is a field in the unified response schema.

### 9.2 Synthesis Flow

```
RetrievalResults + CoffeeProfile + Equipment
                    │
                    ▼
    ┌──────────────────────────────────────────────────────┐
    │  UNIFIED EVALUATE + SYNTHESISE + EXPLAIN             │
    │  ────────────────────────────────────────             │
    │  (Single LLM call — ~2,000 output tokens)            │
    │                                                      │
    │  Input: retrieval results, coffee profile, equipment │
    │                                                      │
    │  The model performs all three steps in one call:      │
    │                                                      │
    │  1. EVALUATE EVIDENCE                                │
    │     • Classify each result (EXACT/STRONG/RELATED/    │
    │       ANALOGOUS/GENERAL)                             │
    │     • Determine match_outcome: A | B | C             │
    │     • Detect parameter conflicts                     │
    │                                                      │
    │  2. SYNTHESISE RECIPE (routed by outcome)            │
    │     • A: Present & adapt source recipe               │
    │     • B: Adapt from related evidence                 │
    │     • C: Generate from brewing principles            │
    │     • Apply equipment adaptation                     │
    │                                                      │
    │  3. EXPLAIN (inline in response schema)              │
    │     • Why this recipe                                │
    │     • What came from sources vs AI                   │
    │     • Equipment impact                               │
    │     • Key assumptions & troubleshooting              │
    │                                                      │
    │  Output: UnifiedRecipeResponse schema                │
    └────────────────────┬─────────────────────────────────┘
                         │
                         ▼
    ┌────────────────────────┐
    │  ARITHMETIC VALIDATION │
    │  ─────────────────     │
    │  ✓ dose × ratio =     │
    │    total_water         │
    │  ✓ Σ(pour_water) =    │
    │    total_water         │
    │  ✓ bloom_water ≤      │
    │    total_water         │
    │  ✓ temperature in     │
    │    80–100°C range      │
    │  ✓ brew_time > 0      │
    │  ✓ All pours have     │
    │    timing              │
    │  ✓ Pour sequence is    │
    │    chronologically     │
    │    ordered             │
    └────────────┬───────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  POST-PROCESSING           │
    │  ────────────────          │
    │  • Populate computed       │
    │    fields (recipe_id,      │
    │    coffee_profile_id,      │
    │    created_at, confidence) │
    │  • Copy equipment from     │
    │    user profile            │
    │  • Verify source_recipes   │
    │    against retrieval set   │
    └────────────┬───────────────┘
                 │
                 ▼
         PersonalisedRecipe
```

### 9.3 Recipe Output Schema

```python
class PourStep(BaseModel):
    step_number: int
    water_g: float
    cumulative_water_g: float
    start_time_seconds: int
    duration_seconds: int
    technique: str                     # e.g., "gentle centre pour", "circular pour"
    notes: str | None

class PersonalisedRecipe(BaseModel):
    recipe_id: str
    coffee_profile_id: str

    # Source & provenance
    source_type: Literal["exact_match", "adapted_from_related",
                         "ai_generated", "curated_baseline"]
    source_recipes: list[SourceReference]
    generation_model: str | None

    # Brewing parameters
    dripper: str
    grinder: str | None
    filter_type: str | None
    dose_g: float
    water_g: float
    ratio: str                         # e.g., "1:16"
    water_temperature_c: int
    grind_description: str
    grind_setting: str | None          # Grinder-specific, if available

    # Procedure
    filter_prep: str | None            # e.g., "Rinse paper filter with hot water"
    bloom_water_g: float
    bloom_time_seconds: int
    pour_schedule: list[PourStep]
    target_brew_time_seconds: int
    step_by_step_instructions: list[str]

    # Expectations
    expected_flavour: str
    flavour_is_prediction: bool = True  # Always true — never a guarantee

    # Explanation & troubleshooting
    explanation: RecipeExplanation
    troubleshooting: list[TroubleshootingTip]

    # Metadata
    adaptations: list[Adaptation]      # What was changed and why
    limitations: list[str]             # What the system doesn't know
    confidence: float
    created_at: datetime

    @model_validator(mode="after")
    def validate_arithmetic(self) -> Self:
        """Ensure water quantities and ratio are internally consistent."""
        total_pour_water = sum(p.water_g for p in self.pour_schedule)
        assert abs(total_pour_water - self.water_g) < 0.5, \
            f"Pour total {total_pour_water}g ≠ recipe total {self.water_g}g"
        # ... additional validations
        return self
```

### 9.4 Prompt Engineering

All LLM prompts are stored as versioned Jinja2 templates in `prompts/v1/`. Key prompts:

| Prompt | Purpose | Notes |
|---|---|---|
| `extract_coffee.j2` | Vision extraction with compact output schema (`ExtractedFieldCompact`) | Uses short key names to minimise output tokens (~600 vs ~1,500) |
| `evaluate_synthesise_explain.j2` | **Unified:** evidence evaluation + recipe synthesis + explanation generation | Replaces three separate prompts (`evaluate_evidence.j2`, `generate_recipe.j2`, `explain_recipe.j2`). Produces `UnifiedRecipeResponse` schema. Single call, ~2,000 output tokens. |
| `adapt_recipe.j2` | Adapt a source recipe to different equipment | Used within the unified call for Outcome A/B paths |
| `extract_web_recipe.j2` | Extract structured recipe data from fetched web pages | Batched: multiple pages sent in a single call |
| `feedback_adjust.j2` | Suggest adjustments based on brew feedback | |

> **Deprecated (v1.1):** `evaluate_evidence.j2`, `generate_recipe.j2`, and `explain_recipe.j2` are superseded by the unified `evaluate_synthesise_explain.j2` prompt. Kept in repo for reference/rollback.

Each prompt follows these optimisation guidelines:
- **Minimal instructions:** Use structured output mode to enforce schema compliance instead of verbose instructions.
- **No few-shot examples in production prompts** — rely on schema definitions and concise rules.
- System instructions with safety guardrails (no fabricated sources, no hallucinated grind settings).
- Output schema definition (for structured generation).
- Version number and changelog.

---

## 10. Equipment Personalisation Module

### 10.1 Equipment Catalogue Design

The equipment catalogue is a database-backed, extensible registry:

```python
class GrinderModel(Base):
    __tablename__ = "grinder_catalogue"

    id: Mapped[uuid.UUID]
    brand: Mapped[str]
    model: Mapped[str]
    type: Mapped[Literal["hand", "electric"]]
    burr_type: Mapped[str | None]          # "conical", "flat", "hybrid"
    grind_range: Mapped[str | None]        # e.g., "0-40 clicks"
    pour_over_range: Mapped[str | None]    # e.g., "18-28 clicks"
    reference_setting: Mapped[str | None]  # Common starting point
    notes: Mapped[str | None]

class DripperModel(Base):
    __tablename__ = "dripper_catalogue"

    id: Mapped[uuid.UUID]
    brand: Mapped[str]
    model: Mapped[str]
    type: Mapped[str]                      # "V60", "Kalita Wave", "flat-bottom", etc.
    sizes: Mapped[list[str]]               # ["01", "02", "03"]
    filter_types: Mapped[list[str]]        # ["paper_tabbed", "paper_untabbed", "metal"]
    flow_characteristics: Mapped[str]      # "fast", "moderate", "restricted"
    technique_notes: Mapped[str | None]    # Dripper-specific pouring guidance
```

### 10.2 Grind Size Mapping

When a supported grinder is selected, the system can map relative grind descriptions to grinder-specific settings:

```
┌───────────────────────────────────────────────────┐
│             GRIND SIZE MAPPING                     │
│                                                    │
│  Relative Description  →  Grinder-Specific Setting │
│  ────────────────────     ────────────────────────  │
│                                                    │
│  "Medium-fine"         →  Comandante C40: 22 clicks│
│  "Medium-fine"         →  1Zpresso JX: 2.4.0       │
│  "Medium-fine"         →  Baratza Encore: 12       │
│  "Medium-fine"         →  Fellow Ode Gen 2: 4      │
│                                                    │
│  If grinder is unknown:                            │
│  → "Medium-fine (slightly finer than table salt)"  │
│  → "Adjust finer if sour, coarser if bitter"       │
└───────────────────────────────────────────────────┘
```

### 10.3 Equipment Profiles

Users can save equipment profiles for quick re-use:

```python
class UserEquipmentProfile(Base):
    __tablename__ = "user_equipment_profiles"

    id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID]
    name: Mapped[str]                 # e.g., "My Home Setup"
    grinder_id: Mapped[uuid.UUID | None]
    grinder_custom: Mapped[str | None]  # Free-text if not in catalogue
    dripper_id: Mapped[uuid.UUID | None]
    dripper_custom: Mapped[str | None]
    dripper_size: Mapped[str | None]
    filter_type: Mapped[str | None]
    preferred_dose_g: Mapped[float | None]
    preferred_ratio: Mapped[str | None]
    water_temperature_c: Mapped[int | None]
    experience_level: Mapped[Literal["beginner", "experienced"] | None]
    is_default: Mapped[bool]
```

---

## 11. Feedback & Brew History Service

### 11.1 Brew Logging

After each brew, users can record:

```python
class BrewLog(Base):
    __tablename__ = "brew_logs"

    id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID]
    recipe_id: Mapped[uuid.UUID]
    coffee_profile_id: Mapped[uuid.UUID]

    # What the user actually did
    actual_dose_g: Mapped[float | None]
    actual_water_g: Mapped[float | None]
    actual_grind_setting: Mapped[str | None]
    actual_water_temp_c: Mapped[int | None]
    actual_brew_time_seconds: Mapped[int | None]

    # Sensory feedback
    acidity_sourness: Mapped[int | None]     # 1-5 scale
    bitterness: Mapped[int | None]           # 1-5 scale
    body_strength: Mapped[int | None]        # 1-5 scale
    sweetness: Mapped[int | None]            # 1-5 scale
    overall_satisfaction: Mapped[int | None]  # 1-5 scale
    flavour_notes: Mapped[str | None]        # Free text
    drawdown_speed: Mapped[Literal["fast", "normal", "slow", "stalled"] | None]

    # System-generated adjustment
    suggested_adjustments: Mapped[dict | None]  # JSON of recommended changes
    brewed_at: Mapped[datetime]
```

### 11.2 Feedback → Adjustment Logic

```
User Feedback
     │
     ▼
┌─────────────────────────────────────────────┐
│  DIAGNOSIS ENGINE                           │
│                                             │
│  IF sourness high AND bitterness low:       │
│    → Under-extracted                        │
│    → Suggest: finer grind OR higher temp    │
│      OR longer brew time                    │
│                                             │
│  IF bitterness high AND sourness low:       │
│    → Over-extracted                         │
│    → Suggest: coarser grind OR lower temp   │
│      OR shorter brew time                   │
│                                             │
│  IF both sour AND bitter:                   │
│    → Channelling likely                     │
│    → Suggest: more even pours, check grind  │
│      distribution                           │
│                                             │
│  IF drawdown stalled/very slow:             │
│    → Suggest: coarser grind, less agitation │
│      check for fines, try different filter  │
│                                             │
│  IF weak/watery:                            │
│    → Suggest: higher ratio, finer grind,    │
│      or higher dose                         │
│                                             │
│  RULE: Change only 1-2 variables at a time  │
└─────────────────────────────────────────────┘
```

---

## 12. Data Layer & Schema Design

### 12.1 Database Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     PostgreSQL 16 + pgvector                     │
│                                                                  │
│  ┌──────────────┐     ┌──────────────────┐    ┌──────────────┐  │
│  │    users      │     │ coffee_profiles   │    │  equipment   │  │
│  │  ──────       │     │ ──────────────    │    │  profiles    │  │
│  │  id (PK)      │     │ id (PK)           │    │  ──────────  │  │
│  │  email        │◀────│ user_id (FK)      │    │  id (PK)     │  │
│  │  display_name │     │ brand             │    │  user_id(FK) │  │
│  │  created_at   │     │ product_name      │    │  grinder_id  │  │
│  └──────┬────────┘     │ estate            │    │  dripper_id  │  │
│         │              │ country           │    │  ...         │  │
│         │              │ region            │    └──────────────┘  │
│         │              │ varietal          │                      │
│         │              │ process           │    ┌──────────────┐  │
│         │              │ roast_level       │    │  grinder_    │  │
│         │              │ roast_date        │    │  catalogue   │  │
│         │              │ tasting_notes     │    │  ──────────  │  │
│         │              │ altitude          │    │  id (PK)     │  │
│         │              │ image_id          │    │  brand       │  │
│         │              │ extraction_data   │    │  model       │  │
│         │              │ confidence_scores │    │  type        │  │
│         │              │ created_at        │    │  burr_type   │  │
│         │              └────────┬──────────┘    │  ...         │  │
│         │                       │               └──────────────┘  │
│         │                       │                                 │
│         │              ┌────────┴──────────┐    ┌──────────────┐  │
│         │              │   recipes          │    │  dripper_   │  │
│         │              │   ───────          │    │  catalogue  │  │
│         │              │   id (PK)          │    │  ──────────  │  │
│         │              │   coffee_profile_id│    │  id (PK)    │  │
│         │              │   source_type      │    │  brand      │  │
│         │              │   source_id (FK)   │────│  model      │  │
│         │              │   dripper          │    │  type       │  │
│         │              │   grinder          │    │  ...        │  │
│         │              │   dose_g           │    └──────────────┘  │
│         │              │   water_g          │                      │
│         │              │   ratio            │                      │
│         │              │   temperature_c    │                      │
│         │              │   grind_desc       │                      │
│         │              │   pour_schedule    │ (JSONB)              │
│         │              │   instructions     │ (JSONB)              │
│         │              │   explanation      │                      │
│         │              │   confidence       │                      │
│         │              │   created_at       │                      │
│         │              └────────┬──────────┘                      │
│         │                       │                                 │
│         │              ┌────────┴──────────┐                      │
│         └──────────────│   brew_logs        │                      │
│                        │   ─────────        │                      │
│                        │   id (PK)          │                      │
│                        │   user_id (FK)     │                      │
│                        │   recipe_id (FK)   │                      │
│                        │   actual_params    │ (JSONB)              │
│                        │   feedback         │ (JSONB)              │
│                        │   adjustments      │ (JSONB)              │
│                        │   brewed_at        │                      │
│                        └───────────────────┘                      │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                 recipe_sources                                │  │
│  │  id (PK) | url | title | author | raw_content |              │  │
│  │  content_hash | retrieval_date | is_accessible                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │               recipe_embeddings (pgvector)                    │  │
│  │  id (PK) | recipe_source_id (FK) | embedding vector(768)     │  │
│  │  chunk_text | chunk_index | metadata (JSONB)                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Indexes:                                                         │
│  • GIN on coffee_profiles(tasting_notes) for full-text search     │
│  • GIN on recipe_sources(raw_content) using tsvector for FTS      │
│  • IVFFlat on recipe_embeddings(embedding) for ANN vector search  │
│  • B-tree on coffee_profiles(brand, estate, process)              │
│  • B-tree on recipe_sources(content_hash) for dedup               │
└──────────────────────────────────────────────────────────────────┘
```

### 12.2 Embedding Strategy

| Content | Embedding Model | Dimensions | Index |
|---|---|---|---|
| Recipe source chunks | `text-embedding-004` | 768 | IVFFlat (pgvector) |
| Coffee profile summary | `text-embedding-004` | 768 | IVFFlat (pgvector) |

**Chunking strategy:**
- Recipe sources are split into overlapping chunks (512 tokens, 64 token overlap).
- Each chunk retains metadata (source_id, coffee name, brewing method) as structured JSONB.
- Embeddings are generated at ingestion time and cached.

---

## 13. API Contract Reference

### 13.1 Core Endpoints

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| `POST` | `/api/v1/scan` | Upload image, extract coffee profile | Optional |
| `GET` | `/api/v1/profiles/{id}` | Get coffee profile | Optional |
| `PUT` | `/api/v1/profiles/{id}` | Update/correct coffee profile | Optional |
| `POST` | `/api/v1/recipes/search` | Search for recipes given a profile | Optional |
| `POST` | `/api/v1/recipes/generate` | Generate personalised recipe | Optional |
| `GET` | `/api/v1/recipes/{id}` | Get a saved recipe | Optional |
| `GET` | `/api/v1/equipment/grinders` | List grinder catalogue | Public |
| `GET` | `/api/v1/equipment/drippers` | List dripper catalogue | Public |
| `POST` | `/api/v1/equipment/profiles` | Save equipment profile | Auth |
| `GET` | `/api/v1/equipment/profiles` | List user's equipment profiles | Auth |
| `POST` | `/api/v1/brews` | Log a brew attempt | Auth |
| `GET` | `/api/v1/brews` | List brew history | Auth |
| `POST` | `/api/v1/brews/{id}/feedback` | Submit brew feedback | Auth |
| `GET` | `/api/v1/brews/{id}/adjustments` | Get suggested adjustments | Auth |
| `GET` | `/api/v1/health` | Health check | Public |

### 13.2 Key Request/Response Examples

**POST `/api/v1/scan`**

```json
// Request: multipart/form-data
//   - image: File (JPEG, PNG, WebP; max 10 MB)

// Response: 200 OK
{
  "profile_id": "uuid",
  "coffee_profile": {
    "brand": { "value": "Blue Tokai", "confidence": 0.95, "source": "bag_text" },
    "estate": { "value": "Riverdale Estate", "confidence": 0.92, "source": "bag_text" },
    "country": { "value": "India", "confidence": 0.98, "source": "bag_text" },
    "region": { "value": "Chikmagalur", "confidence": 0.88, "source": "bag_text" },
    "process": { "value": "washed", "confidence": 0.90, "source": "bag_text" },
    "roast_level": { "value": "light", "confidence": 0.85, "source": "bag_text" },
    "varietal": { "value": null, "confidence": 0.0, "source": "unknown" },
    "tasting_notes": { "value": "Citrus, florals, stone fruit", "confidence": 0.87, "source": "bag_text" }
  },
  "image_id": "uuid",
  "extraction_model": "gemini-2.5-flash",
  "warnings": []
}
```

**POST `/api/v1/recipes/generate`**

```json
// Request: application/json
{
  "profile_id": "uuid",
  "equipment": {
    "grinder": { "catalogue_id": "uuid" },
    "dripper": { "catalogue_id": "uuid", "size": "02" },
    "filter_type": "paper_tabbed",
    "preferred_dose_g": 15,
    "experience_level": "beginner"
  }
}

// Response: 200 OK
{
  "recipe": { "...PersonalisedRecipe..." },
  "evidence": {
    "outcome": "B",
    "matched_recipes": [],
    "match_explanation": "No exact recipe found for this coffee. A recipe for another washed coffee from Riverdale Estate was used as a reference."
  }
}
```

---

## 14. Security & Privacy Architecture

### 14.1 Security Controls

| Layer | Control |
|---|---|
| **Input validation** | Pydantic v2 strict validation on all API inputs; file type + size restrictions on uploads (JPEG, PNG, WebP; max 10 MB) |
| **Authentication** | Optional JWT-based auth (for profile/history features); anonymous scan allowed |
| **Authorisation** | Users can only access their own profiles, equipment, and brew history |
| **API keys** | All provider API keys stored as environment variables, never exposed to frontend |
| **Rate limiting** | Redis-backed rate limiter: 10 scans/min per IP, 100 recipe requests/hour per user |
| **Content sanitisation** | Ingested web content treated as untrusted; stripped before inclusion in LLM prompts |
| **Prompt injection defence** | Retrieved content wrapped in data delimiters in prompts; system prompt instructs model to treat retrieved text as data, not instructions |
| **CORS** | Strict origin allowlist |
| **HTTPS** | Enforced in production |

### 14.2 Privacy Controls

| Concern | Approach |
|---|---|
| **Image retention** | Configurable: images deleted after extraction by default, or retained if user opts in |
| **User data** | Minimal PII collected; email only if account created |
| **EXIF data** | Stripped on the client side before upload |
| **Logging** | Structured logs exclude user images, API keys, and personal data |
| **Data export/deletion** | Support for user data export and account deletion (GDPR-aligned) |

---

## 15. Observability & Monitoring

### 15.1 Logging

- **Structured JSON logging** via Python `structlog`.
- Log levels: `DEBUG` (dev), `INFO` (production), `ERROR` (always).
- Key fields on every log: `request_id`, `user_id` (if authenticated), `service_module`, `duration_ms`.

### 15.2 Metrics

| Metric | Type | Purpose |
|---|---|---|
| `scan_extraction_duration_seconds` | Histogram | Track vision API latency |
| `retrieval_query_duration_seconds` | Histogram | Track RAG pipeline latency |
| `recipe_generation_duration_seconds` | Histogram | Track LLM generation latency |
| `retrieval_match_outcome` | Counter (A/B/C) | Track evidence quality distribution |
| `recipe_validation_failures` | Counter | Track arithmetic validation failures |
| `llm_token_usage` | Counter | Track cost per model |
| `active_users_daily` | Gauge | User engagement |

### 15.3 Error Tracking

- Unhandled exceptions → structured error log + optional Sentry integration.
- LLM failures → retry with exponential backoff (max 3 attempts), then fallback to baseline recipe.
- Vision failures → fallback to Tesseract OCR, then manual entry.

---

## 16. Performance & Caching Strategy

### 16.1 Caching Layers

```
┌────────────────────────────────────────────────┐
│                CACHING STRATEGY                 │
│                                                 │
│  Layer 1: Browser Cache                         │
│  • Static assets: 1 year (hashed filenames)     │
│  • Equipment catalogue: 1 hour                  │
│                                                 │
│  Layer 2: CDN / Reverse Proxy                   │
│  • Equipment catalogue endpoints                │
│  • Static recipe pages (if public)              │
│                                                 │
│  Layer 3: Redis Application Cache               │
│  • Embedding results: keyed by content hash     │
│  • Retrieval results: keyed by profile hash     │
│    (TTL: 1 hour)                                │
│  • Equipment catalogue: keyed by version        │
│    (TTL: 24 hours)                              │
│  • Rate limiting counters                       │
│                                                 │
│  Layer 4: PostgreSQL Query Cache                │
│  • pgvector index for fast ANN queries          │
│  • Materialised views for common aggregations   │
└────────────────────────────────────────────────┘
```

### 16.2 Performance Targets

| Operation | Target | Strategy |
|---|---|---|
| Image upload + extraction | < 8 seconds | Compress client-side, stream to vision API |
| Recipe retrieval (RAG) | < 3 seconds | Hybrid search with pre-computed embeddings |
| Recipe generation | < 10 seconds | Structured output mode, streaming response |
| Equipment catalogue load | < 200 ms | Redis cache, CDN |
| Full scan-to-recipe pipeline | < 20 seconds | Parallel where possible, progress indicators |

### 16.3 Progress Indicators

Since the full pipeline can take 15–20 seconds, the frontend displays granular progress:

1. ⬆️ "Uploading image..." (upload)
2. 🔍 "Reading your coffee bag..." (extraction)
3. ✅ "Coffee identified!" (profile ready)
4. 🔎 "Searching for recipes..." (retrieval)
5. ☕ "Crafting your recipe..." (synthesis)
6. 🎉 "Recipe ready!" (done)

Implemented via Server-Sent Events (SSE) on the `/api/v1/scan` endpoint for real-time progress streaming.

---

## 17. Cost Optimisation Strategy

### 17.1 LLM Call Budget (Optimised — v1.1)

> **Key changes from v1.0:** Switched to Gemini Flash (~10× cheaper per token), merged 3 calls into 1, compact extraction schema (~60% fewer output tokens), batched live discovery extraction.

| Operation | Model | Est. Output Tokens | Calls per Scan | Change from v1.0 |
|---|---|---|---|---|
| Image extraction (compact schema) | Gemini Flash | **~600** | 1 | Was ~1,500 (slim schema with short keys) |
| Evidence eval + Recipe synthesis + Explanation | Gemini Flash | **~2,000** | **1** | Was 3 separate calls totalling ~3,300 |
| **Core scan total** | | **~2,600** | **2** | **Was ~4,800 across 4 calls (46% reduction)** |
| Live discovery extraction (batched) | Gemini Flash | **~800** | 1 | Was ~300 × N (up to 5 separate calls) |
| **With live discovery** | | **~3,400** | **3** | **Was ~6,300 across 9 calls** |

**Input token savings:** Prompt compression (removing few-shot examples, using structured output mode for schema enforcement) reduces input overhead from ~4,000 → ~1,500 tokens per scan.

### 17.2 Cost Controls

| Strategy | Implementation |
|---|---|
| **Gemini Flash first** | Use Flash for all tasks by default; only upgrade to Pro for modules where evals show quality degradation |
| **Merged LLM calls** | Evidence evaluation + recipe synthesis + explanation in a single call (saves 2 round-trips + prompt overhead) |
| **Compact extraction schemas** | LLM outputs short key names (`v`, `c`); code expands to full field names post-extraction |
| **Avoid redundant calls** | Cache extraction results; don't re-extract if image unchanged |
| **Batched live extraction** | Multiple fetched pages sent to LLM in a single call instead of one call per URL |
| **Skip discovery for known coffees** | If KB has ≥3 high-quality recipes for this coffee, skip live search entirely |
| **Aggressive caching** | `image_hash → profile` (30d), `coffee_id + equipment → recipe` (24h), `url_hash → extracted_recipe` (30d), `search_query → results` (1h) |
| **Batch embeddings** | Generate embeddings in batch during ingestion, not at query time |
| **Cache embeddings** | Store embeddings in pgvector; recompute only on content change |
| **Structured output** | Use JSON mode to avoid parsing overhead and reduce token waste |
| **Configurable providers** | Switch to cheaper models or local models via config |

---

## 18. Deployment Architecture

### 18.1 Development Environment

```
docker-compose.yml
├── frontend        (Vite dev server, port 3000)
├── backend         (FastAPI + uvicorn, port 8000)
├── postgres        (PostgreSQL 16 + pgvector, port 5432)
├── redis           (Redis 7, port 6379)
├── minio           (S3-compatible storage, port 9000)
└── celery-worker   (Async task processing)
```

### 18.2 Production Architecture

```
┌───────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   CDN         │     │  Load Balancer  │     │  Object Storage  │
│  (CloudFlare) │────▶│  (Cloud LB)     │     │  (Cloud S3)      │
└───────┬───────┘     └────────┬────────┘     └──────────────────┘
        │                      │
        │              ┌───────┴────────┐
        │              │                │
        ▼              ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Frontend    │ │  Backend     │ │  Backend     │
│  (Static     │ │  Instance 1  │ │  Instance 2  │
│   hosting)   │ │  (Container) │ │  (Container) │
└──────────────┘ └──────┬───────┘ └──────┬───────┘
                        │                │
                 ┌──────┴────────────────┴──────┐
                 │                               │
                 ▼                               ▼
          ┌──────────────┐              ┌──────────────┐
          │  PostgreSQL  │              │    Redis     │
          │  (Managed)   │              │  (Managed)   │
          └──────────────┘              └──────────────┘
```

**Deployment options (choose based on scale):**

| Scale | Recommendation |
|---|---|
| Prototype / Hackathon | Single VM + Docker Compose |
| Small production | Google Cloud Run (auto-scaling containers) |
| Medium production | GKE with horizontal pod autoscaling |

---

## 19. Testing Strategy

### 19.1 Test Pyramid

```
           ┌────────┐
           │  E2E   │  Playwright (5-10 critical flows)
          ┌┴────────┴┐
          │Integration│  pytest (API + DB + providers)
         ┌┴──────────┴┐
         │   Unit      │  pytest (services, validators, normalisers)
        ┌┴────────────┴┐
        │  Static       │  mypy, ruff, eslint, Pydantic validation
        └──────────────┘
```

### 19.2 Test Categories

| Category | Scope | Key Tests |
|---|---|---|
| **Extraction** | Vision service | OCR accuracy on test images, missing field handling, non-coffee rejection |
| **Identity** | Normalisation | Process/roast term normalisation, name dedup, ambiguity detection |
| **Live Discovery** | Discovery service | Search query construction, page fetch with timeout, robots.txt compliance, recipe extraction from pages, snippet-vs-page distinction, no-result vs failure distinction, rate limiting |
| **Retrieval** | RAG pipeline | Precision@5, match classification accuracy, irrelevant result rejection, live result merging |
| **Synthesis** | Recipe generator | Arithmetic validation, schema compliance, equipment adaptation correctness |
| **Validation** | Validator | Water total consistency, ratio correctness, temperature bounds |
| **Feedback** | Adjustment engine | Sourness → extraction increase, bitterness → extraction decrease |
| **API** | Endpoints | Request validation, error handling, auth, rate limiting |
| **E2E** | Full pipeline | Image → profile → live discovery → recipe → feedback → adjustment |

### 19.3 Evaluation Dataset

A curated dataset of 20-30 coffee bag images covering:

| Dimension | Coverage |
|---|---|
| **Origins** | India, Ethiopia, Kenya, Colombia, Guatemala, Brazil, Indonesia |
| **Processes** | Washed, natural, honey, anaerobic |
| **Roast levels** | Light, medium-light, medium, dark |
| **Image quality** | Sharp, slightly blurry, angled, partial, low-light |
| **Layouts** | Minimal text, dense text, multi-language, artistic/stylised |
| **Recipe availability** | Exact match available, related only, no match |

Each image has ground-truth annotations for extracted fields, enabling automated accuracy measurement.

---

## 20. Phased Implementation Roadmap

### Phase 1 — Functional MVP (Weeks 1–3)

```
┌───────────────────────────────────────────────────────┐
│  PHASE 1: Core Image-to-Recipe Flow                   │
│                                                       │
│  ✅ Project scaffolding (FastAPI + React + Docker)     │
│  ✅ Image upload endpoint with validation              │
│  ✅ Gemini Vision extraction with structured output    │
│  ✅ Coffee profile schema + editable UI                │
│  ✅ Basic equipment selection (V60, Kalita, Origami)   │
│  ✅ LLM recipe generation (no RAG yet)                 │
│  ✅ Arithmetic validation                              │
│  ✅ Recipe display with step-by-step instructions      │
│  ✅ Mobile-responsive UI                               │
│  ✅ Basic unit + integration tests                     │
│                                                       │
│  Deliverable: A user can photograph a bag and get     │
│  an AI-generated recipe, even without retrieved data. │
└───────────────────────────────────────────────────────┘
```

### Phase 2 — RAG-Based Recipe Discovery (Weeks 4–6)

```
┌───────────────────────────────────────────────────────┐
│  PHASE 2: Knowledge Base + Retrieval                  │
│                                                       │
│  ✅ PostgreSQL + pgvector setup                        │
│  ✅ Recipe source schema + ingestion pipeline          │
│  ✅ Curated dataset: 50-100 real pour-over recipes     │
│  ✅ Embedding generation + vector indexing             │
│  ✅ Hybrid retrieval (FTS + vector)                    │
│  ✅ Match classification (exact/related/analogous)     │
│  ✅ Evidence evaluation before synthesis               │
│  ✅ Source attribution in recipe display               │
│  ✅ Evidence panel UI                                  │
│  ✅ Retrieval quality evaluation metrics               │
│                                                       │
│  Deliverable: Recipes now cite real sources when      │
│  available, with clear match-type labelling.          │
└───────────────────────────────────────────────────────┘
```

### Phase 3 — Inline Live Web Discovery (Weeks 7–9)

```
┌───────────────────────────────────────────────────────┐
│  PHASE 3: Live Search as First-Class Pipeline Step    │
│                                                       │
│  ✅ SearchProvider integration (Google/Tavily)         │
│  ✅ Inline discovery orchestrator (per-scan trigger)   │
│  ✅ Page fetcher with robots.txt & timeout controls    │
│  ✅ LLM-based recipe extraction from fetched pages     │
│  ✅ Snippet ≠ recipe enforcement                       │
│  ✅ Deduplication against existing knowledge base      │
│  ✅ Result merger: live + local KB into unified set     │
│  ✅ Outcome distinction: no results vs search failure  │
│  ✅ Configurable timeouts, rate limits, retry limits    │
│  ✅ Graceful degradation when search unavailable       │
│  ✅ Freshness tracking + stale source management       │
│  ✅ Search result & URL-level caching (Redis)          │
│  ✅ Reranking with cross-encoder                       │
│  ✅ Acceptance test: unindexed coffee triggers live     │
│    search and uses discovered recipes                  │
│  ✅ Expanded evaluation dataset                        │
│                                                       │
│  Deliverable: Given a never-before-seen coffee, the   │
│  system searches the web inline, fetches full pages,  │
│  extracts real recipes, and uses them in its          │
│  recommendation — all within a single scan request.   │
└───────────────────────────────────────────────────────┘
```

### Phase 4 — Personalisation & Iterative Brewing (Weeks 10–12)

```
┌───────────────────────────────────────────────────────┐
│  PHASE 4: User Accounts + Feedback Loop               │
│                                                       │
│  ✅ User authentication (JWT)                          │
│  ✅ Saved equipment profiles                           │
│  ✅ Expanded grinder/dripper catalogue (20+ models)    │
│  ✅ Grinder-specific grind size mapping                │
│  ✅ Brew logging + feedback form                       │
│  ✅ Feedback → adjustment recommendation engine        │
│  ✅ Brew history + recipe comparison view              │
│  ✅ Brew timer with step-by-step pouring guide         │
│  ✅ PWA offline support for saved recipes              │
│  ✅ Comprehensive E2E test suite                       │
│                                                       │
│  Deliverable: Full iterative brewing experience with  │
│  personal equipment, history, and feedback loops.     │
└───────────────────────────────────────────────────────┘
```

---

## 21. Key Architectural Decisions

### ADR-001: Modular Monolith over Microservices

**Decision:** Use a modular monolith (single FastAPI application with internal service modules) rather than separate microservices.

**Rationale:** The team is small, the request volume is moderate, and the services are tightly coupled in the scan-to-recipe pipeline. A modular monolith avoids network overhead, distributed transaction complexity, and deployment complexity while maintaining clean separation of concerns. Services can be extracted later if scaling demands it.

---

### ADR-002: PostgreSQL + pgvector over Dedicated Vector DB

**Decision:** Use PostgreSQL with the pgvector extension rather than a separate vector database (Pinecone, Weaviate, etc.).

**Rationale:** The recipe knowledge base is expected to be in the low thousands of documents. pgvector handles this scale efficiently while keeping the data layer unified — relational data, full-text search, and vector search in one system. This reduces operational complexity and cost.

---

### ADR-003: Versioned Prompt Templates

**Decision:** Store all LLM prompts as versioned Jinja2 templates in the codebase rather than hardcoding them inline.

**Rationale:** Prompts are a critical part of the system's behaviour. Versioning them enables A/B testing, rollback, audit trails, and systematic improvement. Jinja2 allows dynamic injection of coffee profile data, equipment specs, and evidence context.

---

### ADR-004: Server-Sent Events for Pipeline Progress

**Decision:** Use SSE (Server-Sent Events) rather than WebSockets for streaming progress updates during the scan-to-recipe pipeline.

**Rationale:** The communication is unidirectional (server → client), SSE is simpler to implement, works through CDNs and proxies, and auto-reconnects. WebSockets would be overengineered for this use case.

---

### ADR-005: Structured LLM Output with Pydantic Validation

**Decision:** All LLM calls that produce data (extraction, recipe generation) use structured output mode (JSON schema enforcement) and are validated against Pydantic models before being accepted.

**Rationale:** Free-form text output from LLMs is unpredictable. Structured output + validation ensures arithmetic consistency, schema compliance, and eliminates a large class of generation errors. Recipes with invalid water totals or missing fields are caught before reaching the user.

---

### ADR-006: Two-Stage Retrieval (Retrieve then Evaluate)

**Decision:** Retrieval is split into two stages: (1) broad candidate retrieval, (2) evidence evaluation. The system does not pass raw retrieval results directly to the LLM.

**Rationale:** Raw vector search results frequently include tangentially related content, non-recipe documents, or recipes for different brewing methods. The evaluation stage filters, classifies match types, and detects conflicts *before* synthesis, preventing the LLM from being misled by irrelevant context.

---

### ADR-007: Inline Live Discovery over Background-Only Ingestion

**Decision:** Live web discovery runs inline during every scan request (when a SearchProvider is configured), not only as a background administrative ingestion task.

**Rationale:** The core value proposition is helping users with *any* coffee bag, including coffees that have never been pre-indexed. If discovery only runs in batch mode, the system cannot help with new or uncommon coffees on first encounter. Inline discovery ensures that the very first scan of a previously unseen coffee triggers a real web search, fetches full pages (not just snippets), extracts structured recipe data, and feeds it into the recommendation — all within the same request. Strict timeouts and partial-result handling prevent inline discovery from degrading the user experience. The system explicitly distinguishes "no relevant recipes found" from "search failed" so that users are never misled about the state of available evidence.

---

## 22. Appendix

### A. Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://brewwise:password@localhost:5432/brewwise` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `S3_ENDPOINT` | Object storage endpoint | `http://localhost:9000` |
| `S3_BUCKET` | Image storage bucket | `brewwise-images` |
| `S3_ACCESS_KEY` | Object storage access key | — |
| `S3_SECRET_KEY` | Object storage secret key | — |
| `VISION_PROVIDER` | Vision extraction provider | `gemini` |
| `LLM_PROVIDER` | LLM provider for synthesis | `gemini` |
| `LLM_MODEL` | LLM model name | `gemini-2.5-flash` |
| `EMBEDDING_PROVIDER` | Embedding provider | `gemini` |
| `EMBEDDING_MODEL` | Embedding model name | `text-embedding-004` |
| `GOOGLE_API_KEY` | Google AI API key | — |
| `SEARCH_PROVIDER` | Web search provider | `google` |
| `SEARCH_API_KEY` | Search provider API key | — |
| `LIVE_DISCOVERY_ENABLED` | Enable inline live discovery during scans | `true` |
| `LIVE_DISCOVERY_MAX_URLS` | Max URLs to fetch per scan | `5` |
| `LIVE_DISCOVERY_TIMEOUT_SECONDS` | Per-URL fetch timeout | `10` |
| `LIVE_DISCOVERY_TOTAL_TIMEOUT` | Overall discovery time budget per scan | `15` |
| `LIVE_DISCOVERY_PERSIST` | Persist discovered recipes in knowledge base | `true` |
| `LIVE_DISCOVERY_RATE_LIMIT` | Max search API calls per hour | `30` |
| `LIVE_DISCOVERY_RETRY_LIMIT` | Retries per URL on transient failures | `2` |
| `JWT_SECRET` | JWT signing secret | — |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `MAX_UPLOAD_SIZE_MB` | Maximum image upload size | `10` |
| `RATE_LIMIT_SCANS` | Scans per minute per IP | `10` |
| `LOG_LEVEL` | Application log level | `INFO` |

### B. Key Library Dependencies

**Backend (Python):**
```
fastapi>=0.115
uvicorn[standard]
sqlalchemy[asyncio]>=2.0
asyncpg
alembic
pydantic>=2.0
pydantic-settings
redis[hiredis]
celery[redis]
google-genai
pillow
pytesseract
httpx
jinja2
structlog
python-multipart
python-jose[cryptography]
passlib[bcrypt]
boto3
```

**Frontend (Node.js):**
```
react@18
react-dom@18
react-router-dom@6
@tanstack/react-query
zustand
typescript
vite
```

### C. Glossary

| Term | Definition |
|---|---|
| **Pour-over** | A manual coffee brewing method where water is poured over ground coffee in a filter |
| **Bloom** | The initial pour of water that saturates the coffee grounds and releases CO₂ |
| **Drawdown** | The phase where water drains through the coffee bed after all water has been poured |
| **Dose** | The weight of ground coffee used (in grams) |
| **Ratio** | The proportion of coffee to water (e.g., 1:16 means 1g coffee per 16g water) |
| **Extraction** | The process of dissolving soluble compounds from coffee grounds into water |
| **V60** | A conical pour-over dripper made by Hario, known for its spiral ribs and large drain hole |
| **Kalita Wave** | A flat-bottom pour-over dripper with three small drain holes |
| **Channelling** | When water finds paths of least resistance through the coffee bed, causing uneven extraction |
| **RRF** | Reciprocal Rank Fusion — a method for combining ranked lists from different retrieval methods |
| **ANN** | Approximate Nearest Neighbour — efficient similarity search on vector embeddings |
