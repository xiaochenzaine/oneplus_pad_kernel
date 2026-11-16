# 支持的构建配置

仅保留一加 Pad 2 Pro 和 Pad 3 Pro，默认选择 **一加Pad 2 Pro A15**。

| 菜单名称 | 清单文件 | 官方清单仓库分支 | 源码 revision | CPU / 构建目标 |
| --- | --- | --- | --- | --- |
| 一加Pad 2 Pro A15 | `oneplus_pad_2_pro.xml` | `oneplus/sm8750` | `oneplus/sm8750_v_15.0.1_pad_2_pro` | `sm8750` / `sun perf` |
| 一加Pad 2 Pro A16 | `oneplus_pad_2_pro_b.xml` | `oneplus/sm8750` | `oneplus/sm8750_b_16.0.0_pad_2_pro` | `sm8750` / `sun perf` |
| 一加Pad 3 Pro A16 | `oneplus_pad_3_pro.xml` | `oneplus/sm8850` | `oneplus/sm8850_b_16.0_pad_3_pro` | `sm8850` / `canoe perf` |

清单仓库：[OnePlusOSS/kernel_manifest](https://github.com/OnePlusOSS/kernel_manifest)。
菜单名称与内部清单文件名的对应关系由 [resolve_pad_manifest.py](scripts/resolve_pad_manifest.py) 定义。
详细操作、风驰支持范围与版本说明见 [README](README.md)。
