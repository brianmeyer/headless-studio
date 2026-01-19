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

## Current Phase

**Phase 0: Foundation**

Working on: Task 0.1.1 - Initialize Repository

## License

Private - All rights reserved
