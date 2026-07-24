import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {ResolvedTheme} from './theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const grain =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

export const FullBleedBackdrop: React.FC<{
  theme: ResolvedTheme;
  tint?: 'accent' | 'cool';
}> = ({theme, tint = 'accent'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fps;
  const dx = seconds * 8;
  const dy = seconds * -6;
  const tintColor = tint === 'accent' ? theme.colors.accent : theme.colors.accentAlt;
  return (
    <>
      <AbsoluteFill style={{backgroundColor: theme.colors.canvas}} />
      <div
        style={{
          position: 'absolute',
          inset: '-12%',
          background: `radial-gradient(circle at 20% 12%, ${tintColor}44, transparent 34%), linear-gradient(155deg, ${theme.colors.canvasAlt}, ${theme.colors.canvas})`,
          transform: `translate(${dx * 0.4}px, ${dy * 0.4}px)`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${theme.colors.grid} 1px, transparent 1px), linear-gradient(90deg, ${theme.colors.grid} 1px, transparent 1px)`,
          backgroundPosition: `${dx}px ${dy}px`,
          backgroundSize: `${theme.texture.gridSize}px ${theme.texture.gridSize}px`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage: grain,
          backgroundPosition: `${dx * 1.5}px ${dy * 1.5}px`,
          backgroundSize: '180px 180px',
          mixBlendMode: 'soft-light',
          opacity: theme.texture.grainOpacity,
        }}
      />
    </>
  );
};

export const CreamDriftBackdrop: React.FC<{theme: ResolvedTheme}> = ({theme}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const travel = (frame / fps) * 9;
  return (
    <>
      <AbsoluteFill
        style={{
          background: `linear-gradient(145deg, ${theme.colors.creamAlt}, ${theme.colors.cream})`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: '72%',
          aspectRatio: 1,
          left: '-22%',
          top: '8%',
          borderRadius: '50%',
          background: `${theme.colors.accent}20`,
          filter: 'blur(80px)',
          transform: `translate(${travel}px, ${-travel * 0.45}px)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: '60%',
          aspectRatio: 1,
          right: '-18%',
          bottom: '4%',
          borderRadius: '50%',
          background: `${theme.colors.accentAlt}22`,
          filter: 'blur(90px)',
          transform: `translate(${-travel * 0.55}px, ${travel * 0.35}px)`,
        }}
      />
    </>
  );
};

export const GlassCard: React.FC<
  React.PropsWithChildren<{
    theme: ResolvedTheme;
    tone?: 'dark' | 'light' | 'accent';
    style?: React.CSSProperties;
  }>
> = ({children, theme, tone = 'dark', style}) => {
  const palette =
    tone === 'accent'
      ? {background: theme.colors.accent, color: '#FFFFFF', border: '#FFFFFF33'}
      : tone === 'light'
        ? {background: 'rgba(255,255,255,0.72)', color: theme.colors.ink, border: '#FFFFFFCC'}
        : {background: 'rgba(22,24,30,0.68)', color: theme.colors.text, border: '#FFFFFF26'};
  return (
    <div
      style={{
        ...palette,
        border: `1.5px solid ${palette.border}`,
        borderRadius: theme.radius.card,
        boxShadow: theme.shadow.card,
        backdropFilter: 'blur(16px)',
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const SlideIn: React.FC<
  React.PropsWithChildren<{
    delay?: number;
    from?: 'left' | 'right' | 'top' | 'bottom';
    distance?: number;
  }>
> = ({children, delay = 0, from = 'bottom', distance = 48}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - delay;
  const progress = spring({frame: local, fps, config: {damping: 18, mass: 0.7}});
  const opacity = interpolate(local, [0, Math.max(1, fps * 0.35)], [0, 1], clamp);
  const signed = from === 'left' || from === 'top' ? -distance : distance;
  const offset = interpolate(progress, [0, 1], [signed, 0], clamp);
  const transform =
    from === 'left' || from === 'right'
      ? `translateX(${offset}px)`
      : `translateY(${offset}px)`;
  return <div style={{opacity, transform}}>{children}</div>;
};
