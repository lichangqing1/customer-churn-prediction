# 客户流失分析数仓与 BI 决策支持项目

## 项目定位

本项目不是单纯的机器学习分类实验，而是一个面向业务决策的客户流失分析工程项目。项目从原始 Telco Customer Churn 数据集出发，构建了数据清洗、数据质量校验、SQLite 数仓、SQL 指标集市、客户流失风险评分、留存行动队列、Streamlit 看板以及 Power BI 数据导出流程。

适合在简历或面试中定位为：

```text
Customer Churn Analytics Warehouse and BI Dashboard
客户流失分析数仓与 BI 决策支持项目
```

适配岗位：

- BI 工程师
- Analytics Engineer
- 数据质量工程师
- 初级数据开发工程师
- 数据分析师
- AI/Data 测试工程师
- 测试开发转数据/AI 方向岗位

---

## 项目解决的问题

项目主要回答以下业务问题：

1. 当前客户整体流失率是多少？
2. 哪些客户群体流失风险最高？
3. 哪些客户带来的潜在收入损失最大？
4. 企业应该优先联系哪些客户进行留存？
5. 当前看板所依赖的数据是否通过质量校验？

当前本地验证结果：

| 指标 | 结果 |
|---|---:|
| 客户总数 | 7,043 |
| 整体流失率 | 26.54% |
| 月收入总额 | 456,116.60 |
| 已评分客户数 | 1,409 |
| 预计月收入风险 | 约 42,202.51 |
| 高风险客户数 | 350 |
| pytest 测试结果 | 8 passed |

---

## 技术实现

项目实现了完整的数据到决策流程：

```text
原始 CSV 数据
→ Bronze 原始层
→ Silver 清洗层
→ 维度表 + 事实表
→ Gold 聚合表
→ SQL Mart 指标层
→ Power BI / Streamlit 看板
→ 客户留存行动队列
```

核心模块：

| 模块 | 文件/目录 | 说明 |
|---|---|---|
| 数据清洗 | `src/data_cleaning.py` | 字段标准化、TotalCharges 转换、Churn 编码 |
| 特征工程 | `src/feature_engineering.py` | 构造 tenure、charges、contract 等衍生特征 |
| 数据质量 | `src/data_quality.py` | 唯一性、空值、数值范围、引用完整性校验 |
| 数仓构建 | `src/warehouse_builder.py` | Bronze/Silver/维度表/事实表/Gold 表构建 |
| SQL 指标集市 | `sql/marts/` | 构建 Power BI 和 Streamlit 使用的 mart 视图 |
| Power BI 导出 | `scripts/export_powerbi_data.py` | 导出 5 个 CSV 给 Power BI 使用 |
| Streamlit 看板 | `dashboard/app.py` | 本地交互式业务看板 |
| Docker 部署 | `docker-compose.yml` | PostgreSQL + pipeline + Streamlit |
| Airflow 调度 | `dags/customer_churn_warehouse_dag.py` | 可选定时调度流程 |
| PySpark | `spark/build_churn_gold_tables_pyspark.py` | 可选分布式 Gold 表转换 |

---

## 数据质量亮点

项目实现了可执行的数据质量校验，而不是只在文档中描述：

- 必要字段检查
- `customer_id` 唯一性检查
- 必要字段非空检查
- `churn_flag` 取值范围检查
- tenure、monthly_charges、total_charges 数值范围检查
- Fact 表与 Silver 表行数对账
- Fact 表与维度表引用完整性检查
- Gold 表 churn_rate 范围检查

当前质量监控结果：

```text
pipeline_status = success
raw_rows = 7043
silver_rows = 7043
fact_rows = 7043
reconciliation_variance = 0
failed_quality_checks = 0
```

这可以在面试中体现数据工程和数据质量意识。

---

## Power BI 看板页面

建议展示 5 个页面：

1. Executive Overview：整体业务概览
2. Churned Customer Analysis：流失客户/高风险分群分析
3. Revenue at Risk：收入风险分析
4. Retention Action Queue：客户留存行动队列
5. Data Quality Monitor：数据质量监控

Power BI 使用的数据来自：

```text
results/powerbi_exports/
```

而不是直接读取原始 CSV。这体现了通过 SQL mart 管理业务口径的思路。

---

## 面试表达示例

可以这样介绍项目：

```text
我做了一个客户流失分析数仓与 BI 决策支持项目。这个项目不是只训练一个 churn 模型，而是从原始 Telco 客户数据开始，构建了 Bronze/Silver/Gold 分层数据管道、维度表和事实表、SQL 指标集市、数据质量校验、客户风险评分、收入风险分析和留存行动队列。最终输出可以被 Streamlit 和 Power BI 使用，用于帮助业务方识别高流失风险群体、估算潜在收入损失，并优先联系高价值高风险客户。
```

英文版本：

```text
This is a customer churn analytics warehouse and BI decision-support project. Instead of only training a churn model, I built an end-to-end data pipeline from raw Telco customer data into Bronze, Silver, Gold, fact and dimension tables, SQL marts, data quality checks, churn-risk scoring outputs, revenue-at-risk analysis, and a customer-level retention action queue. The final outputs can be consumed by Streamlit and Power BI to help business users identify high-risk customer segments, estimate potential revenue loss, and prioritize retention actions.
```

---

## 项目优势

- 有完整工程结构，不只是 notebook。
- 有测试用例和 CI。
- 有数仓分层和 SQL mart。
- 有数据质量校验和质量监控页面。
- 有 Power BI 和 Streamlit 两种展示方式。
- 有 Docker/PostgreSQL、Airflow、PySpark 扩展路径。
- 项目能体现测试工程背景向数据质量、BI 和 AI 评测方向迁移的能力。

---

## 注意事项

面试中不要把它夸大为完整企业级生产系统。更准确的说法是：

```text
这是一个 production-style portfolio project，展示了数据管道、数仓建模、BI 指标、质量校验和客户留存决策支持的完整思路。
```

当前限制包括：

- 数据集是静态公开数据；
- 收入风险和留存队列基于 1,409 个已评分客户；
- 模型评分结果目前作为结果文件加载，而不是完整的生产级定时评分服务；
- 尚未接入真实营销活动反馈和 ROI 跟踪。
