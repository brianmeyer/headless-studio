# HEADLESS STUDIO - CLAUDE CODE IMPLEMENTATION GUIDE

## How to Use This Document

This is a task-based implementation guide for Claude Code. The Master Plan (`/docs/MASTER_PLAN.md`) contains the full context and design decisions. This document contains the **actual tasks** to build.

**Rules for Claude Code:**
1. Complete tasks in order within each phase
2. Mark tasks complete with [x] when done
3. Don't skip ahead to future phases
4. Each task should be completable in one session
5. Test each component before moving on
6. Ask for clarification if requirements are unclear

---

## Repository Structure (Target)

```
headless-studio/
├── docs/
│   ├── MASTER_PLAN.md          # Full V18.2 plan (reference)
│   └── IMPLEMENTATION_GUIDE.md  # This file (tasks)
├── backend/                     # Railway deployment
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py           # Environment/settings
│   │   ├── models/             # Pydantic models
│   │   ├── routers/            # API endpoints
│   │   │   ├── discovery.py
│   │   │   ├── validation.py
│   │   │   ├── manufacturing.py
│   │   │   ├── publishing.py
│   │   │   ├── landing_pages.py # Landing page routes (GET /lp/{id})
│   │   │   └── webhooks.py
│   │   ├── services/           # Business logic
│   │   │   ├── x_scout.py      # Primary discovery (xAI/Grok)
│   │   │   ├── trends_scout.py
│   │   │   ├── keyword_scout.py
│   │   │   ├── reddit_scout.py # Add when Reddit API approved
│   │   │   ├── scorer.py
│   │   │   ├── duplicate_checker.py
│   │   │   ├── landing_page.py # Copy generation service
│   │   │   ├── sample_generator.py
│   │   │   ├── ad_manager.py
│   │   │   ├── drafter.py
│   │   │   ├── humanizer.py
│   │   │   ├── image_generator.py
│   │   │   ├── pdf_builder.py
│   │   │   ├── qa_reviewer.py
│   │   │   ├── gumroad.py
│   │   │   └── pinterest.py
│   │   ├── templates/          # Jinja2 HTML templates
│   │   │   ├── landing_page.html
│   │   │   └── thank_you.html
│   │   └── utils/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
├── supabase/
│   ├── migrations/             # SQL migrations
│   │   └── 001_initial_schema.sql
│   └── seed.sql                # Optional seed data
├── n8n/                        # Workflow JSON exports
│   ├── 01_weekly_discovery.json
│   ├── 02_gate1_handler.json
│   └── ...
├── .env.example
├── README.md
└── CHANGELOG.md
```

---

# PHASE 0: FOUNDATION

**Goal**: Infrastructure + Discovery + First organic validation  
**Duration**: 2 weeks  
**Cost**: $25/month (n8n + Railway)

---

## Phase 0.1: Project Setup

### Task 0.1.1: Initialize Repository
- [ ] Create GitHub repo `headless-studio`
- [ ] Add `.gitignore` (Python, Node, environment files)
- [ ] Add `README.md` with project description
- [ ] Add `docs/` folder with Master Plan
- [ ] Add this implementation guide

**Done when**: Repo exists with docs folder containing both documents.

### Task 0.1.2: Create Backend Scaffold
- [ ] Create `backend/` folder structure
- [ ] Create `requirements.txt` with initial dependencies:
  ```
  fastapi==0.109.0
  uvicorn==0.27.0
  pydantic==2.5.3
  pydantic-settings==2.1.0
  httpx==0.26.0
  supabase==2.3.0
  openai==1.12.0        # For xAI/Grok API (OpenAI-compatible)
  python-dotenv==1.0.0
  pytrends==4.9.2       # For Google Trends
  jinja2==3.1.2         # For landing page HTML templates
  python-multipart==0.0.6  # For form handling
  # praw==7.7.1         # Add when Reddit API approved
  ```
- [ ] Create `backend/app/main.py` with basic FastAPI app
- [ ] Create `backend/app/config.py` with settings class
- [ ] Create `.env.example` with all required variables

**Done when**: `uvicorn app.main:app --reload` runs without errors.

### Task 0.1.3: Create Supabase Schema
- [x] Create `supabase/migrations/001_initial_schema.sql`
- [x] Include tables: `opportunities`, `products`, `pins`, `sales`, `smoke_test_signups`, `blog_posts`, `system_logs`
- [x] Include all indexes from Master Plan
- [x] Document how to run migration in README

**Schema reference**: See Master Plan Section 18 for full schema.

