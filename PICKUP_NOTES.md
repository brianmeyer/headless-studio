# Pickup Notes - January 21, 2025

## Current Status: Phase 0 - Foundation (In Progress)

### What's Working ✅

1. **X/Grok Scout** (`backend/app/services/x_scout.py`)
   - Uses xAI Responses API with x_search tool
   - Returns signals with pain points and buying signals
   - Works for some topics (e.g., "chatgpt prompts real estate" → 2-4 signals)
   - Some topics return 0 signals (normal for X search)
   - **Main bottleneck**: ~30s per API call

2. **Gumroad Competition Scout** (`backend/app/services/gumroad_scout.py`)
   - Scrapes Gumroad discover page for competition analysis
   - Extracts price, rating, review count from React on Rails data
   - Competition levels: saturated(-20), high(-10), validated(-5), none(-10)
   - Fast: ~1.5s per search
   - Caches for 24 hours

3. **Opportunity Scorer** (`backend/app/services/scorer.py`)
   - Formula: Demand(0-50) + Intent(0-40) + Competition(-20 to 0) = Score(0-100)
   - Uses real Gumroad data for competition penalty
   - Score floor at 0 (fixed negative scores)

4. **Discovery Aggregator** (`backend/app/services/discovery_aggregator.py`)
   - Orchestrates X + Gumroad + Trends scouts
   - Runs Gumroad lookups in parallel with scoring

### What's Broken/Limited ⚠️

1. **Google Trends** - pytrends is ARCHIVED (April 2025) and returns 429 errors
   - Added caching and rate limit handling
   - Consider it OPTIONAL/supplementary only
   - For reliable trends: DataForSEO or SerpApi (both paid)

2. **Reddit Scout** - Credentials are placeholders
   - Waiting for Reddit API approval
   - Set `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in `.env` when ready

### Timing Breakdown (per topic)

| Component | Time | % |
|-----------|------|---|
| X/Grok | ~30s | 94% |
| Gumroad | ~1.5s | 4% |
| Trends | ~1s | 2% (often fails) |
| Scorer | instant | - |

### Test Commands

```bash
cd backend

# Test X scout
python -c "
import asyncio
from app.config import get_settings
from app.services.x_scout import XGrokScout

async def test():
    settings = get_settings()
    scout = XGrokScout(settings)
    signals = await scout.search_x(['chatgpt prompts real estate'], limit=5)
    print(f'Signals: {len(signals)}')
    for s in signals[:3]:
        print(f'  - {s.text[:60]}...')
asyncio.run(test())
"

# Test Gumroad scout
python -c "
import asyncio
from app.services.gumroad_scout import GumroadCompetitionScout

async def test():
    scout = GumroadCompetitionScout()
    result = await scout.search_competitors('chatgpt prompts', limit=10)
    print(f'Products: {result.product_count}')
    print(f'Competition: {result.competition_level} ({result.competition_penalty})')
    print(f'Avg rating: {result.avg_rating}')
asyncio.run(test())
"

# Test full scoring
python -c "
import asyncio
from app.config import get_settings
from app.services.x_scout import XGrokScout
from app.services.gumroad_scout import GumroadCompetitionScout
from app.services.scorer import OpportunityScorer

async def test():
    settings = get_settings()
    x = XGrokScout(settings)
    gumroad = GumroadCompetitionScout()
    scorer = OpportunityScorer()

    topic = 'ai prompts property manager'
    signals = await x.search_x([topic], limit=5)
    competition = await gumroad.search_competitors(topic)

    result = scorer.score_unified_signals(
        x_signals=signals,
        reddit_signals=[],
        trend_score=0,
        primary_keyword=topic,
        competition_data=competition,
    )
    print(f'Score: {result[\"opportunity_score\"]}/100')
    print(f'Competition: {competition.competition_level}')
asyncio.run(test())
"
```

### Next Steps

1. **Improve X signal quality** - Some topics return 0 signals
   - May need to adjust prompts or search queries
   - Consider adding fallback search templates

2. **Add Reddit** when API is approved
   - Update `.env` with real credentials
   - Test `reddit_scout.py`

3. **Consider paid alternatives for trends**:
   - DataForSEO (already in config, ~$0.002/request)
   - SerpApi ($75/mo)

4. **Speed optimization**:
   - X API is the bottleneck (~30s)
   - Can't really speed this up without changing providers
   - Consider caching X results too

### Files Modified Today

- `backend/app/services/gumroad_scout.py` - NEW
- `backend/app/services/scorer.py` - Added competition_data param, fixed negative scores
- `backend/app/services/trends_scout.py` - Added caching, rate limit handling
- `backend/app/services/x_scout.py` - Simplified query format
- `backend/app/services/discovery_aggregator.py` - Integrated Gumroad scout
