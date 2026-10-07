# 02 · 新仓库骨架：git、uv、src 布局、第一次提交（路线第 1 步第 1 块）

**JD 对应**：「良好的 Python 工程化能力」「熟悉现代 Python 项目管理（pyproject、uv/poetry）」。

## 做了什么

在 `rare-disease-agent/` 里：

```bash
git init -b main                                   # 开记录本，正本分支叫 main
uv init --package --name raredx --python 3.12      # 生成标准骨架
uv sync                                            # 建虚拟环境，装好 Python 3.12 和我们自己
uv run raredx                                      # 跑入口命令 → Hello from raredx!
git add -A && git commit -m "chore: project skeleton"
```

另外手写了三个文件：`pyproject.toml` 里的项目描述、`.gitignore`、`README.md`。

生成的文件：

```
pyproject.toml           项目说明书：名字 raredx、Python ≥3.12、入口命令 raredx、依赖清单（现在为空）
.python-version          锁定 Python 3.12；uv 自己下载管理，不碰系统 Python 和 conda
uv.lock                  采购单：每个依赖精确到版本号和校验和，谁装都一样
.gitignore               永不进记录本的清单：.env、data/、runs/、third_party/、.venv/
README.md                一句话说明 + 怎么跑 + 目录含义。从第一天就有
src/raredx/__init__.py   全部代码的家，目前两行
docs/                    计划文档，原样带进来
```

## 工业界叫什么

| 术语 | 大白话 |
|---|---|
| uv | Python 的包管理器 + 项目生成器。同类还有 poetry、pip + venv；uv 最快，2024 年后新项目的默认选择 |
| `pyproject.toml` | 项目说明书，Python 官方标准（PEP 621）。取代了 `setup.py` 和 `requirements.txt` |
| lockfile（`uv.lock`） | 采购单。`requirements.txt` 写"pandas>=2.0"是意向，lockfile 写"pandas 2.2.3 + 校验和"是事实 |
| src layout | 代码放在 `src/包名/` 下，像正式安装的软件包；测试和脚本都通过 `import raredx` 来用它 |
| virtual environment（`.venv/`） | 这个项目专用的 Python 和依赖，和别的项目互不干扰 |
| conventional commits | 提交信息格式：`类型: 说明`。`chore` 杂务、`feat` 新功能、`fix` 修错、`test`、`docs`、`refactor` |

## 为什么

- **src 布局 vs 旧仓库的 88 处路径 hack。** 旧仓库的脚本靠 `sys.path.insert(0, ROOT)` 才能找到
  自己的代码，换个目录就断。src 布局下包是"安装"进环境的，在任何目录都能 `import raredx`。
- **lockfile 进 git，`.venv` 不进。** 采购单是文本、几 KB、决定别人装出什么；装好的货是几百 MB、
  每台机器自己装。旧仓库两者都没管好：`requirements.txt` 和 `pyproject.toml` 各写一份，还互相不一致。
- **`.gitignore` 第一天就写。** 旧仓库 22 个 `.tbi` 进了 git，就是因为清单是后补的。
- **README 第一天就有**，哪怕只说"还没功能"。面试官第一眼看的就是它。
- **`chore:` 前缀。** 以后翻历史时一眼能分出功能提交和杂务提交，也能自动生成变更日志。

## ✏️ 你来验证

```bash
cd ~/Projects/QAFI_Paper/hearing_agent/rare-disease-agent
uv run raredx                       # Hello from raredx!
uv run python --version             # Python 3.12.x，不是系统的 3.9
git log --oneline                   # 一条：chore: project skeleton
git status --short                  # 空：没有未提交改动
git check-ignore -v third_party .venv   # 显示是哪条规则把它们挡在 git 外面
```

再试一条，体会"包是安装进去的"：

```bash
cd /tmp && uv run --project ~/Projects/QAFI_Paper/hearing_agent/rare-disease-agent python -c "import raredx; print(raredx.__file__)"
```

在 `/tmp` 这个无关目录里照样能导入，打印出的是 `src/raredx/__init__.py` 的路径。旧仓库做不到这一点。

## 思考

`uv.lock` 现在只有 8 行。等我们加上 LangGraph，它会变成几千行。为什么要把这几千行机器生成的文件提交进 git？

<details><summary>答案</summary>

因为它是"谁装都一样"的保证。没有它，今天装的 LangGraph 是 1.2，半年后同事装的是 1.5，
行为不同，排查半天才发现是版本问题。锁定文件把"我这里能跑"变成"任何人任何时候都能跑"。
Docker 镜像（第 1 步第 3 块以后）也是从这个文件装依赖的。

</details>

## 下一块

装代码体检：ruff（格式和低级错误）、mypy（类型）、pytest（测试），用 pre-commit 挂在"提交"前面，
不过检就提交不进去。
