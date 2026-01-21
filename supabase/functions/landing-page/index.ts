import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from 'npm:@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface LandingPageCopy {
  headline: string
  subhead: string
  bullets: string[]
  cta_text: string
}

interface Opportunity {
  id: string
  title: string
  description: string | null
  target_audience: string | null
  product_type: string | null
  landing_page_copy: LandingPageCopy | null
  samples: { title: string; content: string }[] | null
  visits: number
  signups: number
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const url = new URL(req.url)
    const pathParts = url.pathname.split('/').filter(Boolean)

    // Handle signup POST
    if (req.method === 'POST' && pathParts[pathParts.length - 1] === 'signup') {
      return await handleSignup(req)
    }

    const opportunityId = pathParts[pathParts.length - 1]

    if (!opportunityId || opportunityId === 'landing-page') {
      return new Response(
        JSON.stringify({ error: 'Opportunity ID required. Use /landing-page/{id}' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    const { data: opportunity, error } = await supabase
      .from('opportunities')
      .select('id, title, description, target_audience, product_type, landing_page_copy, samples, visits, signups')
      .eq('id', opportunityId)
      .single()

    if (error || !opportunity) {
      return new Response(
        JSON.stringify({ error: 'Opportunity not found' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Increment visits in background
    supabase
      .from('opportunities')
      .update({ visits: (opportunity.visits || 0) + 1 })
      .eq('id', opportunityId)
      .then(() => {})

    // Build the response data
    const copy = opportunity.landing_page_copy || {
      headline: opportunity.title,
      subhead: opportunity.description || 'Get instant access to premium content',
      bullets: [
        'Save hours of time with ready-to-use templates',
        'Proven strategies from industry experts',
        'Instant digital delivery'
      ],
      cta_text: 'Get Free Samples'
    }

    // Return JSON data that the frontend can use
    return new Response(
      JSON.stringify({
        success: true,
        opportunity_id: opportunity.id,
        copy: copy,
        samples: opportunity.samples || [],
        stats: {
          visits: opportunity.visits || 0,
          signups: opportunity.signups || 0
        },
        signup_url: `${supabaseUrl}/functions/v1/landing-page/signup`
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (err) {
    console.error('Landing page error:', err)
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

async function handleSignup(req: Request): Promise<Response> {
  try {
    const body = await req.json()
    const { opportunity_id, email, source, user_agent } = body

    if (!opportunity_id || !email) {
      return new Response(
        JSON.stringify({ error: 'opportunity_id and email are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return new Response(
        JSON.stringify({ error: 'Invalid email address' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    const { data: existing } = await supabase
      .from('smoke_test_signups')
      .select('id')
      .eq('opportunity_id', opportunity_id)
      .eq('email', email.toLowerCase())
      .single()

    if (existing) {
      const { data: opportunity } = await supabase
        .from('opportunities')
        .select('samples')
        .eq('id', opportunity_id)
        .single()

      return new Response(
        JSON.stringify({ success: true, message: 'Already signed up', samples: opportunity?.samples || [] }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { error: insertError } = await supabase
      .from('smoke_test_signups')
      .insert({
        opportunity_id,
        email: email.toLowerCase(),
        source: source || 'landing_page',
        user_agent: user_agent || null,
        referrer: req.headers.get('referer') || null,
        samples_delivered: true
      })

    if (insertError) {
      console.error('Signup insert error:', insertError)
      return new Response(
        JSON.stringify({ error: 'Failed to save signup' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const { data: opportunity, error: updateError } = await supabase
      .from('opportunities')
      .select('signups, samples')
      .eq('id', opportunity_id)
      .single()

    if (!updateError && opportunity) {
      await supabase
        .from('opportunities')
        .update({ signups: (opportunity.signups || 0) + 1 })
        .eq('id', opportunity_id)
    }

    return new Response(
      JSON.stringify({ success: true, message: 'Signup successful', samples: opportunity?.samples || [] }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (err) {
    console.error('Signup error:', err)
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}
