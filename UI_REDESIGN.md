# SahayaKSetu — System Upgrade & Production Readiness Plan

## Overview
This document defines a **full-stack upgrade plan** covering:
1. Frontend migration to latest React
2. UI/UX redesign via structured AI prompts
3. Backend audit + production hardening
4. LLM provider consolidation to OpenRouter

---

# 1) Frontend Migration → Latest React

## Target
- React 19 (latest stable)
- Vite (build tool)
- TypeScript (strict mode)
- Tailwind CSS + shadcn/ui

## Actions

### Core Migration
- Upgrade:
  - `react@19`, `react-dom@19`
  - `vite@latest`
  - `typescript@5.6+`
- Enable:
  - React Query (for data fetching + caching)
  - React Router v7 (client-side routing)
  - Fast Refresh (HMR)

### State Management
- Use:
  - React Query (for server state)
  - Zustand or Jotai (for client state)
  - Context API (for lightweight props passing)
- Remove:
  - Redux (if present)
  - unnecessary global state

### Folder Structure
```
/app
/api
/components
/features
/lib
/hooks
/types
```

### Performance
- Vite optimizations:
  - Code splitting via dynamic imports
  - CSS minification
  - Asset optimization
- React optimizations:
  - Lazy load components (React.lazy)
  - Memoization (React.memo, useMemo, useCallback)
  - Suspense boundaries for async components
- Monitoring:
  - Web Vitals (LCP, FID, CLS)
  - Bundle size tracking

---

# 2) AI Prompt System (Split into 3 Parts)

---

## PART I — UI/UX Migration + Upgrade Prompt

### Objective
Transform UI from landing-page style → **tool-first, production-grade interface**

### Technical Stack
- React 19 with Vite
- TypeScript (strict mode)
- Tailwind CSS 4
- shadcn/ui components
- React Router v7 for navigation
- React Query for data fetching
- Web Speech API + Howler.js for voice
- zustand for state management

### File Structure
```
src/
  ├── components/
  │   ├── SearchInput.tsx
  │   ├── SchemeCard.tsx
  │   ├── VoiceInput.tsx
  │   ├── ResultsPanel.tsx
  │   ├── EvidencePanel.tsx
  │   ├── LanguageSwitcher.tsx
  │   └── shared/
  │       ├── Header.tsx
  │       ├── Footer.tsx
  │       └── ErrorBoundary.tsx
  ├── hooks/
  │   ├── useVoice.ts
  │   ├── useSearch.ts
  │   ├── useLanguage.ts
  │   └── useSpeech.ts
  ├── types/
  │   ├── scheme.ts
  │   ├── api.ts
  │   └── voice.ts
  ├── pages/
  │   ├── SearchPage.tsx
  │   ├── ResultsPage.tsx
  │   └── NotFound.tsx
  ├── store/
  │   └── appStore.ts
  └── App.tsx
```

### Component Specifications

#### SearchInput Component
```typescript
interface SearchInputProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  placeholder?: string;
}
```
- Input bar with search icon
- Voice activation button
- Query history dropdown
- Suggested queries below input
- Accessibility: ARIA labels, keyboard navigation

#### VoiceInput Component
```typescript
interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onError: (error: string) => void;
  isListening: boolean;
}

interface VoiceState {
  idle: { icon: string; text: string };
  listening: { waveform: true; color: string };
  processing: { spinner: true };
  speaking: { waveform: true; wave.js visualization };
}
```
- Real-time waveform visualization
- Transcript display
- Confidence indicator
- Language detection display
- Stop/cancel buttons

#### SchemeCard Component
```typescript
interface SchemeCardProps {
  scheme: {
    id: string;
    name: string;
    ministry: string;
    description: string;
    eligibility: string[];
    benefits: string[];
    applicationUrl: string;
    matchScore: number;
  };
  onSelect: () => void;
}
```
- Card layout with scheme name, ministry
- Match score badge (percentage)
- Eligibility summary (first 2 bullet points)
- "View Details" expandable section
- Apply button with direct link
- Responsive grid: 1 col (mobile), 2 cols (tablet), 3 cols (desktop)

#### LanguageSwitcher Component
- Supported languages: EN, HI, TA, TE, KN, ML, GU, MA
- Layout adapter: RTL support for Arabic/Persian (if adding)
- Font loading per language (noto-sans-* families)
- Persistent in localStorage
- Broadcast change to all components via context

