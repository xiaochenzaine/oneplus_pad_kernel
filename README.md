**简体中文** | [English](README-en.md)

# 一加 Pad Pro 内核构建

仅构建 **一加 Pad 2 Pro** 和 **一加 Pad 3 Pro** 的 SukiSU Ultra 内核。
基于 [Numbersf/Action-Build](https://github.com/Numbersf/Action-Build) 修改；保留上游 [LICENSE](LICENSE)。
本仓库独立维护，初始适配代码来自 `xiaochenzaine/Action-Build` 的 `bbca1d9f8fcf733e96ba5cda64b1ee1239216033` 提交。

[打开构建工作流](https://github.com/xiaochenzaine/oneplus_pad_kernel/actions/workflows/build_oneplus_pad.yml)

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

1. 打开 Actions → **Build OnePlus Pad Kernels** → **Run workflow**。
2. 使用默认的 `main` 分支，选择对应机型和系统版本。安卓 15 的 Pad 2 Pro 选择 **一加Pad 2 Pro A15**。
3. Pad 2 Pro 如需风驰，开启 `SCHED_HMBIRD`；其余功能按需选择。
4. 构建成功后，在该次运行的 Artifacts 下载 AnyKernel3 包及管理器产物（上游 CI 可用时）。

构建脚本和本地补丁始终来自本次运行检出的提交，不会自动切换回上游仓库。
通用选项保留 SukiSU/SUSFS、KPM/KPN、BBG、网络扩展、ZRAM、DroidSpaces、Re-Kernel 等。
`Workflow and Cache Cleanup` 用于清理本仓库的构建记录和缓存。

## 风驰

Pad 2 Pro 的补丁来自 [Numbersf/SCHED_PATCH](https://github.com/Numbersf/SCHED_PATCH/tree/sm8750)：

| 构建菜单名称 | 开启 `SCHED_HMBIRD` 时使用的补丁 |
| --- | --- |
| 一加Pad 2 Pro A15 | `fengchi_oneplus_pad_2_pro.patch` |
| 一加Pad 2 Pro A16 | `fengchi_oneplus_pad_2_pro_b.patch` |
| 一加Pad 3 Pro A16 | 当前无对应补丁，请保持关闭 |

已内置 HMBIRD 的源码不会重复添加。未找到对应补丁时会明确报错，避免套用其他设备的补丁。

## 安卓 15 兼容处理

Pad 2 Pro A15 构建会恢复官方源码缺少的完整 `TLS_STATS` 条件编译，并设置 `CONFIG_TLS_STATS=n`，
避免 TLS 统计字段改变网络命名空间布局。该修补仅用于 A15，来源为
[Android common 7b1f455c](https://android.googlesource.com/kernel/common/+/7b1f455c7143098e61cdd2298639e3c412c285f2)。
完整补丁见 [pad_2_pro_android15_tls_stats.patch](patches/pad_2_pro_android15_tls_stats.patch)。

## SukiSU 和管理器版本

`KSU_META` 保留上游格式：`管理器分支/内置分支/显示标识/内置分支提交哈希`，默认跟随 `main/builtin`，**没有固定为 40602**。
显示标识不等于真正的版本回退；构建旧版需要同时匹配 SukiSU、SUSFS 和管理器。
管理器 APK 下载自上游 CI，本仓库不重新编译或重新签名；CI 包的签名以该上游产物为准。

配置和补丁检查不代表完整编译或实机启动验证。官方公开源码分支也不等于每个系统 OTA 的精确源码。