**Done when**: SQL file exists and is valid (can paste into Supabase SQL editor).

### Task 0.1.4: Environment Configuration
- [ ] Document all required environment variables in `.env.example`:
  ```
  # Required
  XAI_API_KEY=          # From console.x.ai (for Grok + X search)
  GROQ_API_KEY=
  GOOGLE_AI_API_KEY=
  SUPABASE_URL=
  SUPABASE_ANON_KEY=
  SUPABASE_SERVICE_KEY=

  # Add when approved
  REDDIT_CLIENT_ID=
  REDDIT_CLIENT_SECRET=
  REDDIT_USER_AGENT=

  # Optional (Phase 1+)
  REDDIT_ADS_CLIENT_ID=
  REDDIT_ADS_CLIENT_SECRET=
  GUMROAD_ACCESS_TOKEN=
  MAILERLITE_API_KEY=
  ```
- [ ] Create `backend/app/config.py` that loads these with pydantic-settings
- [ ] Add validation for required vs optional keys
- [ ] Add `reddit_configured` property that checks if Reddit credentials are present

**Done when**: App loads config without errors when `.env` has required keys.

---

## Phase 0.2: Discovery - X/Grok Scout (Primary)

### Task 0.2.1: X/Grok Scout Service
- [ ] Create `backend/app/services/x_scout.py`
- [ ] Implement `XGrokScout` class using xAI API:
  ```python
  class XGrokScout:
      def __init__(self, config: Settings):
          # Initialize xAI client with XAI_API_KEY
          # Grok has native X search capability

      async def search_x(
          self,
          topics: list[str],
          search_queries: list[str] | None = None,
          time_filter: str = "week",
          limit: int = 100
      ) -> list[XSignal]:
          # Use Grok to search X for pain points, requests, frustrations
          # Search queries like: "{topic} need help", "{topic} frustrated",
          # "{topic} wish there was", "{topic} looking for"
          # Return structured signals

      async def analyze_signals(
          self,
          raw_tweets: list[dict]
      ) -> list[XSignal]:
          # Use Grok to analyze and score relevance
  ```
- [ ] Create `backend/app/models/signals.py` with `XSignal` model:
  ```python
  class XSignal(BaseModel):
      tweet_id: str
      text: str
      author_username: str
      author_followers: int | None
      engagement_score: int  # likes + retweets + replies
      created_at: datetime
      url: str
      relevance_score: float  # How relevant to product opportunity
      pain_point_type: str | None  # "request", "frustration", "question"
  ```
- [ ] Handle xAI API rate limits gracefully
- [ ] Add logging for debugging

**Done when**: Can call `x_scout.search_x(["chatgpt prompts", "AI tools"])` and get results.

### Task 0.2.2: X/Grok Scout API Endpoint
- [ ] Create `backend/app/routers/discovery.py`
- [ ] Add endpoint `POST /api/discovery/x`:
  ```python
  @router.post("/x")
  async def search_x(
      topics: list[str],
      search_queries: list[str] | None = None,
      time_filter: str = "week"
  ) -> XSearchResponse:
      # Call XGrokScout
      # Return signals
  ```
- [ ] Add error handling for xAI API failures
- [ ] Add response model

**Done when**: Can hit endpoint and get X signals back.

### Task 0.2.3: X/Grok Scout Tests
- [ ] Create `backend/tests/test_x_scout.py`
- [ ] Test: Search returns results for valid query
- [ ] Test: Empty results handled gracefully
- [ ] Test: Invalid topic handled
- [ ] Test: Rate limit behavior

**Done when**: All tests pass.

---

## Phase 0.3: Discovery - Additional Scouts (Trends + Keywords)

### Task 0.3.1: Google Trends Scout (Supplement)
- [ ] Create `backend/app/services/trends_scout.py`
- [ ] Use `pytrends` library
- [ ] Implement:
  ```python
  class TrendsScout:
      async def get_interest_over_time(
          self,
          keywords: list[str],
          timeframe: str = "today 3-m"
      ) -> TrendsData:
          # Return trend data

      async def get_related_queries(
          self,
          keyword: str
      ) -> list[str]:
          # Return related searches
  ```
