import type {VideoPlan} from './types';

const baseTheme = {
  colors: {
    canvas: '#171A22',
    canvasAlt: '#222733',
    cream: '#ECE9E4',
    creamAlt: '#F4F1EB',
    ink: '#17191F',
    text: '#F7F4EF',
    muted: '#A8AFBD',
    surface: 'rgba(255,255,255,0.10)',
    surfaceStrong: 'rgba(255,255,255,0.18)',
    accent: '#FF6A3D',
    accentAlt: '#5B8F7D',
    grid: 'rgba(255,255,255,0.055)',
  },
  typography: {
    bodyFamily: 'Noto Sans SC',
    monoFamily: 'Space Mono',
    hero: 112,
    title: 72,
    body: 42,
    label: 27,
    caption: 38,
  },
  spacing: {
    safeX: 86,
    safeTop: 150,
    safeBottom: 190,
    xs: 12,
    sm: 20,
    md: 30,
    lg: 48,
    xl: 72,
  },
  radius: {
    card: 30,
    media: 28,
    pill: 999,
  },
  shadow: {
    card: '0 28px 64px -22px rgba(0,0,0,0.52)',
    media: '0 32px 72px -20px rgba(0,0,0,0.58)',
  },
  texture: {
    gridSize: 48,
    grainOpacity: 0.075,
  },
  motion: {
    entranceSec: 0.4,
    transitionSec: 0.55,
    poseSlideSec: 0.7,
  },
} as const;

export type ResolvedTheme = {
  colors: Record<keyof typeof baseTheme.colors, string>;
  typography: {
    bodyFamily: string;
    monoFamily: string;
    hero: number;
    title: number;
    body: number;
    label: number;
    caption: number;
  };
  spacing: Record<keyof typeof baseTheme.spacing, number>;
  radius: Record<keyof typeof baseTheme.radius, number>;
  shadow: Record<keyof typeof baseTheme.shadow, string>;
  texture: Record<keyof typeof baseTheme.texture, number>;
  motion: Record<keyof typeof baseTheme.motion, number>;
};

export const resolveTheme = (plan: VideoPlan): ResolvedTheme => {
  const overrides = plan.style.tokens ?? {};
  return {
    colors: {
      ...baseTheme.colors,
      ...overrides.colors,
      canvas: plan.video.background ?? overrides.colors?.canvas ?? baseTheme.colors.canvas,
      accent: plan.style.accent ?? overrides.colors?.accent ?? baseTheme.colors.accent,
    },
    typography: {
      ...baseTheme.typography,
      ...overrides.typography,
      bodyFamily:
        plan.style.fontFamily ??
        overrides.typography?.bodyFamily ??
        baseTheme.typography.bodyFamily,
    },
    spacing: {...baseTheme.spacing, ...overrides.spacing},
    radius: {...baseTheme.radius, ...overrides.radius},
    shadow: {...baseTheme.shadow, ...overrides.shadow},
    texture: {...baseTheme.texture, ...overrides.texture},
    motion: {
      ...baseTheme.motion,
      ...overrides.motion,
      entranceSec:
        plan.style.motion?.entranceSec ??
        overrides.motion?.entranceSec ??
        baseTheme.motion.entranceSec,
      transitionSec:
        plan.style.motion?.transitionSec ??
        overrides.motion?.transitionSec ??
        baseTheme.motion.transitionSec,
      poseSlideSec:
        plan.style.motion?.transitionSec ??
        overrides.motion?.poseSlideSec ??
        baseTheme.motion.poseSlideSec,
    },
  };
};
