# 输出文件说明与Chapter 4使用建议

## 1. 数据检查输出

| 文件 | 内容 | 论文用途 |
|---|---|---|
| `data_audit/fd001_data_preparation_summary.json` | 行数、发动机数量、缺失值、重复行、周期连续性、常量变量和文件哈希 | 方法可复现性与数据质量证据 |
| `data_audit/fd001_data_preparation_summary.md` | 便于人工阅读的检查摘要 | 写作时快速核对，不作为模型结果 |

## 2. 模型输出

| 文件 | 内容 | 论文用途 |
|---|---|---|
| `model_outputs/model_run_summary.json` | 软件版本、输入哈希、候选选择规则、交叉验证与官方测试指标 | Chapter 4模型结果的主数据源 |
| `model_outputs/model_cv_search_results.csv` | Ridge和Gradient Boosting全部候选配置的汇总 | 说明超参数不是凭最终测试集选择 |
| `model_outputs/model_cv_fold_metrics.csv` | 各折MAE和RMSE | 展示分组验证的离散程度 |
| `model_outputs/selected_model_oof_predictions.csv` | 所选Gradient Boosting的训练折外预测与残差 | 仓库层预测噪声敏感性输入 |
| `model_outputs/fd001_test_endpoint_predictions.csv` | 100个测试发动机的官方标签及两个模型预测 | 端点误差表或散点图的数据源 |
| `model_outputs/gradient_boosting_feature_importance.csv` | 特征重要性 | 可选辅助结果，避免过度因果解释 |
| `model_outputs/models/*.joblib` | 拟合后的模型文件 | 复现和存档，不放入正文 |
| `model_outputs/model_results_summary.md` | 自动生成的可读摘要 | 快速核对 |

模型结果只评价C-MAPSS。Gradient Boosting的当前预期测试端点MAE为18.157983，RMSE为24.868127。

## 3. 仓库优先级输出

### 基础示例与公式检查

| 文件 | 内容 | 论文用途 |
|---|---|---|
| `warehouse_base_mapping_and_ranking.csv` | 种子42下五项资产、替代输入、三项评分和三类排序 | 用作方法演示表，不单独证明稳定性 |
| `warehouse_controlled_checks.json` | 权重和、单调性、等输入及支配性检查 | 证明公式符合预先声明的数学行为 |
| `warehouse_ranking_summary.json` | 全部核心设定与汇总指标 | Chapter 4优先级结果的主数据源 |

### 基线比较

| 文件 | 内容 | 论文用途 |
|---|---|---|
| `warehouse_mapping_vs_rul_only_stability.csv` | 1,000次综合排序与RUL-only比较 | 判断指数是否主要重复紧迫度 |
| `warehouse_mapping_vs_criticality_only_stability.csv` | 1,000次综合排序与criticality-only比较 | 判断指数是否只重复资产关键度 |

报告Spearman、Kendall、完全排序一致率和最高优先资产一致率。不要把相关性称为准确率。

### 替代输入分配

| 文件 | 内容 | 论文用途 |
|---|---|---|
| `warehouse_mapping_monte_carlo_rows.csv` | 五分位分层下1,000次、5,000条资产记录 | 资产排名概率和分布 |
| `warehouse_mapping_monte_carlo_summary.csv` | 各资产平均排名、排名标准差和最高优先概率 | Chapter 4汇总表候选 |
| `warehouse_unstratified_assignment_rows.csv` | 相同种子下的无分层替代设计 | 分配设计敏感性 |
| `warehouse_assignment_design_sensitivity_summary.csv` | 分层与无分层结果的并列表 | 说明结论依赖输入分配规则 |

### 情景参数与公式敏感性

| 文件组 | 内容 | 论文用途 |
|---|---|---|
| `warehouse_score_sensitivity_*` | 每个可行1--5评分上下移动一个锚点，共28,000次比较 | 检验作者赋值的不确定性 |
| `warehouse_sensitivity_*` | 三个规划窗口与四套权重 | 判断参数依赖性 |
| `warehouse_ablation_*` | 依次移除关键度、吞吐量或严重度 | 判断每一维的边际作用 |

相邻评分下完全排序一致率约为93.56%，最高优先资产一致率约为96.40%。规划窗口的影响明显大于基础权重变化，应在Discussion中重点解释。

### 预测误差稳健性

| 文件 | 内容 | 论文用途 |
|---|---|---|
| `warehouse_noise_monte_carlo_rows.csv` | 使用中心化C-MAPSS折外残差扰动后的资产结果 | 观察预测误差怎样传播到排序 |
| `warehouse_noise_rank_stability.csv` | 每次扰动与基础排序的比较 | 报告排序稳定性 |
| `warehouse_noise_monte_carlo_summary.csv` | 各资产扰动后排名汇总 | 辅助表 |

噪声实验不是仓库不确定性的校准模型。其最高优先资产一致率约为80.2%，只能说明排名对C-MAPSS模型误差的内部稳健性。

## 4. Chapter 4推荐保留的核心表格

正文建议保留：

1. Ridge与Gradient Boosting的交叉验证和测试端点MAE/RMSE；
2. 种子42的五资产示例表；
3. RUL-only与criticality-only的1,000次比较汇总；
4. 分配设计、相邻评分、权重、规划窗口、消融和噪声敏感性汇总。

详细的5,000条资产记录和28,000条评分比较放入代码包或附录，不应占用正文篇幅。
