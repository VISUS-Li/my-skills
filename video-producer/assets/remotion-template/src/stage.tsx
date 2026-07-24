import React, {useMemo} from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {ScenePlan, StagePose, StagePoseName, VideoPlan} from './types';

type PoseTarget = {
  xPct: number;
  yPct: number;
  widthPct: number;
  scale: number;
  opacity: number;
};

const POSES: Record<StagePoseName, PoseTarget> = {
  center: {xPct: 50, yPct: 8, widthPct: 34, scale: 1, opacity: 1},
  'close-left': {xPct: 24, yPct: 8, widthPct: 30, scale: 1.05, opacity: 1},
  'close-right': {xPct: 76, yPct: 8, widthPct: 30, scale: 1.05, opacity: 1},
  'wide-left': {xPct: 17, yPct: 8, widthPct: 24, scale: 0.9, opacity: 1},
  'wide-right': {xPct: 83, yPct: 8, widthPct: 24, scale: 0.9, opacity: 1},
  'offscreen-left': {xPct: -25, yPct: 8, widthPct: 30, scale: 0.9, opacity: 0},
  'offscreen-right': {xPct: 125, yPct: 8, widthPct: 30, scale: 0.9, opacity: 0},
};

const sceneUsesSubject = (scene: ScenePlan | undefined) =>
  Boolean(scene && (scene.continuousSubject ?? Boolean(scene.pose)));

export const buildPoseSchedule = (plan: VideoPlan): StagePose[] => {
  const entries = new Map<number, StagePose>();
  for (const scene of plan.scenes) {
    if (scene.pose && sceneUsesSubject(scene)) {
      entries.set(scene.startSec, {
        atSec: scene.startSec,
        pose: scene.pose,
        transitionSec: plan.style.motion?.transitionSec ?? 0.55,
      });
    }
  }
  for (const pose of plan.poses ?? []) {
    entries.set(pose.atSec, pose);
  }
  return [...entries.values()].sort((a, b) => a.atSec - b.atSec);
};

const activeSceneIndex = (scenes: ScenePlan[], timeSec: number) =>
  scenes.findIndex(
    (scene) => timeSec >= scene.startSec && timeSec < scene.startSec + scene.durationSec,
  );

const useStageVisibility = (plan: VideoPlan, timeSec: number) => {
  const {fps} = useVideoConfig();
  const index = activeSceneIndex(plan.scenes, timeSec);
  if (index < 0 || !sceneUsesSubject(plan.scenes[index])) return 0;

  const scene = plan.scenes[index];
  const previous = plan.scenes[index - 1];
  const next = plan.scenes[index + 1];
  const tolerance = 1 / fps;
  const previousContinues =
    sceneUsesSubject(previous) &&
    Math.abs(previous.startSec + previous.durationSec - scene.startSec) <= tolerance;
  const nextContinues =
    sceneUsesSubject(next) &&
    Math.abs(scene.startSec + scene.durationSec - next.startSec) <= tolerance;
  const fadeSec = Math.max(0.08, Math.min(0.25, plan.style.motion?.entranceSec ?? 0.2));
  const localSec = timeSec - scene.startSec;
  const enter = previousContinues
    ? 1
    : interpolate(localSec, [0, fadeSec], [0, 1], {
        easing: Easing.bezier(0.16, 1, 0.3, 1),
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
  const exit = nextContinues
    ? 1
    : interpolate(localSec, [scene.durationSec - fadeSec, scene.durationSec], [1, 0], {
        easing: Easing.in(Easing.cubic),
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
  return Math.min(enter, exit);
};

export const ContinuousSubject: React.FC<{plan: VideoPlan}> = ({plan}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const schedule = useMemo(() => buildPoseSchedule(plan), [plan]);
  const timeSec = frame / fps;
  const visibility = useStageVisibility(plan, timeSec);
  if (!plan.stage?.subject || schedule.length === 0 || visibility <= 0) return null;

  let activeIndex = schedule.findIndex((pose) => pose.atSec > timeSec) - 1;
  if (activeIndex < 0) activeIndex = schedule.length - 1;
  if (timeSec < schedule[0].atSec) activeIndex = 0;
  const active = schedule[activeIndex];
  const previous = schedule[Math.max(0, activeIndex - 1)] ?? active;
  const from = POSES[previous.pose];
  const to = POSES[active.pose];
  const transitionFrames = Math.max(0, Math.round((active.transitionSec ?? 0.55) * fps));
  const startFrame = Math.round(active.atSec * fps);
  const progress =
    transitionFrames === 0
      ? 1
      : interpolate(frame, [startFrame, startFrame + transitionFrames], [0, 1], {
          easing: Easing.bezier(0.16, 1, 0.3, 1),
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
  const subject = plan.stage.subject;

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: `${interpolate(progress, [0, 1], [from.xPct, to.xPct])}%`,
          top: `${interpolate(progress, [0, 1], [from.yPct, to.yPct])}%`,
          width: `${interpolate(progress, [0, 1], [from.widthPct, to.widthPct])}%`,
          opacity:
            visibility * interpolate(progress, [0, 1], [from.opacity, to.opacity]),
          translate: '-50% -50%',
          scale: interpolate(progress, [0, 1], [from.scale, to.scale]),
        }}
      >
        {subject.type === 'image' && subject.src ? (
          <Img
            src={staticFile(subject.src)}
            style={{display: 'block', width: '100%', height: 'auto', objectFit: 'contain'}}
          />
        ) : (
          <div
            style={{
              borderRadius: 28,
              padding: '14px 18px',
              background:
                subject.background ??
                `linear-gradient(135deg, ${plan.style.accent}, ${plan.style.accent}BB)`,
              border: '1px solid #FFFFFF55',
              color: '#FFFFFF',
              fontFamily: plan.style.fontFamily,
              textAlign: 'center',
              boxShadow: '0 18px 55px #00000040',
            }}
          >
            <div style={{fontSize: 29, lineHeight: 1.08, fontWeight: 900}}>
              {subject.label ?? 'CONTINUOUS SUBJECT'}
            </div>
            {subject.subtitle ? (
              <div style={{fontSize: 18, lineHeight: 1.25, marginTop: 5, opacity: 0.78}}>
                {subject.subtitle}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
