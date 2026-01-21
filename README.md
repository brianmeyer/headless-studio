# Headless Studio

Autonomous AI-powered digital product factory.

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/YOUR_USERNAME/headless-studio.git
cd headless-studio
```

### 2. Repository Structure

```
headless-studio/
├── docs/
│   ├── MASTER_PLAN.md              # Full V18.2 design document
│   └── IMPLEMENTATION_GUIDE.md     # Task-based guide for Claude Code
├── backend/                         # Python FastAPI (deploys to Railway)
├── supabase/                        # Database + Edge Functions
├── n8n/                             # Workflow JSON exports
└── README.md
```

### 3. Working with Claude Code

1. Open this repo in Claude Code
2. Point Claude to `/docs/IMPLEMENTATION_GUIDE.md`
3. Work through tasks in order, one at a time
4. Each phase has clear success criteria

### 4. Phase Overview

| Phase | Goal | Monthly Cost | Duration |
|-------|------|--------------|----------|
| **0** | Foundation + organic validation | $25 | 2 weeks |
| **1** | Add paid ads, prove funnel | $45 | 2-3 months |
| **2** | Add second ad platform | $70 | 2 months |
| **3** | Scale + optimize | $70-120 | Ongoing |

### 5. Required Accounts (Phase 0)

- [ ] Groq (free): https://console.groq.com
- [ ] Google AI Studio (free): https://aistudio.google.com  
- [ ] Supabase (free): https://supabase.com
- [ ] Railway ($5/mo): https://railway.app
- [ ] n8n Cloud ($20/mo): https://app.n8n.cloud
- [ ] Gumroad (free): https://gumroad.com
- [ ] Pinterest Developer (apply early!): https://developers.pinterest.com

### 6. Documentation

- **Master Plan**: Full system design, decisions, and rationale
- **Implementation Guide**: Step-by-step tasks for Claude Code
- **This README**: Quick reference

## Commands

```bash
# Backend (local development)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run tests
pytest

# Deploy to Railway
railway up
```

## Supabase Setup

### Running the Initial Migration

1. Go to your Supabase project: https://***REMOVED***
2. Navigate to the SQL Editor (left sidebar)
3. Click "New Query"
4. Copy the contents of `supabase/migrations/001_initial_schema.sql`
5. Paste into the SQL Editor and click "Run"
6. Verify tables were created by checking the "Table Editor" section

### Supabase Credentials

Add these to your `.env` file:

```bash
SUPABASE_URL=https://***REMOVED***
SUPABASE_ANON_KEY=***REMOVED_JWT***
SUPABASE_SERVICE_KEY=***REMOVED_JWT***
```

**Note**: The service key provides full access to your database. Keep it secret and never commit to version control.

### What the Migration Creates

The migration creates:
- **8 tables**: opportunities, smoke_test_signups, products, pins, blog_posts, seo_clusters, sales, system_logs
- **Indexes**: For efficient queries on status, dates, foreign keys
- **2 views**: active_validations, product_performance (for easier analytics)
- **Auto-update trigger**: Keeps `updated_at` timestamps current

## Current Phase

**Phase 0: Foundation**

### Completed:
- ✅ Task 0.1.1: Initialize Repository
- ✅ Task 0.1.3: Create Supabase Schema (SQL file created at `supabase/migrations/001_initial_schema.sql`)
- ✅ `.env.example` created with all environment variables

### In Progress:
- ⏳ **Run the Supabase migration** - Use MCP to execute `supabase/migrations/001_initial_schema.sql`
- ⏳ Task 0.1.2: Create `backend/app/main.py` and `backend/app/config.py`

### Next:
- Task 0.1.4: Finalize environment configuration
- Verify backend runs with `uvicorn app.main:app --reload`

### Resume Instructions for Claude:
1. Use Supabase MCP to run the migration SQL from `supabase/migrations/001_initial_schema.sql`
2. Create `backend/app/config.py` with pydantic-settings
3. Create `backend/app/main.py` with FastAPI app
4. Test that uvicorn starts successfully

## License

Private - All rights reserved
