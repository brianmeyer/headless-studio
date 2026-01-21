export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.1"
  }
  public: {
    Tables: {
      blog_posts: {
        Row: {
          avg_position: number | null
          clicks_30d: number | null
          cluster_id: string | null
          content_html: string | null
          content_md: string
          created_at: string | null
          external_links: Json | null
          id: string
          impressions_30d: number | null
          internal_links: Json | null
          is_pillar: boolean | null
          last_updated: string | null
          meta_description: string | null
          meta_title: string | null
          product_id: string | null
          published_at: string | null
          sales_30d: number | null
          slug: string
          status: string | null
          target_keyword: string
          title: string
        }
        Insert: {
          avg_position?: number | null
          clicks_30d?: number | null
          cluster_id?: string | null
          content_html?: string | null
          content_md: string
          created_at?: string | null
          external_links?: Json | null
          id?: string
          impressions_30d?: number | null
          internal_links?: Json | null
          is_pillar?: boolean | null
          last_updated?: string | null
          meta_description?: string | null
          meta_title?: string | null
          product_id?: string | null
          published_at?: string | null
          sales_30d?: number | null
          slug: string
          status?: string | null
          target_keyword: string
          title: string
        }
        Update: {
          avg_position?: number | null
          clicks_30d?: number | null
          cluster_id?: string | null
          content_html?: string | null
          content_md?: string
          created_at?: string | null
          external_links?: Json | null
          id?: string
          impressions_30d?: number | null
          internal_links?: Json | null
          is_pillar?: boolean | null
          last_updated?: string | null
          meta_description?: string | null
          meta_title?: string | null
          product_id?: string | null
          published_at?: string | null
          sales_30d?: number | null
          slug?: string
          status?: string | null
          target_keyword?: string
          title?: string
        }
        Relationships: [
          {
            foreignKeyName: "blog_posts_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "product_performance"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "blog_posts_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
        ]
      }
      opportunities: {
        Row: {
          ad_campaigns: Json | null
          ad_platforms: Json | null
          ad_results: Json | null
          combined_cvr: number | null
          competitor_info: Json | null
          confidence: string | null
          cpc: number | null
          created_at: string | null
          demand_score: number | null
          description: string | null
          evidence_urls: Json | null
          id: string
          intent_score: number | null
          landing_page_copy: Json | null
          landing_page_url: string | null
          logged_signals: Json | null
          monthly_volume: number | null
          opportunity_score: number | null
          organic_deadline: string | null
          post_templates: Json | null
          primary_keyword: string | null
          product_type: string | null
          reddit_mentions: number | null
          retry_eligible_after: string | null
          samples: Json | null
          signups: number | null
          skipped_validation: boolean | null
          status: string | null
          suggested_price_cents: number | null
          target_audience: string | null
          title: string
          twitter_mentions: number | null
          updated_at: string | null
          validation_method: string | null
          validation_points: number | null
          visits: number | null
        }
        Insert: {
          ad_campaigns?: Json | null
          ad_platforms?: Json | null
          ad_results?: Json | null
          combined_cvr?: number | null
          competitor_info?: Json | null
          confidence?: string | null
          cpc?: number | null
          created_at?: string | null
          demand_score?: number | null
          description?: string | null
          evidence_urls?: Json | null
          id?: string
          intent_score?: number | null
          landing_page_copy?: Json | null
          landing_page_url?: string | null
          logged_signals?: Json | null
          monthly_volume?: number | null
          opportunity_score?: number | null
          organic_deadline?: string | null
          post_templates?: Json | null
          primary_keyword?: string | null
          product_type?: string | null
          reddit_mentions?: number | null
          retry_eligible_after?: string | null
          samples?: Json | null
          signups?: number | null
          skipped_validation?: boolean | null
          status?: string | null
          suggested_price_cents?: number | null
          target_audience?: string | null
          title: string
          twitter_mentions?: number | null
          updated_at?: string | null
          validation_method?: string | null
          validation_points?: number | null
          visits?: number | null
        }
        Update: {
          ad_campaigns?: Json | null
          ad_platforms?: Json | null
          ad_results?: Json | null
          combined_cvr?: number | null
          competitor_info?: Json | null
          confidence?: string | null
          cpc?: number | null
          created_at?: string | null
          demand_score?: number | null
          description?: string | null
          evidence_urls?: Json | null
          id?: string
          intent_score?: number | null
          landing_page_copy?: Json | null
          landing_page_url?: string | null
          logged_signals?: Json | null
          monthly_volume?: number | null
          opportunity_score?: number | null
          organic_deadline?: string | null
          post_templates?: Json | null
          primary_keyword?: string | null
          product_type?: string | null
          reddit_mentions?: number | null
          retry_eligible_after?: string | null
          samples?: Json | null
          signups?: number | null
          skipped_validation?: boolean | null
          status?: string | null
          suggested_price_cents?: number | null
          target_audience?: string | null
          title?: string
          twitter_mentions?: number | null
          updated_at?: string | null
          validation_method?: string | null
          validation_points?: number | null
          visits?: number | null
        }
        Relationships: []
      }
      pins: {
        Row: {
          board_id: string | null
          created_at: string | null
          description: string
          destination_url: string
          id: string
          image_path: string
          pinterest_pin_id: string | null
          posted_at: string | null
          posted_by: string | null
          posting_mode: string | null
          priority: number | null
          product_id: string | null
          scheduled_date: string
          status: string | null
          title: string
        }
        Insert: {
          board_id?: string | null
          created_at?: string | null
          description: string
          destination_url: string
          id?: string
          image_path: string
          pinterest_pin_id?: string | null
          posted_at?: string | null
          posted_by?: string | null
          posting_mode?: string | null
          priority?: number | null
          product_id?: string | null
          scheduled_date: string
          status?: string | null
          title: string
        }
        Update: {
          board_id?: string | null
          created_at?: string | null
          description?: string
          destination_url?: string
          id?: string
          image_path?: string
          pinterest_pin_id?: string | null
          posted_at?: string | null
          posted_by?: string | null
          posting_mode?: string | null
          priority?: number | null
          product_id?: string | null
          scheduled_date?: string
          status?: string | null
          title?: string
        }
        Relationships: [
          {
            foreignKeyName: "pins_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "product_performance"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "pins_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
        ]
      }
      products: {
        Row: {
          ai_detection_score: number | null
          cover_path: string | null
          created_at: string | null
          crosssell_sales: number | null
          diff_guard_passed: boolean | null
          draft_json: Json | null
          gumroad_browse_sales: number | null
          gumroad_product_id: string | null
          gumroad_url: string | null
          health_status: string | null
          humanized_json: Json | null
          id: string
          last_health_check: string | null
          launch_email_sales: number | null
          opportunity_id: string | null
          page_count: number | null
          pdf_path: string | null
          pinterest_sales: number | null
          price_cents: number
          published_at: string | null
          qa_passed: boolean | null
          qa_review_1_score: number | null
          qa_review_2_score: number | null
          qa_revision_count: number | null
          refund_count: number | null
          seo_sales: number | null
          title: string
          total_revenue_cents: number | null
          total_sales: number | null
          word_count: number | null
          zip_path: string | null
        }
        Insert: {
          ai_detection_score?: number | null
          cover_path?: string | null
          created_at?: string | null
          crosssell_sales?: number | null
          diff_guard_passed?: boolean | null
          draft_json?: Json | null
          gumroad_browse_sales?: number | null
          gumroad_product_id?: string | null
          gumroad_url?: string | null
          health_status?: string | null
          humanized_json?: Json | null
          id?: string
          last_health_check?: string | null
          launch_email_sales?: number | null
          opportunity_id?: string | null
          page_count?: number | null
          pdf_path?: string | null
          pinterest_sales?: number | null
          price_cents: number
          published_at?: string | null
          qa_passed?: boolean | null
          qa_review_1_score?: number | null
          qa_review_2_score?: number | null
          qa_revision_count?: number | null
          refund_count?: number | null
          seo_sales?: number | null
          title: string
          total_revenue_cents?: number | null
          total_sales?: number | null
          word_count?: number | null
          zip_path?: string | null
        }
        Update: {
          ai_detection_score?: number | null
          cover_path?: string | null
          created_at?: string | null
          crosssell_sales?: number | null
          diff_guard_passed?: boolean | null
          draft_json?: Json | null
          gumroad_browse_sales?: number | null
          gumroad_product_id?: string | null
          gumroad_url?: string | null
          health_status?: string | null
          humanized_json?: Json | null
          id?: string
          last_health_check?: string | null
          launch_email_sales?: number | null
          opportunity_id?: string | null
          page_count?: number | null
          pdf_path?: string | null
          pinterest_sales?: number | null
          price_cents?: number
          published_at?: string | null
          qa_passed?: boolean | null
          qa_review_1_score?: number | null
          qa_review_2_score?: number | null
          qa_revision_count?: number | null
          refund_count?: number | null
          seo_sales?: number | null
          title?: string
          total_revenue_cents?: number | null
          total_sales?: number | null
          word_count?: number | null
          zip_path?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "products_opportunity_id_fkey"
            columns: ["opportunity_id"]
            isOneToOne: false
            referencedRelation: "active_validations"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "products_opportunity_id_fkey"
            columns: ["opportunity_id"]
            isOneToOne: false
            referencedRelation: "opportunities"
            referencedColumns: ["id"]
          },
        ]
      }
      sales: {
        Row: {
          amount_cents: number
          buyer_email: string | null
          created_at: string | null
          gumroad_sale_id: string
          id: string
          product_id: string | null
          referrer_url: string | null
          refund_reason: string | null
          refunded: boolean | null
          refunded_at: string | null
          source: string | null
          utm_params: Json | null
        }
        Insert: {
          amount_cents: number
          buyer_email?: string | null
          created_at?: string | null
          gumroad_sale_id: string
          id?: string
          product_id?: string | null
          referrer_url?: string | null
          refund_reason?: string | null
          refunded?: boolean | null
          refunded_at?: string | null
          source?: string | null
          utm_params?: Json | null
        }
        Update: {
          amount_cents?: number
          buyer_email?: string | null
          created_at?: string | null
          gumroad_sale_id?: string
          id?: string
          product_id?: string | null
          referrer_url?: string | null
          refund_reason?: string | null
          refunded?: boolean | null
          refunded_at?: string | null
          source?: string | null
          utm_params?: Json | null
        }
        Relationships: [
          {
            foreignKeyName: "sales_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "product_performance"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "sales_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
        ]
      }
      seo_clusters: {
        Row: {
          created_at: string | null
          id: string
          name: string
          niche: string | null
          pillar_post_id: string | null
          post_count: number | null
          product_count: number | null
          total_clicks_30d: number | null
          total_sales_30d: number | null
        }
        Insert: {
          created_at?: string | null
          id?: string
          name: string
          niche?: string | null
          pillar_post_id?: string | null
          post_count?: number | null
          product_count?: number | null
          total_clicks_30d?: number | null
          total_sales_30d?: number | null
        }
        Update: {
          created_at?: string | null
          id?: string
          name?: string
          niche?: string | null
          pillar_post_id?: string | null
          post_count?: number | null
          product_count?: number | null
          total_clicks_30d?: number | null
          total_sales_30d?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "seo_clusters_pillar_post_id_fkey"
            columns: ["pillar_post_id"]
            isOneToOne: false
            referencedRelation: "blog_posts"
            referencedColumns: ["id"]
          },
        ]
      }
      smoke_test_signups: {
        Row: {
          converted_to_sale: boolean | null
          created_at: string | null
          email: string
          id: string
          launch_email_sent: boolean | null
          opportunity_id: string | null
          referrer: string | null
          samples_delivered: boolean | null
          source: string | null
          user_agent: string | null
        }
        Insert: {
          converted_to_sale?: boolean | null
          created_at?: string | null
          email: string
          id?: string
          launch_email_sent?: boolean | null
          opportunity_id?: string | null
          referrer?: string | null
          samples_delivered?: boolean | null
          source?: string | null
          user_agent?: string | null
        }
        Update: {
          converted_to_sale?: boolean | null
          created_at?: string | null
          email?: string
          id?: string
          launch_email_sent?: boolean | null
          opportunity_id?: string | null
          referrer?: string | null
          samples_delivered?: boolean | null
          source?: string | null
          user_agent?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "smoke_test_signups_opportunity_id_fkey"
            columns: ["opportunity_id"]
            isOneToOne: false
            referencedRelation: "active_validations"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "smoke_test_signups_opportunity_id_fkey"
            columns: ["opportunity_id"]
            isOneToOne: false
            referencedRelation: "opportunities"
            referencedColumns: ["id"]
          },
        ]
      }
      system_logs: {
        Row: {
          created_at: string | null
          details: Json | null
          id: string
          log_type: string
          message: string
          opportunity_id: string | null
          product_id: string | null
          severity: string | null
          workflow_name: string | null
        }
        Insert: {
          created_at?: string | null
          details?: Json | null
          id?: string
          log_type: string
          message: string
          opportunity_id?: string | null
          product_id?: string | null
          severity?: string | null
          workflow_name?: string | null
        }
        Update: {
          created_at?: string | null
          details?: Json | null
          id?: string
          log_type?: string
          message?: string
          opportunity_id?: string | null
          product_id?: string | null
          severity?: string | null
          workflow_name?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "system_logs_opportunity_id_fkey"
            columns: ["opportunity_id"]
            isOneToOne: false
            referencedRelation: "active_validations"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "system_logs_opportunity_id_fkey"
            columns: ["opportunity_id"]
            isOneToOne: false
            referencedRelation: "opportunities"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "system_logs_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "product_performance"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "system_logs_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      active_validations: {
        Row: {
          id: string | null
          organic_deadline: string | null
          passed: boolean | null
          signups: number | null
          status: string | null
          title: string | null
          validation_method: string | null
          validation_points: number | null
          visits: number | null
        }
        Relationships: []
      }
      product_performance: {
        Row: {
          days_live: number | null
          id: string | null
          price_cents: number | null
          published_at: string | null
          refund_count: number | null
          refund_rate_pct: number | null
          sales_per_day: number | null
          title: string | null
          total_revenue_cents: number | null
          total_sales: number | null
        }
        Relationships: []
      }
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DefaultSchema = Database[Extract<keyof Database, "public">]

export type Tables<
  TableName extends keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
> = (DefaultSchema["Tables"] & DefaultSchema["Views"])[TableName] extends {
  Row: infer R
}
  ? R
  : never

export type TablesInsert<
  TableName extends keyof DefaultSchema["Tables"]
> = DefaultSchema["Tables"][TableName] extends {
  Insert: infer I
}
  ? I
  : never

export type TablesUpdate<
  TableName extends keyof DefaultSchema["Tables"]
> = DefaultSchema["Tables"][TableName] extends {
  Update: infer U
}
  ? U
  : never
