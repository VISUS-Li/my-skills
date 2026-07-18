# Wan API reference

Use the configured base URL, default `http://10.0.221.33:8090`. Set
`WAN_BASE_URL` or pass `wan_generate.py --base-url` to override it.

## I2V

`POST /generate/i2v`, `multipart/form-data`:

- `image`: required start frame
- `prompt`: required motion and camera description
- `negative_prompt`: optional
- `width`, `height`: default 640; use multiples of 16
- `length`: default 81; prefer `4n+1`
- `fps`, `steps`, `cfg`, `seed`: defaults 16, 20, 3.5, -1

Use I2V for one stable state: tied idle, defeated breathing, wind loop, guard
motion, glow pulse. Do not ask it to cross several story states.

## FLF2V

`POST /generate/flf2v`, `multipart/form-data`:

- `start_image`: required
- `end_image`: required
- `prompt`: required transition description
- Other fields match I2V; typical `cfg=4.0`

Use FLF2V for a deliberate state transition: guard to slash, upright dragon to
defeated dragon, tied princess to freed princess. Both endpoint frames must use
the same element canvas, scale, viewpoint, palette, and chroma/luma background.
Prefer a Chinese transition prompt.

## Response

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

Download `base_url + video_url`. `scripts/wan_generate.py` performs the call,
download, and request/response metadata capture.

## Connectivity

If the internal endpoint is unreachable from the current machine, the user may
open their documented SSH tunnel separately:

```bash
ssh -L 8090:127.0.0.1:8090 -p 38323 root@10.0.221.33
```

Then use `WAN_BASE_URL=http://127.0.0.1:8090`. Do not start or retain a tunnel
without user authorization.
