import React from 'react';
import {Composition} from 'remotion';
import {z} from 'zod';
import rawPlan from '../video-plan.json';
import {MasterVideo} from './MasterVideo';
import type {VideoPlan} from './types';

const sceneSchema = z
  .object({
    id: z.string(),
    type: z.string(),
    startSec: z.number().nonnegative(),
    durationSec: z.number().positive(),
    beatIds: z.array(z.string()).optional(),
    pose: z.string().optional(),
    continuousSubject: z.boolean().optional(),
    props: z.record(z.string(), z.any()),
  })
  .passthrough();

export const videoPlanSchema = z
  .object({
    version: z.literal(1),
    video: z
      .object({
        id: z.string(),
        fps: z.number().positive(),
        width: z.number().int().positive(),
        height: z.number().int().positive(),
        timingMode: z.enum(['voice', 'music', 'fixed']),
        durationSec: z.number().positive(),
        background: z.string().optional(),
      })
      .passthrough(),
    style: z
      .object({
        theme: z.string(),
        fontFamily: z.string(),
        accent: z.string(),
      })
      .passthrough(),
    scenes: z.array(sceneSchema).min(1),
  })
  .passthrough();

const defaultPlan = rawPlan as VideoPlan;
const durationInFrames = (plan: VideoPlan) =>
  Math.max(1, Math.round(plan.video.durationSec * plan.video.fps));

export const RemotionRoot: React.FC = () => (
  <Composition
    id="MasterVideo"
    component={MasterVideo}
    schema={videoPlanSchema}
    defaultProps={defaultPlan}
    fps={defaultPlan.video.fps}
    width={defaultPlan.video.width}
    height={defaultPlan.video.height}
    durationInFrames={durationInFrames(defaultPlan)}
    calculateMetadata={({props}) => {
      const plan = props as VideoPlan;
      return {
        durationInFrames: durationInFrames(plan),
        fps: plan.video.fps,
        width: plan.video.width,
        height: plan.video.height,
      };
    }}
  />
);
