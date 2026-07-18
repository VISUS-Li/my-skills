#!/usr/bin/env python3
"""Validate a layered scene plan and compile deterministic Wan generation jobs."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


GENERATED_MODES = {"i2v", "flf2v"}
STATIC_MODES = {"static"}


def slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return clean.strip("_") or "item"


def nearest_4n1(frame_count: float) -> int:
    """Return a valid Wan length close to frame_count (5, 9, 13, ...)."""
    return max(5, 4 * max(1, round((frame_count - 1) / 4)) + 1)


def resolve(root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else root / path


def transform_ok(transform: dict) -> bool:
    for key in ("x", "y", "height", "opacity"):
        if key in transform and not isinstance(transform[key], (int, float)):
            return False
    return True


def compile_plan(plan_path: Path, strict_assets: bool = False) -> tuple[dict, dict]:
    root = plan_path.parent.resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    project = plan.get("project") or {}
    errors: list[str] = []
    warnings: list[str] = []

    fps = int(project.get("fps", 16))
    canvas = project.get("canvas") or [960, 540]
    element_canvas = project.get("element_canvas") or [640, 640]
    if fps <= 0:
        errors.append("project.fps must be positive")
    if len(canvas) != 2 or any(int(v) <= 0 for v in canvas):
        errors.append("project.canvas must be [width, height]")
    if len(element_canvas) != 2 or any(int(v) <= 0 for v in element_canvas):
        errors.append("project.element_canvas must be [width, height]")

    wan_cfg = project.get("wan") or {}
    defaults = {
        "width": int(wan_cfg.get("width", element_canvas[0])),
        "height": int(wan_cfg.get("height", element_canvas[1])),
        "fps": int(wan_cfg.get("fps", fps)),
        "steps": int(wan_cfg.get("steps", 20)),
        "cfg_i2v": float(wan_cfg.get("cfg_i2v", 3.5)),
        "cfg_flf2v": float(wan_cfg.get("cfg_flf2v", 4.0)),
        "seed": int(wan_cfg.get("seed", -1)),
    }

    visual_lock = str(project.get("visual_lock") or "").strip()
    global_negative = str(project.get("negative_prompt") or "").strip()
    compiled = json.loads(json.dumps(plan, ensure_ascii=False))
    jobs: list[dict] = []
    interaction_times: dict[tuple[str, str], list[tuple[str, float, float]]] = {}

    shots = compiled.get("shots") or []
    if not shots:
        errors.append("at least one shot is required")

    for shot_index, shot in enumerate(shots):
        shot_id = slug(str(shot.get("id") or f"shot_{shot_index + 1:02d}"))
        shot["id"] = shot_id
        shot_start = float(shot.get("start_sec", 0.0))
        shot_end = float(shot.get("end_sec", 0.0))
        shot_duration = shot_end - shot_start
        if shot_duration <= 0:
            errors.append(f"{shot_id}: end_sec must be greater than start_sec")
            continue

        background = shot.get("background") or {}
        if background.get("image"):
            bg_path = resolve(root, background["image"])
            if bg_path and not bg_path.exists():
                message = f"{shot_id}: missing background {bg_path}"
                (errors if strict_assets else warnings).append(message)

        element_ids: set[str] = set()
        for element_index, element in enumerate(shot.get("elements") or []):
            element_id = slug(str(element.get("id") or f"element_{element_index + 1:02d}"))
            if element_id in element_ids:
                errors.append(f"{shot_id}: duplicate element id {element_id}")
            element_ids.add(element_id)
            element["id"] = element_id
            identity = str(element.get("identity_lock") or "").strip()
            states = element.get("states") or []
            if not states:
                warnings.append(f"{shot_id}/{element_id}: no states")
                continue

            ordered_states = sorted(states, key=lambda s: float(s.get("start_sec", 0.0)))
            previous_end = -math.inf
            for state_index, state in enumerate(ordered_states):
                state_id = slug(str(state.get("id") or f"state_{state_index + 1:02d}"))
                state["id"] = state_id
                start = float(state.get("start_sec", 0.0))
                end = float(state.get("end_sec", 0.0))
                if start < 0 or end <= start or end > shot_duration + 1e-6:
                    errors.append(
                        f"{shot_id}/{element_id}/{state_id}: state range must fit 0..{shot_duration:.3f}s"
                    )
                    continue
                if start < previous_end - 1e-6:
                    errors.append(f"{shot_id}/{element_id}: overlapping states near {state_id}")
                previous_end = max(previous_end, end)

                for transform_name in ("transform", "transform_from", "transform_to"):
                    transform = state.get(transform_name) or {}
                    if not transform_ok(transform):
                        errors.append(f"{shot_id}/{element_id}/{state_id}: invalid {transform_name}")

                mode = str(state.get("mode") or "i2v").lower()
                if mode not in GENERATED_MODES | STATIC_MODES:
                    errors.append(f"{shot_id}/{element_id}/{state_id}: unsupported mode {mode}")
                    continue

                interaction = state.get("interaction") or {}
                if interaction.get("id"):
                    interaction_times.setdefault((shot_id, str(interaction["id"])), []).append(
                        (element_id, start, end)
                    )

                if mode == "static":
                    image_path = resolve(root, state.get("image") or state.get("start_image"))
                    if image_path and not image_path.exists():
                        message = f"{shot_id}/{element_id}/{state_id}: missing static image {image_path}"
                        (errors if strict_assets else warnings).append(message)
                    continue

                start_image = resolve(root, state.get("start_image"))
                end_image = resolve(root, state.get("end_image"))
                if not start_image:
                    errors.append(f"{shot_id}/{element_id}/{state_id}: start_image is required")
                    continue
                if mode == "flf2v" and not end_image:
                    errors.append(f"{shot_id}/{element_id}/{state_id}: end_image is required for flf2v")
                    continue
                for label, asset in (("start_image", start_image), ("end_image", end_image)):
                    if asset and not asset.exists():
                        message = f"{shot_id}/{element_id}/{state_id}: missing {label} {asset}"
                        (errors if strict_assets else warnings).append(message)

                matte = state.get("matte") or element.get("matte") or {"mode": "chroma", "color": "#00FF00"}
                matte_mode = str(matte.get("mode") or "chroma")
                if matte_mode == "luma":
                    isolation = "纯黑背景，仅保留发光特效；没有人物、没有场景、没有文字。"
                else:
                    key_color = str(matte.get("color") or "#00FF00")
                    isolation = (
                        f"纯色抠像背景 {key_color}，背景颜色完全均匀；单独主体居中；"
                        "没有地面、投影、反射、环境、文字或边框。"
                    )

                camera_lock = (
                    "固定机位，镜头完全静止，不推拉、不平移、不旋转、不变焦；"
                    "主体大小和中心位置稳定，只发生局部动作。"
                )
                motion_prompt = str(state.get("motion_prompt") or "细微自然动作").strip()
                prompt_parts = [visual_lock, identity, motion_prompt, camera_lock, isolation]
                prompt = " ".join(p for p in prompt_parts if p)
                negative = "，".join(
                    p
                    for p in (
                        global_negative,
                        str(element.get("negative_prompt") or "").strip(),
                        str(state.get("negative_prompt") or "").strip(),
                        "镜头运动，多主体，重复肢体，形象漂移，背景纹理，色键渐变，运动模糊，残影",
                    )
                    if p
                )

                job_id = f"{shot_id}__{element_id}__{state_id}"
                source_fps = int(state.get("fps", defaults["fps"]))
                duration = end - start
                length = int(state.get("length") or nearest_4n1(duration * source_fps))
                if (length - 1) % 4 != 0:
                    warnings.append(f"{job_id}: length {length} is not 4n+1")
                raw_video = f"renders/raw/{job_id}.mp4"
                rgba_dir = f"renders/rgba/{job_id}"
                state["job_id"] = job_id
                state["raw_video"] = raw_video
                state["rgba_dir"] = rgba_dir
                state["source_fps"] = source_fps
                state["matte"] = matte
                jobs.append(
                    {
                        "id": job_id,
                        "shot_id": shot_id,
                        "element_id": element_id,
                        "state_id": state_id,
                        "mode": mode,
                        "start_image": str(start_image.resolve()),
                        **(
                            {"end_image": str(end_image.resolve())}
                            if end_image is not None
                            else {}
                        ),
                        "prompt": prompt,
                        "negative_prompt": negative,
                        "width": int(state.get("width", defaults["width"])),
                        "height": int(state.get("height", defaults["height"])),
                        "length": length,
                        "fps": source_fps,
                        "steps": int(state.get("steps", defaults["steps"])),
                        "cfg": float(
                            state.get(
                                "cfg",
                                defaults["cfg_flf2v"] if mode == "flf2v" else defaults["cfg_i2v"],
                            )
                        ),
                        "seed": int(state.get("seed", defaults["seed"])),
                        "output": raw_video,
                        "rgba_dir": rgba_dir,
                        "matte": matte,
                        "pixel_grid": int(
                            matte.get(
                                "pixel_grid",
                                4 if project.get("style_id") == "pixel-8bit" else 1,
                            )
                        ),
                    }
                )

    for contract in plan.get("interaction_contracts") or []:
        contract_id = str(contract.get("id") or "")
        contract_shot = slug(
            str(contract.get("shot_id") or (shots[0].get("id") if len(shots) == 1 else ""))
        )
        if not contract_shot:
            errors.append(f"interaction {contract_id}: shot_id is required when multiple shots exist")
            continue
        participants = set(contract.get("participants") or [])
        event_sec = float(contract.get("event_sec", -1))
        active = interaction_times.get((contract_shot, contract_id), [])
        active_participants = {
            element_id for element_id, start, end in active if start <= event_sec <= end
        }
        missing = participants - active_participants
        if missing:
            warnings.append(
                f"interaction {contract_id}: participants not active at {event_sec}s: {sorted(missing)}"
            )
        if contract.get("contact") == "sustained" and not contract.get("contact_group"):
            errors.append(
                f"interaction {contract_id}: sustained contact requires contact_group"
            )

    report = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "job_count": len(jobs),
        "source": str(plan_path.resolve()),
    }
    if errors:
        return {}, report
    compiled["compiled"] = {
        "source": str(plan_path.resolve()),
        "job_count": len(jobs),
        "notes": "State times are shot-local; global transforms are composited outside Wan.",
    }
    job_doc = {
        "base_url": wan_cfg.get("base_url", "http://10.0.221.33:8090"),
        "source_plan": str(plan_path.resolve()),
        "jobs": jobs,
    }
    return {"scene": compiled, "jobs": job_doc}, report


def main() -> None:
    ap = argparse.ArgumentParser(description="Compile scene_plan.json into Wan jobs")
    ap.add_argument("plan", type=Path)
    ap.add_argument("-o", "--out-dir", type=Path, default=None)
    ap.add_argument("--strict-assets", action="store_true")
    args = ap.parse_args()

    out_dir = args.out_dir or args.plan.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    compiled, report = compile_plan(args.plan, strict_assets=args.strict_assets)
    (out_dir / "compile_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not report["ok"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    (out_dir / "compiled_scene_plan.json").write_text(
        json.dumps(compiled["scene"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "wan_jobs.json").write_text(
        json.dumps(compiled["jobs"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK compiled {report['job_count']} Wan jobs → {out_dir.resolve()}")
    for warning in report["warnings"]:
        print(f"WARN {warning}")


if __name__ == "__main__":
    main()
