# Effect Registry

This registry maps scene needs to reusable effects, skills, and component banks. Do not copy external implementations into this skill.

| Entry | Use when | Avoid when | Good scene types | Typical duration | Required inputs | Fallback |
|---|---|---|---|---|---|---|
| vibe-motion/claude-typer | Terminal or coding-agent prompt typing is the main visual | The scene needs a full IDE or browser workflow | terminal, code-demo, caption-focus | 3-12s | prompt text, terminal title, theme | HyperFrames terminal mockup or Remotion code component |
| vibe-motion/wechat-2d-render | Dialogue or social chat opens the narrative | The content is not conversational | chat, contrast, setup | 3-15s | speaker names, messages, timing | HyperFrames chat UI or Remotion chat component |
| vibe-motion/svg-assembly-animator | Architecture, workflow, logo, or system relationship should assemble dynamically | The diagram is too dense or purely textual | diagram, graph, architecture | 4-20s | SVG or structured nodes | GSAP DrawSVG or Remotion SVG |
| vibe-motion/pixel2motion | A screenshot, icon, or logo must become a motion-ready SVG | The source image has unclear rights or too much detail | logo reveal, UI identity | 3-12s | image path, brand intent | Manual SVG redraw or simple mask reveal |
| vibe-motion/light-spotlight-render | Title or keyword reveal needs a dramatic light sweep | The preset is sober developer UI | kinetic-title, punchline | 2-8s | text, background, light params | GSAP opacity and blur reveal |
| vibe-motion/ruler-progress-render | Steps, routes, progress, or milestones need visual measurement | The topic is not sequential | timeline, progress, process | 4-12s | labels, progress values | Remotion timeline or SVG path growth |
| vibe-motion/disney-animation-rule-skill | Animation feels stiff, weightless, or PPT-like | Reviewing static graphic design only | QA, motion polish | N/A | preview, source, symptom | Manual motion critique |
| vibe-motion/threejs-earth-render | Global route, network, city, or tech-world metaphor is useful | The video is local developer workflow | 3D globe, network intro | 4-15s | cities/routes/theme | Three.js custom scene or map diagram |
| vibe-motion/remotion-3d-ticker | Case wall, app wall, image wall, or repeated examples need 3D depth | The images are not available or not licensed | 3D ticker, proof, examples | 5-20s | images, columns, direction | Remotion carousel or CSS 3D stack |
| HyperFrames Catalog captions | Kinetic subtitles or per-word emphasis are central | Captions would cover the main object | caption-focus, explainer | whole video or scene | transcript, timing, style | Remotion captions |
| HyperFrames code animations | Code snippets need animated focus quickly | The demo needs real IDE interaction | code-demo, terminal | 3-15s | code, highlights, timing | Remotion code component |
| HyperFrames social overlays | Tweets, posts, quote cards, or social proof are needed | It becomes a fake screenshot without context | social overlay, proof | 3-10s | text, handle, style | Remotion card component |
| HyperFrames shader transitions | Section changes need a strong visual break | The style preset is restrained | transition, motif shift | 0.5-2s | colors, transition type | Remotion transition |
| HyperFrames data-viz components | A quick chart or stat visual must be previewed fast | Data needs complex interaction or reuse | data-viz, dashboard | 3-12s | data, labels | Remotion chart |
| GSAP timeline / stagger / CustomEase | Multiple elements need choreographed motion | Single trivial fade only | any HTML/SVG scene | any | DOM/SVG targets, timing | CSS keyframes for simple loops |
| GSAP DrawSVG / MorphSVG / MotionPath / ScrambleText | Paths, icons, text, or abstract shapes need expressive motion | Plugin behavior would be overkill | diagram, title, graph | 2-15s | SVG paths or text | Remotion SVG or CSS |
| Remotion captions | Full video subtitle track, word timing, or Studio tuning is needed | Single standalone caption shot | captions, long timeline | whole video | transcript or SRT | HyperFrames captions |
| Remotion charts | Data-driven charts need React structure and reuse | One tiny static stat can be HTML | chart, data-viz, dashboard | 4-20s | data, chart type | HyperFrames data-viz |
| Remotion SVG / Canvas / Three.js | Complex visual system, particles, or 3D needs timeline control | The effect is a one-off HTML shot | graph, 3D, simulation | 5-30s | props, data, assets | HyperFrames or custom Three.js |
| Remotion Studio props | Human needs to tune timing, colors, layout, or data | No iterative visual editing is expected | reusable scenes | any | prop schema, default props | JSON config plus rerender |
| Remotion Bits | Ready-made Remotion components such as animated text, charts, or transitions fit | The component style conflicts with the preset | component bank | 2-20s | props, data | Custom Remotion component |
| RemotionUI | Polished Remotion UI components are needed | The video is not UI-heavy | UI mockup, cards | 3-20s | props, theme | HyperFrames UI |
| remotion-scenes | Professional scene bank accelerates common motion graphics | The scene requires a unique visual metaphor | title, text, shapes, transitions | 2-15s | scene props | Custom scene |
| Locomotion | SaaS, product tour, data viz, or text template fits | The shot needs a custom director metaphor | product, data-viz, text | 3-20s | template props | Remotion custom |
| ReactVideoEditor templates | A Remotion template can provide structure | Template import would outweigh value | template-backed scenes | 5-30s | template, assets | Remotion scaffold |
| SwiftClip | Short Remotion clip patterns fit a social video | The project needs deep custom design | short-form clip | 3-20s | content, style | Remotion custom |
