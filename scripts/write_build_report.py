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


def validate_config(config, device, profile, require_hmbird=False):
    required = {"CONFIG_KSU": "y", "CONFIG_KSU_SUSFS": "y", "CONFIG_SECCOMP": "y",
                "CONFIG_SECCOMP_FILTER": "y", "CONFIG_STACKPROTECTOR_STRONG": "y"}
    for name, expected in required.items():
        if config.get(name) != expected:
            raise ValueError(f"Actual build configuration requires {name}={expected}")
    if require_hmbird and config.get("CONFIG_HMBIRD_SCHED") != "y":
        raise ValueError("Requested HMBIRD is missing from the actual build configuration")
    if device == "oneplus_pad_2_pro" and config.get("CONFIG_TLS_STATS", "n") != "n":
        raise ValueError("Pad 2 Pro A15 requires CONFIG_TLS_STATS=n for the stock layout")
    if profile["source_layout"] == "kbuild":
        if config.get("CONFIG_KSU_TRACEPOINT_HOOK", "n") != "n":
            raise ValueError("ReSukiSU must use the paired SUSFS inline hook")
        if config.get("CONFIG_KSU_MULTI_MANAGER_SUPPORT", "n") != "n":
            raise ValueError("ReSukiSU multi-manager support must remain disabled")


