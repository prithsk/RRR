import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';

import { getLeaderboard, type LeaderboardEntry } from '@/services/items';

/** Fetches the global leaderboard, refreshing on focus. */
export function useLeaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setError('');
    try {
      const data = await getLeaderboard();
      setEntries(data);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return { entries, loading, error, reload: load };
}