- [ ] Handle pytrends rate limits (it's aggressive)
- [ ] Make this optional - don't fail discovery if trends fails

**Done when**: Can get trend data, or gracefully returns empty if API fails.

### Task 0.3.2: Keyword Scout (DataForSEO or Fallback)
- [ ] Create `backend/app/services/keyword_scout.py`
- [ ] Primary: DataForSEO API (if key provided)
- [ ] Fallback: Hardcoded estimates based on patterns
- [ ] Implement:
  ```python
  class KeywordScout:
      async def get_keyword_data(
          self,
          keyword: str
      ) -> KeywordData:
          # Returns: volume, cpc, competition

      async def get_related_keywords(
          self,
          seed_keyword: str,
          limit: int = 10
      ) -> list[KeywordData]:
  ```
- [ ] Model:
  ```python
  class KeywordData(BaseModel):
      keyword: str
      monthly_volume: int | None
      cpc: float | None
      competition: str | None  # low, medium, high
      source: str  # "dataforseo" or "estimate"
  ```

**Done when**: Returns keyword data (real or estimated).

### Task 0.3.3: Discovery Aggregator
- [ ] Create `backend/app/services/discovery_aggregator.py`
- [ ] Combines all scouts into one discovery run:
  ```python
  class DiscoveryAggregator:
      async def run_discovery(
          self,
          topics: list[str],
          subreddits: list[str] | None = None
      ) -> list[RawOpportunity]:
          # 1. Search X via Grok (primary)
          x_signals = await self.x_scout.search_x(topics)

          # 2. Get trends (supplement)
          trends = await self.trends_scout.get_trends(topics)

          # 3. Get keywords
          keywords = await self.keyword_scout.get_data(topics)

          # 4. Reddit (only if configured)
          reddit_signals = []
          if self.config.reddit_configured:
              reddit_signals = await self.reddit_scout.search(subreddits, topics)

          # 5. Combine and score
          # 6. Return raw (unscored) opportunities
  ```
- [ ] Handle partial failures (some scouts fail, others succeed)
- [ ] Track which sources returned data for confidence scoring
- [ ] X/Grok is required; other sources are supplementary

**Done when**: Can run full discovery and get combined opportunities.

---

## Phase 0.4: Scoring System

### Task 0.4.1: Opportunity Scorer
- [ ] Create `backend/app/services/scorer.py`
- [ ] Implement scoring algorithm from Master Plan Section 7.2:
  ```python
  class OpportunityScorer:
      def score_opportunity(
          self,
          raw: RawOpportunity
      ) -> ScoredOpportunity:
          demand_score = self._calculate_demand(raw)  # 0-50
          intent_score = self._calculate_intent(raw)   # 0-40
          competition_penalty = self._calculate_competition(raw)  # -20 to 0
          
          total = demand_score + intent_score + competition_penalty
          confidence = self._determine_confidence(raw)
          
          return ScoredOpportunity(
              ...raw,
              opportunity_score=total,
              demand_score=demand_score,
              intent_score=intent_score,
              confidence=confidence
          )
  ```
- [ ] Implement demand scoring:
  - X/Twitter mentions: 0-30 pts (primary, with freshness decay)
  - Google Trends: 0-10 pts
  - Reddit mentions: 0-10 pts (when available)
- [ ] Implement intent scoring (CPC, competitor presence)
- [ ] Implement competition penalty
- [ ] Implement confidence level (based on data completeness - higher if X data available)

**Done when**: Can score opportunities, scores match expected ranges.

### Task 0.4.2: Duplicate Checker
- [ ] Create `backend/app/services/duplicate_checker.py`
- [ ] Implement:
  ```python
  class DuplicateChecker:
      async def check_duplicate(
          self,
          opportunity: ScoredOpportunity,
          lookback_days: int = 90
      ) -> DuplicateCheckResult:
          # 1. Check exact title match
          # 2. Check same primary keyword in lookback period
          # 3. Check semantic similarity (simple: Jaccard on tokens)
          # 4. Check against published products
          
          return DuplicateCheckResult(
              is_duplicate=bool,
              reason=str | None,
              similar_to_id=uuid | None,
              similarity_score=float | None
          )
  ```
- [ ] Query Supabase for historical opportunities
- [ ] Simple token-based similarity (don't need embeddings yet)

**Done when**: Can detect duplicates against database.

### Task 0.4.3: Full Discovery Pipeline
- [ ] Create `POST /api/discovery/run` endpoint
- [ ] Orchestrate: Aggregate → Score → Dedupe → Save
- [ ] Return list of new opportunities ready for Gate 1
- [ ] Save to Supabase with status `pending_gate1`

**Done when**: Can trigger discovery and see opportunities in Supabase.

---

## Phase 0.5: Landing Page System

**Note**: Landing pages are served from FastAPI on Railway, NOT Supabase Edge Functions.
Supabase Edge Functions cannot serve HTML (returns `text/plain` instead of `text/html`).

### Task 0.5.1: Landing Page Templates
- [ ] Create `backend/app/templates/` directory
- [ ] Create `backend/app/templates/landing_page.html` Jinja2 template:
  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{{ copy.headline }}</title>
      <style>
          /* Mobile-responsive CSS */
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
          /* ... styling for container, form, bullets, etc. */
      </style>
  </head>
  <body>
      <div class="container">
          <h1>{{ copy.headline }}</h1>
          <p class="subhead">{{ copy.subhead }}</p>
          <ul class="benefits">
              {% for bullet in copy.bullets %}
              <li>{{ bullet }}</li>
              {% endfor %}
          </ul>
          <form action="/api/signup/{{ opportunity_id }}" method="POST">
              <input type="email" name="email" placeholder="Enter your email" required>
              <button type="submit">{{ copy.cta_text }}</button>
          </form>
          <p class="footer">Full product launching soon. No spam, unsubscribe anytime.</p>
      </div>
  </body>
  </html>
  ```
- [ ] Create `backend/app/templates/thank_you.html` for post-signup page with samples
- [ ] Include mobile-responsive CSS (inline in templates)

**Done when**: Templates exist and render correctly with test data.

### Task 0.5.2: Landing Page Router
- [ ] Create `backend/app/routers/landing_pages.py`
- [ ] Add Jinja2 template configuration to FastAPI app
- [ ] Implement landing page route:
  ```python
  from fastapi import APIRouter, Request, HTTPException
  from fastapi.responses import HTMLResponse
  from fastapi.templating import Jinja2Templates

  router = APIRouter()
  templates = Jinja2Templates(directory="app/templates")

  @router.get("/lp/{opportunity_id}", response_class=HTMLResponse)
  async def landing_page(request: Request, opportunity_id: UUID):
      # Fetch opportunity from database
      # Increment visit counter
      # Render template with opportunity data
      return templates.TemplateResponse("landing_page.html", {
          "request": request,
          "opportunity_id": opportunity_id,
          "copy": opportunity.landing_page_copy or default_copy
      })
  ```
- [ ] Track page visits in `opportunities.visits` counter
- [ ] Handle 404 for invalid opportunity IDs

**Done when**: Can visit `https://your-app.railway.app/lp/{id}` and see rendered HTML page.

### Task 0.5.3: Signup Handler
- [ ] Create signup endpoint in `backend/app/routers/landing_pages.py`:
  ```python
  @router.post("/api/signup/{opportunity_id}", response_class=HTMLResponse)
  async def handle_signup(
      request: Request,
      opportunity_id: UUID,
      email: str = Form(...)
  ):
      # Validate email format
      # Check for duplicate signups
      # Insert into `smoke_test_signups`
      # Increment `opportunities.signups`
      # Fetch samples and render thank_you.html
      return templates.TemplateResponse("thank_you.html", {
          "request": request,
          "samples": opportunity.samples or []
      })
  ```
- [ ] Handle duplicate emails gracefully (show samples again, don't double-count)
- [ ] Store source/referrer info for tracking

**Done when**: Can submit email via form and see thank you page with samples.

### Task 0.5.4: Landing Page Copy Generator Service
- [ ] Create `backend/app/services/landing_page.py`
- [ ] Use Gemini to generate marketing copy:
  ```python
  class LandingPageGenerator:
      async def generate_copy(
          self,
          opportunity: ScoredOpportunity
      ) -> LandingPageCopy:
          # Generate: headline, subhead, bullets, cta_text
          # Store in opportunity.landing_page_copy
  ```
- [ ] Create `LandingPageCopy` Pydantic model:
  ```python
  class LandingPageCopy(BaseModel):
      headline: str
      subhead: str
      bullets: list[str]
      cta_text: str
  ```
- [ ] Prompt should create benefit-focused copy
- [ ] Call this during discovery, before Gate 1
- [ ] Store generated copy in `opportunities.landing_page_copy` JSONB field

**Done when**: Opportunities have generated landing page copy that renders in templates.

---

## Phase 0.6: Sample Generation

### Task 0.6.1: Sample Generator Service
- [ ] Create `backend/app/services/sample_generator.py`
- [ ] Generate 5 real, useful sample prompts:
  ```python
  class SampleGenerator:
      async def generate_samples(
          self,
          opportunity: Opportunity
      ) -> list[Sample]:
          # Use Qwen3 32B via Groq
          # Generate 5 actually useful prompts
          # These get delivered to signups
  ```
- [ ] Samples should be good enough that people feel they got value
- [ ] Store in `opportunities.samples` JSONB field

**Done when**: Can generate samples, they're stored, and shown after signup.

### Task 0.6.2: Sample Delivery on Signup
- [ ] After email capture, show samples immediately on confirmation page
- [ ] Format samples nicely (not raw JSON)
- [ ] Include "Full pack coming soon" messaging

**Done when**: Signing up shows actual sample prompts.

---

## Phase 0.7: Organic Validation Tracking

### Task 0.7.1: Signal Logging Endpoint
- [ ] Create `POST /api/validation/log-signal`:
  ```python
  @router.post("/log-signal")
  async def log_organic_signal(
      opportunity_id: UUID,
      signal_type: Literal["dm", "buy_comment", "question", "share", "upvotes"],
      platform: str,
      quote: str | None = None,
      count: int = 1
  ):
      # Update opportunities.logged_signals JSONB
      # Recalculate validation points
  ```
- [ ] Store signals in structured format
- [ ] Auto-calculate points based on rubric from Master Plan Section 8.2

**Done when**: Can log signals and see points update.

### Task 0.7.2: Validation Points Calculator
- [ ] Implement point calculation:
  ```python
  def calculate_validation_points(opportunity: Opportunity) -> int:
      signups = opportunity.signups * 3
      dms = opportunity.logged_signals.get("dms", 0) * 4
      buy_comments = opportunity.logged_signals.get("buy_comments", 0) * 3
      questions = opportunity.logged_signals.get("questions", 0) * 2
      upvotes = opportunity.logged_signals.get("upvotes", 0) // 25
      shares = opportunity.logged_signals.get("shares", 0) * 3
      
      return signups + dms + buy_comments + questions + upvotes + shares
  ```
- [ ] Store in `opportunities.validation_points`
- [ ] Check if >= 15 (pass threshold)

**Done when**: Points calculated correctly per rubric.

### Task 0.7.3: Post Template Generator
- [ ] Create `backend/app/services/post_templates.py`
- [ ] Generate posting templates for Reddit, Twitter, Facebook:
  ```python
  class PostTemplateGenerator:
      async def generate_templates(
          self,
          opportunity: Opportunity
      ) -> PostTemplates:
          # Reddit: Title + body (with link and without)
          # Twitter: Short version
          # Facebook: Group-friendly version
          # Include tips for each platform
  ```
- [ ] Store in `opportunities.post_templates` JSONB
- [ ] Generate when opportunity approved for organic validation

**Done when**: Templates generated and accessible.

---

## Phase 0.8: Gate 1 (Minimal)

### Task 0.8.1: Gate 1 Data Endpoint
- [ ] Create `GET /api/gates/gate1/pending`:
  ```python
  @router.get("/gate1/pending")
  async def get_pending_gate1() -> list[Gate1Opportunity]:
      # Return all opportunities with status = 'pending_gate1'
      # Include: scores, evidence links, landing page URL, ad copy
  ```
- [ ] Return enough data to show in approval UI

**Done when**: Endpoint returns pending opportunities with all needed data.

### Task 0.8.2: Gate 1 Approval Endpoint
- [ ] Create `POST /api/gates/gate1/approve`:
  ```python
  @router.post("/gate1/approve")
  async def approve_gate1(
      opportunity_id: UUID,
      validation_method: Literal["organic", "paid", "skip"],
      notes: str | None = None
  ):
      # Update status based on method
      # If organic: set deadline, generate post templates
      # If paid: (Phase 1 - just mark for now)
      # If skip: trigger manufacturing
  ```
- [ ] Handle each validation method appropriately

**Done when**: Can approve opportunities via API.

### Task 0.8.3: Gate 1 Rejection Endpoint
- [ ] Create `POST /api/gates/gate1/reject`:
  ```python
  @router.post("/gate1/reject")
  async def reject_gate1(
      opportunity_id: UUID,
      reason: str | None = None
  ):
      # Set status = 'rejected'
      # Set retry_eligible_after = now + 90 days
  ```

**Done when**: Can reject opportunities via API.

---

## Phase 0.9: N8N Integration (Minimal)

### Task 0.9.1: N8N Workflow - Weekly Discovery
- [ ] Create `n8n/01_weekly_discovery.json`
- [ ] Workflow:
  1. Cron trigger: Monday 6am
  2. HTTP Request: POST to `/api/discovery/run`
  3. IF results > 0: Send Slack/Email notification
  4. Include count and link to approval

**Done when**: Workflow can be imported into n8n and triggers correctly.

### Task 0.9.2: N8N Workflow - Gate 1 Approval
- [ ] Create `n8n/02_gate1_handler.json`
- [ ] For Phase 0, this can be simple:
  1. Webhook trigger
  2. Fetch pending opportunities
  3. Show form with each opportunity
  4. On submit: Call approve/reject endpoint
  5. Send confirmation

**Done when**: Can approve opportunities through n8n form.

### Task 0.9.3: N8N Workflow - Organic Validation Check
- [ ] Create `n8n/03_organic_validation_check.json`
- [ ] Daily workflow:
  1. Fetch opportunities with status = 'validating_organic'
  2. For each: Check points and deadline
  3. If passed: Trigger manufacturing
  4. If expired and failed: Mark as failed
  5. Send daily summary

**Done when**: Workflow correctly checks validation status.

---

## Phase 0.10: Testing & Deployment

### Task 0.10.1: Local Testing
- [ ] Test full discovery flow locally
- [ ] Test landing page + signup flow
- [ ] Test validation point tracking
- [ ] Test Gate 1 approval flow

**Done when**: Can run through entire Phase 0 flow locally.

### Task 0.10.2: Railway Deployment
- [ ] Create `Dockerfile` for backend
- [ ] Create `railway.toml` configuration
- [ ] Add deploy instructions to README
- [ ] Deploy and verify endpoints work

**Done when**: Backend is live on Railway, endpoints respond.

### Task 0.10.3: Supabase Setup
- [ ] Run migrations in Supabase
- [ ] Verify database tables created correctly
- [ ] Test database connectivity from Railway backend

**Done when**: Backend on Railway connects to production Supabase database.

### Task 0.10.4: N8N Setup
- [ ] Import workflows to n8n Cloud
- [ ] Configure credentials
- [ ] Test each workflow

**Done when**: Workflows run successfully in n8n.

---

## Phase 0 Complete Checklist

Before moving to Phase 1, verify:

- [ ] Discovery runs and finds opportunities
- [ ] Opportunities are scored and deduplicated
- [ ] Landing pages render with copy (via FastAPI/Railway)
- [ ] Signups are captured and samples delivered
- [ ] Organic validation points can be logged
- [ ] Gate 1 approval works via n8n
- [ ] At least one organic validation completed
- [ ] At least one real opportunity identified

**Phase 0 Success Criteria:**
1. System finds real opportunities
2. Landing pages capture signups (served from Railway, not Supabase)
3. You successfully validate one idea organically
4. Everything runs without manual intervention (except approvals)

---

# PHASE 0.X: REDDIT SCOUT (WHEN APPROVED)

**Status**: ⏸️ SKIP UNTIL REDDIT API APPROVED
**Prerequisite**: Reddit API access approved
**Note**: Once approved, Reddit Scout can be added to the Discovery Aggregator as an additional signal source

---

## Phase 0.X.1: Reddit Scout Service

### Task 0.X.1.1: Reddit Scout Service
- [ ] Create `backend/app/services/reddit_scout.py`
- [ ] Implement `RedditScout` class:
  ```python
  class RedditScout:
      def __init__(self, config: Settings):
          # Initialize PRAW client

      async def search_subreddits(
          self,
          subreddits: list[str],
          keywords: list[str],
          time_filter: str = "month",
          limit: int = 100
      ) -> list[RedditSignal]:
          # Search for posts matching keywords
          # Return structured signals

      async def get_trending_posts(
          self,
          subreddits: list[str],
          limit: int = 50
      ) -> list[RedditSignal]:
          # Get hot/rising posts
  ```
- [ ] Create `RedditSignal` model in `backend/app/models/signals.py`:
  ```python
  class RedditSignal(BaseModel):
      post_id: str
      title: str
      subreddit: str
      score: int
      num_comments: int
      url: str
      created_utc: datetime
      author: str
      selftext: str | None
      relevance_score: float  # How relevant to keywords
  ```
- [ ] Handle PRAW rate limits gracefully
- [ ] Add logging for debugging

**Done when**: Can call `reddit_scout.search_subreddits(["chatgpt"], ["prompts"])` and get results.

### Task 0.X.1.2: Reddit Scout API Endpoint
- [ ] Add endpoint `POST /api/discovery/reddit` to `backend/app/routers/discovery.py`:
  ```python
  @router.post("/reddit")
  async def search_reddit(
      subreddits: list[str],
      keywords: list[str],
      time_filter: str = "month"
  ) -> RedditSearchResponse:
      # Call RedditScout
      # Return signals
  ```
- [ ] Add error handling for Reddit API failures
- [ ] Add response model

**Done when**: Can hit endpoint and get Reddit signals back.

### Task 0.X.1.3: Reddit Scout Tests
- [ ] Create `backend/tests/test_reddit_scout.py`
- [ ] Test: Search returns results for valid query
- [ ] Test: Empty results handled gracefully
- [ ] Test: Invalid subreddit handled
- [ ] Test: Rate limit behavior

**Done when**: All tests pass.

---

## Phase 0.X.2: Integrate Reddit into Discovery Aggregator

### Task 0.X.2.1: Update Discovery Aggregator
- [ ] Add Reddit scout to `DiscoveryAggregator`:
  ```python
  # In run_discovery method, Reddit signals are already handled:
  # 4. Reddit (only if configured)
  reddit_signals = []
  if self.config.reddit_configured:
      reddit_signals = await self.reddit_scout.search(subreddits, topics)
  ```
- [ ] Update scoring to include Reddit mentions (0-10 pts when available)
- [ ] Update confidence scoring to reflect Reddit data availability

**Done when**: Discovery aggregator uses Reddit data when available.

---

# PHASE 1: PAID VALIDATION

**Goal**: Add Reddit ads, prove smoke test → sale correlation  
**Duration**: 2-3 months  
**Cost**: $45/month ($20 ad spend)

**Prerequisites**: Phase 0 complete, Reddit Ads account created

---

## Phase 1.1: Reddit Ads Integration

### Task 1.1.1: Reddit Ads Service
- [ ] Create `backend/app/services/reddit_ads.py`
- [ ] Implement campaign creation:
  ```python
  class RedditAdsManager:
      async def create_smoke_test_campaign(
          self,
          opportunity: Opportunity,
          budget_cents: int = 1000
      ) -> RedditCampaign:
          # 1. Create campaign
          # 2. Create ad group with targeting
          # 3. Create ad creative
          # 4. Return campaign info
  ```
- [ ] Implement status polling
- [ ] Implement stats fetching

### Task 1.1.2: Ad Copy Generator
- [ ] Create `backend/app/services/ad_copy.py`
- [ ] Generate Reddit ad copy (headline, body, targeting)
- [ ] Store in opportunity

### Task 1.1.3: Paid Validation Monitor
- [ ] Track ad approval status
- [ ] Start timer when ad goes live
- [ ] Calculate CVR after 5 days
- [ ] Trigger pass/fail

### Task 1.1.4: N8N Workflows for Paid Validation
- [ ] Ad launcher workflow
- [ ] Ad status monitor (every 4 hours)
- [ ] Validation completion handler

---

## Phase 1.2: Manufacturing Pipeline

### Task 1.2.1: Drafter Service
- [ ] Create `backend/app/services/drafter.py`
- [ ] Use Qwen3 32B to generate structured content
- [ ] Handle different product types

### Task 1.2.2: Humanizer Service
- [ ] Create `backend/app/services/humanizer.py`
- [ ] Use Gemini to make content natural
- [ ] Implement Diff Guard check

### Task 1.2.3: Image Generator Service
- [ ] Create `backend/app/services/image_generator.py`
- [ ] Use Imagen 3 for cover + interior images
- [ ] Save to Supabase Storage

### Task 1.2.4: PDF Builder Service
- [ ] Create `backend/app/services/pdf_builder.py`
- [ ] Use ReportLab or WeasyPrint
- [ ] Apply template with proper formatting

### Task 1.2.5: Manufacturing Orchestrator
- [ ] Create `POST /api/manufacturing/build`
- [ ] Orchestrate: Draft → Humanize → Images → PDF
- [ ] Handle failures with retries

---

## Phase 1.3: Quality Assurance

### Task 1.3.1: QA Reviewer Service
- [ ] Create `backend/app/services/qa_reviewer.py`
- [ ] Implement Review 1 (Gemini)
- [ ] Implement Review 2 (Qwen3)
- [ ] Implement Tone Check

### Task 1.3.2: QA Pipeline
- [ ] Run both reviews
- [ ] Calculate pass/fail
- [ ] Auto-revision loop (max 2x)
- [ ] Alert if still failing

---

## Phase 1.4: Gate 2 & Publishing

### Task 1.4.1: Gate 2 Endpoints
- [ ] GET pending products
- [ ] POST approve/reject
- [ ] Include QA scores, PDF download link

### Task 1.4.2: Gumroad Integration
- [ ] Create `backend/app/services/gumroad.py`
- [ ] Upload product (PDF, cover)
- [ ] Create listing
- [ ] Set price and publish

### Task 1.4.3: Sales Webhooks
- [ ] Handle Gumroad sale webhooks
- [ ] Handle refund webhooks
- [ ] Track in database

---

## Phase 1.5: Pinterest

### Task 1.5.1: Pin Generator
- [ ] Generate 5 pin images per product
- [ ] Generate descriptions with keywords

### Task 1.5.2: Pinterest API Integration (if approved)
- [ ] Create pin posting service
- [ ] Implement scheduling

### Task 1.5.3: Manual Pinterest Dashboard
- [ ] Create pin queue view
- [ ] Mark as posted functionality

---

## Phase 1.6: Email & Blog

### Task 1.6.1: MailerLite Integration
- [ ] Create email service
- [ ] Send launch emails to signups

### Task 1.6.2: Blog Post Generator
- [ ] Generate SEO blog post per product
- [ ] Save as draft for review

---

# PHASE 2: MULTI-PLATFORM

**Goal**: Add Google OR Meta ads, optimize performance  
**Prerequisites**: Phase 1 complete, platform account created

---

## Phase 2.1: Add Second Ad Platform

### Task 2.1.1: Platform Selection Logic
- [ ] Implement platform recommendation based on niche

### Task 2.1.2: Google Ads Integration (Option A)
- [ ] Complex: OAuth, multiple API calls
- [ ] Create campaign, ad group, responsive search ad

### Task 2.1.3: Meta Ads Integration (Option B)
- [ ] Medium complexity
- [ ] Create campaign, ad set, ad creative

### Task 2.1.4: Multi-Platform Budget Split
- [ ] Configure budget allocation
- [ ] Track per-platform performance

---

## Phase 2.2: Performance Tracking

### Task 2.2.1: Platform Performance Table
- [ ] Track metrics per platform per niche
- [ ] Calculate which platform converts best

### Task 2.2.2: Funnel Dashboard
- [ ] Show sales by source
- [ ] Track conversion rates

---

# PHASE 3: SCALE

**Goal**: Add more platforms, SEO clustering, optimize  
**Prerequisites**: Phase 2 complete, profitable or near

---

## Phase 3.1: Additional Platforms
- [ ] TikTok Ads (if young audience products)
- [ ] Quora Ads (if Q&A intent)
- [ ] Dynamic platform allocation

## Phase 3.2: SEO System
- [ ] Keyword clustering
- [ ] Pillar content generation
- [ ] Internal linking automation
- [ ] Performance tracking

## Phase 3.3: Automation Polish
- [ ] Dashboard improvements
- [ ] Alerting refinements
- [ ] Documentation

---

# IMPLEMENTATION NOTES FOR CLAUDE CODE

## Working Style

1. **One task at a time**: Complete and test each task before moving on
2. **Commit often**: Each task should be one or more commits
3. **Test as you go**: Don't build everything then test
4. **Ask questions**: If requirements unclear, ask before building

## Common Patterns

### API Endpoint Pattern
```python
@router.post("/endpoint")
async def endpoint_handler(
    request: RequestModel,
    db: Client = Depends(get_supabase)
) -> ResponseModel:
    try:
        # Business logic via service
        result = await service.do_thing(request)
        return ResponseModel(success=True, data=result)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Service Pattern
```python
class SomeService:
    def __init__(self, config: Settings, db: Client):
        self.config = config
        self.db = db
    
    async def do_thing(self, input: InputModel) -> OutputModel:
        # Implementation
        pass
```

### Supabase Query Pattern
```python
result = await db.table("opportunities") \
    .select("*") \
    .eq("status", "pending_gate1") \
    .execute()

opportunities = result.data
```

## Error Handling

- Use try/except around external API calls
- Log errors with context
- Return meaningful error messages
- Don't let one failure crash the whole system

## Environment Variables

Always check if optional keys exist before using:
```python
# X/Grok is required - will fail if not configured
x_signals = await self.x_scout.search_x(topics)

# Reddit is optional - only use if configured
if config.reddit_configured:
    reddit_signals = await self.reddit_scout.search(subreddits, topics)
else:
    reddit_signals = []
    logger.info("Reddit not configured, skipping Reddit search")
```

---

**START WITH PHASE 0, TASK 0.1.1**
