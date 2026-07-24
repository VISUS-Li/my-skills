import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {EffectPlan, VideoPlan} from './types';

const secondsToFrames = (seconds: number, fps: number) => Math.max(0, Math.round(seconds * fps));

export const VoiceTrack: React.FC<{plan: VideoPlan}> = ({plan}) => {
  const {fps} = useVideoConfig();
  return (
    <>
      {(plan.voice?.tracks ?? []).map((track) => (
        <Sequence
          key={track.beatId}
          from={secondsToFrames(track.startSec, fps)}
          durationInFrames={Math.max(1, secondsToFrames(track.durationSec, fps))}
          name={`voice:${track.beatId}`}
        >
          <Audio src={staticFile(track.src)} volume={track.volume ?? 1} />
        </Sequence>
      ))}
    </>
  );
};

const KeywordPunch: React.FC<{effect: EffectPlan; plan: VideoPlan}> = ({effect, plan}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(frame, [0, Math.max(1, fps * 0.22)], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', pointerEvents: 'none'}}>
      <div
        style={{
          opacity: p,
          transform: `scale(${interpolate(p, [0, 1], [1.35, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })}) rotate(-2deg)`,
          color: '#FFFFFF',
          background: plan.style.accent,
          borderRadius: 22,
          padding: '18px 30px',
          fontFamily: plan.style.fontFamily,
          fontSize: 44,
          fontWeight: 900,
          boxShadow: '0 18px 60px #00000055',
        }}
      >
        {String(effect.props?.text ?? '')}
      </div>
    </AbsoluteFill>
  );
};

export const GlobalEffectTrack: React.FC<{plan: VideoPlan}> = ({plan}) => {
  const {fps} = useVideoConfig();
  return (
    <>
      {(plan.effects ?? []).map((effect, index) => {
        if (effect.type !== 'KeywordPunch') return null;
        return (
          <Sequence
            key={`${effect.type}-${effect.atSec}-${index}`}
            from={secondsToFrames(effect.atSec, fps)}
            durationInFrames={Math.max(1, secondsToFrames(effect.durationSec, fps))}
            name={`effect:${effect.type}`}
          >
            <KeywordPunch effect={effect} plan={plan} />
          </Sequence>
        );
      })}
    </>
  );
};

export const SfxTrack: React.FC<{plan: VideoPlan}> = ({plan}) => {
  const {fps} = useVideoConfig();
  return (
    <>
      {(plan.audio?.cues ?? []).map((cue, index) => (
        <Sequence
          key={`${cue.src}-${cue.atSec}-${index}`}
          from={secondsToFrames(cue.atSec, fps)}
          durationInFrames={
            cue.durationSec ? Math.max(1, secondsToFrames(cue.durationSec, fps)) : undefined
          }
          name="sfx"
        >
          <Audio src={staticFile(cue.src)} volume={cue.volume ?? 0.35} />
        </Sequence>
      ))}
    </>
  );
};

export const BgmTrack: React.FC<{plan: VideoPlan}> = ({plan}) => {
  const bgm = plan.audio?.bgm;
  if (!bgm) return null;
  return <Audio src={staticFile(bgm.src)} volume={bgm.volume ?? 0.12} loop={bgm.loop ?? true} />;
};
