import React from 'react';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {resolveTheme} from './theme';
import type {ScenePlan, VideoPlan} from './types';
import {CreamDriftBackdrop, FullBleedBackdrop, GlassCard} from './visuals';

type SceneProps = {
  scene: ScenePlan;
  plan: VideoPlan;
};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const stageDelayFrames = (scene: ScenePlan, plan: VideoPlan, fps: number) =>
  scene.pose ? Math.round((plan.style.motion?.transitionSec ?? 0.55) * fps * 0.7) : 0;

const contentColumnStyle = (scene: ScenePlan): React.CSSProperties => {
  const pose = scene.pose ?? '';
  if (pose.includes('left')) return {width: '54%', marginLeft: '46%'};
  if (pose.includes('right')) return {width: '54%', marginRight: '46%'};
  return {};
};

const useEntrance = (plan: VideoPlan, scene: ScenePlan) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const theme = resolveTheme(plan);
  const delay = stageDelayFrames(scene, plan, fps);
  const progress = interpolate(
    frame,
    [delay, delay + Math.max(1, fps * theme.motion.entranceSec)],
    [0, 1],
    clamp,
  );
  return {
    opacity: progress,
    transform: `translateY(${interpolate(progress, [0, 1], [42, 0], clamp)}px)`,
  };
};

const Shell: React.FC<
  React.PropsWithChildren<{plan: VideoPlan; scene?: ScenePlan; tone?: 'dark' | 'light'}>
> = ({
  children,
  plan,
  scene,
  tone = 'dark',
}) => (
  (() => {
    const theme = resolveTheme(plan);
    return (
      <AbsoluteFill style={{overflow: 'hidden'}}>
        {scene && (scene.continuousSubject ?? Boolean(scene.pose)) ? null : tone === 'dark' ? (
          <FullBleedBackdrop theme={theme} />
        ) : (
          <CreamDriftBackdrop theme={theme} />
        )}
        <AbsoluteFill
          style={{
            color: tone === 'dark' ? theme.colors.text : theme.colors.ink,
            fontFamily: theme.typography.bodyFamily,
            padding: `${theme.spacing.safeTop}px ${theme.spacing.safeX}px ${theme.spacing.safeBottom}px`,
            boxSizing: 'border-box',
            overflow: 'hidden',
          }}
        >
          {children}
        </AbsoluteFill>
      </AbsoluteFill>
    );
  })()
);

const HookScene: React.FC<SceneProps> = ({scene, plan}) => {
  const style = useEntrance(plan, scene);
  const theme = resolveTheme(plan);
  const props = scene.props as {eyebrow?: string; title?: string; subtitle?: string};
  return (
    <Shell plan={plan} scene={scene}>
      <div style={{...style, ...contentColumnStyle(scene), marginTop: 250}}>
        <div
          style={{
            fontFamily: theme.typography.monoFamily,
            fontSize: theme.typography.label,
            letterSpacing: 6,
            color: theme.colors.accent,
            fontWeight: 700,
          }}
        >
          {props.eyebrow ?? 'HOOK'}
        </div>
        <div
          style={{
            fontSize: theme.typography.hero,
            lineHeight: 1.02,
            fontWeight: 800,
            marginTop: 34,
          }}
        >
          {props.title ?? 'Hook title'}
        </div>
        {props.subtitle ? (
          <div style={{fontSize: 44, lineHeight: 1.45, opacity: 0.78, marginTop: 38}}>
            {props.subtitle}
          </div>
        ) : null}
      </div>
    </Shell>
  );
};

