import {spawnSync} from 'node:child_process';
import {existsSync, mkdirSync} from 'node:fs';
import path from 'node:path';

const video = process.argv[2] ?? 'renders/preview.mp4';
const output = process.argv[3] ?? 'renders/contact-sheet.png';
const fps = process.env.CONTACT_SHEET_FPS ?? '1/3';
const columns = Number(process.env.CONTACT_SHEET_COLS ?? 5);
const scale = Number(process.env.CONTACT_SHEET_SCALE ?? 320);

if (!existsSync(video)) throw new Error(`video missing: ${video}`);
if (!Number.isInteger(columns) || columns <= 0) throw new Error('CONTACT_SHEET_COLS must be positive');
if (!Number.isFinite(scale) || scale <= 0) throw new Error('CONTACT_SHEET_SCALE must be positive');

const parts = fps.split('/').map(Number);
const rate = parts.length === 2 ? parts[0] / parts[1] : parts[0];
if (!Number.isFinite(rate) || rate <= 0) throw new Error('CONTACT_SHEET_FPS must be positive');

const probe = spawnSync(
  'ffprobe',
  [
    '-v',
    'error',
    '-select_streams',
    'v:0',
    '-show_entries',
    'stream=duration:format=duration',
    '-of',
    'json',
    video,
  ],
  {encoding: 'utf8'},
);
if (probe.error) throw probe.error;
if (probe.status !== 0) throw new Error(probe.stderr || 'ffprobe failed');
const payload = JSON.parse(probe.stdout);
const duration = Number(payload.streams?.[0]?.duration ?? payload.format?.duration);
if (!Number.isFinite(duration) || duration <= 0) throw new Error('ffprobe returned an invalid duration');

const frames = Math.max(1, Math.ceil(duration * rate));
const rows = Math.ceil(frames / columns);
const filter = [
  `fps=${fps}`,
  `scale=${scale}:-1:force_original_aspect_ratio=decrease`,
  `tile=${columns}x${rows}`,
].join(',');
mkdirSync(path.dirname(path.resolve(output)), {recursive: true});
const render = spawnSync(
  'ffmpeg',
  ['-y', '-i', video, '-vf', filter, '-frames:v', '1', '-update', '1', output],
  {stdio: 'inherit'},
);
if (render.error) throw render.error;
if (render.status !== 0) process.exit(render.status ?? 1);
console.log(`wrote ${output}`);
