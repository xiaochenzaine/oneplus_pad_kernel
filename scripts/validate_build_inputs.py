#!/usr/bin/env python3
"""Reject unsupported device options before downloads or kernel preparation."""

import argparse
import json
import os
from pathlib import Path
import re

from resolve_pad_manifest import device_choices, device_configs


boolean_inputs = (
    "adios", "zstd_update", "display_fix", "lz4_update", "fast_build", "lsm_bbg",
    "netfilter", "ccm", "unicode_bypass", "droid_spaces", "re_kernel",
    "space_noclean", "build_nocache",
)
zram_algorithms = {"lz4", "lz4hc", "lz4k", "lz4kd", "lz4k_oplus", "lzo", "lzo-rle", "zstd", "842"}
default_zram_profile = "原厂配置（推荐）"
zram_profiles = {
    default_zram_profile: "system",
    "LZ4KD / 4 GiB": "1/lz4kd/4294967296",
    "LZ4KD / 8 GiB": "1/lz4kd/8589934592",
    "LZ4 / 4 GiB": "1/lz4/4294967296",
    "LZ4 / 8 GiB": "1/lz4/8589934592",
}


def parse_zram(value):
    if value == "system":
        return {"custom": False, "algorithm": None, "size_bytes": None}
    if not isinstance(value, str):
        raise ValueError("ZRAM 必须为 system 或 1/算法/字节数。")
    match = re.fullmatch(r"([01])/([a-z0-9_-]+)/([0-9]+)", value)
    if not match:
        raise ValueError("ZRAM 格式错误：使用 system，或例如 1/lz4kd/8589934592。")
    enabled, algorithm, size_text = match.groups()
    if enabled == "0":
        return {"custom": False, "algorithm": None, "size_bytes": None}
    if algorithm not in zram_algorithms:
        raise ValueError(f"未支持的 ZRAM 算法：{algorithm}。")
    size_bytes = int(size_text)
    if not 0 < size_bytes < 2 ** 63:
        raise ValueError("ZRAM 大小必须为有效的正整数，单位为字节。")
    return {"custom": True, "algorithm": algorithm, "size_bytes": size_bytes}


def resolve_zram_config(inputs):
    profile = inputs.get("zram_profile", default_zram_profile)
    if profile not in zram_profiles:
        raise ValueError("ZRAM 方案无效，请选择原厂配置或下拉菜单中的预设。")
    legacy_config = inputs.get("zram", "system")
    if profile != default_zram_profile and legacy_config != "system":
        raise ValueError("ZRAM 预设与旧自定义参数不能同时指定，请只选择一种方式。")
    return zram_profiles[profile] if profile != default_zram_profile else legacy_config


def validate_build_inputs(inputs):
    if not isinstance(inputs, dict):
        raise ValueError("构建参数必须为 JSON 对象。")
    target = inputs.get("pad_target")
    if target not in device_choices:
        raise ValueError("请选择受支持的 Pad 2 Pro A15、Pad 2 Pro A16 或 Pad 3 Pro A16 入口。")
    device = device_choices[target]
    for name in boolean_inputs:
        if name in inputs and not isinstance(inputs[name], bool):
            raise ValueError(f"{name} 必须是布尔值。")
    profile = inputs.get("sukisu_profile", "resukisu_35203")
    if profile not in {"resukisu_35203", "ultra_41184"}:
        raise ValueError("请选择 ReSukiSU 35203 或 Ultra 41184。")
    kpm = inputs.get("kpm", "N/A")
    if kpm not in {"N/A", "KPM", "KPN"}:
        raise ValueError("KPM 选项无效。")
    if profile == "resukisu_35203" and kpm != "N/A":
        raise ValueError("ReSukiSU 未提供 Ultra KPM/KPN 实现，请选择 N/A。")
    zram_config = resolve_zram_config(inputs)
    zram = parse_zram(zram_config)
    lz4_update = inputs.get("lz4_update", False)
    if device == "oneplus_pad_3_pro":
        if zram["custom"]:
            raise ValueError("Pad 3 Pro A16/6.12 缺少对应的自定义 ZRAM 补丁，请保留原厂配置。")
        if lz4_update:
            raise ValueError("Pad 3 Pro A16/6.12 的 LZ4 升级尚未完成适配验证，当前不开放。")
    if inputs.get("zstd_update", False) and device != "oneplus_pad_2_pro":
        raise ValueError("ZSTD 升级仅适用于 Pad 2 Pro A15/6.6.57。")
    if inputs.get("display_fix", False) and device != "oneplus_pad_2_pro_b":
        raise ValueError("显示补丁仅适用于 Pad 2 Pro A16/6.6.118。")
    return {
        "target": target,
        "device": device,
        "kmi": device_configs[device]["kmi"],
        "sukisu_profile": profile,
        "zram_config": zram_config,
        "zram": zram,
        "lz4_update": lz4_update,
        "zram_lz4_combination": "device_test_required" if zram["custom"] and lz4_update else "not_selected",
        "fengchi": "native_hmbird_ii_runtime_unverified" if device == "oneplus_pad_3_pro" else "builtin_hmbird",
        "requested_inputs": inputs,
    }


def write_summary(report, path):
    zram = report["zram"]
    zram_text = (f"{zram['algorithm'].upper()} / {zram['size_bytes'] / 2 ** 30:g} GiB（需另装生成的 ZRAM 模块）"
                 if zram["custom"] else "原厂配置（推荐）；保留系统 ZRAM")
    fengchi_text = ("原生 HMBIRD II 框架；厂商模块加载及游戏策略待实机确认"
                    if report["device"] == "oneplus_pad_3_pro" else "编入目标机型 HMBIRD 补丁")
    with path.open("a", encoding="utf-8") as summary:
        summary.write(
            f"## 构建选项检查\n\n| 项目 | 本次选择 |\n| --- | --- |\n"
            f"| 机型 | {report['target']} |\n| Root | {report['sukisu_profile']} |\n"
            f"| ZRAM | {zram_text} |\n| 升级 LZ4 | {'是' if report['lz4_update'] else '否'} |\n"
            f"| 风驰 | {fengchi_text} |\n\n"
        )
        if report["zram_lz4_combination"] == "device_test_required":
            summary.write("自定义 ZRAM 与 LZ4 升级同时选择：仍需构建和实机验证；lz4kd 与普通 LZ4 是不同实现。\n\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-path", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate_build_inputs(json.loads(os.environ["pad_build_inputs"]))
    except (KeyError, TypeError, ValueError) as error:
        parser.exit(1, f"::error::{error}\n")
    args.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if output_path := os.environ.get("GITHUB_OUTPUT"):
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"zram_custom={'true' if report['zram']['custom'] else 'false'}\n")
            output.write(f"zram_config={report['zram_config']}\n")
    if summary_path := os.environ.get("GITHUB_STEP_SUMMARY"):
        write_summary(report, Path(summary_path))
    print(f"Validated build options: {report['target']}")


if __name__ == "__main__":
    main()
