# ai-job-analyzer｜招聘 JD 结构化提取与评测

一个用于学习 **LLM 应用开发与模型评测** 的 Python 个人项目：将招聘岗位描述（JD）提取为固定九字段 JSON，对结果做结构校验，并通过固定测试集记录模型表现和错误类型。

> **项目状态：核心流程已实现，仍处于个人项目迭代阶段。** 目前是命令行批处理脚本，不是已上线的招聘推荐平台；没有实现岗位推荐、自动投递、Agent 或 RAG。项目目标是让岗位信息更方便比较，并评估模型提取是否可靠。

## 已实现的功能

- 使用 Python 调用经阿里云百炼兼容接口访问的 `deepseek-v4.1-flash`，结合版本化 Prompt 批量处理 JD。
- 提取九个字段：`job_title`、`company`、`location`、`education`、`major_requirement`、`required_skills`、`preferred_skills`、`attendance`、`duration`。
- 使用 JSON Mode 获取结构化输出，解析 JSON，并验证字段是否齐全、类型是否正确；记录调用和结构错误。
- 保存每次批量提取结果、错误记录、运行元数据（模型、Prompt 版本、Token、耗时）。
- 提供人工标注规范、开发集和真实 JD 测试集；用脚本进行逐字段**精确匹配**评测，另外保留语义复核和错误分析记录。

## 技术与流程

- Python、OpenAI Python SDK（兼容接口）、python-dotenv、JSON。
- 当前实验配置：`deepseek-v4.1-flash`、`prompts/v3.txt`、`USE_SCHEMA=False`（JSON Mode；不是启用严格 JSON Schema 的实验）。

```text
JD 数据（eval_cases.json 或 testset/test_cases.json）
              │
              ▼
main.py：读取 Prompt → 调用 LLM → JSON 解析
              │
              ▼
validator.py：字段存在性及类型检查
              │
              ▼
outputs/：保存 batch_output / batch_errors / run_summary
              │
              ▼
evaluate.py：与 expected 比较，统计逐字段精确匹配
breakdown.py：按数据子集、空值与非空字段分组统计精确匹配
```

**边界说明**：`validator.py` 检查的是数据结构，不检查提取内容的真实性，目前也未显式拒绝多余键。`evaluate.py` 自动计算的是**精确匹配**，不是自动语义评测；语义等价需要另行复核。

## 项目目录

| 路径 | 用途 |
| --- | --- |
| `main.py` | 批量调用模型、解析/校验、保存运行记录 |
| `validator.py` | 九字段完整性与类型校验 |
| `evaluate.py` | 对指定数据集的模型输出计算精确匹配 |
| `breakdown.py` | 精确匹配的分组统计 |
| `prompts/` | v1、v2、v2_1、v3 Prompt 版本及演进记录 |
| `eval_cases.json` | 四条开发用例（其中三条为模拟 JD） |
| `testset/test_cases.json` | 十条真实招聘 JD 及冻结人工标准答案 |
| `testset/annotation_questions.md` | 标注时的歧义与裁定依据 |
| `annotation_guide.md`、`judging_rules.md` | 标注规范与语义判定规则 |
| `outputs/` | 历史模型输出、异常日志和运行摘要 |
| `test_validator.py`、`check_testset.py` | 早期校验练习和测试集检查脚本（不是完整 pytest 测试套件） |
| `evaluation_report.md` | 两轮测试结果、主要错误和局限 |
| 根目录其他 `json_practice.py`、`schema_probe*.py`、`batch_output*.json` 等 | 早期学习与实验文件；为保留历史暂不移动或删除 |

## 如何在本地运行

### 1. 环境

建议 Python 3.10 或更新版本。当前依赖列于 `requirements.txt`；这是便于安装的依赖清单，**尚不是经环境锁定的完整可复现版本**。

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. 配置 API Key

复制根目录 `.env.example` 为 `.env`，然后填写你自己的百炼 API Key：

```dotenv
DASHSCOPE_API_KEY=your_own_api_key
```

`.env` 已被 Git 忽略；不要提交真实 Key，也不要将运行日志中的秘密信息公开。API 调用可能产生费用，需自行确认账户额度。

### 3. 运行模型

打开 `main.py`，检查文件顶部的配置：

```python
MODEL = "deepseek-v4.1-flash"
USE_SCHEMA = False
PROMPT_VERSION = "v3"
RUN_NAME = "my_local_run_01"
DATA_FILE = "eval_cases.json"
```

**务必使用一个未存在的 `RUN_NAME`**。仓库中已有历史实验的同名输出，脚本为保护实验记录会拒绝覆盖。`DATA_FILE="eval_cases.json"` 用于开发集练习；已有 `testset/test_cases.json` 是**冻结测试集**，不应拿它来继续调 Prompt。

```bash
python main.py
```

运行结束后，`outputs/` 中会出现 `batch_output_<RUN_NAME>.json`、`batch_errors_<RUN_NAME>.json`、`run_summary_<RUN_NAME>.json`。

### 4. 评测已有结果

```bash
python evaluate.py
python breakdown.py
```

两个脚本当前默认读取 `testset/test_cases.json`，对仓库中保存的测试集实验结果做精确匹配与分组汇总。前者的 `RUN_FILTER` 会选择符合条件的实验；如仅需评测开发集，请同步修改脚本顶部的 `DATA_FILE` 等设置。**它们不会自动计算语义正确率。**

## 已有评测结果

固定测试集：**10 条真实 JD × 9 字段 = 90 个字段**。基于固定 Prompt v3 和 `deepseek-v4.1-flash` 两次运行，成功处理 10/10、结构校验 10/10。

| 结果 | run1 | run2 |
| --- | ---: | ---: |
| 自动逐字段精确匹配 | **65/90（72.2%）** | **60/90（66.7%）** |
| 语义复核结果 | **72/90（80.0%）** | **65/90（72.2%）** |

**解释口径**：精确匹配由程序计算；run1 的不一致字段先由用户判定、再复核并确认修订；**run2 主要由 AI 辅助判定，不能称为独立人工评测**。语义分数与自动指标来源不同，不能混作一种测量，也不能只展示得分更高的一轮。详情见 [评测报告](evaluation_report.md)。

典型问题包括：从平台信息卡错误采用较低学历门槛、把非强制要求归入必备技能、将团队所在地误作工作地点、漏掉线下转远程的限制条件等。项目因此提出未来按“必备/优先条件”分组并保留地点、时长等重要限制词的设计方向；**该设计目前未实现**。

## 评测局限与下一步

- 样本只有 10 条真实 JD，无法据此证明普遍泛化能力或可靠的运行稳定性；开发集四条中三条为模拟 JD。
- `T001–T007` 曾在其他岗位讨论中被 AI 阅读，未用于当前 Prompt 调参，但不能声称完全盲测；标注以一位主要标注者为主，部分样本 AI 预标。
- `judging_rules.md` 是测试前冻结口径；技能条目精确率/召回率的合并拆分计数规则尚需单独验收，因此不在此页宣称正式的技能级 P/R。
- 现阶段先完成基本的 README、项目代码理解、小规模自动化测试以及可复现说明；以后如果改变 Prompt 或规则，应使用新的开发/测试数据重新验证，不能回写当前冻结成绩。

---

**项目定位**：用于训练和展示 LLM 结构化提取、输出校验、实验记录及错误分析的方法，而非成熟商用招聘产品。
