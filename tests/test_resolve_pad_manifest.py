import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from io import BytesIO


script_path = Path(__file__).resolve().parents[1] / "scripts" / "resolve_pad_manifest.py"
module_spec = importlib.util.spec_from_file_location("resolve_pad_manifest", script_path)
pad_manifest = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(pad_manifest)

manifest_xml = """<manifest>
  <remote name="origin" fetch="https://github.com/OnePlusOSS"/>
  <project remote="origin" name="android_kernel_common_oneplus_sm8750"
    path="kernel_platform/common" revision="oneplus/sm8750_v_15.0.1_pad_2_pro"/>
  <project remote="origin" name="android_kernel_oneplus_sm8750"
    path="kernel_platform/msm-kernel" revision="oneplus/sm8750_v_15.0.1_pad_2_pro"/>
  <project remote="origin" name="android_kernel_modules_and_devicetree_oneplus_sm8750"
    path="./" revision="oneplus/sm8750_v_15.0.1_pad_2_pro"/>
</manifest>"""


class PadManifestTests(unittest.TestCase):
    def test_menu_labels_resolve_to_manifest_filenames(self):
        expected_choices = [
            ("一加Pad 2 Pro A15", "oneplus_pad_2_pro"),
            ("一加Pad 2 Pro A16", "oneplus_pad_2_pro_b"),
            ("一加Pad 3 Pro A16", "oneplus_pad_3_pro"),
        ]
        for label, device in expected_choices:
            with self.subTest(label=label):
                with patch("sys.argv", ["resolve_pad_manifest.py", label]), \
                        patch.dict(os.environ, {"GITHUB_WORKSPACE": ".", "GITHUB_ENV": "env",
                                                "GITHUB_OUTPUT": "output"}), \
                        patch.object(pad_manifest, "resolve_manifest") as resolve:
                    pad_manifest.main()
                self.assertEqual(resolve.call_args.args[0], device)

    def test_accepts_matching_official_manifest(self):
        pad_manifest.validate_manifest(manifest_xml, pad_manifest.device_configs["oneplus_pad_2_pro"])

    def test_rejects_android16_drivers_in_android15_manifest(self):
        xml_text = manifest_xml.replace(
            'path="./" revision="oneplus/sm8750_v_15.0.1_pad_2_pro"',
            'path="./" revision="oneplus/sm8750_b_16.0.0_pad_2_pro"')
        with self.assertRaisesRegex(ValueError, "Unexpected source"):
            pad_manifest.validate_manifest(xml_text, pad_manifest.device_configs["oneplus_pad_2_pro"])

    def test_rejects_missing_common_project(self):
        xml_text = manifest_xml.replace("android_kernel_common_oneplus_sm8750", "wrong_project")
        with self.assertRaisesRegex(ValueError, "Missing official project"):
            pad_manifest.validate_manifest(xml_text, pad_manifest.device_configs["oneplus_pad_2_pro"])

    def test_rejects_unexpected_source_remote(self):
        xml_text = manifest_xml.replace("https://github.com/OnePlusOSS", "https://example.com")
        with self.assertRaisesRegex(ValueError, "Unexpected source"):
            pad_manifest.validate_manifest(xml_text, pad_manifest.device_configs["oneplus_pad_2_pro"])

    def test_rejects_incorrect_project_path(self):
        xml_text = manifest_xml.replace('path="kernel_platform/common"', 'path="wrong/common"')
        with self.assertRaisesRegex(ValueError, "Unexpected source"):
            pad_manifest.validate_manifest(xml_text, pad_manifest.device_configs["oneplus_pad_2_pro"])

    def test_wrong_firmware_does_not_write_build_state(self):
        xml_text = manifest_xml.replace("_v_15.0.1_", "_b_16.0.0_")
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            env_path = workspace / "github_env"
            output_path = workspace / "github_output"
            with patch.object(pad_manifest, "urlopen", return_value=BytesIO(xml_text.encode())):
                with self.assertRaises(ValueError):
                    pad_manifest.resolve_manifest("oneplus_pad_2_pro", workspace, env_path, output_path)
            self.assertEqual(list(workspace.iterdir()), [])

    def test_valid_manifest_exports_canonical_file_for_patch_selection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            env_path = workspace / "github_env"
            output_path = workspace / "github_output"
            with patch.object(pad_manifest, "urlopen", return_value=BytesIO(manifest_xml.encode())):
                pad_manifest.resolve_manifest("oneplus_pad_2_pro", workspace, env_path, output_path)
            self.assertIn("FILE=oneplus_pad_2_pro\n", env_path.read_text(encoding="utf-8"))
            self.assertEqual((workspace / ".repo/manifests_fallback/oneplus_pad_2_pro.xml")
                             .read_text(encoding="utf-8"), manifest_xml)


if __name__ == "__main__":
    unittest.main()
