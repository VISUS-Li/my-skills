import React, {useMemo} from 'react';
import {
  AbsoluteFill,
  Easing,
  Html5Video,
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useRemotionEnvironment,
  useVideoConfig,
} from 'remotion';
import {resolveTheme} from './theme';
import type {
  ScenePlan,
  StagePose,
  StagePoseTarget,
  StageSubject,
  VideoPlan,
} from './types';
import {CreamDriftBackdrop, GlassCard} from './visuals';

type ResolvedPose = Required<StagePoseTarget>;

const neutralPose: ResolvedPose = {
  scale: 1,
  tx: 0,
  ty: 0,
  insetT: 0,
  insetR: 0,
  insetB: 0,
  insetL: 0,
  radius: 0,
  border: 0,
  shadow: 0,
  background: 0,
  gradL: 0,
  gradR: 0,
  opacity: 1,
};

export const defaultStagePoses: Record<string, StagePoseTarget> = {
  full: {},
  center: {
    insetT: 5,
    insetR: 31,
    insetB: 74,
    insetL: 31,
    radius: 28,
    border: 1,
    shadow: 1,
    background: 0.6,
  },
  'close-left': {
    insetT: 5,
    insetR: 54,
    insetB: 70,
    insetL: 4,
    radius: 28,
    border: 1,
    shadow: 1,
    background: 0.7,
    gradR: 0.35,
  },
  'close-right': {
    insetT: 5,
    insetR: 4,
    insetB: 70,
    insetL: 54,
    radius: 28,
    border: 1,
    shadow: 1,
    background: 0.7,
    gradL: 0.35,
  },
  'wide-left': {
    scale: 0.94,
    insetT: 7,
    insetR: 64,
    insetB: 74,
    insetL: 4,
    radius: 24,
    border: 1,
    shadow: 1,
    background: 0.65,
  },
  'wide-right': {
    scale: 0.94,
    insetT: 7,
    insetR: 4,
    insetB: 74,
    insetL: 64,
    radius: 24,
    border: 1,
    shadow: 1,
    background: 0.65,
  },
  'card-left': {
    insetT: 12,
    insetR: 54,
    insetB: 12,
    insetL: 4,
    radius: 28,
    border: 1,
    shadow: 1,
    background: 1,
  },
  'card-right': {
    insetT: 12,
    insetR: 4,
    insetB: 12,
    insetL: 54,
    radius: 28,
    border: 1,
    shadow: 1,
    background: 1,
  },
  'offscreen-left': {tx: -120, opacity: 0},
  'offscreen-right': {tx: 120, opacity: 0},
};

const resolvePose = (
  poses: Record<string, StagePoseTarget>,
  name: string,
): ResolvedPose => ({...neutralPose, ...(poses[name] ?? {})});

const lerp = (from: number, to: number, progress: number) =>
  from + (to - from) * progress;

const interpolatePose = (
  from: ResolvedPose,
  to: ResolvedPose,
  progress: number,
): ResolvedPose => ({
  scale: lerp(from.scale, to.scale, progress),
  tx: lerp(from.tx, to.tx, progress),
  ty: lerp(from.ty, to.ty, progress),
  insetT: lerp(from.insetT, to.insetT, progress),
  insetR: lerp(from.insetR, to.insetR, progress),
  insetB: lerp(from.insetB, to.insetB, progress),
  insetL: lerp(from.insetL, to.insetL, progress),
  radius: lerp(from.radius, to.radius, progress),
  border: lerp(from.border, to.border, progress),
  shadow: lerp(from.shadow, to.shadow, progress),
  background: lerp(from.background, to.background, progress),
  gradL: lerp(from.gradL, to.gradL, progress),
  gradR: lerp(from.gradR, to.gradR, progress),
  opacity: lerp(from.opacity, to.opacity, progress),
});

