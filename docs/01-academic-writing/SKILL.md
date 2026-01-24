---
name: academic-paper-writing
description: Write publication-ready research papers for top-tier conferences (NeurIPS, ICLR, CVPR) by learning from Best Paper/Oral/Spotlight winners
version: 1.0.0
author: Paper-Agent
tags: [academic-writing, research, NeurIPS, ICLR, CVPR, best-paper]
---

# Academic Paper Writing Skill

## 📋 Metadata
- **Skill Name**: `academic-paper-writing`
- **Purpose**: Generate high-quality research papers by learning structural, rhetorical, and argumentative patterns from top-tier conference papers
- **Target Venues**: NeurIPS, ICLR, CVPR, ICML, ACL
- **Quality Level**: Best Paper / Oral / Spotlight standard

## 🎯 When to Use This Skill

Use this skill when you need to:
- Transform a research idea into a complete paper draft
- Structure your paper following proven patterns from award-winning papers
- Write compelling introductions that set up the problem and contributions
- Craft clear and logical method sections
- Present experimental results with proper argumentation
- Ensure your writing style matches top-tier publication standards

## ⚠️ CRITICAL RULES

### Never Hallucinate Citations
**WRONG** ❌: Generating fake references like "Smith et al. (2023). Deep Learning Advances. arXiv:2301.12345"
**CORRECT** ✅: Only cite papers that you have verified exist via:
- ArXiv API search
- Semantic Scholar API
- User-provided bibliography

### Always Follow the Learned Patterns
The skills extracted from top papers are battle-tested. Don't deviate without good reason.

## 🔄 Core Workflows

### Workflow 1: Generate Paper from Idea

**Input**: A research idea (1-2 sentences)
**Output**: Complete paper draft with all sections

**Steps**:
1. **Idea Expansion** (5 minutes)
   ```bash
   # Use the idea_expander.py script
   python3 paper_agent/idea_expander.py --idea "Your research idea here"
   ```
   - Identify the core problem
   - List potential contributions
   - Suggest related work areas

2. **Outline Generation** (10 minutes)
   - Apply structural patterns from `data/skills_base.json`
   - Create section-by-section outline
   - Define key messages for each section

3. **Section-by-Section Drafting** (Iterative)
   ```bash
   # Draft each section using learned rhetorical patterns
   python3 paper_agent/generator.py --section abstract --outline outline.json
   python3 paper_agent/generator.py --section introduction --outline outline.json
   python3 paper_agent/generator.py --section method --outline outline.json
   # ... continue for all sections
   ```

4. **Refinement** (20 minutes)
   - Check logical flow between sections
   - Ensure contributions are clearly stated
   - Verify experimental claims are supported

### Workflow 2: Learn New Skills from Papers

**Input**: PDF of a top-tier paper
**Output**: Updated skills database

**Steps**:
1. Convert PDF to Markdown
   ```bash
   python3 paper_agent/processor.py --pdf path/to/paper.pdf
   ```

2. Extract writing skills
   ```bash
   python3 paper_agent/skills_analyzer.py --md path/to/paper.md
   ```

3. Update skills base
   ```bash
   # Skills are automatically appended to data/skills_base.json
   ```

### Workflow 3: Refine Existing Draft

**Input**: Your draft paper (LaTeX or Markdown)
**Output**: Improved draft with suggestions

**Steps**:
1. Analyze current draft against learned patterns
2. Identify gaps in argumentation
3. Suggest improvements for each section
4. Regenerate weak sections

## 📚 Learned Writing Patterns

### Pattern 1: Introduction Structure (from ICLR Best Papers)

**Hook → Gap → Approach → Contributions**