def source_revision(path):
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def validate_optimizations(build_options, applied_patches, compiler_report, config, command_text):
    requested = build_options.get("requested_inputs", {}) if build_options else {}
    patch_names = {item["file"] for item in applied_patches}
    for name, patch_name in (("mem_prefetch", "mem_prefetch.patch"),
                             ("s2idle_wakeup", "s2idle_wakeup.patch")):
        if requested.get(name, False) != (patch_name in patch_names):
            raise ValueError(f"Requested optimization differs from the applied patch: {name}")
    mlgo_requested = requested.get("mlgo", False)
    if (compiler_report.get("requested", False) != mlgo_requested
            or compiler_report.get("enabled", False) != mlgo_requested):
        raise ValueError("Requested MLGO was not enabled by the verified compiler")
    if mlgo_requested:
        if config.get("CONFIG_LTO_NONE") != "y":
            raise ValueError("MLGO validation currently requires CONFIG_LTO_NONE=y")
        if compiler_report.get("cflags") != ["-mllvm", "-regalloc-enable-advisor=release"]:
            raise ValueError("MLGO compiler report has unexpected flags")
        if not re.search(r"(?:^|\s)-mllvm\s+-regalloc-enable-advisor=release(?:\s|$)", command_text):
            raise ValueError("Compiled root commands do not contain the requested MLGO flags")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--platform-dir", type=Path, required=True)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--require-hmbird", action="store_true")
    parser.add_argument("--inputs-report", type=Path)
    parser.add_argument("--compiler-report", type=Path)
    args = parser.parse_args()
    lock_path = args.bundle_dir / "sukisu_lock.json"
    profile = json.loads(lock_path.read_text())
    apk_path = args.bundle_dir / profile["apk"]["name"]
    verify_apk(apk_path, profile)
    config_path = args.out_dir / ".config"
    config = read_config(config_path)
    validate_config(config, args.device, profile, args.require_hmbird)
    compatibility_path = args.bundle_dir / "root_compatibility_patches.json"
    # Validate the compiler command, not just the ZIP name or patched source text.
    command_paths = list((args.out_dir / "drivers" / "kernelsu").rglob("*.cmd"))
    version_pattern = rf"-DKSU_VERSION={profile['version_code']}(?:\s|$)"
    matching_commands = [path for path in command_paths
                         if re.search(version_pattern, path.read_text())]
    if not matching_commands:
        raise ValueError("No compiled SukiSU object command has the selected real version code")
    source_dir = args.platform_dir / "KernelSU"
    if source_revision(source_dir) != profile["builtin_commit"]:
        raise ValueError("Compiled source checkout differs from the selected profile")
    if source_revision(args.platform_dir.parent / "susfs4ksu") != profile["susfs"]["commit"]:
        raise ValueError("SUSFS checkout differs from the selected profile")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    command_report = args.report_dir / "root_compile_commands"
    command_report.write_text("\n\n".join(
        f"# {path.relative_to(args.out_dir).as_posix()}\n{path.read_text()}"
        for path in sorted(matching_commands)), encoding="utf-8")
    copied_files = [{"file": command_report.name, "sha256": file_sha256(command_report)}]
    build_options = None
    if args.inputs_report:
        build_options = json.loads(args.inputs_report.read_text(encoding="utf-8"))
        if build_options["device"] != args.device:
            raise ValueError("Validated input target differs from the compiled device")
        options_report = args.report_dir / "build_options.json"
        shutil.copyfile(args.inputs_report, options_report)
        copied_files.append({"file": options_report.name, "sha256": file_sha256(options_report)})
    applied_patches = json.loads((args.bundle_dir / "optional_patches.json").read_text())
    compiler_report = {"requested": False, "enabled": False, "status": "not_requested"}
    if args.compiler_report:
        compiler_report = json.loads(args.compiler_report.read_text(encoding="utf-8"))
        compiler_target = args.report_dir / "compiler_optimizations.json"
        shutil.copyfile(args.compiler_report, compiler_target)
        copied_files.append({"file": compiler_target.name, "sha256": file_sha256(compiler_target)})
    validate_optimizations(build_options, applied_patches, compiler_report, config,
                           command_report.read_text(encoding="utf-8"))
    requested = build_options.get("requested_inputs", {}) if build_options else {}
    optimization_commands = []
    for name, source_name, object_dir, report_name in (
            ("mem_prefetch", "arch/arm64/lib/copy_template.S", "arch/arm64/lib", "optimization_copy_template.s"),
            ("s2idle_wakeup", "drivers/base/power/wakeup.c", "drivers/base/power", "optimization_wakeup.c")):
        if not requested.get(name, False):
            continue
        dependencies = [path for path in (args.out_dir / object_dir).glob("*.cmd")
                        if Path(source_name).name in path.read_text()]
        if not dependencies:
            raise ValueError(f"No compiled object references the optimized source: {source_name}")
        optimization_commands.extend(dependencies)
        target_path = args.report_dir / report_name
        shutil.copyfile(args.platform_dir / "common" / source_name, target_path)
        copied_files.append({"file": target_path.name, "sha256": file_sha256(target_path)})
    if optimization_commands:
        target_path = args.report_dir / "optimization_compile_commands"
        target_path.write_text("\n\n".join(
            f"# {path.relative_to(args.out_dir).as_posix()}\n{path.read_text()}"
            for path in sorted(set(optimization_commands))), encoding="utf-8")
        copied_files.append({"file": target_path.name, "sha256": file_sha256(target_path)})
    if profile["profile"] == "ultra_41184":
        hook_report = args.report_dir / "root_lsm_hook.c"
        shutil.copyfile(source_dir / "kernel" / "hook" / "lsm_hook.c", hook_report)
        copied_files.append({"file": hook_report.name, "sha256": file_sha256(hook_report)})
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
        "hmbird_requested": args.require_hmbird,
        "build_options": build_options,
        "compiler_optimizations": compiler_report,
        "configuration": {key: value for key, value in config.items() if key.startswith(
            ("CONFIG_KSU", "CONFIG_SECCOMP", "CONFIG_STACKPROTECTOR", "CONFIG_TLS_STATS",
             "CONFIG_MQ_IOSCHED", "CONFIG_DEFAULT_", "CONFIG_NET_SCH", "CONFIG_HMBIRD",
             "CONFIG_SCHED_CLASS_EXT", "CONFIG_BPF", "CONFIG_DEBUG_INFO_BTF", "CONFIG_ZRAM",
             "CONFIG_CRYPTO_LZ4", "CONFIG_LZ4", "CONFIG_LTO", "CONFIG_CC_VERSION_TEXT"))},
        "stock_module_abi": "not_verified_against_stock_modules",
        "device_boot_test": "not_performed", "validation_files": copied_files,
        "optional_patches": applied_patches,
        "root_compatibility_patches": (json.loads(compatibility_path.read_text())
                                       if compatibility_path.exists() else []),
    }
    manifest_text = json.dumps(manifest, indent=2) + "\n"
    (args.report_dir / "build_manifest.json").write_text(manifest_text, encoding="utf-8")
    (args.package_dir / "build_manifest.json").write_text(manifest_text, encoding="utf-8")
    shutil.copyfile(apk_path, args.package_dir / apk_path.name)
    shutil.copyfile(Path(__file__).with_name("check_seccomp.sh"), args.package_dir / "check_seccomp.sh")
    hashes = "\n".join(f"{file_sha256(path)}  {path.relative_to(args.package_dir).as_posix()}"
                       for path in sorted(args.package_dir.rglob("*"))
                       if path.is_file() and path.name != "sha256sums") + "\n"
    (args.package_dir / "sha256sums").write_text(hashes, encoding="utf-8")
    if summary_path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary_path).open("a", encoding="utf-8") as summary:
            summary.write("## 实际优化检查\n\n")
            for name, label in (("mem_prefetch", "内存拷贝预取"), ("s2idle_wakeup", "待机唤醒去重")):
                summary.write(f"- {label}：{'补丁和编译依赖已核对' if requested.get(name, False) else '关闭'}\n")
            summary.write(f"- MLGO：{'探测及最终编译参数已核对' if compiler_report['enabled'] else '关闭'}\n")
            summary.write("\n以上为构建检查；帧率、功耗及实机兼容性仍需测试。\n")
    print(f"Verified compiled {profile['profile']}; stock module ABI and device boot remain untested")


if __name__ == "__main__":
    main()
