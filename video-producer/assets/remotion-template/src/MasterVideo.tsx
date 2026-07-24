import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {CaptionTrack} from './captions';
import {SceneRenderer} from './scenes';
import {ContinuousSubject} from './stage';
import {BgmTrack, GlobalEffectTrack, SfxTrack, VoiceTrack} from './tracks';
import type {VideoPlan} from './types';

const frames = (seconds: number, fps: number) => Math.max(0, Math.round(seconds * fps));

const SceneTrack: React.FC<{plan: VideoPlan}> = ({plan}) => {
  const {fps} = useVideoConfig();
  return (
    <>
      {plan.scenes.map((scene) => (
        <Sequence
          key={scene.id}
          from={frames(scene.startSec, fps)}
          durationInFrames={Math.max(1, frames(scene.durationSec, fps))}
          name={`${scene.id}:${scene.type}`}
        >
          <SceneRenderer scene={scene} plan={plan} />
        </Sequence>
      ))}
    </>
  );
};

export const MasterVideo: React.FC<VideoPlan> = (plan) => (
  <AbsoluteFill style={{backgroundColor: plan.video.background ?? '#171A22'}}>
    <SceneTrack plan={plan} />
    <ContinuousSubject plan={plan} />
    <GlobalEffectTrack plan={plan} />
    <CaptionTrack plan={plan} />
    <VoiceTrack plan={plan} />
    <SfxTrack plan={plan} />
    <BgmTrack plan={plan} />
  </AbsoluteFill>
);
