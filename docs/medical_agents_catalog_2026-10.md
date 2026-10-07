# 医疗 Agent 文献全景（2024-01 至 2026-10-03）

来源：arXiv API（标题含 agent/agents/agentic/multiagent 且含医疗词）+ PubMed（标题含 agent 且摘要含大模型相关词）。
处理：去重；只保留大模型 agent；标题需有明确医疗语境（或摘要有足够医疗词）；不含药物发现/蛋白/化学类科研 agent。
分类：关键词自动归类，标题优先，一篇只归一个主专科，属粗分，个别会错。未覆盖中文期刊和大部分 medRxiv。

共 984 篇（2024: 73，2025: 325，2026 至 10 月: 585）。

| 专科/领域 | 篇数 | 其中 2026 年 |
|---|---|---|
| 通用/跨专科 | 378 | 220 |
| 医学影像/放射 | 105 | 62 |
| 精神心理 | 71 | 37 |
| 肿瘤 | 58 | 39 |
| 遗传/罕见病/组学 | 54 | 32 |
| 急诊/重症 | 40 | 32 |
| 生物医学科研 | 35 | 18 |
| 病理 | 30 | 19 |
| 神经 | 26 | 13 |
| 健康管理/生活方式 | 21 | 14 |
| 心血管 | 20 | 14 |
| 外科/手术 | 19 | 9 |
| 医学教育 | 19 | 9 |
| 医保/编码/行政 | 15 | 11 |
| 公共卫生/流行病 | 14 | 7 |
| 药学/用药 | 14 | 8 |
| 眼科 | 13 | 6 |
| 呼吸/肝肾/消化 | 12 | 8 |
| 临床试验 | 10 | 8 |
| 老年/康复/护理 | 9 | 4 |
| 儿科/产科 | 5 | 4 |
| 内分泌/代谢 | 5 | 3 |
| 口腔 | 3 | 3 |
| 皮肤 | 3 | 3 |
| 检验 | 3 | 2 |
| 中医 | 2 | 0 |

