import type {Caption, TikTokPage} from '@remotion/captions';
import {createTikTokStyleCaptions} from '@remotion/captions';
import React, {useMemo} from 'react';
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {CaptionCue, VideoPlan} from './types';

const DEFAULT_PAGE_MS = 1200;

const toCaption = (text: string, startMs: number, endMs: number): Caption => ({
  text,
  startMs,
  endMs,
  timestampMs: null,
  confidence: null,
});

export const cuesToCaptions = (cues: CaptionCue[]): Caption[] =>
  cues.flatMap((cue) => {
    if (cue.words?.length) {
      return cue.words.map((word) => toCaption(word.text, word.startMs, word.endMs));
    }
    return [toCaption(cue.text, cue.startMs, cue.endMs)];
  });

export const markCaptionPageBreaks = (captions: Caption[], pageMs: number): Caption[] => {
  let pageStartMs: number | null = null;
  let previousEndMs = 0;
  return captions.map((caption) => {
    const startsWithPunctuation = /^[，。！？、；：,.!?;:]/u.test(caption.text.trimStart());
    const shouldBreak =
      pageStartMs !== null &&
      previousEndMs - pageStartMs > pageMs &&
      !startsWithPunctuation;
    if (pageStartMs === null || shouldBreak) pageStartMs = caption.startMs;
    previousEndMs = caption.endMs;
    return shouldBreak && !caption.text.startsWith(' ')
      ? {...caption, text: ` ${caption.text}`}
      : caption;
  });
};

const CaptionPage: React.FC<{
  page: TikTokPage;
  mode: 'plain' | 'word-highlight';
  plan: VideoPlan;
}> = ({page, mode, plan}) => {
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const absoluteTimeMs = page.startMs + (frame / fps) * 1000;
  const enterFrames = Math.max(1, Math.round(fps * 0.12));
  const fontSize = Math.max(34, Math.round(42 * (width / 1080)));

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        padding: '0 80px 105px',
        boxSizing: 'border-box',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          opacity: interpolate(frame, [0, enterFrames], [0, 1], {
            easing: Easing.bezier(0.16, 1, 0.3, 1),
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          maxWidth: '100%',
          padding: '20px 30px',
          borderRadius: 24,
          background: '#0A0C11E8',
          border: '1px solid #FFFFFF26',
          color: '#FFFFFF',
          fontFamily: plan.style.fontFamily,
          fontSize,
          fontWeight: 800,
          lineHeight: 1.35,
          textAlign: 'center',
          whiteSpace: 'pre-wrap',
          boxShadow: '0 16px 50px #00000055',
        }}
      >
        {page.tokens.map((token, index) => {
          const active =
            mode === 'word-highlight' &&
            token.fromMs <= absoluteTimeMs &&
            token.toMs > absoluteTimeMs;
          return (
            <span
              key={`${token.fromMs}-${token.toMs}-${index}`}
              style={{
                color: active ? plan.style.accent : '#FFFFFF',
                textShadow: active ? `0 0 24px ${plan.style.accent}88` : 'none',
              }}
            >
              {token.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const CaptionTrack: React.FC<{plan: VideoPlan}> = ({plan}) => {
  const {fps} = useVideoConfig();
  const cues = plan.captions?.cues ?? [];
  const pageMs = Math.max(250, plan.captions?.combineTokensWithinMs ?? DEFAULT_PAGE_MS);
  const mode = plan.captions?.mode ?? 'plain';
  const captions = useMemo(
    () => markCaptionPageBreaks(cuesToCaptions(cues), pageMs),
    [cues, pageMs],
  );
  const pages = useMemo(
    () =>
      createTikTokStyleCaptions({
        captions,
        combineTokensWithinMilliseconds: pageMs,
      }).pages,
    [captions, pageMs],
  );

  return (
    <>
      {pages.map((page, index) => {
        const nextPage = pages[index + 1];
        const lastTokenEnd = page.tokens.reduce(
          (latest, token) => Math.max(latest, token.toMs),
          page.startMs,
        );
        const endMs = Math.min(
          nextPage?.startMs ?? plan.video.durationSec * 1000,
          Math.max(lastTokenEnd, page.startMs + pageMs),
        );
        const from = Math.max(0, Math.round((page.startMs / 1000) * fps));
        const durationInFrames = Math.max(1, Math.round(((endMs - page.startMs) / 1000) * fps));

        return (
          <Sequence
            key={`${page.startMs}-${index}`}
            from={from}
            durationInFrames={durationInFrames}
            name={`caption-page:${index + 1}`}
          >
            <CaptionPage page={page} mode={mode} plan={plan} />
          </Sequence>
        );
      })}
    </>
  );
};
