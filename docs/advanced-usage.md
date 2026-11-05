# 详细使用说明

[返回首页](../README.md)。下列命令均在仓库根目录运行。

基于真实材料的科研写作技能与本地校验工具。输入论文、实验记录和参考文献，
由当前会话中的 Agent 审阅，输出修改建议、修订稿、逐条修改差异与检查报告。

**不需要创建 API 密钥。** Python 程序负责材料快照、全文分块、接口校验和修订
应用；当前会话的 Agent 负责推理与写作。程序不会在后台调用模型、检索引用或
运行实验，也不会自动从终端反向调用当前聊天。可由其他 Agent 通过同一 JSON
接口提交审阅结果。本版已移除旧的硬编码模型与“假设结果直接生成正文”流程。

## 安装与快速验证

Python 3.10+：

```bash
python3 -m pip install -e .
python3 src/main.py validate-skills
python3 -m unittest discover -s tests -v
python3 examples/revision/demo.py --out output/demo-01
```

安装后可将 `python3 src/main.py` 换成 `paper-agent`；未安装时可直接从仓库运行。
PDF 输入需要 PyMuPDF，技能读取需要 PyYAML。采集脚本的额外依赖可通过
`python3 -m pip install -e '.[collection]'` 或 `requirements.txt` 安装。

演示重放 `examples/revision/response_fixture.json` 中预先由宿主 Agent 审阅的
答案，用当前材料包 ID 绑定后执行校验。论文及实验数据明确标为**合成测试样例**；
演示不是运行了一次新模型，也不代表真实科研效果。其引用书目包含一篇真实论文，
本地程序仍将书目身份与引用支持标为未独立核验。

## 完整修订流程

### 1. 整理材料

```bash
python3 src/main.py prepare \
  --paper /path/to/paper.tex \
  --experiments /path/to/results.csv \
  --references /path/to/references.bib \
  --out runs/review-01
```

支持 Markdown、文本、单文件 TeX 与有文字层的 PDF；实验支持 JSON/CSV；
参考文献支持 JSON/BibTeX。格式见 [输入说明](input-formats.md)。
未提供实验或书目时可以审阅，但缺失证据会明确记录，不能生成已完成的结果。

`runs/review-01/` 包含原始材料字节快照及 SHA-256、`manuscript.txt` 全文、
带行号与 PDF 页码映射的材料索引、完整分块、实际加载的技能文件、基线检查、
`agent_task.md` 和 `response.schema.json`。全文和附录均不会按字符数截断。

### 2. 让当前 Agent 执行审阅

在本会话或其他具有本地文件访问权限的 Agent 中发送：

> 读取 runs/review-01/agent_task.md，加载包内技能，审阅全部材料，按
> response.schema.json 写出 runs/review-01/response.json，再执行 apply 和 check。
> 不要补造缺失实验和引用。

Agent 需要提交：带原稿行号的建议与待办状态、论点和证据对应关系、全部分块的
阅读声明，以及带精确原文的逐行修改。JSON 是显式模型接口，无需特定模型 SDK。
阅读覆盖率是 Agent 的声明，程序不能证明 Agent 确实读完；结论仍需作者审阅。

### 3. 校验并产出修订稿

```bash
python3 src/main.py apply --run runs/review-01 --response runs/review-01/response.json
python3 src/main.py check --run runs/review-01
```

`results/` 输出：

- `revised.md` 或 `revised.tex`：应用经过校验的修改；原始论文保持不变。
- `suggestions.md` / `suggestions.json`：修改建议、证据定位和未解决事项。
- `claim_evidence.json`：基于原稿行号的论点判断及来源 ID。
- `changes.diff`：精确修改差异。
- `checks.md` / `checks.json`：原稿与修订稿检查、材料局限、待办事项。
- `response.json` / `manifest.json`：已校验的 Agent 答案和产物哈希。

未知证据 ID、过期原文、重叠修改、遗漏全文分块、新增未解析引用，以及缺少所引
已完成记录/来源摘录支持的新数字会被拒绝。百分数与小数的转换按记录单位检查。
`check` 会重验快照、重放修改并重算检查结果；不会静默覆盖已有任务或结果目录。
再次修订可用新目录，或 `apply --out runs/review-01/revision-02`。

