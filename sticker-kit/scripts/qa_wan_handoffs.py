#!/usr/bin/env python3
"""度量持续接触交接处：离开侧相对接触组入口的几何。"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from compose_scene import active_state, interpolate_transform, place, state_asset


def render_elements(
    plan: dict,
    shot: dict,
    element_ids: list[str],
    local_time: float,
    root: Path,
) -> Image.Image:
    width, height = [int(value) for value in plan["project"].get("canvas", [960, 540])]
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    elements = {element["id"]: element for element in shot.get("elements") or []}
    fps = int(plan["project"].get("fps", 16))
    default_sampling = "nearest" if plan["project"].get("style_id") == "pixel-8bit" else "smooth"
    for element_id in element_ids:
        element = elements.get(element_id)
        if element is None:
            raise ValueError(f"missing element {element_id}")
        state = active_state(element, local_time)
        if state is None:
            raise ValueError(f"{element_id} is inactive at {local_time:.3f}s")
        duration = float(state["end_sec"]) - float(state["start_sec"])
        progress = min(
            1.0,
            max(0.0, (local_time - float(state["start_sec"])) / max(duration, 1e-6)),
        )
        transform = interpolate_transform(state, progress)
        transform["opacity"] = 1.0
        asset = state_asset(root, state, local_time, fps)
        sampling = state.get("sampling", element.get("sampling", default_sampling))
        place(
            canvas,
            asset,
            transform,
            state.get("anchor", element.get("anchor", "bottom-center")),
            sampling,
        )
    return canvas


def geometry(image: Image.Image, threshold: int = 16) -> tuple[np.ndarray, dict]:
    mask = np.asarray(image.getchannel("A")) > threshold
    ys, xs = np.where(mask)
    if not len(xs):
        raise ValueError("rendered handoff side has no visible pixels")
    width, height = image.size
    left, right = int(xs.min()), int(xs.max()) + 1
    top, bottom = int(ys.min()), int(ys.max()) + 1
    return mask, {
        "bbox": [left, top, right, bottom],
        "center": [(left + right) / (2 * width), (top + bottom) / (2 * height)],
        "height": (bottom - top) / height,
        "width": (right - left) / width,
    }


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / union) if union else 1.0


def main() -> None:
    ap = argparse.ArgumentParser(
        description="QA sustained-contact handoff position, scale, and silhouette continuity"
    )
    ap.add_argument("plan", type=Path, help="compiled_scene_plan.json")
    ap.add_argument("-o", "--out", type=Path, default=None)
    ap.add_argument("--save-overlays", action="store_true")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    root = args.plan.parent.resolve()
    fps = int(plan["project"].get("fps", 16))
    shots = {shot["id"]: shot for shot in plan.get("shots") or []}
    results: list[dict] = []

    for contract in plan.get("interaction_contracts") or []:
        if contract.get("contact") != "sustained":
            continue
        contract_id = str(contract.get("id") or "unnamed")
        shot = shots.get(str(contract.get("shot_id") or ""))
        handoff = contract.get("handoff") or {}
        try:
            if shot is None:
                raise ValueError("missing shot")
            window_start, window_end = [float(value) for value in handoff["window_sec"]]
            epsilon = 0.5 / max(fps, 1)
            outgoing_time = max(window_start, window_end - epsilon)
            incoming_time = min(window_end - epsilon, window_start + epsilon)
            outgoing = render_elements(
                plan,
                shot,
                list(handoff.get("from_elements") or []),
                outgoing_time,
                root,
            )
            incoming = render_elements(
                plan,
                shot,
                [str(handoff.get("to_element"))],
                incoming_time,
                root,
            )
            outgoing_mask, outgoing_geometry = geometry(outgoing)
            incoming_mask, incoming_geometry = geometry(incoming)
            center_delta = math.hypot(
                outgoing_geometry["center"][0] - incoming_geometry["center"][0],
                outgoing_geometry["center"][1] - incoming_geometry["center"][1],
            )
            scale_delta = abs(
                incoming_geometry["height"] / max(outgoing_geometry["height"], 1e-6) - 1.0
            )
            silhouette_iou = mask_iou(outgoing_mask, incoming_mask)
            max_position = float(handoff.get("max_position_delta", 0.04))
            max_scale = float(handoff.get("max_scale_delta", 0.08))
            min_iou = float(handoff.get("min_silhouette_iou", 0.45))
            enforce_shape = handoff.get("method") != "occlusion"
            failures = []
            if center_delta > max_position:
                failures.append(f"center_delta {center_delta:.4f} > {max_position:.4f}")
            if scale_delta > max_scale:
                failures.append(f"scale_delta {scale_delta:.2%} > {max_scale:.2%}")
            if enforce_shape and silhouette_iou < min_iou:
                failures.append(f"silhouette_iou {silhouette_iou:.3f} < {min_iou:.3f}")
            result = {
                "id": contract_id,
                "ok": not failures,
                "outgoing_time_sec": outgoing_time,
                "incoming_time_sec": incoming_time,
                "outgoing": outgoing_geometry,
                "incoming": incoming_geometry,
                "center_delta": center_delta,
                "scale_delta": scale_delta,
                "silhouette_iou": silhouette_iou,
                "limits": {
                    "max_position_delta": max_position,
                    "max_scale_delta": max_scale,
                    "min_silhouette_iou": min_iou,
                },
                "failures": failures,
            }
            if args.save_overlays:
                overlay_dir = root / "renders" / "handoff_qa"
                overlay_dir.mkdir(parents=True, exist_ok=True)
                outgoing.save(overlay_dir / f"{contract_id}__outgoing.png")
                incoming.save(overlay_dir / f"{contract_id}__incoming.png")
                overlay = Image.blend(outgoing, incoming, 0.5)
                overlay.save(overlay_dir / f"{contract_id}__overlay.png")
        except (KeyError, TypeError, ValueError, FileNotFoundError) as exc:
            result = {"id": contract_id, "ok": False, "failures": [str(exc)]}
        results.append(result)

    report = {
        "ok": all(result["ok"] for result in results),
        "source": str(args.plan.resolve()),
        "handoff_count": len(results),
        "results": results,
    }
    out = args.out or (root / "handoff_qa_report.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
