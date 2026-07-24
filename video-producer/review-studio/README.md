# Review Studio

Review Studio 是 Video Producer 的人/代理评审面。处处使用同一 `outputs/` 契约——静态包与完整本地应用都读 `outputs/beat_plan.json`。

## 静态评审

在视频项目目录下：

```bash
python <skill>/scripts/score_preview_plan.py --outputs outputs
python <skill>/scripts/build_review_bundle.py --outputs outputs
```

打开：

```text
outputs/review/review-studio/index.html
```

## 完整本地应用

用于交互式拍编辑、TTS 生成与时间线检查：

```bash
pip install -r review-studio/requirements.txt
python review-studio/server/main.py --project D:\videos\my-project --port 8787
```

打开 [http://127.0.0.1:8787](http://127.0.0.1:8787)。

## 数据契约

| 文件 | 角色 |
|------|------|
| `outputs/beat_plan.json` | **SSOT** — voice_text、keyword、visual_owner、visual_action |
| `outputs/segment_spec.json` | 镜头、visual_actions、渲染器委派 |
| `outputs/script.md` | 长稿；拍编辑时同步 voice 块 |
| `segments/{seg}/vo_timing.json` | 测得的 TTS 时长（运行时） |
| `audio/stems/voice/beats/{beat_id}.wav` | TTS stems |
| `outputs/review/preview.mp4` | 首片预览 |

拍读写集中在 `scripts/beat_store.py`。没有遗留的 `script/narration_beats.csv` 路径。

## Agent 规则

直接生成与编辑 `outputs/beat_plan.json`。计划变更后跑 `build_review_bundle.py`。用户需要 TTS 或实时拍编辑时用完整应用。
