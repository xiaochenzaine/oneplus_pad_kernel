from pathlib import Path
import unittest


workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "build_oneplus_pad.yml"


class workflow_input_tests(unittest.TestCase):
    def test_hmbird_is_derived_from_device_target(self):
        workflow_text = workflow_path.read_text(encoding="utf-8")
        self.assertNotIn("\n      SCHED_HMBIRD:\n", workflow_text)
        self.assertIn(
            "startsWith(github.event.inputs.FILE, '一加Pad 2 Pro')",
            workflow_text,
        )
        self.assertIn(
            "github.event.inputs.FILE != '一加Pad 3 Pro A16'",
            workflow_text,
        )
        self.assertIn(
            'if [[ "$FILE" != "oneplus_pad_3_pro" ]]; then report_args+=(--require-hmbird); fi',
            workflow_text,
        )


if __name__ == "__main__":
    unittest.main()
