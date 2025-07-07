from transformers import pipeline

summarizer = pipeline('summarization', model='facebook/bart-large-cnn')

def summarize_text(text: str) -> str:
    text = text.strip()
    if not text:
        return ''
    # BART max tokens is 1024, but to be safe, chunk by words
    words = text.split()
    chunk_size = 900
    summaries = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i+chunk_size])
        if len(chunk.split()) < 30:
            continue  # skip too-short chunks
        try:
            summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            summaries.append('')
    return ' '.join(summaries) if summaries else ''

def extract_policies(text: str) -> list:
    # Placeholder: Use regex/NLP to extract policy statements
    # For now, return sentences containing 'policy', 'rule', or 'directive'
    import re
    sentences = re.split(r'(?<=[.!?]) +', text)
    keywords = ['policy', 'rule', 'directive']
    return [s for s in sentences if any(k in s.lower() for k in keywords)] 