const TalkScene: React.FC<SceneProps> = ({scene, plan}) => {
  const style = useEntrance(plan, scene);
  const theme = resolveTheme(plan);
  const props = scene.props as {title?: string; body?: string; label?: string};
  return (
    <Shell plan={plan} scene={scene} tone="light">
      <div style={{...style, ...contentColumnStyle(scene), marginTop: 220}}>
        <div
          style={{
            fontFamily: theme.typography.monoFamily,
            fontSize: theme.typography.label,
            color: theme.colors.accent,
            fontWeight: 700,
          }}
        >
          {props.label ?? 'EXPLAIN'}
        </div>
        <div
          style={{
            fontSize: theme.typography.title,
            lineHeight: 1.1,
            fontWeight: 800,
            marginTop: 28,
          }}
        >
          {props.title ?? 'Explanation'}
        </div>
        <div
          style={{
            fontSize: theme.typography.body,
            lineHeight: 1.55,
            marginTop: 48,
            opacity: 0.8,
          }}
        >
          {props.body ?? ''}
        </div>
      </div>
    </Shell>
  );
};

const ListScene: React.FC<SceneProps> = ({scene, plan}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const props = scene.props as {title?: string; items?: string[]; staggerSec?: number};
  const items = props.items ?? [];
  const theme = resolveTheme(plan);
  const contentDelay = stageDelayFrames(scene, plan, fps);
  const contentOpacity = interpolate(frame, [contentDelay, contentDelay + 8], [0, 1], clamp);
  return (
    <Shell plan={plan} scene={scene}>
      <div
        style={{
          ...contentColumnStyle(scene),
          opacity: contentOpacity,
          fontSize: 72,
          fontWeight: 800,
          marginTop: 80,
        }}
      >
        {props.title ?? 'List'}
      </div>
      <div
        style={{
          ...contentColumnStyle(scene),
          display: 'flex',
          flexDirection: 'column',
          gap: 26,
          marginTop: 72,
        }}
      >
        {items.map((item, index) => {
          const delay = contentDelay + index * (props.staggerSec ?? 0.35) * fps;
          const p = interpolate(frame, [delay, delay + fps * 0.35], [0, 1], clamp);
          return (
            <GlassCard
              key={`${item}-${index}`}
              theme={theme}
              style={{
                opacity: p,
                transform: `translateX(${interpolate(p, [0, 1], [70, 0], clamp)}px)`,
                border: `2px solid ${index === 0 ? theme.colors.accent : '#FFFFFF2A'}`,
                padding: '34px 40px',
                fontSize: 46,
                fontWeight: 750,
              }}
            >
              <span
                style={{
                  color: theme.colors.accent,
                  fontFamily: theme.typography.monoFamily,
                  marginRight: 26,
                }}
              >
                {String(index + 1).padStart(2, '0')}
              </span>
              {item}
            </GlassCard>
          );
        })}
      </div>
    </Shell>
  );
};

const CompareScene: React.FC<SceneProps> = ({scene, plan}) => {
  const style = useEntrance(plan, scene);
  const theme = resolveTheme(plan);
  const props = scene.props as {
    title?: string;
    left?: {label?: string; text?: string};
    right?: {label?: string; text?: string};
  };
  const cards = [props.left ?? {}, props.right ?? {}];
  return (
    <Shell plan={plan} scene={scene}>
      <div style={{...style, ...contentColumnStyle(scene), marginTop: 90}}>
        <div style={{fontSize: 70, fontWeight: 900}}>{props.title ?? 'Compare'}</div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 30, marginTop: 70}}>
          {cards.map((card, index) => (
            <GlassCard
              key={index}
              theme={theme}
              tone={index === 1 ? 'accent' : 'dark'}
              style={{
                padding: '50px 44px',
              }}
            >
              <div style={{fontSize: 27, letterSpacing: 4, opacity: 0.75}}>
                {card.label ?? (index === 0 ? 'BEFORE' : 'AFTER')}
              </div>
              <div style={{fontSize: 52, fontWeight: 850, marginTop: 18}}>{card.text ?? ''}</div>
            </GlassCard>
          ))}
        </div>
      </div>
    </Shell>
  );
};

