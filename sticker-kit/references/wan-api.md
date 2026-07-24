# Wan API 参考

使用已配置的 base URL，默认 `http://10.0.221.33:8090`。可通过 `WAN_BASE_URL` 或
`wan_generate.py --base-url` 覆盖。这是环境配置，不保证服务一定可用。

## 健康检查与失败行为

`wan_generate.py` 开始前探测 `GET /health`。连接错误或 HTTP 错误会在生成前停止整批。
对 `/health` 返回 404/405 的部署视为未暴露健康路由，可继续生成。
仅在理解该行为时使用 `--skip-health`。

每次生成调用默认重试两次。脚本在每个任务后写入 `wan_run_report.json`，重试耗尽即停止。
已成功的 MP4 在重跑时跳过，服务恢复后可续跑。`--continue-on-error` 记录所有独立失败，
但仍在有失败时以非零退出。

禁止为了赶时间线把失败任务改成 `static` 演员/接触状态。按
[wan-layered-video.md](wan-layered-video.md) 的回退阶梯处理。

## I2V

`POST /generate/i2v`，`multipart/form-data`：

- `image`：必填起始帧
- `prompt`：必填运动与机位描述
- `negative_prompt`：可选
- `width`、`height`：默认 640；用 16 的倍数
- `length`：默认 81；优先 `4n+1`
- `fps`、`steps`、`cfg`、`seed`：默认 16、20、3.5、-1

I2V 用于单一稳定姿态类：呼吸、站定反应、风循环、格挡保持、接触保持。
不要用它代替受控位移端点或多状态故事过渡。

## FLF2V

`POST /generate/flf2v`，`multipart/form-data`：

- `start_image`：必填
- `end_image`：必填
- `prompt`：必填过渡描述
- 其他字段同 I2V；典型 `cfg=4.0`

当位置、接触、剪影或姿态类必须精确落在某状态时用 FLF2V。两端点须同一元素画布、
比例、视角、色板、色键背景与地线。位移时把主体放在共享画布内不同位置并锁定机位；
不要给每个端点回中。

## 响应与下载

```json
{
  "job_id": "e1e503378cad",
  "status": "succeeded",
  "mode": "i2v",
  "video_url": "/videos/e1e503378cad",
  "video_path": "/mnt/comfyui/wan_api/outputs/e1e503378cad.mp4",
  "elapsed_sec": 120.06
}
```

下载 `base_url + video_url`。`wan_generate.py` 保存 MP4、请求、响应与可复现元数据。
失败 job id 留在运行报告中；不要伪造输出文件。

## 连通性

若当前机器访问不到内网端点，用户可自行按其文档开 SSH 隧道：

```bash
ssh -L 8090:127.0.0.1:8090 -p 38323 root@10.0.221.33
```

然后使用 `WAN_BASE_URL=http://127.0.0.1:8090`。未经用户授权不要启动或保留隧道。
