import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


script_path = Path(__file__).resolve().parents[1] / "scripts" / "prepare_mlgo.py"
module_spec = importlib.util.spec_from_file_location("prepare_mlgo", script_path)
prepare_mlgo = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(prepare_mlgo)


class mlgo_tests(unittest.TestCase):
    def test_disabled_option_does_not_run_an_optimization_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            compiler = Path(directory) / "clang"
            compiler.write_bytes(b"test compiler")
            version = subprocess.CompletedProcess([], 0, "Clang test version\n", "")
            with patch.object(prepare_mlgo.subprocess, "run", return_value=version) as run:
                report = prepare_mlgo.prepare_mlgo(compiler, False, Path(directory) / "missing_config")
            self.assertFalse(report["enabled"])
            self.assertEqual(report["cflags"], [])
            self.assertEqual(run.call_count, 1)

    def test_lto_and_unsupported_models_cannot_claim_mlgo_is_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            compiler = Path(directory) / "clang"
            compiler.write_bytes(b"test compiler")
            config = Path(directory) / "kernel_config"
            version = subprocess.CompletedProcess([], 0, "Clang test version\n", "")
            config.write_text("CONFIG_LTO_CLANG_THIN=y\n")
            with patch.object(prepare_mlgo.subprocess, "run", return_value=version) as run:
                with self.assertRaisesRegex(ValueError, "LTO"):
                    prepare_mlgo.prepare_mlgo(compiler, True, config)
                self.assertEqual(run.call_count, 1)
            config.write_text("CONFIG_LTO_NONE=y\n")
            baseline = subprocess.CompletedProcess([], 0, "", "")
            unsupported = subprocess.CompletedProcess([], 1, "", "release model is not compiled")
            with patch.object(prepare_mlgo.subprocess, "run", side_effect=[version, baseline, unsupported]):
                with self.assertRaisesRegex(ValueError, "release model is not compiled"):
                    prepare_mlgo.prepare_mlgo(compiler, True, config)


if __name__ == "__main__":
    unittest.main()
