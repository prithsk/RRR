import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';

import { getProfile } from '@/services/items';
import { useAuth } from '@/hooks/use-auth';
import type { UserProfile } from '@/types/user';

/** Fetches the signed-in user's profile (stats), refreshing on focus. */
export function useProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!user) return;
    try {
      const data = await getProfile(user.id);
      setProfile(data);
    } catch {
      // leave previous profile
    } finally {
      setLoading(false);
    }
  }, [user]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return { profile, loading, reload: load };
}
