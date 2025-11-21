"""Detector utilities (moved to src root)."""
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein

def generate_ngrams(text, n=3):
    """
    Generates n-grams from text.
    Returns a set of n-grams.
    """
    if not text:
        return set()
    
    # Simple character-based n-grams for code might be better than word-based
    # depending on how "clean" the code is. 
    # Let's use word-based first as we cleaned the code.
    words = text.split()
    if len(words) < n:
        return set([text]) # Return the whole text if shorter than n
        
    ngrams = zip(*[words[i:] for i in range(n)])
    return set([" ".join(ngram) for ngram in ngrams])

def calculate_jaccard_similarity(text1, text2, n=3):
    """
    Calculates Jaccard similarity based on n-grams.
    """
    set1 = generate_ngrams(text1, n)
    set2 = generate_ngrams(text2, n)
    
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
        
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union

def calculate_cosine_similarity(text1, text2):
    """
    Calculates Cosine similarity using CountVectorizer.
    """
    if not text1 or not text2:
        return 0.0
        
    try:
        vectorizer = CountVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.toarray()
        return cosine_similarity(vectors)[0][1]
    except ValueError:
        # Handle cases where text might be empty or stop words only
        return 0.0

def calculate_levenshtein_similarity(text1, text2):
    """
    Calculates similarity based on Levenshtein distance.
    Ratio = (len(text1) + len(text2) - distance) / (len(text1) + len(text2))
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
        
    return Levenshtein.ratio(text1, text2)

def calculate_combined_similarity(text1, text2):
    """
    Returns a dictionary of similarity scores.
    """
    return {
        'jaccard': calculate_jaccard_similarity(text1, text2),
        'cosine': calculate_cosine_similarity(text1, text2),
        'levenshtein': calculate_levenshtein_similarity(text1, text2)
    }
