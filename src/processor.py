import fitz  # PyMuPDF
import os
import json

def pdf_to_markdown(pdf_path, md_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    
    # Simple heuristic to clean up and format as MD
    # In a real scenario, we'd use better layout analysis.
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(text)

def process_all_pdfs(pdf_dir='data/pdfs', md_dir='data/markdown'):
    if not os.path.exists(md_dir):
        os.makedirs(md_dir)
        
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, filename)
            md_path = os.path.join(md_dir, filename.replace('.pdf', '.md'))
            
            if os.path.exists(md_path):
                continue
                
            print(f"Processing {filename}...")
            pdf_to_markdown(pdf_path, md_path)

if __name__ == "__main__":
    process_all_pdfs()
