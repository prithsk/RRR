import '@/global.css';

/**
 * RRR2 — warm vintage-thrift aesthetic.
 * Light mode ONLY. Beige paper backgrounds, light-orange accents,
 * flat design: bold solid outlines instead of shadows. No gradients, no fades.
 *
 * Both `light` and `dark` keys map to the SAME warm palette so the app is
 * effectively light-only regardless of system color scheme.
 */

const warm = {
  // Surfaces — beige paper
  text: '#2B2118', // dark warm brown ink
  background: '#F3E7D3', // warm beige paper
  backgroundElement: '#FBF3E4', // lighter cream cards
  backgroundSelected: '#F0DFC2', // pressed/selected cream
  textSecondary: '#8A7252', // muted brown

  // Brand — light orange
  primary: '#E07A3E', // light orange
  primaryLight: '#F7E3CE', // pale orange wash
  accent: '#C75C28', // deeper terracotta accent

  // Decision earth tones (cohesive, warm, distinguishable)
  donate: '#6F7A3C', // olive
  donateBg: '#E9E7CC',
  sell: '#E07A3E', // orange
  sellBg: '#F7E3CE',
  discard: '#B05334', // terracotta brick
  discardBg: '#F2DCCD',

  // Status
  error: '#B0352A',
  errorBg: '#F2D7D2',
  success: '#6F7A3C',
  successBg: '#E9E7CC',

  // Structure — bold flat outlines do the work shadows would
  border: '#2B2118', // strong ink border
  borderSoft: '#D8C4A2', // soft divider
  cardShadow: 'transparent', // no shadows
  overlay: 'rgba(43, 33, 24, 0.45)',
} as const;

export const Colors = {
  light: warm,
  dark: warm,
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = {
  // Distinctive serif display + clean grotesque body
  display: 'Fraunces_600SemiBold',
  displayBold: 'Fraunces_700Bold',
  body: 'HankenGrotesk_400Regular',
  bodyMedium: 'HankenGrotesk_500Medium',
  bodyBold: 'HankenGrotesk_700Bold',
  // legacy keys used by template components
  sans: 'HankenGrotesk_400Regular',
  serif: 'Fraunces_600SemiBold',
  rounded: 'HankenGrotesk_500Medium',
  mono: 'monospace',
} as const;

export const Typography = {
  display: { fontFamily: Fonts.displayBold, fontSize: 40, lineHeight: 44 },
  h1: { fontFamily: Fonts.displayBold, fontSize: 32, lineHeight: 38 },
  h2: { fontFamily: Fonts.display, fontSize: 24, lineHeight: 30 },
  h3: { fontFamily: Fonts.bodyBold, fontSize: 20, lineHeight: 26 },
  body: { fontFamily: Fonts.body, fontSize: 16, lineHeight: 24 },
  bodyBold: { fontFamily: Fonts.bodyBold, fontSize: 16, lineHeight: 24 },
  caption: { fontFamily: Fonts.body, fontSize: 14, lineHeight: 20 },
  captionBold: { fontFamily: Fonts.bodyBold, fontSize: 14, lineHeight: 20 },
  small: { fontFamily: Fonts.bodyMedium, fontSize: 12, lineHeight: 16 },
  button: { fontFamily: Fonts.bodyBold, fontSize: 16, lineHeight: 22 },
  buttonSmall: { fontFamily: Fonts.bodyBold, fontSize: 14, lineHeight: 18 },
} as const;

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

export const BorderRadius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  full: 9999,
} as const;

/** Standard flat outline used across the app instead of shadows. */
export const FlatBorder = {
  borderWidth: 2,
  borderColor: warm.border,
} as const;

export const BottomTabInset = 80;
export const MaxContentWidth = 800;
