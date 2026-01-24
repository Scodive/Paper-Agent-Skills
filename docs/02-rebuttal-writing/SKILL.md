---
name: rebuttal-writing
description: Generate professional, persuasive responses to reviewer comments for top-tier AI conferences
version: 1.0.0
tags: [rebuttal, peer-review, negotiation, academic-writing]
---

# Rebuttal Writing Skill

## Metadata
- **Skill Name**: `rebuttal-writing`
- **Purpose**: Address reviewer concerns effectively to flip scores from Reject to Accept.
- **Target Venues**: NeurIPS, ICLR, CVPR, ICML
- **Key Principle**: Be polite, be specific, and provide new evidence.

## When to Use This Skill

- When you receive reviews from a conference submission.
- When drafting a "Author Response" or "Rebuttal" document.
- To analyze whether a reviewer misunderstood a claim or identified a genuine flaw.

## Critical Rules

### 1. Tone Management
- **Never** be defensive or aggressive.
- **Always** thank the reviewer for their time and constructive feedback.
- Use "We appreciate the reviewer's insight" instead of "The reviewer is wrong".

### 2. Evidence First
- Do not just argue; show results.
- If a reviewer asks for a baseline, run it (or explain clearly why it's impossible/irrelevant with cited reasons).

## Core Workflows

### Workflow 1: Rebuttal Generation

**Input**: Review text, Paper PDF
**Output**: Point-by-point rebuttal draft

1. **Deconstruct the Review**
   - Split the review into distinct points (major vs. minor).
   - Classify each point: "Misunderstanding", "Valid Limitation", "Request for Experiment", "Suggestion".

2. **Draft Responses**
   - **Misunderstanding**: "We apologize for the confusion. We clarify that..." (Point to specific lines in paper).
   - **Valid Limitation**: "We acknowledge this limitation and have added a discussion in Section X."
   - **Experiment**: "Per the reviewer's suggestion, we ran Exp Y. Results in Table R show..."

3. **Synthesize**
   - Combine into a cohesive narrative if the conference allows a general response.

## Learned Patterns (From Successful Rebuttals)

### Pattern 1: The "I Agree, But..." (Agreement + Pivot)
reviewer: "The method is computationally expensive."
response: "We agree that computational cost is an important factor. However, we note that our method's inference time is comparable to [SOTA] (Table 2), and the training cost is a one-time expense amortized over usage."

### Pattern 2: The "Hidden Detail" (Pointing to Text)
reviewer: "It is unclear how X works."
response: "We thank the reviewer for pointing this out. As described in Section 3.2 (Lines 145-150), X functions by..."

## Style Guidelines

- **Conciseness**: Reviewers are busy. Get to the point.
- **Visuals**: If allowed, refer to new figures/tables included in the rebuttal.
- **Structure**:
  - **R1 (Score: 6 -> 8)**: "Thank you..."
    - **Q1**: Response.
    - **Q2**: Response.

## Quick Start Example

```markdown
**R1 Q1: Comparison with [A]**
Result: We have added the comparison with [A].
Table:
| Method | Acc |
| [A]    | 85% |
| Ours   | 88% |
Discussion: Ours outperforms [A] by 3%...
```