## 通用/跨专科（378）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-10-01 | [A Multi-Agent LLM Framework for Personalized Health Checkup Interpretation and Guidance](http://arxiv.org/abs/2610.01451v1) | 多智能体协作 | 16 pages, 2 figures, 8 tables and Appendix |
| 2026-10-01 | [SCOPE-AD: Sequential cost-aware ordinal-belief planning with energy-based models for diagnostic agents](http://arxiv.org/abs/2610.01278v1) | 诊断/鉴别诊断 | 5 pages,2 figures |
| 2026-10-01 | [My FAULT: Self-Diagnosis as Credit Assignment in Self-Evolving Agentic Reinforcement Learning](http://arxiv.org/abs/2610.01161v1) | 训练方法(RL/微调) | Preprint |
| 2026-09-30 | [Agent Error Dataset: Scaling 50,000 Error--Diagnosis Pairs for Failure Analysis and Error-Aware Post-Training](http://arxiv.org/abs/2609.40111v2) | 诊断/鉴别诊断 |  |
| 2026-09-30 | [EHR-RobustGym: Benchmarking and Training Agents for Robust Clinical Reasoning](http://arxiv.org/abs/2609.39371v1) | 评测基准/环境 |  |
| 2026-09-29 | [Personalized State-Transition-Aware Memory for Clinical Agents](http://arxiv.org/abs/2609.38490v1) | 评测基准/环境 |  |
| 2026-09-29 | [PrivMeSA: Privacy-Aware Self-Evolving Multi-Agent System for Medicine via Local-Remote LLM Collaboration](http://arxiv.org/abs/2609.38458v1) | 安全/幻觉/攻击 |  |
| 2026-09-28 | [ARCagent: An Adaptive Retrieval Calibration Agent for Clinical Question Answering](http://arxiv.org/abs/2609.36392v1) | 检索/RAG/知识 | 13 pages, 7 figures, 5 tables |
| 2026-09-26 | [What Can a Leaderboard Certify? Compositional Controllability for Fair Evaluation and Training of Biomedical Literature-Review Agents](http://arxiv.org/abs/2609.32318v1) | 综述/观点 | 33 pages, 1 figure, 18 tables. Zhaowei Han, Xiang Zhang, and |
| 2026-09-24 | [SkinAgent AI: A Safety-Grounded Multimodal Agentic Framework for Non-Diagnostic Skincare Support](http://arxiv.org/abs/2609.29341v1) | 安全/幻觉/攻击 | Submitted to JMIR AI and currently under peer review |
| 2026-09-24 | [SMARtCARE: Privacy-Preserving Agentic AI Systems for Bounded-Autonomy Clinical Decision Support](http://arxiv.org/abs/2609.31763v1) | 安全/幻觉/攻击 | Paper accepted to, and to appear in, the 2026 IEEE HealthCom |
| 2026-09-15 | [[MM/AI] Mental Models in Human-AI Interaction: Methods and Challenges in the Generative and Agentic AI Era (Workshop)](http://arxiv.org/abs/2609.17206v1) | 综述/观点 | Accepted workshop paper to IUI '27, CFP is available at http |
| 2026-09-15 | [AURA: Agentic Diagnosis and Refinement for Production Recommender Systems at Scale](http://arxiv.org/abs/2609.16625v1) | 诊断/鉴别诊断 | 14 pages, 1 figure, 6 tables. Accepted at GenAIECommerce'26: |
| 2026-09-14 | [EMR: Self-Evolving Medical Multi-Agent System via Experience Mining and Reuse](http://arxiv.org/abs/2609.15161v1) | 训练方法(RL/微调) |  |
| 2026-09-14 | [MedVA: An End-to-End Neuro-Symbolic Agentic System for Medical Volume Visualization](http://arxiv.org/abs/2609.14874v1) | 训练方法(RL/微调) | 11pages |
| 2026-09-11 | [Same Patient, Different Order: Action-Level Reliability of Clinical LLM Agents Under Repeated Runs](http://arxiv.org/abs/2609.13582v1) | 评测基准/环境 | 13 pages, 2 figures, 3 tables. Code, run records and the rer |
| 2026-09-11 | [Asclepius: An Adaptive Harness for Long-Horizon Clinical Agents](http://arxiv.org/abs/2609.13543v1) | 评测基准/环境 | 9 pages, 4 figures, 11 tables. EMNLP 2026 Findings |
| 2026-09-07 | [EmoMed: An Emotionally-Aware Agent for Multimodal Medical Support with Real-Time Information Retrieval](http://arxiv.org/abs/2609.07194v1) | 检索/RAG/知识 |  |
| 2026-09-04 | [A Structured Debate-Mixture-of-Agents Framework for Complex Clinical Diagnostic Decision Support](http://arxiv.org/abs/2609.05069v1) | 诊断/鉴别诊断 | 13 pages, 6 figures |
| 2026-09-02 | [Instability Floors: Separating Bias from Noise in Fairness Audits of Clinical LLM Agents with FairMedAgent](http://arxiv.org/abs/2609.03221v3) | 安全/幻觉/攻击 | 27 pages (13 main plus 14 supplementary), 4 figures, 3 table |
| 2026-09-02 | [Beyond Outcome Gaps: Process-Aware Fairness Diagnosis for LLM-based Multi-Agent Decision Systems](http://arxiv.org/abs/2609.02092v1) | 安全/幻觉/攻击 | Accepted to EMNLP 2026 |
| 2026-08-31 | [Toward Workflow-Aware Benchmarking for Healthcare NLP Agents](http://arxiv.org/abs/2609.00296v1) | 评测基准/环境 | 4 pages, 3 tables |
| 2026-08-31 | [GPAgentBench-2K: Benchmarking Large Language Model Agents in Complex Clinical Action Space](http://arxiv.org/abs/2608.30188v2) | 评测基准/环境 |  |
| 2026-08-28 | [Automated Analysis Framework for Multilingual Climate-Health Literature Based on Multi-Agent Large Language Model](http://arxiv.org/abs/2608.27998v1) | 多智能体协作 |  |
| 2026-08-28 | [FedEHR-Agents: Federated Agentic Optimization for Automated EHR Modeling](http://arxiv.org/abs/2608.27856v1) | EHR/结构化数据 | 25 pages, 6 figures |
| 2026-08-26 | [A Multi-Agent Pipeline for Source-Grounded Synthetic Note Generation from Longitudinal Structured EHR](http://arxiv.org/abs/2609.22164v1) | EHR/结构化数据 | Accepted at the FMSD Workshop, ICML 2026 |
| 2026-08-25 | [EviDx: Evidence-Aware Active Diagnosis with Scaffolded LLM Agents](http://arxiv.org/abs/2608.24570v1) | 诊断/鉴别诊断 |  |
| 2026-08-24 | [Generating Biomedical Fact-Checking Reports with RL-Enhanced Agentic Search](http://arxiv.org/abs/2608.23811v1) | 训练方法(RL/微调) |  |
| 2026-08-24 | [CDEG: Learning Decision-Critical Evidence for Long-Horizon Diagnostic Agents](http://arxiv.org/abs/2608.22899v2) | 诊断/鉴别诊断 | 9 pages, 5 figures |
| 2026-08-23 | [CaseWeaver: A Multi-Agent Framework for Multimodal Virtual Clinical Case Generation](http://arxiv.org/abs/2609.05480v1) | 多智能体协作 |  |
| 2026-08-23 | [Role-Specialized Mixture-of-Agents with Open-Weight LLMs for Clinical Prediction](http://arxiv.org/abs/2608.22176v1) | 安全/幻觉/攻击 | COLM 2026 DAIH Workshop |
| 2026-08-22 | [SSE-Bio: A Structured Self-Evolving Agent with Agentic Retrieval Policy for Multi-Hop Biomedical Reasoning](http://arxiv.org/abs/2608.22132v1) | 训练方法(RL/微调) | Accepted to EMNLP 2026 |
| 2026-08-22 | [Sparse Multi-Stage Expert-Agent Routing for Complex Clinical Reasoning](http://arxiv.org/abs/2608.21948v1) | 问答/推理 |  |
| 2026-08-22 | [BioMed-Agent-RL: A Meta Learning, All You Need for Biomedical Applications](http://arxiv.org/abs/2608.21864v1) | 训练方法(RL/微调) |  |
| 2026-08-22 | [MSM-Mem: A Universal Medical Structured Multimodal Memory Framework for Medical AI Agents](http://arxiv.org/abs/2608.21810v1) | 诊断/鉴别诊断 | 8 pages |
| 2026-08-22 | [ATHENA: Knowledge-guided agentic neural architecture search for AutoFormer-based electronic health record modeling](http://arxiv.org/abs/2608.21712v2) | EHR/结构化数据 |  |
| 2026-08-21 | [From Search Agents to Dissemination Interfaces: Understanding Human Trust in Health Information from Conversational Search](http://arxiv.org/abs/2608.21177v1) | 问诊/医患对话 |  |
| 2026-08-19 | [Adaptive Memory and Reflection Multi-Agent System for Medical Question Answering](http://arxiv.org/abs/2608.19029v1) | 问答/推理 | Accepted by IEEE SMC 2026 |
| 2026-08-19 | [EVADE: Evidence-Verified Agentic Diagnosis with Escape](http://arxiv.org/abs/2608.18833v1) | 诊断/鉴别诊断 |  |
| 2026-08-15 | [ETHOS: Towards a Modular Ethics Framework for Clinical Multi-Agent Systems](http://arxiv.org/abs/2608.15424v2) | 多智能体协作 | Preprint of an article submitted for consideration in Pacifi |
| 2026-08-13 | [MARC v1: An Open-Source Multi-Agent Framework for Clinical AI Reasoning and Coordination](http://arxiv.org/abs/2608.13476v1) | 问答/推理 | 13 pages, 4 figures |
| 2026-08-11 | [Social Chain of Thought: A Multi-Agent Architecture Grounded in Medical Differential Diagnosis Methodology](http://arxiv.org/abs/2608.11420v1) | 诊断/鉴别诊断 | 14 pages, 9 figures, 6 tables |
| 2026-08-10 | [Beyond Cash Flows: A Multi-Agent AI Framework for Valuing Clinical-Stage, Cross-Border Biotechnology](http://arxiv.org/abs/2608.10175v1) | 多智能体协作 |  |
| 2026-08-07 | [From Single Chatbots to Governed Agent Ecosystems: An Agentic AI Pattern Catalogue and Orchestration Framework for Mission-Critical Hospital Information Management Systems](http://arxiv.org/abs/2608.07627v1) | 问诊/医患对话 | Peer-reviewed published article |
| 2026-08-06 | [ECHO: A Locally-Deployable Agentic Health Assistant with Temporal Memory, Safety Guardrails, and Speech Assessment](http://arxiv.org/abs/2608.06110v2) | 安全/幻觉/攻击 | 5 pages |
| 2026-08-05 | [DoctorAgents: an agentic framework to iteratively refine AutoML pipeline for small clinical temporal data](http://arxiv.org/abs/2608.05375v1) | 训练方法(RL/微调) | 34 pages, 5 figures |
| 2026-08-04 | [ANCHOR-RE: An Agentic Neuro-Symbolic Framework for Grounded Biomedical Relation Extraction](http://arxiv.org/abs/2608.03154v1) | 评测基准/环境 | Submitted to Journal of Biomedical Informatics (under review |
| 2026-07-30 | [Inference-Time Agentic Decision Rules Beat Longer Evolving Search for Multi-Image Medical Reasoning](http://arxiv.org/abs/2607.27564v1) | 检索/RAG/知识 | Presented at the CVPR 2026 Workshop on Multi-Modal Reasoning |
| 2026-07-28 | [GuideSkill: Evolving Executable LLM Agent Skills for Guideline-Grounded Clinical Reasoning](http://arxiv.org/abs/2607.26160v1) | 问答/推理 |  |
| 2026-07-28 | [ClinLens: Towards Long-Horizon LLM Agents for Longitudinal Multimodal Clinical Data Science](http://arxiv.org/abs/2607.26155v2) | 评测基准/环境 |  |
| 2026-07-28 | [VetClaw: An Edge-Cloud Multimodal Agentic System for Veterinary Disease Screening](http://arxiv.org/abs/2607.26042v1) | 安全/幻觉/攻击 |  |
| 2026-07-28 | [Agentic AI in medicine: architectures, applications, evaluation, and challenges for clinical translation](http://arxiv.org/abs/2607.25489v1) | 综述/观点 | Review article, 6 figures, 2 tables. 42 pages |
| 2026-07-23 | [Spectral Dynamics of Semantic Drift in Clinical Multi-Agent Language Model Networks](http://arxiv.org/abs/2607.22758v1) | 多智能体协作 |  |
| 2026-07-21 | [CARE: Pre-Execution Command Verification for Shell-Executing LLM Agents](http://arxiv.org/abs/2607.21642v2) | 安全/幻觉/攻击 | Accepted by ISSRE 2026 |
| 2026-07-21 | [MedDDC-Eval: Diagnosis-Decoupled Evaluation of Multi-Turn Medical Consultation Agents](http://arxiv.org/abs/2607.18999v2) | 评测基准/环境 | supplementary material included |
| 2026-07-15 | [Cura 1T: Specialized Model for Agentic Healthcare](http://arxiv.org/abs/2607.15314v2) | 评测基准/环境 | Model: https://actava.ai/cura; Docs: https://actava.ai/cura/ |
| 2026-07-10 | [LongMedBench: Benchmarking Medical Agents for Long-Horizon Clinical Decision-Making](http://arxiv.org/abs/2607.09322v2) | 评测基准/环境 | Submitted manuscript prior to peer review in MICCAI 2026 |
| 2026-07-03 | [MedCalc-Pro: Solving Complex Medical Calculations with LLM Agents](http://arxiv.org/abs/2607.02879v1) | 评测基准/环境 |  |
| 2026-07-02 | [Adoption and Ecosystem Health: A Longitudinal Analysis of Open-Source Multi-Agent Frameworks](http://arxiv.org/abs/2607.02453v1) | 多智能体协作 | 24 pages, 10 figures |
| 2026-07-01 | [World Feedback for Clinical Agents: Diagnosing RL in FHIR Environments](http://arxiv.org/abs/2607.01470v1) | 训练方法(RL/微调) |  |
| 2026-06-30 | [HealthAgentBench: A Unified Benchmark Suite of Realistic Agentic Healthcare Environments for Challenging Frontier AI Agents](http://arxiv.org/abs/2606.31179v1) | 评测基准/环境 |  |
| 2026-06-29 | [DEEPMED Search: An Open-Source Agentic Platform for Medical Deep Research with Introspective Verification](http://arxiv.org/abs/2606.29746v1) | 检索/RAG/知识 | 5 pages, 2 figures, 2 tables. Accepted to IJCAI-ECAI 2026 De |
| 2026-06-27 | [An AI agent for treatment reasoning over a biomedical tool universe](http://arxiv.org/abs/2606.28692v1) | 治疗/决策支持 | Project page: https://athena.openscientist.ai Code: https:// |
| 2026-06-27 | [Why Trust Your Agent? Empirical Security Gains from TRiSM-Guided Agentic Workflows in Healthcare](http://arxiv.org/abs/2606.28666v1) | 安全/幻觉/攻击 | 15 pages, 6 figures |
| 2026-06-26 | [It Lied to a Doctor to Buy Poison Ingredients: Quantifying Real-World Misuse of Phone-use Agents](http://arxiv.org/abs/2606.27944v1) | 综述/观点 | work in progress |
| 2026-06-24 | [MedGuards: Multi-Agent System for Reliable Medical Error Detection and Correction](http://arxiv.org/abs/2606.25651v2) | 多智能体协作 |  |
| 2026-06-24 | [Bridging the Post-discharge Gap: A Traceable Multi-agent Framework for Safe and Continuous Care](http://arxiv.org/abs/2606.25334v1) | 报告/文书生成 | 23 pages, 10 figures |
| 2026-06-22 | [EHR-Complex: Benchmarking Medical Agents for Complex Clinical Reasoning](http://arxiv.org/abs/2606.23301v1) | 评测基准/环境 |  |
| 2026-06-17 | [Configurable Clinical Information Extraction with Agentic RAG: What Works, What Breaks, and Why](http://arxiv.org/abs/2606.19602v1) | 检索/RAG/知识 |  |
| 2026-06-16 | [Agentic AI-based Framework for Mitigating Premature Diagnostic Handoff and Silent Hallucination in Healthcare Applications](http://arxiv.org/abs/2606.18068v1) | 安全/幻觉/攻击 |  |
| 2026-06-16 | [Agentic AI Enhances Physician Trust in Clinical Decision Making](http://arxiv.org/abs/2606.30658v1) | 治疗/决策支持 | Accepted by AMIA 2026 Annual Symposium |
| 2026-06-14 | [DeepRoot: A KG-Coordinated Multi-Agent System for Therapeutic Reasoning over Historical Medical Texts](http://arxiv.org/abs/2606.15931v1) | 问答/推理 |  |
| 2026-06-13 | [Let LLMs Judge Each Other: Multi-Agent Peer-Reviewed Reasoning for Medical Question Answering](http://arxiv.org/abs/2606.15419v1) | 问答/推理 | Accepted by the Journal of the American Medical Informatics  |
| 2026-06-12 | [Trust but Verify: Mitigating Medical Hallucinations via Post-Hoc Adversarial Auditing and Multi-Agent Feedback Loops](http://arxiv.org/abs/2606.14149v1) | 安全/幻觉/攻击 |  |
| 2026-06-11 | [LatentDx: Latent Multi-Agent Communication for Cross-Hospital Rare-Disease Diagnosis](http://arxiv.org/abs/2606.13945v2) | 诊断/鉴别诊断 |  |
| 2026-06-10 | [MedCTA: A Benchmark for Clinical Tool Agents](http://arxiv.org/abs/2606.11702v1) | 评测基准/环境 | Project Page: https://ivul-kaust.github.io/MedCTA/ Code: htt |
| 2026-06-04 | [Humans' ALMANAC: A Human Collaboration Dataset of Action-Level Mental Model Annotations for Agent Collaboration](http://arxiv.org/abs/2606.06388v2) | 多智能体协作 |  |
| 2026-06-02 | [MeDxAgent: Multi-Agent Consultation for Interactive Medical Diagnosis](http://arxiv.org/abs/2606.03416v1) | 诊断/鉴别诊断 | 28 pages, 6 figures |
| 2026-06-01 | [ClinEnv: An Interactive Multi-Stage Long Horizon EHR Environment for Agents](http://arxiv.org/abs/2606.02568v1) | 评测基准/环境 | 20 pages, 6 figures, 12 tables |
| 2026-06-01 | [Better with Experience: Self-Evolving LLM Agents for Evidence-Grounded Health Community Notes](http://arxiv.org/abs/2606.02215v1) | 训练方法(RL/微调) |  |
| 2026-05-31 | [DrugClaw and DrugAudit: A Primary-Source-Grounded Agent and Authority-Aware Benchmark for Drug-Information Question Answering](http://arxiv.org/abs/2606.01434v1) | 评测基准/环境 |  |
| 2026-05-31 | [Early Diagnosis of Wasted Computation in Multi-Agent LLM Systems via Failure-Aware Observability](http://arxiv.org/abs/2606.01365v2) | 诊断/鉴别诊断 |  |
| 2026-05-31 | [CAREAgent: Clinical Agent with Structured Reasoning and Tool-Integrated for Order Generation](http://arxiv.org/abs/2606.01094v1) | 问答/推理 |  |
| 2026-05-28 | [Why Specialist Models Still Matter: A Heterogeneous Multi-Agent Paradigm for Medical Artificial Intelligence](http://arxiv.org/abs/2605.29744v1) | 多智能体协作 | Accepted at ICML 2026. 12 pages main text, 16 pages appendix |
| 2026-05-27 | [From paper to benchmark: agentic, framework-based reproduction of under-specified methods in machine health intelligence](http://arxiv.org/abs/2605.28371v1) | 评测基准/环境 |  |
| 2026-05-26 | [Mind the Tool Failures: Achieving Synergistic Tool Gains for Medical Agents](http://arxiv.org/abs/2605.26691v1) | 评测基准/环境 |  |
| 2026-05-25 | [VeriTrace: Evolving Mental Models for Deep Research Agents](http://arxiv.org/abs/2605.26081v2) | 检索/RAG/知识 | Accepted to Findings of EMNLP 2026 |
| 2026-05-23 | [MDIA: A Multi-Agent Diagnostic Intelligence Pipeline on HealthBench Professional](http://arxiv.org/abs/2605.24699v1) | 诊断/鉴别诊断 | 33 pages, 10 figures |
| 2026-05-19 | [ClinSeekAgent: Automating Multimodal Evidence Seeking for Agentic Clinical Reasoning](http://arxiv.org/abs/2605.20176v1) | 检索/RAG/知识 | 24 pages, 9 figures; Project Page: https://ucsc-vlaa.github. |
| 2026-05-19 | [DeepLens Diagnosis Agent: Agentic Workflow Design Lets a Small Reasoning Model Compete with Frontier LLMs](http://arxiv.org/abs/2607.22555v1) | 诊断/鉴别诊断 | 20 pages, 5 figures, 5 tables. Technical report, John Snow L |
| 2026-05-16 | [SEMA-RAG: A Self-Evolving Multi-Agent Retrieval-Augmented Generation Framework for Medical Reasoning](http://arxiv.org/abs/2605.17101v2) | 训练方法(RL/微调) | Accepted to Findings of ACL 2026 |
| 2026-05-15 | [The Impact of Heatwaves on Population Health: A Large Language Model-Enhanced Agent-Based Simulation](http://arxiv.org/abs/2605.15918v1) | 模拟病人/医院 |  |
| 2026-05-13 | [Reinforcement Learning for Tool-Calling Agents in Fast Healthcare Interoperability Resources (FHIR)](http://arxiv.org/abs/2605.14126v1) | 训练方法(RL/微调) |  |
| 2026-05-13 | [ProtoMedAgent: Multimodal Clinical Interpretability via Privacy-Aware Agentic Workflows](http://arxiv.org/abs/2605.14113v2) | 安全/幻觉/攻击 | CVR 2026 |
| 2026-05-13 | [SHM-Agents: A Generalist-Specialist Integrated Agent System for Structural Health Monitoring](http://arxiv.org/abs/2605.12916v1) | 综述/观点 | 19 pages, 20 figures |
| 2026-05-10 | [SAGE: Scalable Agentic Grounded Evaluation for Crop Disease Diagnosis](http://arxiv.org/abs/2605.09768v1) | 诊断/鉴别诊断 |  |
| 2026-05-10 | [MOTOR-Bench: A Real-world Dataset and Multi-agent Framework for Zero-shot Human Mental State Understanding](http://arxiv.org/abs/2605.09703v1) | 多智能体协作 | Accepted by CVPR 2026 workshop AI4RWC |
| 2026-05-08 | [Measuring What Matters: Benchmarking Generative, Multimodal, and Agentic AI in Healthcare](http://arxiv.org/abs/2605.08445v1) | 评测基准/环境 |  |
| 2026-05-08 | [MedExAgent: Training LLM Agents to Ask, Examine, and Diagnose in Noisy Clinical Environments](http://arxiv.org/abs/2605.07058v1) | 诊断/鉴别诊断 |  |
| 2026-05-07 | [Research on Security Enhancement Methods for Adversarial Robust Large Language Model Intelligent Agents for Medical Decision-Making Tasks](http://arxiv.org/abs/2605.08257v1) | 安全/幻觉/攻击 | 5 pages, 2 figures, 1 table.Accepted for oral presentation a |
| 2026-05-05 | [CuraView: A Multi-Agent Framework for Medical Hallucination Detection with GraphRAG-Enhanced Knowledge Verification](http://arxiv.org/abs/2605.03476v1) | 安全/幻觉/攻击 | 44 pages, 8 figures, 13 tables |
| 2026-05-01 | [Virtual Speech Therapist: A Clinician-in-the-Loop AI Speech Therapy Agent for Personalized and Supervised Therapy](http://arxiv.org/abs/2605.01101v2) | 综述/观点 | Under Review |
| 2026-05-01 | [Healthcare AI GYM for Medical Agents](http://arxiv.org/abs/2605.02943v1) | 评测基准/环境 |  |
| 2026-04-30 | [Collaborative Agent Reasoning Engineering (CARE): A Three-Party Design Methodology for Systematically Engineering AI Agents with Subject Matter Experts, Developers, and Helper Agents](http://arxiv.org/abs/2604.28043v1) | 问答/推理 |  |
| 2026-04-30 | [Modeling Clinical Concern Trajectories in Language Model Agents](http://arxiv.org/abs/2604.27872v1) | 其他 |  |
| 2026-04-27 | [Agentic clinical reasoning over longitudinal myeloma records: a retrospective evaluation against expert consensus](http://arxiv.org/abs/2604.24473v1) | 问答/推理 |  |
| 2026-04-26 | [Thinking Like a Clinician: A Cognitive AI Agent for Clinical Diagnosis via Panoramic Profiling and Adversarial Debate](http://arxiv.org/abs/2604.23605v1) | 安全/幻觉/攻击 |  |
| 2026-04-25 | [CUJBench: Benchmarking LLM-Agent on Cross-Modal Failure Diagnosis from Browser to Backend](http://arxiv.org/abs/2604.23455v2) | 评测基准/环境 | 10 pages, 1 figure; updated source code url |
| 2026-04-19 | [Towards Self-Improving Error Diagnosis in Multi-Agent Systems](http://arxiv.org/abs/2604.17658v1) | 训练方法(RL/微调) | 15 pages, 3 figures; accepted at ACL 2026 Findings |
| 2026-04-14 | [QuarkMedSearch: A Long-Horizon Deep Search Agent for Exploring Medical Intelligence](http://arxiv.org/abs/2604.12867v4) | 检索/RAG/知识 |  |
| 2026-04-14 | [Coding-Free and Privacy-Preserving Agentic Framework for Data-Driven Clinical Research](http://arxiv.org/abs/2604.12258v2) | 安全/幻觉/攻击 | 10 pages, 5 figures, 2 tables, Supplementary Appendix |
| 2026-04-13 | [Dialectic-Med: Mitigating Diagnostic Hallucinations via Counterfactual Adversarial Multi-Agent Debate](http://arxiv.org/abs/2604.11258v1) | 安全/幻觉/攻击 | Accepted by ACL 2026 |
| 2026-04-13 | [ClinQueryAgent: A Conversational Agent for Population Health Management](http://arxiv.org/abs/2605.18768v1) | 问诊/医患对话 | 11 pages, 4 figures. Submitted to ACL Systems Demonstrations |
| 2026-04-09 | [MedVR: Annotation-Free Medical Visual Reasoning via Agentic Reinforcement Learning](http://arxiv.org/abs/2604.08203v1) | 训练方法(RL/微调) | Accepted by ICLR 2026 |
| 2026-04-08 | [Joint Optimization of Reasoning and Dual-Memory for Self-Learning Diagnostic Agent](http://arxiv.org/abs/2604.07269v2) | 诊断/鉴别诊断 |  |
| 2026-04-08 | [GraphDx: A Cost-Aware Knowledge-Enhanced Multi-Agent Framework for Sequential Diagnosis](http://arxiv.org/abs/2607.15280v1) | 诊断/鉴别诊断 |  |
| 2026-04-07 | [CareGuardAI: Context-Aware Multi-Agent Guardrails for Clinical Safety & Hallucination Mitigation in Patient-Facing LLMs](http://arxiv.org/abs/2604.26959v1) | 安全/幻觉/攻击 |  |
| 2026-04-03 | [ESL-Bench: An Event-Driven Synthetic Longitudinal Benchmark for Health Agents](http://arxiv.org/abs/2604.02834v1) | 评测基准/环境 |  |
| 2026-04-02 | [Care-Conditioned Neuromodulation for Autonomy-Preserving Supportive Dialogue Agents](http://arxiv.org/abs/2604.01576v1) | 问诊/医患对话 |  |
| 2026-04-01 | [Doctor-RAG: A Failure-Aware Repair Framework for Agentic Retrieval-Augmented Generation](http://arxiv.org/abs/2604.00865v2) | 检索/RAG/知识 |  |
| 2026-04-01 | [Toward Vibe Medicine: A Self-Evolving Multi-Agent Framework for Clinical Decision Support](http://arxiv.org/abs/2606.15504v2) | 训练方法(RL/微调) |  |
| 2026-03-31 | [Agentic AI for Clinical Urgency Mapping and Queue Optimization in High-Volume Outpatient Departments: A Simulation-Based Evaluation](http://arxiv.org/abs/2604.00215v1) | 模拟病人/医院 | 17 pages, 3 figures, 7 tables. Code available at https://git |
| 2026-03-31 | [One Panel Does Not Fit All: Case-Adaptive Multi-Agent Deliberation for Clinical Prediction](http://arxiv.org/abs/2604.00085v1) | 多智能体协作 |  |
| 2026-03-30 | [Within the MDT Room: Situated in Multidisciplinary Team-Grounded Agent Debate for Clinical Diagnosis](http://arxiv.org/abs/2603.28393v1) | 诊断/鉴别诊断 |  |
| 2026-03-29 | [Improving Clinical Diagnosis with Counterfactual Multi-Agent Reasoning](http://arxiv.org/abs/2603.27820v2) | 诊断/鉴别诊断 |  |
| 2026-03-28 | [MediHive: A Decentralized Agent Collective for Medical Reasoning](http://arxiv.org/abs/2603.27150v2) | 问答/推理 | Journal of healthcare informatics research |
| 2026-03-27 | [ClinicalAgents: Multi-Agent Orchestration for Clinical Decision Making with Dual-Memory](http://arxiv.org/abs/2603.26182v2) | 治疗/决策支持 | Accepted to the 32nd ACM SIGKDD Conference on Knowledge Disc |
| 2026-03-26 | [Rethinking Health Agents: From Siloed AI to Collaborative Decision Mediators](http://arxiv.org/abs/2603.24986v1) | 多智能体协作 | Accepted in CHI '26 Workshop on Human-Agent Collaboration |
| 2026-03-25 | [CarePilot: A Multi-Agent Framework for Long-Horizon Computer Task Automation in Healthcare](http://arxiv.org/abs/2603.24157v1) | 多智能体协作 | CVPR 2026 Findings |
| 2026-03-25 | [Dialogue to Question Generation for Evidence-based Medical Guideline Agent Development](http://arxiv.org/abs/2603.23937v1) | 问诊/医患对话 | 9 pages. To appear in Proceedings of Machine Learning Resear |
| 2026-03-24 | [Can LLM Agents Generate Real-World Evidence? Evaluating Observational Studies in Medical Databases](http://arxiv.org/abs/2603.22767v1) | 评测基准/环境 |  |
| 2026-03-18 | [Caging the Agents: A Zero Trust Security Architecture for Autonomous AI in Healthcare](http://arxiv.org/abs/2603.17419v1) | 安全/幻觉/攻击 | Keywords: agentic AI security, autonomous agents, healthcare |
| 2026-03-16 | [DR. INFO at the Point of Care: A Prospective Pilot Study of Physician-Perceived Value of an Agentic AI Clinical Assistant](http://arxiv.org/abs/2604.16346v2) | 安全/幻觉/攻击 |  |
| 2026-03-16 | [Open Biomedical Knowledge Graphs at Scale: Construction, Federation, and AI Agent Access with Samyama Graph Database](http://arxiv.org/abs/2603.15080v3) | 检索/RAG/知识 | 12 pages, 7 tables, open-source code and data |
| 2026-03-14 | [Six Interventions for the Responsible and Ethical Implementation of Medical AI Agents](http://arxiv.org/abs/2603.13743v1) | 评测基准/环境 | 7 pages, 1 figure |
| 2026-03-14 | [Front-End Ethics for Sensor-Fused Health Conversational Agents: An Ethical Design Space for Biometrics](http://arxiv.org/abs/2604.06203v1) | 问诊/医患对话 | Accepted at the Proceedings of the CHI 2026 Workshop: Ethics |
| 2026-03-12 | [When OpenClaw Meets Hospital: Toward an Agentic Operating System for Dynamic Clinical Workflows](http://arxiv.org/abs/2603.11721v2) | 评测基准/环境 |  |
| 2026-03-11 | [Human-AI Co-reasoning for Clinical Diagnosis with Evidence-Integrated Language Agent](http://arxiv.org/abs/2603.10492v2) | 诊断/鉴别诊断 | After further evaluation, we have decided to withdraw the cu |
| 2026-03-10 | [Automated Standardization of Legacy Biomedical Metadata Using an Ontology-Constrained LLM Agent](http://arxiv.org/abs/2604.08552v3) | 训练方法(RL/微调) |  |
| 2026-03-10 | [MedMASLab: A Unified Orchestration Framework for Benchmarking Multimodal Medical Multi-Agent Systems](http://arxiv.org/abs/2603.09909v2) | 评测基准/环境 |  |
| 2026-03-06 | [Empowering Locally Deployable Medical Agent via State Enhanced Logical Skills for FHIR-based Clinical Tasks](http://arxiv.org/abs/2603.06902v1) | EHR/结构化数据 | 10 pages, 5 figures |
| 2026-03-02 | [CARE: Towards Clinical Accountability in Multi-Modal Medical Reasoning with an Evidence-Grounded Agentic Framework](http://arxiv.org/abs/2603.01607v2) | 检索/RAG/知识 | Accepted by ICLR 2026 |
| 2026-03-01 | [MedCollab: IBIS-Guided Multi-Agent Collaboration with Hierarchical Disease Relation Chains for Clinical Diagnosis](http://arxiv.org/abs/2603.01131v4) | 诊断/鉴别诊断 |  |
| 2026-02-23 | [AgenticSum: An Agentic Inference-Time Framework for Faithful Clinical Text Summarization](http://arxiv.org/abs/2602.20040v1) | 报告/文书生成 |  |
| 2026-02-23 | [Human-Guided Agentic AI for Multimodal Clinical Prediction: Lessons from the AgentDS Healthcare Benchmark](http://arxiv.org/abs/2602.19502v2) | 评测基准/环境 | Presented at the Data Challenge track at the 14th IEEE Inter |
| 2026-02-19 | [MedClarify: An information-seeking AI agent for medical diagnosis with case-specific follow-up questions](http://arxiv.org/abs/2602.17308v1) | 诊断/鉴别诊断 |  |
| 2026-02-18 | [Agentic AI, Medical Morality, and the Transformation of the Patient-Physician Relationship](http://arxiv.org/abs/2602.16553v1) | 安全/幻觉/攻击 | 25 pages |
| 2026-02-17 | [Optimization Instability in Autonomous Agentic Workflows for Clinical Symptom Detection](http://arxiv.org/abs/2602.16037v1) | 评测基准/环境 |  |
| 2026-02-16 | [Hunt Globally: Wide Search AI Agents for Drug Asset Scouting in Investing, Business Development, and Competitive Intelligence](http://arxiv.org/abs/2602.15019v5) | 检索/RAG/知识 |  |
| 2026-02-16 | [Picking the Right Specialist: Attentive Neural Process-based Selection of Task-Specialized Models as Tools for Agentic Healthcare Systems](http://arxiv.org/abs/2602.14901v1) | 评测基准/环境 |  |
| 2026-02-15 | [A Multi-Agent Framework for Medical AI: Leveraging Fine-Tuned GPT, LLaMA, and DeepSeek R1 for Evidence-Based and Bias-Aware Clinical Query Processing](http://arxiv.org/abs/2602.14158v1) | 安全/幻觉/攻击 | 27 pages, 14 figures, 5 tables |
| 2026-02-14 | [Do Mixed-Vendor Multi-Agent LLMs Improve Clinical Diagnosis?](http://arxiv.org/abs/2603.04421v2) | 诊断/鉴别诊断 | Accepted as Oral at the EACL 2026 Workshop on Healthcare and |
| 2026-02-10 | [Closing Reasoning Gaps in Clinical Agents with Differential Reasoning Learning](http://arxiv.org/abs/2602.09945v1) | 诊断/鉴别诊断 |  |
| 2026-02-08 | [Small Agent Group is the Future of Digital Health](http://arxiv.org/abs/2602.08013v2) | 治疗/决策支持 | ICML'26 |
| 2026-02-06 | [From Conflict to Consensus: Boosting Medical Reasoning via Multi-Round Agentic RAG](http://arxiv.org/abs/2603.03292v3) | 检索/RAG/知识 | 27 pages, 8 figures, 18 tables |
| 2026-02-06 | [The Doctor Will (Still) See You Now: On the Structural Limits of Agentic AI in Healthcare](http://arxiv.org/abs/2602.18460v1) | 评测基准/环境 | 17 pages, 3 pages of appendix, 4 tables |
| 2026-02-04 | [Agentic AI in Healthcare & Medicine: A Seven-Dimensional Taxonomy for Empirical Evaluation of LLM-based Agents](http://arxiv.org/abs/2602.04813v1) | 评测基准/环境 |  |
| 2026-02-01 | [AutoHealth: An Uncertainty-Aware Multi-Agent System for Autonomous Health Data Modeling](http://arxiv.org/abs/2602.01078v1) | 多智能体协作 |  |
| 2026-01-31 | [MedTextWeaver: Procedural Knowledge Evolution in Agentic Medical Text Editing](http://arxiv.org/abs/2602.00740v2) | 检索/RAG/知识 |  |
| 2026-01-29 | [Automatic Construction of Clinical Scoring Systems with LLM Agents](http://arxiv.org/abs/2601.22324v3) | 检索/RAG/知识 |  |
| 2026-01-26 | [DEEPMED: Building a Medical DeepResearch Agent via Multi-hop Med-Search Data and Turn-Controlled Agentic Training & Inference](http://arxiv.org/abs/2601.18496v2) | 检索/RAG/知识 |  |
| 2026-01-22 | [Agentic AI Governance and Lifecycle Management in Healthcare](http://arxiv.org/abs/2601.15630v2) | 治疗/决策支持 | 21 Pages, 9 figures |
| 2026-01-21 | [Retrieval-Augmented Agentic Rubric Generation for Reliable Medical Response Evaluation](http://arxiv.org/abs/2601.15161v3) | 检索/RAG/知识 |  |
| 2026-01-19 | [Improving the Safety and Trustworthiness of Medical AI via Multi-Agent Evaluation Loops](http://arxiv.org/abs/2601.13268v1) | 安全/幻觉/攻击 |  |
| 2026 | [Automated Health Care Thematic Analysis Using a Multiagent Large Language Model: Algorithm Development and Evaluation Study.](https://pubmed.ncbi.nlm.nih.gov/42814987/) | 多智能体协作 | Journal of medical Internet research |
| 2026 | [PMxAgent: An Agentic Platform for Pharmacometrics.](https://pubmed.ncbi.nlm.nih.gov/42781735/) | 评测基准/环境 | CPT: pharmacometrics & systems pharmacology |
| 2026 | [Agentic AI in Medicine: Challenges for Responsible Development and the Case for Clinical Testing Harnesses.](https://pubmed.ncbi.nlm.nih.gov/42776404/) | 综述/观点 | Annals of biomedical engineering |
| 2026 | [From Answers to Agents: What Must Change Before Generative and Agentic AI Become Clinical Infrastructure in Hematology.](https://pubmed.ncbi.nlm.nih.gov/42764575/) | 安全/幻觉/攻击 | Turkish journal of haematology : official journal of Turkish |
| 2026 | [A medically grounded LLM agent-based tool to detect patient safety events in medical records.](https://pubmed.ncbi.nlm.nih.gov/42752617/) | 安全/幻觉/攻击 | PLOS digital health |
| 2026 | [Prompt Injection in Clinical Artificial Intelligence Systems: The Emerging Security Challenge of Large Language Models and Agentic AI.](https://pubmed.ncbi.nlm.nih.gov/42745101/) | 安全/幻觉/攻击 | Annals of biomedical engineering |
| 2026 | [On-premise medical AI agents for reliable clinical decision-making.](https://pubmed.ncbi.nlm.nih.gov/42744896/) | 治疗/决策支持 | Nature medicine |
| 2026 | [DisPhaseDB 2.0: Improved interpretation of disease-associated variants in liquid-liquid phase separation proteins with agent-accessible querying.](https://pubmed.ncbi.nlm.nih.gov/42742059/) | 评测基准/环境 | Protein science : a publication of the Protein Society |
| 2026 | [Multi-Agent collaboration as a complementary architecture for AI-generated medical examination items.](https://pubmed.ncbi.nlm.nih.gov/42736348/) | 问答/推理 | NPJ digital medicine |
| 2026 | [NeuraGraph: a visual workflow framework for reproducible biomedical text mining with LLM-agents.](https://pubmed.ncbi.nlm.nih.gov/42719913/) | 评测基准/环境 | Bioinformatics advances |
| 2026 | [AI agents in clinical medicine: delegation, supervision, and the problem of correlated failure.](https://pubmed.ncbi.nlm.nih.gov/42667591/) | 综述/观点 | Irish journal of medical science |
| 2026 | [A multi-agent vision-language debate framework for zero-shot crop disease diagnosis.](https://pubmed.ncbi.nlm.nih.gov/42643398/) | 诊断/鉴别诊断 | Frontiers in plant science |
| 2026 | [MedHopper: an agentic RAG-LLM system for multi-hop biomedical QA.](https://pubmed.ncbi.nlm.nih.gov/42594270/) | 检索/RAG/知识 | Database : the journal of biological databases and curation |
| 2026 | [Orchestrated multi agents sustain accuracy under clinical-scale workloads compared to a single agent.](https://pubmed.ncbi.nlm.nih.gov/42527531/) | 检索/RAG/知识 | medRxiv : the preprint server for health sciences |
| 2026 | [HAMAgent: human assisted multiagent system for emotion recognition and digital health-a survey and preliminary study.](https://pubmed.ncbi.nlm.nih.gov/42495047/) | 综述/观点 | Frontiers in digital health |
| 2026 | [How to benchmark medical AI agents.](https://pubmed.ncbi.nlm.nih.gov/42424385/) | 评测基准/环境 | PLoS medicine |
| 2026 | [A multi-source fusion and feedback-optimized intelligent agent for crop disease and pest diagnosis and treatment.](https://pubmed.ncbi.nlm.nih.gov/42403408/) | 诊断/鉴别诊断 | Frontiers in plant science |
| 2026 | [Agentic AI for Structural Elucidation and Discovery of Drug Metabolites from Mass Spectrometry Data.](https://pubmed.ncbi.nlm.nih.gov/42395381/) | 安全/幻觉/攻击 | bioRxiv : the preprint server for biology |
| 2026 | [Real-World Analysis of Organ Transplantation-Specific Agent Based on Large Language Model in Post-Transplant Self-Management During Off-Hours: A Mixed-Methods Study.](https://pubmed.ncbi.nlm.nih.gov/42384291/) | 治疗/决策支持 | Current medical science |
| 2026 | [A Secure Sandbox Environment for Orchestrating Medical AI Agents Using Model Context Protocols and Role-Based Access Control.](https://pubmed.ncbi.nlm.nih.gov/42317836/) | 评测基准/环境 | AMIA Joint Summits on Translational Science proceedings. AMI |
| 2026 | [Let large language models judge each other: multi-agent peer-reviewed reasoning for medical question answering.](https://pubmed.ncbi.nlm.nih.gov/42289818/) | 问答/推理 | Journal of the American Medical Informatics Association : JA |
| 2026 | [An Efficient and Reliable Agent-Based System for Clinical Data Governance.](https://pubmed.ncbi.nlm.nih.gov/42268760/) | 安全/幻觉/攻击 | IEEE journal of biomedical and health informatics |
| 2026 | [Evaluating open LLMs for agentic analysis orchestration in a typical biomedical lab.](https://pubmed.ncbi.nlm.nih.gov/42239169/) | 评测基准/环境 | bioRxiv : the preprint server for biology |
| 2026 | [Clinical agents fail silently on patient identity.](https://pubmed.ncbi.nlm.nih.gov/42217263/) | 评测基准/环境 | International journal of medical informatics |
| 2026 | [Artificial intelligence (AI) agents assemble: The new age of AI agentic workflows and their clinical applications.](https://pubmed.ncbi.nlm.nih.gov/42202957/) | 其他 | Journal of the American Academy of Dermatology |
| 2026 | [DR. INFO at the Point of Care: A Prospective Pilot Study of Physician-Perceived Value of an Agentic Artificial Intelligence Clinical Assistant.](https://pubmed.ncbi.nlm.nih.gov/42181426/) | 安全/幻觉/攻击 | Cureus |
| 2026 | [Automated Symptom Identification from Clinical Interview Transcripts in Diagnosed Schizophrenia: A Multi-Agent LLM Framework.](https://pubmed.ncbi.nlm.nih.gov/42174998/) | 诊断/鉴别诊断 | Studies in health technology and informatics |
| 2026 | [Knowledge-Based Interpretation of Multi-Modal Clinical Findings: Evaluating a Local Agentic Bridge Between Worlds.](https://pubmed.ncbi.nlm.nih.gov/42174868/) | 评测基准/环境 | Studies in health technology and informatics |
| 2026 | [A Multiassessment and Multiprofessional Agents Approach for Medical Chatbot Risk Estimation: Development and Evaluation Study.](https://pubmed.ncbi.nlm.nih.gov/42140617/) | 问诊/医患对话 | JMIR medical informatics |
| 2026 | [When Chatbots Become Agents: The Next Phase of Healthcare AI.](https://pubmed.ncbi.nlm.nih.gov/42126692/) | 问诊/医患对话 | Journal of medical systems |
| 2026 | [MediCARE: Medical Collaborative Agents REasoning over Interpretable Heterogeneous Graphs.](https://pubmed.ncbi.nlm.nih.gov/42119431/) | 问答/推理 | Artificial intelligence in medicine |
| 2026 | [Designing Agentic Workflows in Healthcare Informatics: Challenges and Insights from a Student Perspective.](https://pubmed.ncbi.nlm.nih.gov/42119128/) | 综述/观点 | Studies in health technology and informatics |
| 2026 | [Exploring the Concept of an AI-Enabled Multi-Agentic Workflow to Support Telehealth Disease Management.](https://pubmed.ncbi.nlm.nih.gov/42119115/) | 治疗/决策支持 | Studies in health technology and informatics |
| 2026 | [AgentClinic: a multimodal benchmark for tool-using clinical AI agents.](https://pubmed.ncbi.nlm.nih.gov/42045532/) | 评测基准/环境 | NPJ digital medicine |
| 2026 | [DxDirector: an agentic large language model driving the full-process clinical diagnosis.](https://pubmed.ncbi.nlm.nih.gov/42026083/) | 诊断/鉴别诊断 | Nature communications |
| 2026 | [A neural-symbolic AI agent system for biomedical concept mapping.](https://pubmed.ncbi.nlm.nih.gov/41935204/) | 评测基准/环境 | NPJ digital medicine |
| 2026 | [Med.ai ASK: an agentic system for biomedical question answering.](https://pubmed.ncbi.nlm.nih.gov/41911379/) | 问答/推理 | Journal of the American Medical Informatics Association : JA |
| 2026 | [Agentic AI in rheumatology.](https://pubmed.ncbi.nlm.nih.gov/41905369/) | 综述/观点 | The Lancet. Rheumatology |
| 2026 | [A Review of Multi-Agent AI Systems for Biological and Clinical Data Analysis.](https://pubmed.ncbi.nlm.nih.gov/41874150/) | 综述/观点 | Methods and protocols |
| 2026 | [An agentic AI system enhances clinical detection of immunotherapy toxicities: a multi-phase validation study.](https://pubmed.ncbi.nlm.nih.gov/41867215/) | 综述/观点 | medRxiv : the preprint server for health sciences |
| 2026 | [MedAgentBench v2: Improving Medical LLM Agent Design.](https://pubmed.ncbi.nlm.nih.gov/41758153/) | 评测基准/环境 | Pacific Symposium on Biocomputing. Pacific Symposium on Bioc |
| 2026 | [When Agentic LLMs Trust Poisoned Tools: Vulnerability of Clinical LLMs to Adversarial Guidelines.](https://pubmed.ncbi.nlm.nih.gov/41756452/) | 安全/幻觉/攻击 | Research square |
| 2026 | [Bridging Perception and Reasoning: An Evidence-Based Agentic System for Diagnosis and Treatment Recommendations of Vascular Anomalies.](https://pubmed.ncbi.nlm.nih.gov/41750769/) | 诊断/鉴别诊断 | Diagnostics (Basel, Switzerland) |
| 2026 | [FHIR-AgentEval: A Modular Sandbox for Benchmarking Clinical LLM Agents with an Evaluation of Memory-Augmented Configurations.](https://pubmed.ncbi.nlm.nih.gov/41727598/) | 评测基准/环境 | Research square |
| 2026 | [Agentic memory-augmented retrieval and evidence grounding for medical question-answering tasks.](https://pubmed.ncbi.nlm.nih.gov/41713127/) | 检索/RAG/知识 | International journal of medical informatics |
| 2026 | [Benchmarking large language model-based agent systems for clinical decision tasks.](https://pubmed.ncbi.nlm.nih.gov/41708802/) | 评测基准/环境 | NPJ digital medicine |
| 2026 | [Comparative Performance of agentic AI and Physicians in Taking Clinical History across Leading Large Language Models (LLMs).](https://pubmed.ncbi.nlm.nih.gov/41646794/) | 模拟病人/医院 | medRxiv : the preprint server for health sciences |
| 2026 | [Early diagnosis of axial spondyloarthritis in primary care using multi-agent systems.](https://pubmed.ncbi.nlm.nih.gov/41571772/) | 诊断/鉴别诊断 | NPJ digital medicine |
| 2026 | [A randomized controlled trial of a WeChat-based artificial intelligence agent for postoperative care in orthopedic patients.](https://pubmed.ncbi.nlm.nih.gov/41548028/) | 综述/观点 | NPJ digital medicine |
| 2026 | [From Agents to Governance: Essential AI Skills for Clinicians in the Large Language Model Era.](https://pubmed.ncbi.nlm.nih.gov/41534067/) | 综述/观点 | Journal of medical Internet research |
| 2026 | [Generative AI in pharmaceutical R&D: From large language models to AI agents to regulation.](https://pubmed.ncbi.nlm.nih.gov/41519434/) | 综述/观点 | Drug discovery today |
| 2026 | [An autonomous agentic workflow for clinical detection of cognitive concerns using large language models.](https://pubmed.ncbi.nlm.nih.gov/41501421/) | 报告/文书生成 | NPJ digital medicine |
| 2026 | [Hierarchical agent reflection for aligning LLM reasoning with clinical diagnostic processes.](https://pubmed.ncbi.nlm.nih.gov/41497892/) | 诊断/鉴别诊断 | Health information science and systems |
| 2026 | [Using secure artificial intelligence agents integrated within the electronic medical record for the evaluation of blood culture appropriateness-Northern California, 2025.](https://pubmed.ncbi.nlm.nih.gov/41216923/) | 评测基准/环境 | Infection control and hospital epidemiology |
| 2026 | [Small language models: The big play for agentic artificial intelligence in orthopaedics.](https://pubmed.ncbi.nlm.nih.gov/41144760/) | 评测基准/环境 | Knee surgery, sports traumatology, arthroscopy : official jo |
| 2026 | [MedARC: Adaptive multi-agent refinement and collaboration for enhanced medical reasoning in large language models.](https://pubmed.ncbi.nlm.nih.gov/41109093/) | 问答/推理 | International journal of medical informatics |
| 2025-12-18 | [Automated Healthcare Thematic Analysis using Multi-Agent Large Language Model: Algorithm Development and Evaluation](http://arxiv.org/abs/2512.16063v2) | 多智能体协作 | 45 pages, 5 figures |
| 2025-12-12 | [MedAI: Evaluating TxAgent's Therapeutic Agentic Reasoning in the NeurIPS CURE-Bench Competition](http://arxiv.org/abs/2512.11682v2) | 评测基准/环境 | 7 pages, 3 figures |
| 2025-12-11 | [AutoMedic: An Automated Evaluation Framework for Clinical Conversational Agents with Medical Dataset Grounding](http://arxiv.org/abs/2512.10195v1) | 问诊/医患对话 | IEEE journal of biomedical and health informatics |
| 2025-12-03 | [Orchestrator Multi-Agent Clinical Decision Support System for Secondary Headache Diagnosis in Primary Care](http://arxiv.org/abs/2512.04207v2) | 诊断/鉴别诊断 | Journal of the American Medical Informatics Association : JA |
| 2025-12-03 | [Multi-Aspect Knowledge-Enhanced Medical Vision-Language Pretraining with Multi-Agent Data Generation](http://arxiv.org/abs/2512.03445v1) | 多智能体协作 | 10 pages. Under Review |
| 2025-12-02 | [UCAgents: Unidirectional Convergence for Visual Evidence Anchored Multi-Agent Medical Decision-Making](http://arxiv.org/abs/2512.02485v1) | 治疗/决策支持 |  |
| 2025-12-01 | [Many-to-One Adversarial Consensus: Exposing Multi-Agent Collusion Risks in AI-Based Healthcare](http://arxiv.org/abs/2512.03097v1) | 安全/幻觉/攻击 | 7 pages Conference level paper |
| 2025-12-01 | [Reinventing Clinical Dialogue: Agentic Paradigms for LLM Enabled Healthcare Communication](http://arxiv.org/abs/2512.01453v1) | 问诊/医患对话 |  |
| 2025-11-29 | [Exploring Health Misinformation Detection with Multi-Agent Debate](http://arxiv.org/abs/2512.09935v1) | 多智能体协作 |  |
| 2025-11-27 | [Byzantine Fault-Tolerant Multi-Agent System for Healthcare: A Gossip Protocol Approach to Secure Medical Message Propagation](http://arxiv.org/abs/2512.17913v1) | 多智能体协作 |  |
| 2025-11-19 | [OEMA: Ontology-Enhanced Multi-Agent Collaboration Framework for Zero-Shot Clinical Named Entity Recognition](http://arxiv.org/abs/2511.15211v2) | 多智能体协作 | JAMIA open |
| 2025-11-18 | [MedBench v4: A Robust and Scalable Benchmark for Evaluating Chinese Medical Language Models, Multimodal Models, and Intelligent Agents](http://arxiv.org/abs/2511.14439v2) | 评测基准/环境 |  |
| 2025-11-17 | [Causal Reinforcement Learning based Agent-Patient Interaction with Clinical Domain Knowledge](http://arxiv.org/abs/2512.00048v1) | 训练方法(RL/微调) | Accepted by AAAI workshop |
| 2025-11-17 | [Grounded by Experience: Generative Healthcare Prediction Augmented with Hierarchical Agentic Retrieval](http://arxiv.org/abs/2511.13293v1) | 检索/RAG/知识 |  |
| 2025-10-28 | [Evolving Interactive Diagnostic Agents in a Virtual Clinical Environment](http://arxiv.org/abs/2510.24654v2) | 诊断/鉴别诊断 |  |
| 2025-10-21 | [Med-VRAgent: A Framework for Medical Visual Reasoning-Enhanced Agents](http://arxiv.org/abs/2510.18424v1) | 问答/推理 |  |
| 2025-10-17 | [MedBuild AI: An Agent-Based Hybrid Intelligence Framework for Reshaping Agency in Healthcare Infrastructure Planning through Generative Design for Medical Architecture](http://arxiv.org/abs/2511.11587v3) | 问诊/医患对话 | 24 pages, 16 figures. Submitted to the IJAC Special Issue "R |
| 2025-10-11 | [Auditing medical multi-agent AI reveals risks of false consensus](http://arxiv.org/abs/2510.10185v3) | 多智能体协作 | Code and Data: https://github.com/MedX-PKU/MedAgentAudit |
| 2025-10-06 | [Biomedical reasoning in action: Multi-agent System for Auditable Biomedical Evidence Synthesis](http://arxiv.org/abs/2510.05335v1) | 检索/RAG/知识 |  |
| 2025-10-06 | [MedPAO: A Protocol-Driven Agent for Structuring Medical Reports](http://arxiv.org/abs/2510.04623v1) | 报告/文书生成 | Paper published at "Agentic AI for Medicine" Workshop, MICCA |
| 2025-10-05 | [Doctor-R1: Mastering Clinical Inquiry with Experiential Agentic Reinforcement Learning](http://arxiv.org/abs/2510.04284v3) | 训练方法(RL/微调) |  |
| 2025-09-30 | [A Field Guide to Deploying AI Agents in Clinical Practice](http://arxiv.org/abs/2509.26153v3) | 综述/观点 | Under review. 7 Tables, 2 Figures |
| 2025-09-29 | [The Dialogue That Heals: A Comprehensive Evaluation of Doctor Agents' Inquiry Capability](http://arxiv.org/abs/2509.24958v2) | 评测基准/环境 |  |
| 2025-09-29 | [MedMMV: A Controllable Multimodal Multi-Agent Framework for Reliable and Verifiable Clinical Reasoning](http://arxiv.org/abs/2509.24314v1) | 问答/推理 | 25 pages, 5 figures |
| 2025-09-29 | [PAME-AI: Patient Messaging Creation and Optimization using Agentic AI](http://arxiv.org/abs/2509.24263v2) | 其他 |  |
| 2025-09-28 | [MedLA: A Logic-Driven Multi-Agent Framework for Complex Medical Reasoning with Large Language Models](http://arxiv.org/abs/2509.23725v3) | 问答/推理 | accepted by AAAI-26 (ORAL) |
| 2025-09-27 | [From Conversation to Query Execution: Benchmarking User and Tool Interactions for EHR Database Agents](http://arxiv.org/abs/2509.23415v2) | 评测基准/环境 | ICLR 2026 |
| 2025-09-26 | [AMANDA: Agentic Medical Knowledge Augmentation for Data-Efficient Medical Visual Question Answering](http://arxiv.org/abs/2510.02328v1) | 问答/推理 | EMNLP Findings |
| 2025-09-25 | [Agentic-AI Healthcare: Multilingual, Privacy-First Framework with MCP Agents](http://arxiv.org/abs/2510.02325v1) | 安全/幻觉/攻击 | 6 pages, 1 figure. Submitted as a system/vision paper |
| 2025-09-24 | [MACD: Multi-Agent Clinical Diagnosis with Self-Learned Knowledge for LLM](http://arxiv.org/abs/2509.20067v5) | 诊断/鉴别诊断 |  |
| 2025-09-18 | [OpenLens AI: Fully Autonomous Research Agent for Health Infomatics](http://arxiv.org/abs/2509.14778v2) | 检索/RAG/知识 |  |
| 2025-09-15 | [Agentic Temporal Graph of Reasoning with Multimodal Language Models: A Potential AI Aid to Healthcare](http://arxiv.org/abs/2509.11944v1) | 问答/推理 |  |
| 2025-09-15 | [Agentic System with Modal Logic for Autonomous Diagnostics](http://arxiv.org/abs/2509.11943v3) | 诊断/鉴别诊断 | 10 pages, 1 figure |
| 2025-09-15 | [MedicalOS: An LLM Agent based Operating System for Digital Healthcare](http://arxiv.org/abs/2509.11507v1) | 安全/幻觉/攻击 |  |
| 2025-09-14 | [Patient-Zero: Scaling Synthetic Patient Agents to Real-World Distributions without Real Patient Data](http://arxiv.org/abs/2509.11078v2) | 模拟病人/医院 |  |
| 2025-09-12 | [Compartmentalised Agentic Reasoning for Clinical NLI](http://arxiv.org/abs/2509.10222v2) | 问答/推理 |  |
| 2025-09-12 | [FHIR-AgentBench: Benchmarking LLM Agents for Realistic Interoperable EHR Question Answering](http://arxiv.org/abs/2509.19319v2) | 评测基准/环境 | ML4H 2025 Proceedings |
| 2025-09-04 | [An Agentic Model Context Protocol Framework for Medical Concept Standardization](http://arxiv.org/abs/2509.03828v1) | 安全/幻觉/攻击 |  |
| 2025-08-29 | [Automated Clinical Problem Detection from SOAP Notes using a Collaborative Multi-Agent LLM Architecture](http://arxiv.org/abs/2508.21803v1) | 多智能体协作 | Accepted to The 16th ACM Conference on Bioinformatics, Compu |
| 2025-08-26 | [MATRIX: Multi-Agent simulaTion fRamework for safe Interactions and conteXtual clinical conversational evaluation](http://arxiv.org/abs/2508.19163v1) | 模拟病人/医院 | 36 pages, 16 figures |
| 2025-08-26 | [Trustworthy Agents for Electronic Health Records through Confidence Estimation](http://arxiv.org/abs/2508.19096v1) | 安全/幻觉/攻击 |  |
| 2025-08-22 | [LLM-Based Agents for Competitive Landscape Mapping in Drug Asset Due Diligence](http://arxiv.org/abs/2508.16571v4) | 评测基准/环境 |  |
| 2025-08-21 | [End-to-End Agentic RAG System Training for Traceable Diagnostic Reasoning](http://arxiv.org/abs/2508.15746v2) | 诊断/鉴别诊断 |  |
| 2025-08-19 | [LLM-Powered Virtual Patient Agents for Interactive Clinical Skills Training with Automated Feedback](http://arxiv.org/abs/2508.13943v1) | 模拟病人/医院 |  |
| 2025-08-17 | [MedKGent: A Large Language Model Agent Framework for Constructing Temporally Evolving Medical Knowledge Graph](http://arxiv.org/abs/2508.12393v3) | 检索/RAG/知识 | Accepted by Npj Digital Medicine |
| 2025-08-11 | [TeamMedAgents: Pareto-Efficient Multi-Agent Medical Reasoning Through Teamwork Theory](http://arxiv.org/abs/2508.08115v3) | 问答/推理 | 19 pages, 6 figure, 12 tables, 2 algorithm |
| 2025-08-08 | [Mediator-Guided Multi-Agent Collaboration among Open-Source Models for Medical Decision-Making](http://arxiv.org/abs/2508.05996v2) | 治疗/决策支持 | 14 pages, 4 figures |
| 2025-08-07 | [MoMA: A Mixture-of-Multimodal-Agents Architecture for Enhancing Clinical Prediction Modelling](http://arxiv.org/abs/2508.05492v1) | 评测基准/环境 | NPJ digital medicine |
| 2025-08-05 | [Tree-of-Reasoning: Towards Complex Medical Diagnosis via Multi-Agent Reasoning with Evidence Tree](http://arxiv.org/abs/2508.03038v1) | 诊断/鉴别诊断 | Accepted by ACM MM 2025 |
| 2025-07-27 | [Embeddings to Diagnosis: Latent Fragility under Agentic Perturbations in Clinical LLMs](http://arxiv.org/abs/2507.21188v1) | 诊断/鉴别诊断 |  |
| 2025-07-26 | [CANDLE: A Cross-Modal Agentic Knowledge Distillation Framework for Interpretable Sarcopenia Diagnosis](http://arxiv.org/abs/2507.21179v2) | 诊断/鉴别诊断 | 11 pages, 4 figures, 5 tables |
| 2025-07-25 | [MAC: Masked Agent Collaboration Boosts Large Language Model Medical Decision-Making](http://arxiv.org/abs/2507.21159v3) | 治疗/决策支持 |  |
| 2025-07-24 | [Agentic AI framework for End-to-End Medical Data Inference](http://arxiv.org/abs/2507.18115v1) | 安全/幻觉/攻击 | 10 pages, 5 figures, 2 tables, BIBM conference |
| 2025-07-22 | [Voice-based AI Agents: Filling the Economic Gaps in Digital Health Delivery](http://arxiv.org/abs/2507.16229v1) | 综述/观点 | IEEE International Conference on Digital Health (ICDH) 2025 |
| 2025-07-16 | [Infherno: End-to-end Agent-based FHIR Resource Synthesis from Free-form Clinical Notes](http://arxiv.org/abs/2507.12261v2) | 报告/文书生成 | EACL 2026 System Demonstrations / Code: https://github.com/j |
| 2025-07-15 | [Dr.Copilot: A Multi-Agent Prompt Optimized Assistant for Improving Patient-Doctor Communication in Romanian](http://arxiv.org/abs/2507.11299v2) | 问诊/医患对话 | 10 figures, 2 tables, 2 listings |
| 2025-07-09 | [Multi-Agent Retrieval-Augmented Framework for Evidence-Based Counterspeech Against Health Misinformation](http://arxiv.org/abs/2507.07307v2) | 检索/RAG/知识 | Accepted for publication at COLM 2025 |
| 2025-07-07 | [Architecting Clinical Collaboration: Multi-Agent Reasoning Systems for Multimodal Medical VQA](http://arxiv.org/abs/2507.05520v3) | 问答/推理 |  |
| 2025-07-03 | [KERAP: A Knowledge-Enhanced Reasoning Approach for Accurate Zero-shot Diagnosis Prediction Using Multi-agent LLMs](http://arxiv.org/abs/2507.02773v2) | 诊断/鉴别诊断 | AMIA ... Annual Symposium proceedings. AMIA Symposium |
| 2025-07-03 | [DynamiCare: A Dynamic Multi-Agent Framework for Interactive and Open-Ended Medical Decision-Making](http://arxiv.org/abs/2507.02616v1) | 治疗/决策支持 | AMIA Joint Summits on Translational Science proceedings. AMI |
| 2025-07-02 | [PAL: Designing Conversational Agents as Scalable, Cooperative Patient Simulators for Palliative-Care Training](http://arxiv.org/abs/2507.02122v1) | 模拟病人/医院 |  |
| 2025-06-27 | [Toward the Autonomous AI Doctor: Quantitative Benchmarking of an Autonomous Agentic AI Versus Board-Certified Clinicians in a Real World Setting](http://arxiv.org/abs/2507.22902v1) | 评测基准/环境 |  |
| 2025-06-24 | [MAM: Modular Multi-Agent Framework for Multi-Modal Medical Diagnosis via Role-Specialized Collaboration](http://arxiv.org/abs/2506.19835v1) | 诊断/鉴别诊断 | ACL 2025 Findings |
| 2025-06-18 | [From RAG to Agentic: Validating Islamic-Medicine Responses with LLM Agents](http://arxiv.org/abs/2506.15911v2) | 检索/RAG/知识 | Published at the 4th Muslims in Machine Learning (MusIML) Wo |
| 2025-06-14 | [Tiered Agentic Oversight: A Hierarchical Multi-Agent System for Healthcare Safety](http://arxiv.org/abs/2506.12482v2) | 安全/幻觉/攻击 |  |
| 2025-06-12 | [Neural at ArchEHR-QA 2025: Agentic Prompt Optimization for Evidence-Grounded Clinical Question Answering](http://arxiv.org/abs/2506.10751v2) | 检索/RAG/知识 | Accepted to Proceedings of the 24th Workshop on Biomedical L |
| 2025-06-11 | [ReasonMed: A 370K Multi-Agent Generated Dataset for Advancing Medical Reasoning](http://arxiv.org/abs/2506.09513v3) | 问答/推理 | 28 pages, 6 figures, 7 tables |
| 2025-06-04 | [MedAgentGym: A Scalable Agentic Training Environment for Code-Centric Reasoning in Biomedical Data Science](http://arxiv.org/abs/2506.04405v2) | 评测基准/环境 |  |
| 2025-05-29 | [CDR-Agent: Intelligent Selection and Execution of Clinical Decision Rules Using Large Language Model Agents](http://arxiv.org/abs/2505.23055v2) | 治疗/决策支持 | AMIA ... Annual Symposium proceedings. AMIA Symposium |
| 2025-05-27 | [BehaviorSFT: Behavioral Token Conditioning for Clinical Agents Across the Proactivity Spectrum](http://arxiv.org/abs/2505.21757v1) | 训练方法(RL/微调) |  |
| 2025-05-27 | [Silence is Not Consensus: Disrupting Agreement Bias in Multi-Agent LLMs via Catfish Agent for Clinical Decision Making](http://arxiv.org/abs/2505.21503v1) | 安全/幻觉/攻击 |  |
| 2025-05-27 | [MedSentry: Understanding and Mitigating Safety Risks in Medical LLM Multi-Agent Systems](http://arxiv.org/abs/2505.20824v1) | 安全/幻觉/攻击 |  |
| 2025-05-26 | [Real-World Doctor Agent with Proactive Consultation through Multi-Agent Reinforcement Learning](http://arxiv.org/abs/2505.19630v4) | 训练方法(RL/微调) |  |
| 2025-05-24 | [DDO: Dual-Decision Optimization for LLM-Based Medical Consultation via Multi-Agent Collaboration](http://arxiv.org/abs/2505.18630v2) | 问诊/医患对话 | Accepted to EMNLP 2025 |
| 2025-05-22 | [No Black Boxes: Interpretable and Interactable Predictive Healthcare with Knowledge-Enhanced Agentic Causal Discovery](http://arxiv.org/abs/2505.16288v2) | 训练方法(RL/微调) | EMNLP 2025 |
| 2025-05-18 | [MedAgentBoard: Benchmarking Multi-Agent Collaboration with Conventional Methods for Diverse Medical Tasks](http://arxiv.org/abs/2505.12371v2) | 评测基准/环境 | Accepted by NeurIPS 2025 Datasets & Benchmarks Track |
| 2025-05-06 | [FRAME: Feedback-Refined Agent Methodology for Enhancing Medical Research Insights](http://arxiv.org/abs/2505.04649v3) | 检索/RAG/知识 | 12 pages, 4 figures, 5 table |
| 2025-04-30 | [Talk Before You Retrieve: Agent-Led Discussions for Better RAG in Medical QA](http://arxiv.org/abs/2504.21252v1) | 检索/RAG/知识 |  |
| 2025-04-28 | [Knowledge-Driven Agentic Scientific Corpus Distillation Framework for Biomedical Large Language Models Training](http://arxiv.org/abs/2504.19565v3) | 训练方法(RL/微调) | Biomedical Large Language Models, Agentic Corpus Distillatio |
| 2025-04-24 | [Towards a HIPAA Compliant Agentic AI System in Healthcare](http://arxiv.org/abs/2504.17669v2) | 报告/文书生成 |  |
| 2025-04-15 | [Learning to Be A Doctor: Searching for Effective Medical Agent Architectures](http://arxiv.org/abs/2504.11301v2) | 检索/RAG/知识 | Accepted at ACM MM 2025 |
| 2025-04-04 | [YaleNLP @ PerAnsSumm 2025: Multi-Perspective Integration via Mixture-of-Agents for Enhanced Healthcare QA Summarization](http://arxiv.org/abs/2504.03932v1) | 综述/观点 | Paper accepted at CL4HEALTH @ NAACL 2025: Annual Conference  |
| 2025-04-03 | [Survey and Experiments on Mental Disorder Detection via Social Media: From Large Language Models and RAG to Agents](http://arxiv.org/abs/2504.02800v4) | 综述/观点 | 20 pages, 10 figures. This is an extension of ICDEW 2025 |
| 2025-04-02 | [Emerging Cyber Attack Risks of Medical AI Agents](http://arxiv.org/abs/2504.03759v1) | 安全/幻觉/攻击 |  |
| 2025-03-26 | [3MDBench: Medical Multimodal Multi-agent Dialogue Benchmark](http://arxiv.org/abs/2504.13861v3) | 评测基准/环境 | EMNLP 25 (main) |
| 2025-03-21 | [MedAgent-Pro: Towards Evidence-based Multi-modal Medical Diagnosis via Reasoning Agentic Workflow](http://arxiv.org/abs/2503.18968v3) | 诊断/鉴别诊断 |  |
| 2025-03-19 | [Empowering Medical Multi-Agents with Clinical Consultation Flow for Dynamic Diagnosis](http://arxiv.org/abs/2503.16547v1) | 诊断/鉴别诊断 |  |
| 2025-03-18 | [MDTeamGPT: A Self-Evolving LLM-based Multi-Agent Framework for Multi-Disciplinary Team Medical Consultation](http://arxiv.org/abs/2503.13856v1) | 训练方法(RL/微调) | 24 pages |
| 2025-03-10 | [MedicalAgentsBench for Complex Medical Reasoning: Comparing Internalized Reasoning Models versus Externalized Agent-based Frameworks](http://arxiv.org/abs/2503.07459v3) | 问答/推理 | https://github.com/gersteinlab/MedicalAgentsBench |
| 2025-03-07 | [Multi Agent based Medical Assistant for Edge Devices](http://arxiv.org/abs/2503.05397v1) | 综述/观点 |  |
| 2025-02-26 | [MEDDxAgent: A Unified Modular Agent Framework for Explainable Automatic Differential Diagnosis](http://arxiv.org/abs/2502.19175v2) | 诊断/鉴别诊断 | ACL 2025 (main) |
| 2025-02-24 | [Improving Interactive Diagnostic Ability of a Large Language Model Agent Through Clinical Experience Learning](http://arxiv.org/abs/2503.16463v1) | 诊断/鉴别诊断 | 30 pages |
| 2025-02-21 | [AutoToM: Scaling Model-based Mental Inference via Automated Agent Modeling](http://arxiv.org/abs/2502.15676v3) | 评测基准/环境 | NeurIPS 2025 (Spotlight). 42 pages, 11 figures, 15 tables. W |
| 2025-02-19 | [UM_FHS at TREC 2024 PLABA: Exploration of Fine-tuning and AI agent approach for plain language adaptations of biomedical text](http://arxiv.org/abs/2502.14144v1) | 训练方法(RL/微调) | 10 pages, 2 figures, to be published in the 33rd Text REtrie |
| 2025-02-18 | [Agentic Medical Knowledge Graphs Enhance Medical Question Answering: Bridging the Gap Between LLMs and Evolving Medical Knowledge](http://arxiv.org/abs/2502.13010v3) | 检索/RAG/知识 |  |
| 2025-02-16 | [A Survey of LLM-based Agents in Medicine: How far are we from Baymax?](http://arxiv.org/abs/2502.11211v2) | 综述/观点 | ACL 2025 Findings |
| 2025-01-24 | [MedAgentBench: A Realistic Virtual EHR Environment to Benchmark Medical LLM Agents](http://arxiv.org/abs/2501.14654v2) | 评测基准/环境 |  |
| 2025 | [From chat to act: large language model agents and agentic AI as the next frontier of AI in rheumatology.](https://pubmed.ncbi.nlm.nih.gov/42368619/) | 综述/观点 | EULAR rheumatology open |
| 2025 | [Virtual Agent for Real-Time Motivational Interviewing by Integrating Adaptive Nonverbal Behavior and Language Models.](https://pubmed.ncbi.nlm.nih.gov/41525230/) | 问诊/医患对话 | Journal of visualized experiments : JoVE |
| 2025 | [A medically grounded LLM agent-based tool to detect patient safety events in medical records: Identifying patient safety events with large language models.](https://pubmed.ncbi.nlm.nih.gov/41445638/) | 安全/幻觉/攻击 | medRxiv : the preprint server for health sciences |
| 2025 | [Autonomous Analysis of Curated Patient Data Using a Large Language Model-Based Multiagent Framework.](https://pubmed.ncbi.nlm.nih.gov/41418093/) | 多智能体协作 | JCO clinical cancer informatics |
| 2025 | [A Multiagent Summarization and Auto-Evaluation Framework for Medical Text: Development and Evaluation Study.](https://pubmed.ncbi.nlm.nih.gov/41401442/) | 报告/文书生成 | JMIR AI |
| 2025 | [A Bilingual On-Premises AI Agent for Clinical Drafting: Implementation Report of Seamless Electronic Health Records Integration in the Y-KNOT Project.](https://pubmed.ncbi.nlm.nih.gov/41284981/) | 报告/文书生成 | JMIR medical informatics |
| 2025 | [Enhancing Large Language Models With AI Agents for Chronic Gastritis Management: Comprehensive Comparative Study.](https://pubmed.ncbi.nlm.nih.gov/41236204/) | 治疗/决策支持 | JMIR medical informatics |
| 2025 | [Privacy-, linguistic-, and information-preserving synthesis of clinical documentation through generative agents.](https://pubmed.ncbi.nlm.nih.gov/41036253/) | 安全/幻觉/攻击 | Frontiers in artificial intelligence |
| 2025 | [Optimizing Order Sets With a Large Language Model-Powered Multiagent System.](https://pubmed.ncbi.nlm.nih.gov/40986301/) | 多智能体协作 | JAMA network open |
| 2025 | [From data silos to insights: the PRINCE multi-agent knowledge engine for preclinical drug development.](https://pubmed.ncbi.nlm.nih.gov/40904819/) | 多智能体协作 | Frontiers in artificial intelligence |
| 2025 | [Multiagent AI Systems in Health Care: Envisioning Next-Generation Intelligence.](https://pubmed.ncbi.nlm.nih.gov/40831649/) | 多智能体协作 | Federal practitioner : for the health care professionals of  |
| 2025 | [Generative AI as Third Agent: Large Language Models and the Transformation of the Clinician-Patient Relationship.](https://pubmed.ncbi.nlm.nih.gov/40826831/) | 综述/观点 | Journal of participatory medicine |
| 2025 | [Democratizing cost-effective, agentic artificial intelligence to multilingual medical summarization through knowledge distillation.](https://pubmed.ncbi.nlm.nih.gov/40730812/) | 报告/文书生成 | Scientific reports |
| 2025 | [Conversational health agents: a personalized large language model-powered agent framework.](https://pubmed.ncbi.nlm.nih.gov/40620478/) | 问诊/医患对话 | JAMIA open |
| 2025 | [Assessment of GPT-Based Conversational Agents Aimed to Reduce Healthcare Provider Stigma.](https://pubmed.ncbi.nlm.nih.gov/40588869/) | 问诊/医患对话 | Studies in health technology and informatics |
| 2025 | [Integrating large language model-based agents into a virtual patient chatbot for clinical anamnesis training.](https://pubmed.ncbi.nlm.nih.gov/40547455/) | 模拟病人/医院 | Computational and structural biotechnology journal |
| 2025 | [Agent-guided AI-powered interpretation and reporting of nerve conduction studies and EMG (INSPIRE).](https://pubmed.ncbi.nlm.nih.gov/40540846/) | 报告/文书生成 | Clinical neurophysiology : official journal of the Internati |
| 2025 | [ABCD: A Simulation Method for Accelerating Conversational Agents With Applications in Aphasia Therapy.](https://pubmed.ncbi.nlm.nih.gov/40512969/) | 模拟病人/医院 | Journal of speech, language, and hearing research : JSLHR |
| 2025 | [Answering real-world clinical questions using large language model, retrieval-augmented generation, and agentic systems.](https://pubmed.ncbi.nlm.nih.gov/40510193/) | 检索/RAG/知识 | Digital health |
| 2025 | [How generative AI voice agents will transform medicine.](https://pubmed.ncbi.nlm.nih.gov/40506466/) | 综述/观点 | NPJ digital medicine |
| 2025 | [Performance of single-agent and multi-agent language models in Spanish language medical competency exams.](https://pubmed.ncbi.nlm.nih.gov/40336004/) | 问答/推理 | BMC medical education |
| 2025 | [DruGagent: Multi-Agent Large Language Model-Based Reasoning for Drug-Target Interaction Prediction.](https://pubmed.ncbi.nlm.nih.gov/40297237/) | 问答/推理 | ArXiv |
| 2025 | [Performance of Three Conversational Artificial Intelligence Agents in Defining End-of-Life Care Terms.](https://pubmed.ncbi.nlm.nih.gov/40138176/) | 问诊/医患对话 | Journal of palliative medicine |
| 2025 | [Large language model agents can use tools to perform clinical calculations.](https://pubmed.ncbi.nlm.nih.gov/40097720/) | 安全/幻觉/攻击 | NPJ digital medicine |
| 2025 | [Enhancing diagnostic capability with multi-agents conversational large language models.](https://pubmed.ncbi.nlm.nih.gov/40082662/) | 诊断/鉴别诊断 | NPJ digital medicine |
| 2025 | [ESCARGOT: an AI agent leveraging large language models, dynamic graph of thoughts, and biomedical knowledge graphs for enhanced reasoning.](https://pubmed.ncbi.nlm.nih.gov/39842860/) | 检索/RAG/知识 | Bioinformatics (Oxford, England) |
| 2024-12-22 | [KG4Diagnosis: A Hierarchical Multi-Agent LLM Framework with Knowledge Graph Enhancement for Medical Diagnosis](http://arxiv.org/abs/2412.16833v4) | 诊断/鉴别诊断 | 10 pages,5 figures,published to AAAI-25 Bridge Program |
| 2024-12-16 | [LLMs Can Simulate Standardized Patients via Agent Coevolution](http://arxiv.org/abs/2412.11716v2) | 模拟病人/医院 | Accepted to ACL 2025 |
| 2024-12-02 | [Medchain: Bridging the Gap Between LLM Agents and Clinical Practice with Interactive Sequence](http://arxiv.org/abs/2412.01605v2) | 评测基准/环境 | Accepted by NeurIPS25 Spotlight |
| 2024-11-16 | [Towards Next-Generation Medical Agent: How o1 is Reshaping Decision-Making in Medical Scenarios](http://arxiv.org/abs/2411.14461v1) | 治疗/决策支持 |  |
| 2024-11-09 | [GuidelineGuard: An Agentic Framework for Medical Note Evaluation with Guideline Adherence](http://arxiv.org/abs/2411.06264v1) | 评测基准/环境 |  |
| 2024-10-23 | [ReflecTool: Towards Reflection-Aware Tool-Augmented Clinical Agents](http://arxiv.org/abs/2410.17657v3) | 评测基准/环境 | ACL 2025 Main Paper |
| 2024-10-17 | [MeNTi: Bridging Medical Calculator and LLM Agent with Nested Tool Calling](http://arxiv.org/abs/2410.13610v3) | 评测基准/环境 | NAACL 2025 main conference. Code and Dataset available at [h |
| 2024-10-16 | [MedAide: Information Fusion and Anatomy of Medical Intents via LLM-based Agent Collaboration](http://arxiv.org/abs/2410.12532v3) | 多智能体协作 | LLM-based Multi-Agent Collaboration for Medical Applications |
| 2024-10-13 | [IMAS: A Comprehensive Agentic Approach to Rural Healthcare Delivery](http://arxiv.org/abs/2410.12868v1) | 综述/观点 |  |
| 2024-10-13 | [Adaptive Reasoning and Acting in Medical Language Agents](http://arxiv.org/abs/2410.10020v1) | 问答/推理 |  |
| 2024-10-07 | [KGARevion: An AI Agent for Knowledge-Intensive Biomedical QA](http://arxiv.org/abs/2410.04660v2) | 问答/推理 |  |
| 2024-10-03 | [ColaCare: Enhancing Electronic Health Record Modeling through Large Language Model-Driven Multi-Agent Collaboration](http://arxiv.org/abs/2410.02551v2) | EHR/结构化数据 | ACM TheWebConf 2025 Conference (WWW 2025) Research Track |
| 2024-08-23 | [DrugAgent: Reliable Multi-Agent Integration of Conflicting Biomedical Evidence for Drug-Target Interaction Assessment](http://arxiv.org/abs/2408.13378v5) | 检索/RAG/知识 |  |
| 2024-08-02 | [Agentic LLM Workflows for Generating Patient-Friendly Medical Reports](http://arxiv.org/abs/2408.01112v2) | 报告/文书生成 | 12 pages, 7 figures |
| 2024-07-18 | [CoD, Towards an Interpretable Medical Agent using Chain of Diagnosis](http://arxiv.org/abs/2407.13301v2) | 诊断/鉴别诊断 |  |
| 2024-07-02 | [MMedAgent: Learning to Use Medical Tools with Multi-modal Agent](http://arxiv.org/abs/2407.02483v2) | 综述/观点 | EMNLP 2024 |
| 2024-06-29 | [BioKGBench: A Knowledge Graph Checking Benchmark of AI Agent for Biomedical Science](http://arxiv.org/abs/2407.00466v1) | 评测基准/环境 |  |
| 2024-06-26 | [Mental Modeling of Reinforcement Learning Agents by Language Models](http://arxiv.org/abs/2406.18505v1) | 训练方法(RL/微调) | https://lukaswill.github.io/ |
| 2024-06-19 | [ClinicalLab: Aligning Agents for Multi-Departmental Clinical Diagnostics in the Real World](http://arxiv.org/abs/2406.13890v2) | 诊断/鉴别诊断 |  |
| 2024-06-08 | [Artificial social influence via human-embodied AI agent interaction in immersive virtual reality (VR): Effects of similarity-matching during health conversations](http://arxiv.org/abs/2406.05486v2) | 问诊/医患对话 | 11 pages, 4 figures, manuscript submitted to a journal |
| 2024-05-19 | [Inquire, Interact, and Integrate: A Proactive Agent Collaborative Framework for Zero-Shot Multimodal Medical Reasoning](http://arxiv.org/abs/2405.11640v1) | 问答/推理 |  |
| 2024-05-13 | [AgentClinic: a multimodal agent benchmark to evaluate AI in simulated clinical environments](http://arxiv.org/abs/2405.07960v5) | 评测基准/环境 |  |
| 2024-05-05 | [Agent Hospital: A Simulacrum of Hospital with Evolvable Medical Agents](http://arxiv.org/abs/2405.02957v3) | 模拟病人/医院 |  |
| 2024-04-23 | [IryoNLP at MEDIQA-CORR 2024: Tackling the Medical Error Detection & Correction Task On the Shoulders of Medical Agents](http://arxiv.org/abs/2404.15488v1) | 报告/文书生成 |  |
| 2024-03-19 | [LLMs-based Few-Shot Disease Predictions using EHR: A Novel Approach Combining Predictive Agent Reasoning and Critical Agent Instruction](http://arxiv.org/abs/2403.15464v1) | EHR/结构化数据 | AMIA ... Annual Symposium proceedings. AMIA Symposium |
| 2024-03-10 | [ArgMed-Agents: Explainable Clinical Decision Reasoning with LLM Disscusion via Argumentation Schemes](http://arxiv.org/abs/2403.06294v3) | 治疗/决策支持 |  |
| 2024-02-20 | [AgentMD: Empowering Language Agents for Risk Prediction with Large-Scale Clinical Tool Learning](http://arxiv.org/abs/2402.13225v1) | 评测基准/环境 | ArXiv |
| 2024-02-15 | [AI Hospital: Benchmarking Large Language Models in a Multi-agent Medical Interaction Simulator](http://arxiv.org/abs/2402.09742v4) | 评测基准/环境 | https://github.com/LibertFan/AI_Hospital |
| 2024-01-29 | [Beyond Direct Diagnosis: LLM-based Multi-Specialist Agent Consultation for Automatic Diagnosis](http://arxiv.org/abs/2401.16107v1) | 诊断/鉴别诊断 |  |
| 2024-01-26 | [Enhancing Diagnostic Accuracy through Multi-Agent Conversations: Using Large Language Models to Mitigate Cognitive Bias](http://arxiv.org/abs/2401.14589v2) | 安全/幻觉/攻击 | 21 pages, 3 figures |
| 2024-01-05 | [Natural Language Programming in Medicine: Administering Evidence Based Clinical Workflows with Autonomous Agents Powered by Generative Large Language Models](http://arxiv.org/abs/2401.02851v2) | 检索/RAG/知识 | Figures: 5, Tables: 3 |
| 2024 | [Mitigating Cognitive Biases in Clinical Decision-Making Through Multi-Agent Conversations Using Large Language Models: Simulation Study.](https://pubmed.ncbi.nlm.nih.gov/39561363/) | 模拟病人/医院 | Journal of medical Internet research |
| 2024 | [Ontology extension by online clustering with large language model agents.](https://pubmed.ncbi.nlm.nih.gov/39435030/) | 其他 | Frontiers in big data |
| 2024 | [Voice-Enabled Response Analysis Agent (VERAA): Leveraging Large Language Models to Map Voice Responses in SDoH Survey.](https://pubmed.ncbi.nlm.nih.gov/38827075/) | 综述/观点 | AMIA Joint Summits on Translational Science proceedings. AMI |
| 2024 | [Evaluating large language models as agents in the clinic.](https://pubmed.ncbi.nlm.nih.gov/38570554/) | 评测基准/环境 | NPJ digital medicine |

## 医学影像/放射（105）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-30 | [From Given to Gathered Evidence: Agentic Learning for Longitudinal Medical Reasoning](http://arxiv.org/abs/2609.39566v1) | 检索/RAG/知识 |  |
| 2026-09-25 | [CRC-Router: Risk-Constrained Routing for Medical Agentic AI Systems](http://arxiv.org/abs/2609.30714v1) | 训练方法(RL/微调) |  |
| 2026-09-24 | [Teaching an LLM agent to fit XRR curves with X-Ray Calc 3](http://arxiv.org/abs/2609.28926v1) | 报告/文书生成 |  |
| 2026-09-20 | [MAC-RRG: Iterative Multi-Agent Collaboration for X-ray Radiology Report Generation](http://arxiv.org/abs/2609.26124v1) | 报告/文书生成 |  |
| 2026-08-31 | [Evidence, Logic, and Compliance: Multi-Agent Structured Graph Reasoning with Expert Arbitration for Medical Referral](http://arxiv.org/abs/2608.30938v1) | 检索/RAG/知识 | 18 pages |
| 2026-08-24 | [Can Coding Agents Build Robust Baselines? A Skill-Based Approach for Automating the Medical Imaging Model-Development Pipeline](http://arxiv.org/abs/2608.23336v1) | 安全/幻觉/攻击 | MICCAI 2026 Workshop AgenticMed |
| 2026-08-21 | [A Modular Agent for Reliable and Auditable Spatial Relation Verification in CT Scans](http://arxiv.org/abs/2608.21140v1) | 评测基准/环境 |  |
| 2026-08-18 | [Multi-Agent AI System for Radiology Report Structuring and Quality Assurance with Independent Radiologist Evaluation](http://arxiv.org/abs/2608.18072v1) | 报告/文书生成 | 14 pages, 2 figures, 4 tables |
| 2026-08-12 | [Auditable agentic AI for evidence-grounded thyroid ultrasound diagnosis and reporting](http://arxiv.org/abs/2608.12590v1) | 诊断/鉴别诊断 | Under review |
| 2026-08-11 | [MIRA: Medical Image Reflection for Agentic Diagnosis](http://arxiv.org/abs/2608.10827v1) | 诊断/鉴别诊断 |  |
| 2026-08-04 | [Agents Catching Agents: Shortcut Cascades and Benchmark Gaming in Clinical Multi-Agent Systems](http://arxiv.org/abs/2608.03744v2) | 评测基准/环境 |  |
| 2026-07-30 | [CyberNeuro: A Privacy-Preserving Agentic Workbench for Cohort-Scale Neuroimage and Clinical Data Analysis](http://arxiv.org/abs/2607.28841v1) | 安全/幻觉/攻击 | 25 pages, 4 figures |
| 2026-07-24 | [Agentic Autoresearch for CT Reconstruction](http://arxiv.org/abs/2607.22824v1) | 检索/RAG/知识 | 16 pages |
| 2026-07-24 | [RadHarmony: Radiological Data Handling in the Era of Agentic AI](http://arxiv.org/abs/2607.27235v1) | 训练方法(RL/微调) |  |
| 2026-07-15 | [MonteRET: AI Agent Enhancing Multimodal LLMs with Multi-granularity Knowledge Retrieval for Chest CT Report Generation](http://arxiv.org/abs/2607.14264v1) | 报告/文书生成 |  |
| 2026-07-13 | [The Path to Self-Evolving Clinical Systems: Scaling Medical Agents from Assistance to Autonomy](http://arxiv.org/abs/2607.11175v2) | 训练方法(RL/微调) | Project page: https://github.com/zhcz328/Awesome-Medical-Age |
| 2026-07-04 | [CogRad: A Cognitively-Inspired Multi-Agent Framework for Radiology Report Generation](http://arxiv.org/abs/2607.03853v1) | 报告/文书生成 |  |
| 2026-06-29 | [TopoAgent: An Agentic Framework for Automated Topology Learning in Medical Imaging](http://arxiv.org/abs/2606.29763v1) | 评测基准/环境 |  |
| 2026-06-11 | [ArogyaSutra: A Multi-Agent Framework for Multimodal Medical Reasoning in Indic Languages](http://arxiv.org/abs/2606.13572v2) | 问答/推理 | Accepted for publication in IJCAI,2026 |
| 2026-06-08 | [A multi-agent system for spine MRI report generation from multi-sequence imaging](http://arxiv.org/abs/2606.08897v1) | 报告/文书生成 |  |
| 2026-06-01 | [AutoMedBench: Towards Medical AutoResearch with Agentic AI Models](http://arxiv.org/abs/2606.01961v2) | 检索/RAG/知识 |  |
| 2026-05-27 | [BCER Agent: Reliable Long-Horizon MRI Workflow Execution via Compilation, Artifact Binding, and Bounded Local Recovery](http://arxiv.org/abs/2605.29163v1) | 评测基准/环境 | Pre-review submitted version of a paper accepted to MICCAI 2 |
| 2026-05-11 | [AgentRx: A Benchmark Study of LLM Agents for Multimodal Clinical Prediction Tasks](http://arxiv.org/abs/2605.10286v1) | 评测基准/环境 | Accepted at the AHLI Conference on Health, Inference, and Le |
| 2026-05-03 | [MedScribe: Clinically Grounded CT Reporting through Agentic Workflows](http://arxiv.org/abs/2605.01779v1) | 报告/文书生成 |  |
| 2026-04-25 | [GAZE: Grounded Agentic Zero-shot Evaluation with Viewer-Level Tools and Literature Retrieval on Rare Brain MRI](http://arxiv.org/abs/2605.00876v1) | 检索/RAG/知识 |  |
| 2026-04-17 | [Agentic Large Language Models for Training-Free Neuro-Radiological Image Analysis](http://arxiv.org/abs/2604.16729v2) | 评测基准/环境 |  |
| 2026-04-17 | [MARCH: Multi-Agent Radiology Clinical Hierarchy for CT Report Generation](http://arxiv.org/abs/2604.16175v1) | 报告/文书生成 | Proceedings of the conference. Association for Computational |
| 2026-04-15 | [Evo-MedAgent: Beyond One-Shot Diagnosis with Agents That Remember, Reflect, and Improve](http://arxiv.org/abs/2604.14475v1) | 诊断/鉴别诊断 |  |
| 2026-04-07 | [DosimeTron: Automating Personalized Monte Carlo Radiation Dosimetry in PET/CT with Agentic AI](http://arxiv.org/abs/2604.06280v1) | 模拟病人/医院 |  |
| 2026-03-25 | [MedOpenClaw and MedFlowBench: Auditing Medical Agents in Full-Study Workflows](http://arxiv.org/abs/2603.24649v2) | 评测基准/环境 | 33 pages |
| 2026-03-14 | [EviAgent: Evidence-Driven Agent for Radiology Report Generation](http://arxiv.org/abs/2603.13956v1) | 报告/文书生成 |  |
| 2026-03-11 | [UltrasoundAgents: Hierarchical Multi-Agent Evidence-Chain Reasoning for Breast Ultrasound Diagnosis](http://arxiv.org/abs/2603.10852v1) | 诊断/鉴别诊断 |  |
| 2026-03-09 | [Meissa: Multi-modal Medical Agentic Intelligence](http://arxiv.org/abs/2603.09018v1) | 评测基准/环境 |  |
| 2026-03-06 | [Agentic retrieval-augmented reasoning reshapes collective reliability under model variability in radiology question answering](http://arxiv.org/abs/2603.06271v1) | 检索/RAG/知识 |  |
| 2026-03-06 | [Shifting Adaptation from Weight Space to Memory Space: A Memory-Augmented Agent for Medical Image Segmentation](http://arxiv.org/abs/2603.05873v1) | 安全/幻觉/攻击 |  |
| 2026-02-28 | [DUCX: Decomposing Unfairness in Tool-Using Chest X-ray Agents](http://arxiv.org/abs/2603.00777v2) | 安全/幻觉/攻击 | Early accepted by MICCAI 2026 |
| 2026-02-28 | [OPGAgent: An Agent for Auditable Dental Panoramic X-ray Interpretation](http://arxiv.org/abs/2603.00462v1) | 评测基准/环境 | 10 pages, 2 figures |
| 2026-02-26 | [CXReasonAgent: Evidence-Grounded Diagnostic Reasoning Agent for Chest X-rays](http://arxiv.org/abs/2602.23276v2) | 诊断/鉴别诊断 |  |
| 2026-02-26 | [Can Agents Distinguish Visually Hard-to-Separate Diseases in a Zero-Shot Setting? A Pilot Study](http://arxiv.org/abs/2602.22959v2) | 评测基准/环境 | Code available at https://github.com/TruhnLab/Contrastive-Ag |
| 2026-02-25 | [Which Tool Response Should I Trust? Tool-Expertise-Aware Chest X-ray Agent with Multimodal Agentic Learning](http://arxiv.org/abs/2602.21517v1) | 安全/幻觉/攻击 | 11 pages |
| 2026-02-17 | [Multi-Modal Multi-Agent Reinforcement Learning for Radiology Report Generation](http://arxiv.org/abs/2603.16876v2) | 训练方法(RL/微调) | 23 pages, 4 figures |
| 2026-02-03 | [MedSAM-Agent: Empowering Interactive Medical Image Segmentation with Multi-turn Agentic Reinforcement Learning](http://arxiv.org/abs/2602.03320v1) | 训练方法(RL/微调) | 23 Pages, 4 Figures |
| 2026-01-23 | [AgentsEval: Clinically Faithful Evaluation of Medical Imaging Reports via Multi-Agent Reasoning](http://arxiv.org/abs/2601.16685v1) | 评测基准/环境 |  |
| 2026-01-13 | [Route, Retrieve, Reflect, Repair: Self-Improving Agentic Framework for Visual Detection and Linguistic Reasoning in Medical Imaging](http://arxiv.org/abs/2601.08192v2) | 训练方法(RL/微调) |  |
| 2026 | [Assessing the accuracy and readability of large language models in answering Turkish-language patient-generated queries on radiological contrast agents.](https://pubmed.ncbi.nlm.nih.gov/42756369/) | 综述/观点 | Digital health |
| 2026 | [Agentic artificial intelligence in radiology workflow: from image interpretation to report quality control.](https://pubmed.ncbi.nlm.nih.gov/42746192/) | 报告/文书生成 | Frontiers in medicine |
| 2026 | [Deep Learning Segmentation of Abdominal Organs Across Ultrasound, MRI, and CT: A Scoping Review of Modality-Specific Approaches and the Emerging Role of Foundation Models and LLM-Based Agents.](https://pubmed.ncbi.nlm.nih.gov/42722950/) | 综述/观点 | Journal of imaging informatics in medicine |
| 2026 | [Swin-Qwen3: a three-stage vision-language framework for automated radiology report generation with multi-agent verification.](https://pubmed.ncbi.nlm.nih.gov/42582763/) | 报告/文书生成 | Frontiers in radiology |
| 2026 | [Interpretable agentic AI system with localized reasoning for radiology.](https://pubmed.ncbi.nlm.nih.gov/42457975/) | 问答/推理 | NPJ digital medicine |
| 2026 | [JADE-Plus: A Multimodal Agentic Retrieval-Augmented Generation Large Language Framework for Diagnostic Support in Jawbone Lesions: Development and Technical Validation Study.](https://pubmed.ncbi.nlm.nih.gov/42440194/) | 诊断/鉴别诊断 | Journal of imaging informatics in medicine |
| 2026 | [Closing the Loop: A Custom Artificial Intelligence Agent to Improve Detection of Radiologist Follow-Up Recommendations.](https://pubmed.ncbi.nlm.nih.gov/42418605/) | 综述/观点 | NEJM catalyst innovations in care delivery |
| 2026 | [End-to-End PET/CT Interpretation and Quantification with an LLM-Orchestrated AI Agent: A Real-World Pilot Study.](https://pubmed.ncbi.nlm.nih.gov/42315314/) | 报告/文书生成 | Journal of nuclear medicine : official publication, Society  |
| 2026 | [From raw audio to structure: an agent-based pipeline that boosts medical LLM performance.](https://pubmed.ncbi.nlm.nih.gov/42259903/) | 评测基准/环境 | NPJ digital medicine |
| 2026 | [Agentic Artificial Intelligence for the Automated Generation of Accurate Summary Podcasts of Radiology Research Papers.](https://pubmed.ncbi.nlm.nih.gov/42252992/) | 检索/RAG/知识 | Korean journal of radiology |
| 2026 | [Glass-box agentic-style workflow for multiclass cine cardiac magnetic resonance imaging classification with a large language model.](https://pubmed.ncbi.nlm.nih.gov/42112697/) | 评测基准/环境 | Diagnostic and interventional radiology (Ankara, Turkey) |
| 2026 | [Autonomous skeletal landmark localization toward agentic C-arm control.](https://pubmed.ncbi.nlm.nih.gov/42008049/) | 训练方法(RL/微调) | International journal of computer assisted radiology and sur |
| 2026 | [From Chatbots to Agentic Workflows: Ensuring Responsible Deployment of Large Language Models in Radiology.](https://pubmed.ncbi.nlm.nih.gov/41867274/) | 问诊/医患对话 | The Indian journal of radiology & imaging |
| 2026 | [Systematic Review: Agentic AI in Neuroradiology: Technical Promise with Limited Clinical Evidence.](https://pubmed.ncbi.nlm.nih.gov/41629669/) | 综述/观点 | Journal of imaging informatics in medicine |
| 2026 | [Agentic AI in Radiology: Evolution from Large Language Models to Future Clinical Integration.](https://pubmed.ncbi.nlm.nih.gov/41532836/) | 综述/观点 | Radiology. Artificial intelligence |
| 2026 | [Agentic systems in radiology: Principles, opportunities, privacy risks, regulation, and sustainability concerns.](https://pubmed.ncbi.nlm.nih.gov/41432042/) | 综述/观点 | Diagnostic and interventional imaging |
| 2026 | [Experience-guided multi-agent interpretable framework for radiology report summarization.](https://pubmed.ncbi.nlm.nih.gov/41046706/) | 报告/文书生成 | Computer methods and programs in biomedicine |
| 2026 | [Large Language Model Agentic Workflows for Automated Opportunistic Screening of Incidental Coronary Artery Calcium on Chest CT Reports.](https://pubmed.ncbi.nlm.nih.gov/40751498/) | 报告/文书生成 | Canadian Association of Radiologists journal = Journal l'Ass |
| 2025-12-19 | [ReX-MLE: The Autonomous Agent Benchmark for Medical Imaging Challenges](http://arxiv.org/abs/2512.17838v1) | 评测基准/环境 | https://github.com/rajpurkarlab/ReX-MLE |
| 2025-12-02 | [Simple Agents Outperform Experts in Biomedical Imaging Workflow Optimization](http://arxiv.org/abs/2512.06006v1) | 综述/观点 |  |
| 2025-12-02 | [Radiologist Copilot: An Agentic Framework Orchestrating Specialized Tools for Reliable Radiology Reporting](http://arxiv.org/abs/2512.02814v2) | 报告/文书生成 |  |
| 2025-11-19 | [IMACT-CXR: An Interactive Multi-Agent Conversational Tutoring System for Chest X-Ray Interpretation](http://arxiv.org/abs/2511.15825v2) | 问诊/医患对话 | Accepted at IEEE ISBI 2026. This version corresponds to the  |
| 2025-11-11 | [Auto-US: An Ultrasound Video Diagnosis Agent Using Video Classification Framework and LLMs](http://arxiv.org/abs/2511.07748v1) | 诊断/鉴别诊断 | Under Review |
| 2025-10-19 | [ReclAIm: A Multi-Agent Framework for Monitoring and Correcting Performance Decline in Medical Imaging AI](http://arxiv.org/abs/2510.17004v2) | 多智能体协作 | Radiology. Artificial intelligence |
| 2025-10-10 | [Agentic Systems in Radiology: Design, Applications, Evaluation, and Challenges](http://arxiv.org/abs/2510.09404v2) | 综述/观点 |  |
| 2025-10-06 | [Bridging Clinical Narratives and ACR Appropriateness Guidelines: A Multi-Agent RAG System for Medical Imaging Decisions](http://arxiv.org/abs/2510.04969v1) | 检索/RAG/知识 |  |
| 2025-09-28 | [FedAgentBench: Towards Automating Real-world Federated Medical Image Analysis with Server-Client LLM Agents](http://arxiv.org/abs/2509.23803v1) | 评测基准/环境 |  |
| 2025-09-24 | [RadAgents: Multimodal Agentic Reasoning for Chest X-ray Interpretation with Radiologist-like Workflows](http://arxiv.org/abs/2509.20490v4) | 问答/推理 | MIDL 2026 |
| 2025-09-24 | [A co-evolving agentic AI system for medical imaging analysis](http://arxiv.org/abs/2509.20279v1) | 安全/幻觉/攻击 |  |
| 2025-09-24 | [Scan-do Attitude: Towards Autonomous CT Protocol Management using a Large Language Model Agent](http://arxiv.org/abs/2509.20270v1) | 治疗/决策支持 |  |
| 2025-09-22 | [Medical AI Consensus: A Multi-Agent Framework for Radiology Report Generation and Evaluation](http://arxiv.org/abs/2509.17353v1) | 报告/文书生成 | NeurIPS2025 Workshop: Evaluating the Evolving LLM Lifecycle: |
| 2025-08-26 | [AT-CXR: Uncertainty-Aware Agentic Triage for Chest X-rays](http://arxiv.org/abs/2508.19322v1) | 检索/RAG/知识 |  |
| 2025-08-14 | [PASS: Probabilistic Agentic Supernet Sampling for Interpretable and Adaptive Chest X-Ray Reasoning](http://arxiv.org/abs/2508.10501v4) | 问答/推理 |  |
| 2025-08-04 | [A Multi-Agent System for Complex Reasoning in Radiology Visual Question Answering](http://arxiv.org/abs/2508.02841v1) | 问答/推理 |  |
| 2025-08-04 | [Clinically Grounded Agent-based Report Evaluation: An Interpretable Metric for Radiology Report Generation](http://arxiv.org/abs/2508.02808v1) | 报告/文书生成 |  |
| 2025-07-22 | [AURA: A Multi-Modal Medical Agent for Understanding, Reasoning & Annotation](http://arxiv.org/abs/2507.16940v1) | 问答/推理 | 9 pages, 3 figures, International Conference on Medical Imag |
| 2025-07-20 | [InsightX Agent: An LMM-based Agentic Framework with Integrated Tools for Reliable X-ray NDT Analysis](http://arxiv.org/abs/2507.14899v3) | 综述/观点 |  |
| 2025-06-18 | [MAARTA:Multi-Agentic Adaptive Radiology Teaching Assistant](http://arxiv.org/abs/2506.17320v1) | 多智能体协作 | Accepted to MICCAI 2025 (Main Conference) |
| 2025-06-17 | [RadFabric: Agentic AI System with Reasoning Capability for Radiology](http://arxiv.org/abs/2506.14142v1) | 问答/推理 | 4 figures, 2 tables |
| 2025-05-27 | [FUAS-Agents: Autonomous Multi-Modal LLM Agents for Treatment Planning in Focused Ultrasound Ablation Surgery](http://arxiv.org/abs/2505.21418v3) | 治疗/决策支持 | 35 pages |
| 2025-05-24 | [MRGAgents: A Multi-Agent Framework for Improved Medical Report Generation with Med-LVLMs](http://arxiv.org/abs/2505.18530v1) | 报告/文书生成 | 10pages |
| 2025-05-22 | [CT-Agent: A Multimodal-LLM Agent for 3D CT Radiology Question Answering](http://arxiv.org/abs/2505.16229v1) | 问答/推理 |  |
| 2025-05-14 | [A Multimodal Multi-Agent Framework for Radiology Report Generation](http://arxiv.org/abs/2505.09787v1) | 报告/文书生成 |  |
| 2025-05-12 | [Towards user-centered interactive medical image segmentation in VR with an assistive AI agent](http://arxiv.org/abs/2505.07214v3) | 问诊/医患对话 |  |
| 2025-03-28 | [Self-Evolving Multi-Agent Simulations for Realistic Clinical Interactions](http://arxiv.org/abs/2503.22678v2) | 模拟病人/医院 | 14 page, 4 figures, 61 references, presented in MICCAI (Oral |
| 2025-03-07 | [GEMA-Score: Granular Explainable Multi-Agent Scoring Framework for Radiology Report Evaluation](http://arxiv.org/abs/2503.05347v2) | 报告/文书生成 |  |
| 2025-02-27 | [M^3Builder: A Multi-Agent System for Automated Machine Learning in Medical Imaging](http://arxiv.org/abs/2502.20301v1) | 多智能体协作 | 38 pages, 7 figures |
| 2025-02-14 | [Enhancing Patient Acceptance of Robotic Ultrasound through Conversational Virtual Agent and Immersive Visualizations](http://arxiv.org/abs/2502.10088v1) | 问诊/医患对话 | IEEE transactions on visualization and computer graphics |
| 2025-02-04 | [MedRAX: Medical Reasoning Agent for Chest X-ray](http://arxiv.org/abs/2502.02673v2) | 问答/推理 | 16 pages, 4 figures, 5 Tables |
| 2025-02-02 | [Agent-Based Uncertainty Awareness Improves Automated Radiology Report Labeling with an Open-Source Large Language Model](http://arxiv.org/abs/2502.01691v1) | 报告/文书生成 |  |
| 2025 | [Agentic AI and Large Language Models in Radiology: Opportunities and Hallucination Challenges.](https://pubmed.ncbi.nlm.nih.gov/41463600/) | 综述/观点 | Bioengineering (Basel, Switzerland) |
| 2025 | [Uncover This Tech Term: Agentic Artificial Intelligence in Radiology.](https://pubmed.ncbi.nlm.nih.gov/40873379/) | 其他 | Korean journal of radiology |
| 2025 | [A Proactive Agent Collaborative Framework for Zero-Shot Multimodal Medical Reasoning.](https://pubmed.ncbi.nlm.nih.gov/40852092/) | 问答/推理 | Advanced intelligent systems (Weinheim an der Bergstrasse, G |
| 2025 | [Evaluating Large Language Models for imaging modality selection: Potential to reduce unnecessary contrast agent use and radiation exposure.](https://pubmed.ncbi.nlm.nih.gov/40752449/) | 评测基准/环境 | Clinical imaging |
| 2024-12-20 | [Towards Interpretable Radiology Report Generation via Concept Bottlenecks using a Multi-Agentic RAG](http://arxiv.org/abs/2412.16086v2) | 报告/文书生成 | Accepted in the 47th European Conference for Information Ret |
| 2024-12-12 | [How Well Can Modern LLMs Act as Agent Cores in Radiology Environments?](http://arxiv.org/abs/2412.09529v4) | 评测基准/环境 |  |
| 2024-12-06 | [Enhancing LLMs for Impression Generation in Radiology Reports through a Multi-Agent System](http://arxiv.org/abs/2412.06828v1) | 报告/文书生成 |  |
| 2024-10-10 | [VoxelPrompt: A Vision Agent for End-to-End Medical Image Analysis](http://arxiv.org/abs/2410.08397v2) | 训练方法(RL/微调) | 22 pages, vision-language agent, medical image analysis, neu |
| 2024-09-10 | [MAGDA: Multi-agent guideline-driven diagnostic assistance](http://arxiv.org/abs/2409.06351v1) | 诊断/鉴别诊断 |  |
| 2024-07-11 | [CXR-Agent: Vision-language models for chest X-ray interpretation with uncertainty aware radiology reporting](http://arxiv.org/abs/2407.08811v1) | 报告/文书生成 | Supervised by Professor Ben Glocker |
| 2024 | [Intelligent Agent Planning for Optimizing Parallel MRI Reconstruction via A Large Language Model.](https://pubmed.ncbi.nlm.nih.gov/40031503/) | 检索/RAG/知识 | Annual International Conference of the IEEE Engineering in M |

## 精神心理（71）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-08-27 | [BALMS: Benchmarking Agentic LLMs for Longitudinal Mental Health Sensing](http://arxiv.org/abs/2608.27219v1) | 评测基准/环境 | Accepted to EMNLP 2026 Main Conference |
| 2026-08-22 | [HiMA-MDD: A Hierarchical Multi-Agent Harness for Interpretable Multimodal Depression Detection in Clinical Interviews](http://arxiv.org/abs/2608.21868v1) | 问诊/医患对话 |  |
| 2026-08-14 | [Designing Mobile and Wearable Sensor-Fused Conversational Agents for Health and Wellbeing](http://arxiv.org/abs/2608.14273v1) | 问诊/医患对话 | 6 pages, 3 figures. Accepted as a Tutorial at the 28th Inter |
| 2026-08-07 | [Agentic Artificial Intelligence for Reproducible Human-in-the-Loop Environmental Health Research](http://arxiv.org/abs/2608.06771v1) | 检索/RAG/知识 | 41 pages, 3 figures |
| 2026-07-18 | [DS@GT ARC at eRisk 2026: Hybrid Multi-Agent LLM System with Structured Algorithmic Guidance for Conversational Depression Screening](http://arxiv.org/abs/2607.16712v1) | 问诊/医患对话 | Conference and Labs of the Evaluation Forum (CLEF), 19 pages |
| 2026-06-29 | [Training Therapeutic Judges and Multi-Agent Systems for Human-Aligned Mental Health Support](http://arxiv.org/abs/2606.30887v1) | 多智能体协作 |  |
| 2026-06-24 | [Knowledge-augmented Agentic AI for Mental Health Medication Information Seeking](http://arxiv.org/abs/2606.26205v1) | 问诊/医患对话 |  |
| 2026-06-19 | [A Multi-Agent Audit Framework for High-Stakes Reasoning: Evaluation and Interpretability in Clinical Mental Health Screening](http://arxiv.org/abs/2606.21123v1) | 问答/推理 |  |
| 2026-05-13 | [An Agentic LLM-Based Framework for Population-Scale Mental Health Screening](http://arxiv.org/abs/2605.13046v1) | 综述/观点 | 8 pages, conference paper presented at IEEE BigData 2025, Ma |
| 2026-05-11 | [CPEMH: An Agentic Framework for Prompt-Driven Behavior Evaluation and Assurance in Foundation-Model Systems for Mental Health Screening](http://arxiv.org/abs/2605.11341v1) | 安全/幻觉/攻击 | 4 pages, 2 figures. Accepted at the AGENT 2026 Workshop (ICS |
| 2026-04-22 | [Can Virtual Agents Care? Designing an Empathetic and Personalized LLM-Driven Conversational Agent](http://arxiv.org/abs/2604.20948v1) | 问诊/医患对话 | Accepted manuscript version to be presented at the SCI-2026 |
| 2026-04-18 | [StoryMI: Steerable Multi-Agent Therapeutic Dialogue Generation](http://arxiv.org/abs/2605.27393v1) | 问诊/医患对话 | ACL2026 |
| 2026-04-09 | [From Synthesis to Clinical Assistance: A Strategy-Aware Agent Framework for Autism Intervention based on Real Clinical Dataset](http://arxiv.org/abs/2605.02916v1) | 综述/观点 | Accepted to 2026 ACL Main Conference |
| 2026-04-08 | [COSMIC: Emotionally Intelligent Agents to Support Mental and Emotional Well-being in Extreme Isolation: Lessons from Analog Astronaut Training Missions](http://arxiv.org/abs/2604.07589v1) | 评测基准/环境 | 7 pages, 2 figures, 3 tables |
| 2026-04-08 | [CCD-CBT: Multi-Agent Therapeutic Interaction for CBT Guided by Cognitive Conceptualization Diagram](http://arxiv.org/abs/2604.06551v1) | 多智能体协作 |  |
| 2026-03-31 | [Train the Trainers -- An Agentic AI Framework for Peer-Based Mental Health Support in Battlefield Environments](http://arxiv.org/abs/2605.16269v1) | 模拟病人/医院 |  |
| 2026-03-28 | [SocialWise: LLM-Agentic Conversation Therapy for Individuals with Autism Spectrum Disorder to Enhance Communication Skills](http://arxiv.org/abs/2604.15347v1) | 问诊/医患对话 |  |
| 2026-03-17 | [Differential Harm Propensity in Personalized LLM Agents: The Curious Case of Mental Health Disclosure](http://arxiv.org/abs/2603.16734v1) | 诊断/鉴别诊断 |  |
| 2026-03-08 | [YAQIN: Culturally Sensitive, Agentic AI for Mental Healthcare Support Among Muslim Women in the UK](http://arxiv.org/abs/2603.07709v1) | 评测基准/环境 |  |
| 2026-02-28 | [Structure Matters: Evaluating Multi-Agents Orchestration in Generative Therapeutic Chatbots](http://arxiv.org/abs/2603.00774v2) | 评测基准/环境 |  |
| 2026-02-10 | [LingxiDiagBench: A Multi-Agent Framework for Benchmarking LLMs in Chinese Psychiatric Consultation and Diagnosis](http://arxiv.org/abs/2602.09379v3) | 评测基准/环境 |  |
| 2026-02-09 | [SynthAgent: A Multi-Agent LLM Framework for Realistic Patient Simulation -- A Case Study in Obesity with Mental Health Comorbidities](http://arxiv.org/abs/2602.08254v1) | 模拟病人/医院 | Presented in AAAI 2026 Singapore at the workshop of Health I |
| 2026-01-25 | [EFT-CoT: A Multi-Agent Chain-of-Thought Framework for Emotion-Focused Therapy](http://arxiv.org/abs/2601.17842v2) | 多智能体协作 |  |
| 2026-01-20 | [Towards Efficient and Robust Linguistic Emotion Diagnosis for Mental Health via Multi-Agent Instruction Refinement](http://arxiv.org/abs/2601.13481v1) | 安全/幻觉/攻击 |  |
| 2026-01-19 | [PAIR-SAFE: A Paired-Agent Approach for Runtime Auditing and Refining AI-Mediated Mental Health Support](http://arxiv.org/abs/2601.12754v1) | 模拟病人/医院 |  |
| 2026-01-14 | [Honesty-Aware Multi-Agent Framework for High-Fidelity Synthetic Data Generation in Digital Psychiatric Intake Doctor-Patient Interactions](http://arxiv.org/abs/2601.09216v1) | 问诊/医患对话 |  |
| 2026 | [Multiagent Large Language Model Framework for Psychotherapy Fidelity Assessment in Motivational Interviewing and Cognitive Behavioral Therapy Training: Cross-Sectional, Simulation-Based Evaluation Study.](https://pubmed.ncbi.nlm.nih.gov/42611045/) | 模拟病人/医院 | JMIR medical education |
| 2026 | [Human-like conversational agents as social partners: a scoping review of socioaffective mechanisms, well-being outcomes, risks and governance in the post-Turing era.](https://pubmed.ncbi.nlm.nih.gov/42528981/) | 综述/观点 | Frontiers in artificial intelligence |
| 2026 | [Enhancing Psychiatry Training Using an Agentic AI Simulated Consultation Tool: Prospective Cohort Study.](https://pubmed.ncbi.nlm.nih.gov/42479623/) | 模拟病人/医院 | JMIR medical education |
| 2026 | [AI Agents Are Coming: 5-Stage Taxonomy of Language-Based AI Systems for Psychiatry, Psychotherapy, and Counseling.](https://pubmed.ncbi.nlm.nih.gov/42440357/) | 评测基准/环境 | JMIR mental health |
| 2026 | [AI counseling agent for motivational interviewing: Conversational processes associated with change talk in emergency department patients.](https://pubmed.ncbi.nlm.nih.gov/42285418/) | 问诊/医患对话 | Journal of substance use and addiction treatment |
| 2026 | [Barriers and Facilitators to the Use of Large Language Model-Based Conversational Agents in Mental Healthcare: A Systematic Review.](https://pubmed.ncbi.nlm.nih.gov/42194358/) | 综述/观点 | Healthcare (Basel, Switzerland) |
| 2026 | [Intelligent virtual agents in psychotherapy: a safety evaluation across high-risk mental health scenarios.](https://pubmed.ncbi.nlm.nih.gov/42034907/) | 安全/幻觉/攻击 | Scientific reports |
| 2026 | [Development, system design, safety, and performance metrics of a conversational agent for reducing depressive and anxious symptoms based on a large language model: The MHAI study.](https://pubmed.ncbi.nlm.nih.gov/41849345/) | 安全/幻觉/攻击 | PloS one |
| 2026 | [Large Language Model-Based Chatbots and Agentic AI for Mental Health Counseling: Systematic Review of Methodologies, Evaluation Frameworks, and Ethical Safeguards.](https://pubmed.ncbi.nlm.nih.gov/41592221/) | 综述/观点 | JMIR AI |
| 2026 | [Autonomous conversational agents for loneliness, social isolation, depression, and anxiety in older people without cognitive impairment: Systematic review and meta-analysis.](https://pubmed.ncbi.nlm.nih.gov/41556104/) | 综述/观点 | Psychological medicine |
| 2026 | [ClinPreAI: An Agentic AI System for Early Postpartum Depression Risk Prediction from Multimodal EHR Data.](https://pubmed.ncbi.nlm.nih.gov/41332803/) | EHR/结构化数据 | medRxiv : the preprint server for health sciences |
| 2025-12-31 | [MAMA-Memeia! Multi-Aspect Multi-Agent Collaboration for Depressive Symptoms Identification in Memes](http://arxiv.org/abs/2512.25015v1) | 多智能体协作 | Accepted by AAAI 2026 |
| 2025-11-25 | [Adaptive LLM Agents: Toward Personalized Empathetic Care](http://arxiv.org/abs/2511.20080v1) | 问诊/医患对话 | Accepted at workshop Future Wellbeing: Using Design Fiction  |
| 2025-11-18 | [Tell Me: An LLM-powered Mental Well-being Assistant with RAG, Synthetic Dialogue Generation, and Agentic Planning](http://arxiv.org/abs/2511.14445v2) | 问诊/医患对话 | 8 pages, 2 figures, 1 Table. Submitted to the Computation an |
| 2025-10-17 | [MoPHES:Leveraging on-device LLMs as Agent for Mobile Psychological Health Evaluation and Support](http://arxiv.org/abs/2510.16085v1) | 评测基准/环境 | This work has been submitted to the IEEE for possible public |
| 2025-09-04 | [MAGneT: Coordinated Multi-Agent Generation of Synthetic Multi-Turn Mental Health Counseling Sessions](http://arxiv.org/abs/2509.04183v3) | 多智能体协作 | 50 pages, 39 figures, 20 Tables |
| 2025-08-15 | [Trustworthy AI Psychotherapy: Multi-Agent LLM Workflow for Counseling and Explainable Mental Disorder Diagnosis](http://arxiv.org/abs/2508.11398v2) | 安全/幻觉/攻击 | This paper has been accepted by CIKM 2025 as a full paper |
| 2025-07-17 | [LLM Agent-Based Simulation of Student Activities and Mental Health Using Smartphone Sensing Data](http://arxiv.org/abs/2508.02679v2) | 模拟病人/医院 |  |
| 2025-07-15 | [DS@GT at eRisk 2025: From prompts to predictions, benchmarking early depression detection with conversational agent based assessments and temporal attention models](http://arxiv.org/abs/2507.10958v1) | 评测基准/环境 |  |
| 2025-07-11 | [An Offline Mobile Conversational Agent for Mental Health Support: Learning from Emotional Dialogues and Psychological Texts with Student-Centered Evaluation](http://arxiv.org/abs/2507.10580v2) | 问诊/医患对话 |  |
| 2025-06-30 | [Harnessing AI Agents to Advance Research on Refugee Child Mental Health](http://arxiv.org/abs/2506.23992v1) | 检索/RAG/知识 | 14 page , 2 image , 2 tables , accepted under 5th Internatio |
| 2025-06-04 | [MoodAngels: A Retrieval-augmented Multi-agent Framework for Psychiatry Diagnosis](http://arxiv.org/abs/2506.03750v2) | 诊断/鉴别诊断 | 46 pages, 11 figures |
| 2025-06-04 | [VChatter: Exploring Generative Conversational Agents for Simulating Exposure Therapy to Reduce Social Anxiety](http://arxiv.org/abs/2506.03520v1) | 模拟病人/医院 |  |
| 2025-04-25 | [MAGI: Multi-Agent Guided Interview for Psychiatric Assessment](http://arxiv.org/abs/2504.18260v1) | 问诊/医患对话 | In progress |
| 2025-03-21 | [Deterministic AI Agent Personality Expression through Standard Psychological Diagnostics](http://arxiv.org/abs/2503.17085v1) | 诊断/鉴别诊断 | 25 pages, 8 figures, 4 tables; appeared in ADI (March 2025) |
| 2025-02-28 | [WiseMind: a knowledge-guided multi-agent framework for accurate and empathetic psychiatric diagnosis](http://arxiv.org/abs/2502.20689v4) | 诊断/鉴别诊断 | NPJ digital medicine |
| 2025-02-09 | [HamRaz: A Culture-Based Persian Conversation Dataset for Person-Centered Therapy Using LLM Agents](http://arxiv.org/abs/2502.05982v2) | 问诊/医患对话 |  |
| 2025-01-27 | [MADP: Multi-Agent Deductive Planning for Enhanced Cognitive-Behavioral Mental Health Question Answer](http://arxiv.org/abs/2501.15826v1) | 多智能体协作 |  |
| 2025-01-16 | [AutoCBT: An Autonomous Multi-agent Framework for Cognitive Behavioral Therapy in Psychological Counseling](http://arxiv.org/abs/2501.09426v1) | 多智能体协作 |  |
| 2025-01-05 | [A Study about Distribution and Acceptance of Conversational Agents for Mental Health in Germany: Keep the Human in the Loop?](http://arxiv.org/abs/2502.00005v1) | 问诊/医患对话 | Master's thesis |
| 2025-01-03 | [PSYCHE: A Multi-faceted Patient Simulation Framework for Evaluation of Psychiatric Assessment Conversational Agents](http://arxiv.org/abs/2501.01594v1) | 评测基准/环境 | The first two authors contributed equally |
| 2025 | [A Rule-Based Conversational Agent for Mental Health and Well-Being in Young People: Formative Case Series During the Rise of Generative AI.](https://pubmed.ncbi.nlm.nih.gov/41325605/) | 问诊/医患对话 | JMIR formative research |
| 2025 | [Exploring Body Image Awareness With a Large Language Model-Based Conversational Agent: Qualitative Study With Young Adults.](https://pubmed.ncbi.nlm.nih.gov/41248495/) | 问诊/医患对话 | Journal of medical Internet research |
| 2025 | [Effect of an AI agent trained on a large language model (LLM) as an intervention for depression and anxiety symptoms in young adults: A 28-day randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/40910958/) | 训练方法(RL/微调) | Applied psychology. Health and well-being |
| 2025 | [An intelligent agent for sentence completion test: creation and application in depression assessment.](https://pubmed.ncbi.nlm.nih.gov/40873505/) | 综述/观点 | Frontiers in psychology |
| 2025 | [Current Landscape and Future Directions for Mental Health Conversational Agents for Youth: Scoping Review.](https://pubmed.ncbi.nlm.nih.gov/40053735/) | 综述/观点 | JMIR medical informatics |
| 2025 | [Prompt Engineering an Informational Chatbot for Education on Mental Health Using a Multiagent Approach for Enhanced Compliance With Prompt Instructions: Algorithm Development and Validation.](https://pubmed.ncbi.nlm.nih.gov/39992720/) | 问诊/医患对话 | JMIR AI |
| 2025 | [Modelling the impact of environmental and social determinants on mental health using generative agents.](https://pubmed.ncbi.nlm.nih.gov/39820048/) | 综述/观点 | NPJ digital medicine |
| 2024-12-19 | [PsyDraw: A Multi-Agent Multimodal System for Mental Health Screening in Left-Behind Children](http://arxiv.org/abs/2412.14769v1) | 多智能体协作 | preprint |
| 2024-11-27 | [A Multi-Agent Dual Dialogue System to Support Mental Health Care Providers](http://arxiv.org/abs/2411.18429v2) | 问诊/医患对话 | Update: Render figures properly and update title |
| 2024-08-22 | [MDD-5k: A New Diagnostic Conversation Dataset for Mental Disorders Synthesized via Neuro-Symbolic LLM Agents](http://arxiv.org/abs/2408.12142v2) | 诊断/鉴别诊断 | Accepted by the 39th Annual AAAI Conference on Artificial In |
| 2024-07-03 | [MentalAgora: A Gateway to Advanced Personalized Care in Mental Health through Multi-Agent Debating and Attribute Control](http://arxiv.org/abs/2407.02736v1) | 多智能体协作 |  |
| 2024-06-22 | [Revolutionizing Mental Health Support: An Innovative Affective Mobile Framework for Dynamic, Proactive, and Context-Adaptive Conversational Agents](http://arxiv.org/abs/2406.15942v1) | 问诊/医患对话 | Accepted to Ubicomp '23, GenAI4PC Symposium |
| 2024 | [Neural Conversational Agent for Weight Loss Counseling: Protocol for an Implementation and Feasibility Study.](https://pubmed.ncbi.nlm.nih.gov/39303273/) | 问诊/医患对话 | JMIR research protocols |
| 2023 | [Understanding the Benefits and Challenges of Using Large Language Model-based Conversational Agents for Mental Well-being Support.](https://pubmed.ncbi.nlm.nih.gov/38222348/) | 综述/观点 | AMIA ... Annual Symposium proceedings. AMIA Symposium |

## 肿瘤（58）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-25 | [MammoClaw: Towards Skill-Evolving Agent Harness for Breast Cancer Mammography Analysis](http://arxiv.org/abs/2609.31789v1) | 训练方法(RL/微调) | Accepted at Deep Breast Imaging Workshop, MICCAI 2026 |
| 2026-08-24 | [LUCAID: Agentic Multimodal AI for Lung Cancer Precision Pathology](http://arxiv.org/abs/2608.23803v2) | 综述/观点 |  |
| 2026-08-10 | [An Agentic Generative Large Language Model for Treatment Planning of Colorectal Cancer](http://arxiv.org/abs/2608.09142v1) | 治疗/决策支持 |  |
| 2026-08-04 | [Learning Clinical-Trial Strategy: Offline Policy Training for Decision Agents](http://arxiv.org/abs/2608.03606v1) | 训练方法(RL/微调) | Accepted for a spotlight at the ICML 2026 Workshop on Genera |
| 2026-07-15 | [Evaluating Frontier AI Agents as Autonomous Clinical Security Auditors](http://arxiv.org/abs/2607.13411v1) | 评测基准/环境 | 29 pages, 2 figures, 7 tables |
| 2026-07-13 | [Agentic systems for breast cancer treatment recommendations](http://arxiv.org/abs/2607.12051v1) | 治疗/决策支持 | Under peer review. Source code available at: https://github. |
| 2026-07-11 | [Information-seeking failures of large language models in agentic clinical reasoning](http://arxiv.org/abs/2607.10275v1) | 问答/推理 | 66 pages, 9 figures; includes supplementary material |
| 2026-06-01 | [Traj-Evolve: A Self-Evolving Multi-Agent System for Patient Trajectory Modeling in Lung Cancer Early Detection](http://arxiv.org/abs/2606.02812v1) | 训练方法(RL/微调) |  |
| 2026-05-30 | [A Machine-to-Machine Knowledge-Guided LLM Agent for Generalizable Radiotherapy Treatment Planning](http://arxiv.org/abs/2606.00922v1) | 治疗/决策支持 | 10 pages, 6 figures |
| 2026-05-28 | [Counterfactual Evaluation Reveals Hidden Capability Profiles in Clinical LLMs and Agents](http://arxiv.org/abs/2605.30590v1) | 评测基准/环境 | Accepted to RLEval @ ACM CAIS 2026 (Workshop on Methods and  |
| 2026-05-25 | [PathWISE: Multi-Agent Cancer Pathway Triaging Ontology Learning from Clinical Flowcharts](http://arxiv.org/abs/2605.25970v2) | 多智能体协作 | 13 pages, 4 figures |
| 2026-05-17 | [PULSE: Agentic Investigation with Passive Sensing for Proactive Affective Intervention in Cancer Survivorship](http://arxiv.org/abs/2605.17679v2) | 评测基准/环境 |  |
| 2026-05-10 | [DeepTumorVQA: A Hierarchical 3D CT Benchmark for Stage-Wise Evaluation of Medical VLMs and Tool-Augmented Agents](http://arxiv.org/abs/2605.09679v1) | 评测基准/环境 |  |
| 2026-04-26 | [EndoGov: A knowledge-governed multi-agent expert system for endometrial cancer risk stratification](http://arxiv.org/abs/2604.23802v1) | 多智能体协作 |  |
| 2026-04-12 | [TrajOnco: a multi-agent framework for temporal reasoning over longitudinal EHR for multi-cancer early detection](http://arxiv.org/abs/2604.10386v1) | EHR/结构化数据 |  |
| 2026-04-11 | [Empathic and agentic artificial intelligence in nursing: perspectives on a human-centered framework for cancer care navigation in the United States](http://arxiv.org/abs/2606.00010v1) | 综述/观点 | 5 Pages, 1 Figure, 1 Table |
| 2026-03-17 | [Ablation Study of a Fairness Auditing Agentic System for Bias Mitigation in Early-Onset Colorectal Cancer Detection](http://arxiv.org/abs/2603.17179v2) | 安全/幻觉/攻击 |  |
| 2026-03-01 | [Contextual Invertible World Models: A Neuro-Symbolic Agentic Framework for Colorectal Cancer Drug Response](http://arxiv.org/abs/2603.02274v3) | 问答/推理 |  |
| 2026-02-09 | [CoMMa: Contribution-Aware Medical Multi-Agents for Decentralized Oncology Decision Support](http://arxiv.org/abs/2602.09159v2) | 治疗/决策支持 | 9 pages, 5 figures |
| 2026 | [A Modular Multi-Agent Reinforcement Learning Framework Guided by LLMs: Improving Quality and Efficiency of Treatment Planning in Lung Radiotherapy.](https://pubmed.ncbi.nlm.nih.gov/42754176/) | 训练方法(RL/微调) | International journal of radiation oncology, biology, physic |
| 2026 | [AI Agents for Multimodal Oncology Diagnosis: Toward Transparent and Traceable Clinical Decision Support.](https://pubmed.ncbi.nlm.nih.gov/42743545/) | 诊断/鉴别诊断 | JMIR cancer |
| 2026 | [PlanningCopilot: An agentic framework integrating ESAPI modules for autonomous treatment planning in lung radiotherapy.](https://pubmed.ncbi.nlm.nih.gov/42682183/) | 治疗/决策支持 | Medical physics |
| 2026 | [Automating cost-effectiveness models with agentic artificial intelligence: Case study and implications for value assessment.](https://pubmed.ncbi.nlm.nih.gov/42640119/) | 评测基准/环境 | Journal of managed care & specialty pharmacy |
| 2026 | [Reference-Free large language model agents for physician-guided radiotherapy treatment planning.](https://pubmed.ncbi.nlm.nih.gov/42535478/) | 治疗/决策支持 | Medical physics |
| 2026 | [Safety-aware AI for NSCLC trial pre-screening: a comparative proof-of-concept study of rule-based, single-agent, and multi-agent approaches.](https://pubmed.ncbi.nlm.nih.gov/42485959/) | 安全/幻觉/攻击 | International journal of medical informatics |
| 2026 | [Multiturn Large Language Model-Based Conversational Agents for Patients With Cancer and Caregivers: Scoping Review.](https://pubmed.ncbi.nlm.nih.gov/42479903/) | 综述/观点 | JMIR cancer |
| 2026 | [Autonomous radiotherapy planning via agentic orchestration using a multimodal TPS-integrated compound AI platform.](https://pubmed.ncbi.nlm.nih.gov/42466075/) | 治疗/决策支持 | Machine learning. Health |
| 2026 | [Clinical decision support in hematological malignancies using a case-grounded AI agent.](https://pubmed.ncbi.nlm.nih.gov/42380678/) | 治疗/决策支持 | Nature medicine |
| 2026 | [Use of AI agents to assess preoperative frailty in cancer patients.](https://pubmed.ncbi.nlm.nih.gov/42254078/) | EHR/结构化数据 | npj digital surgery |
| 2026 | [Precision oncology: from large language models to multi-agent systems.](https://pubmed.ncbi.nlm.nih.gov/42158433/) | 多智能体协作 | Frontiers in oncology |
| 2026 | [MARTP: a multi-agent simulation framework for automated radiation therapy planning based on LLMs.](https://pubmed.ncbi.nlm.nih.gov/42102858/) | 模拟病人/医院 | Physics in medicine and biology |
| 2026 | [Re: Personalizing Prostate Cancer Education for Patients Using an EHR-Integrated LLM Agent.](https://pubmed.ncbi.nlm.nih.gov/42055905/) | EHR/结构化数据 | European urology |
| 2026 | [Transforming oncology clinical trial matching through neuro-symbolic, multi-agent AI and an oncology-specific knowledge graph: a prospective evaluation in 3804 patients.](https://pubmed.ncbi.nlm.nih.gov/42004487/) | 检索/RAG/知识 | ESMO real world data and digital oncology |
| 2026 | [Development and validation of a multimodal AI-agent system for prognosis analysis of bladder urothelial carcinoma.](https://pubmed.ncbi.nlm.nih.gov/41981218/) | 安全/幻觉/攻击 | NPJ precision oncology |
| 2026 | [Agent-based large language model system for extracting structured data from breast cancer synoptic reports: a dual-validation study.](https://pubmed.ncbi.nlm.nih.gov/41756715/) | 报告/文书生成 | JAMIA open |
| 2026 | [Artificial intelligence agent for delirium screening among patients in oncology and cardiac intensive care units: a proof-of-concept study.](https://pubmed.ncbi.nlm.nih.gov/41629753/) | 评测基准/环境 | European journal of cardiovascular nursing |
| 2026 | [Artificial intelligence agents in cancer research and oncology.](https://pubmed.ncbi.nlm.nih.gov/41526721/) | 检索/RAG/知识 | Nature reviews. Cancer |
| 2026 | [EvoMDT: a self-evolving multi-agent system for structured clinical decision-making in multi-cancer.](https://pubmed.ncbi.nlm.nih.gov/41501128/) | 训练方法(RL/微调) | NPJ digital medicine |
| 2026 | [Tumor Board-Inspired Multiagent Artificial Intelligence System for Interpreting Oncology Guidelines.](https://pubmed.ncbi.nlm.nih.gov/41499718/) | 治疗/决策支持 | JCO clinical cancer informatics |
| 2025-12-22 | [HARMON-E: Hierarchical Agentic Reasoning for Multimodal Oncology Notes to Extract Structured Data](http://arxiv.org/abs/2512.19864v2) | 问答/推理 | 39 Pages, Supplementary Included |
| 2025-12-16 | [Multi-Agent Medical Decision Consensus Matrix System: An Intelligent Collaborative Framework for Oncology MDT Consultations](http://arxiv.org/abs/2512.14321v1) | 问诊/医患对话 | 14 pages, 6 figures |
| 2025-12-09 | [Multi-Agent Intelligence for Multidisciplinary Decision-Making in Gastrointestinal Oncology](http://arxiv.org/abs/2512.08674v2) | 治疗/决策支持 |  |
| 2025-12-05 | [Multimodal Oncology Agent for IDH1 Mutation Prediction in Low-Grade Glioma](http://arxiv.org/abs/2512.05824v1) | 报告/文书生成 | 4 pages, 2 figures |
| 2025-10-12 | [Zero-Shot Large Language Model Agents for Fully Automated Radiotherapy Treatment Planning](http://arxiv.org/abs/2510.11754v1) | 治疗/决策支持 | Accepted for poster presentation at the NeurIPS 2025 Worksho |
| 2025-10-12 | [Traj-CoA: Patient Trajectory Modeling via Chain-of-Agents for Lung Cancer Risk Prediction](http://arxiv.org/abs/2510.10454v2) | 综述/观点 | Accepted by NeurIPS 2025 GenAI4Health Workshop |
| 2025-09-29 | [RadOnc-GPT: An Autonomous LLM Agent for Real-Time Patient Outcomes Labeling at Scale](http://arxiv.org/abs/2509.25540v2) | 治疗/决策支持 |  |
| 2025-08-20 | [Cohort-Aware Agents for Individualized Lung Cancer Risk Prediction Using a Retrieval-Augmented Model Selection Framework](http://arxiv.org/abs/2508.14940v2) | 检索/RAG/知识 | Proceedings of SPIE--the International Society for Optical E |
| 2025-08-03 | [Scaling Clinician-Grade Feature Generation from Clinical Notes with Multi-Agent Language Models](http://arxiv.org/abs/2508.01956v2) | 报告/文书生成 |  |
| 2025-03-21 | [Autonomous Radiotherapy Treatment Planning Using DOLA: A Privacy-Preserving, LLM-Based Optimization Agent](http://arxiv.org/abs/2503.17553v1) | 安全/幻觉/攻击 | 19 pages, 5 figures, preprint |
| 2025 | [A multimodal LLM-agent framework for personalized clinical decision-making in hepatocellular carcinoma.](https://pubmed.ncbi.nlm.nih.gov/41472823/) | 治疗/决策支持 | Patterns (New York, N.Y.) |
| 2025 | [AI for evidence-based treatment recommendation in oncology: a blinded evaluation of large language models and agentic workflows.](https://pubmed.ncbi.nlm.nih.gov/41446897/) | 评测基准/环境 | Frontiers in artificial intelligence |
| 2025 | [Towards Intelligent Agents for Radiotherapy: Integrating Exploration-Exploitation with Foundation Models.](https://pubmed.ncbi.nlm.nih.gov/41335754/) | 模拟病人/医院 | Annual International Conference of the IEEE Engineering in M |
| 2025 | [From Mutation to Prognosis: AI-HOPE-PI3K Enables Artificial Intelligence Agent-Driven Integration of PI3K Pathway Data in Colorectal Cancer Precision Medicine.](https://pubmed.ncbi.nlm.nih.gov/40650262/) | 训练方法(RL/微调) | International journal of molecular sciences |
| 2025 | [Development and validation of an autonomous artificial intelligence agent for clinical decision-making in oncology.](https://pubmed.ncbi.nlm.nih.gov/40481323/) | 治疗/决策支持 | Nature cancer |
| 2025 | [A feasibility study of automating radiotherapy planning with large language model agents.](https://pubmed.ncbi.nlm.nih.gov/40073507/) | 治疗/决策支持 | Physics in medicine and biology |
| 2025 | [ChatExosome: An Artificial Intelligence (AI) Agent Based on Deep Learning of Exosomes Spectroscopy for Hepatocellular Carcinoma (HCC) Diagnosis.](https://pubmed.ncbi.nlm.nih.gov/39932366/) | 诊断/鉴别诊断 | Analytical chemistry |
| 2024-09-27 | [Personalizing Prostate Cancer Education for Patients Using an EHR-Integrated LLM Agent](http://arxiv.org/abs/2409.19100v2) | EHR/结构化数据 | NPJ digital medicine |
| 2024-04-06 | [Autonomous Artificial Intelligence Agents for Clinical Decision Making in Oncology](http://arxiv.org/abs/2404.04667v1) | 治疗/决策支持 | 91 pages, 2 Figures |

## 遗传/罕见病/组学（54）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-17 | [Large Language Model Agents for Evidence Based Genetic Disease Severity Classification](http://arxiv.org/abs/2609.19569v2) | 检索/RAG/知识 |  |
| 2026-09-14 | [HypoEvolve: Genetic Algorithms Enable Multi-Agent LLMs to Discover Scientific Hypotheses](http://arxiv.org/abs/2609.15938v1) | 多智能体协作 | 22 pages, 8 figures, 5 tables |
| 2026-08-19 | [Accelerated Genetic Programming Hyper-Heuristics for Simulation-Based Scheduling via Agentic AI](http://arxiv.org/abs/2608.19487v1) | 模拟病人/医院 |  |
| 2026-08-17 | [Automating Parent Selection Configuration in Genetic Programming with Agentic AI](http://arxiv.org/abs/2608.17172v2) | 评测基准/环境 | Updated Benchmarking figure with correct statistical test re |
| 2026-08-14 | [Engineering Signals of Human-AI Collaboration in the Agentic Coding Era: A Longitudinal Analysis of 33,228 Pull Requests from vLLM and SGLang with Implications for Biomedical AI Agents and Bioinformatics Pipeline Developmen](http://arxiv.org/abs/2608.13884v1) | 多智能体协作 | 24 pages, 9 Figures |
| 2026-07-21 | [BioSecBench-Surveillance: A Verifiable Benchmark for AI Agents in Pathogen Genomic Surveillance](http://arxiv.org/abs/2607.19262v1) | 评测基准/环境 |  |
| 2026-06-23 | [DeepBD: A Grounded Agentic Workflow for Variant Prioritization and Diagnosis of Genetic Birth Defects](http://arxiv.org/abs/2606.24779v1) | 诊断/鉴别诊断 |  |
| 2026-06-15 | [Teaching agentic AI to generalize expert diagnostic reasoning in rare diseases](http://arxiv.org/abs/2606.16149v5) | 诊断/鉴别诊断 | Updated ablation experiments and layout; revised manuscript  |
| 2026-06-10 | [Skill-Augmented AI Agents for Medical Research Analysis: An Exploratory Multi-Model Human Evaluation in an NSCLC Transcriptomic Biomarker Task](http://arxiv.org/abs/2606.11830v1) | 检索/RAG/知识 |  |
| 2026-05-29 | [Agentic Authoring of Interactive Multiview Visualizations in Genomics](http://arxiv.org/abs/2606.00370v1) | 综述/观点 | 11 pages, 12 figures |
| 2026-05-08 | [GEAR: Genetic AutoResearch for Agentic Code Evolution](http://arxiv.org/abs/2605.13874v1) | 检索/RAG/知识 |  |
| 2026-05-07 | [BioResearcher: Scenario-Guided Multi-Agent for Translational Medicine](http://arxiv.org/abs/2605.05985v1) | 检索/RAG/知识 | 5 pages (main text), 21 pages (appendix), 8 figures, 11 tabl |
| 2026-03-12 | [ELISA: An Interpretable Hybrid Generative AI Agent for Expression-Grounded Discovery in Single-Cell Genomics](http://arxiv.org/abs/2603.11872v3) | 评测基准/环境 |  |
| 2026-03-06 | [Evaluating Multi-Agent LLM Architectures for Rare Disease Diagnosis](http://arxiv.org/abs/2603.06856v1) | 评测基准/环境 |  |
| 2026-02-15 | [Process-Supervised Multi-Agent Reinforcement Learning for Reliable Clinical Reasoning](http://arxiv.org/abs/2602.14160v1) | 训练方法(RL/微调) |  |
| 2026-01-20 | [AgentGC: Evolutionary Learning-based Lossless Compression for Genomics Data with LLM-driven Multiple Agent](http://arxiv.org/abs/2601.13559v1) | 治疗/决策支持 |  |
| 2026-01-15 | [From Single to Multi-Agent Reasoning: Advancing GeneGPT for Genomics QA](http://arxiv.org/abs/2601.10581v1) | 问答/推理 | Accepted paper by the 48th European Conference on Informatio |
| 2026 | [ELISA (Embedding-Linked Interactive Single-cell Agent): an interpretable hybrid generative Artificial Intelligence agent for expression-grounded discovery in single-cell genomics.](https://pubmed.ncbi.nlm.nih.gov/42721440/) | 评测基准/环境 | Briefings in bioinformatics |
| 2026 | [Artificial intelligence agents and agentic artificial intelligence applied to precision medicine.](https://pubmed.ncbi.nlm.nih.gov/42617946/) | 综述/观点 | Drug discovery today |
| 2026 | [A generative AI multi-agent framework with integrated XAI governance for cancer diagnostics: from multi-omics interpretation to lifestyle risk stratification.](https://pubmed.ncbi.nlm.nih.gov/42609245/) | 诊断/鉴别诊断 | Frontiers in systems biology |
| 2026 | [GeneGenie: enhancing biomedical question-answering with agentic graphs.](https://pubmed.ncbi.nlm.nih.gov/42555501/) | 评测基准/环境 | Briefings in bioinformatics |
| 2026 | [Agentic genomics: From pipeline automation to autonomous validation.](https://pubmed.ncbi.nlm.nih.gov/42480539/) | 评测基准/环境 | Cell genomics |
| 2026 | [SPARROW: subtyping Parkinson's disease with agentic reasoning and robust omics workflow.](https://pubmed.ncbi.nlm.nih.gov/42445450/) | 安全/幻觉/攻击 | NPJ artificial intelligence |
| 2026 | [RESCUE: An end-to-end multi-agent LLM system for proactive rare-disease patient screening in the EHR.](https://pubmed.ncbi.nlm.nih.gov/42428098/) | EHR/结构化数据 | medRxiv : the preprint server for health sciences |
| 2026 | [Optimizing genomics-aware clinical agents in precision oncology.](https://pubmed.ncbi.nlm.nih.gov/42248877/) | 安全/幻觉/攻击 | NPJ systems biology and applications |
| 2026 | [MARRVEL-MCP: An agentic interface for Mendelian disease discovery via tool-augmented context engineering.](https://pubmed.ncbi.nlm.nih.gov/42167217/) | 综述/观点 | American journal of human genetics |
| 2026 | [An agentic AI system for automated pharmacogenomic recommendation generation.](https://pubmed.ncbi.nlm.nih.gov/41986608/) | 治疗/决策支持 | NPJ digital medicine |
| 2026 | [Empowering AI data scientists using a multi-agent LLM framework with self-evolving capabilities for autonomous, tool-aware biomedical data analyses.](https://pubmed.ncbi.nlm.nih.gov/41912700/) | 训练方法(RL/微调) | Nature biomedical engineering |
| 2026 | [Large language model agents for biological intelligence across genomics, proteomics, spatial biology, and biomedicine.](https://pubmed.ncbi.nlm.nih.gov/41883029/) | 综述/观点 | Briefings in bioinformatics |
| 2026 | [Medea: An omics AI agent for therapeutic discovery.](https://pubmed.ncbi.nlm.nih.gov/41648610/) | 检索/RAG/知识 | bioRxiv : the preprint server for biology |
| 2026 | [Publisher Correction: CRISPR-GPT for agentic automation of gene-editing experiments.](https://pubmed.ncbi.nlm.nih.gov/41361600/) | 其他 | Nature biomedical engineering |
| 2026 | [CRISPR-GPT for agentic automation of gene-editing experiments.](https://pubmed.ncbi.nlm.nih.gov/40738974/) | 治疗/决策支持 | bioRxiv : the preprint server for biology |
| 2025-11-19 | [Beyond GeneGPT: A Multi-Agent Architecture with Open-Source LLMs for Enhanced Genomic Question Answering](http://arxiv.org/abs/2511.15061v1) | 问答/推理 | This paper has been accepted to SIGIR-AP 2025 |
| 2025-11-06 | [Learning to reason about rare diseases through retrieval-augmented agents](http://arxiv.org/abs/2511.04720v1) | 检索/RAG/知识 | Submitted on behalf of the PREDICTOM consortium |
| 2025-09-23 | [Nano Bio-Agents (NBA): Small Language Model Agents for Genomics](http://arxiv.org/abs/2509.19566v1) | 评测基准/环境 |  |
| 2025-08-06 | [Discovery of Disease Relationships via Transcriptomic Signature Analysis Powered by Agentic AI](http://arxiv.org/abs/2508.04742v1) | 综述/观点 |  |
| 2025-07-14 | [RDMA: Cost Effective Agent-Driven Rare Disease Mining from Electronic Health Records](http://arxiv.org/abs/2507.15867v2) | EHR/结构化数据 |  |
| 2025-06-25 | [An Agentic System for Rare Disease Diagnosis with Traceable Reasoning](http://arxiv.org/abs/2506.20430v3) | 诊断/鉴别诊断 | Nature |
| 2025-06-05 | [Agentomics-ML: Autonomous Machine Learning Experimentation Agent for Genomic and Transcriptomic Data](http://arxiv.org/abs/2506.05542v1) | 评测基准/环境 |  |
| 2025-05-25 | [Investigating Pedagogical Teacher and Student LLM Agents: Genetic Adaptation Meets Retrieval Augmented Generation Across Learning Style](http://arxiv.org/abs/2505.19173v1) | 检索/RAG/知识 | 38 Pages |
| 2025-04-30 | [mAIstro: an open-source multi-agentic system for automated end-to-end development of radiomics and deep learning models for medical imaging](http://arxiv.org/abs/2505.03785v2) | 多智能体协作 |  |
| 2025-04-10 | [An LLM-Driven Multi-Agent Debate System for Mendelian Diseases](http://arxiv.org/abs/2504.07881v2) | 多智能体协作 | 21 pages, 5 figures, 1 table |
| 2025 | [BioRAGent: natural language biomedical querying with retrieval-augmented multiagent systems.](https://pubmed.ncbi.nlm.nih.gov/41081729/) | 检索/RAG/知识 | Briefings in bioinformatics |
| 2025 | [Streamline automated biomedical discoveries with agentic bioinformatics.](https://pubmed.ncbi.nlm.nih.gov/41016012/) | 综述/观点 | Briefings in bioinformatics |
| 2025 | [Conversational AI agent for precision oncology: AI-HOPE-WNT integrates clinical and genomic data to investigate WNT pathway dysregulation in colorectal cancer.](https://pubmed.ncbi.nlm.nih.gov/40860720/) | 问诊/医患对话 | Frontiers in artificial intelligence |
| 2025 | [A4SLR: An Agentic Artificial Intelligence-Assisted Systematic Literature Review Framework to Augment Evidence Synthesis for Health Economics and Outcomes Research and Health Technology Assessment.](https://pubmed.ncbi.nlm.nih.gov/40816692/) | 综述/观点 | Value in health : the journal of the International Society f |
| 2025 | [GeneAgent: self-verification language agent for gene-set analysis using domain databases.](https://pubmed.ncbi.nlm.nih.gov/40721871/) | 评测基准/环境 | Nature methods |
| 2025 | [AI-HOPE: an AI-driven conversational agent for enhanced clinical and genomic data integration in precision medicine research.](https://pubmed.ncbi.nlm.nih.gov/40577785/) | 问诊/医患对话 | Bioinformatics (Oxford, England) |
| 2025 | [PlantGPT: An Arabidopsis-Based Intelligent Agent that Answers Questions about Plant Functional Genomics.](https://pubmed.ncbi.nlm.nih.gov/40397417/) | 评测基准/环境 | Advanced science (Weinheim, Baden-Wurttemberg, Germany) |
| 2025 | [MRAgent: an LLM-based automated agent for causal knowledge discovery in disease via Mendelian randomization.](https://pubmed.ncbi.nlm.nih.gov/40194554/) | 安全/幻觉/攻击 | Briefings in bioinformatics |
| 2025 | [RDguru: A Conversational Intelligent Agent for Rare Diseases.](https://pubmed.ncbi.nlm.nih.gov/39298307/) | 问诊/医患对话 | IEEE journal of biomedical and health informatics |
| 2024-05-27 | [BioDiscoveryAgent: An AI Agent for Designing Genetic Perturbation Experiments](http://arxiv.org/abs/2405.17631v3) | 训练方法(RL/微调) |  |
| 2024 | [RDguru: An Intelligent Agent for Rare Diseases.](https://pubmed.ncbi.nlm.nih.gov/40417483/) | 诊断/鉴别诊断 | AMIA ... Annual Symposium proceedings. AMIA Symposium |
| 2024 | [GeneAgent: Self-verification Language Agent for Gene Set Knowledge Discovery using Domain Databases.](https://pubmed.ncbi.nlm.nih.gov/38903746/) | 评测基准/环境 | ArXiv |

## 急诊/重症（40）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-27 | [HESP: Separating What to Probe from When to Stop in Local LLM Alert-Triage Agents](http://arxiv.org/abs/2609.33446v1) | 安全/幻觉/攻击 | 15 pages, 5 figures. Code and data: https://github.com/lzwhe |
| 2026-09-21 | [Dissecting Agentic Forensics: The Role of Triage, Prompting, and Evidence Arbitration in Open-World Fake Image Detection](http://arxiv.org/abs/2609.24359v1) | 检索/RAG/知识 | Accepted at the 2026 Workshop on AI for Multimedia Forensics |
| 2026-09-01 | [TRIAGE: Three-level Routing and Intelligent Agent Guidance for Efficient Execution](http://arxiv.org/abs/2609.01428v1) | 问答/推理 |  |
| 2026-08-22 | [FRAC-MAS: A Safe and Explainable Multi-Agent System for Fracture Diagnosis](http://arxiv.org/abs/2608.28662v1) | 诊断/鉴别诊断 | Medical Image Computing and Computer Assisted Intervention ( |
| 2026-08-07 | [Does Splitting a Triage Decision Across Agents Hide Bias or Help Catch It? A Multi-Agent Simulation Study of LLM-Based Resource Allocation Under Audit Capacity Constraints](http://arxiv.org/abs/2608.06949v1) | 模拟病人/医院 | 6 pages, 2 figures, 3 tables. Code and data available at htt |
| 2026-08-06 | [From Siloed Algorithms to Compliance-First Agentic Platforms: A Multi-Layered Architecture for Hospital AI Systems](http://arxiv.org/abs/2608.06112v1) | 模拟病人/医院 | Peer-reviewed published article |
| 2026-07-28 | [PatientAgentBench: A Benchmark Framework for Evaluating Patient-Facing Health AI Agents](http://arxiv.org/abs/2607.25485v1) | 评测基准/环境 | Code: https://github.com/amazon-science/PatientAgentBench |
| 2026-07-22 | [Harnessing Disagreement: Detecting Correlated Agreement Blindness in Multi-Agent Triage](http://arxiv.org/abs/2607.19899v1) | 多智能体协作 | 14 pages, 2 figures, 3 tables. Accepted at PAAMS 2026; this  |
| 2026-06-30 | [TRIAGE: Role-Typed Credit Assignment for Agentic Reinforcement Learning](http://arxiv.org/abs/2606.32017v3) | 训练方法(RL/微调) |  |
| 2026-05-21 | [Standalone LLM and a Pre-specified Agentic Pipeline for Explaining ICU Mortality Predictions: a Feasibility Study on the eICU Demo Dataset](http://arxiv.org/abs/2608.26109v1) | 综述/观点 |  |
| 2026-05-15 | [STAR: A Stage-attributed Triage and Repair framework for RCA Agents in Microservices](http://arxiv.org/abs/2605.15581v1) | 评测基准/环境 | 11 pages |
| 2026-05-13 | [RealICU: Do LLM Agents Understand Long-Context ICU Data? A Benchmark Beyond Behavior Imitation](http://arxiv.org/abs/2605.13542v1) | 评测基准/环境 |  |
| 2026-05-10 | [CodeClinic: Evaluating Automation of Coding Skills for Clinical Reasoning Agents](http://arxiv.org/abs/2605.09675v1) | 评测基准/环境 |  |
| 2026-04-17 | [Don't Start What You Can't Finish: A Counterfactual Audit of Support-State Triage in LLM Agents](http://arxiv.org/abs/2604.16752v1) | 诊断/鉴别诊断 |  |
| 2026-04-08 | [EMSDialog: Synthetic Multi-person Emergency Medical Service Dialogue Generation from Electronic Patient Care Reports via Multi-LLM Agents](http://arxiv.org/abs/2604.07549v2) | 问诊/医患对话 | Accepted by ACL Findings 2026 |
| 2026-04-08 | [SkillSieve: A Hierarchical Triage Framework for Detecting Malicious AI Agent Skills](http://arxiv.org/abs/2604.06550v3) | 评测基准/环境 | 10 pages, 2 figures, 6 tables |
| 2026-04-01 | [CARE: Privacy-Compliant Agentic Reasoning with Evidence Discordance](http://arxiv.org/abs/2604.01113v2) | 安全/幻觉/攻击 | Accepted as a Findings paper at EMNLP 2026 |
| 2026-04-01 | [Signals: Trajectory Sampling and Triage for Agentic Interactions](http://arxiv.org/abs/2604.00356v1) | 评测基准/环境 |  |
| 2026-01-31 | [Agentic Observability: Automated Alert Triage for Adobe E-Commerce](http://arxiv.org/abs/2602.02585v1) | 诊断/鉴别诊断 | Accepted at AAAI'26 Agentic AI Benchmarks and Applications f |
| 2026-01-06 | [SastBench: A Benchmark for Testing Agentic SAST Triage](http://arxiv.org/abs/2601.02941v1) | 评测基准/环境 |  |
| 2026 | [ProMem-agent: Procedural memory-augmented large language model agents for clinical trajectory reasoning.](https://pubmed.ncbi.nlm.nih.gov/42784988/) | 问答/推理 | International journal of medical informatics |
| 2026 | [An LLM-enhanced AI agent for rapid diagnosis of acute aortic dissection in multi-center settings.](https://pubmed.ncbi.nlm.nih.gov/42757002/) | 诊断/鉴别诊断 | iScience |
| 2026 | [ED-triage-agent: a multi-agent framework for human-in-the-loop emergency triage.](https://pubmed.ncbi.nlm.nih.gov/42612553/) | 多智能体协作 | International journal of medical informatics |
| 2026 | [A large language model-driven multidisciplinary AI agent system predicts delirium in emergency critically ill patients.](https://pubmed.ncbi.nlm.nih.gov/42594876/) | 综述/观点 | Cell reports. Medicine |
| 2026 | [PAUSE-Agents: A Clinician-in-the-Loop Multi-Agent AI Pipeline for ICU-to-Ward Handoff Briefs.](https://pubmed.ncbi.nlm.nih.gov/42528499/) | 多智能体协作 | medRxiv : the preprint server for health sciences |
| 2026 | [MAP: evaluation and multi-agent enhancement of large language models for inpatient pathways.](https://pubmed.ncbi.nlm.nih.gov/42527484/) | 多智能体协作 | npj health systems |
| 2026 | [An autonomous AI agent for knowledge and data cooperation in ED clinical decision support.](https://pubmed.ncbi.nlm.nih.gov/42286154/) | 治疗/决策支持 | NPJ digital medicine |
| 2026 | [Multi-Agent System for Early Sepsis Management Support: A Follow-up Evaluation Study.](https://pubmed.ncbi.nlm.nih.gov/42167741/) | 治疗/决策支持 | Healthcare informatics research |
| 2026 | [Agentic GPT-5.0 system outperforms standard large language models and human experts in critical care clinical decision-making: a simulation study.](https://pubmed.ncbi.nlm.nih.gov/42104391/) | 模拟病人/医院 | BMC medical informatics and decision making |
| 2026 | [From non-agentic large language models to multi-agent systems in emergency medicine: a scoping review.](https://pubmed.ncbi.nlm.nih.gov/41952479/) | 综述/观点 | Clinical and experimental emergency medicine |
| 2026 | [DILIConsult: A Multi-Agent Large Language Model Framework for Evaluating Drug-Induced Liver Injury in ICU Settings.](https://pubmed.ncbi.nlm.nih.gov/41826786/) | 评测基准/环境 | Pharmacotherapy |
| 2026 | [LLM-based pedagogical agent for ICU simulation instructor training: A quasi-experimental study.](https://pubmed.ncbi.nlm.nih.gov/41197517/) | 模拟病人/医院 | Nurse education today |
| 2025-11-16 | [Multi-agent Self-triage System with Medical Flowcharts](http://arxiv.org/abs/2511.12439v2) | 多智能体协作 |  |
| 2025-10-30 | [A Multi-agent Large Language Model Framework to Automatically Assess Performance of a Clinical AI Triage Tool](http://arxiv.org/abs/2510.26498v1) | 多智能体协作 | npj health systems |
| 2025-10-24 | [DispatchMAS: Fusing taxonomy and artificial intelligence agents for emergency medical services](http://arxiv.org/abs/2510.21228v1) | 综述/观点 | BMC emergency medicine |
| 2025-10-17 | [TriAgent: Automated Biomarker Discovery with Deep Research Grounding for Triage in Acute Care by LLM-Based Multi-Agent Collaboration](http://arxiv.org/abs/2510.16080v1) | 检索/RAG/知识 |  |
| 2025-09-30 | [CORTEX: Collaborative LLM Agents for High-Stakes Alert Triage](http://arxiv.org/abs/2510.00311v1) | 多智能体协作 |  |
| 2025-06-04 | [AI Agents for Conversational Patient Triage: Preliminary Simulation-Based Evaluation with Real-World EHR Data](http://arxiv.org/abs/2506.04032v1) | 模拟病人/医院 |  |
| 2024-08-14 | [Development of a Large Language Model-based Multi-Agent Clinical Decision Support System for Korean Triage and Acuity Scale (KTAS)-Based Triage and Treatment Planning in Emergency Departments](http://arxiv.org/abs/2408.07531v2) | 治疗/决策支持 |  |
| 2024 | [AKI-Detector: A Multi-Agent Framework by Integrating Machine Learning and Large Language Models for Early Prediction of Acute Kidney Injury in ICU.](https://pubmed.ncbi.nlm.nih.gov/41726403/) | 多智能体协作 | AMIA ... Annual Symposium proceedings. AMIA Symposium |

## 生物医学科研（35）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-08-14 | [How Do Agents Fail on AutoResearch: End-to-End Diagnostic Evaluation on 100 Real-World Frontier Research Tasks](http://arxiv.org/abs/2608.14905v3) | 诊断/鉴别诊断 | *Equal Contribution (alphabetical order by last name) |
| 2026-06-20 | [OpenBioRQ: Unsolved Biomedical Research Questions for Agents](http://arxiv.org/abs/2606.21959v1) | 检索/RAG/知识 |  |
| 2026-05-15 | [BioXArena: Benchmarking LLM Agents on Multi-Modal Biomedical Machine Learning Tasks](http://arxiv.org/abs/2605.15766v1) | 评测基准/环境 | 69 pages, 13 figures, 34 tables |
| 2026-04-16 | [DeepER-Med: Advancing Deep Evidence-Based Research in Medicine Through Agentic AI](http://arxiv.org/abs/2604.15456v1) | 检索/RAG/知识 | 37 pages, 6 figures, 5 tables |
| 2026-01-28 | [MedViz: An Agent-based, Visual-guided Research Assistant for Navigating Biomedical Literature](http://arxiv.org/abs/2601.20709v1) | 检索/RAG/知识 |  |
| 2026 | [An agentic AI framework connecting language models to electronic health records and a biomedical knowledge graph for real-world evidence.](https://pubmed.ncbi.nlm.nih.gov/42761240/) | EHR/结构化数据 | Frontiers in artificial intelligence |
| 2026 | [DDA: a traceable multi-agent framework for automated structure-based drug design.](https://pubmed.ncbi.nlm.nih.gov/42745879/) | 多智能体协作 | Frontiers in chemistry |
| 2026 | [Retraction: Small Language Models for Developing Agentic AI in Healthcare: A Comprehensive Systematic Review and Critical Analysis.](https://pubmed.ncbi.nlm.nih.gov/42719872/) | 综述/观点 | Cureus |
| 2026 | [Improvement of Clinical Practice Guideline Appraisal by Human Experts and AI Agents by Using Structured Guidance: Systematic Review, Meta-Analysis, and Validation Study.](https://pubmed.ncbi.nlm.nih.gov/42647856/) | 综述/观点 | Journal of medical Internet research |
| 2026 | [BioPathfinder: Evidence-guided multi-agent platform enables hypothesis discovery for CAR-T engineering.](https://pubmed.ncbi.nlm.nih.gov/42619779/) | 检索/RAG/知识 | bioRxiv : the preprint server for biology |
| 2026 | [EcoXAI: Autonomous Agentic Ecosystem for Explainable Artificial Intelligence and Biomedical Discovery.](https://pubmed.ncbi.nlm.nih.gov/42523383/) | 安全/幻觉/攻击 | bioRxiv : the preprint server for biology |
| 2026 | [Agentic artificial intelligence in medicine and biomedical research: A primer and framework for clinicians and researchers.](https://pubmed.ncbi.nlm.nih.gov/42436873/) | 检索/RAG/知识 | JAAD international |
| 2026 | [Autonomous biomedical research with an artificial intelligence agent.](https://pubmed.ncbi.nlm.nih.gov/42424436/) | 检索/RAG/知识 | Science (New York, N.Y.) |
| 2026 | [Are artificial intelligence (AI) agents ready for medicine and biomedical research? A narrative review.](https://pubmed.ncbi.nlm.nih.gov/42304602/) | 综述/观点 | Journal of Yeungnam medical science |
| 2026 | [MechAInistic: A Reviewer-Supervised Multi-Agent LLM System for Auditable Mechanistic Drug-Hypothesis Generation.](https://pubmed.ncbi.nlm.nih.gov/42182411/) | 多智能体协作 | bioRxiv : the preprint server for biology |
| 2026 | [Small Language Models for Developing Agentic AI in Healthcare: A Comprehensive Systematic Review and Critical Analysis.](https://pubmed.ncbi.nlm.nih.gov/42088811/) | 综述/观点 | Cureus |
| 2026 | [DrugAgent: A multi-agent digital biosensor framework for interpretable virtual drug screening.](https://pubmed.ncbi.nlm.nih.gov/41950794/) | 多智能体协作 | Journal of molecular graphics & modelling |
| 2026 | [[Application and progress of artificial intelligence agents in drug development].](https://pubmed.ncbi.nlm.nih.gov/41490887/) | 综述/观点 | Zhejiang da xue xue bao. Yi xue ban = Journal of Zhejiang Un |
| 2025-11-26 | [Conversational No-code, Multi-agentic Disease Module Identification and Drug Repurposing Prediction with ChatDRex](http://arxiv.org/abs/2511.21438v2) | 问诊/医患对话 |  |
| 2025-11-25 | [FRAGMENTA: End-to-end Fragmentation-based Generative Model with Agentic Tuning for Drug Lead Optimization](http://arxiv.org/abs/2511.20510v2) | 问诊/医患对话 |  |
| 2025-11-12 | [BioVerge: A Comprehensive Benchmark and Study of Self-Evaluating Agents for Biomedical Hypothesis Generation](http://arxiv.org/abs/2511.08866v1) | 评测基准/环境 |  |
| 2025-08-14 | [FROGENT: An End-to-End Full-process Drug Design Multi-Agent System](http://arxiv.org/abs/2508.10760v2) | 多智能体协作 | 37 pages, 20 figures |
| 2025-07-10 | [DrugMCTS: a drug repurposing framework combining multi-agent, RAG and Monte Carlo Tree Search](http://arxiv.org/abs/2507.07426v3) | 检索/RAG/知识 |  |
| 2025-07-01 | [STELLA: Self-Evolving LLM Agent for Biomedical Research](http://arxiv.org/abs/2507.02004v1) | 训练方法(RL/微调) |  |
| 2025-06-16 | [Language Agents for Hypothesis-driven Clinical Decision Making with Reinforcement Learning](http://arxiv.org/abs/2506.13474v3) | 训练方法(RL/微调) |  |
| 2025-05-22 | [Beyond Correlation: Towards Causal Large Language Model Agents in Biomedicine](http://arxiv.org/abs/2505.16982v1) | 评测基准/环境 |  |
| 2025 | [Multi agent large language models for biomedical hypothesis generation in drug combination discovery.](https://pubmed.ncbi.nlm.nih.gov/41362614/) | 检索/RAG/知识 | iScience |
| 2025 | [Effectiveness of Communication Competence in AI Conversational Agents for Health: Systematic Review and Meta-Analysis.](https://pubmed.ncbi.nlm.nih.gov/41183242/) | 综述/观点 | Journal of medical Internet research |
| 2025 | [AI Agents in Clinical Medicine: A Systematic Review.](https://pubmed.ncbi.nlm.nih.gov/40909853/) | 综述/观点 | medRxiv : the preprint server for health sciences |
| 2025 | [Evidence-based Knowledge Synthesis and Hypothesis Validation: Navigating Biomedical Knowledge Bases via Explainable AI and Agentic Systems.](https://pubmed.ncbi.nlm.nih.gov/40587410/) | 检索/RAG/知识 | Journal of visualized experiments : JoVE |
| 2025 | [Biomni: A General-Purpose Biomedical AI Agent.](https://pubmed.ncbi.nlm.nih.gov/40501924/) | 评测基准/环境 | bioRxiv : the preprint server for biology |
| 2025 | [LITERAS: Biomedical literature review and citation retrieval agents.](https://pubmed.ncbi.nlm.nih.gov/40383055/) | 综述/观点 | Computers in biology and medicine |
| 2025 | [Role of artificial intelligence-powered conversational agents (chatbots) in musculoskeletal disorders: a scoping review protocol.](https://pubmed.ncbi.nlm.nih.gov/40132840/) | 综述/观点 | BMJ open |
| 2024-09-21 | [Current Trends and Future Directions for Sexual Health Conversational Agents (CAs) for Youth: A Scoping Review](http://arxiv.org/abs/2409.14226v1) | 综述/观点 | The 14th International Conference on Current and Future Tren |
| 2024-04-03 | [Empowering Biomedical Discovery with AI Agents](http://arxiv.org/abs/2404.02831v2) | 模拟病人/医院 | Cell |

## 病理（30）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-25 | [MACBT: A Multi-Agent Cognitive Behavioral Therapy Decision Support System with Longitudinal Memory](http://arxiv.org/abs/2609.30939v1) | 治疗/决策支持 |  |
| 2026-08-09 | [Agentic Visual Reasoning in Whole-Slide Pathology Images via Active Perception](http://arxiv.org/abs/2608.08648v1) | 问答/推理 | 14 pages, 5 figures |
| 2026-07-01 | [Evaluating Agentic Harness Systems for Autonomous Computational Pathology](http://arxiv.org/abs/2607.02598v1) | 评测基准/环境 |  |
| 2026-06-18 | [Prompt, Plan, Extract: Zero-Shot Agentic LLMs Workflows for Lung Pathology Extraction from Clinical Narratives](http://arxiv.org/abs/2606.19852v2) | 报告/文书生成 | 7 pages, 2 figures, 3 tables. Affiliations: (1) Department o |
| 2026-06-12 | [Democratizing and accelerating AI-driven pathology research through agentic intelligence](http://arxiv.org/abs/2606.20677v1) | 检索/RAG/知识 | 29 pages, 4 figures |
| 2026-06-06 | [A Multimodal Agentic Pathology Co-pilot via Evidence Grounded Reasoning](http://arxiv.org/abs/2606.08093v2) | 检索/RAG/知识 |  |
| 2026-05-22 | [PathNavigate: A Training-Free Pathology Agent with Surprise-Guided Scan and Shared Slide Memory for Whole-Slide Image VQA](http://arxiv.org/abs/2605.23559v1) | 检索/RAG/知识 |  |
| 2026-05-18 | [PathoSage: Towards Multi-Source Evidence Adjudication in Pathology via Experience-Aware Agentic Workflow](http://arxiv.org/abs/2606.07549v1) | 检索/RAG/知识 |  |
| 2026-05-11 | [CellDX AI Autopilot: Agent-Guided Training and Deployment of Pathology Classifiers](http://arxiv.org/abs/2605.10362v1) | 诊断/鉴别诊断 |  |
| 2026-03-06 | [Computational Pathology in the Era of Emerging Foundation and Agentic AI -- International Expert Perspectives on Clinical Integration and Translational Readiness](http://arxiv.org/abs/2603.05884v2) | 综述/观点 |  |
| 2026-03-02 | [QCAgent: An agentic framework for quality-controllable pathology report generation from whole slide image](http://arxiv.org/abs/2603.01647v1) | 报告/文书生成 |  |
| 2026-02-01 | [SAGE: Agentic Framework for Interpretable and Clinically Translatable Computational Pathology Biomarker Discovery](http://arxiv.org/abs/2602.00953v2) | 检索/RAG/知识 |  |
| 2026-01-26 | [Potential Role of Agentic Artificial Intelligence in Toxicologic Pathology](http://arxiv.org/abs/2602.06980v2) | 评测基准/环境 |  |
| 2026 | [Comparative Evaluation of a New Autonomous AI Agent Versus Frontier LLMs for AI-Generated Patient Information Sheets on Pediatric Pathologies.](https://pubmed.ncbi.nlm.nih.gov/42795013/) | 评测基准/环境 | Cancers |
| 2026 | [Agentic systems in computational pathology: architectures, evidence, and translational challenges.](https://pubmed.ncbi.nlm.nih.gov/42665811/) | 综述/观点 | Journal of translational medicine |
| 2026 | [End-to-End Clinical Validation of a Human-Supervised Large Language Model Agent for Enterprise Surgical Pathology Reporting.](https://pubmed.ncbi.nlm.nih.gov/42526601/) | 报告/文书生成 | Modern pathology : an official journal of the United States  |
| 2026 | [Pathology-CoT: learning visual chain-of-thought agents from expert whole-slide image diagnosis behaviour.](https://pubmed.ncbi.nlm.nih.gov/42498734/) | 诊断/鉴别诊断 | Nature biomedical engineering |
| 2026 | [A Systematic Literature Review on Integrated Deep Learning and Multiagent Vision-Language Frameworks for Pathology Image Analysis and Report Generation.](https://pubmed.ncbi.nlm.nih.gov/41982676/) | 综述/观点 | Computational and structural biotechnology journal |
| 2026 | [[Study of the performances of conversational agents in interpreting textual description of lesions in pathology].](https://pubmed.ncbi.nlm.nih.gov/41545265/) | 问诊/医患对话 | Annales de pathologie |
| 2025-12-29 | [PathFound: An Agentic Multimodal Model Activating Evidence-seeking Pathological Diagnosis](http://arxiv.org/abs/2512.23545v1) | 诊断/鉴别诊断 | Medical image analysis |
| 2025-11-30 | [Exploring General-Purpose Autonomous Multimodal Agents for Pathology Report Generation](http://arxiv.org/abs/2601.11540v1) | 报告/文书生成 | 6 pages, 1 figure, accepted paper for BVM 2026 |
| 2025-11-21 | [PathAgent: Toward Interpretable Analysis of Whole-slide Pathology Images via Large Language Model-based Agentic Reasoning](http://arxiv.org/abs/2511.17052v1) | 问答/推理 | 11 pages, 6 figures |
| 2025-10-06 | [Pathology-CoT: Learning Visual Chain-of-Thought Agent from Expert Whole Slide Image Diagnosis Behavior](http://arxiv.org/abs/2510.04587v2) | 诊断/鉴别诊断 |  |
| 2025-08-04 | [Patho-AgenticRAG: Towards Multimodal Agentic Retrieval-Augmented Generation for Pathology VLMs via Reinforcement Learning](http://arxiv.org/abs/2508.02258v2) | 训练方法(RL/微调) |  |
| 2025-08-02 | [GMAT: Grounded Multi-Agent Clinical Description Generation for Text Encoder in Vision-Language MIL for Whole Slide Image Classification](http://arxiv.org/abs/2508.01293v2) | 多智能体协作 | Acccepted in MICCAI Workshop 2025 |
| 2025-06-26 | [Evidence-based diagnostic reasoning with multi-agent copilot for human pathology](http://arxiv.org/abs/2506.20964v2) | 诊断/鉴别诊断 |  |
| 2025-05-26 | [CPathAgent: An Agent-based Foundation Model for Interpretable High-Resolution Pathology Image Analysis Mimicking Pathologists' Diagnostic Logic](http://arxiv.org/abs/2505.20510v2) | 诊断/鉴别诊断 | 52 pages, 34 figures |
| 2025-02-13 | [PathFinder: A Multi-Modal Multi-Agent System for Medical Diagnostic Decision-Making Applied to Histopathology](http://arxiv.org/abs/2502.08916v1) | 诊断/鉴别诊断 |  |
| 2025 | [Agentic Generative Artificial Intelligence System for Classification of Pathology-Confirmed Primary Progressive Aphasia Variants.](https://pubmed.ncbi.nlm.nih.gov/41282783/) | 综述/观点 | medRxiv : the preprint server for health sciences |
| 2024-06-28 | [PathGen-1.6M: 1.6 Million Pathology Image-text Pairs Generation through Multi-agent Collaboration](http://arxiv.org/abs/2407.00203v1) | 多智能体协作 | 13 pages, 3 figures |

## 神经（26）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-22 | [Governed AI-Agent Coordination for Dementia Care: Architecture, Safety Contracts, and Evidence-Derived Workflow Verification](http://arxiv.org/abs/2609.25956v1) | 安全/幻觉/攻击 | 13 pages, 2 figures, 5 tables. Includes an executable archit |
| 2026-07-30 | [MA-RAG: Multi-Agent Retrieval-Augmented Generation for Query-Driven Summarization of Longitudinal Parkinson's Disease Assessments](http://arxiv.org/abs/2608.28624v1) | 报告/文书生成 |  |
| 2026-05-08 | [AI-Care: A Conversational Agentic System for Task Coordination in Alzheimer's Disease Care](http://arxiv.org/abs/2605.08480v1) | 问诊/医患对话 | 9 pages, 3 figures |
| 2026-04-10 | [Neuro-Oracle: A Trajectory-Aware Agentic RAG Framework for Interpretable Epilepsy Surgical Prognosis](http://arxiv.org/abs/2604.14216v1) | 检索/RAG/知识 |  |
| 2026-03-26 | [AD-CARE: A Guideline-grounded, Modality-agnostic LLM Agent for Real-world Alzheimer's Disease Diagnosis with Multi-cohort Assessment, Fairness Analysis, and Reader Study](http://arxiv.org/abs/2603.25322v1) | 安全/幻觉/攻击 |  |
| 2026-03-18 | [Agentic Cognitive Profiling: Realigning Automated Alzheimer's Disease Detection with Clinical Construct Validity](http://arxiv.org/abs/2603.17392v1) | 安全/幻觉/攻击 |  |
| 2026 | [CellSwarm-AD: A Multi-Scale Agent-Based Framework for Virtual Alzheimer's Disease Trials.](https://pubmed.ncbi.nlm.nih.gov/42589569/) | 模拟病人/医院 | International journal of molecular sciences |
| 2026 | [OntoCodex: a multi-agent biomedical ontology enrichment framework.](https://pubmed.ncbi.nlm.nih.gov/42552428/) | 多智能体协作 | npj health systems |
| 2026 | [A Multiagent Large Language Model Framework for Emergency Treatment Recommendation in Acute Ischemic Stroke: Development and Validation Study.](https://pubmed.ncbi.nlm.nih.gov/42531250/) | 治疗/决策支持 | Journal of medical Internet research |
| 2026 | [Bridging the outcome documentation gap in epilepsy surgery: Validating large language model agents for automated Engel and International League Against Epilepsy scoring from clinical notes.](https://pubmed.ncbi.nlm.nih.gov/42284021/) | 报告/文书生成 | Epilepsia |
| 2026 | [Collaborative multi-agent conversational artificial intelligence for clinical support in Parkinson disease.](https://pubmed.ncbi.nlm.nih.gov/41925479/) | 问诊/医患对话 | Parkinsonism & related disorders |
| 2026 | [A large language model-based self-learning and critical agent framework for multimodal Alzheimer's disease diagnosis.](https://pubmed.ncbi.nlm.nih.gov/41885908/) | 诊断/鉴别诊断 | Neuropsychology |
| 2026 | [Multimodal diagnosis of Parkinson's disease with an internet-based collaborative agent architecture of medical language models.](https://pubmed.ncbi.nlm.nih.gov/41558387/) | 诊断/鉴别诊断 | Computers in biology and medicine |
| 2025-11-08 | [Towards Human-AI-Robot Collaboration and AI-Agent based Digital Twins for Parkinson's Disease Management: Review and Outlook](http://arxiv.org/abs/2511.06036v1) | 综述/观点 | 20 pages, 5 figures, 4 tables, under review with a journal |
| 2025-09-14 | [Designing and Evaluating a Conversational Agent for Early Diagnosis of Alzheimer's Disease and Related Dementias](http://arxiv.org/abs/2509.11478v2) | 评测基准/环境 | First two authors contributed equally |
| 2025-09-01 | [AgenticAD: A Specialized Multiagent System Framework for Holistic Alzheimer Disease Management](http://arxiv.org/abs/2510.08578v1) | 治疗/决策支持 |  |
| 2025-08-10 | [A Multi-Agent Approach to Neurological Clinical Reasoning](http://arxiv.org/abs/2508.14063v1) | 问答/推理 | PLOS digital health |
| 2025-06-11 | [ADAgent: LLM Agent for Alzheimer's Disease Analysis with Collaborative Coordinator](http://arxiv.org/abs/2506.11150v3) | 多智能体协作 |  |
| 2025-05-30 | [MedOrch: Medical Diagnosis with Tool-Augmented Reasoning Agents for Flexible Extensibility](http://arxiv.org/abs/2506.00235v1) | 诊断/鉴别诊断 |  |
| 2025-05-29 | [Large Language Model-Based Agents for Automated Research Reproducibility: An Exploratory Study in Alzheimer's Disease](http://arxiv.org/abs/2505.23852v1) | 检索/RAG/知识 |  |
| 2025-03-26 | [DEMENTIA-PLAN: An Agent-Based Framework for Multi-Knowledge Graph Retrieval-Augmented Generation in Dementia Care](http://arxiv.org/abs/2503.20950v1) | 检索/RAG/知识 | Accepted by AAAI 2025 Workshop on Knowledge Graphs for Perso |
| 2025-02-06 | [Agentic AI for Scaling Diagnosis and Care in Neurodegenerative Disease](http://arxiv.org/abs/2502.06842v4) | 诊断/鉴别诊断 | Nature aging |
| 2025-01-28 | [Integrating Reinforcement Learning and AI Agents for Adaptive Robotic Interaction and Assistance in Dementia Care](http://arxiv.org/abs/2501.17206v1) | 训练方法(RL/微调) | 18 pages, 12 figures |
| 2025 | [AI agents in Alzheimer's disease management: challenges and future directions.](https://pubmed.ncbi.nlm.nih.gov/41561816/) | 综述/观点 | Frontiers in aging neuroscience |
| 2025 | [Agentic artificial intelligence in cognitive screening: A translational roadmap for dementia care.](https://pubmed.ncbi.nlm.nih.gov/41393341/) | 综述/观点 | Journal of Alzheimer's disease reports |
| 2025 | [CARE-AD: a multi-agent large language model framework for Alzheimer's disease prediction using longitudinal clinical notes.](https://pubmed.ncbi.nlm.nih.gov/40849361/) | 报告/文书生成 | NPJ digital medicine |

## 健康管理/生活方式（21）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-21 | [A Task-Oriented Multi-Agent Framework for Complex Wearable Health Analysis](http://arxiv.org/abs/2609.24107v1) | 多智能体协作 | 23 pages, 4 figures. Code available at https://github.com/ya |
| 2026-08-20 | [A knowledge-guided agentic framework for mitigating patient-context ambiguity in health queries](http://arxiv.org/abs/2608.19875v1) | 评测基准/环境 | 48 pages, 3 figures, 6 tables, journal |
| 2026-07-23 | [HiMe: Real-Time Self-Hosted Personal Agent Platform for Health Insights with Wearable Devices](http://arxiv.org/abs/2607.21019v1) | 综述/观点 |  |
| 2026-06-16 | [RubricsTree: Scalable and Evolving Open-Ended Evaluation of Personal Health Agents across Health Memory and Medical Skills](http://arxiv.org/abs/2606.18203v1) | 评测基准/环境 |  |
| 2026-06-16 | [WEQA: Wearable hEalth Question Answering with Query-Adaptive Agentic Reasoning](http://arxiv.org/abs/2606.18147v1) | 问答/推理 |  |
| 2026-05-28 | [VitalAgent: A Tool-Augmented Agent for Reactive and Proactive Physiological Monitoring over Wearable Health Data](http://arxiv.org/abs/2605.29483v2) | 评测基准/环境 | Minor revisions; results unchanged |
| 2026-05-07 | [Dual-Agent Co-Training for Health Coaching via Implicit Adversarial Preference Optimization](http://arxiv.org/abs/2605.07011v1) | 安全/幻觉/攻击 |  |
| 2026-04-29 | [Detecting Clinical Discrepancies in Health Coaching Agents: A Dual-Stream Memory and Reconciliation Architecture](http://arxiv.org/abs/2604.27045v1) | 安全/幻觉/攻击 |  |
| 2026-04-12 | [Sense Less, Infer More: Agentic Multimodal Transformers for Edge Medical Intelligence](http://arxiv.org/abs/2604.10404v1) | 安全/幻觉/攻击 | 7 figures, 4 tables |
| 2026-03-15 | [SAGE: Sensor-Augmented Grounding Engine for LLM-Powered Sleep Care Agent](http://arxiv.org/abs/2604.16342v1) | 检索/RAG/知识 | Accepted to the Extended Abstracts of the 2026 CHI Conferenc |
| 2026-02-20 | [NutriOrion: A Hierarchical Multi-Agent Framework for Personalized Nutrition Intervention Grounded in Clinical Guidelines](http://arxiv.org/abs/2602.18650v1) | 多智能体协作 |  |
| 2026 | [Computational Nutrition 2.0: From Static Models to Closed-loop Agentic Systems for Personalized Nutrition.](https://pubmed.ncbi.nlm.nih.gov/42805435/) | 评测基准/环境 | The Journal of nutrition |
| 2026 | [A multimodal multi-agent LLM framework for identifying key drivers of sleep disorders.](https://pubmed.ncbi.nlm.nih.gov/42518951/) | 多智能体协作 | Frontiers in neurology |
| 2026 | [Toward integrated sleep health: multimodal AI in Hang Hao Meng agent.](https://pubmed.ncbi.nlm.nih.gov/41663720/) | 综述/观点 | NPJ digital medicine |
| 2025-10-31 | [A Memory-Efficient Retrieval Architecture for RAG-Enabled Wearable Medical LLMs-Agents](http://arxiv.org/abs/2510.27107v1) | 检索/RAG/知识 | Accepted by BioCAS2025 |
| 2025-09-05 | [SePA: A Search-enhanced Predictive Agent for Personalized Health Coaching](http://arxiv.org/abs/2509.04752v1) | 检索/RAG/知识 | Accepted at IEEE-EMBS International Conference on Biomedical |
| 2025-08-27 | [The Anatomy of a Personal Health Agent](http://arxiv.org/abs/2508.20148v2) | 评测基准/环境 | Minor updates to the manuscript (V2) |
| 2025-02-18 | [Sleepless Nights, Sugary Days: Creating Synthetic Users with Health Conditions for Realistic Coaching Agent Interactions](http://arxiv.org/abs/2502.13135v3) | 评测基准/环境 | Published in Findings of the Association for Computational L |
| 2025 | [Comparative analysis of AI on human nutrition knowledge: Evaluating large language model-based conversational agents against dietetics students and the general population.](https://pubmed.ncbi.nlm.nih.gov/41359659/) | 评测基准/环境 | PloS one |
| 2025 | [Development of a personalized conversational health agent to enhance physical activity for blind and low-vision individuals.](https://pubmed.ncbi.nlm.nih.gov/40755937/) | 问诊/医患对话 | mHealth |
| 2024-06-10 | [Transforming Wearable Data into Personal Health Insights using Large Language Model Agents](http://arxiv.org/abs/2406.06464v4) | 评测基准/环境 | Nature communications |

## 心血管（20）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-27 | [ECG-Scroll: A Long-Horizon, Streaming Benchmark and Agent Environment for Interpretation of Ambulatory Electrocardiograms](http://arxiv.org/abs/2609.33117v1) | 评测基准/环境 |  |
| 2026-08-10 | [Diagnosing as Cardiologists Do: ECG Agents with Doctor-Grounded Priors for Clinical Reasoning Across Diseases and Populations](http://arxiv.org/abs/2608.09053v1) | 诊断/鉴别诊断 |  |
| 2026-07-28 | [Cardiologent: Multi-Agent Clinical Decision Support for Patient-Level Arrhythmia Assessment, Urgency, and Management](http://arxiv.org/abs/2607.25340v1) | 治疗/决策支持 | 21 pages, 8 figures |
| 2026-07-27 | [Failures Reveal What Metrics Miss: An Evidence-Driven Agent for Recursive Refinement of ECG Classifiers](http://arxiv.org/abs/2607.24419v1) | 检索/RAG/知识 |  |
| 2026-06-26 | [CPAgents: Agentic Composite Phenotype Generation for Cardiac Disease Association](http://arxiv.org/abs/2606.28179v1) | 安全/幻觉/攻击 | Accepted to MICCAI 2026 |
| 2026-04-12 | [CARE-ECG: Causal Agent-based Reasoning for Explainable and Counterfactual ECG Interpretation](http://arxiv.org/abs/2604.10420v1) | 问答/推理 |  |
| 2026-04-02 | [ECG Foundation Models and Medical LLMs for Agentic Cardiovascular Intelligence at the Edge: A Review and Outlook](http://arxiv.org/abs/2604.02501v1) | 综述/观点 | 18 pages, 4 figures, 4 tables, under review with a journal |
| 2026-03-23 | [MARCUS: An agentic, multimodal vision-language model for cardiac diagnosis and management](http://arxiv.org/abs/2603.22179v2) | 诊断/鉴别诊断 |  |
| 2026-01-28 | [ECG-Agent: On-Device Tool-Calling Agent for ECG Multi-Turn Dialogue](http://arxiv.org/abs/2601.20323v1) | 问诊/医患对话 | Accepted to ICASSP 2026 (5 pages, 2 figures, 5 tables) |
| 2026 | [From assistance to autonomy: AI agent systems in cardiovascular medicine-a review of paradigms, architectures, and clinical translation.](https://pubmed.ncbi.nlm.nih.gov/42688813/) | 综述/观点 | Frontiers in cardiovascular medicine |
| 2026 | [A knowledge-enhanced domain-aware large language model agent for atrial fibrillation management.](https://pubmed.ncbi.nlm.nih.gov/42477462/) | 治疗/决策支持 | NPJ digital medicine |
| 2026 | [Behavior Change Content and Implementation of Large Language Model-Driven Conversational Agents in Cardiometabolic Care: Scoping Review.](https://pubmed.ncbi.nlm.nih.gov/42456008/) | 综述/观点 | Journal of medical Internet research |
| 2026 | [An Agentic LLM Framework for Autonomous Surgical Continuum Monitoring: ReAct-Driven Tool-Use Agents for Presurgical, Intraoperative, and Postsurgical Cardiopulmonary Care.](https://pubmed.ncbi.nlm.nih.gov/42351930/) | 安全/幻觉/攻击 | Bioengineering (Basel, Switzerland) |
| 2026 | [Large Language Model Agent for Managing Patients With Suspected Hypertension.](https://pubmed.ncbi.nlm.nih.gov/41064862/) | 评测基准/环境 | Hypertension (Dallas, Tex. : 1979) |
| 2025-12-08 | [ClinNoteAgents: An LLM Multi-Agent System for Predicting and Interpreting Heart Failure 30-Day Readmission from Clinical Notes](http://arxiv.org/abs/2512.07081v2) | 报告/文书生成 | AMIA Joint Summits on Translational Science proceedings. AMI |
| 2025-08-18 | [CardAIc-Agents: A Multimodal Framework with Hierarchical Adaptation for Cardiac Care Support](http://arxiv.org/abs/2508.13256v2) | 综述/观点 |  |
| 2025-03-26 | [TAMA: A Human-AI Collaborative Thematic Analysis Framework Using Multi-Agent LLMs for Clinical Interviews](http://arxiv.org/abs/2503.20666v2) | 问诊/医患对话 | Manuscript accepted to ACM Transactions on Computing for Hea |
| 2025 | [Digital Cardiovascular Twins, AI Agents, and Sensor Data: A Narrative Review from System Architecture to Proactive Heart Health.](https://pubmed.ncbi.nlm.nih.gov/40942702/) | 综述/观点 | Sensors (Basel, Switzerland) |
| 2024-10-21 | [Large Language Models Powered Multiagent Ensemble for Mitigating Hallucination and Efficient Atrial Fibrillation Annotation of ECG Reports](http://arxiv.org/abs/2410.16543v3) | 安全/幻觉/攻击 | 36 pages, 12 figures and 1 table |
| 2024-10-02 | [Zodiac: A Cardiologist-Level LLM Framework for Multi-Agent Diagnostics](http://arxiv.org/abs/2410.02026v1) | 诊断/鉴别诊断 |  |

## 外科/手术（19）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-28 | [AGRO-SUVIDE: Agentic Robotics for Surgical Viscoelastic Debridement](http://arxiv.org/abs/2609.34823v2) | 训练方法(RL/微调) |  |
| 2026-08-14 | [MedClaw: Heuristic Agent Harness for Long-Horizon Surgical Video Reasoning](http://arxiv.org/abs/2608.14015v1) | 问答/推理 |  |
| 2026-05-28 | [SURGENT: A Surgical Multi-Agent Assistance System Across the Perioperative Workflow](http://arxiv.org/abs/2605.29368v1) | 多智能体协作 | preprint |
| 2026-05-25 | [A Multi-Agent LLM Framework for Rating the Quality of Surgical Feedback](http://arxiv.org/abs/2605.25440v1) | 多智能体协作 | 25 pages, 3 figures |
| 2026 | [Local LLMs as cooperative agents for low-cost surgical navigation support.](https://pubmed.ncbi.nlm.nih.gov/42543000/) | 评测基准/环境 | International journal of computer assisted radiology and sur |
| 2026 | [ReflectOR: an LLM-based Agent for Post-Operative Surgical Debriefing.](https://pubmed.ncbi.nlm.nih.gov/42125632/) | 安全/幻觉/攻击 | ... International Workshop on Spoken Dialogue Systems Techno |
| 2026 | [A Multi-AI Agent Framework for Interactive Neurosurgical Education and Evaluation: From Vignettes to Virtual Conversations.](https://pubmed.ncbi.nlm.nih.gov/41982325/) | 问诊/医患对话 | Neurosurgery practice |
| 2026 | [An AI-powered RAG Conversational Agent for Enhancing Patient Recall of Surgical Consultations: A Proof-of-concept Study.](https://pubmed.ncbi.nlm.nih.gov/41911425/) | 问诊/医患对话 | Aesthetic surgery journal |
| 2026 | [Explainable and evidence-linked recommendations for spine surgery via a retrieval-augmented LLM agent.](https://pubmed.ncbi.nlm.nih.gov/41722332/) | 检索/RAG/知识 | European journal of radiology |
| 2025-11-10 | [Voice-Interactive Surgical Agent for Multimodal Patient Data Control](http://arxiv.org/abs/2511.07392v3) | 安全/幻觉/攻击 | 14 pages, 13 figures, 3 tables |
| 2025-10-09 | [CommandSans: Securing AI Agents with Surgical Precision Prompt Sanitization](http://arxiv.org/abs/2510.08829v1) | 评测基准/环境 |  |
| 2025-08-12 | [CARES: Collaborative Agentic Reasoning for Error Detection in Surgery](http://arxiv.org/abs/2508.08764v1) | 问答/推理 |  |
| 2025-08-10 | [EndoCogniAgent: Closed-Loop Agentic Reasoning with Self-Consistency Validation for Endoscopic Diagnosis](http://arxiv.org/abs/2508.07292v4) | 诊断/鉴别诊断 | 21 pages, 24 figures, 9 tables. Revised version: adds a blin |
| 2025-07-03 | [SurgVisAgent: Multimodal Agentic Model for Versatile Surgical Visual Enhancement](http://arxiv.org/abs/2507.02252v1) | 评测基准/环境 |  |
| 2025-06-09 | [Agentic Surgical AI: Surgeon Style Fingerprinting and Privacy Risk Quantification via Discrete Diffusion in a Vision-Language-Action Framework](http://arxiv.org/abs/2506.08185v2) | 安全/幻觉/攻击 |  |
| 2025-03-13 | [SurgRAW: Multi-Agent Workflow with Chain of Thought Reasoning for Robotic Surgical Video Analysis](http://arxiv.org/abs/2503.10265v3) | 问答/推理 |  |
| 2025-03-12 | [Surgical AI Copilot: Energy-Based Fourier Gradient Low-Rank Adaptation for Surgical LLM Agent Reasoning and Planning](http://arxiv.org/abs/2503.09474v2) | 问答/推理 | 11 pages |
| 2025 | [Custom Large Language Models Improve Accuracy: Comparing Retrieval Augmented Generation and Artificial Intelligence Agents to Noncustom Models for Evidence-Based Medicine.](https://pubmed.ncbi.nlm.nih.gov/39521391/) | 检索/RAG/知识 | Arthroscopy : the journal of arthroscopic & related surgery  |
| 2024-12-06 | [SurgBox: Agent-Driven Operating Room Sandbox with Surgery Copilot](http://arxiv.org/abs/2412.05187v1) | 综述/观点 | This work is accepted by IEEE Big Data 2024 |

## 医学教育（19）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-10 | [Evaluating Scaffolding-Oriented Multi-Agent Large Language Model System for Clinical Interview Training](http://arxiv.org/abs/2609.10939v1) | 评测基准/环境 |  |
| 2026-08-17 | [BaT: Towards Self-Evolving Medical Research Agent with Stage Rubrics](http://arxiv.org/abs/2608.16211v1) | 训练方法(RL/微调) |  |
| 2026-04-19 | [Persona-Based Requirements Engineering for Explainable Multi-Agent Educational Systems: A Scenario Simulator for Clinical Reasoning Training](http://arxiv.org/abs/2604.17186v1) | 模拟病人/医院 | 7 pages, 2 figures, CSTE2026: https://cste.net/index.html |
| 2026 | [Early evidence for a multi-agent AI simulator for clinical reasoning practice: performance, consistency, and challenges.](https://pubmed.ncbi.nlm.nih.gov/42740524/) | 综述/观点 | Diagnosis (Berlin, Germany) |
| 2026 | [What Platform Scores Miss: Multidimensional Evaluation of AI Teaching Agents in Medical Education.](https://pubmed.ncbi.nlm.nih.gov/42690903/) | 评测基准/环境 | JMIR medical education |
| 2026 | [A Large Language Model-Powered Multiagent Framework Emulating Standardized Patients in Clinical Communication Skills Training: Development and Evaluation Study.](https://pubmed.ncbi.nlm.nih.gov/42241338/) | 模拟病人/医院 | Journal of medical Internet research |
| 2026 | [Agent-Based Improvement of Multiple-Choice Question Quality in Medical Education.](https://pubmed.ncbi.nlm.nih.gov/42175303/) | 综述/观点 | Studies in health technology and informatics |
| 2026 | [Development and application of an artificial intelligence agent-based case teaching model for health assessment: A quasi-experimental study.](https://pubmed.ncbi.nlm.nih.gov/42114223/) | 综述/观点 | Nurse education today |
| 2026 | [Deep Research Agents: Major Breakthrough or Incremental Progress for Medical AI?](https://pubmed.ncbi.nlm.nih.gov/41886751/) | 检索/RAG/知识 | Journal of medical Internet research |
| 2025-09-10 | [HealthDial: A No-Code LLM-Assisted Dialogue Authoring Tool for Healthcare Virtual Agents](http://arxiv.org/abs/2510.15898v1) | 问诊/医患对话 |  |
| 2025-05-31 | [MMedAgent-RL: Optimizing Multi-Agent Collaboration for Multimodal Medical Reasoning](http://arxiv.org/abs/2506.00555v3) | 训练方法(RL/微调) | ICLR 2026 |
| 2025-03-03 | [Designing VR Simulation System for Clinical Communication Training with LLMs-Based Embodied Conversational Agents](http://arxiv.org/abs/2503.01767v1) | 模拟病人/医院 |  |
| 2025 | [Factors influencing medical students' adoption of AI educational agents: an extended UTAUT model.](https://pubmed.ncbi.nlm.nih.gov/41350656/) | 综述/观点 | BMC medical education |
| 2025 | [Expert Consensus Best Practices for the Safe, Ethical, and Effective Design and Implementation of Artificially Intelligent Conversational Agent (i.e., Chatbot/Virtual Human) Systems in Health Care Applications.](https://pubmed.ncbi.nlm.nih.gov/41113761/) | 问诊/医患对话 | Journal of medical extended reality |
| 2025 | [Beyond Chatbots: Moving Toward Multistep Modular AI Agents in Medical Education.](https://pubmed.ncbi.nlm.nih.gov/41037756/) | 问诊/医患对话 | JMIR medical education |
| 2025 | [Development and evaluation of an agentic LLM based RAG framework for evidence-based patient education.](https://pubmed.ncbi.nlm.nih.gov/40713064/) | 评测基准/环境 | BMJ health & care informatics |
| 2024-09-27 | [Simulated patient systems powered by large language model-based AI agents offer potential for transforming medical education](http://arxiv.org/abs/2409.18924v4) | 模拟病人/医院 | Communications medicine |
| 2024-08-22 | [MEDCO: Medical Education Copilots Based on A Multi-Agent Framework](http://arxiv.org/abs/2408.12496v1) | 多智能体协作 |  |
| 2024 | [Intelligent Tutoring Systems, Generative Artificial Intelligence (AI), and Healthcare Agents: A Proof of Concept and Dual-Layer Approach.](https://pubmed.ncbi.nlm.nih.gov/39308847/) | 综述/观点 | Cureus |

## 医保/编码/行政（15）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-21 | [Ascent: An Agentic System over the Model Context Protocol for Real-World Clinical Data Analysis](http://arxiv.org/abs/2609.24620v1) | 诊断/鉴别诊断 |  |
| 2026-08-20 | [Agentic Governance and Adversarial Verification for Policy-Constrained LLM Healthcare Appeal Generation](http://arxiv.org/abs/2609.27844v1) | 安全/幻觉/攻击 | 18 pages, 7 figures. This manuscript is under review at ACM  |
| 2026-08-17 | [Foundation Agents Meet Agentic Deep Research: Evidence-Grounded Clinical Code Forecasting](http://arxiv.org/abs/2608.17075v1) | 检索/RAG/知识 |  |
| 2026-08-10 | [Listwise Cross-Encoder Fine-Tuning vs. Agentic Instruction Tuning for LLM Rerankers: A Systematic Study in Medical Procedure Reranking](http://arxiv.org/abs/2608.09650v1) | 训练方法(RL/微调) | 10 pages, 6 figures, 4 tables. Code available at https://git |
| 2026-07-06 | [Toward Trustworthy Large Language Model Agents in Healthcare](http://arxiv.org/abs/2607.05055v1) | 安全/幻觉/攻击 |  |
| 2026-04-10 | [HealthAdminBench: Evaluating Computer-Use Agents on Healthcare Administration Tasks](http://arxiv.org/abs/2604.09937v1) | 评测基准/环境 | 24 pages, 5 figures, 5 tables. Benchmark paper introducing 4 |
| 2026-03-31 | [Symphony for Medical Coding: A Next-Generation Agentic System for Scalable and Explainable Medical Coding](http://arxiv.org/abs/2603.29709v1) | 评测基准/环境 |  |
| 2026-03-24 | [Evaluating a Multi-Agent Voice-Enabled Smart Speaker for Care Homes: A Safety-Focused Framework](http://arxiv.org/abs/2603.23625v1) | 评测基准/环境 |  |
| 2026-02-05 | [H-AdminSim: A Multi-Agent Simulator for Realistic Hospital Administrative Workflows with FHIR Integration](http://arxiv.org/abs/2602.05407v3) | 模拟病人/医院 | Accepted at CHIL 2026 |
| 2026 | [Hard to Halt: Automation Bias in Agent-Driven Sequencing Prior Authorization Workflows.](https://pubmed.ncbi.nlm.nih.gov/42369474/) | 安全/幻觉/攻击 | medRxiv : the preprint server for health sciences |
| 2026 | [Using a large language model artificial intelligence agent to improve the efficiency of clinical quality measure evidence evaluation: a case study.](https://pubmed.ncbi.nlm.nih.gov/42020095/) | 检索/RAG/知识 | BMJ health & care informatics |
| 2025-11-17 | [MedDCR: Learning to Design Agentic Workflows for Medical Coding](http://arxiv.org/abs/2511.13361v1) | 评测基准/环境 |  |
| 2025-09-04 | [Code Like Humans: A Multi-Agent Solution for Medical Coding](http://arxiv.org/abs/2509.05378v3) | 多智能体协作 | EMNLP Findings 2025 |
| 2025 | [MedScrubCrew: A Medical Multi-Agent Framework for Automating Appointment Scheduling Based on Patient-Provider Profile Resource Matching.](https://pubmed.ncbi.nlm.nih.gov/40724673/) | 多智能体协作 | Healthcare (Basel, Switzerland) |
| 2024-04-27 | [Advancing Healthcare Automation: Multi-Agent System for Medical Necessity Justification](http://arxiv.org/abs/2404.17977v2) | 多智能体协作 | Accepted at BioNLP2024 |

## 公共卫生/流行病（14）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-23 | [Driving Epidemic Models with AI Agents: the Epydemix Agent Framework](http://arxiv.org/abs/2609.28692v1) | 其他 |  |
| 2026-09-16 | [Collective Loss of Control in LLM Agent Systems: An Epidemic Account of Mutation, Contagion, and Recovery](http://arxiv.org/abs/2609.18460v1) | 评测基准/环境 |  |
| 2026-07-08 | [A Large Language Model-Driven Agent-Based Modeling Framework with Multi-Round Communication for Simulating Vaccine Opinion Dynamics](http://arxiv.org/abs/2607.07387v1) | 模拟病人/医院 | 11 pages, 5 figures |
| 2026 | [A Multi-Agent Framework for Real-Time Sentiment Monitoring and Predictive Analysis of Public Health Policies.](https://pubmed.ncbi.nlm.nih.gov/42434700/) | 多智能体协作 | China CDC weekly |
| 2026 | [Viral Sentry AI-Automated zoonotic surveillance and drug repurposing agent.](https://pubmed.ncbi.nlm.nih.gov/42292930/) | 安全/幻觉/攻击 | Biology methods & protocols |
| 2026 | [Federated Multi-Agent Architecture for Harmonizing Public Health Datasets into OMOP and FHIR Standards.](https://pubmed.ncbi.nlm.nih.gov/42174884/) | EHR/结构化数据 | Studies in health technology and informatics |
| 2026 | [The Infectious Diseases Orchestrator: Embracing AI Literacy in the Agentic Era.](https://pubmed.ncbi.nlm.nih.gov/41502906/) | 综述/观点 | Open forum infectious diseases |
| 2025-12-11 | [EpiPlanAgent: Agentic Automated Epidemic Response Planning](http://arxiv.org/abs/2512.10313v2) | 模拟病人/医院 |  |
| 2025-09-24 | [EpidemIQs: Prompt-to-Paper LLM Agents for Epidemic Modeling and Analysis](http://arxiv.org/abs/2510.00024v2) | 综述/观点 |  |
| 2025-07-23 | [Resilient Multi-Agent Negotiation for Medical Supply Chains:Integrating LLMs and Blockchain for Transparent Coordination](http://arxiv.org/abs/2507.17134v1) | 多智能体协作 | 11 pages, 6 figure |
| 2025-07-04 | [AI-VaxGuide: An Agentic RAG-Based LLM for Vaccination Decisions](http://arxiv.org/abs/2507.03493v1) | 检索/RAG/知识 |  |
| 2025-06-10 | [Infected Smallville: How Disease Threat Shapes Sociality in LLM Agents](http://arxiv.org/abs/2506.13783v2) | 模拟病人/医院 | ICML 2025 Workshop on Multi-Agent Systems in the Era of Foun |
| 2025-03-12 | [Can A Society of Generative Agents Simulate Human Behavior and Inform Public Health Policy? A Case Study on Vaccine Hesitancy](http://arxiv.org/abs/2503.09639v4) | 模拟病人/医院 | Accepted to COLM 2025 |
| 2025 | [Advancing epidemic modeling: The role of LLMs and generative agent-based models Comment on LLMs and generative agent-based models for complex systems research by Lu et al.](https://pubmed.ncbi.nlm.nih.gov/39756195/) | 检索/RAG/知识 | Physics of life reviews |

## 药学/用药（14）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-05-27 | [SafeRx-Agent: A Knowledge-Grounded Multi-Agent Framework for Safe and Explainable Medication Recommendation](http://arxiv.org/abs/2605.29146v2) | 多智能体协作 |  |
| 2026-05-04 | [PhysicianBench: Evaluating LLM Agents in Real-World EHR Environments](http://arxiv.org/abs/2605.02240v1) | 评测基准/环境 |  |
| 2026-03-06 | [From Physician Expertise to Clinical Agents: Preserving, Standardizing, and Scaling Physicians' Medical Expertise with Lightweight LLM](http://arxiv.org/abs/2603.23520v1) | 安全/幻觉/攻击 |  |
| 2026-01-19 | [MedConsultBench: A Full-Cycle, Fine-Grained, Process-Aware Benchmark for Medical Consultation Agents](http://arxiv.org/abs/2601.12661v1) | 评测基准/环境 |  |
| 2026 | [A multi-agent GraphRAG framework for pharmacotherapy safety verification in clinical decision support systems.](https://pubmed.ncbi.nlm.nih.gov/42718584/) | 安全/幻觉/攻击 | Frontiers in medicine |
| 2026 | [Towards autonomous medical artificial intelligence agents.](https://pubmed.ncbi.nlm.nih.gov/42310457/) | 模拟病人/医院 | Nature |
| 2026 | [Pharmacovigilance Assistant: An Agentic Workflow for Reproducible Drug Safety Summaries.](https://pubmed.ncbi.nlm.nih.gov/42174782/) | 安全/幻觉/攻击 | Studies in health technology and informatics |
| 2026 | [Quantitative Systems Pharmacology Modeling Amid the Rise of Agentic AI.](https://pubmed.ncbi.nlm.nih.gov/41957555/) | 其他 | CPT: pharmacometrics & systems pharmacology |
| 2025-10-12 | [MedCoAct: Confidence-Aware Multi-Agent Collaboration for Complete Clinical Decision](http://arxiv.org/abs/2510.10461v1) | 治疗/决策支持 |  |
| 2025-07-15 | [Lessons Learned from Evaluation of LLM based Multi-agents in Safer Therapy Recommendation](http://arxiv.org/abs/2507.10911v1) | 评测基准/环境 |  |
| 2025-03-14 | [TxAgent: An AI Agent for Therapeutic Reasoning Across a Universe of Tools](http://arxiv.org/abs/2503.10970v1) | 问答/推理 | Project page: https://zitniklab.hms.harvard.edu/TxAgent TxAg |
| 2025 | [Impact of Patient Communication Style on Agentic AI-Generated Clinical Advice in E-Medicine.](https://pubmed.ncbi.nlm.nih.gov/41573348/) | 安全/幻觉/攻击 | The American journal of medicine |
| 2025 | [Agents for Change: Artificial Intelligent Workflows for Quantitative Clinical Pharmacology and Translational Sciences.](https://pubmed.ncbi.nlm.nih.gov/40055986/) | 综述/观点 | Clinical and translational science |
| 2024 | [A Conversational Agent for Early Detection of Neurotoxic Effects of Medications through Automated Intensive Observation.](https://pubmed.ncbi.nlm.nih.gov/38160267/) | 问诊/医患对话 | Pacific Symposium on Biocomputing. Pacific Symposium on Bioc |

## 眼科（13）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-06-22 | [Evo-RAD: Navigating Rare Retinal Disease Diagnosis via Self-Evolving Agentic Retrieval](http://arxiv.org/abs/2606.22955v1) | 训练方法(RL/微调) | Accepted by MICCAI 2026. 10 pages, 2 figures, 3 tables |
| 2026-03-22 | [Deliberative multi-agent large language models improve clinical reasoning in ophthalmology](http://arxiv.org/abs/2603.21447v1) | 问答/推理 |  |
| 2026 | [Performance, Failures, and Oversight of a Large Language Model Agent for Clinical Data Analysis: Evaluation Study.](https://pubmed.ncbi.nlm.nih.gov/42709964/) | 评测基准/环境 | Journal of medical Internet research |
| 2026 | [An autonomous multimodal AI agent for evidence-grounded ophthalmic diagnosis.](https://pubmed.ncbi.nlm.nih.gov/42556343/) | 诊断/鉴别诊断 | Cell reports. Medicine |
| 2026 | [GLLaucoMed: A Secure LLM-Powered Agentic Workflow for Automated Medication Extraction from Free-Text Glaucoma Clinical Notes.](https://pubmed.ncbi.nlm.nih.gov/42369494/) | 报告/文书生成 | medRxiv : the preprint server for health sciences |
| 2026 | [Toward autonomous discovery: agentic AI and the future of ophthalmic research.](https://pubmed.ncbi.nlm.nih.gov/41175385/) | 检索/RAG/知识 | Current opinion in ophthalmology |
| 2025-11-12 | [EyeAgent: An Agentic AI System for Multimodal Clinical Decision Support in Ophthalmology](http://arxiv.org/abs/2511.09394v2) | 治疗/决策支持 | 28 pages, 5 figures |
| 2025-06-09 | [MedChat: A Multi-Agent Framework for Multimodal Diagnosis with Large Language Models](http://arxiv.org/abs/2506.07400v3) | 诊断/鉴别诊断 |  |
| 2025-06-06 | [ChatMyopia: An AI Agent for Pre-consultation Education in Primary Eye Care Settings](http://arxiv.org/abs/2507.19498v1) | 问诊/医患对话 | 35 pages, 4 figures, 1 table |
| 2025 | [ChatMyopia: An AI agent for myopia-related consultation in primary eye care settings.](https://pubmed.ncbi.nlm.nih.gov/41244561/) | 问诊/医患对话 | iScience |
| 2025 | [LLM-based multi-agent system for neuro-ophthalmic diagnosis and personalized treatment planning.](https://pubmed.ncbi.nlm.nih.gov/41122382/) | 诊断/鉴别诊断 | Frontiers in neuroscience |
| 2025 | [From visual question answering to intelligent AI agents in ophthalmology.](https://pubmed.ncbi.nlm.nih.gov/40866109/) | 问答/推理 | The British journal of ophthalmology |
| 2025 | [Multimodal reasoning agent for enhanced ophthalmic decision-making: a preliminary real-world clinical validation.](https://pubmed.ncbi.nlm.nih.gov/40772224/) | 治疗/决策支持 | Frontiers in cell and developmental biology |

## 呼吸/肝肾/消化（12）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-07-10 | [From Sound to Symptom: Real-Time Respiratory Signal Understanding for Conversational Healthcare Agents](http://arxiv.org/abs/2608.26163v1) | 问诊/医患对话 | Accepted for publication at SIGDIAL 2026 |
| 2026-03-25 | [Multi-Agent Reasoning with Consistency Verification Improves Uncertainty Calibration in Medical MCQA](http://arxiv.org/abs/2603.24481v2) | 问答/推理 | 20 pages, 6 figures. Preprint under review |
| 2026-02-16 | [Resp-Agent: An Agent-Based System for Multimodal Respiratory Sound Generation and Disease Diagnosis](http://arxiv.org/abs/2602.15909v3) | 诊断/鉴别诊断 | 24 pages, 3 figures. Published as a conference paper at ICLR |
| 2026 | [Transplant-Agents: A Multi-Agent Artificial Intelligence Framework for Reproducibility Assessment of Post-Transplant Risk Prediction and Rejection Biomarkers.](https://pubmed.ncbi.nlm.nih.gov/42523221/) | 多智能体协作 | bioRxiv : the preprint server for biology |
| 2026 | [PHO-Agents: A Large Language Model-Powered Multi-Agent System for Predicting Health Outcomes.](https://pubmed.ncbi.nlm.nih.gov/42428062/) | 多智能体协作 | medRxiv : the preprint server for health sciences |
| 2026 | [Transforming hemodialysis care: a tripartite collaboration model among medical staff, AI agents, and robots.](https://pubmed.ncbi.nlm.nih.gov/42271122/) | 多智能体协作 | Clinical and experimental nephrology |
| 2026 | [A multiagent large language model-based system to simulate the liver transplant selection committee: a retrospective cohort study.](https://pubmed.ncbi.nlm.nih.gov/41951492/) | 模拟病人/医院 | The Lancet. Digital health |
| 2026 | [Codesigning a Nurse-Led, Large Language Model-Empowered Agent to Increase Hepatitis B Screening and Vaccination for Inclusion Health Populations: A Research Protocol.](https://pubmed.ncbi.nlm.nih.gov/41745899/) | 检索/RAG/知识 | Nursing reports (Pavia, Italy) |
| 2025-11-26 | [LungNoduleAgent: A Collaborative Multi-Agent System for Precision Diagnosis of Lung Nodules](http://arxiv.org/abs/2511.21042v1) | 诊断/鉴别诊断 | Accepted by AAAI 2026 |
| 2025 | [A self-correcting Agentic Graph RAG for clinical decision support in hepatology.](https://pubmed.ncbi.nlm.nih.gov/41476879/) | 治疗/决策支持 | Frontiers in medicine |
| 2025 | [Digital transformation of nephrology POCUS education-Integrating a multiagent, artificial intelligence, and human collaboration-enhanced curriculum with expert feedback.](https://pubmed.ncbi.nlm.nih.gov/40162173/) | 多智能体协作 | Digital health |
| 2024 | [New prospective insecticidal agents based on thiazolo[4,5-b]quinoxaline derivatives against cotton leafworm Spodoptera litura (Fabricius): Design, synthesis, toxicological, morphology, histological, and biomedical studies.](https://pubmed.ncbi.nlm.nih.gov/38879303/) | 其他 | Pesticide biochemistry and physiology |

## 临床试验（10）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-18 | [TrialAtlas: Multi-Agent Research Organization for Clinical Trial Design and Optimization](http://arxiv.org/abs/2609.21859v1) | 检索/RAG/知识 |  |
| 2026-09-12 | [ClinAgent: A ReAct-Based Agent for Conversational Access to Clinical Trial Information](http://arxiv.org/abs/2609.13860v1) | 问诊/医患对话 | Accepted at the CIBB 2026 conference (https://cibb2026.teral |
| 2026-07-30 | [Bridging Probabilistic LLMs and Deterministic Statistical Validation: The PROVE Multi-Agent Framework for Clinical Trial Reporting](http://arxiv.org/abs/2607.28218v1) | 报告/文书生成 |  |
| 2026-05-13 | [GxP-Agent: Process-DAG Topology for Reliable Clinical Trial Programming with LLM Agents](http://arxiv.org/abs/2608.16890v1) | 评测基准/环境 | Preprint. 9 pages main text, 3 figures, plus references and  |
| 2026-04-03 | [Eligibility-Aware Evidence Synthesis: An Agentic Framework for Clinical Trial Meta-Analysis](http://arxiv.org/abs/2604.02678v1) | 检索/RAG/知识 |  |
| 2026-03-23 | [EviSearch: Trustworthy Extraction and Synthesis of Clinical Trial Evidence with Agents that Improve with Use](http://arxiv.org/abs/2604.14165v3) | 安全/幻觉/攻击 | 12 pages, 6 figures, 3 tables. Substantially revised version |
| 2026 | [From Idea to Data: An Agentic Architecture for the Clinical Trial Life Cycle.](https://pubmed.ncbi.nlm.nih.gov/42394036/) | 检索/RAG/知识 | Studies in health technology and informatics |
| 2026 | [EC2Seq2Sql: Patient-trial matching with LLM agents.](https://pubmed.ncbi.nlm.nih.gov/41678526/) | EHR/结构化数据 | PloS one |
| 2025-06-04 | [AUTOCT: Automating Interpretable Clinical Trial Prediction with LLM Agents](http://arxiv.org/abs/2506.04293v1) | EHR/结构化数据 |  |
| 2024-04-23 | [ClinicalAgent: Clinical Trial Multi-Agent System with Large Language Model-based Reasoning](http://arxiv.org/abs/2404.14777v2) | 问答/推理 |  |

## 老年/康复/护理（9）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026 | [Human-AI co-research on design and evaluation of Embodied Conversational Agent in rehabilitation contexts.](https://pubmed.ncbi.nlm.nih.gov/41969732/) | 评测基准/环境 | Frontiers in robotics and AI |
| 2026 | [Secure and accessible AI in nursing education: A modular agentic chatbot framework comparing ChatGPT-4o with an open-source LLM for chronic wound care.](https://pubmed.ncbi.nlm.nih.gov/41905130/) | 问诊/医患对话 | Nurse education in practice |
| 2026 | [Developing a Nursing Research Education Agent Using Knowledge Graphs and Large Language Models: A Proof-of-Concept Study.](https://pubmed.ncbi.nlm.nih.gov/41521533/) | 检索/RAG/知识 | Nurse educator |
| 2026 | [A large language model-powered reflective AI agent for evidence-based nursing education: Design and evaluation.](https://pubmed.ncbi.nlm.nih.gov/41520587/) | 检索/RAG/知识 | Nurse education in practice |
| 2025-07-20 | [Redefining Elderly Care with Agentic AI: Challenges and Opportunities](http://arxiv.org/abs/2507.14912v1) | 综述/观点 |  |
| 2025-06-13 | [Large Language Model-Powered Conversational Agent Delivering Problem-Solving Therapy (PST) for Family Caregivers: Enhancing Empathy and Therapeutic Alliance Using In-Context Learning](http://arxiv.org/abs/2506.11376v1) | 问诊/医患对话 | AMIA ... Annual Symposium proceedings. AMIA Symposium |
| 2025 | [Large language model-driven agents in nursing practice: A scoping review.](https://pubmed.ncbi.nlm.nih.gov/41367594/) | 综述/观点 | International journal of nursing sciences |
| 2024-11-21 | [PIORS: Personalized Intelligent Outpatient Reception based on Large Language Model with Multi-Agents Medical Scenario Simulation](http://arxiv.org/abs/2411.13902v1) | 模拟病人/医院 |  |
| 2024 | [GPT-agents based on medical guidelines can improve the responsiveness and explainability of outcomes for traumatic brain injury rehabilitation.](https://pubmed.ncbi.nlm.nih.gov/38561445/) | 训练方法(RL/微调) | Scientific reports |

## 儿科/产科（5）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-09-28 | [Large Language Models for Structured Clinical Data Analysis: Dual-Agent Grounding and Validation](http://arxiv.org/abs/2609.34039v1) | 评测基准/环境 | 22 pages, 2 figures |
| 2026-08-30 | [SIC-Agents: Benchmarking and Building an Adaptive Simulator for Pediatric Serious Illness Communication Training](http://arxiv.org/abs/2608.29481v1) | 评测基准/环境 | Accepted to EMNLP 2026 |
| 2026-06-09 | [PATHFinder Agent for Tailored Prenatal Care](http://arxiv.org/abs/2607.24768v1) | 问诊/医患对话 | Accepted as demo at ACM Interactive Health 2026. https://rea |
| 2026-01-14 | [SafeTalkCoach: Diversity-Driven Multi-Agent Simulation for Parent-Teen Health Conversations](http://arxiv.org/abs/2602.00017v1) | 模拟病人/医院 |  |
| 2025-03-25 | [LLM-based Agent Simulation for Maternal Health Interventions: Uncertainty Estimation and Decision-focused Evaluation](http://arxiv.org/abs/2503.22719v1) | 模拟病人/医院 |  |

## 内分泌/代谢（5）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-08-31 | [DIASENTINEL: An Auditable Multi-Agent System for Guideline-Grounded Diabetes Risk Screening](http://arxiv.org/abs/2608.31128v1) | 多智能体协作 |  |
| 2026 | [CDTD-Agent: a retrieval-augmented multi-agent digital health framework for integrated diabetes care: a single-case expert-rated pilot study.](https://pubmed.ncbi.nlm.nih.gov/42819271/) | 检索/RAG/知识 | Frontiers in digital health |
| 2026 | [Responsible AI for Personalized Patient Education and Engagement Across Medical Conditions: Leveraging Multi-Agent LLMs, Ambient Technology, and NotebookLM-A Case Study in Diabetes Education and Limb Preservation.](https://pubmed.ncbi.nlm.nih.gov/42200993/) | 多智能体协作 | Journal of the American Podiatric Medical Association |
| 2025 | [Exploring the value of ChatGPT in selecting antidiabetic agents for type 2 diabetes.](https://pubmed.ncbi.nlm.nih.gov/40698399/) | 诊断/鉴别诊断 | Diabetes, obesity & metabolism |
| 2024-02-15 | [Knowledge-Infused LLM-Powered Conversational Health Agent: A Case Study for Diabetes Patients](http://arxiv.org/abs/2402.10153v2) | 问诊/医患对话 | Annual International Conference of the IEEE Engineering in M |

## 口腔（3）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-08-19 | [DentAgent: Evidence-Centric Multi-Agent Coordination for Multimodal Dental Reasoning](http://arxiv.org/abs/2608.18878v1) | 检索/RAG/知识 |  |
| 2026-03-31 | [A Safety-Aware Role-Orchestrated Multi-Agent LLM Framework for Behavioral Health Communication Simulation](http://arxiv.org/abs/2604.00249v1) | 模拟病人/医院 |  |
| 2026 | [DGADS: A graph-based agentic decision support system for precision dental question answering.](https://pubmed.ncbi.nlm.nih.gov/42385839/) | 治疗/决策支持 | Journal of dentistry |

## 皮肤（3）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026-05-14 | [DermAgent: A Self-Reflective Agentic System for Dermatological Image Analysis with Multi-Tool Reasoning and Traceable Decision-Making](http://arxiv.org/abs/2605.14403v1) | 治疗/决策支持 | MICCAI2026 early acceptance |
| 2026-03-27 | [SkinGPT-X: A Self-Evolving Collaborative Multi-Agent System for Transparent and Trustworthy Dermatological Diagnosis](http://arxiv.org/abs/2603.26122v1) | 安全/幻觉/攻击 |  |
| 2026-03-06 | [DERM-3R: A Resource-Efficient Multimodal Agents Framework for Dermatologic Diagnosis and Treatment in Real-World Clinical Settings](http://arxiv.org/abs/2604.09596v1) | 诊断/鉴别诊断 |  |

## 检验（3）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2026 | [Clinical Laboratory Terminology Standardization for Semantic Interoperability Using a Large Language Model-Based Agent: Methodological Study.](https://pubmed.ncbi.nlm.nih.gov/42623484/) | 安全/幻觉/攻击 | Journal of medical Internet research |
| 2026 | [From automation to agentic artificial intelligence in laboratory medicine: an opinion of the IFCC Division on Emerging Technologies.](https://pubmed.ncbi.nlm.nih.gov/41454792/) | 综述/观点 | Clinical chemistry and laboratory medicine |
| 2024 | [GPT-4-based AI agents-the new expert system for detection of antimicrobial resistance mechanisms?](https://pubmed.ncbi.nlm.nih.gov/39417635/) | 安全/幻觉/攻击 | Journal of clinical microbiology |

## 中医（2）

| 日期 | 标题 | 任务类型 | 出处 |
|---|---|---|---|
| 2025-02-04 | [Jingfang: An LLM-Based Multi-Agent System for Precise Medical Consultation and Syndrome Differentiation in Traditional Chinese Medicine](http://arxiv.org/abs/2502.04345v3) | 问诊/医患对话 |  |
| 2025 | [Integrating knowledge graphs with ancient Chinese medicine classics: challenges and future prospects of multi-agent system convergence.](https://pubmed.ncbi.nlm.nih.gov/41057976/) | 综述/观点 | Chinese medicine |
