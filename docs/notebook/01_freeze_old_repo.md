# 01 · 冻结旧仓库，两本记录本分开放（路线第 0 步）

**JD 对应**：「熟悉 Git 协作流程」——标签、分支、把仓库当记录本而不是备份盘。

## 做了什么

在旧仓库 `old/`（就是原来的 hearing_agent）里：

1. 查清三层状态：GitHub 上的正本停在 7 月 20 日（提交 `c84508d`）；本地 `main` 比它多 5 次
   8 月 2 日的提交，从没推上去；再往后是 8 月 5–21 日的 37 处改动，没提交，共 5.5 MB。
2. 打标签 `paper-v1`，钉在 GitHub 那个版本（`c84508d`）上。
3. 新建分支 `archive/agent-experiments-2026-08`，把 8 月的全部工作（5 次提交 + 没提交的
   89 个文件、1.9 万行）提交进去。
4. 切回 `main`，工作区 0 处未提交改动。什么都没删，什么都没上传。

然后你把整个旧仓库搬进 `hearing_agent/old/`，新项目放在 `hearing_agent/rare-disease-agent/`。

## 工业界叫什么

| 术语 | 意思 | 这次 |
|---|---|---|
| tag（标签） | 给某个版本钉一个永久名字；发布版本都靠它 | `paper-v1` = 论文投稿时的代码 |
| branch（分支） | 正本的一个副本，在上面改不影响正本 | `archive/...` 当抽屉用 |
| working tree clean | 工作区没有未提交改动 | `main` 现在是这个状态 |
| 仓库 = 含 `.git` 的文件夹 | 搬家、改名都不影响记录，因为记录本跟着文件夹走 | 整个搬进 `old/` 照常工作 |

## 为什么

- **记录本不能合订。** 旧仓库在 GitHub 上是公开的 OtoVCE，新项目要一本从零开始的干净记录。
  所以 `hearing_agent/` 只是普通文件夹（抽屉），里面两个子文件夹各自是独立仓库。
- **先存档再动手。** 两个月没提交的一万多行，放进分支比放在工作区安全：工作区的改动一次
  `git checkout` 就能抹掉，分支里的不会。
- **标签指向公开的那个版本**，不指向本地多出来的 5 次提交——读者在 GitHub 上看到的才是论文代码。

## ✏️ 你来验证

```bash
cd ~/Projects/QAFI_Paper/hearing_agent/old
git status -sb          # 第一行应是 ## main...origin/main [ahead 5]，下面没有别的
git tag                 # 能看到 paper-v1（还有以前的 v1.0 v1.0.1 v1.1）
git branch              # 能看到 archive/agent-experiments-2026-08 和 * main
git log --oneline -1 archive/agent-experiments-2026-08   # 存档那次提交
```

## 思考

`main` 上那 5 次 8 月的提交从没推到 GitHub，这为什么是个问题？

<details><summary>答案</summary>

本地是唯一副本：硬盘坏了就没了；合作者和审稿人也看不到。公司里的规矩是"当天的工作当天推"，
正本在服务器上，本地只是工作副本。等第 1 步第 3 块接上 GitHub，新仓库每个改动都会推上去。

</details>
