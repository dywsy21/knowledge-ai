# AI-Native Knowledge Evolution Platform

## 1. Vision

This project is a generic AI-native knowledge evolution platform. It is not tied
to one industry. Any organization can feed the platform with operational
documents, cases, policies, events, training materials, research notes, or public
content. The platform then turns those inputs into structured knowledge,
interactive learning experiences, measurable user behavior, and continuously
improved knowledge assets.

The core idea remains:

```text
Knowledge sources -> AI understanding -> interactive experiences -> user signals
-> evolutionary ranking -> better knowledge products
```

This is not a classic document repository. It is a knowledge ecosystem designed
to select, improve, and distribute useful knowledge through feedback loops.

## 2. Product Positioning

The platform should be built as a general-purpose "knowledge evolution engine"
for enterprises, schools, communities, and expert networks.

Typical domains include:

- Safety training
- Compliance and policy learning
- Technical onboarding
- Case-based education
- Product and customer support knowledge
- Research intelligence
- Professional certification preparation
- Operational incident review

The domain is configurable. A deployment can be maritime, medical operations,
manufacturing, finance, energy, education, legal training, software engineering,
or any other knowledge-intensive field.

## 3. From Knowledge Management to Knowledge Evolution

Traditional systems store knowledge and ask people to search or read it.

This platform treats knowledge as an evolving product:

| Traditional Knowledge System | AI Knowledge Evolution Platform |
| --- | --- |
| Experts write documents | Users and systems provide knowledge sources |
| Platform stores files | AI extracts concepts, rules, risks, timelines, and decisions |
| Users read and take tests | AI generates interactive scenarios and challenges |
| Content is updated manually | User behavior drives ranking, revision, and retirement |
| Value is measured by page views | Value is measured by learning, reuse, completion, and impact |

The system uses Darwinian selection at the content level: useful experiences are
promoted and improved; weak or outdated ones are demoted, revised, or retired.

## 4. Five-Layer Architecture

### 4.1 Knowledge Intake Layer

The intake layer accepts knowledge from many sources:

- Plain text
- Markdown
- PDF
- Word documents
- Web pages
- Images with OCR
- Video or audio transcripts
- API feeds
- Manual notes
- Imported datasets

Each source is normalized into a common `KnowledgeSource` record with metadata:
domain, language, author, source type, trust level, tags, and lifecycle state.

### 4.2 Knowledge Intelligence Layer

The intelligence layer extracts useful structure from raw content.

Core capabilities:

- Entity extraction
- Concept extraction
- Rule and policy extraction
- Cause-and-effect extraction
- Risk and control identification
- Timeline extraction
- Procedure and checklist extraction
- Difficulty estimation
- Knowledge value assessment
- Duplicate and contradiction detection

The output is a structured knowledge graph and a set of reusable knowledge units.
The first implementation can use deterministic heuristics plus LLM calls. Later
versions can add vector retrieval, graph storage, and domain-specific ontologies.

### 4.3 Interaction Generation Layer

The platform does not simply create quizzes. It maps knowledge units to reusable
interactive templates.

Initial templates:

- Decision scenario
- Defect or anomaly spotting
- Incident reconstruction
- Process ordering
- Simulation-lite resource allocation
- Risk triage
- Role-based dialogue
- Flash review
- Certification drill

Each generated experience stores:

- Source knowledge references
- Learning objective
- Game or interaction template
- Rules
- Scoring model
- Feedback text
- Expected misconceptions
- Difficulty level
- Version lineage

### 4.4 Evolution Layer

The evolution layer ranks and improves generated experiences using signals.

Signals include:

- Completion rate
- Time on task
- Replay rate
- Share rate
- Like or bookmark rate
- Error distribution
- Learning gain
- User confidence delta
- Expert review score
- Reported issue count
- Recency and source trust

Poor performers are hidden, revised, or retired. Strong performers are promoted,
translated, remixed, or used as parents for new variants.

### 4.5 User Growth Layer

The user layer turns learning into a visible progression system:

- Points
- Skill levels
- Badges
- Domain certifications
- Team rankings
- Cohort progress
- Weakness maps
- Personalized recommendations

The goal is not shallow gamification. The goal is to make knowledge practice
frequent, measurable, and socially reinforced.

## 5. AI Architecture

AI must be isolated behind a harness. Business code should not directly call a
model SDK. This keeps the system testable, auditable, and provider-agnostic.

### 5.1 Library Strategy

The recommended default is:

- LiteLLM for unified access to OpenAI, Anthropic, Google, Azure, Bedrock,
  Ollama, OpenRouter, and other OpenAI-compatible providers.
- Pydantic for strict input and output schemas.
- A local mock provider for tests, demos, and offline development.
- LlamaIndex as the optional future RAG/indexing layer.
- LangChain or LangGraph only when the platform needs complex multi-step
  agentic orchestration.

This project should keep its own small harness even when using these libraries.
External libraries solve provider access and orchestration; the harness defines
the platform contract, trace records, task names, fallback behavior, and schema
validation.

