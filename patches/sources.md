# Patch sources

These patches retain their upstream source identifiers and licensing notices.
Imported C identifiers are kept as upstream interfaces.

| Local patch | Source repository and immutable revision | Upstream path |
| --- | --- | --- |
| `adios_6_6.patch` | [qdykernel/Build_Oneplus_Realme_Action](https://github.com/qdykernel/Build_Oneplus_Realme_Action/tree/44ad196f918ae34d19b6629710da974d27eec816) | `patch/adios_ioscheduler_6.6.patch` |
| `adios_6_12.patch` | [firelzrd/adios](https://github.com/firelzrd/adios/tree/8117e935197fd45259ef77407b1c274d3386cd53) | `patches/stable/0001-linux6.12.44-ADIOS-3.3.0.patch` |
| `pad_2_pro_a16_display.patch` | [qdykernel/Build_Oneplus_Realme_Action](https://github.com/qdykernel/Build_Oneplus_Realme_Action/tree/44ad196f918ae34d19b6629710da974d27eec816) | `patch/Fix_Screen_Flickering.patch` |
| `zstd_1_5_7.patch` | [cctv18/oppo_oplus_realme_sm8750](https://github.com/cctv18/oppo_oplus_realme_sm8750/tree/1f68e2c058416a79dcdc5f5052000d8b7d3e7d36) | `zram_patch/002-zstd.patch` |
| `pad_3_pro_susfs_2_4_compat.patch` | SUSFS 6.12 commits `9b0b13f069673b9b07b713a5c66977de4d62b175` and `b213c54126fb243595ce7876e91d84d6e0861fec` | Rebase the 2.4 patch's exec include context and task_mmu hooks onto the existing 6.12.58 VMA API |

ADIOS is an optional I/O scheduler, separate from HMBIRD CPU scheduling. The
6.12 patch declares GPL-2.0. ZSTD retains the Linux/ZSTD copyright and dual
BSD/GPL notices in its source. No default I/O scheduler, qdisc or ZRAM size is
changed by enabling these build options.

The display patch is limited to Pad 2 Pro A16 / 6.6.118. ZSTD is limited to
Pad 2 Pro A15 / 6.6.57, where it applies without fuzzy matching. Both are off
by default. All optional patches require a successful dry run before mutation.

The Pad 3 Pro SUSFS compatibility patch applies to the pinned 2.4 patch itself,
only for Ultra 41184 on 6.12.58. It retains the 2.4 exec/preinit hooks and uses
the matching older VMA iteration hooks from SUSFS 2.3. No failed hunks are skipped.
