export type TimingMode = 'voice' | 'music' | 'fixed';

export type VoiceTrack = {
  beatId: string;
  src: string;
  text?: string;
  startSec: number;
  durationSec: number;
  volume?: number;
};

export type ScenePlan = {
  id: string;
  type: string;
  startSec: number;
  durationSec: number;
  beatIds?: string[];
  pose?: StagePoseName;
  continuousSubject?: boolean;
  props: Record<string, unknown>;
  effects?: EffectPlan[];
};

export type EffectPlan = {
  type: string;
  atSec: number;
  durationSec: number;
  props?: Record<string, unknown>;
};

export type CaptionCue = {
  startMs: number;
  endMs: number;
  text: string;
  words?: CaptionWord[];
};

export type CaptionWord = {
  text: string;
  startMs: number;
  endMs: number;
};

export type StagePoseName = string;

export type StagePoseTarget = {
  scale?: number;
  tx?: number;
  ty?: number;
  insetT?: number;
  insetR?: number;
  insetB?: number;
  insetL?: number;
  radius?: number;
  border?: number;
  shadow?: number;
  background?: number;
  gradL?: number;
  gradR?: number;
  opacity?: number;
};

export type StagePose = {
  atSec: number;
  pose: StagePoseName;
  transitionSec?: number;
};

export type StageSubject = {
  type?: 'card' | 'image' | 'video';
  src?: string;
  proxySrc?: string;
  masterSrc?: string;
  objectFit?: 'cover' | 'contain';
  objectPosition?: string;
  audioMode?: 'muted' | 'media';
  volume?: number;
  label?: string;
  subtitle?: string;
  background?: string;
};

export type ThemeTokens = {
  colors?: Partial<{
    canvas: string;
    canvasAlt: string;
    cream: string;
    creamAlt: string;
    ink: string;
    text: string;
    muted: string;
    surface: string;
    surfaceStrong: string;
    accent: string;
    accentAlt: string;
    grid: string;
  }>;
  typography?: Partial<{
    bodyFamily: string;
    monoFamily: string;
    hero: number;
    title: number;
    body: number;
    label: number;
    caption: number;
  }>;
  spacing?: Partial<{
    safeX: number;
    safeTop: number;
    safeBottom: number;
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  }>;
  radius?: Partial<{card: number; media: number; pill: number}>;
  shadow?: Partial<{card: string; media: string}>;
  texture?: Partial<{gridSize: number; grainOpacity: number}>;
  motion?: Partial<{entranceSec: number; transitionSec: number; poseSlideSec: number}>;
};

export type VideoPlan = {
  version: 1;
  video: {
    id: string;
    fps: number;
    width: number;
    height: number;
    timingMode: TimingMode;
    durationSec: number;
    background?: string;
  };
  style: {
    theme: string;
    fontFamily: string;
    accent: string;
    tokens?: ThemeTokens;
    motion?: {
      pace?: 'slow' | 'medium' | 'fast';
      entranceSec?: number;
      transitionSec?: number;
    };
  };
  voice?: {
    mode: 'single' | 'per-beat';
    tracks: VoiceTrack[];
  };
  scenes: ScenePlan[];
  stage?: {
    subject: StageSubject;
    poses?: Record<string, StagePoseTarget>;
    backdrop?: string;
  };
  poses?: StagePose[];
  effects?: EffectPlan[];
  captions?: {
    mode?: 'plain' | 'word-highlight';
    style?: string;
    combineTokensWithinMs?: number;
    cues?: CaptionCue[];
  };
  audio?: {
    bgm?: {src: string; volume?: number; loop?: boolean};
    cues?: Array<{
      src: string;
      atSec: number;
      durationSec?: number;
      volume?: number;
    }>;
  };
};
