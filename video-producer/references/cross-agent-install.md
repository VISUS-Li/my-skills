# Cross-Agent Installation and Testing

This skill follows the open Agent Skills layout: `SKILL.md` plus optional `scripts/`, `references/`, and `assets/`.

## Recommended Packaging Strategy

Use a two-layer structure:

1. `AGENTS.md` at the repository root for cross-agent project rules and commands.
2. `skills/video-producer/` for the reusable workflow itself.

After the workflow is stable, distribute it as a plugin for clients that support plugins.

## Claude Code

Standalone project skill:

```bash
mkdir -p .claude/skills
cp -R skills/video-producer .claude/skills/video-producer
```

Plugin development layout:

```text
video-factory-plugin/
├── .claude-plugin/plugin.json
└── skills/video-producer/SKILL.md
```

Test locally:

```bash
claude --plugin-dir ./video-factory-plugin
# then try: /video-factory:video-producer plan ...
# after edits: /reload-plugins
```

## Codex

Local skill layout:

```bash
mkdir -p .agents/skills
cp -R skills/video-producer .agents/skills/video-producer
```

Plugin layout:

```text
video-factory-plugin/
├── .codex-plugin/plugin.json
└── skills/video-producer/SKILL.md
```

Minimal `.codex-plugin/plugin.json`:

```json
{
  "name": "video-factory",
  "version": "0.1.0",
  "description": "Controllable video production workflow from idea or media input to script, storyboard, HyperFrames segments, assembly, QC, and publish pack.",
  "skills": "./skills/"
}
```

## Cursor-like Coding Agents

Use `AGENTS.md` plus Cursor project rules as the compatibility fallback. If the client supports open Agent Skills, place the skill under `.agents/skills/video-producer/`. If not, instruct the agent to read `skills/video-producer/SKILL.md` and follow `AGENTS.md`.

Suggested files:

```text
AGENTS.md
.cursor/rules/video-factory.mdc
skills/video-producer/SKILL.md
```

## Trigger Tests

Should trigger:

- "把这个播客做成3条短视频"
- "从这个想法生成一个完整视频脚本和分镜"
- "用 HyperFrames 做第3段对比动态图表"
- "第2段太像PPT，保留口播但重写分镜"
- "生成最终发布包：标题、封面文案、简介、hashtags"

Should not trigger:

- "帮我写一个普通 Python 函数"
- "只总结这篇文章，不做视频"
- "画一张静态图"
- "修复一个无关网页的CSS"
