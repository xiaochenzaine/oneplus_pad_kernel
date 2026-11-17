# Patch sources

These patches retain their upstream source identifiers and licensing notices.
Imported C identifiers are kept as upstream interfaces.

| Local patch | Source repository and immutable revision | Upstream path |
| --- | --- | --- |
| `adios_6_6.patch` | [qdykernel/Build_Oneplus_Realme_Action](https://github.com/qdykernel/Build_Oneplus_Realme_Action/tree/44ad196f918ae34d19b6629710da974d27eec816) | `patch/adios_ioscheduler_6.6.patch` |
| `adios_6_12.patch` | [firelzrd/adios](https://github.com/firelzrd/adios/tree/8117e935197fd45259ef77407b1c274d3386cd53) | `patches/stable/0001-linux6.12.44-ADIOS-3.3.0.patch` |
| `pad_2_pro_a16_display.patch` | [qdykernel/Build_Oneplus_Realme_Action](https://github.com/qdykernel/Build_Oneplus_Realme_Action/tree/44ad196f918ae34d19b6629710da974d27eec816) | `patch/Fix_Screen_Flickering.patch` |
| `zstd_1_5_7.patch` | [cctv18/oppo_oplus_realme_sm8750](https://github.com/cctv18/oppo_oplus_realme_sm8750/tree/1f68e2c058416a79dcdc5f5052000d8b7d3e7d36) | `zram_patch/002-zstd.patch` |
| `mem_prefetch.patch` | [WildKernels/kernel_patches](https://github.com/WildKernels/kernel_patches/tree/e86915e3ff30fc316c6b0764ba0b1eaf22ba0b44), original change `2ce22c11c862dadcb129007e58856cb5e918be99` | `common/mem_opt_prefetch.patch` |
| `s2idle_wakeup.patch` | [WildKernels/kernel_patches](https://github.com/WildKernels/kernel_patches/tree/e86915e3ff30fc316c6b0764ba0b1eaf22ba0b44), original change `d7b472cd88bfb58b75792f3e8c5ecbfe384a55d7` | `common/avoid_extra_s2idle_wake_attempts.patch` |
| `pad_3_pro_susfs_2_4_compat.patch` | SUSFS 6.12 commits `9b0b13f069673b9b07b713a5c66977de4d62b175` and `b213c54126fb243595ce7876e91d84d6e0861fec` | Rebase the 2.4 patch's exec include context and task_mmu hooks onto the existing 6.12.58 VMA API |
| `ultra_6_12_compat.patch` | Local API port of Ultra `f9aa2fec23c3f4a06a935f69dc04cb85b261e7f3` against OnePlus common `6d16e5c7628c17cce37f03cad3bcb3bbece9d3fc` | Register a persistent `struct lsm_id` with the modern `security_add_hooks` API and resolve the preinit source path for in-tree O=out builds |
| `pad_3_pro_lsm_count.patch` | Local integration fix for OnePlus common `6d16e5c7628c17cce37f03cad3bcb3bbece9d3fc` | Reserve static LSM slots for builtin KSU and BBG, instead of exceeding the compiled table capacity |
| `ultra_manager_seccomp.patch` | Local fix against Ultra builtin `f9aa2fec23c3f4a06a935f69dc04cb85b261e7f3` | Preserve the manager's existing seccomp filter in both SUSFS zygote paths while retaining driver-fd installation and root-profile handling |

ADIOS is an optional I/O scheduler, separate from HMBIRD CPU scheduling. The
6.12 patch declares GPL-2.0. ZSTD retains the Linux/ZSTD copyright and dual
BSD/GPL notices in its source. No default I/O scheduler, qdisc or ZRAM size is
changed by enabling these build options.

The memory prefetch and s2idle wakeup patches are imported byte-for-byte, with
SHA256 `da6572571b56afe8d6d0aac34727a362770bfbd32359e2fd13b1c00be2063ee4`
and `0216f48b2fed634d9b308ff599de655713290cabc6b94855779207b0f2d69c38` respectively.
They require a zero-fuzz preflight and are scoped to Pad 2 Pro A15 / 6.6.57,
Pad 2 Pro A16 / 6.6.118 and Pad 3 Pro A16 / 6.12.58. Historical performance
numbers in the original messages are not benchmark results for these tablets.
The wakeup patch coalesces repeated s2idle wake attempts; it does not disable
wakeup sources, timers, notifications or thermal controls. Both are off by default.

MLGO is a compiler option, not an imported kernel patch. `prepare_mlgo.py` uses
the selected Clang's release register-allocation advisor after compiling an
AArch64 probe object. It is restricted to FAST_BUILD with CONFIG_LTO_NONE=y;
unsupported compilers fail explicitly. The final report checks the actual root
object commands and records the compiler binary hash, version and selected flags.

The display patch is limited to Pad 2 Pro A16 / 6.6.118. ZSTD is limited to
Pad 2 Pro A15 / 6.6.57, where it applies without fuzzy matching. Both are off
by default. All optional patches require a successful dry run before mutation.

The Pad 3 Pro SUSFS compatibility patch applies to the pinned 2.4 patch itself,
only for Ultra 41184 on 6.12.58. It retains the 2.4 exec/preinit hooks and uses
the matching older VMA iteration hooks from SUSFS 2.3. No failed hunks are skipped.

The LSM and Ultra compatibility patches apply only to the 6.12 target. The slot count follows
CONFIG_KSU and CONFIG_BBG; disabled modules do not reserve slots. The Ultra
registration uses an internal undefined LSM id and does not add security-context
APIs or change the manager trust list.

The manager seccomp patch applies to Ultra 41184 on all three device targets.
The official manager reads its own calling thread with `PR_GET_SECCOMP`; this is
not a kernel-wide enable switch. The patch removes only the two manager-specific
`disable_seccomp()` calls under `CONFIG_KSU_SUSFS`. It preserves the injected
driver descriptor used by the official APK's ioctl interface. The authorized-app
branches, non-SUSFS fallback and actual root-profile filter handling are retained.
No syscall cache is broadened or private seccomp structure layout duplicated.
