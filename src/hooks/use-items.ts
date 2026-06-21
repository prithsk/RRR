import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';

import { listItems } from '@/services/items';
import { useAuth } from '@/hooks/use-auth';
import type { Item } from '@/types/item';

/** Fetches the signed-in user's items, refreshing whenever the screen regains focus. */
export function useItems() {
  const { user } = useAuth();
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!user) return;
    setError('');
    try {
      const data = await listItems(user.id);
      setItems(data);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load items');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return { items, loading, error, reload: load };
}