export const poseAt = ({
  frame,
  fps,
  schedule,
  poses,
  transitionSec,
}: {
  frame: number;
  fps: number;
  schedule: StagePose[];
  poses: Record<string, StagePoseTarget>;
  transitionSec: number;
}): ResolvedPose => {
  if (schedule.length === 0) return neutralPose;
  const timeSec = frame / fps;
  let activeIndex = -1;
  for (let index = 0; index < schedule.length; index += 1) {
    if (schedule[index].atSec <= timeSec) activeIndex = index;
    else break;
  }
  if (activeIndex < 0) return resolvePose(poses, schedule[0].pose);
  const active = schedule[activeIndex];
  const previous =
    activeIndex === 0 ? resolvePose(poses, active.pose) : resolvePose(poses, schedule[activeIndex - 1].pose);
  const target = resolvePose(poses, active.pose);
  const duration = active.transitionSec ?? transitionSec;
  const progress =
    duration === 0
      ? 1
      : interpolate(timeSec, [active.atSec, active.atSec + duration], [0, 1], {
          easing: Easing.inOut(Easing.cubic),
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
  return interpolatePose(previous, target, progress);
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
  for (const pose of plan.poses ?? []) entries.set(pose.atSec, pose);
  return [...entries.values()].sort((left, right) => left.atSec - right.atSec);
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
  const fadeSec = Math.max(0.08, Math.min(0.3, plan.style.motion?.entranceSec ?? 0.2));
  const localSec = timeSec - scene.startSec;
  const enter = previousContinues
    ? 1
    : interpolate(localSec, [0, fadeSec], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
  const exit = nextContinues
    ? 1
    : interpolate(localSec, [scene.durationSec - fadeSec, scene.durationSec], [1, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
  return Math.min(enter, exit);
};

const SubjectMedia: React.FC<{subject: StageSubject; plan: VideoPlan}> = ({
  subject,
  plan,
}) => {
  const environment = useRemotionEnvironment();
  const theme = resolveTheme(plan);
  if (subject.type === 'video') {
    const source = environment.isRendering
      ? (subject.masterSrc ?? subject.src ?? subject.proxySrc)
      : (subject.proxySrc ?? subject.src ?? subject.masterSrc);
    if (!source) return null;
    const Footage = environment.isRendering ? OffthreadVideo : Html5Video;
    return (
      <Footage
        src={staticFile(source)}
        muted={(subject.audioMode ?? 'muted') !== 'media'}
        volume={subject.volume ?? 1}
        style={{
          width: '100%',
          height: '100%',
          objectFit: subject.objectFit ?? 'cover',
          objectPosition: subject.objectPosition ?? '50% 50%',
        }}
      />
    );
  }
  if (subject.type === 'image' && subject.src) {
    return (
      <Img
        src={staticFile(subject.src)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: subject.objectFit ?? 'cover',
          objectPosition: subject.objectPosition ?? '50% 50%',
        }}
      />
    );
  }
  return (
    <GlassCard
      theme={theme}
      tone="accent"
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '14px 18px',
        boxSizing: 'border-box',
        textAlign: 'center',
        background:
          subject.background ??
          `linear-gradient(135deg, ${theme.colors.accent}, ${theme.colors.accentAlt})`,
      }}
    >
      <div style={{fontSize: 29, lineHeight: 1.08, fontWeight: 800}}>
        {subject.label ?? 'CONTINUOUS SUBJECT'}
      </div>
      {subject.subtitle ? (
        <div style={{fontSize: 18, lineHeight: 1.25, marginTop: 5, opacity: 0.78}}>
          {subject.subtitle}
        </div>
      ) : null}
    </GlassCard>
  );
};

export const ContinuousSubject: React.FC<{plan: VideoPlan}> = ({plan}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const schedule = useMemo(() => buildPoseSchedule(plan), [plan]);
  const timeSec = frame / fps;
  const visibility = useStageVisibility(plan, timeSec);
  if (!plan.stage?.subject || schedule.length === 0 || visibility <= 0) return null;
  const theme = resolveTheme(plan);
  const poses = {...defaultStagePoses, ...(plan.stage.poses ?? {})};
  const pose = poseAt({
    frame,
    fps,
    schedule,
    poses,
    transitionSec: theme.motion.poseSlideSec,
  });
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <AbsoluteFill style={{opacity: pose.background}}>
        {plan.stage.backdrop ? (
          <AbsoluteFill style={{background: plan.stage.backdrop}} />
        ) : (
          <CreamDriftBackdrop theme={theme} />
        )}
      </AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          top: `${pose.insetT}%`,
          right: `${pose.insetR}%`,
          bottom: `${pose.insetB}%`,
          left: `${pose.insetL}%`,
          borderRadius: pose.radius,
          overflow: 'hidden',
          border: `1.5px solid rgba(255,255,255,${0.2 * pose.border})`,
          boxShadow: `0 28px 72px rgba(0,0,0,${0.5 * pose.shadow})`,
          opacity: visibility * pose.opacity,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            transform: `scale(${pose.scale}) translate(${pose.tx}%, ${pose.ty}%)`,
            transformOrigin: 'center center',
          }}
        >
          <SubjectMedia subject={plan.stage.subject} plan={plan} />
        </div>
      </div>
      <AbsoluteFill
        style={{
          opacity: pose.gradL,
          background:
            'linear-gradient(90deg, rgba(8,9,12,0.78), rgba(8,9,12,0.34) 34%, transparent 56%)',
        }}
      />
      <AbsoluteFill
        style={{
          opacity: pose.gradR,
          background:
            'linear-gradient(270deg, rgba(8,9,12,0.78), rgba(8,9,12,0.34) 34%, transparent 56%)',
        }}
      />
    </AbsoluteFill>
  );
};
