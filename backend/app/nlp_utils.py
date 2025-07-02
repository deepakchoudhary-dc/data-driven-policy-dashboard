from transformers import pipeline

summarizer = pipeline('summarization', model='facebook/bart-large-cnn')

def summarize_text(text: str) -> str:
    if not text.strip():
        return ''
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    return summary[0]['summary_text']

def extract_policies(text: str) -> list:
    # Placeholder: Use regex/NLP to extract policy statements
    # For now, return sentences containing 'policy', 'rule', or 'directive'
    import re
    sentences = re.split(r'(?<=[.!?]) +', text)
    keywords = ['policy', 'rule', 'directive']
    return [s for s in sentences if any(k in s.lower() for k in keywords)] 