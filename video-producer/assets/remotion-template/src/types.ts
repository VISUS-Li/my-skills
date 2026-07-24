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

export type StagePoseName =
  | 'center'
  | 'close-left'
  | 'close-right'
  | 'wide-left'
  | 'wide-right'
  | 'offscreen-left'
  | 'offscreen-right';

export type StagePose = {
  atSec: number;
  pose: StagePoseName;
  transitionSec?: number;
};

export type StageSubject = {
  type?: 'card' | 'image';
  src?: string;
  label?: string;
  subtitle?: string;
  background?: string;
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
