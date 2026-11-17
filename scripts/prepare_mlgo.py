#!/usr/bin/env python3
"""Probe the selected compiler before enabling the MLGO register allocator."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


mlgo_cflags = ["-mllvm", "-regalloc-enable-advisor=release"]
probe_source = """unsigned long mlgo_probe(const unsigned long *values, unsigned long count)
{
    unsigned long first = 1, second = 3, third = 5, fourth = 7;
    for (unsigned long index = 0; index < count; ++index) {
        first += values[index] * second;
        second ^= first + third;
        third += second * fourth;
        fourth ^= third + values[index];
    }
    return first ^ second ^ third ^ fourth;
}
"""


def prepare_mlgo(compiler, enabled, kernel_config):
    compiler = compiler.resolve(strict=True)
    version = subprocess.run([str(compiler), "--version"], capture_output=True, text=True,
                             check=True, timeout=30).stdout.splitlines()[0]
    with compiler.open("rb") as source:
        compiler_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
    report = {"requested": enabled, "enabled": False, "status": "not_requested", "cflags": [],
              "compiler": str(compiler), "compiler_version": version,
              "compiler_sha256": compiler_sha256, "optimization_level": "O2",
              "device_benchmark": "not_performed"}
    if not enabled:
        return report
    if "CONFIG_LTO_NONE=y" not in kernel_config.read_text().splitlines():
        raise ValueError("MLGO 当前仅验证非 LTO 极速构建；不会自动更改内核的 LTO 配置。")
    with tempfile.TemporaryDirectory(prefix="mlgo_probe_") as temporary_dir:
        temporary_path = Path(temporary_dir)
        source_path = temporary_path / "mlgo_probe.c"
        object_path = temporary_path / "mlgo_probe.o"
        source_path.write_text(probe_source, encoding="utf-8")
        base_command = [str(compiler), "--target=aarch64-linux-gnu", "-O2", "-ffreestanding",
                        "-fno-stack-protector", "-mgeneral-regs-only", "-c", str(source_path),
                        "-o", str(object_path)]
        baseline = subprocess.run(base_command, capture_output=True, text=True, timeout=60)
        if baseline.returncode:
            raise ValueError(f"所选 Clang 无法编译 AArch64 探测对象：{baseline.stderr[-2000:]}")
        result = subprocess.run(base_command + mlgo_cflags, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError(f"所选 Clang 不支持 MLGO release 模型，请关闭 MLGO：{result.stderr[-2000:]}")
        object_bytes = object_path.read_bytes()
        if object_bytes[:4] != b"\x7fELF" or int.from_bytes(object_bytes[18:20], "little") != 183:
            raise ValueError("MLGO 探测没有生成预期的 AArch64 ELF 对象。")
    report.update(enabled=True, status="probe_passed", cflags=list(mlgo_cflags),
                  probe_target="aarch64-linux-gnu", probe="actual_object_compile", lto="none")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--kernel-config", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--enable", action="store_true")
    args = parser.parse_args()
    try:
        report = prepare_mlgo(args.compiler, args.enable, args.kernel_config)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"::error::{error}\n")
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MLGO: {report['status']}; compiler: {report['compiler_version']}")


if __name__ == "__main__":
    main()
