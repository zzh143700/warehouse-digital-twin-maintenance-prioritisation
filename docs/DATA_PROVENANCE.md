# C-MAPSS FD001数据来源与完整性记录

## 来源

- 数据集：NASA C-MAPSS Turbofan Engine Degradation Simulation Data Set；
- 数据子集：FD001；
- 来源页面：NASA Prognostics Center of Excellence Data Set Repository；
- 项目下载日期：20 July 2026；
- 原始外层压缩包：`6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip`；
- 原始外层压缩包SHA-256：`c9c5dec12a945a82e8bb4446589d7fb3cc057b5e5d81fa1a12e25ee9912ad3b2`。

本代码包保存FD001运行所需的三份原始文本副本，不修改这些文件。若将代码包公开上传，应另行确认NASA数据集页面当时适用的分发和引用要求。

## 包内原始文本SHA-256

| 文件 | SHA-256 |
|---|---|
| `train_FD001.txt` | `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8` |
| `test_FD001.txt` | `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851` |
| `RUL_FD001.txt` | `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca` |

## 预处理CSV的预期SHA-256

| 文件 | SHA-256 |
|---|---|
| `train_FD001_with_headers_and_rul.csv` | `4a86551f5e1985f3c372c9fd3ebb9685bc416996f62c96370d94245ef940817b` |
| `test_FD001_with_headers.csv` | `4d917f79d873151afea497a344ce11f39e67275177e34be519364625ad6136fb` |
| `RUL_FD001_with_unit_id.csv` | `237b1822e6fd461b3ada4c781daba392a80ac5eb2334dea27f3dee24d7cb7738` |

`src/prepare_fd001_data.py`会从三份原始文本重新生成CSV，并在`outputs/data_audit/fd001_data_preparation_summary.json`中记录本次运行的实际哈希。

## 数据解释边界

FD001表示模拟涡扇发动机退化。传感器列不能重新命名为输送机、提升机、AGV或包装设备传感器。模型仅在C-MAPSS上接受RUL评价。预测数值进入仓库模拟后只作为受控替代退化输入，不构成仓库资产测量或仓库RUL标签。
