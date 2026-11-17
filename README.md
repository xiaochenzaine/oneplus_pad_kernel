**简体中文** | [English](README-en.md)

# 一加 Pad Pro 内核构建

仅构建 **一加 Pad 2 Pro** 和 **一加 Pad 3 Pro** 的 ReSukiSU / SukiSU Ultra 内核。
基于 [Numbersf/Action-Build](https://github.com/Numbersf/Action-Build) 修改；保留上游 [LICENSE](LICENSE)。
本仓库独立维护，初始适配代码来自 `xiaochenzaine/Action-Build` 的 `bbca1d9f8fcf733e96ba5cda64b1ee1239216033` 提交。

构建入口：[一加Pad 2 Pro A15](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_pad_2_pro_a15.yml) · [一加Pad 2 Pro A16](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_pad_2_pro_a16.yml) · [一加Pad 3 Pro A16](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_pad_3_pro_a16.yml)

## 成品下载与验证

[下载已修复 Seccomp 的 Ultra 41184 AK3、官方管理器和校验报告](https://github.com/xiaochenzaine/oneplus_pad_kernel/releases/tag/pad_pro_2026_11_17_seccomp_fix)。
以下 6 套成品均已完整编译通过，并独立核对 AK3 文件清单、Image 内嵌配置、Root 版本和官方 APK 字节。

| 设备选项 | 内核版本 | ReSukiSU 35203 | Ultra 41184 | HMBIRD 风驰 |
| --- | --- | --- | --- | --- |
| 一加Pad 2 Pro A15 | 6.6.57 | [通过](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954240785) | [通过](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43953536348) | 已编入 |
| 一加Pad 2 Pro A16 | 6.6.118 | [通过](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954677418) | [通过](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43954684670) | 已编入 |
| 一加Pad 3 Pro A16 | 6.12.58 | [通过](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43962282495) | [通过](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/runs/43964665574) | 原生 HMBIRD II 框架，运行待验证 |

这些成品均使用 `KPM=N/A`，未开启 ADIOS、ZSTD 升级和显示可选补丁。
22 项 Python 检查、actionlint 和相关对象编译通过；两份官方 APK 的包名、版本和签名均已验证，没有重新签名。
Pad 3 Pro / 6.12 已适配 SUSFS 的 VMA 接口、Ultra 的 LSM 注册与构建路径，并修复 Root/BBG 的静态 LSM 槽位计数。
各包实际构建提交与哈希见下载页的 `verification_results.json`，完整校验说明见 `validation_report.md`。
实机启动、原厂模块 ABI 和游戏性能尚未验证。

## 机型与系统版本

| 构建菜单名称 | 系统 | 官方源码清单 | 官方源码分支 | 内核系列 |
| --- | --- | --- | --- | --- |
| 一加Pad 2 Pro A15（默认） | 安卓 15 | `oneplus_pad_2_pro.xml` | `oneplus/sm8750_v_15.0.1_pad_2_pro` | 6.6 |
| 一加Pad 2 Pro A16 | 安卓 16 | `oneplus_pad_2_pro_b.xml` | `oneplus/sm8750_b_16.0.0_pad_2_pro` | 6.6 |
| 一加Pad 3 Pro A16 | 安卓 16 | `oneplus_pad_3_pro.xml` | `oneplus/sm8850_b_16.0_pad_3_pro` | 6.12 |

工作流仅接受以上三个选项，并校验官方清单中 common、平台和设备驱动项目的源码分支。
清单来自 [OnePlusOSS/kernel_manifest](https://github.com/OnePlusOSS/kernel_manifest) 的 `oneplus/sm8750`、`oneplus/sm8850` 分支。
Pad 3 Pro 当前没有官方安卓 15 清单，因此不提供 A15 选项。

Pad 2 Pro 的安卓 15 和安卓 16 源码都使用 `android15-6.6` GKI 分支。
该字符串不能判断设备系统版本；请按菜单里的 A15/A16 选择。修改 `RESUBLEVEL` 只会改内核显示版本，不能移植安卓版本。

## 构建

1. 打开 Actions，进入对应的 **一加Pad 2 Pro A15**、**一加Pad 2 Pro A16** 或 **一加Pad 3 Pro A16** 工作流，再点击 **Run workflow**。
2. 使用默认的 `main` 分支。入口已固定机型和系统版本，无需在表单中重复选择。
3. 风驰按机型处理：Pad 2 Pro 编入对应 HMBIRD 补丁；Pad 3 Pro 使用原生 HMBIRD II 所需框架，厂商模块兼容和游戏策略仍需实机确认。
4. `sukisu_profile` 选择 ReSukiSU 35203（默认）或 SukiSU Ultra 41184；ReSukiSU 保持 `KPM=N/A`。
5. 构建成功后，在该次运行的 Artifacts 下载 AnyKernel3 包、官方管理器和校验报告。

构建脚本和本地补丁始终来自本次运行检出的提交，不会自动切换回上游仓库。
三个入口共用 `build_oneplus_pad.yml` 编译流程。GitHub 表单无法根据机型动态隐藏选项，因此在入口层区分可选功能；共用流程也会在下载源码和清理磁盘前再次校验参数。
**内部公共编译流程**由这三个入口自动调用，无需单独运行。

| 功能 | Pad 2 Pro A15 | Pad 2 Pro A16 | Pad 3 Pro A16 |
| --- | --- | --- | --- |
| 自定义 ZRAM | 可选，默认保留系统配置 | 可选，默认保留系统配置 | 不显示；缺少对应 6.12 补丁 |
| 升级 LZ4 | 可选，默认关闭 | 可选，默认关闭 | 不显示；尚未完成适配验证 |
| 升级 ZSTD 1.5.7 | 可选，默认关闭 | 不显示 | 不显示 |
| 显示兼容补丁 | 不显示 | 可选，默认关闭 | 不显示 |
| ADIOS I/O 调度 | 可选，默认关闭 | 可选，默认关闭 | 可选，默认关闭 |

`zram=system` 表示保留系统原有 ZRAM，并非关闭系统 ZRAM；旧的 `0/lz4kd/8589934592` 仍按保留系统配置处理。
Pad 2 Pro 可填写 `1/lz4kd/8589934592` 请求自定义算法和 8 GiB 逻辑容量，需要另外安装该次构建生成的 ZRAM 模块。
算法和容量在模块启动时应用；仅刷 AK3 不代表该配置已经生效。容量不是提前占用同等大小的物理内存。
自定义 ZRAM 与 LZ4 升级可以组合选择，但当前组合尚未完成构建和实机验证；`lz4kd` 与普通 LZ4 是不同实现，升级 LZ4 不直接升级 `lz4kd`。
每次运行的摘要与 `build_manifest.json` 会记录所选机型、ZRAM、LZ4 及验证范围。

## 风驰

Pad 2 Pro 的补丁来自 [Numbersf/SCHED_PATCH](https://github.com/Numbersf/SCHED_PATCH/tree/sm8750)：

| 构建菜单名称 | 自动使用的风驰补丁 |
| --- | --- |
| 一加Pad 2 Pro A15 | `fengchi_oneplus_pad_2_pro.patch` |
| 一加Pad 2 Pro A16 | `fengchi_oneplus_pad_2_pro_b.patch` |
| 一加Pad 3 Pro A16 | 原厂 HMBIRD II / sched_ext 路线，跳过 Pad 2 Pro 的补丁 |

已内置 HMBIRD 的源码不会重复添加。未找到对应补丁时会明确报错，避免套用其他设备的补丁。

Pad 3 Pro 官方源码包含 [HMBIRD II](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8850/tree/8be53e8b737a83a33512d5e0106cccb010a5c24c/vendor/oplus/kernel/cpu/sched_ext)，以 `oplus_bsp_sched_ext` 厂商模块构建。
当前成品确认 `CONFIG_SCHED_CLASS_EXT=y`、BPF 和 BTF 支持，未重新打包该厂商模块；模块是否成功加载和游戏时是否生效仍待实机验证。
跳过旧 HMBIRD 补丁不代表关闭系统原厂风驰。

## 安卓 15 兼容处理

Pad 2 Pro A15 构建会恢复官方源码缺少的完整 `TLS_STATS` 条件编译，并设置 `CONFIG_TLS_STATS=n`，
避免 TLS 统计字段改变网络命名空间布局。该修补仅用于 A15，来源为
[Android common 7b1f455c](https://android.googlesource.com/kernel/common/+/7b1f455c7143098e61cdd2298639e3c412c285f2)。
完整补丁见 [pad_2_pro_android15_tls_stats.patch](patches/pad_2_pro_android15_tls_stats.patch)。

## Root 与管理器配套

| `sukisu_profile` | 内核 Root / 官方管理器 | SUSFS | 默认 |
| --- | --- | --- | --- |
| `resukisu_35203` | ReSukiSU v4.2.0-rc3 / 35203（更名前历史版） | 2.3.0 | 是 |
| `ultra_41184` | SukiSU Ultra v4.3.0-r2 / 41184 | 2.4.0 | 否 |

两项均面向以上三套设备源码提供构建选项，41184 本身不要求安卓 16。
安卓系统选择决定 OEM 内核和驱动源码；Root 版本由另一个菜单独立选择。
ReSukiSU 官方仓库已更名为 BakaSU，本仓库固定其更名前提交，不会自动跟随 BakaSU。

源码提交、上游提交数量、SUSFS 提交、APK 版本/包名/证书和 SHA256 均锁定在
[config/sukisu_profiles.json](config/sukisu_profiles.json)。构建前下载原始官方 APK，校验任意一项失败即停止。
APK 镜像保存原始字节，并记录官方 CI 来源；本仓库不重新编译或重新签名管理器。
ReSukiSU 与 Ultra 使用不同的官方签名，请安装所选实现对应的 APK。
ReSukiSU 默认关闭多管理器支持，不添加自定义受信任证书。

内核编译期间不会通过移动的 main 分支或最新 Release 动态计算 Root 版本。
构建后检查真实 .config、编译命令中的版本号、源码提交以及 APK 签名，生成
build_manifest.json、sha256sums 和独立的 kernel_validation 产物。
校验要求启用 SECCOMP、SECCOMP_FILTER 和强栈保护；A15 同时检查 TLS_STATS=n。

## Seccomp 状态

官方管理器的这一行通过 `PR_GET_SECCOMP` 读取自身线程，不能代表整个内核或其他应用。
历史 Ultra 41184 会在管理器启动时主动取消它的过滤，所以即使内核启用 SECCOMP 也会显示“未启用”。
本仓库现对三个机型共用 [管理器 Seccomp 修补](patches/ultra_manager_seccomp.patch)：
在 SUSFS 的 zygote 和 zygote_next 两条管理器启动路径保留原有过滤，同时保留官方 APK 使用的驱动 fd。
实际执行 `su` 的 Root 会话继续采用原上游处理。APK 不修改、不重签，ReSukiSU 的处理也不变。
这项修补用于之后的新构建；旧下载页中的 Ultra 成品是修补前版本，请使用上面的修复版下载页。

更新内核并重启后，重新打开管理器检查。需要客观核实时，可从 AK3 中提取
[check_seccomp.sh](scripts/check_seccomp.sh)，在设备上运行：

```sh
su -c 'sh /sdcard/Download/check_seccomp.sh com.sukisu.ultra com.android.settings'
```

先打开管理器和待检查的普通应用；示例的系统设置可换成任一未授予 Root 的应用包名。
脚本只读配置和进程状态，不修改设备，也不发送数据。`Seccomp: 2` 表示被检查进程使用过滤模式；
Root shell 的 `Seccomp: 0` 不能用于判断普通应用。仍需实机验证管理器识别内核、Root 授权、
`su -c id` 和模块页面正常；编译通过不能代替这些检查。

## 可选改进

- `adios`：编入 ADIOS I/O 调度器，保留原默认 I/O 调度。它与风驰 CPU 调度是不同功能。
- `zstd_update`：ZSTD 升级至 1.5.7，目前仅开放 Pad 2 Pro A15 / 6.6.57；不改变 ZRAM 大小或默认算法。
- `display_fix`：仅用于 Pad 2 Pro A16 / 6.6.118 的显示兼容修补。
- `NETFILTER`：增加 FQ、FQ_CODEL、CAKE、PIE、FQ_PIE 支持，保留系统默认网络队列。

前三项默认关闭。补丁在修改源码前必须通过 dry run，来源与适用范围见
[patches/sources.md](patches/sources.md)。不适用的机型或源码版本会停止构建。
ReSukiSU 不提供 Ultra 的 KPM 实现，因此不允许与 KPM / KPN 混选。

构建成功仅代表编译及产物校验通过。报告会单独注明原厂模块 ABI 和实机启动是否已验证；
官方公开源码分支也不等于每个系统 OTA 的精确源码。
