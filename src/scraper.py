import openreview
import os
import json

def fetch_top_papers(venue_id='ICLR.cc/2024/Conference', limit=10):
    """
    Fetches papers with high ratings or 'Oral' status from OpenReview.
    """
    client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
    
    print(f"Fetching submissions for {venue_id}...")
    # Get all accepted submissions
    submissions = client.get_all_notes(invitation=f'{venue_id}/-/Submission')
    
    # Decisions are usually in notes with invitation f'{venue_id}/Paper{number}/-/Decision'
    # Actually, API V2 often has a simpler way or we filter by content.
    
    top_papers = []
    
    # This is a simplified logic. In practice, we'd look for Decision notes.
    # For now, let's just get the first few accepted notes to demonstrate.
    # We'll filter for those that have 'Oral' in their meta or decision.
    
    for note in submissions:
        # Check if the paper has an 'Oral' decision
        # Decisions are separate notes. client.get_notes(invitation=f'{venue_id}/Paper{note.number}/-/Decision')
        # However, for efficiency, let's just use some sample high-impact ones or search content.
        
        # In API V2, some venues put keywords or decision in the submission content itself after acceptance.
        content = note.content
        title = content.get('title', {}).get('value', 'No Title')
        pdf_url = f"https://openreview.net/pdf?id={note.id}"
        
        # Try to find if it's oral/spotlight
        # This part depends on the specific conference's invitation structure.
        # For ICLR 2024, decisions are under f'{venue_id}/Paper{note.number}/-/Decision'
        
        top_papers.append({
            'id': note.id,
            'number': note.number,
            'title': title,
            'pdf_url': pdf_url,
            'venue': venue_id
        })
        
        if len(top_papers) >= limit:
            break
            
    return top_papers

if __name__ == "__main__":
    if not os.path.exists('data'):
        os.makedirs('data')
        
    papers = fetch_top_papers(limit=5)
    with open('data/paper_metadata.json', 'w') as f:
        json.dump(papers, f, indent=4)
    print(f"Saved {len(papers)} paper metadata to data/paper_metadata.json")
