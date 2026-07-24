#!/usr/bin/env python3
"""校验分层场景计划并编译确定性 Wan 生成任务。"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


GENERATED_MODES = {"i2v", "flf2v"}
STATIC_MODES = {"static"}
MOTION_SPACES = {"in_place", "locomotion", "hybrid", "compositor"}
HANDOFF_METHODS = {"matched_crossfade", "occlusion", "shared_endpoint"}
BOUNDARY_METHODS = {"occlusion", "designed_transition"}


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


def state_transform(state: dict, endpoint: str) -> dict[str, float]:
    fixed = state.get("transform") or {}
    start = {**fixed, **(state.get("transform_from") or {})}
    end = {**start, **(state.get("transform_to") or {})}
    source = start if endpoint == "start" else end
    return {
        "x": float(source.get("x", 0.5)),
        "y": float(source.get("y", 0.85)),
        "height": float(source.get("height", 0.5)),
        "opacity": float(source.get("opacity", 1.0)),
    }


def position_delta(a: dict[str, float], b: dict[str, float]) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def visibility_seconds(state: dict, key: str) -> float:
    return float((state.get("visibility") or {}).get(key, 0.0))


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
    continuity = project.get("continuity") or {}
    max_position_jump = float(continuity.get("max_position_jump", 0.04))
    max_scale_change = float(continuity.get("max_scale_change", 0.08))
    failure_policy = str(project.get("wan_failure_policy") or "stop-and-replan")
    compiled = json.loads(json.dumps(plan, ensure_ascii=False))
    jobs: list[dict] = []
    interaction_times: dict[tuple[str, str], list[tuple[str, float, float]]] = {}
    shot_elements: dict[str, dict[str, dict]] = {}

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
        shot_elements[shot_id] = {}
        for element_index, element in enumerate(shot.get("elements") or []):
            element_id = slug(str(element.get("id") or f"element_{element_index + 1:02d}"))
            if element_id in element_ids:
                errors.append(f"{shot_id}: duplicate element id {element_id}")
            element_ids.add(element_id)
            element["id"] = element_id
            shot_elements[shot_id][element_id] = element
            identity = str(element.get("identity_lock") or "").strip()
            element_kind = str(element.get("kind") or "actor")
            states = element.get("states") or []
            if not states:
                warnings.append(f"{shot_id}/{element_id}: no states")
                continue

            ordered_states = sorted(states, key=lambda s: float(s.get("start_sec", 0.0)))
            previous_end = -math.inf
            previous_state: dict | None = None
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

                visibility = state.get("visibility") or {}
                for visibility_key in ("fade_in_sec", "fade_out_sec"):
                    value = visibility.get(visibility_key, 0)
                    if not isinstance(value, (int, float)) or float(value) < 0:
                        errors.append(
                            f"{shot_id}/{element_id}/{state_id}: visibility.{visibility_key} must be non-negative"
                        )

                motion_space = str(state.get("motion_space") or "").strip()
                start_transform = state_transform(state, "start")
                end_transform = state_transform(state, "end")
                compositor_travel = position_delta(start_transform, end_transform)
                if motion_space and motion_space not in MOTION_SPACES:
                    errors.append(
                        f"{shot_id}/{element_id}/{state_id}: motion_space must be one of {sorted(MOTION_SPACES)}"
                    )
                if compositor_travel > 0.02 and not motion_space:
                    warnings.append(
                        f"{shot_id}/{element_id}/{state_id}: compositor moves the subject {compositor_travel:.3f}; "
                        "declare motion_space so root-motion ownership is explicit"
                    )
                if motion_space == "in_place" and compositor_travel > 0.02:
                    errors.append(
                        f"{shot_id}/{element_id}/{state_id}: in_place state cannot use compositor travel "
                        f"{compositor_travel:.3f}; encode locomotion in Wan or choose hybrid"
                    )
                if motion_space == "locomotion" and compositor_travel > 0.03:
                    warnings.append(
                        f"{shot_id}/{element_id}/{state_id}: locomotion also has compositor travel "
                        f"{compositor_travel:.3f}; this can read as sliding"
                    )
                if motion_space in {"locomotion", "hybrid"} and not str(
                    state.get("body_mechanics") or ""
                ).strip():
                    errors.append(
                        f"{shot_id}/{element_id}/{state_id}: {motion_space} requires body_mechanics "
                        "describing gait, weight shift, recoil, or another visible body driver"
                    )

                if previous_state is not None:
                    gap = start - float(previous_state.get("end_sec", start))
                    if abs(gap) <= 1e-6:
                        previous_transform = state_transform(previous_state, "end")
                        boundary_position = position_delta(previous_transform, start_transform)
                        previous_height = max(previous_transform["height"], 1e-6)
                        boundary_scale = abs(start_transform["height"] / previous_height - 1.0)
                        boundary = state.get("boundary") or {}
                        if boundary:
                            boundary_method = str(boundary.get("method") or "")
                            if boundary_method not in BOUNDARY_METHODS:
                                errors.append(
                                    f"{shot_id}/{element_id}/{state_id}: boundary.method must be one of "
                                    f"{sorted(BOUNDARY_METHODS)}; use a new shot for a camera cut"
                                )
                            if not boundary.get("mask_element") or not boundary.get("reason"):
                                errors.append(
                                    f"{shot_id}/{element_id}/{state_id}: masked boundary requires "
                                    "mask_element and reason"
                                )
                        if boundary_position > max_position_jump and not boundary:
                            errors.append(
                                f"{shot_id}/{element_id}/{state_id}: boundary position jump "
                                f"{boundary_position:.3f} exceeds {max_position_jump:.3f}"
                            )
                        if boundary_scale > max_scale_change and not boundary:
                            errors.append(
                                f"{shot_id}/{element_id}/{state_id}: boundary scale change "
                                f"{boundary_scale:.1%} exceeds {max_scale_change:.1%}"
                            )
                        previous_end_image = previous_state.get("end_image")
                        current_start_image = state.get("start_image")
                        if (
                            previous_end_image
                            and current_start_image
                            and previous_end_image != current_start_image
                            and not boundary
                        ):
                            warnings.append(
                                f"{shot_id}/{element_id}/{state_id}: boundary images differ; "
                                "reuse the accepted prior end frame or declare a masked boundary"
                            )
                    elif gap > 1e-6:
                        warnings.append(
                            f"{shot_id}/{element_id}: inactive gap {gap:.3f}s before {state_id}; "
                            "a disappearing actor is usually a continuity failure"
                        )
                previous_state = state

                mode = str(state.get("mode") or "i2v").lower()
                if mode not in GENERATED_MODES | STATIC_MODES:
                    errors.append(f"{shot_id}/{element_id}/{state_id}: unsupported mode {mode}")
                    continue
                if mode in GENERATED_MODES and not motion_space:
                    errors.append(
                        f"{shot_id}/{element_id}/{state_id}: generated states require motion_space"
                    )

                interaction = state.get("interaction") or {}
                if interaction.get("id"):
                    interaction_times.setdefault((shot_id, str(interaction["id"])), []).append(
                        (element_id, start, end)
                    )

                if mode == "static":
                    if element_kind in {"actor", "actor_group", "contact_group"} and failure_policy == "stop-and-replan":
                        errors.append(
                            f"{shot_id}/{element_id}/{state_id}: static actor state is forbidden by "
                            "wan_failure_policy=stop-and-replan; use a shot cut or coherent fallback sequence"
                        )
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
                    if motion_space == "locomotion":
                        subject_layout = (
                            "单独主体及其完整运动路径都在画布内；允许按首尾帧真实位移，"
                            "不要自动重新居中；"
                        )
                    elif motion_space == "hybrid":
                        subject_layout = "单独主体与完整动作范围都在画布内；保留设计的有限根位移；"
                    else:
                        subject_layout = "单独主体位于设计位置；"
                    isolation = (
                        f"纯色抠像背景 {key_color}，背景颜色完全均匀；"
                        f"{subject_layout}没有地面、投影、反射、环境、文字或边框。"
                    )

                if motion_space == "locomotion":
                    camera_lock = (
                        "固定机位，镜头完全静止，不跟拍、不重新居中、不推拉或变焦；"
                        "完整身体始终可见，允许主体按首尾帧在元素画布内真实位移。"
                    )
                elif motion_space == "hybrid":
                    camera_lock = (
                        "固定机位，镜头完全静止，不跟拍、不重新居中、不推拉或变焦；"
                        "身体必须完成可见的重心与肢体驱动，允许有限根位移。"
                    )
                else:
                    camera_lock = (
                        "固定机位，镜头完全静止，不推拉、不平移、不旋转、不变焦；"
                        "主体尺度稳定，不发生未经设计的根位移。"
                    )
                motion_prompt = str(state.get("motion_prompt") or "细微自然动作").strip()
                body_mechanics = str(state.get("body_mechanics") or "").strip()
                prompt_parts = [visual_lock, identity, motion_prompt, body_mechanics, camera_lock, isolation]
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
                        "motion_space": motion_space,
                        "body_mechanics": body_mechanics,
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
                        "qa": state.get("qa") or {},
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
        if contract.get("contact") in {"transient", "sustained"} and not contract.get(
            "screen_contact"
        ):
            errors.append(
                f"interaction {contract_id}: screen_contact is required for contact timing/alignment"
            )
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
        handoff = contract.get("handoff") or {}
        if contract.get("contact") == "sustained":
            if not handoff:
                errors.append(
                    f"interaction {contract_id}: sustained contact requires an executable handoff"
                )
                continue
            method = str(handoff.get("method") or "")
            if method not in HANDOFF_METHODS:
                errors.append(
                    f"interaction {contract_id}: handoff.method must be one of {sorted(HANDOFF_METHODS)}"
                )
            from_elements = [slug(str(v)) for v in handoff.get("from_elements") or []]
            to_element = slug(str(handoff.get("to_element") or ""))
            known_elements = shot_elements.get(contract_shot, {})
            missing_elements = set(from_elements + [to_element]) - set(known_elements)
            if missing_elements:
                errors.append(
                    f"interaction {contract_id}: handoff references missing elements {sorted(missing_elements)}"
                )
            window = handoff.get("window_sec") or []
            if len(window) != 2 or float(window[1]) <= float(window[0]):
                errors.append(
                    f"interaction {contract_id}: handoff.window_sec must be [start, end]"
                )
                continue
            window_start, window_end = float(window[0]), float(window[1])
            for tolerance_key, project_limit in (
                ("max_position_delta", max_position_jump),
                ("max_scale_delta", max_scale_change),
            ):
                tolerance = handoff.get(tolerance_key)
                if not isinstance(tolerance, (int, float)) or float(tolerance) <= 0:
                    errors.append(
                        f"interaction {contract_id}: handoff.{tolerance_key} must be positive"
                    )
                elif float(tolerance) > project_limit + 1e-9:
                    errors.append(
                        f"interaction {contract_id}: handoff.{tolerance_key} {float(tolerance):.3f} "
                        f"exceeds project limit {project_limit:.3f}"
                    )
            min_iou = handoff.get("min_silhouette_iou", 0.45)
            if not isinstance(min_iou, (int, float)) or not 0 <= float(min_iou) <= 1:
                errors.append(
                    f"interaction {contract_id}: handoff.min_silhouette_iou must be 0..1"
                )
            if not bool(handoff.get("shared_endpoint")) and method != "occlusion":
                errors.append(
                    f"interaction {contract_id}: matched handoff requires shared_endpoint=true"
                )
            if method == "occlusion" and not handoff.get("mask_element"):
                errors.append(
                    f"interaction {contract_id}: occlusion handoff requires mask_element"
                )
            for outgoing_id in from_elements:
                outgoing = known_elements.get(outgoing_id) or {}
                candidates = [
                    state
                    for state in outgoing.get("states") or []
                    if float(state.get("start_sec", 0)) < window_end
                    and float(state.get("end_sec", 0)) > window_start
                ]
                if not candidates:
                    errors.append(
                        f"interaction {contract_id}: outgoing {outgoing_id} is not active in handoff window"
                    )
                elif method == "matched_crossfade" and not any(
                    visibility_seconds(state, "fade_out_sec") > 0 for state in candidates
                ):
                    errors.append(
                        f"interaction {contract_id}: outgoing {outgoing_id} needs visibility.fade_out_sec"
                    )
            incoming = known_elements.get(to_element) or {}
            incoming_candidates = [
                state
                for state in incoming.get("states") or []
                if float(state.get("start_sec", 0)) < window_end
                and float(state.get("end_sec", 0)) > window_start
            ]
            if not incoming_candidates:
                errors.append(
                    f"interaction {contract_id}: incoming {to_element} is not active in handoff window"
                )
            elif method == "matched_crossfade" and not any(
                visibility_seconds(state, "fade_in_sec") > 0 for state in incoming_candidates
            ):
                errors.append(
                    f"interaction {contract_id}: incoming {to_element} needs visibility.fade_in_sec"
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
        "notes": (
            "State times are shot-local. Wan owns articulated motion and declared root motion; "
            "the compositor owns placement, timing, visibility handoffs, and limited residual transforms."
        ),
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
