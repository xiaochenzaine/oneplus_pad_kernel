[简体中文](README.md) | **English**

# OnePlus Pad Pro kernel builds

This repository builds ReSukiSU / SukiSU Ultra kernels exclusively for **OnePlus Pad 2 Pro** and **OnePlus Pad 3 Pro**.
Based on [Numbersf/Action-Build](https://github.com/Numbersf/Action-Build); the upstream [LICENSE](LICENSE) is retained.
This repository is maintained independently. Its initial adaptation comes from commit `bbca1d9f8fcf733e96ba5cda64b1ee1239216033` in `xiaochenzaine/Action-Build`.

Build entries: [Pad 2 Pro A15](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_pad_2_pro_a15.yml) · [Pad 2 Pro A16](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_pad_2_pro_a16.yml) · [Pad 3 Pro A16](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_pad_3_pro_a16.yml)

## Downloads and validation

[Download the fixed Ultra 41184 AK3 packages, official manager and validation reports](https://github.com/xiaochenzaine/oneplus_pad_kernel/releases/tag/pad_pro_2026_11_17_seccomp_fix).
All six packages below passed full compilation and independent verification of their file checksums,
embedded kernel configuration, root versions and original official APK bytes.

| Target | Kernel version | ReSukiSU 35203 | Ultra 41184 | HMBIRD / Fengchi |
| --- | --- | --- | --- | --- |
| 一加Pad 2 Pro A15 | 6.6.57 | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954240785) | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43953536348) | Built in |
| 一加Pad 2 Pro A16 | 6.6.118 | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954677418) | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954684670) | Built in |
| 一加Pad 3 Pro A16 | 6.12.58 | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43962282495) | [Passed](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43964665574) | Native HMBIRD II framework; runtime unverified |

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

1. Open the **一加Pad 2 Pro A15**, **一加Pad 2 Pro A16** or **一加Pad 3 Pro A16** workflow in Actions, then select **Run workflow**.
2. Use the default `main` branch. Each entry fixes its device and Android version.
3. Pad 2 Pro receives its matching HMBIRD patch. Pad 3 Pro uses the framework required by native HMBIRD II; vendor-module compatibility and game policies still require device testing.
4. Select `resukisu_35203` (default) or `ultra_41184` in `sukisu_profile`; keep `KPM=N/A` for ReSukiSU.
5. Download the AnyKernel3 package, paired official manager and validation artifacts from the completed run.

Scripts and local patches always come from the checked-out workflow commit, without switching to upstream sources.
The three entry workflows call the same `build_oneplus_pad.yml` implementation. GitHub cannot dynamically hide fields by selected target, so each entry exposes applicable options. Shared validation rejects unsupported combinations before downloads or disk cleanup.
The **内部公共编译流程** shared workflow is called automatically by these entries and does not need to be run separately.

| Option | Pad 2 Pro A15 | Pad 2 Pro A16 | Pad 3 Pro A16 |
| --- | --- | --- | --- |
| Custom ZRAM | Optional; system settings by default | Optional; system settings by default | Hidden; no matching 6.12 patch |
| LZ4 upgrade | Optional; off by default | Optional; off by default | Hidden; compatibility not validated |
| ZSTD 1.5.7 | Optional; off by default | Hidden | Hidden |
| Display patch | Hidden | Optional; off by default | Hidden |
| ADIOS I/O scheduler | Optional; off by default | Optional; off by default | Optional; off by default |

The Pad 2 Pro **ZRAM** dropdown defaults to **原厂配置（推荐）** (stock settings, recommended); no manual parameters are needed.
Other presets are **LZ4KD / 4 GiB**, **LZ4KD / 8 GiB**, **LZ4 / 4 GiB** and **LZ4 / 8 GiB**. Algorithm and capacity are resolved automatically; install the separately generated ZRAM module to apply a custom preset at startup.
Stock settings preserve existing system ZRAM. The legacy `system` and `0/lz4kd/8589934592` inputs also retain stock settings.
Flashing AK3 alone does not activate that configuration. Logical capacity does not reserve an equal amount of physical RAM upfront.
Custom ZRAM and LZ4 upgrades can be selected together, but the combination has not passed a full build or device test. `lz4kd` is distinct from ordinary LZ4, so upgrading LZ4 does not directly upgrade `lz4kd`.
The run summary and `build_manifest.json` record the target, requested memory options and validation scope.

## Fengchi / HMBIRD

Pad 2 Pro uses [Numbersf/SCHED_PATCH, branch sm8750](https://github.com/Numbersf/SCHED_PATCH/tree/sm8750):

| Workflow choice | Patch |
| --- | --- |
| 一加Pad 2 Pro A15 | `fengchi_oneplus_pad_2_pro.patch` |
| 一加Pad 2 Pro A16 | `fengchi_oneplus_pad_2_pro_b.patch` |
| 一加Pad 3 Pro A16 | Native HMBIRD II / sched_ext path; skips the Pad 2 Pro patch |

Existing HMBIRD source directories are not patched again. Unsupported devices or missing patches produce an explicit error.

The official Pad 3 Pro source includes [HMBIRD II](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8850/tree/8be53e8b737a83a33512d5e0106cccb010a5c24c/vendor/oplus/kernel/cpu/sched_ext), built as the `oplus_bsp_sched_ext` vendor module.
Current packages enable `CONFIG_SCHED_CLASS_EXT=y`, BPF and BTF, without repackaging that vendor module. Module loading and actual game scheduling remain unverified on a device.
Skipping the older patch does not mean disabling stock Fengchi.

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
are retained; ReSukiSU behavior is unchanged. Use the fixed release link above for Ultra packages;
the older release's Ultra assets predate this patch.

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

Three experimental options are available for every device entry, all off by default:
`mem_prefetch` adds ARM64 copy prefetches, `s2idle_wakeup` coalesces repeated s2idle
wake attempts, and `mlgo` enables the selected Clang's release register allocator.
They can be selected independently or together. The patches require zero-fuzz
preflight on Pad 2 Pro A15 / 6.6.57, Pad 2 Pro A16 / 6.6.118 or Pad 3 Pro A16 / 6.12.58.
MLGO retains O2, requires FAST_BUILD and CONFIG_LTO_NONE=y, and compiles a real
AArch64 probe before the build. Unsupported compilers fail instead of ignoring
the request. Build validation preserves source/dependency evidence and checks
the final MLGO flags; reports include the compiler version and binary hash.
No tablet performance or battery gains are claimed without device tests.
Compiler-content checks also prevent cache reuse across changed compilers.
