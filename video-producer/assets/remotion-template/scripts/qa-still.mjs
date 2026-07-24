import {spawnSync} from 'node:child_process';
import {mkdirSync, readFileSync} from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const plan = JSON.parse(readFileSync(path.join(root, 'video-plan.json'), 'utf8'));
const fps = plan.video.fps;
const frames = new Set([0, Math.max(0, Math.round(plan.video.durationSec * fps) - 1)]);
for (const scene of plan.scenes) {
  frames.add(Math.round((scene.startSec + scene.durationSec / 2) * fps));
}
const candidates = [...frames].sort((a, b) => a - b);
const sampleIndexes = new Set([0, Math.floor((candidates.length - 1) / 2), candidates.length - 1]);
const sampledFrames = new Set([...sampleIndexes].map((index) => candidates[index]));

for (const pose of (plan.poses ?? []).slice(0, 4)) {
  const transitionSec = pose.transitionSec ?? plan.style?.motion?.transitionSec ?? 0;
  sampledFrames.add(Math.round((pose.atSec + transitionSec / 2) * fps));
}
for (const cue of (plan.captions?.cues ?? []).slice(0, 3)) {
  const words = cue.words ?? [];
  const word = words[Math.floor(words.length / 2)];
  if (word) sampledFrames.add(Math.round((((word.startMs + word.endMs) / 2) / 1000) * fps));
}

mkdirSync(path.join(root, 'renders', 'stills'), {recursive: true});
const remotionCli = path.join(root, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
for (const frame of [...sampledFrames].sort((a, b) => a - b)) {
  const output = path.join('renders', 'stills', `f${String(frame).padStart(5, '0')}.png`);
  const result = spawnSync(
    process.execPath,
    [remotionCli, 'still', 'MasterVideo', output, `--frame=${frame}`, '--scale=0.5'],
    {cwd: root, stdio: 'inherit'},
  );
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
