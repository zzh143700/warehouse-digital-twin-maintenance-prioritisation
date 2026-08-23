# 可复现源码包：运行与复现说明

## 1. 这个文件夹用于什么

本文件夹是论文方法与结果对应的独立源码包。它可以在Windows电脑上从FD001原始文本开始，依次完成：

```text
原始C-MAPSS FD001文本
→ 数据结构检查与未截顶RUL目标构造
→ Ridge和Gradient Boosting训练及C-MAPSS测试
→ 五分位受控的替代退化输入分配
→ 作者构建的仓库维护优先级指数
→ RUL-only与criticality-only基线比较
→ 评分、权重、规划窗口、分配设计、消融和预测噪声敏感性分析
→ 自动核验输出是否完整
→ 交互式dashboard即时重算并用颜色与文字标签展示当前维护优先级（红色为Top 1）
```

方法边界必须保持不变：模型预测的是C-MAPSS涡扇发动机RUL。进入仓库情景后，预测数值只称为`surrogate degradation input`或“替代退化输入”，不能称为仓库资产RUL预测。仓库层的结果只能支持概念验证和内部行为评价。

## 2. 文件夹结构

```text
2026-08-04_reproducible_code_package/
├─ run_all.ps1                         一键运行入口
├─ run_dashboard.ps1                   dashboard启动入口
├─ requirements.txt                    固定版本的Python依赖
├─ README_运行与复现说明.md             本文档
├─ DELIVERY_NOTE_本次调整说明_2026-08-04.md
├─ src/
│  ├─ prepare_fd001_data.py            数据准备和质量检查
│  ├─ run_fd001_models.py              RUL模型训练与测试
│  ├─ run_warehouse_priority_simulation.py
│  ├─ dashboard_logic.py               dashboard共享计算与校验逻辑
│  └─ verify_outputs.py                自动检查输出完整性
├─ dashboard/
│  ├─ streamlit_app.py                 基础交互界面
│  └─ screenshots/                     浏览器核验截图
├─ tests/
│  └─ test_dashboard_logic.py          dashboard回归测试
├─ source_data/                        NASA FD001原始文本副本
├─ input_data/                         处理后、可直接建模的CSV
├─ docs/
│  ├─ warehouse_scenario_protocol.md
│  ├─ DATA_PROVENANCE.md
│  └─ OUTPUT_DICTIONARY.md
└─ outputs/
   ├─ data_audit/
   ├─ model_outputs/
   └─ ranking_outputs/
```

`src`只保存源码，`outputs`只保存运行结果。论文正文不放入这个文件夹，从而避免把学术写作文件和可执行代码混在一起。

## 3. 电脑环境要求

- Windows 10或Windows 11；
- 64位Python 3.11至3.13；
- 能够使用PowerShell；
- 首次安装依赖时需要网络连接；
- 建议至少保留2 GB可用磁盘空间和4 GB内存。

本次实测中，模型阶段约用6分24秒，优先级与敏感性阶段约用3分15秒，完整运行约需10分钟。不同电脑的时间可能明显不同；模型搜索阶段数分钟没有新终端输出并不表示程序停止。

本包已在以下环境完成实测：

- Windows 11；
- Python 3.13.9；
- NumPy 2.3.5；
- pandas 2.3.3；
- SciPy 1.16.3；
- scikit-learn 1.9.0；
- joblib 1.5.3。
- Altair 5.5.0；
- Streamlit 1.50.0。

## 4. 最简单的运行方法

在文件资源管理器中打开本文件夹，在地址栏输入`powershell`并按Enter。随后运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -InstallDependencies
```

第一次运行会：

1. 在本文件夹创建独立的`.venv`虚拟环境；
2. 安装`requirements.txt`中的固定版本依赖；
3. 从`source_data`重新生成`input_data`；
4. 训练并测试两个RUL模型；
5. 运行仓库优先级及全部敏感性实验；
6. 自动检查关键文件、行数、种子数量、五分位覆盖和数学约束。

以后依赖已经安装时，只需运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1
```

正常结束时，最后一行应显示`All required checks passed`和`Completed successfully`。

如果已经运行完毕，只想重新检查现有输出，可以执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -VerifyOnly
```

### 启动basic priority dashboard

第一次启动并安装固定依赖：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_dashboard.ps1 -InstallDependencies
```

以后直接运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_dashboard.ps1
```

浏览器默认打开`http://localhost:8501`。编辑五项资产的`Surrogate RUL input`或调整规划窗口后，priority score和排名会立即更新。这里的“立即更新”是概念模拟中的界面重算，不表示已经连接真实仓库传感器。

## 5. 手动分步运行

如果需要判断哪一步发生错误，可在包内虚拟环境已经创建后依次运行：

```powershell
.\.venv\Scripts\python.exe .\src\prepare_fd001_data.py
.\.venv\Scripts\python.exe .\src\run_fd001_models.py
.\.venv\Scripts\python.exe .\src\run_warehouse_priority_simulation.py
.\.venv\Scripts\python.exe .\src\verify_outputs.py
```

必须保持上述顺序。仓库模拟需要模型阶段生成的端点预测和折外预测误差。

若只测试dashboard计算逻辑，可运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 6. 如何判断结果正确

