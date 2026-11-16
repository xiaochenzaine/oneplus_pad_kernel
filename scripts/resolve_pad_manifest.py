#!/usr/bin/env python3
"""Resolve and validate the official manifests for the supported OnePlus pads."""

import argparse
import os
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as element_tree


device_configs = {
    "oneplus_pad_2_pro": {
        "cpu": "sm8750",
        "android_version": "15.0.1",
        "revision": "oneplus/sm8750_v_15.0.1_pad_2_pro",
        "platform_path": "kernel_platform/msm-kernel",
        "cpud": "sun",
        "kmi": "android15-6.6",
        "file_conf": "oneplus_pad_2_pro",
        "file_base": "OnePlusPad2Pro",
    },
    "oneplus_pad_2_pro_b": {
        "cpu": "sm8750",
        "android_version": "16.0.0",
        "revision": "oneplus/sm8750_b_16.0.0_pad_2_pro",
        "platform_path": "kernel_platform/msm-kernel",
        "cpud": "sun",
        "kmi": "android15-6.6",
        "file_conf": "oneplus_pad_2_pro",
        "file_base": "OnePlusPad2Pro",
    },
    "oneplus_pad_3_pro": {
        "cpu": "sm8850",
        "android_version": "16.0",
        "revision": "oneplus/sm8850_b_16.0_pad_3_pro",
        "platform_path": "kernel_platform/soc-repo",
        "cpud": "canoe",
        "kmi": "android16-6.12",
        "file_conf": "oneplus_pad_3_pro",
        "file_base": "OnePlusPad3Pro",
    },
}

device_choices = {
    "一加Pad 2 Pro A15": "oneplus_pad_2_pro",
    "一加Pad 2 Pro A16": "oneplus_pad_2_pro_b",
    "一加Pad 3 Pro A16": "oneplus_pad_3_pro",
}


def validate_manifest(xml_text, config):
    manifest = element_tree.fromstring(xml_text)
    remotes = {remote.get("name"): remote.get("fetch", "").rstrip("/")
               for remote in manifest.findall("remote")}
    projects = {project.get("name"): project for project in manifest.findall("project")}
    cpu = config["cpu"]
    expected_projects = {
        f"android_kernel_common_oneplus_{cpu}": "kernel_platform/common",
        f"android_kernel_oneplus_{cpu}": config["platform_path"],
        f"android_kernel_modules_and_devicetree_oneplus_{cpu}": "./",
    }
    for name, path in expected_projects.items():
        project = projects.get(name)
        if project is None:
            raise ValueError(f"Missing official project: {name}")
        if (project.get("revision") != config["revision"]
                or project.get("path") != path
                or remotes.get(project.get("remote")) != "https://github.com/OnePlusOSS"):
            raise ValueError(f"Unexpected source for {name}: {project.attrib}")


def resolve_manifest(device, workspace, env_path, output_path):
    config = device_configs[device]
    branch = f"oneplus/{config['cpu']}"
    url = ("https://raw.githubusercontent.com/OnePlusOSS/kernel_manifest/"
           f"{branch}/{device}.xml")
    request = Request(url, headers={"User-Agent": "oneplus_pad_kernel_build"})
    with urlopen(request, timeout=60) as response:
        xml_text = response.read().decode("utf-8")
    validate_manifest(xml_text, config)

    manifest_dir = workspace / ".repo" / "manifests_fallback"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / f"{device}.xml").write_text(xml_text, encoding="utf-8")
    env_values = {
        "FILE": device,
        "FILE_CONF": config["file_conf"],
        "FILE_BASE": config["file_base"],
        "MANIFEST_REPO": "OnePlusOSS",
        "MANIFEST_REPO_NAME": "kernel_manifest",
        "MANIFEST_BRANCH": branch,
        "CPU": config["cpu"],
        "ANDROID_VERSION": config["android_version"],
        "ANDROID_SHORT_VERSION": config["android_version"].split(".")[0],
        "CPUD": config["cpud"],
        "BUILD_METHOD": "perf",
        "pad_expected_kmi": config["kmi"],
    }
    with env_path.open("a", encoding="utf-8") as env_file:
        for name, value in env_values.items():
            env_file.write(f"{name}={value}\n")
    with output_path.open("a", encoding="utf-8") as output_file:
        output_file.write(f"value={config['file_base']}_Android{config['android_version']}\n")
    print(f"{device}: Android {config['android_version']}, {config['revision']}")
    print(f"Manifest: {url}")
    print(f"GKI branch: {config['kmi']} (separate from the device Android version)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device", choices=device_choices)
    args = parser.parse_args()
    resolve_manifest(device_choices[args.device], Path(os.environ["GITHUB_WORKSPACE"]),
                     Path(os.environ["GITHUB_ENV"]), Path(os.environ["GITHUB_OUTPUT"]))


if __name__ == "__main__":
    main()
