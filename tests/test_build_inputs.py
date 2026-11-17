import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts_dir))
module_spec = importlib.util.spec_from_file_location("validate_build_inputs", scripts_dir / "validate_build_inputs.py")
build_inputs = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(build_inputs)


class build_input_tests(unittest.TestCase):
    def test_each_device_accepts_original_system_memory_settings(self):
        for target in build_inputs.device_choices:
            with self.subTest(target=target):
                report = build_inputs.validate_build_inputs({"pad_target": target})
                self.assertFalse(report["zram"]["custom"])
                self.assertEqual(report["zram_config"], "system")

    def test_dropdown_profiles_resolve_algorithm_and_capacity_for_both_pad_2_targets(self):
        for target in ["一加Pad 2 Pro A15", "一加Pad 2 Pro A16"]:
            for algorithm in ["lz4kd", "lz4"]:
                for size_gib in [4, 8]:
                    profile = f"{algorithm.upper()} / {size_gib} GiB"
                    with self.subTest(target=target, profile=profile):
                        report = build_inputs.validate_build_inputs({
                            "pad_target": target, "zram_profile": profile})
                        self.assertEqual(report["zram"], {
                            "custom": True, "algorithm": algorithm, "size_bytes": size_gib * 2 ** 30})
                        self.assertEqual(report["zram_config"], f"1/{algorithm}/{size_gib * 2 ** 30}")

    def test_unknown_or_conflicting_profile_is_rejected(self):
        for options in [{"zram_profile": "LZ4KD / 16 GiB"},
                        {"zram_profile": "LZ4 / 4 GiB", "zram": "1/lz4kd/8589934592"}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                build_inputs.validate_build_inputs({"pad_target": "一加Pad 2 Pro A15", **options})

    def test_pad_2_can_request_both_options_without_claiming_runtime_validation(self):
        for target in ["一加Pad 2 Pro A15", "一加Pad 2 Pro A16"]:
            with self.subTest(target=target):
                report = build_inputs.validate_build_inputs({
                    "pad_target": target, "zram": "1/lz4kd/8589934592", "lz4_update": True})
                self.assertEqual(report["zram"]["algorithm"], "lz4kd")
                self.assertEqual(report["zram"]["size_bytes"], 8589934592)
                self.assertEqual(report["zram_lz4_combination"], "device_test_required")

    def test_pad_3_rejects_each_unavailable_option(self):
        for options in [{"zram": "1/lz4kd/8589934592"},
                        {"zram_profile": "LZ4KD / 8 GiB"}, {"lz4_update": True}]:
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, "Pad 3 Pro"):
                build_inputs.validate_build_inputs({"pad_target": "一加Pad 3 Pro A16", **options})

    def test_old_zero_setting_preserves_system_zram(self):
        report = build_inputs.validate_build_inputs({
            "pad_target": "一加Pad 3 Pro A16", "zram": "0/lz4kd/8589934592"})
        self.assertFalse(report["zram"]["custom"])

    def test_invalid_zram_is_rejected_before_shell_use(self):
        for value in ["1/lz4kd/0", "1/lz4kd/-1", "1/unknown/1024", "1/lz4kd/1;id",
                      "1/lz4kd/1024\n", "1/lz4kd/9223372036854775808", "1/lz4kd", "1/$(id)/1024"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_inputs.parse_zram(value)

    def test_other_device_specific_patches_and_root_pairing_are_checked(self):
        for options in [{"pad_target": "一加Pad 2 Pro A15", "display_fix": True},
                        {"pad_target": "一加Pad 2 Pro A16", "zstd_update": True},
                        {"pad_target": "一加Pad 3 Pro A16", "kpm": "KPM"}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                build_inputs.validate_build_inputs(options)

    def test_failed_cli_does_not_write_a_success_report(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "build_options.json"
            inputs = {"pad_target": "一加Pad 3 Pro A16", "zram": "1/lz4kd/8589934592"}
            result = subprocess.run(
                [sys.executable, str(scripts_dir / "validate_build_inputs.py"), "--report-path", str(report_path)],
                env={**os.environ, "pad_build_inputs": json.dumps(inputs)}, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(report_path.exists())

    def test_cli_exports_stock_and_custom_profiles_to_workflow(self):
        for profile, expected_config, expected_custom in [
                ("原厂配置（推荐）", "system", "false"),
                ("LZ4KD / 8 GiB", "1/lz4kd/8589934592", "true")]:
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                report_path = Path(directory) / "build_options.json"
                output_path = Path(directory) / "github_output"
                summary_path = Path(directory) / "summary.md"
                inputs = {"pad_target": "一加Pad 2 Pro A15", "zram_profile": profile}
                result = subprocess.run(
                    [sys.executable, str(scripts_dir / "validate_build_inputs.py"),
                     "--report-path", str(report_path)],
                    env={**os.environ, "pad_build_inputs": json.dumps(inputs),
                         "GITHUB_OUTPUT": str(output_path), "GITHUB_STEP_SUMMARY": str(summary_path)},
                    capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output_path.read_text(encoding="utf-8").splitlines(), [
                    f"zram_custom={expected_custom}", f"zram_config={expected_config}"])
                self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["zram_config"],
                                 expected_config)
                self.assertIn(profile, summary_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
