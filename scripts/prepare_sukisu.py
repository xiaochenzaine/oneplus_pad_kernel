#!/usr/bin/env python3
"""Fetch a locked official manager and integrate its matching builtin source."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.request import urlopen
from zipfile import ZipFile


config_path = Path(__file__).resolve().parents[1] / "config" / "sukisu_profiles.json"


def run_output(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def file_sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def load_profile(profile_name, kmi):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile = dict(config["profiles"][profile_name])
    profile.update(profile=profile_name, kmi=kmi,
                   susfs=dict(profile["susfs"][kmi], repository=config["susfs_repository"]))
    expected_code = (profile["version_base"] + profile["main_commit_count"]
                     - profile["version_offset"])
    if expected_code != profile["version_code"]:
        raise ValueError("Version code disagrees with the pinned upstream commit count")
    for revision in [profile["main_commit"], profile["builtin_commit"], profile["susfs"]["commit"]]:
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("Source revisions must be full immutable commit hashes")
    return profile


def validate_apk_metadata(badging, certificates, profile):
    match = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'",
                      badging, re.MULTILINE)
    if not match or match.groups() != (profile["package"], str(profile["version_code"]),
                                       profile["version_name"]):
        raise ValueError("Official APK package/version does not match the selected profile")
    signers = re.findall(r"^Signer #\d+ certificate SHA-256 digest: ([0-9a-f]+)$",
                         certificates, re.MULTILINE)
    if signers != [profile["certificate_sha256"]]:
        raise ValueError("APK signer is not the locked official SukiSU certificate")


def verify_apk(apk_path, profile):
    if file_sha256(apk_path) != profile["apk"]["sha256"]:
        raise ValueError("APK SHA256 mismatch; refusing a changed or repackaged manager")
    badging = run_output("aapt", "dump", "badging", str(apk_path))
    certificates = run_output("apksigner", "verify", "--print-certs", str(apk_path))
    validate_apk_metadata(badging, certificates, profile)


def download_apk(profile, output_dir):
    apk = profile["apk"]
    apk_path = output_dir / apk["name"]
    if "url" in apk:
        with urlopen(apk["url"], timeout=120) as response, apk_path.open("wb") as target:
            shutil.copyfileobj(response, target)
    else:
        endpoint = f"repos/{profile['repository']}/actions/artifacts/{apk['artifact_id']}"
        metadata = json.loads(run_output("gh", "api", endpoint))
        if (metadata["expired"] or metadata["name"] != apk.get("artifact_name", "Manager")
                or metadata["workflow_run"]["head_sha"] != profile["main_commit"]
                or metadata["workflow_run"]["id"] != apk["run_id"]):
            raise ValueError("The locked official Manager artifact is unavailable or mismatched")
        archive_path = output_dir / "manager_artifact.zip"
        with archive_path.open("wb") as target:
            subprocess.run(["gh", "api", f"{endpoint}/zip"], stdout=target, check=True)
        with ZipFile(archive_path) as archive:
            members = [name for name in archive.namelist() if Path(name).name == apk["name"]]
            if len(members) != 1:
                raise ValueError("Expected exactly one matching official Manager APK")
            with archive.open(members[0]) as source, apk_path.open("wb") as target:
                shutil.copyfileobj(source, target)
        archive_path.unlink()
    verify_apk(apk_path, profile)
    return apk_path


def checkout_commit(repository, revision, destination):
    # Refuse an existing checkout rather than resetting somebody else's edits.
    destination.mkdir()
    subprocess.run(["git", "init", "-q", str(destination)], check=True)
    subprocess.run(["git", "remote", "add", "origin", repository], cwd=destination, check=True)
    subprocess.run(["git", "fetch", "--depth=1", "origin", revision], cwd=destination, check=True)
    subprocess.run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=destination, check=True)
    if run_output("git", "rev-parse", "HEAD", cwd=destination) != revision:
        raise ValueError(f"Checkout does not match the lock: {destination}")


def lock_makefile(makefile_text, profile):
    if profile["source_layout"] == "kbuild":
        start = makefile_text.index("$(shell cd $(KSU_SRC); [ -f ../.git/shallow ]")
    else:
        start = makefile_text.index("REPO_OWNER ")
    end = makefile_text.index("ccflags-y += -DKSU_VERSION=", start)
    full_version = (f"{profile['version_name']}-{profile['builtin_commit'][:8]}"
                    f"@{profile['profile']}")
    # Replace ONLY upstream's moving version lookup block. Retain feature/compat checks.
    fixed_block = (
        "# Version derived from the official CI/release in sukisu_profiles.json.\n"
        "# No network lookup or moving main branch is used during compilation.\n"
        f"REPO_NAME := {profile['display_name']}\n"
        f"KSU_VERSION := {profile['version_code']}\n"
        f"KSU_VERSION_FULL := {full_version}\n"
        "$(info -- $(REPO_NAME) version: $(KSU_VERSION) [$(KSU_VERSION_FULL)])\n\n"
    )
    if profile["source_layout"] == "makefile":
        package = re.search(r"^KSU_PACKAGE_NAME \?= (\S+)$", makefile_text, re.MULTILINE)
        if not package or package.group(1) != profile["package"]:
            raise ValueError("Builtin source has a different manager package name")
    return makefile_text[:start] + fixed_block + makefile_text[end:]


def integrate_source(profile, platform_dir):
    source_dir = platform_dir / "KernelSU"  # Existing upstream integration interface.
    checkout_commit(f"https://github.com/{profile['repository']}.git",
                    profile["builtin_commit"], source_dir)
    makefile_name = "Kbuild" if profile["source_layout"] == "kbuild" else "Makefile"
    makefile = source_dir / "kernel" / makefile_name
    makefile.write_text(lock_makefile(makefile.read_text(), profile), encoding="utf-8")
    signature_source = "\n".join(path.read_text() for path in
                                (source_dir / "kernel" / "manager").glob("*.[ch]"))
    if profile["certificate_sha256"] not in signature_source:
        raise ValueError("Upstream builtin does not trust the locked official certificate")
    drivers_dir = platform_dir / "common" / "drivers"
    (drivers_dir / "kernelsu").symlink_to("../../KernelSU/kernel", target_is_directory=True)
    with (drivers_dir / "Makefile").open("a") as target:
        target.write("\nobj-$(CONFIG_KSU) += kernelsu/\n")
    kconfig_path = drivers_dir / "Kconfig"
    kconfig_text = kconfig_path.read_text()
    insertion = kconfig_text.rfind("endmenu")
    if insertion < 0:
        raise ValueError("Cannot locate the drivers Kconfig menu")
    kconfig_path.write_text(kconfig_text[:insertion] + 'source "drivers/kernelsu/Kconfig"\n'
                           + kconfig_text[insertion:])
    susfs_dir = platform_dir.parent / "susfs4ksu"
    checkout_commit(profile["susfs"]["repository"], profile["susfs"]["commit"], susfs_dir)
    header = (susfs_dir / "kernel_patches" / "include" / "linux" / "susfs.h").read_text()
    if f'#define SUSFS_VERSION "{profile["susfs"]["version"]}"' not in header:
        raise ValueError("SUSFS header version does not match the lock")


def write_env(profile):
    env_path = os.environ.get("GITHUB_ENV")
    if env_path:
        values = {"KSUVER": profile["version_code"], "sukisu_profile": profile["profile"],
                  "sukisu_name": profile["display_name"].replace(" ", "")}
        with open(env_path, "a", encoding="utf-8") as target:
            for name, value in values.items():
                target.write(f"{name}={value}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["prepare", "install"])
    parser.add_argument("--profile", required=True, choices=["ultra_41184", "resukisu_35203"])
    parser.add_argument("--kmi", required=True, choices=["android15-6.6", "android16-6.12"])
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--platform-dir", type=Path)
    args = parser.parse_args()
    profile = load_profile(args.profile, args.kmi)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    lock_path = args.output_dir / "sukisu_lock.json"
    if args.operation == "prepare":
        download_apk(profile, args.output_dir)
        lock_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    else:
        if json.loads(lock_path.read_text()) != profile:
            raise ValueError("Prepared manager lock does not match this source selection")
        verify_apk(args.output_dir / profile["apk"]["name"], profile)
        if args.platform_dir is None:
            parser.error("install requires --platform-dir")
        integrate_source(profile, args.platform_dir.resolve())
    write_env(profile)
    print(f"Verified {args.profile}: {profile['version_name']} ({profile['version_code']})")


if __name__ == "__main__":
    main()
