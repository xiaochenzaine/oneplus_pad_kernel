#!/usr/bin/env python3
"""Check the real build output and preserve source/configuration provenance."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from prepare_sukisu import file_sha256, verify_apk


def read_config(path):
    return dict(re.findall(r"^(CONFIG_\w+)=(.*)$", path.read_text(), re.MULTILINE))


def validate_config(config, device, profile):
    required = {"CONFIG_KSU": "y", "CONFIG_KSU_SUSFS": "y", "CONFIG_SECCOMP": "y",
                "CONFIG_SECCOMP_FILTER": "y", "CONFIG_STACKPROTECTOR_STRONG": "y"}
    for name, expected in required.items():
        if config.get(name) != expected:
            raise ValueError(f"Actual build configuration requires {name}={expected}")
    if device == "oneplus_pad_2_pro" and config.get("CONFIG_TLS_STATS", "n") != "n":
        raise ValueError("Pad 2 Pro A15 requires CONFIG_TLS_STATS=n for the stock layout")
    if profile["source_layout"] == "kbuild":
        if config.get("CONFIG_KSU_TRACEPOINT_HOOK", "n") != "n":
            raise ValueError("ReSukiSU must use the paired SUSFS inline hook")
        if config.get("CONFIG_KSU_MULTI_MANAGER_SUPPORT", "n") != "n":
            raise ValueError("ReSukiSU multi-manager support must remain disabled")


def source_revision(path):
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--platform-dir", type=Path, required=True)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--device", required=True)
    args = parser.parse_args()
    lock_path = args.bundle_dir / "sukisu_lock.json"
    profile = json.loads(lock_path.read_text())
    apk_path = args.bundle_dir / profile["apk"]["name"]
    verify_apk(apk_path, profile)
    config_path = args.out_dir / ".config"
    config = read_config(config_path)
    validate_config(config, args.device, profile)
    # Validate the compiler command, not just the ZIP name or patched source text.
    command_paths = list((args.out_dir / "drivers" / "kernelsu").rglob("*.cmd"))
    version_pattern = rf"-DKSU_VERSION={profile['version_code']}(?:\s|$)"
    if not any(re.search(version_pattern, path.read_text()) for path in command_paths):
        raise ValueError("No compiled SukiSU object command has the selected real version code")
    source_dir = args.platform_dir / "KernelSU"
    if source_revision(source_dir) != profile["builtin_commit"]:
        raise ValueError("Compiled source checkout differs from the selected profile")
    if source_revision(args.platform_dir.parent / "susfs4ksu") != profile["susfs"]["commit"]:
        raise ValueError("SUSFS checkout differs from the selected profile")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    copied_files = []
    for name in [".config", "Module.symvers", "include/config/kernel.release"]:
        source_path = args.out_dir / name
        if source_path.is_file():
            target_name = "kernel_config" if name == ".config" else Path(name).name.lower().replace(".", "_")
            target_path = args.report_dir / target_name
            shutil.copyfile(source_path, target_path)
            copied_files.append({"file": target_name, "sha256": file_sha256(target_path)})
    manifest = {
        "device": args.device, "profile": profile, "workflow_commit": os.environ.get("GITHUB_SHA"),
        "workflow_run": os.environ.get("GITHUB_RUN_ID"),
        "common_commit": source_revision(args.platform_dir / "common"),
        "image_sha256": file_sha256(args.image), "apk_sha256": file_sha256(apk_path),
        "compiled_version_verified": True,
        "configuration": {key: value for key, value in config.items() if key.startswith(
            ("CONFIG_KSU", "CONFIG_SECCOMP", "CONFIG_STACKPROTECTOR", "CONFIG_TLS_STATS",
             "CONFIG_MQ_IOSCHED", "CONFIG_DEFAULT_IOSCHED", "CONFIG_NET_SCH"))},
        "stock_module_abi": "not_verified_against_stock_modules",
        "device_boot_test": "not_performed", "validation_files": copied_files,
        "optional_patches": json.loads((args.bundle_dir / "optional_patches.json").read_text()),
    }
    manifest_text = json.dumps(manifest, indent=2) + "\n"
    (args.report_dir / "build_manifest.json").write_text(manifest_text, encoding="utf-8")
    (args.package_dir / "build_manifest.json").write_text(manifest_text, encoding="utf-8")
    shutil.copyfile(apk_path, args.package_dir / apk_path.name)
    hashes = "\n".join(f"{file_sha256(path)}  {path.relative_to(args.package_dir).as_posix()}"
                       for path in sorted(args.package_dir.rglob("*"))
                       if path.is_file() and path.name != "sha256sums") + "\n"
    (args.package_dir / "sha256sums").write_text(hashes, encoding="utf-8")
    print(f"Verified compiled {profile['profile']}; stock module ABI and device boot remain untested")


if __name__ == "__main__":
    main()
