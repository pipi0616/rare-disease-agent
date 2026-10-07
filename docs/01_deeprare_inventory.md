# 第 1 步：DeepRare 依赖盘点（2026-10-05）

> 注（2026-10-05）：DeepRare 复现推迟到总体计划的 M5，只作为对照组；相似病例检索不纳入我们的系统。见 [00_plan.md](00_plan.md)。

目标：在公开病例上原样跑通 DeepRare 的"只看症状"模式（`main.py` → `diagnosis.py`），量出基线。
代码：`third_party/DeepRare`（commit 7897820，2026-04-14）。

## 本机环境

| 项目 | 状态 |
|---|---|
| Python | 系统自带 3.9.6，太旧；用 uv 另建 3.11 环境 |
| uv / git / Chrome | 有 |
| Java | 没有（Exomiser 需要，第一轮不用） |
| 磁盘 | 剩 27 GB；Exomiser 数据约 20 GB，第一轮不装 |
| API 密钥 | DeepSeek、NCBI 有；OpenAI 没有 |

## DeepRare "只看症状"模式的依赖

| 依赖 | 用途 | 状态 |
|---|---|---|
| 主模型（`--model deepseek`） | 诊断推理、复核 | DeepSeek 密钥现成 |
| OpenAI `text-embedding-3-small` | 相似病例检索：病例库的向量是用它预先算好的 | **缺密钥**，换模型就得重算整个病例库 |
| OpenAI `gpt-4o-mini` | 总结搜到的网页 | **缺密钥**，可改用 DeepSeek |
| DuckDuckGo 搜索 | 网页检索 | 不需要密钥 |
| Selenium + Chrome | 打开网页读正文 | Chrome 有；驱动由 Selenium 自动下载 |
| PubCaseFinder、PhenoBrain | 症状 → 候选疾病 | 公开网络接口，不需要密钥 |
| BioLORD-2023-C、MedCPT-Cross-Encoder | 疾病名标准化、相似病例精排 | HuggingFace 下载，CPU 可跑 |
| 数据库 `Angelakeke/DeepRare` | 疾病映射、预算好的向量、PubMed 病例库（约 6.7 万例） | 公开，共 0.66 GB |

## 需要改的地方（复现差异要在论文里写明）

1. `requirements.txt` 里有 Linux 专用的 CUDA 包，Mac 上要去掉。
2. `utils.py` 第 106–133 行写死读取 `dataset/` 下的新华、MIMIC、DDD、RareBench、MyGene2 病例文件，这些都没公开 → 相似病例库只用公开的 PubMed 病例。这也顺带避免了测试病例出现在病例库里。
3. `data.py` 第 43 行的 MyGene2 测试文件没公开 → 第一轮改用 RareBench 的公开子集（MME 40 例、HMS 88 例、LIRICAL 370 例、RAMEDIS 624 例）。
4. RareBench 在 HuggingFace 上用的是加载脚本，新版 `datasets` 可能不再支持 → 必要时直接读 `data.zip`。

## 待定

- 是否申请 OpenAI 密钥：有 → 相似病例检索与原文一致；没有 → 用开源向量模型重算病例库，与原文有差异。