### Prompt
```
Build the complete UI/UX for an AI-powered government scheme discovery platform using React 19 + Vite + TypeScript.

TECHNICAL CONTEXT:
- Stack: React 19, Vite, TypeScript 5.6+, Tailwind CSS 4, shadcn/ui
- Package.json dependencies:
  * react@19, react-dom@19
  * vite@latest, typescript@5.6+
  * react-router-dom@7, @tanstack/react-query@5
  * zustand@4
  * tailwindcss@4, @shadcn/ui/*
  * howler@2.2 (for audio)
  * date-fns (for formatting)
- Dev tools: ESLint (with @typescript-eslint), Prettier, Vitest
- Build target: Modern browsers (ES2020+)

PLATFORM CONTEXT:
- Use case: Indian citizens discovering government schemes
- Primary device: Mobile first (70% traffic)
- Primary interaction: Voice search
- Multilingual: 8 languages (EN, HI, TA, TE, KN, ML, GU, MA)
- Accessibility: WCAG 2.1 AA minimum
- Performance: LCP < 2.5s, FID < 100ms, CLS < 0.1

Step 1: Audit & Plan

* Document existing UI:
  - List all pages/components
  - Identify every friction point (forms, unclear buttons, slow interactions)
  - Flag all marketing/landing-page elements for removal
  
* Plan new architecture:
  - User flow: lands → sees search → types/speaks → sees results → applies
  - No intermediate pages, no chat history, no breadcrumbs
  - Single source of truth for schemes data

Step 2: Implement Core Components (TypeScript)

* SearchInput.tsx
  - Props: onSearch(query), isLoading, placeholder, suggestedQueries
  - Render: input + search icon + voice button
  - Behavior:
    * On Enter: call onSearch(value)
    * On blur: optionally save to history
    * Placeholder: localized per language
  - Mobile: full width, 48px min height (touch target)
  - Accessibility: aria-label, aria-describedby for errors

* VoiceInput.tsx (custom hook: useVoice)
  - Props: onTranscript(text), onError(msg), language
  - States (visual + behavioral):
    * idle: mic outline, clickable, text "Tap to speak"
    * listening: animated waveform, bars, "Listening..." + partial transcript
    * processing: spinner, "Processing..."
    * speaking: speaker icon, "Playing..." + waveform reflecting audio
  - Implementation:
    * Use Web Speech API (SpeechRecognition)
    * Fallback: if not supported, show message + text-only search
    * Real-time PCM visualization via Web Audio API (10-20 bars)
    * Auto-stop after 10 seconds silence
  - Error handling:
    * no-speech → "Didn't catch that, try again"
    * network-error → "Connection lost"
    * permission-denied → "Microphone not allowed"

* SchemeCard.tsx
  - Props: scheme (full object), onSelect, isLoading
  - Render:
    * Header: logo/icon + name (bold) + ministry (gray)
    * Match score: badge with % (e.g., 95% match)
    * Summary: eligibility (2 bullets) + first 20 chars of description
    * Actions: "View Details" (expandable) + "Apply Now" (link to scheme URL)
  - Expand state:
    * Full description
    * All eligibility criteria (numbered list)
    * All benefits (bulleted)
    * Required documents (if available)
    * Link to official scheme page
  - Responsive:
    * Mobile: full width, stacked cards
    * Tablet (640px+): 2-column grid
    * Desktop (1024px+): 3-column grid
  - Accessibility:
    * Semantic HTML (article > header > h3, main > section)
    * Focus outline visible
    * Expandable marked as role="region" aria-expanded

* ResultsPanel.tsx
  - Props: results[], isLoading, isEmpty, error
  - Render: grid of SchemeCards
  - States:
    * Loading: show 3 skeleton cards (use Skeleton from shadcn/ui)
    * Empty: "No schemes match '{query}'. Try different keywords."
    * Error: "Search failed. Please try again." + Retry button
  - Pagination: "Load More" button (not infinite scroll — reduces memory)
  - Count: "Found {count} schemes"

* LanguageSwitcher.tsx
  - Props: currentLanguage, onLanguageChange
  - Render: 8 pill buttons (EN, हिन्दी, தமிழ், etc.)
  - Behavior:
    * On click: call onLanguageChange(lang)
    * Persist to localStorage['language']
    * Reload page OR use i18n library to swap strings in-memory
  - Font loading: link Noto Sans variants in HTML head (one per language)
  - RTL: if adding RTL languages, toggle dir="rtl" on <html>

* EvidencePanel.tsx (optional, shown when user taps "Why this match?")
  - Props: scheme, snippet
  - Render:
    * Snippet: highlighted excerpt from scheme description (why it matched)
    * Source: "From official {ministry} website"
    * Share: copy-to-clipboard button

Step 3: Hooks & State Management (zustand)

* useVoice.ts
  - State: isListening, transcript, confidence, error
  - Methods: start(), stop(), getPermission()
  - Returns: { isListening, transcript, start, stop, error }

* useSearch.ts
  - Uses React Query to call /api/search endpoint
  - State: results[], isLoading, error
  - Returns: { results, isLoading, error, search(query) }

* useLanguage.ts
  - State: currentLanguage
  - Methods: setLanguage(lang), loadTranslations()
  - Returns: { language, setLanguage, t(key) } for i18n

* appStore.ts (zustand)
  - State: { searchQuery, results, selectedScheme, language, voiceEnabled }
  - Actions: { setQuery, setResults, selectScheme, setLanguage, toggleVoice }

Step 4: API Types (TypeScript)

```typescript
// types/scheme.ts
export interface Scheme {
  id: string;
  name: string;
  ministry: string;
  description: string;
  eligibility: string[];
  benefits: string[];
  applicationUrl: string;
  matchScore: number;
  documents?: string[];
}

// types/api.ts
export interface SearchRequest {
  query: string;
  language: string;
}

export interface SearchResponse {
  schemes: Scheme[];
  total: number;
  query: string;
}

