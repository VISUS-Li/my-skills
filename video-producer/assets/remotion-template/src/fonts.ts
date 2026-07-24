import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

const latinRange =
  'U+0000-024F,U+1E00-1EFF,U+2000-206F,U+20A0-20CF,U+2100-214F,U+2190-21FF';
const simplifiedChineseRange =
  'U+2E80-2FFF,U+3000-303F,U+3100-312F,U+31A0-31BF,U+3400-4DBF,U+4E00-9FFF,U+F900-FAFF,U+FE30-FE4F,U+FF00-FFEF';

// Load sequentially. Chromium can stall when several subset FontFace objects
// with the same family and weight are registered concurrently.
void (async () => {
  await loadFont({
    family: 'Noto Sans SC',
    url: staticFile('fonts/NotoSansSC-latin-700.woff2'),
    weight: '700',
    unicodeRange: latinRange,
  });
  await loadFont({
    family: 'Noto Sans SC',
    url: staticFile('fonts/NotoSansSC-sc-700.woff2'),
    weight: '700',
    unicodeRange: simplifiedChineseRange,
  });
  await loadFont({
    family: 'Noto Sans SC',
    url: staticFile('fonts/NotoSansSC-latin-800.woff2'),
    weight: '800',
    unicodeRange: latinRange,
  });
  await loadFont({
    family: 'Noto Sans SC',
    url: staticFile('fonts/NotoSansSC-sc-800.woff2'),
    weight: '800',
    unicodeRange: simplifiedChineseRange,
  });
  await loadFont({
    family: 'Space Mono',
    url: staticFile('fonts/SpaceMono-latin-400.woff2'),
    weight: '400',
    unicodeRange: latinRange,
  });
  await loadFont({
    family: 'Space Mono',
    url: staticFile('fonts/SpaceMono-latin-700.woff2'),
    weight: '700',
    unicodeRange: latinRange,
  });
})();
