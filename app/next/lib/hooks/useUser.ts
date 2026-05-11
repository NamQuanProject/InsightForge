import { useEffect, useState } from 'react'
import { supabase } from '../supabase/client'

export interface UserProfile {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  role?: 'admin' | 'user' | 'viewer'
  created_at?: string
  updated_at?: string
}

export function useUser() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get current session
    const getUser = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        
        if (session?.user) {
          // Fetch profile from user_profiles table
          const { data: profile, error } = await supabase
            .from('user_profiles')
            .select('*')
            .eq('id', session.user.id)
            .single()

          if (error && error.code !== 'PGRST116') { // PGRST116 means no rows returned
            console.error('Error fetching user profile:', error)
            setUser(null)
          } else {
            // Combine auth user with profile data
            setUser({
              id: session.user.id,
              email: session.user.email ?? '',
              full_name: profile?.full_name,
              avatar_url: profile?.avatar_url,
              role: profile?.role,
              created_at: profile?.created_at,
              updated_at: profile?.updated_at
            })
          }
        } else {
          setUser(null)
        }
      } catch (error) {
        console.error('Error in useUser:', error)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    getUser()

    // Subscribe to auth changes
    const {
      data: { subscription }
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (session?.user) {
        const { data: profile, error } = await supabase
          .from('user_profiles')
          .select('*')
          .eq('id', session.user.id)
          .single()

        if (!error && profile) {
          setUser({
            id: session.user.id,
            email: session.user.email ?? '',
            full_name: profile.full_name,
            avatar_url: profile.avatar_url,
            role: profile.role,
            created_at: profile.created_at,
            updated_at: profile.updated_at
          })
        } else {
          setUser({
            id: session.user.id,
            email: session.user.email ?? '',
            full_name: undefined,
            avatar_url: undefined,
            role: undefined,
            created_at: undefined,
            updated_at: undefined
          })
        }
      } else {
        setUser(null)
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  return { user, loading }
}