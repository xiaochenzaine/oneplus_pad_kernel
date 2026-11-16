import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


scripts_dir = Path(__file__).resolve().parents[1] / "scripts"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, scripts_dir / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare_sukisu = load_script("prepare_sukisu")
optional_patches = load_script("apply_optional_patches")


class test_sukisu_profiles(unittest.TestCase):
    def setUp(self):
        self.profile = prepare_sukisu.load_profile("ultra_41184", "android15-6.6")
        self.badging = "package: name='com.sukisu.ultra' versionCode='41184' versionName='v4.3.0-r2'"
        self.certificates = "Signer #1 certificate SHA-256 digest: " + self.profile["certificate_sha256"]

    def test_only_the_two_requested_implementations_are_available(self):
        config = json.loads(prepare_sukisu.config_path.read_text())
        self.assertEqual(set(config["profiles"]), {"ultra_41184", "resukisu_35203"})
        for name in config["profiles"]:
            for kmi in ["android15-6.6", "android16-6.12"]:
                profile = prepare_sukisu.load_profile(name, kmi)
                self.assertEqual(profile["version_code"], profile["version_base"]
                                 + profile["main_commit_count"] - profile["version_offset"])

    def test_rejects_wrong_apk_package(self):
        with self.assertRaisesRegex(ValueError, "package/version"):
            prepare_sukisu.validate_apk_metadata(self.badging.replace("ultra", "nova"),
                                                 self.certificates, self.profile)

    def test_rejects_wrong_actual_apk_version(self):
        with self.assertRaisesRegex(ValueError, "package/version"):
            prepare_sukisu.validate_apk_metadata(self.badging.replace("41184", "40602"),
                                                 self.certificates, self.profile)

    def test_rejects_unofficial_and_additional_signers(self):
        for certificates in [self.certificates.replace("947ae", "00000"),
                             self.certificates + "\nSigner #2 certificate SHA-256 digest: " + "0" * 64]:
            with self.subTest(certificates=certificates), self.assertRaisesRegex(ValueError, "certificate"):
                prepare_sukisu.validate_apk_metadata(self.badging, certificates, self.profile)

    def test_accepts_locked_official_apk_metadata(self):
        prepare_sukisu.validate_apk_metadata(self.badging, self.certificates, self.profile)

    def test_apk_hash_mismatch_stops_before_any_signature_tool(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(prepare_sukisu, "run_output") as tool:
            apk_path = Path(directory) / "manager.apk"
            apk_path.write_bytes(b"modified apk")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                prepare_sukisu.verify_apk(apk_path, self.profile)
            tool.assert_not_called()

    def test_makefile_lock_retains_compatibility_detection(self):
        source = ("ksu-y := ksu_main.o\nREPO_OWNER  := upstream\n"
                  "KSU_VERSION := $(shell curl upstream)\n"
                  "ccflags-y += -DKSU_VERSION=$(KSU_VERSION)\n"
                  "KSU_PACKAGE_NAME ?= com.sukisu.ultra\n"
                  "ifeq ($(CONFIG_KSU_SUSFS),y)\ninclude compat.mk\nendif\n")
        locked = prepare_sukisu.lock_makefile(source, self.profile)
        self.assertNotIn("shell curl", locked)
        self.assertIn("KSU_VERSION := 41184", locked)
        self.assertTrue(locked.endswith(source[source.index("ccflags-y"):]))

    def test_kbuild_lock_keeps_source_location_and_hook_checks(self):
        profile = prepare_sukisu.load_profile("resukisu_35203", "android15-6.6")
        source = ("KSU_SRC := $(realpath $(src))\n"
                  "$(shell cd $(KSU_SRC); [ -f ../.git/shallow ] && git fetch --unshallow)\n"
                  "KSU_VERSION := $(shell expr 30000 + 4503 + 700)\n"
                  "ccflags-y += -DKSU_VERSION=$(KSU_VERSION)\ninclude $(KSU_SRC)/tools/inline_hook_check.mk\n")
        locked = prepare_sukisu.lock_makefile(source, profile)
        self.assertIn("KSU_SRC := $(realpath $(src))", locked)
        self.assertIn("KSU_VERSION := 35203", locked)
        self.assertNotIn("fetch --unshallow", locked)
        self.assertIn("include $(KSU_SRC)/tools/inline_hook_check.mk", locked)

    def test_optional_patches_reject_the_wrong_device_before_application(self):
        for args in [("oneplus_pad_3_pro", "6.12.58", False, True, False),
                     ("oneplus_pad_2_pro", "6.6.57", False, False, True)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                optional_patches.select_patches(*args)

    def test_failed_patch_preflight_does_not_mutate_the_kernel(self):
        with patch.object(optional_patches.subprocess, "run") as run:
            run.side_effect = subprocess.CalledProcessError(1, ["patch", "--dry-run"])
            with self.assertRaises(subprocess.CalledProcessError):
                optional_patches.apply_patch(Path("kernel"), "adios_6_6.patch", 1)
            self.assertEqual(run.call_count, 1)
            self.assertIn("--dry-run", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