export interface ErrorResponse {
  error: string;
  code: string;
  timestamp: string;
}
```

Step 5: Pages & Routing

* SearchPage.tsx
  - Layout: centered SearchInput at top + LanguageSwitcher in header
  - Below: suggested queries (3 examples in user's language)
  - On search: navigate to /results?q={query}

* ResultsPage.tsx
  - Layout: header with back button + SearchInput (sticky on scroll) + LanguageSwitcher
  - Main: ResultsPanel (grid of cards)
  - On card select: show EvidencePanel in modal/drawer

* App.tsx / Router setup
  - Routes: / → SearchPage, /results → ResultsPage
  - Error boundary wrapping all routes
  - Loading provider (React Query)

Step 6: Styling & Design Tokens

* Tailwind config:
  - Extend colors: primary-600 (government blue), success-500, warning-500, error-500
  - Spacing: use 4px base unit consistently
  - Fonts: inter for EN, noto-sans-{lang} for other languages
  - Dark mode: prefers-color-scheme media query

* Component styling:
  - SearchInput: bg-white, border-gray-200, focus:ring-2 ring-primary-500
  - SchemeCard: shadow-md, hover:shadow-lg, border-l-4 border-primary-600 (left accent)
  - VoiceButton: size 56px (mobile), animated pulse when idle
  - Results grid: gap-4, responsive columns

Step 7: Performance & Accessibility

* Code splitting:
  - Use React.lazy for ResultsPage, LanguageSwitcher
  - Suspense boundary with Skeleton loader

* Optimization:
  - Memoize SearchInput, SchemeCard with React.memo
  - useCallback for event handlers
  - useMemo for computed results filtering
  - Lazy-load fonts (font-display: swap)

* Accessibility (WCAG 2.1 AA):
  - All inputs have <label> or aria-label
  - Focus visible on all interactive elements
  - Color contrast: 4.5:1 for text
  - Keyboard navigation: Tab through all, Enter to submit, Escape to close modals
  - Screen reader: aria-live regions for status updates ("Searching...", "Found 5 schemes")
  - Images: alt text or aria-hidden if decorative
  - Language: lang attribute on <html>, lang prop passed to components

* Testing:
  - Write Vitest unit tests for SearchInput, SchemeCard, useSearch hook
  - Integration test: search → results display
  - Test voice fallback (no Web Speech API)
  - Test i18n language switching
  - Test mobile responsiveness

Step 8: Output

Deliver:
* All .tsx component files (fully typed, production-ready)
* /hooks/*.ts with error handling
* /types/*.ts with full type safety
* /pages/*.tsx with routing
* /store/appStore.ts with zustand setup
* tailwind.config.js with design tokens
* Main App.tsx with router + providers
* README.md with setup instructions
* Example .env.local variables
* Accessibility checklist (WCAG mapping)
* Performance metrics targets

Constraints:

* Zero placeholders — all code runnable
* Every component must be fully typed (no 'any')
* Every event must have error handling
* UI must be responsive (test at 375px, 768px, 1280px viewports)
* No external API calls in components — use custom hooks
* No inline styles — use Tailwind + shadcn/ui only
* Keyboard + voice + touch all equally functional
* Language switch must be seamless (no page reload if possible)
* Production-ready: minified, optimized, deployed to Vercel or similar

```

---

## PART II — Backend Audit + Production Hardening Prompt

### Objective
Ensure backend is **scalable, reliable, test-covered, production-ready**

### Technical Stack
- Runtime: Node.js 20+ or Python 3.11+
- Framework: Express.js (Node) or FastAPI (Python)
- Database: PostgreSQL (relational) + Redis (cache)
- ORM: Prisma (Node) or SQLAlchemy (Python)
- Testing: Jest/Vitest (Node) or pytest (Python)
- API Docs: OpenAPI/Swagger
- Container: Docker + docker-compose
- Logging: Winston (Node) or Python logging
- Monitoring: Sentry or similar

### Expected APIs
```
GET /api/schemes                    # List all schemes (paginated)
POST /api/search                    # Search schemes by query
GET /api/schemes/{id}              # Get single scheme details
POST /api/schemes/{id}/apply       # Track application (optional)
POST /api/voice/transcribe         # Voice-to-text via external API
GET /api/health                    # Health check
POST /api/feedback                 # User feedback
```

### Database Schema
```sql
-- schemes table
CREATE TABLE schemes (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  ministry VARCHAR(255),
  description TEXT,
  eligibility_criteria TEXT[],
  benefits TEXT[],
  application_url VARCHAR(512),
  embedding VECTOR(1536),  -- for RAG similarity
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- search_cache table
CREATE TABLE search_cache (
  id UUID PRIMARY KEY,
  query_hash VARCHAR(255) UNIQUE,
  results JSONB,
  ttl_expires_at TIMESTAMP,
  hit_count INT DEFAULT 0
);

-- request_log table (for observability)
CREATE TABLE request_logs (
  id UUID PRIMARY KEY,
  method VARCHAR(10),
  endpoint VARCHAR(255),
  status_code INT,
  response_time_ms INT,
  user_id VARCHAR(255),
  created_at TIMESTAMP
);
```

