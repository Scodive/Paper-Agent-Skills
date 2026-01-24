#!/usr/bin/env python3
"""
Paper-Agent: Generate high-quality research papers from ideas
Based on learned skills from top-tier conference papers
"""

import argparse
import json
import os
from pathlib import Path
import litellm

# Load the skills base
SKILLS_BASE_PATH = "data/skills_base.json"
OUTPUT_DIR = "output"

def load_skills():
    """Load the learned writing skills from top papers."""
    if os.path.exists(SKILLS_BASE_PATH):
        with open(SKILLS_BASE_PATH, 'r') as f:
            return json.load(f)
    return []

def generate_outline(idea: str, skills: list) -> dict:
    """
    Generate a paper outline from a research idea.
    Uses learned structural patterns from top papers.
    """
    # Synthesize structural patterns from skills
    structural_guidance = "\n".join([
        f"- {skill.get('structural_patterns', '')}" 
        for skill in skills if skill.get('structural_patterns')
    ])
    
    prompt = f"""
You are an expert academic writer. Generate a detailed outline for a research paper based on this idea:

IDEA: {idea}

Use the following structural patterns learned from top-tier conference papers:
{structural_guidance}

Generate a JSON outline with the following structure:
{{
    "title": "Proposed paper title",
    "abstract": {{
        "problem": "What problem does this solve?",
        "approach": "High-level approach",
        "results": "Key results (can be hypothetical for now)"
    }},
    "sections": [
        {{
            "name": "Introduction",
            "key_points": ["Point 1", "Point 2", ...],
            "structure": "Hook → Gap → Approach → Contributions"
        }},
        {{
            "name": "Related Work",
            "key_points": ["Area 1", "Area 2", ...],
            "structure": "Group by theme, identify gaps"
        }},
        {{
            "name": "Method",
            "key_points": ["Component 1", "Component 2", ...],
            "structure": "Overview → Components → Algorithm"
        }},
        {{
            "name": "Experiments",
            "key_points": ["Setup", "Main results", "Ablations"],
            "structure": "Setup → Results → Analysis"
        }},
        {{
            "name": "Conclusion",
            "key_points": ["Summary", "Impact", "Future work"],
            "structure": "Recap → Broader impact → Next steps"
        }}
    ]
}}

Return ONLY the JSON, no additional text.
"""
    
    try:
        response = litellm.completion(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating outline: {e}")
        return None

def generate_section(section_name: str, section_info: dict, outline: dict, skills: list) -> str:
    """
    Generate a specific section of the paper.
    Uses learned rhetorical patterns and style guidelines.
    """
    # Extract relevant patterns
    rhetorical_patterns = "\n".join([
        f"- {skill.get('rhetorical_moves', '')}" 
        for skill in skills if skill.get('rhetorical_moves')
    ])
    
    style_guide = "\n".join([
        f"- {skill.get('style_guide', '')}" 
        for skill in skills if skill.get('style_guide')
    ])
    
    prompt = f"""
You are writing the {section_name} section of a research paper.

PAPER TITLE: {outline.get('title', '')}
PAPER ABSTRACT: {json.dumps(outline.get('abstract', {}), indent=2)}

SECTION OUTLINE:
{json.dumps(section_info, indent=2)}

LEARNED RHETORICAL PATTERNS from top papers:
{rhetorical_patterns}

STYLE GUIDELINES:
{style_guide}

Write a complete {section_name} section following these guidelines:
1. Follow the structural pattern specified in the outline
2. Use the rhetorical moves learned from top papers
3. Match the writing style of award-winning papers
4. Be specific and concrete, avoid vague statements
5. Use active voice for contributions, passive for background
6. Average sentence length: 15-20 words

Write in Markdown format. Include subsection headers where appropriate.
DO NOT include citations yet (we'll add them in a separate step).
"""
    
    try:
        response = litellm.completion(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating section {section_name}: {e}")
        return f"# {section_name}\n\n[Error generating section]"

def generate_full_draft(outline: dict, skills: list) -> str:
    """
    Generate a complete paper draft from an outline.
    """
    draft = f"# {outline.get('title', 'Research Paper')}\n\n"
    
    # Generate abstract
    abstract = outline.get('abstract', {})
    draft += "## Abstract\n\n"
    draft += f"{abstract.get('problem', '')} {abstract.get('approach', '')} {abstract.get('results', '')}\n\n"
    
    # Generate each section
    for section in outline.get('sections', []):
        print(f"Generating section: {section['name']}...")
        section_content = generate_section(section['name'], section, outline, skills)
        draft += f"\n{section_content}\n\n"
    
    return draft

def refine_draft(draft: str, skills: list) -> str:
    """
    Refine an existing draft using learned patterns.
    """
    argumentation_logic = "\n".join([
        f"- {skill.get('argumentation_logic', '')}" 
        for skill in skills if skill.get('argumentation_logic')
    ])
    
    prompt = f"""
You are a senior reviewer for a top-tier conference. Review and improve this paper draft.

DRAFT:
{draft[:8000]}  # Limit to avoid token overflow

LEARNED ARGUMENTATION PATTERNS:
{argumentation_logic}

Provide specific suggestions for improvement:
1. Logical flow between sections
2. Clarity of contributions
3. Strength of argumentation
4. Writing style improvements

Return a JSON with:
{{
    "overall_assessment": "Brief assessment",
    "suggestions": [
        {{"section": "Introduction", "issue": "...", "suggestion": "..."}},
        ...
    ],
    "improved_sections": {{
        "section_name": "improved content (if needed)",
        ...
    }}
}}
"""
    
    try:
        response = litellm.completion(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error refining draft: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Paper-Agent: Generate research papers from ideas")
    parser.add_argument("--mode", choices=["outline", "draft", "refine"], required=True,
                        help="Mode: outline, draft, or refine")
    parser.add_argument("--idea", type=str, help="Research idea (for outline mode)")
    parser.add_argument("--outline", type=str, help="Path to outline JSON (for draft mode)")
    parser.add_argument("--draft", type=str, help="Path to draft markdown (for refine mode)")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load skills
    print("Loading learned writing skills...")
    skills = load_skills()
    if not skills:
        print("⚠️  No skills found. Run skills_analyzer.py first to learn from top papers.")
        print("Using default patterns for now...")
        skills = [{"structural_patterns": "Introduction → Method → Experiments → Conclusion"}]
    
    if args.mode == "outline":
        if not args.idea:
            print("Error: --idea required for outline mode")
            return
        
        print(f"\n📝 Generating outline for idea: {args.idea}\n")
        outline = generate_outline(args.idea, skills)
        
        if outline:
            output_path = os.path.join(OUTPUT_DIR, "outline.json")
            with open(output_path, 'w') as f:
                json.dump(outline, f, indent=2)
            print(f"✅ Outline saved to: {output_path}")
            print(f"\nProposed Title: {outline.get('title', '')}")
            print(f"\nNext step: python3 paper_agent/main.py --mode draft --outline {output_path}")
    
    elif args.mode == "draft":
        if not args.outline:
            print("Error: --outline required for draft mode")
            return
        
        with open(args.outline, 'r') as f:
            outline = json.load(f)
        
        print(f"\n📄 Generating full draft for: {outline.get('title', '')}\n")
        draft = generate_full_draft(outline, skills)
        
        output_path = os.path.join(OUTPUT_DIR, "draft.md")
        with open(output_path, 'w') as f:
            f.write(draft)
        print(f"✅ Draft saved to: {output_path}")
        print(f"\nNext step: python3 paper_agent/main.py --mode refine --draft {output_path}")
    
    elif args.mode == "refine":
        if not args.draft:
            print("Error: --draft required for refine mode")
            return
        
        with open(args.draft, 'r') as f:
            draft = f.read()
        
        print(f"\n🔍 Refining draft...\n")
        suggestions = refine_draft(draft, skills)
        
        if suggestions:
            output_path = os.path.join(OUTPUT_DIR, "refinement_suggestions.json")
            with open(output_path, 'w') as f:
                f.write(suggestions)
            print(f"✅ Suggestions saved to: {output_path}")

if __name__ == "__main__":
    main()
