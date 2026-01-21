-- HEADLESS STUDIO - Initial Database Schema
-- Version: 1.0
-- Date: 2026-01-20

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- OPPORTUNITIES TABLE
-- Stores discovered product opportunities from Reddit, Twitter, Trends
-- ============================================================================
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic info
    title TEXT NOT NULL,
    description TEXT,
    target_audience TEXT,
    product_type TEXT, -- 'prompt_pack', 'guide', 'roadmap', 'template_pack', 'checklist'

    -- Scores
    opportunity_score FLOAT,
    demand_score FLOAT,
    intent_score FLOAT,
    confidence TEXT DEFAULT 'high', -- 'high', 'medium', 'low'

    -- SEO
    primary_keyword TEXT,
    monthly_volume INTEGER,
    cpc DECIMAL(10,2),

    -- Discovery evidence (for display)
    reddit_mentions INTEGER DEFAULT 0,
    twitter_mentions INTEGER DEFAULT 0,
    evidence_urls JSONB, -- Links to example posts
    competitor_info JSONB, -- Competitor products found

    -- Landing page
    landing_page_url TEXT,
    landing_page_copy JSONB, -- {headline, subhead, bullets, cta_text}
    samples JSONB, -- 5 sample prompts/items delivered after signup

    -- Tracking
    visits INTEGER DEFAULT 0,
    signups INTEGER DEFAULT 0,

    -- Validation
    validation_method TEXT, -- 'paid', 'organic', 'skipped'

    -- Organic validation
    post_templates JSONB, -- {reddit, twitter, facebook} templates
    organic_deadline TIMESTAMPTZ,
    logged_signals JSONB, -- {dms: 2, buy_comments: 1, questions: 3, upvotes: 50, shares: 1}
    validation_points INTEGER DEFAULT 0,

    -- Paid validation
    ad_platforms JSONB, -- ['reddit', 'google', 'meta']
    ad_campaigns JSONB, -- Campaign IDs and details per platform
    ad_results JSONB, -- {reddit: {spend: 800, clicks: 32, signups: 2}, ...}
    combined_cvr FLOAT,

    -- Status
    status TEXT DEFAULT 'discovered',
    -- 'discovered' -> 'pending_gate1' -> 'validating_organic' | 'validating_paid' -> 'validated' | 'validation_failed' -> 'manufacturing' -> 'pending_gate2' -> 'published' | 'rejected'
    retry_eligible_after TIMESTAMPTZ,
    skipped_validation BOOLEAN DEFAULT FALSE,

    -- Suggested price (cents)
    suggested_price_cents INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for opportunities
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_created_at ON opportunities(created_at DESC);
CREATE INDEX idx_opportunities_primary_keyword ON opportunities(primary_keyword);
CREATE INDEX idx_opportunities_retry_eligible ON opportunities(retry_eligible_after) WHERE status = 'rejected' OR status = 'validation_failed';

-- ============================================================================
-- SMOKE TEST SIGNUPS TABLE
-- Stores email signups from landing pages during validation
-- ============================================================================
CREATE TABLE smoke_test_signups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,

    email TEXT NOT NULL,
    source TEXT, -- 'landing_page', 'manual_logged'
    user_agent TEXT,
    referrer TEXT,

    -- Tracking
    samples_delivered BOOLEAN DEFAULT FALSE,
    launch_email_sent BOOLEAN DEFAULT FALSE,
    converted_to_sale BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for signups
CREATE INDEX idx_signups_opportunity ON smoke_test_signups(opportunity_id);
CREATE INDEX idx_signups_email ON smoke_test_signups(email);
CREATE INDEX idx_signups_launch_email ON smoke_test_signups(launch_email_sent) WHERE launch_email_sent = FALSE;