自动核验至少检查以下内容：

- 100个训练发动机和100个测试发动机；
- 1,000次五分位分层分配，共5,000条资产记录；
- 每次分配包含五项资产和五个不同五分位组；
- 28,000条相邻评分敏感性比较；
- 1,000条RUL-only比较和1,000条criticality-only比较；
- 基础权重之和等于1；
- 紧迫度单调性、同RUL后果排序、同后果RUL排序和组成维度支配检验全部通过；
- JSON中明确记录“替代退化输入”边界。
- dashboard基础情景与既有CSV得分和排名一致，输入变化、规划窗口门控、负值拒绝和CSV导出逻辑均通过测试。

在相同依赖版本和随机种子下，关键数值应接近：

| 结果 | 预期值 |
|---|---:|
| Gradient Boosting测试端点MAE | 18.157983 |
| Gradient Boosting测试端点RMSE | 24.868127 |
| 相邻评分完全排序一致率 | 0.935607 |
| 相邻评分最高优先资产一致率 | 0.963964 |
| 预测噪声最高优先资产一致率 | 0.802000 |

运行时间可能因电脑性能而不同，因此拟合时间和推理时间不要求完全相同。模型误差和排名结果若出现明显变化，先检查Python与依赖版本、源数据哈希以及脚本是否被修改。

## 7. 主要输出应该怎样使用

### 数据阶段

`outputs/data_audit/fd001_data_preparation_summary.json`保存源文件哈希、数据行数、发动机数量、缺失值、重复行和常量变量。该文件用于证明输入结构与处理过程可追溯。

### C-MAPSS模型阶段

`outputs/model_outputs/model_run_summary.json`是最重要的机器可读汇总。Chapter 4中的模型选择、交叉验证以及测试端点MAE/RMSE应以该文件为准。

`outputs/model_outputs/fd001_test_endpoint_predictions.csv`保存100个测试发动机的真实端点RUL和模型预测。这里只能解释为C-MAPSS模型结果。

### 仓库优先级阶段

`outputs/ranking_outputs/warehouse_ranking_summary.json`保存方法边界、五分位范围、基础权重、基线比较、评分敏感性和噪声稳定性。

`warehouse_base_mapping_and_ranking.csv`只是一组种子42示例，不能单独用于宣称方法稳定。主要结论必须结合1,000次重复实验和敏感性结果。

全部文件的用途见[OUTPUT_DICTIONARY.md](docs/OUTPUT_DICTIONARY.md)。

## 8. 如果需要修改参数

核心参数位于`src/run_warehouse_priority_simulation.py`开头，包括：

- `BASE_HORIZON = 125.0`；
- `ASSIGNMENT_REPETITIONS = 1_000`；
- `NOISE_REPETITIONS = 1_000`；
- `BASE_WEIGHTS`和`WEIGHT_SCHEMES`；
- `ASSETS`中的五项虚拟资产和基础评分。

不要只修改一个数字后选择更好看的结果。任何参数修改都必须遵循：

1. 先写明新的criteria和修改理由；
2. 同时修改`docs/warehouse_scenario_protocol.md`；
3. 保证所有权重总和仍为1；
4. 重新运行全部受影响的基线和敏感性检验；
5. 在新的交付说明文档中记录旧值、新值、原因和结果变化；
6. 论文中把变化解释为情景依赖，而不是证明新参数“更准确”。

## 9. 常见问题

### PowerShell禁止运行脚本

使用README中的完整命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -InstallDependencies
```

该设置只作用于这一次PowerShell调用，不需要永久修改电脑策略。

### 提示找不到Python

安装64位Python 3.11至3.13，并在安装界面勾选“Add Python to PATH”。重新打开PowerShell后运行`py --version`或`python --version`检查。

### 提示缺少numpy、pandas或sklearn

重新执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -InstallDependencies
```

### OneDrive路径中包含空格或中文

一键脚本使用绝对路径组合，不要求移动文件夹。手动运行时应保留命令中的引号，或先进入本文件夹再执行相对路径命令。

### 结果文件已经存在

再次运行会覆盖同名结果文件，但不会删除其他文件。若要保留旧结果，应先复制整个代码包并在新副本中运行。

## 10. 论文中的正确表述

可以写：

> The executable workflow was preserved as a separate reproducibility package containing source-data checks, model training, prioritisation simulation, pinned dependencies, recorded seeds and automated output verification.

> A basic interactive dashboard recalculates and displays the current scenario priority ranking immediately after the surrogate degradation inputs or planning horizon are updated. It is not connected to live warehouse sensors.

不应写：

- “模型预测了五项仓库资产的RUL”；
- “敏感性分析验证了真实仓库优先级”；
- “该方法是标准FMEA/FMECA”；
- “模拟证明能够降低实际成本或提高吞吐量”。

## 11. 后续每次交付的固定规则

以后每次生成新的模型、章节、图表或实验结果，都应建立日期化文件夹，并至少附带一个`DELIVERY_NOTE_日期.md`。说明文档必须记录：工作目的、输入文件、生成或修改的文件、运行方法、关键结果、解释边界、已完成检查以及下一步。涉及代码时还必须包含依赖、随机种子、参数criteria、敏感性分析和自动核验方法。
