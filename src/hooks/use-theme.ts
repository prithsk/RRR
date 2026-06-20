/**
 * RRR2 is light-mode only — always returns the warm palette
 * regardless of the system color scheme.
 */

import { Colors } from '@/constants/theme';

export function useTheme() {
  return Colors.light;
}
