[简体中文](README.md) | **English**

# OnePlus Pad Pro kernel builds

This repository builds ReSukiSU / SukiSU Ultra kernels exclusively for **OnePlus Pad 2 Pro** and **OnePlus Pad 3 Pro**.
Based on [Numbersf/Action-Build](https://github.com/Numbersf/Action-Build); the upstream [LICENSE](LICENSE) is retained.
This repository is maintained independently. Its initial adaptation comes from commit `bbca1d9f8fcf733e96ba5cda64b1ee1239216033` in `xiaochenzaine/Action-Build`.

[Open the build workflow](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_oneplus_pad.yml)

## Downloads and validation

[Download AK3 packages, paired official managers and validation reports](https://github.com/xiaochenzaine/oneplus_pad_kernel/releases/tag/pad_pro_2026_11_17).
All six packages below passed full compilation and independent verification of their file checksums,
embedded kernel configuration, root versions and original official APK bytes.

| Target | Kernel version | ReSukiSU 35203 | Ultra 41184 | HMBIRD / Fengchi |
| --- | --- | --- | --- | --- |
| 一加Pad 2 Pro A15 | 6.6.57 | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954240785) | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43953536348) | Built in |
| 一加Pad 2 Pro A16 | 6.6.118 | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954677418) | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954684670) | Built in |
| 一加Pad 3 Pro A16 | 6.12.58 | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43962282495) | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43964665574) | Not added |

These packages use KPM=N/A, with optional ADIOS, ZSTD updates and display patches disabled.
All 22 Python checks, actionlint and relevant object compilation passed. Both official APKs passed
package, version and signing-certificate verification and retain their original signatures.
Pad 3 Pro / 6.12 includes SUSFS VMA adaptation, Ultra LSM registration and build-path fixes,
and corrected static LSM slot counts for root/BBG. The release's verification_results.json records
each package's actual workflow commit and hashes; validation_report.md contains the full report.
Device boot, stock-module ABI and gaming performance have not been verified.

## Supported targets

| Workflow choice | Device OS | Official manifest | Source revision | Kernel series |
| --- | --- | --- | --- | --- |
| 一加Pad 2 Pro A15 (default) | Android 15 | `oneplus_pad_2_pro.xml` | `oneplus/sm8750_v_15.0.1_pad_2_pro` | 6.6 |
| 一加Pad 2 Pro A16 | Android 16 | `oneplus_pad_2_pro_b.xml` | `oneplus/sm8750_b_16.0.0_pad_2_pro` | 6.6 |
| 一加Pad 3 Pro A16 | Android 16 | `oneplus_pad_3_pro.xml` | `oneplus/sm8850_b_16.0_pad_3_pro` | 6.12 |

