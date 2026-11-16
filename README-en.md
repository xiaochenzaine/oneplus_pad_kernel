[简体中文](README.md) | **English**

# OnePlus Pad Pro kernel builds

This repository builds ReSukiSU / SukiSU Ultra kernels exclusively for **OnePlus Pad 2 Pro** and **OnePlus Pad 3 Pro**.
Based on [Numbersf/Action-Build](https://github.com/Numbersf/Action-Build); the upstream [LICENSE](LICENSE) is retained.
This repository is maintained independently. Its initial adaptation comes from commit `bbca1d9f8fcf733e96ba5cda64b1ee1239216033` in `xiaochenzaine/Action-Build`.

[Open the build workflow](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_oneplus_pad.yml)

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
4. Download the AnyKernel3 package and manager artifacts (with the paired official manager) from the completed run.

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

Optional adios, zstd_update and display_fix are off by default. ADIOS does not
replace the default I/O scheduler and is separate from HMBIRD CPU scheduling. ZSTD
1.5.7 is currently restricted to Pad 2 Pro A15 / 6.6.57; the display patch is restricted
to Pad 2 Pro A16 / 6.6.118. NETFILTER adds optional FQ/FQ_CODEL/CAKE/PIE/FQ_PIE
support without changing the default qdisc. See [patch sources](patches/sources.md).

Successful compilation is not proof of stock-module ABI compatibility or device boot.
