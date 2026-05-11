import { createBrowserClient } from '@supabase/ssr'

const isValidSupabaseUrl = (url: string | undefined): url is string => {
  if (!url) return false
  return url.startsWith('https://') || url.startsWith('http://')
}

const createMockClient = () => {
  console.warn('Supabase not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local')
  return {
    auth: {
      signInWithPassword: async () => ({ error: new Error('Supabase not configured') }),
      signUp: async () => ({ error: new Error('Supabase not configured') }),
      signInWithOtp: async () => ({ error: new Error('Supabase not configured') }),
      signInWithOAuth: async () => ({ error: new Error('Supabase not configured') }),
      getSession: async () => ({ data: { session: null } }),
      getUser: async () => ({ data: { user: null } }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } })
    },
    from: () => ({
      select: () => ({
        eq: () => ({
          single: async () => ({ data: null, error: new Error('Supabase not configured') })
        })
      })
    })
  } as any
}

export const createSupabaseBrowserClient = () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!isValidSupabaseUrl(supabaseUrl) || !supabaseAnonKey) {
    return createMockClient()
  }

  return createBrowserClient(supabaseUrl, supabaseAnonKey)
}

export const supabase = createSupabaseBrowserClient()