### 5.2 AI Harness Responsibilities

The harness owns:

- Provider selection
- Prompt assembly
- Model settings
- Structured output validation
- Retry policy
- Timeout policy
- Fallback policy
- Cost and token metadata
- Prompt and response logging
- Evaluation fixtures
- Deterministic test mode
- Safety checks before generated content is published

The harness exposes task-level methods instead of generic chat calls:

- `extract_knowledge_units`
- `assess_knowledge_value`
- `generate_interaction`
- `review_interaction`
- `recommend_next_items`
- `summarize_learning_signals`

### 5.3 Provider Contract

Every AI provider must implement one simple contract:

```text
generate_json(task, messages, response_schema, settings) -> AIResult
```

This makes it possible to use LiteLLM, direct SDKs, local models, hosted gateway
services, or deterministic mocks without changing domain services.

### 5.4 Testing Harness

AI code is tested at three levels:

1. Contract tests: every provider returns an `AIResult` and handles errors in a
   consistent format.
2. Schema tests: generated outputs validate against Pydantic models.
3. Golden tests: known inputs produce stable mock outputs for CI.

Live model tests should be opt-in and skipped unless API keys are configured.

## 6. Backend Plan

The backend is a Python FastAPI service.

Main modules:

- `app.api`: HTTP endpoints
- `app.core`: configuration, logging, database setup
- `app.ai`: AI harness, providers, prompts, schemas, evaluations
- `app.knowledge`: source ingestion and knowledge unit management
- `app.interactions`: generated scenarios, games, reviews, publishing
- `app.evolution`: signal collection, ranking, retirement, variant generation
- `app.users`: profiles, progress, achievements, teams

Initial storage can use SQLite for local development. The production path should
support PostgreSQL, object storage, vector search, and graph storage.

## 7. Frontend Plan

The frontend is a Vue application focused on operational workflows, not a
marketing page.

Primary screens:

- Knowledge intake workspace
- Source detail and extraction review
- Knowledge graph explorer
- Interaction studio
- Generated experience player
- Evolution dashboard
- User progress dashboard
- Admin settings for domains, models, templates, and review policies

The UI should be dense, clear, and work-oriented. Cards should be used only for
repeated items, modals, and specific tools. The first screen should be the usable
workspace.

## 8. MVP Scope

The MVP should include:

- Create and list knowledge sources
- Extract structured knowledge units from text
- Generate an interaction from selected knowledge units
- Play or preview the interaction
- Submit completion and quality signals
- Rank interactions using evolution signals
- Show user progress
- Use mock AI by default and LiteLLM when configured

## 9. Implementation Phases

| Phase | Goal | Capabilities |
| --- | --- | --- |
| 1. MVP | Prove the loop | Text intake, extraction, template generation, user feedback, ranking |
| 2. Intelligence | Improve quality | RAG, embeddings, review workflows, knowledge graph, recommendations |
| 3. Agent Operations | Automate operation | Source monitoring, scheduled generation, automatic revision, retirement |
| 4. Autonomous Ecosystem | Self-improving platform | Multi-agent content operations, continuous evals, domain marketplace |

## 10. Strategic Value

The platform changes knowledge distribution from:

```text
Document -> training -> test
```

to:

```text
Event or source -> interaction -> feedback -> evolution -> improved knowledge
```

The long-term value is a reusable engine for making expert knowledge easier to
practice, measure, improve, and spread.

## 11. Local Implementation

This repository contains a working full-chain MVP:

- Python FastAPI backend in `backend/`
- Vue 3 frontend in `frontend/`
- AI harness with mock and LiteLLM providers
- In-memory platform store for sources, extracted units, generated
  interactions, feedback signals, and evolution ranking

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8800
```

Useful endpoints:

- `GET /health`
- `GET /summary`
- `POST /full-chain`
- `POST /feedback`
- `GET /sources`
- `GET /interactions`

LLM access is managed through `.env` in the repository root. Copy
`.env.example` when creating a new environment.

The current default is an OpenAI-compatible local endpoint through LiteLLM:

```bash
KNOWLEDGE_AI_PROVIDER=litellm
KNOWLEDGE_AI_MODEL=openai/mlx-qwen3.5-35b-a3b-claude-4.6-opus-reasoning-distilled
KNOWLEDGE_AI_API_BASE=http://192.168.1.106:1234/v1
KNOWLEDGE_AI_API_KEY=not-needed
```

For deterministic offline behavior:

```bash
KNOWLEDGE_AI_PROVIDER=mock
KNOWLEDGE_AI_MODEL=mock/local
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://127.0.0.1:8800`. Override it with:

```bash
set VITE_API_BASE=http://127.0.0.1:8800
```

### Verification

```bash
cd backend
python -m pytest -q -s

cd ../frontend
npm run build
```

### Docker

```bash
docker compose up -d --build
```

The compose stack exposes the frontend on `127.0.0.1:18880`. The frontend NGINX
container proxies `/api/*` to the backend container.
