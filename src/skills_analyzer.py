import os
import json
import litellm

def analyze_paper_writing_skills(md_content, paper_title=""):
    """
    Uses an LLM to analyze the writing style and structure of a paper.
    Extracts concrete, actionable patterns that can be reused.
    """
    prompt = f"""
You are an expert academic writing consultant analyzing a top-tier research paper.

PAPER: {paper_title}
CONTENT (first 10000 chars):
{md_content[:10000]}

Extract concrete, reusable writing patterns in JSON format:

{{
    "structural_patterns": {{
        "introduction_flow": "Describe the exact flow (e.g., 'Hook with broad impact → Identify specific gap → Preview approach → List 3 contributions')",
        "method_organization": "How is the method section organized?",
        "experiment_structure": "How are experiments presented?"
    }},
    "rhetorical_moves": {{
        "problem_motivation": ["List 2-3 exact phrases used to motivate the problem"],
        "gap_identification": ["List 2-3 exact phrases used to identify gaps"],
        "contribution_phrasing": ["List 2-3 exact phrases used to state contributions"],
        "result_presentation": ["List 2-3 exact phrases used to present results"]
    }},
    "argumentation_logic": {{
        "claim_to_evidence": "How do they link claims to experimental evidence?",
        "ablation_strategy": "How do they justify design choices?",
        "limitation_handling": "How do they address limitations?"
    }},
    "style_guide": {{
        "sentence_length": "Average sentence length (short/medium/long)",
        "voice_usage": "When do they use active vs passive voice?",
        "paragraph_structure": "Typical paragraph length and organization",
        "transition_phrases": ["List 3-5 transition phrases used between sections/ideas"]
    }},
    "key_phrases": [
        "List 10-15 impactful phrases that could be reused (e.g., 'Building on this insight', 'Our key observation is that')"
    ]
}}

Focus on CONCRETE, REUSABLE patterns, not generic advice.
Return ONLY valid JSON.
"""
    
    try:
        response = litellm.completion(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result['source_paper'] = paper_title
        return result
    except Exception as e:
        print(f"Error during analysis: {e}")
        return None

def build_skills_base(md_dir='data/markdown', out_file='data/skills_base.json'):
    """
    Analyze all papers in the markdown directory and build a skills database.
    """
    skills_base = []
    
    if not os.path.exists(md_dir):
        print(f"Error: {md_dir} does not exist. Run scraper.py and processor.py first.")
        return
    
    md_files = [f for f in os.listdir(md_dir) if f.endswith('.md')]
    
    if not md_files:
        print(f"No markdown files found in {md_dir}")
        return
    
    for filename in md_files:
        print(f"📖 Analyzing {filename}...")
        with open(os.path.join(md_dir, filename), 'r', encoding='utf-8') as f:
            content = f.read()
            skills = analyze_paper_writing_skills(content, paper_title=filename)
            if skills:
                skills_base.append(skills)
                print(f"   ✅ Extracted skills from {filename}")
            else:
                print(f"   ❌ Failed to extract skills from {filename}")
    
    # Save skills base
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w') as f:
        json.dump(skills_base, f, indent=2)
    
    print(f"\n✅ Skills base built with {len(skills_base)} papers.")
    print(f"📁 Saved to: {out_file}")
    
    # Print summary
    print("\n📊 Skills Summary:")
    for skill in skills_base:
        print(f"  - {skill.get('source_paper', 'Unknown')}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        # Build skills from all papers in data/markdown
        build_skills_base()
    else:
        print("Usage:")
        print("  python3 paper_agent/skills_analyzer.py --build")
        print("\nThis will analyze all papers in data/markdown/ and create data/skills_base.json")
        print("\nNote: Requires OPENAI_API_KEY environment variable")