### Prompt
```
Perform a complete production-grade audit and hardening of an AI-powered RAG backend system.

TECHNICAL CONTEXT:
- Node.js 20+ with Express OR Python 3.11+ with FastAPI
- Database: PostgreSQL + Redis
- ORM: Prisma (Node) or SQLAlchemy (Python)
- Testing: Jest/Vitest (Node) or pytest (Python)
- Package management: npm or pip
- Environment: .env file for secrets (DATABASE_URL, OPENROUTER_API_KEY, REDIS_URL, etc.)
- Build: docker build -t sahaya:latest .
- Run: docker run -p 3000:3000 --env-file .env sahaya:latest

PLATFORM CONTEXT:
- System: RAG pipeline (Retrieval-Augmented Generation)
- Input: user query (text or transcribed voice)
- Process:
  1. Query embedding via OpenRouter
  2. Vector similarity search in PostgreSQL
  3. Retrieve top-3 schemes
  4. Generate response via OpenRouter LLM
  5. Cache result for 24 hours
- Output: JSON { schemes: [...], message: "..." }
- Scale: 10k-100k daily queries, <500ms response time target

Step 1: Architecture Review

* Validate current API structure:
  - Are all endpoints RESTful?
  - Do they follow consistent naming? (/api/v1/... prefix?)
  - Are there clear separation of concerns? (routes, controllers, services, models)
  - Folder structure:
    * /src/routes or /app/routers
    * /src/controllers or /app/handlers
    * /src/services or /app/services
    * /src/db or /app/models
    * /src/middleware
    * /src/utils
    * /tests
  - Middleware stack clear? (auth, logging, error handling)
  
* Service boundaries:
  - Is RAG logic isolated in a service class?
  - Is embeddings logic isolated?
  - Are database queries in models/DAOs, not in controllers?
  - Is config management centralized? (DATABASE_URL from env, not hardcoded)
  
* Scalability review:
  - Are queries indexed properly? (CREATE INDEX on schemes(embedding) using IVFFLAT)
  - Is connection pooling configured? (max: 20, idle: 5)
  - Is caching implemented? (Redis or in-memory)
  - Can the system run horizontally? (stateless, no file uploads to local disk)

Step 2: API Validation

For EVERY API endpoint:

* Document the contract:
  ```
  POST /api/search
  Request:
    {
      "query": "string (required, min 3 chars, max 500)",
      "language": "string (default: 'en', enum: ['en', 'hi', 'ta', ...])"
    }
  Response (200):
    {
      "schemes": [
        {
          "id": "uuid",
          "name": "string",
          "matchScore": "number (0-100)",
          ...
        }
      ],
      "total": "number",
      "query": "string"
    }
  Response (400):
    {
      "error": "Invalid query length",
      "code": "INVALID_INPUT",
      "timestamp": "ISO 8601"
    }
  Response (500):
    {
      "error": "Internal server error",
      "code": "SERVER_ERROR",
      "timestamp": "ISO 8601"
    }
  ```

* Validation: strict input checks
  - query: required, string, 3-500 chars, trim whitespace, no SQL injection
  - language: required, enum, lowercase
  - Add schema validation via Zod (Node) or Pydantic (Python)

* Error handling: all errors must return consistent format
  - 400 Bad Request: validation failed
  - 401 Unauthorized: auth needed
  - 403 Forbidden: user doesn't have permission
  - 404 Not Found: resource not found
  - 429 Too Many Requests: rate limited
  - 500 Internal Server Error: unhandled exception
  - All errors: { error: string, code: string, timestamp: ISO8601 }

* Rate limiting:
  - Implement rate limiting: 100 requests/minute per IP (or per user if auth)
  - Use redis-rate-limit or similar library
  - Return 429 with Retry-After header

* CORS:
  - Enable CORS only for frontend domain (not *)
  - Origins: [ "https://sahaya.example.com", "http://localhost:3000" ]

* Logging: every request must be logged
  - Log: method, endpoint, status_code, response_time_ms, user_id
  - Store in request_logs table or external service (Sentry)

Step 3: Testing (Comprehensive)

* Unit tests (test individual functions):
  - Mock external dependencies (OpenRouter API, database)
  - Test schema validation (valid input, invalid input, edge cases)
  - Test error handling (what happens on API error? On timeout?)
  - Use Jest (Node) or pytest (Python)
  - Example test:
    ```
    describe('searchSchemes', () => {
      it('returns schemes matching query', async () => {
        const result = await searchSchemes('education')
        expect(result.schemes.length).toBeGreaterThan(0)
        expect(result.schemes[0]).toHaveProperty('matchScore')
      })
      
      it('rejects query < 3 chars', async () => {
        expect(() => searchSchemes('ab')).toThrow('Query too short')
      })
      
      it('returns empty array if no match', async () => {
        const result = await searchSchemes('xyz123abc')
        expect(result.schemes).toEqual([])
      })
    })
    ```

* Integration tests (test API endpoints end-to-end):
  - Use test database (separate from production)
  - Create sample schemes, then search
  - Test full request/response flow
  - Example:
    ```
    test('POST /api/search returns valid response', async () => {
      const response = await request(app)
        .post('/api/search')
        .send({ query: 'education', language: 'en' })
      
      expect(response.status).toBe(200)
      expect(response.body).toHaveProperty('schemes')
      expect(Array.isArray(response.body.schemes)).toBe(true)
    })
    
    test('POST /api/search returns 400 on invalid input', async () => {
      const response = await request(app)
        .post('/api/search')
        .send({ query: 'ab' })
      
      expect(response.status).toBe(400)
      expect(response.body.code).toBe('INVALID_INPUT')
    })
    ```

* RAG pipeline tests:
  - Test embedding quality: do embeddings cluster correctly?
  - Test retrieval: given a query, are the top-3 results relevant?
  - Test caching: is result served from cache on duplicate query?
  - Test fallback: if embedding API fails, does system gracefully degrade?

* Load tests (using k6 or Artillery):
  - Simulate 100 concurrent users searching
  - Ensure response time < 500ms at 95th percentile
  - Monitor database connection pool (should not exceed max)
  - Monitor memory usage (should not spike)

* Security tests:
  - SQL injection: try query = "'; DROP TABLE schemes; --"
  - XSS: try query with <script> tags
  - Rate limiting: send 200 requests in 1 minute, expect 429 after threshold

Step 4: RAG Pipeline Validation

* Embedding quality:
  - Document which embedding model is used (e.g., "text-embedding-3-small" via OpenRouter)
  - Test: given scheme title, can it find the same scheme via embedding similarity?
  - Threshold: cosine similarity > 0.7 for matching
  - Chunk strategy: are schemes chunked into sections? Or whole document?

* Retrieval accuracy:
  - Manual test: search for "education loan" → expect schemes about education
  - Measure: precision (are results relevant?) + recall (are all relevant schemes found?)
  - Log queries + results for later analysis

* Latency + cost:
  - Measure current latency per query (embedding + retrieval + LLM generation)
  - Measure cost per query (API calls to OpenRouter)
  - Goal: < 2 API calls per query, < $0.001 per query
  - Optimization: cache frequent queries, re-rank results locally if needed

Step 5: Security Hardening

* Authentication (if user accounts exist):
  - Use JWT tokens (signed, 1 hour expiry)
  - Refresh tokens (signed, 7 day expiry)
  - Hash passwords: bcrypt (Node) or werkzeug (Python)

* Input sanitization:
  - Validate all inputs against schema
  - Escape special characters in logs (prevent log injection)
  - Sanitize error messages (don't leak internal details)

* Data protection:
  - All data over HTTPS (TLS 1.3)
  - Database credentials in environment variables (never in code)
  - Sensitive data: encrypt in transit + at rest
  - Audit logs: track who accessed what

* API key management (for OpenRouter, etc.):
  - Store in environment variables (.env file, not git)
  - Rotate keys quarterly
  - Log API usage (separate from user queries, for cost tracking)
  - If key is exposed, revoke immediately

* CORS + CSP:
  - Content-Security-Policy headers
  - X-Frame-Options: DENY (prevent clickjacking)
  - X-Content-Type-Options: nosniff

Step 6: Observability

* Logging:
  - Log levels: DEBUG, INFO, WARN, ERROR
  - Log every request: method, endpoint, status, response_time_ms, user_id
  - Log errors with full stack trace
  - Store logs: file system OR external service (Sentry, DataDog)
  - Example:
    ```
    logger.info('Search request', { query, language, userId, responseTimeMs: 245 })
    logger.error('API error', { endpoint: '/api/search', error: err.message, stack: err.stack })
    ```

* Metrics:
  - Response time per endpoint (histogram)
  - Request count per endpoint (counter)
  - Error rate (percentage of 5xx responses)
  - Cache hit rate (percentage of requests served from cache)
  - Database query time (average, p99)
  - External API latency (embedding, LLM)

* Error tracking:
  - Catch all unhandled exceptions → log + alert
  - Track error frequency + trends
  - Set up alerts: if error rate > 5% for 5 minutes, notify ops team

* Distributed tracing (optional):
  - Trace a single request through the system
  - See: request → embedding API call → database query → LLM API call → response
  - Use OpenTelemetry or similar

Step 7: Production Readiness

* Dockerfile:
  ```dockerfile
  FROM node:20-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci
  COPY . .
  RUN npm run build
  EXPOSE 3000
  CMD ["npm", "start"]
  ```

* docker-compose.yml:
  ```yaml
  version: '3.8'
  services:
    api:
      build: .
      ports:
        - "3000:3000"
      environment:
        DATABASE_URL: postgresql://user:pass@db:5432/sahaya
        REDIS_URL: redis://redis:6379
        OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      depends_on:
        - db
        - redis
    db:
      image: postgres:16-alpine
      environment:
        POSTGRES_DB: sahaya
        POSTGRES_USER: user
        POSTGRES_PASSWORD: pass
      volumes:
        - db_data:/var/lib/postgresql/data
    redis:
      image: redis:7-alpine
  volumes:
    db_data:
  ```

* Environment config:
  - .env.example (checked in, lists all required variables)
  - .env.local (git-ignored, actual values)
  - .env.production (for prod deployment)

* Startup checks:
  - Database connectivity: try connection on startup, fail if down
  - Redis connectivity: check on startup
  - API key validity: try single call to OpenRouter on startup
  - If any critical service unavailable, don't start, log error

* Horizontal scalability:
  - No local file storage (use cloud storage if needed)
  - No in-memory caches (use Redis)
  - All state in database or Redis
  - Can run multiple instances behind load balancer

* Deployment:
  - CI/CD pipeline (GitHub Actions, GitLab CI, etc.):
    1. Run tests: npm test
    2. Build: npm run build
    3. Docker build + push
    4. Deploy to prod (e.g., AWS ECS, Heroku, Railway)
  - Health check endpoint: GET /api/health → { status: 'ok' }

Step 8: Output

Deliver:
* Fully tested API with Jest/pytest
* API documentation (Swagger/OpenAPI spec)
* Database schema + migration scripts
* docker-compose.yml for local development
* Production Dockerfile
* .env.example with all required variables
* Error handling guide (error codes + causes)
* Security checklist (passed/failed each item)
* Performance benchmarks (latency, throughput, cost per query)
* Monitoring dashboard config (Sentry, DataDog, or similar)
* Deployment guide (how to run in production)
* README with setup instructions

Constraints:

* Zero skipped tests — every API must pass tests
* Every function must have error handling (try/catch, async/await)
* No hardcoded secrets or API keys
* All responses consistent format
* Database queries must use ORM (no raw SQL except migrations)
* All user inputs validated + sanitized
* All errors logged with context
* System must handle 100 concurrent requests gracefully
* Must be deployable via Docker
* Must include observability (logging, metrics, tracing)
* Production-ready: no warnings, no console.logs, no TODOs

```

