# 使用示例

## 通用分层叙事（默认动画路径）

用户：`做一个多角色、有接近、互动和状态变化的短过场，Wan 可用`

走 **Mode D-Wan**。先从故事中立模板起步，再把占位演员、状态、端点与契约换成实际 brief。

```bash
python scripts/init_wan_scene.py --template generic --out ./sticker-kit-output/my-story
python scripts/compile_wan_scene.py ./sticker-kit-output/my-story/scene_plan.json
# 按编辑后的计划创建端点图，然后：
python scripts/compile_wan_scene.py ./sticker-kit-output/my-story/scene_plan.json --strict-assets
python scripts/wan_generate.py ./sticker-kit-output/my-story/wan_jobs.json --dry-run
```

生成前，每个状态先回答四个问题：

1. 哪些部件共享移动附着、受力或持续接触？
2. Wan 负责原地表演、位移，还是混合根运动？
3. 该状态结束时，精确位置、缩放、朝向、姿态与接触拓扑是什么？
4. 下一状态如何进入，且不消失、不瞬移、不跳缩放？

## 耦合发射，独立抛体

用户：`角色蓄力后从手中发射能量球，能量球再独立飞向目标`

- 蓄力到释放全程：手/身体 + 成形能量球同一演员组生成。
- 提示词写身体链：站姿、手臂后拉、躯干后坐、掌心张开、释放。
- 释放事件处结束附着球，并从同一屏幕点开始独立抛体层；之后抛体可用合成位移。
- 仅当冲击闪光需要独立时序/遮挡时才另开一层。

错误：静态演员层 + 根点漂离手的独立浮空球。错误：用 `transform_to` 挪演员而手臂/脚仍冻结。

## 持续接触交接

用户：`两个人走近后握手，再并肩离开`

1. 分开时用各自位移片段；每段须在元素画布内表现真实迈步与重心转移。
2. 双方结束于匹配的接触前姿态。
3. 用匹配那两张离开端点的接触前双人图，开两人接触组 FLF2V；由该片段完成握手。
4. 用 2–8 帧匹配交叉淡化（或命名前景遮挡），保持同一中心、缩放、地线、朝向。
5. 手仍相握时保持同组。仅在可见释放事件处再拆开，并再次匹配交接。

错误：3.0s 单人层消失，同刻另一位置出现已握好手的双人组。

## 故事专用示例：战斗与救援

可选 `dragon-rescue` 模板演示一个具体故事；它不是通用架构。

```bash
python scripts/init_wan_scene.py --template dragon-rescue \
  --out ./sticker-kit-output/dragon-rescue
```

可复用的决策：

- 演员与手持武器同组；
- 生物与源绑定吐息同组，使嘴、胸、后坐、翅膀、火焰源点一起生成；
- 脱离的冲击闪光保持独立；
- 接近用位移端点，而非大段合成平移；
- 双人接触组从匹配的接触前帧起步，表演拥抱，而非直接以已合体姿态出现；
- 战败姿态保持同一合成高度，身体在画布内变矮，而不是整层缩小。

## 必需状态中 Wan 中断

用户：`前面的片段生成了，但接触组 job 失败`

不要用一张静帧顶替接触组。保留成功输出，检查 `wan_run_report.json`，选一条连贯恢复：

1. 恢复 Wan 后重跑（已成功任务会跳过）；
2. 简化/重组并重生失败节拍；
3. 把过渡放到有动机的切镜或命名遮挡处；
4. 用连续的 D-Frames 端点整段重做受影响节拍。

若皆不可行，按部分成片报告，不要当最终片。

## 选择 / 切换风格

用户：`用8bit像素风做一只跳跃的猫贴纸动画`
→ Mode D，`style_id=pixel-8bit`，从 [styles.md](styles.md) 锁定 Master。

用户：`换成彩色海克斯`
→ 用 `hex-colorful` **重做锚图**，再派生帧。

## 应避免的连续性失败

错误：道具附着点改变、演员跨状态变大变小，或用硬切静图代替姿态过渡。

修正：共享端点 + 恒定元素画布/变换高度 + 更密状态 + 匹配交接 + 拒绝/重生。
纯图像动画另加部件清单 + 拓扑句 + 双参考（[continuity.md](continuity.md)）。

## 无视频的长动作（D-Long）

用户：`没有视频模型，要做约 120 帧的多阶段技能动作`

走 **Mode D-Long**（[long-action.md](long-action.md)），不要一张全精灵表，也不要用 hold 把八个姿态注水。

```bash
python scripts/init_long_action.py --template generic --out ./sticker-kit-output/my-move
python scripts/expand_stages.py ./sticker-kit-output/my-move/acts.json
```

按幕用双参考生成干净微帧，跑 `qa_frames.py`，生成真实桥接姿态，合并幕次，合成独立特效，只打包通过帧。
`interpolate_sequence.py` 仅预览。
