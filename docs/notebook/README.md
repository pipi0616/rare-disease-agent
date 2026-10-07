# 工程笔记 · 边做边学

项目每做一步，这里加一章。每章只讲三件事：**为什么要做、做完得到什么、公司为什么这么干**。

## 怎么用

在 VS Code 里打开 `.ipynb`，右上角内核选 **raredx (.venv)**，然后从上往下一格一格点 ▶。
标着"这格不用看懂"的是准备工作，直接运行就行。

（没有 raredx 这个内核的话，在项目目录跑一次：
`uv run python -m ipykernel install --user --name raredx --display-name "raredx (.venv)"`）

## 目录

| 章 | 一句话 |
|---|---|
| [0](00_overview.ipynb) | 为什么重做，要做成什么，路线和进度 |
| [1](01_freeze_old_repo.ipynb) | 存档旧项目：论文那一版随时能找回 |
| [2](02_skeleton.ipynb) | 搭骨架：一条命令建项目、一条命令跑起来 |
| [3](03_checks.ipynb) | 自动体检：有毛病的代码存不进去 |
| [4](04_github_ci_pr.ipynb) | GitHub、自动检查、合并：正本永远是好的 |
| [5](05_data.ipynb) | 准备考题：一万例真实病例 |

用到的东西几乎都是公司通用的标准做法；只有 agent 框架这类有几家可选，我们选最常见的。
这本笔记本身是为了学习才有的，公司里没有。
