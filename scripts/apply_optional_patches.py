#!/usr/bin/env python3
"""Apply reviewed, device-scoped patches after a successful dry run."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


patch_dir = Path(__file__).resolve().parents[1] / "patches"


def select_patches(device, version, adios, zstd_update, display_fix,
                   mem_prefetch=False, s2idle_wakeup=False):
    selected = []
    if adios:
        patch_name = "adios_6_12.patch" if version.startswith("6.12.") else "adios_6_6.patch"
        if not version.startswith(("6.6.", "6.12.")):
            raise ValueError("ADIOS is only reviewed for the supported 6.6/6.12 sources")
        selected.append((patch_name, 1))
    if zstd_update:
        if device != "oneplus_pad_2_pro" or version != "6.6.57":
            raise ValueError("ZSTD 1.5.7 backport is currently reviewed only for Pad 2 Pro A15/6.6.57")
        selected.append(("zstd_1_5_7.patch", 0))
    if display_fix:
        if device != "oneplus_pad_2_pro_b" or version != "6.6.118":
            raise ValueError("Display fix is only reviewed for Pad 2 Pro A16/6.6.118")
        selected.append(("pad_2_pro_a16_display.patch", 0))
    if mem_prefetch or s2idle_wakeup:
        reviewed_versions = {"oneplus_pad_2_pro": "6.6.57", "oneplus_pad_2_pro_b": "6.6.118",
                             "oneplus_pad_3_pro": "6.12.58"}
        if reviewed_versions.get(device) != version:
            raise ValueError("Memory prefetch and s2idle patches require the reviewed device/kernel pair")
    if mem_prefetch:
        selected.append(("mem_prefetch.patch", 0))
    if s2idle_wakeup:
        selected.append(("s2idle_wakeup.patch", 0))
    return selected


def apply_patch(kernel_dir, patch_name, fuzz):
    patch_path = patch_dir / patch_name
    command = ["patch", "--batch", "--forward", f"--fuzz={fuzz}", "-p1", "-i", str(patch_path)]
    subprocess.run(command + ["--dry-run"], cwd=kernel_dir, check=True)
    subprocess.run(command, cwd=kernel_dir, check=True)
    return {"file": patch_name, "sha256": hashlib.sha256(patch_path.read_bytes()).hexdigest(),
            "maximum_fuzz": fuzz}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-dir", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--adios", action="store_true")
    parser.add_argument("--zstd-update", action="store_true")
    parser.add_argument("--display-fix", action="store_true")
    parser.add_argument("--mem-prefetch", action="store_true")
    parser.add_argument("--s2idle-wakeup", action="store_true")
    args = parser.parse_args()
    selected = select_patches(args.device, args.version, args.adios,
                              args.zstd_update, args.display_fix, args.mem_prefetch, args.s2idle_wakeup)
    applied = [apply_patch(args.kernel_dir, name, fuzz) for name, fuzz in selected]
    args.report.write_text(json.dumps(applied, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