Only these three targets are accepted. The resolver validates the common, platform and device-driver revisions in the official manifest.
Manifests come from the `oneplus/sm8750` and `oneplus/sm8850` branches of [OnePlusOSS/kernel_manifest](https://github.com/OnePlusOSS/kernel_manifest).
There is currently no official Android 15 manifest for Pad 3 Pro.

Both Pad 2 Pro firmware versions use the `android15-6.6` GKI branch. This is separate from the device OS version.
Choose A15/A16 according to the installed OS. `RESUBLEVEL` changes only the displayed kernel version.

## Build

1. Open Actions → **Build OnePlus Pad Kernels** → **Run workflow**.
2. Use the default `main` branch, then select the device and Android version.
3. Enable `SCHED_HMBIRD` for Fengchi on Pad 2 Pro if desired. Keep it disabled for Pad 3 Pro.
4. Select `resukisu_35203` (default) or `ultra_41184` in `sukisu_profile`; keep `KPM=N/A` for ReSukiSU.
5. Download the AnyKernel3 package, paired official manager and validation artifacts from the completed run.

Scripts and local patches always come from the checked-out workflow commit, without switching to upstream sources.
Shared options for SukiSU/SUSFS, KPM/KPN, BBG, networking, ZRAM, DroidSpaces and Re-Kernel are retained.
Use `Workflow and Cache Cleanup` to clean build history and caches.

## Fengchi / HMBIRD

Pad 2 Pro uses [Numbersf/SCHED_PATCH, branch sm8750](https://github.com/Numbersf/SCHED_PATCH/tree/sm8750):

| Workflow choice | Patch |
| --- | --- |
| 一加Pad 2 Pro A15 | `fengchi_oneplus_pad_2_pro.patch` |
| 一加Pad 2 Pro A16 | `fengchi_oneplus_pad_2_pro_b.patch` |
| 一加Pad 3 Pro A16 | No matching patch is currently available; leave HMBIRD disabled |

Existing HMBIRD source directories are not patched again. Unsupported devices or missing patches produce an explicit error.

## Pad 2 Pro Android 15 compatibility

The A15 build restores all missing `TLS_STATS` guards and sets `CONFIG_TLS_STATS=n` to preserve the network namespace layout.
This A15-only [patch](patches/pad_2_pro_android15_tls_stats.patch) uses the corresponding files from
[Android common 7b1f455c](https://android.googlesource.com/kernel/common/+/7b1f455c7143098e61cdd2298639e3c412c285f2).

## Paired root and manager

Choose `resukisu_35203` (default, historical ReSukiSU v4.2.0-rc3 with SUSFS 2.3.0)
or `ultra_41184` (SukiSU Ultra v4.3.0-r2 with SUSFS 2.4.0). Android 15 does not
inherently exclude Ultra 41184. Device firmware and root implementation are separate choices.
The historical ReSukiSU commit is pinned before the project was renamed BakaSU.
ReSukiSU requires KPM=N/A; its multi-manager support is disabled.

[config/sukisu_profiles.json](config/sukisu_profiles.json) locks the source commits,
upstream version arithmetic, SUSFS revisions and original official APKs. Package,
actual version, certificate and SHA256 mismatches stop the build. Mirrored APKs
retain the original bytes and signatures and record their official CI origins.
The two implementations have different official signing certificates.

Build validation checks the compiled root version and actual configuration,
including seccomp, seccomp filters, strong stack protection and the A15 TLS layout.
Artifacts include the AK3 package, its official APK and a separate validation report.
Stock-module ABI and device boot validation are reported separately from compilation.

## Seccomp status

The official manager reads its calling thread with `PR_GET_SECCOMP`, which does not
measure kernel-wide or other apps' protection. Historical Ultra 41184 explicitly
drops the manager's filter on startup, so its status can read Disabled even with
SECCOMP enabled in the kernel.

New Ultra builds for all three targets apply the [manager seccomp patch](patches/ultra_manager_seccomp.patch).
Both SUSFS zygote paths retain the manager's existing filter and injected driver fd.
Actual su sessions keep upstream root-profile handling. Official APKs and signatures
are retained; ReSukiSU behavior is unchanged. Existing release assets are unaffected.

After updating the kernel and rebooting, reopen the manager. Extract check_seccomp.sh
from the new AK3 and run it from a root shell to read the manager and an ordinary app:

```sh
su -c 'sh /sdcard/Download/check_seccomp.sh com.sukisu.ultra com.android.settings'
```

Open both apps before checking. Replace the settings package with another app that
has not been granted root if desired. The script reads configuration and process
status without changing the device or transmitting data. Seccomp: 2 means filter
mode for the inspected process; a root shell's Seccomp: 0 does not describe app
protection. Device checks must still confirm manager detection, root authorization,
su -c id and module management; compilation alone cannot verify those functions.

Optional adios, zstd_update and display_fix are off by default. ADIOS does not
replace the default I/O scheduler and is separate from HMBIRD CPU scheduling. ZSTD
1.5.7 is currently restricted to Pad 2 Pro A15 / 6.6.57; the display patch is restricted
to Pad 2 Pro A16 / 6.6.118. NETFILTER adds optional FQ/FQ_CODEL/CAKE/PIE/FQ_PIE
support without changing the default qdisc. See [patch sources](patches/sources.md).

Successful compilation is not proof of stock-module ABI compatibility or device boot.
