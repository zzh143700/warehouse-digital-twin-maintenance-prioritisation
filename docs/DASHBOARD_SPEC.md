# Basic Priority Dashboard Specification / 基础优先级Dashboard说明

**Recorded / 记录日期：** 16 August 2026 / 2026年8月16日

## 1. Supervisor Requirement / 导师要求

**English**

The dissertation should include a basic dashboard that displays current maintenance priorities. The dashboard does not need to be complex and should be introduced briefly in the dissertation.

**中文对照**

论文需要包含一个能够展示当前维护优先级的基础dashboard。界面不需要复杂，并在论文中作简要介绍。

## 2. Implemented Scope / 已实现范围

- **Editable input / 可编辑输入：** the surrogate RUL input for each of five virtual warehouse assets / 五项虚拟仓库资产各自的代理RUL输入。
- **Scenario control / 情景控制：** planning horizon \(H=50\)–\(200\) abstract cycles, with \(H=125\) as the base case / 规划窗口可在50–200个抽象周期内调整，基础值为\(H=125\)。
- **Immediate recalculation / 即时重算：** editing an input or changing \(H\) immediately recalculates urgency, consequence, priority score and rank / 编辑输入或调整\(H\)后，立即重新计算紧迫度、后果、优先级得分及排名。
- **Headline output / 核心输出：** current top-priority asset, its priority score and the number of assets inside the active horizon / 当前首位资产、其优先级得分以及有效窗口内的资产数量。
- **Visual output / 可视化输出：** a ranked horizontal bar chart and a compact priority table. Top 1 is red, followed by orange, amber, blue and grey; text rank labels remain visible so colour is not the only cue / 排序后的横向柱状图和紧凑优先级表。Top 1使用红色，其后依次为橙色、琥珀色、蓝色和灰色；同时保留文字排名标签，避免仅依赖颜色传递信息。
- **Audit output / 审计输出：** downloadable CSV containing rank, asset, role, surrogate input, urgency, consequence and priority score / 可下载CSV，包含排名、资产、角色、代理输入、紧迫度、后果及优先级得分。
- **Reset / 重置：** restores the seed-42 base inputs and \(H=125\) / 恢复种子42基础输入和\(H=125\)。

## 3. Calculation / 计算方式

The dashboard imports the same `score_assets` function used by the reproducible simulation. It does not duplicate or alter the dissertation formula:

Dashboard直接导入可复现模拟所使用的同一个`score_assets`函数，不复制或修改论文公式：

\[
U_i=\max\left(0,1-\frac{R_i}{H}\right),
\]

\[
K_i=\frac{1}{3}\frac{C_i}{5}+\frac{1}{3}\frac{T_i}{5}+\frac{1}{3}\frac{S_i}{5},
\]

\[
P_i=100\times U_i\times K_i.
\]

## 4. Meaning of “Current” or “Real-Time” / “当前”或“实时”的含义

**Permitted wording / 可使用表述**

> The dashboard recalculates and refreshes maintenance priorities immediately when the surrogate degradation inputs or planning horizon are updated.

> 当代理退化输入或规划窗口更新时，dashboard会立即重新计算并刷新维护优先级。

**Boundary / 边界**

The application is not connected to live warehouse sensors, a warehouse management system or physical equipment. “Real-time” therefore describes immediate interface recalculation in the conceptual simulation, not operational data synchronisation.

该应用没有连接实时仓库传感器、仓库管理系统或物理设备。因此，“实时”仅表示概念模拟中的界面即时重算，而不是运营数据同步。

The colours show relative rank within the current five-asset scenario. They are interface cues, not validated operational risk categories or alarm thresholds.

颜色表示当前五资产情景中的相对排名。它们只是界面提示，并非经过验证的运营风险等级或告警阈值。

## 5. Files / 文件

- `dashboard/streamlit_app.py`: Streamlit interface / Streamlit界面。
- `src/dashboard_logic.py`: shared calculation, validation and export logic / 共享计算、校验和导出逻辑。
- `tests/test_dashboard_logic.py`: five deterministic regression tests / 五项确定性回归测试。
- `run_dashboard.ps1`: Windows launch script / Windows启动脚本。
- `dashboard/screenshots/dashboard_input_view.png`: input and boundary view / 输入及边界界面截图。
- `dashboard/screenshots/dashboard_priority_output.png`: priority output view / priority输出界面截图。

## 6. Verification / 核验

- The base case reproduces the saved priority scores and ranks in `warehouse_base_mapping_and_ranking.csv`.
- Changing A2's surrogate input from approximately 121.8 to 0 changes the top asset from A1 to A2 and raises the displayed top score from 49.43 to 93.33.
- Moving the planning horizon to 50 changes the top score to 23.58 and the active-asset count to two; Reset restores \(H=125\), a 49.43 top score and four active assets.
- Negative surrogate inputs are rejected.
- The CSV export is generated successfully.
- Browser inspection found no console errors.

- 基础情景能够复现`warehouse_base_mapping_and_ranking.csv`中的既有优先级得分和排名。
- 将A2的代理输入从约121.8改为0后，首位资产由A1变为A2，最高得分由49.43变为93.33。
- 将规划窗口调整为50后，最高得分变为23.58，有效资产数变为2；Reset可恢复\(H=125\)、49.43的最高得分和4项有效资产。
- 负代理输入会被拒绝。
- CSV导出已成功触发。
- 浏览器检查未发现控制台错误。

## 7. Suggested Brief Dissertation Description / 建议写入论文的简短介绍

**English**

> A basic interactive dashboard was implemented as the visual interface of the conceptual warehouse digital twin. The dashboard loads the five-asset base scenario and recalculates the author-developed priority index whenever a surrogate degradation input or the planning horizon is changed. It displays the current top-priority asset, ranked priority scores and the number of assets within the active horizon, and allows the current ranking to be exported as a CSV file. The interface provides immediate scenario feedback, but it is not connected to live warehouse sensors and therefore does not demonstrate operational real-time synchronisation.

**中文对照**

> 本研究构建了一个基础交互式dashboard，作为概念性仓库数字孪生的可视化界面。该dashboard加载五资产基础情景，并在代理退化输入或规划窗口发生变化时重新计算作者构建的优先级指数。界面显示当前首位资产、排序后的优先级得分和有效窗口内的资产数量，并允许将当前排序导出为CSV文件。该界面能够提供即时情景反馈，但没有连接实时仓库传感器，因此不能证明运营层面的实时同步。
