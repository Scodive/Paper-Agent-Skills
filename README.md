# Paper-Agent-Skills

A comprehensive library of AI agent skills for academic research and writing, designed to be used by autonomous agents to generate high-quality research outputs.

## Overview

This repository uses a skill-based architecture to teach AI agents how to perform complex research tasks. Instead of generic prompting, we extract concrete, reusable patterns from top-tier conference papers (NeurIPS, ICLR, CVPR) and encapsulate them into "Skills".

## Repository Structure

```
.
├── docs/                       # Skill definitions
│   ├── 01-academic-writing/    # Writing publication-ready papers
│   ├── 02-rebuttal-writing/    # Responding to reviewer comments
│   └── 03-presentation-slides/ # Creating conference presentations
├── src/                        # Core implementation python scripts
├── data/                       # Knowledge base (extracted skills, metadata)
└── references/                 # Templates and detailed guides
```

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API Key (for skill extraction and generation)

### Installation

```bash
pip install -r requirements.txt
```

### Usage

#### 1. Build the Skills Database

Collect data from top papers and extract writing patterns:

```bash
python3 src/scraper.py
python3 src/downloader.py
python3 src/processor.py
python3 src/skills_analyzer.py --build
```

#### 2. Generate a Paper

Use the extracted skills to write a new paper from an idea:

```bash
# Generate outline
python3 src/main.py --mode outline --idea "Your research idea"

# Generate draft
python3 src/main.py --mode draft --outline output/outline.json

# Refine draft
python3 src/main.py --mode refine --draft output/draft.md
```

## Available Skills

### Academic Writing
- **Purpose**: Transform research ideas into full paper drafts.
- **Source**: Learned from Best Paper and Oral awards.
- **Key Features**: Structural templates, rhetorical pattern matching, argument verification.

### Rebuttal Writing
- **Purpose**: Generate professional responses to reviewer critiques.
- **Key Features**: Tone management, point-by-point addressing logic.

### Presentation Slides
- **Purpose**: Convert papers into slide decks for conferences.
- **Key Features**: Key point extraction, visual hierarchy planning.

## License

MIT License
