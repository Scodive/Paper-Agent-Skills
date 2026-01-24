import os
import json
import requests
from tqdm import tqdm

def download_pdfs(metadata_file='data/paper_metadata.json', output_dir='data/pdfs'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(metadata_file, 'r') as f:
        papers = json.load(f)
        
    for paper in tqdm(papers, desc="Downloading PDFs"):
        title = paper['title'].replace('/', '_').replace(' ', '_')[:50]
        pdf_path = os.path.join(output_dir, f"{paper['id']}_{title}.pdf")
        
        if os.path.exists(pdf_path):
            continue
            
        try:
            response = requests.get(paper['pdf_url'], stream=True)
            if response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                print(f"Failed to download {paper['title']}: Status {response.status_code}")
        except Exception as e:
            print(f"Error downloading {paper['title']}: {e}")

if __name__ == "__main__":
    download_pdfs()