```
1. Opening Hook (1-2 sentences)
   - State the broad problem or exciting opportunity
   - Example: "Large language models have revolutionized NLP, but their computational cost remains prohibitive for many applications."

2. Gap Setting (2-3 sentences)
   - Identify what's missing in current solutions
   - Example: "While quantization reduces model size, existing methods suffer from significant accuracy degradation on complex reasoning tasks."

3. Our Approach (2-3 sentences)
   - Introduce your method at a high level
   - Example: "We propose AdaptQuant, a training-free quantization method that preserves reasoning capabilities by..."

4. Contributions (Bulleted list)
   - List 3-4 concrete contributions
   - Be specific about what's novel
```

### Pattern 2: Method Section Flow

**Overview → Components → Algorithm → Analysis**

```
1. Method Overview (1 paragraph)
   - High-level description
   - Key intuition

2. Component Breakdown (2-3 subsections)
   - Each component gets its own subsection
   - Include mathematical formulation
   - Provide intuitive explanation

3. Algorithm (Pseudocode or detailed steps)
   - Make it reproducible
   - Highlight key design choices

4. Theoretical Analysis (Optional but strong)
   - Complexity analysis
   - Theoretical guarantees
```

### Pattern 3: Experimental Argumentation

**Setup → Main Results → Ablations → Analysis**

```
1. Experimental Setup (1 subsection)
   - Datasets
   - Baselines
   - Metrics
   - Implementation details

2. Main Results (Tables + Analysis)
   - Lead with your strongest result
   - Compare against all baselines
   - Highlight key takeaways in text

3. Ablation Studies
   - Justify each design choice
   - Show what happens when you remove components

4. Qualitative Analysis
   - Case studies
   - Visualizations
   - Error analysis
```

## 🎨 Style Guidelines (from Top Papers)

### Vocabulary
- **Prefer**: "We propose", "Our method", "We demonstrate"
- **Avoid**: "We believe", "We think", "Obviously"

### Sentence Structure
- Average length: 15-20 words
- Mix short (impact) and long (detail) sentences
- Use active voice for your contributions
- Use passive voice for background/related work

### Paragraph Flow
- First sentence: Topic sentence (what this paragraph is about)
- Middle sentences: Supporting details
- Last sentence: Transition or conclusion

### Common Phrases from Best Papers
- "Building on this insight, we..."
- "To address this limitation, we propose..."
- "Our key observation is that..."
- "This suggests that..."
- "We empirically find that..."

## 📊 Conference-Specific Requirements

| Conference | Page Limit | Key Focus | Review Criteria |
|------------|------------|-----------|-----------------|
| NeurIPS | 9 pages | Novelty + Theory | Soundness, Significance, Clarity |
| ICLR | 9 pages | Empirical + Reproducibility | Originality, Quality, Clarity |
| CVPR | 8 pages | Visual Results | Technical Quality, Novelty |
| ICML | 8 pages | Theory + Experiments | Correctness, Significance |

## 🔗 Deep Dive Resources

For detailed guidance on specific topics, see:
- [LaTeX Templates](./references/latex_templates.md) - Conference-specific templates
- [Citation Guidelines](./references/citations.md) - How to properly cite and verify references
- [Figure Design](./references/figures.md) - Creating publication-quality figures
- [Rebuttal Writing](./references/rebuttal.md) - Responding to reviewer comments

## 🚀 Quick Start Example

```bash
# 1. Set your research idea
export IDEA="A new attention mechanism that reduces computational complexity from O(n²) to O(n log n)"

# 2. Generate outline
python3 paper_agent/main.py --mode outline --idea "$IDEA"

# 3. Generate full draft
python3 paper_agent/main.py --mode draft --outline output/outline.json

# 4. Review and refine
python3 paper_agent/main.py --mode refine --draft output/draft.md
```

## 📈 Success Metrics

A good paper generated with this skill should:
- [ ] Have a clear problem statement in the first paragraph
- [ ] List 3-4 concrete contributions
- [ ] Include proper related work comparison
- [ ] Present reproducible experimental setup
- [ ] Show ablation studies for key design choices
- [ ] Have no hallucinated citations
- [ ] Follow the structural patterns of top papers

## 🔄 Version History

- **v1.0.0** (2026-01-24): Initial release with patterns from ICLR 2024 Best Papers
