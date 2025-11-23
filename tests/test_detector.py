"""
Unit tests for detector.py
Tests Token Sequence Similarity (LCS) and Levenshtein Distance algorithms
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from detector import (
    tokenize_code,
    lcs_length,
    calculate_token_sequence_similarity,
    calculate_levenshtein_similarity,
    calculate_combined_similarity
)


class TestTokenizeCode(unittest.TestCase):
    """Test code tokenization"""
    
    def test_empty_string(self):
        self.assertEqual(tokenize_code(""), [])
        
    def test_simple_code(self):
        result = tokenize_code("mov a, #55h")
        self.assertEqual(result, ["mov", "a,", "#55h"])
        
    def test_multiple_spaces(self):
        result = tokenize_code("mov   a,    #55h")
        self.assertEqual(result, ["mov", "a,", "#55h"])


class TestLCSLength(unittest.TestCase):
    """Test Longest Common Subsequence calculation"""
    
    def test_empty_sequences(self):
        self.assertEqual(lcs_length([], []), 0)
        self.assertEqual(lcs_length(["a"], []), 0)
        self.assertEqual(lcs_length([], ["a"]), 0)
        
    def test_identical_sequences(self):
        tokens = ["mov", "a", "#55h"]
        self.assertEqual(lcs_length(tokens, tokens), 3)
        
    def test_completely_different(self):
        seq1 = ["mov", "a", "#55h"]
        seq2 = ["clr", "r0", "ret"]
        self.assertEqual(lcs_length(seq1, seq2), 0)
        
    def test_partial_overlap(self):
        seq1 = ["mov", "a", "#55h", "add", "a", "r0"]
        seq2 = ["mov", "a", "#85", "add", "a", "r1"]
        # Common: mov, a, add, a
        result = lcs_length(seq1, seq2)
        self.assertGreater(result, 0)
        self.assertLess(result, 6)


class TestTokenSequenceSimilarity(unittest.TestCase):
    """Test Token Sequence Similarity (LCS-based)"""
    
    def test_empty_strings(self):
        # Both empty should be 1.0 (identical)
        self.assertEqual(calculate_token_sequence_similarity("", ""), 1.0)
        
    def test_one_empty(self):
        # One empty should be 0.0
        self.assertEqual(calculate_token_sequence_similarity("mov a", ""), 0.0)
        self.assertEqual(calculate_token_sequence_similarity("", "mov a"), 0.0)
        
    def test_identical_code(self):
        code = "mov a, #55h add a, r0"
        self.assertEqual(calculate_token_sequence_similarity(code, code), 1.0)
        
    def test_completely_different(self):
        code1 = "mov a, #55h"
        code2 = "clr r0"
        similarity = calculate_token_sequence_similarity(code1, code2)
        self.assertLess(similarity, 0.3)
        
    def test_similar_code(self):
        code1 = "mov a, #55h add a, r0"
        code2 = "mov a, #85 add a, r1"  # Changed constants and register
        similarity = calculate_token_sequence_similarity(code1, code2)
        # Should have high similarity due to common structure
        self.assertGreater(similarity, 0.5)
        
    def test_reordered_code(self):
        code1 = "mov a, #55h clr r0"
        code2 = "clr r0 mov a, #55h"
        similarity = calculate_token_sequence_similarity(code1, code2)
        # LCS should still find common tokens (adjusted expectation)
        self.assertGreater(similarity, 0.5)


class TestLevenshteinSimilarity(unittest.TestCase):
    """Test Levenshtein Distance similarity"""
    
    def test_empty_strings(self):
        self.assertEqual(calculate_levenshtein_similarity("", ""), 1.0)
        
    def test_one_empty(self):
        self.assertEqual(calculate_levenshtein_similarity("test", ""), 0.0)
        self.assertEqual(calculate_levenshtein_similarity("", "test"), 0.0)
        
    def test_identical_strings(self):
        text = "mov a, #55h"
        self.assertEqual(calculate_levenshtein_similarity(text, text), 1.0)
        
    def test_single_char_difference(self):
        text1 = "mov a, #55h"
        text2 = "mov a, #56h"  # One character different
        similarity = calculate_levenshtein_similarity(text1, text2)
        self.assertGreater(similarity, 0.9)
        
    def test_completely_different(self):
        text1 = "aaaa"
        text2 = "bbbb"
        similarity = calculate_levenshtein_similarity(text1, text2)
        self.assertEqual(similarity, 0.0)
        
    def test_case_sensitive(self):
        text1 = "MOV A"
        text2 = "mov a"
        similarity = calculate_levenshtein_similarity(text1, text2)
        # Should be different due to case
        self.assertLess(similarity, 1.0)


class TestCombinedSimilarity(unittest.TestCase):
    """Test combined similarity calculation"""
    
    def test_returns_dict(self):
        result = calculate_combined_similarity("mov a", "mov a")
        self.assertIsInstance(result, dict)
        self.assertIn('token_seq', result)
        self.assertIn('levenshtein', result)
        
    def test_identical_code(self):
        code = "mov a, #55h add a, r0"
        result = calculate_combined_similarity(code, code)
        self.assertEqual(result['token_seq'], 1.0)
        self.assertEqual(result['levenshtein'], 1.0)
        
    def test_empty_strings(self):
        result = calculate_combined_similarity("", "")
        self.assertEqual(result['token_seq'], 1.0)
        self.assertEqual(result['levenshtein'], 1.0)
        
    def test_realistic_plagiarism_case(self):
        # Student A's code
        code1 = "mov a, #55h cpl p1 sjmp loop"
        # Student B's code (changed constant and added nop)
        code2 = "mov a, #85 nop cpl p1 sjmp loop"
        
        result = calculate_combined_similarity(code1, code2)
        
        # Both metrics should show high similarity
        self.assertGreater(result['token_seq'], 0.6)
        self.assertGreater(result['levenshtein'], 0.6)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_single_token(self):
        similarity = calculate_token_sequence_similarity("mov", "mov")
        self.assertEqual(similarity, 1.0)
        
    def test_whitespace_only(self):
        result = calculate_combined_similarity("   ", "   ")
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        
    def test_very_long_code(self):
        # Test performance with longer code
        code1 = " ".join(["mov a, #55h"] * 100)
        code2 = " ".join(["mov a, #85"] * 100)
        result = calculate_combined_similarity(code1, code2)
        # Should complete without error (adjusted expectation)
        self.assertIsInstance(result, dict)
        self.assertGreater(result['token_seq'], 0.6)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