---

## PART III — LLM Migration to OpenRouter

### Objective
Replace Gemini + Groq → **single OpenRouter key with cost & quality optimization**

### Current State Assessment
- Identify all LLM calls in codebase (grep: "Gemini", "Groq", "LLM", "generate", "completion")
- Document: which task uses which provider (e.g., query understanding → Groq, summarization → Gemini)
- Measure: current cost, latency, quality metrics
- Find: all hardcoded API keys, remove them

### Target State
- Single OpenRouter API key
- 3-5 model options (cheap small models for most tasks, one larger model for complex cases)
- Cost target: < $1 per 1000 user queries
- Latency target: < 300ms per API call (including network)
- Quality: maintain or improve current output accuracy

### Prompt
```
Migrate all LLM integrations from Gemini + Groq to OpenRouter, optimizing for cost, speed, and quality.

TECHNICAL CONTEXT:
- OpenRouter API: https://openrouter.ai/api/v1/chat/completions
- Authentication: Bearer token in Authorization header
- Single API endpoint for all models (no provider-specific logic)
- Supports 200+ models (proprietary + open-source)
- Billing: per 1M tokens, varies by model
- Rate limits: depends on subscription tier

AVAILABLE MODELS ON OPENROUTER (recommend these):
* Query understanding: meta-llama/llama-2-7b-chat (fast, cheap, <1ms)
* Summarization: mistral/mistral-7b (balanced, good quality)
* RAG answer generation: meta-llama/llama-2-13b-chat (higher quality)
* Fallback: qwen/qwen-14b-chat (diverse output, different perspective if first fails)

MIGRATION CONTEXT:
- System: government scheme discovery via RAG
- Current flow: Gemini (embedding + understanding) + Groq (generation)
- New flow: OpenRouter (all tasks)
- Do NOT break user queries during migration
- Test thoroughly before switch-over

Step 1: Audit Current Usage

* Find ALL LLM calls:
  - Grep codebase for: "gemini", "groq", "openai", "llm", "model", "chat", "complete"
  - Document each call:
    * File + line number
    * Task (query understanding, summarization, generation, etc.)
    * Current provider + model
    * Frequency (how many times per day?)
    * Cost (if logged)
    * Latency (if logged)
    * Output quality (manual assessment)

* Remove hardcoded credentials:
  - List all hardcoded API keys: gemini_key, groq_key, etc.
  - Move to environment: GEMINI_API_KEY → (delete), GROQ_API_KEY → (delete)
  - Add: OPENROUTER_API_KEY (new)

* Measure baseline:
  - Current daily cost (sum of all provider costs)
  - Current average latency per LLM call
  - Error rate (how often does LLM call fail?)

Step 2: Replace Provider Integrations

* Remove Gemini library:
  - If using google-generativeai npm package: npm uninstall google-generativeai
  - Delete all Gemini client initialization code
  - Find all gemini.generate() calls, mark for replacement

* Remove Groq library:
  - If using @groq/sdk npm package: npm uninstall @groq/sdk
  - Delete all Groq client initialization code
  - Find all groq.chat.completions() calls, mark for replacement

* Add OpenRouter client:
  - npm install --save axios (or use node-fetch, or use openai library with custom baseURL)
  - Create file: src/services/llm.ts (or llm.py for Python)
  - Initialize OpenRouter client:
    ```typescript
    // src/services/llm.ts
    import axios from 'axios'
    
    const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY
    const OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
    
    const client = axios.create({
      baseURL: OPENROUTER_BASE_URL,
      headers: {
        Authorization: \`Bearer \${OPENROUTER_API_KEY}\`,
        'HTTP-Referer': 'https://sahaya.example.com',
        'X-Title': 'SahayaKSetu'
      }
    })
    
    export async function generateLLMResponse(
      model: string,
      messages: Array<{ role: string; content: string }>,
      maxTokens: number = 150
    ) {
      const response = await client.post('/chat/completions', {
        model: model,
        messages: messages,
        max_tokens: maxTokens,
        temperature: 0.3
      })
      
      return response.data.choices[0].message.content
    }
    ```

Step 3: Model Selection Strategy

* Categorize tasks:
  1. Query understanding (parse user intent from search query)
     - Example: "education loan" → { intent: 'find_schemes', topic: 'education', type: 'loan' }
     - Model: meta-llama/llama-2-7b-chat (fast, cheap)
     - Max tokens: 50
     - Temperature: 0.1 (deterministic)
  
  2. Summarization (condense scheme description)
     - Example: 1000-char description → 100-char summary
     - Model: mistral/mistral-7b (good balance)
     - Max tokens: 80
     - Temperature: 0.2
  
  3. RAG answer generation (generate user-facing response with scheme info)
     - Example: user query + top-3 schemes → "Here are 3 schemes for you..."
     - Model: meta-llama/llama-2-13b-chat (higher quality)
     - Max tokens: 200
     - Temperature: 0.3
  
  4. Fallback (if primary model fails)
     - Model: qwen/qwen-14b-chat (different architecture, different failure modes)
     - Use only if primary fails after 1 retry

* Cost comparison (approx., as of 2024):
  - Llama-2-7b: $0.00007 per 1k tokens (cheapest)
  - Mistral-7b: $0.00014 per 1k tokens
  - Llama-2-13b: $0.00020 per 1k tokens
  - Qwen-14b: $0.00030 per 1k tokens
  - Gemini (previous): $0.0005 per 1k tokens
  - Groq (previous): $0.0008 per 1k tokens
  - → Target: 50-70% cost reduction

* Quality benchmarks (manual testing):
  - Test 20 queries with each model
  - Rate outputs: 1 (bad) to 5 (excellent)
  - Keep models with avg rating >= 3.5

Step 4: Implement Abstraction Layer

Create provider-agnostic interface:

```typescript
// src/services/llm-interface.ts
export interface LLMTask {
  type: 'query_understanding' | 'summarization' | 'generation'
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  maxTokens?: number
}

export interface LLMResponse {
  content: string
  model: string
  tokensUsed: number
  costUsd: number
}

// Map task type → model + config
const TASK_CONFIG = {
  query_understanding: {
    model: 'meta-llama/llama-2-7b-chat',
    maxTokens: 50,
    temperature: 0.1
  },
  summarization: {
    model: 'mistral/mistral-7b',
    maxTokens: 80,
    temperature: 0.2
  },
  generation: {
    model: 'meta-llama/llama-2-13b-chat',
    maxTokens: 200,
    temperature: 0.3
  }
}

export async function callLLM(task: LLMTask): Promise<LLMResponse> {
  const config = TASK_CONFIG[task.type]
  
  try {
    const response = await generateLLMResponse(
      config.model,
      task.messages,
      config.maxTokens
    )
    
    return {
      content: response,
      model: config.model,
      tokensUsed: response.usage.total_tokens,
      costUsd: calculateCost(config.model, response.usage.total_tokens)
    }
  } catch (error) {
    // Retry with fallback model
    return callLLMWithFallback(task, config.model)
  }
}

function calculateCost(model: string, tokens: number): number {
  const rates = {
    'meta-llama/llama-2-7b-chat': 0.00007,
    'mistral/mistral-7b': 0.00014,
    'meta-llama/llama-2-13b-chat': 0.00020,
    'qwen/qwen-14b-chat': 0.00030
  }
  return (tokens / 1000) * (rates[model] || 0)
}
```

Step 5: Prompt Optimization

For EACH task, optimize prompts:

* Query understanding prompt:
  ```
  User query: "{userQuery}"
  
  Extract intent and topics. Output JSON only (no explanation):
  { "intent": "find_schemes|get_info|...", "topics": ["..."], "confidence": 0.95 }
  ```
  - Old (Gemini): 500 tokens average
  - New (optimized): 30 tokens average
  - Improvement: 94% cost reduction

* Summarization prompt:
  ```
  Summarize in one sentence (max 20 words):
  "{description}"
  ```
  - Old (Groq): 150 tokens
  - New: 50 tokens
  - Improvement: 67% reduction

* Generation prompt:
  ```
  You are a helpful assistant for Indian government schemes.
  User asked: "{userQuery}"
  
  Relevant schemes:
  1. {schemeName}: {description}
  2. ...
  
  Respond in {language} in 2 sentences. Be concise and helpful.
  ```
  - Old: 350 tokens
  - New: 200 tokens
  - Improvement: 43% reduction

* Common optimizations:
  - Remove examples (use few-shot sparingly)
  - Use JSON output (parseable, no rambling)
  - Set low temperature (0.1-0.3) for deterministic output
  - Set low max_tokens (don't allow unlimited)
  - Avoid asking model to "think step by step" (costs tokens, not needed for simple tasks)

Step 6: Testing (Quality + Cost)

* Unit tests:
  ```typescript
  describe('callLLM', () => {
    it('generates valid query understanding', async () => {
      const response = await callLLM({
        type: 'query_understanding',
        messages: [{ role: 'user', content: 'education loan' }]
      })
      
      expect(response.content).toContain('intent')
      expect(response.costUsd).toBeLessThan(0.01)
    })
    
    it('falls back to secondary model on failure', async () => {
      // Mock primary model to fail
      const response = await callLLM({...})
      expect(response.model).toBe('qwen/qwen-14b-chat')
    })
  })
  ```

* Integration tests (end-to-end):
  - Search query → query understanding → retrieve schemes → generate response
  - Measure: latency, cost, output quality
  - Test 50 real queries from production logs
  - Compare old (Gemini+Groq) vs new (OpenRouter) outputs
  - If quality drop > 10%, investigate + fix prompts

* Cost analysis:
  - Log cost per query
  - Sum daily cost
  - Compare to baseline
  - Goal: < 50% of previous cost

* Performance testing:
  - Send 100 concurrent requests
  - Measure: avg latency, p99 latency, error rate
  - Ensure < 300ms per call
  - Ensure < 1% error rate

Step 7: Rollout Strategy

* Phase 1 (Staging): Test in staging environment
  - Deploy new LLM service
  - Run tests
  - Monitor logs
  - Measure cost/quality for 1 week

* Phase 2 (Canary): Route 10% of prod traffic to OpenRouter
  - Keep 90% on old providers
  - Compare outputs manually
  - If quality OK, proceed to 50%
  - If quality drop, rollback to 0%

* Phase 3 (Full rollout): 100% traffic to OpenRouter
  - Monitor for 24 hours
  - Watch error rate, latency, user feedback
  - If any issues, rollback to Phase 1

* Rollback plan:
  - If error rate > 5% for > 10 minutes, auto-rollback to old providers
  - Alert ops team
  - Investigate root cause

Step 8: Output

Deliver:
* src/services/llm.ts (OpenRouter client)
* src/services/llm-interface.ts (provider-agnostic interface)
* Task-specific prompts (documented + versioned)
* Model cost calculator + logging
* Unit + integration tests (100% coverage of LLM paths)
* Migration checklist (audit → implementation → testing → rollout)
* Cost tracking dashboard (cost per query, daily total, trend analysis)
* Monitoring alerts (error rate, cost anomalies, latency spikes)
* Runbook: how to switch models, how to rollback, how to debug

Constraints:

* Must maintain quality (> 90% match to old outputs, or improve)
* Must reduce cost (target: 50% reduction)
* Must be < 300ms per call (including network)
* Zero breaking changes (users should not notice difference)
* Easy to switch models (change config, not code)
* All costs logged + traceable (audit trail)
* Must handle API errors gracefully (retry + fallback)
* Must not expose API keys in logs
* Production-ready: tested, monitored, rollback plan ready

```

---

# 2.5) Development Setup & Tooling Guide (for Claude Code)

## Frontend Development Environment

### package.json (Core Dependencies)
```json
{
  "name": "sahaya-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "type-check": "tsc --noEmit",
    "lint": "eslint . --ext ts,tsx --max-warnings=0",
    "format": "prettier --write .",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "tailwindcss": "^4.0.0",
    "@shadcn/ui": "^0.7.0",
    "howler": "^2.2.4",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^4.0.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.50.0",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "prettier": "^3.0.0",
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.0"
  }
}
```

### TypeScript Configuration (tsconfig.json)
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitAny": true,
    "allowSyntheticDefaultImports": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### ESLint Configuration (.eslintrc.json)
```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module",
    "ecmaFeatures": {
      "jsx": true
    }
  },
  "plugins": ["@typescript-eslint", "react", "react-hooks"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/explicit-function-return-types": "warn",
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

### Prettier Configuration (.prettierrc.json)
```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always"
}
```

## Backend Development Environment

### package.json (Node.js)
```json
{
  "name": "sahaya-backend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "NODE_ENV=development tsx watch src/server.ts",
    "start": "NODE_ENV=production node dist/server.js",
    "build": "tsc",
    "db:migrate": "prisma migrate deploy",
    "db:seed": "tsx src/db/seed.ts",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "lint": "eslint . --ext ts --max-warnings=0",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "express": "^4.18.0",
    "prisma": "^5.0.0",
    "@prisma/client": "^5.0.0",
    "dotenv": "^16.3.0",
    "zod": "^3.22.0",
    "axios": "^1.5.0",
    "redis": "^4.6.0",
    "winston": "^3.11.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "express-rate-limit": "^7.0.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "tsx": "^4.0.0",
    "@types/express": "^4.17.17",
    "@types/node": "^20.3.0",
    "vitest": "^1.0.0",
    "supertest": "^6.3.0",
    "eslint": "^8.50.0",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0"
  }
}
```

### Backend .env.example
```env
# Server
PORT=3000
NODE_ENV=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sahaya
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=20

# Redis
REDIS_URL=redis://localhost:6379

# LLM
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Logging
LOG_LEVEL=info

# Security
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# CORS
FRONTEND_URL=http://localhost:5173

# Sentry (optional)
SENTRY_DSN=
```

## Git Workflow & Pre-commit Hooks

### .husky/pre-commit
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run type-check
npm run lint
npm test -- --run
```

### .gitignore
```
node_modules/
dist/
build/
.env
.env.local
.env.*.local
.vscode/
.idea/
*.log
.DS_Store
coverage/
.next/
.vercel/
```

## CI/CD Pipeline (GitHub Actions)

### .github/workflows/test-and-deploy.yml
```yaml
name: Test & Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: sahaya_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run type-check
      - run: npm run lint
      - run: npm test -- --run
      - run: npm run build

      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build
      - run: docker build -t sahaya:${{ github.sha }} .
      - run: docker push registry.example.com/sahaya:${{ github.sha }}
```

## Documentation Standards

### Each component should have JSDoc:
```typescript
/**
 * SearchInput Component
 * 
 * A voice-first search input for discovering government schemes.
 * 
 * @component
 * @example
 * <SearchInput 
 *   onSearch={(query) => console.log(query)}
 *   isLoading={false}
 * />
 * 
 * @param {SearchInputProps} props
 * @returns {ReactElement}
 */
export const SearchInput: React.FC<SearchInputProps> = (props) => {
  // ...
}
```

### Each API endpoint should have OpenAPI doc:
```typescript
/**
 * @openapi
 * /api/search:
 *   post:
 *     summary: Search government schemes
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               query:
 *                 type: string
 *                 minLength: 3
 *               language:
 *                 type: string
 *                 enum: [en, hi, ta, te, kn, ml, gu, ma]
 *     responses:
 *       200:
 *         description: List of matching schemes
 */
app.post('/api/search', searchHandler)
```

---

# 3) Execution Order & Timeline

**Recommended sequence:** (total time: 6-8 weeks)

1. **Week 1-2: Backend Audit + Hardening (Part II)**
   - Set up testing infrastructure
   - Write API tests + integration tests
   - Fix security vulnerabilities
   - Add logging + monitoring

2. **Week 2-3: LLM Migration (Part III)**
   - Migrate from Gemini+Groq to OpenRouter
   - Optimize prompts
   - Test quality + cost
   - Monitor in staging

3. **Week 3-4: Frontend Setup (Section 2.5)**
   - Initialize Vite + React 19 project
   - Set up TypeScript strict mode
   - Configure ESLint + Prettier
   - Set up Git hooks + CI/CD

4. **Week 4-6: UI/UX Redesign + Implementation (Part I)**
   - Build all components
   - Implement voice UX
   - Add i18n support
   - Test accessibility

5. **Week 6-8: Integration + Testing**
   - Connect frontend to backend
   - End-to-end testing
   - Performance optimization
   - User acceptance testing (UAT)

6. **Week 8: Deployment**
   - Docker containerization
   - CI/CD pipeline
   - Production deployment
   - Monitoring + alerts

---

# 4) Success Criteria

Before considering this upgrade complete, verify:

## Frontend
- [ ] All components render without errors
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Voice input works on Chrome/Firefox/Safari
- [ ] Language switching works (8 languages)
- [ ] Mobile layout responsive (375px to 1920px)
- [ ] Lighthouse score > 90 (Performance, Accessibility, Best Practices)
- [ ] All TypeScript strict mode violations fixed (0 errors)
- [ ] Unit test coverage > 80%

## Backend
- [ ] All APIs have passing tests (unit + integration)
- [ ] Database migrations run cleanly
- [ ] Error handling consistent across all endpoints
- [ ] Rate limiting + auth working
- [ ] Logging captures all requests
- [ ] Docker image builds + runs
- [ ] Response time < 500ms at p95
- [ ] Error rate < 0.5%

## LLM
- [ ] All Gemini+Groq calls replaced with OpenRouter
- [ ] Cost < 50% of previous spend
- [ ] Quality maintained (> 90% match to old outputs)
- [ ] Latency < 300ms per call
- [ ] Fallback model works on primary failure

## Deployment
- [ ] CI/CD pipeline passes all checks
- [ ] Monitoring + alerts configured
- [ ] Runbook + troubleshooting guide written
- [ ] Team trained on new system
- [ ] Gradual rollout (10% → 50% → 100%) completed

---

# 5) Final Goal

A system that is:
- ✅ Production-grade (tested, monitored, secure)
- ✅ Cost-efficient (50% reduction in LLM costs)
- ✅ Voice-first (waveform UI, hands-free interaction)
- ✅ Multilingual (8+ languages with proper fonts + layout)
- ✅ Accessible (WCAG 2.1 AA compliance)
- ✅ Beautiful (consistent design, modern UI)
- ✅ Fast (LCP < 2.5s, API < 500ms)
- ✅ Scalable (horizontal scaling via Docker)

---

# 6) Notes for Claude Code

When implementing these prompts in Claude Code:

1. **Read all 3 prompts** (Part I, II, III) before starting any one
2. **Run tests frequently** (after every major change)
3. **Commit to git** regularly with meaningful commit messages
4. **Follow TypeScript strict mode** — no 'any' types allowed
5. **Document as you code** — JSDoc + OpenAPI specs
6. **Ask for clarification** if any requirement is unclear
7. **Flag architectural decisions** before implementing (especially around caching, auth, data models)
8. **Test edge cases** (empty results, network errors, slow API)
9. **Performance-first**: profile bundle size, API latency, rendering
10. **Security-first**: validate all inputs, log errors without exposing secrets

Good luck! 🚀