const TimelineScene: React.FC<SceneProps> = ({scene, plan}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const props = scene.props as {title?: string; items?: Array<{label: string; text?: string}>};
  const contentDelay = stageDelayFrames(scene, plan, fps);
  const columnStyle = contentColumnStyle(scene);
  return (
    <Shell plan={plan} scene={scene} tone="light">
      <div style={{...columnStyle, fontSize: 72, fontWeight: 800, marginTop: 70}}>
        {props.title ?? 'Timeline'}
      </div>
      <div style={{...columnStyle, marginTop: 80}}>
        {(props.items ?? []).map((item, index) => {
          const start = contentDelay + index * fps * 0.35;
          const p = interpolate(frame, [start, start + 10], [0, 1], clamp);
          return (
            <div key={index} style={{display: 'flex', gap: 30, minHeight: 150, opacity: p}}>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
                <div style={{width: 30, height: 30, borderRadius: 99, background: plan.style.accent}} />
                {index < (props.items?.length ?? 0) - 1 ? (
                  <div style={{width: 4, flex: 1, background: '#1E202830'}} />
                ) : null}
              </div>
              <div>
                <div style={{fontSize: 40, fontWeight: 850}}>{item.label}</div>
                {item.text ? <div style={{fontSize: 30, opacity: 0.68, marginTop: 10}}>{item.text}</div> : null}
              </div>
            </div>
          );
        })}
      </div>
    </Shell>
  );
};

const MissingMedia: React.FC<{label: string; plan: VideoPlan}> = ({label, plan}) => (
  <Shell plan={plan}>
    <div
      style={{
        margin: 'auto',
        border: `3px dashed ${plan.style.accent}`,
        borderRadius: 30,
        padding: 50,
        fontSize: 40,
        textAlign: 'center',
      }}
    >
      {label}
    </div>
  </Shell>
);

const BrollScene: React.FC<SceneProps> = ({scene, plan}) => {
  const props = scene.props as {src?: string; fit?: 'cover' | 'contain'; muted?: boolean};
  if (!props.src) return <MissingMedia label="B-roll src is missing" plan={plan} />;
  return (
    <AbsoluteFill style={{background: plan.video.background}}>
      <OffthreadVideo
        src={staticFile(props.src)}
        muted={props.muted ?? true}
        style={{width: '100%', height: '100%', objectFit: props.fit ?? 'cover'}}
      />
    </AbsoluteFill>
  );
};

const TransparentImageScene: React.FC<SceneProps> = ({scene, plan}) => {
  const style = useEntrance(plan, scene);
  const props = scene.props as {src?: string; title?: string; widthPct?: number};
  if (!props.src) return <MissingMedia label="Transparent image src is missing" plan={plan} />;
  return (
    <Shell plan={plan} scene={scene}>
      {props.title ? <div style={{fontSize: 62, fontWeight: 900}}>{props.title}</div> : null}
      <Img
        src={staticFile(props.src)}
        style={{
          ...style,
          width: `${props.widthPct ?? 86}%`,
          height: '70%',
          objectFit: 'contain',
          margin: 'auto',
        }}
      />
    </Shell>
  );
};

const ImageSequenceScene: React.FC<SceneProps> = ({scene, plan}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const props = scene.props as {
    prefix?: string;
    suffix?: string;
    startNumber?: number;
    digits?: number;
    imageFps?: number;
    frameCount?: number;
  };
  if (!props.prefix) return <MissingMedia label="Image sequence prefix is missing" plan={plan} />;
  const rawIndex = (props.startNumber ?? 0) + Math.floor((frame / fps) * (props.imageFps ?? fps));
  const index = Math.min(rawIndex, (props.startNumber ?? 0) + Math.max(0, (props.frameCount ?? 1) - 1));
  const src = `${props.prefix}${String(index).padStart(props.digits ?? 4, '0')}${props.suffix ?? '.png'}`;
  return (
    <Shell plan={plan} scene={scene}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
    </Shell>
  );
};

const sceneMap: Record<string, React.FC<SceneProps>> = {
  HookScene,
  TalkScene,
  ListScene,
  CompareScene,
  TimelineScene,
  BrollScene,
  TransparentImageScene,
  ImageSequenceScene,
};

export const SceneRenderer: React.FC<SceneProps> = (props) => {
  const Component = sceneMap[props.scene.type];
  if (!Component) {
    return <MissingMedia label={`Unknown scene type: ${props.scene.type}`} plan={props.plan} />;
  }
  return <Component {...props} />;
};
