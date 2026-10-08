# 工程笔记 · 边做边学

这个项目一半是作品，一半是学会"公司里的 agent 工程师怎么干活"。
每做一步，这里加一章 Jupyter notebook。每章固定五段：

| 段 | 回答的问题 |
|---|---|
| 做了什么 | 这一步具体改了哪些文件、跑了哪些命令 |
| 工业界叫什么 | 术语中英对照，招聘要求里怎么写 |
| 为什么 | 不做会怎样，旧仓库里对应的教训 |
| ✏️ 你来验证 | 代码格，点运行，亲眼看到结果 |
| 思考 | 一个问题，答案在下一格 |

## 怎么用

在 VS Code 里打开 `.ipynb`，右上角选内核时选 **raredx (.venv)**（注册过的本项目专属内核；
没有的话在仓库目录跑一次 `uv run python -m ipykernel install --user --name raredx --display-name "raredx (.venv)"`），
然后逐格点 ▶，或顶部 Run All。每章第一格会自动进到正确的目录，重复运行没有副作用。

笔记里**保留了运行输出**，因为输出本身就是教学内容。代码仓库里的分析用 notebook 通常会
清空输出再提交（工具叫 nbstripout），以免每次运行都产生一堆无意义的改动；这里是有意的例外。

## 目录

| 章 | 内容 | 对应路线 |
|---|---|---|
| [00](00_overview.ipynb) | 总览：为什么重做、路线图、"有没有 Databricks 那样的平台"、公司怎么管代码 | — |
| [01](01_freeze_old_repo.ipynb) | 冻结旧仓库，两本记录本分开放 | 第 0 步 |
| [02](02_skeleton.ipynb) | 新仓库骨架：git、uv、src 布局、第一次提交 | 第 1 步第 1 块 |
| [03](03_checks.ipynb) | 代码体检：ruff、mypy、pytest、pre-commit，和一次真实的拒绝 | 第 1 步第 2 块 |
| [04](04_github_ci_pr.ipynb) | GitHub 私有仓库、CI、第一个合并请求，和 CI 第一次红了怎么修 | 第 1 步第 3 块 |
| [05](05_data.ipynb) | 数据层：Phenopacket Store 的下载、校验、解析、开发集/留出集切分 | 第 2 步第 1 块 |

## 用到的每样东西属于哪一类

**A** = 通用软件工程标准，所有公司一样，不是我们选的。
**B** = agent 领域有几家可选，我们选最常见的，换公司可能换牌子但做的事不变。
**C** = 只为了学习，公司里没有。

| 东西 | 类 | 章 | 可替代品 |
|---|---|---|---|
| Git、GitHub、分支 + PR、squash 合并 | A | 01, 04 | GitLab、Bitbucket |
| uv、pyproject.toml、uv.lock、src 布局 | A | 02 | poetry、pip-tools |
| ruff、mypy、pytest、pre-commit | A | 03 | flake8+black+isort、pyright |
| GitHub Actions CI | A | 04 | GitLab CI、Jenkins |
| conventional commits | A | 02 | — |
| 下载 + 校验和 + 版本化原始数据层 | A | 05 | DVC |
| pydantic 数据模型、pydantic-settings 配置 | A | 05 | dataclasses、attrs |
| typer 命令行 | B | 05 | click、argparse |
| 开发集 / 留出集按来源切分 | A（评测方法学） | 05 | — |
| LangGraph（编排） | B | 第 4 步 | CrewAI、AutoGen、Google ADK、OpenAI Agents SDK |
| MCP（工具接口） | B | 第 3 步 | 直接 function calling |
| Langfuse / LangSmith（追踪、评测） | B | 第 4 步 | Phoenix、MLflow |
| 这本笔记、`hearing_agent/old + new` 的摆法 | C | — | — |