-- ============================================================================
-- PRODUCTS TABLE
-- Stores manufactured and published products
-- ============================================================================
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id),

    title TEXT NOT NULL,
    price_cents INTEGER NOT NULL,

    -- Files
    pdf_path TEXT, -- Supabase Storage path
    cover_path TEXT,
    zip_path TEXT, -- Optional: templates/resources ZIP

    -- Content metadata
    word_count INTEGER,
    page_count INTEGER,

    -- Manufacturing
    draft_json JSONB, -- Structured draft before humanization
    humanized_json JSONB, -- After humanization
    diff_guard_passed BOOLEAN,

    -- QA
    qa_review_1_score INTEGER, -- 0-100 (Gemini review)
    qa_review_2_score INTEGER, -- 0-100 (Qwen review)
    ai_detection_score INTEGER, -- 0-100 (lower is better)
    qa_passed BOOLEAN DEFAULT FALSE,
    qa_revision_count INTEGER DEFAULT 0,

    -- Gumroad
    gumroad_product_id TEXT,
    gumroad_url TEXT,

    -- Sales tracking
    total_sales INTEGER DEFAULT 0,
    total_revenue_cents INTEGER DEFAULT 0,
    refund_count INTEGER DEFAULT 0,

    -- Funnel tracking (where sales came from)
    launch_email_sales INTEGER DEFAULT 0,
    pinterest_sales INTEGER DEFAULT 0,
    seo_sales INTEGER DEFAULT 0,
    gumroad_browse_sales INTEGER DEFAULT 0,
    crosssell_sales INTEGER DEFAULT 0,

    -- Evergreen health
    health_status TEXT DEFAULT 'new', -- 'new', 'healthy', 'needs_refresh', 'needs_v2', 'retired'
    last_health_check TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

-- Indexes for products
CREATE INDEX idx_products_opportunity ON products(opportunity_id);
CREATE INDEX idx_products_gumroad_id ON products(gumroad_product_id);
CREATE INDEX idx_products_published_at ON products(published_at DESC);
CREATE INDEX idx_products_health ON products(health_status);

-- ============================================================================
-- PINS TABLE
-- Stores Pinterest pins (automated or manual posting)
-- ============================================================================
CREATE TABLE pins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,

    title TEXT NOT NULL,
    description TEXT NOT NULL,
    image_path TEXT NOT NULL, -- Supabase Storage path
    destination_url TEXT NOT NULL, -- Gumroad product URL
    board_id TEXT, -- Pinterest board ID (or name for manual)

    scheduled_date DATE NOT NULL,
    priority INTEGER DEFAULT 0, -- Higher = post first

    status TEXT DEFAULT 'pending', -- 'pending', 'posted', 'skipped', 'failed'
    posting_mode TEXT DEFAULT 'auto', -- 'auto', 'manual'
    posted_at TIMESTAMPTZ,
    posted_by TEXT, -- 'system' or 'manual'

    pinterest_pin_id TEXT, -- Returned from Pinterest API

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for pins
CREATE INDEX idx_pins_product ON pins(product_id);
CREATE INDEX idx_pins_status ON pins(status);
CREATE INDEX idx_pins_scheduled ON pins(scheduled_date) WHERE status = 'pending';

-- ============================================================================
-- BLOG POSTS TABLE
-- Stores SEO blog posts with clustering support
-- ============================================================================
CREATE TABLE blog_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id),

    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    target_keyword TEXT NOT NULL,
    content_md TEXT NOT NULL, -- Markdown content
    content_html TEXT, -- Rendered HTML

    -- Clustering (Phase 3+)
    cluster_id UUID, -- References seo_clusters table
    is_pillar BOOLEAN DEFAULT FALSE,

    -- Links
    internal_links JSONB, -- [{post_id, anchor_text}, ...]
    external_links JSONB, -- [{url, anchor_text}, ...]

    -- Performance (updated periodically from Google Search Console)
    clicks_30d INTEGER DEFAULT 0,
    impressions_30d INTEGER DEFAULT 0,
    avg_position FLOAT,
    sales_30d INTEGER DEFAULT 0,

    -- SEO metadata
    meta_title TEXT,
    meta_description TEXT,

    status TEXT DEFAULT 'draft', -- 'draft', 'published'
    published_at TIMESTAMPTZ,
    last_updated TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for blog posts
CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_product ON blog_posts(product_id);
CREATE INDEX idx_blog_posts_cluster ON blog_posts(cluster_id);
CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_blog_posts_published ON blog_posts(published_at DESC);

