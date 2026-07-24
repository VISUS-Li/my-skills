from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


VIDEO_PRODUCER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VIDEO_PRODUCER / "scripts"))

from compile_video_plan import compute_duration  # noqa: E402
from build_contact_sheet import sample_rate, tile_rows  # noqa: E402
from validate_video_plan import validate  # noqa: E402


class VideoPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        plan_path = VIDEO_PRODUCER / "assets" / "remotion-template" / "video-plan.json"
        cls.template_plan = json.loads(plan_path.read_text(encoding="utf-8"))

    def plan(self) -> dict:
        return copy.deepcopy(self.template_plan)

    def test_p4_example_is_valid(self) -> None:
        self.assertEqual(validate(self.plan(), VIDEO_PRODUCER, check_assets=False), [])

    def test_stage_subject_is_required_for_pose_schedule(self) -> None:
        plan = self.plan()
        del plan["stage"]
        errors = validate(plan, VIDEO_PRODUCER, check_assets=False)
        self.assertIn("stage.subject is required when poses or scene.pose are used", errors)

    def test_continuous_subject_requires_a_pose_source(self) -> None:
        plan = self.plan()
        plan["poses"] = []
        for scene in plan["scenes"]:
            scene.pop("pose", None)
        errors = validate(plan, VIDEO_PRODUCER, check_assets=False)
        self.assertIn("continuousSubject=true requires poses or scene.pose", errors)

    def test_overlapping_caption_words_are_rejected(self) -> None:
        plan = self.plan()
        words = plan["captions"]["cues"][0]["words"]
        words[1]["startMs"] = words[0]["endMs"] - 1
        errors = validate(plan, VIDEO_PRODUCER, check_assets=False)
        self.assertTrue(
            any("overlaps the preceding word" in error for error in errors),
            errors,
        )

    def test_caption_and_effect_extend_compiled_duration(self) -> None:
        plan = self.plan()
        plan["video"]["durationSec"] = 1
        plan["scenes"] = [
            {
                "id": "short",
                "type": "HookScene",
                "startSec": 0,
                "durationSec": 1,
                "props": {},
            }
        ]
        plan["voice"] = {"mode": "per-beat", "tracks": []}
        plan["captions"]["cues"] = [{"startMs": 0, "endMs": 2400, "text": "caption"}]
        plan["effects"] = [{"type": "KeywordPunch", "atSec": 2.5, "durationSec": 0.75}]
        self.assertEqual(compute_duration(plan), 3.25)

    def test_contact_sheet_layout_has_complete_dimensions(self) -> None:
        self.assertEqual(tile_rows(9, sample_rate("1"), 3), 3)
        self.assertEqual(tile_rows(9.05, sample_rate("1"), 3), 4)
        self.assertEqual(tile_rows(60, sample_rate("1/3"), 5), 4)

    def test_contact_sheet_rejects_invalid_rate(self) -> None:
        with self.assertRaisesRegex(ValueError, "--fps must be positive"):
            sample_rate("0")


if __name__ == "__main__":
    unittest.main()
