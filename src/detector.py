"""Detector utilities (moved to src root)."""
import Levenshtein

def tokenize_code(text):
    """
    Split code into tokens (words/instructions).
    Simple whitespace-based tokenization.
    """
    if not text:
        return []
    return text.split()

def lcs_length(tokens1, tokens2):
    """
    Calculate Longest Common Subsequence length using dynamic programming.
    
    Args:
        tokens1, tokens2: Lists of tokens to compare
    
    Returns:
        Length of the longest common subsequence
    """
    if not tokens1 or not tokens2:
        return 0
    
    m, n = len(tokens1), len(tokens2)
    
    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if tokens1[i-1] == tokens2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def calculate_token_sequence_similarity(text1, text2):
    """
    Calculate similarity based on Longest Common Subsequence ratio.
    
    Similarity = 2 * LCS_length / (len(seq1) + len(seq2))
    
    Args:
        text1, text2: Texts to compare
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
    
    tokens1 = tokenize_code(text1)
    tokens2 = tokenize_code(text2)
    
    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0
    
    lcs_len = lcs_length(tokens1, tokens2)
    total_len = len(tokens1) + len(tokens2)
    
    return (2.0 * lcs_len) / total_len if total_len > 0 else 0.0

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
    Now only uses Token Sequence Similarity and Levenshtein Distance.
    Winnowing has been removed.
    """
    return {
        'token_seq': calculate_token_sequence_similarity(text1, text2),
        'levenshtein': calculate_levenshtein_similarity(text1, text2)
    }