-- ============================================================================
-- SEO CLUSTERS TABLE (Phase 3+)
-- Groups related products/posts for topical authority
-- ============================================================================
CREATE TABLE seo_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    niche TEXT,
    pillar_post_id UUID REFERENCES blog_posts(id),

    post_count INTEGER DEFAULT 0,
    product_count INTEGER DEFAULT 0,

    total_clicks_30d INTEGER DEFAULT 0,
    total_sales_30d INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for clusters
CREATE INDEX idx_clusters_niche ON seo_clusters(niche);

-- ============================================================================
-- SALES TABLE
-- Stores individual sales with source tracking
-- ============================================================================
CREATE TABLE sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id),

    amount_cents INTEGER NOT NULL,
    gumroad_sale_id TEXT UNIQUE NOT NULL,
    buyer_email TEXT,

    -- Source tracking (inferred from referrer, UTM params, or email)
    source TEXT, -- 'launch_email', 'pinterest', 'seo', 'gumroad_browse', 'crosssell', 'unknown'
    referrer_url TEXT,
    utm_params JSONB, -- {utm_source, utm_medium, utm_campaign}

    refunded BOOLEAN DEFAULT FALSE,
    refunded_at TIMESTAMPTZ,
    refund_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for sales
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_sales_gumroad_id ON sales(gumroad_sale_id);
CREATE INDEX idx_sales_created ON sales(created_at DESC);
CREATE INDEX idx_sales_source ON sales(source);
CREATE INDEX idx_sales_refunded ON sales(refunded);

-- ============================================================================
-- SYSTEM LOGS TABLE
-- Stores workflow execution logs, errors, alerts
-- ============================================================================
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    log_type TEXT NOT NULL, -- 'workflow', 'error', 'alert', 'info'
    workflow_name TEXT, -- 'discovery', 'manufacturing', 'validation_check', etc.

    message TEXT NOT NULL,
    details JSONB,

    severity TEXT DEFAULT 'info', -- 'info', 'warning', 'error', 'critical'

    -- Optional references
    opportunity_id UUID REFERENCES opportunities(id),
    product_id UUID REFERENCES products(id),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for logs
CREATE INDEX idx_logs_type ON system_logs(log_type);
CREATE INDEX idx_logs_workflow ON system_logs(workflow_name);
CREATE INDEX idx_logs_severity ON system_logs(severity);
CREATE INDEX idx_logs_created ON system_logs(created_at DESC);

-- ============================================================================
-- UPDATED_AT TRIGGER FUNCTION
-- Auto-updates updated_at timestamp on row changes
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to opportunities table
CREATE TRIGGER update_opportunities_updated_at
    BEFORE UPDATE ON opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER VIEWS (Optional - for easier queries)
-- ============================================================================

-- Active validations view
CREATE VIEW active_validations AS
SELECT
    id,
    title,
    validation_method,
    status,
    validation_points,
    organic_deadline,
    signups,
    visits,
    CASE
        WHEN validation_method = 'organic' THEN validation_points >= 15
        WHEN validation_method = 'paid' THEN combined_cvr >= 0.04 AND signups >= 2
        ELSE NULL
    END AS passed
FROM opportunities
WHERE status IN ('validating_organic', 'validating_paid');

-- Product performance view
CREATE VIEW product_performance AS
SELECT
    p.id,
    p.title,
    p.price_cents,
    p.total_sales,
    p.total_revenue_cents,
    p.refund_count,
    CASE
        WHEN p.total_sales > 0 THEN (p.refund_count::FLOAT / p.total_sales::FLOAT) * 100
        ELSE 0
    END AS refund_rate_pct,
    p.published_at,
    EXTRACT(EPOCH FROM (NOW() - p.published_at)) / 86400 AS days_live,
    CASE
        WHEN EXTRACT(EPOCH FROM (NOW() - p.published_at)) / 86400 > 0
        THEN p.total_sales::FLOAT / (EXTRACT(EPOCH FROM (NOW() - p.published_at)) / 86400)
        ELSE 0
    END AS sales_per_day
FROM products p
WHERE p.published_at IS NOT NULL;

-- ============================================================================
-- INITIAL DATA / CONFIGURATION (Optional)
-- ============================================================================

-- You can add seed data here if needed
-- Example: INSERT INTO system_config VALUES (...);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration
INSERT INTO system_logs (log_type, message, severity)
VALUES ('info', 'Initial schema migration 001 completed successfully', 'info');