默认 `check` 返回 0 表示检查成功执行，**不表示论文通过科学性验证**。
`--fail-on-findings` 在尚未完成 Agent 审阅、存在机械检查问题或未解决建议时返回 1；无效材料、
答案或快照返回 2。无 Agent 答案时状态为 `prepared_awaiting_agent_review`。

## 三个实际加载的技能

技能随 Python 包分发，默认由程序按名称加载与快照，不再只是未接入的文档。
可使用 `prepare --skills-dir PATH` 指定符合相同目录规范的技能根目录。

- [academic-paper-writing](../src/paper_agent/skills/academic-paper-writing/SKILL.md)：基于材料的论文修订，以及显式缺少证据的规划。
- [rebuttal-writing](../src/paper_agent/skills/rebuttal-writing/SKILL.md)：逐条审稿回复与任务跟踪。
- [presentation-slides](../src/paper_agent/skills/presentation-slides/SKILL.md)：带来源定位的演讲分镜与讲稿。

```bash
python3 src/main.py outline --idea "Your research hypothesis" --out runs/outline-01
python3 src/main.py draft --outline outline.json --out runs/draft-01
python3 src/main.py rebuttal --paper paper.md --reviews reviews.txt --out runs/rebuttal-01
python3 src/main.py slides --paper paper.pdf --out runs/slides-01
```

这些命令导出完整输入和已加载技能，等待宿主 Agent 生成对应成果。Slides 输出
目标是分镜文档，不是 PPTX。Outline/Draft 不会把研究假设伪装成已验证论文。
旧 `--mode outline/draft/refine` 参数保留为任务导出兼容入口；`refine --draft`
转到 `prepare --paper`，仍可附加 `--experiments`、`--references`、`--out`。

## 从论文提取可复用写作模式

```bash
python3 src/scraper.py --venue ICLR.cc/2024/Conference --category oral --limit 5
python3 src/downloader.py
python3 src/processor.py
python3 src/skills_analyzer.py --build --metadata data/paper_metadata.json
```

年份由调用方明确选择。采集器先检查录用 venueid，再查找类别的实际元数据或
Decision 依据；找不到 Oral/Spotlight/Best Paper 证据时不猜测、不取前几篇冒充。
不同会议的奖项发布方式不同，因此可能没有对应类别结果。下载有超时、大小限制
与临时文件发布；PDF 处理保留全页文本及来源 sidecar。

`--build` 现在导出全文模式提取任务，而非自动调用 API。宿主 Agent 读取各任务的
`agent_task.md` 并写出包含原文引句和行号的 `response.json` 后，显式导入：

```bash
python3 src/skills_analyzer.py --import-response data/skill_tasks/paper-0001/response.json \
  --task data/skill_tasks/paper-0001 --out-file data/skills_base.json
python3 src/main.py prepare --paper paper.md --experiments results.csv --references refs.bib \
  --patterns data/skills_base.json --out runs/review-with-patterns
```

导入验证引句与行号，保留既有数据库记录并去除重复导入。学习模式进入审阅上下文，
但只能作为有适用条件的写作范例，不能作为实验或引用的科学证据。
单篇入口支持 `processor.py --pdf paper.pdf --out paper.md` 与
`skills_analyzer.py --md paper.md --out-dir data/single-task`。

## 当前边界

数值一致、引用键可解析，都不等于科学论点已获得支持。程序的词法检查可能漏报
或误报；数据集、划分、指标语义、统计显著性、因果性、创新性和用户记录真实性
需要 Agent 与作者判断。外部日志定位符只记录，不读取或执行；实验不会被复现。
引用真实性和引用支持不通过联网自动核验。报告明确保留这些未验证状态。

PDF 修订输出为提取文本的 Markdown，不保留原版排版；表格、公式、图片需要对照
原 PDF 检查。扫描页需先 OCR，多文件 TeX 需先展平。本版不含 LaTeX 编译、PPTX
渲染或论文录用预测。会议要求应按年份、阶段和官方来源核查。

MIT License applies to this repository's code and skills. Collected papers retain
their authors' licenses and are kept in ignored local directories.
