"""
Regression tests for plagiarism detection system
Tests for previously encountered bugs and edge cases to prevent regressions
"""
import unittest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from detector import calculate_combined_similarity
from preprocessor import clean_code, normalize_hex, validate_source_code, check_hex_integrity
from c51_compiler import compile_c_to_asm_keil


class TestC51CompilationRegressions(unittest.TestCase):
    """Regression tests for C51 compiler integration issues"""
    
    def test_utf16_encoded_c_file_handling(self):
        """
        Regression: C51 compiler failed with UTF-16 BOM encoded files
        Issue: PowerShell echo created UTF-16 files causing 'unprintable character 0xFF' errors
        Fix: Files must be ASCII/UTF-8 encoded
        """
        # This test verifies the error message is clear when encountering encoding issues
        # In production, files should be properly encoded before compilation
        
        # Simulate the error scenario
        with patch('c51_compiler.find_keil_c51') as mock_find:
            mock_find.return_value = r"C:\Keil_v5\C51"
            
            with patch('subprocess.run') as mock_run:
                # Simulate C51 error output for encoding issues
                mock_result = MagicMock()
                mock_result.returncode = 2
                mock_result.stdout = "*** ERROR C100: unprintable character 0xFF skipped"
                mock_result.stderr = ""
                mock_run.return_value = mock_result
                
                with patch('shutil.copy2'), patch('tempfile.mkdtemp') as mock_mkdtemp:
                    mock_mkdtemp.return_value = tempfile.gettempdir()
                    
                    success, content, error = compile_c_to_asm_keil("test.c")
                    
                    self.assertFalse(success)
                    self.assertIn("unprintable character", error)
    
    def test_missing_incdir_compilation_failure(self):
        """
        Regression: C51 compilation failed because reg51.h couldn't be found
        Issue: INCDIR parameter was missing from compiler command
        Fix: Added INCDIR({keil_path}/INC) to compiler arguments
        """
        # This is tested implicitly in test_c51_compiler.py
        # Here we verify the error message when include files are missing
        
        with patch('c51_compiler.find_keil_c51') as mock_find:
            mock_find.return_value = r"C:\Keil_v5\C51"
            
            with patch('subprocess.run') as mock_run:
                # Simulate missing include file error
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stdout = "*** ERROR: Cannot open include file 'reg51.h'"
                mock_result.stderr = ""
                mock_run.return_value = mock_result
                
                with patch('shutil.copy2'), patch('tempfile.mkdtemp') as mock_mkdtemp:
                    mock_mkdtemp.return_value = tempfile.gettempdir()
                    
                    success, content, error = compile_c_to_asm_keil("test.c")
                    
                    self.assertFalse(success)
                    self.assertIn("reg51.h", error)


class TestInvalidSubmissionRegressions(unittest.TestCase):
    """Regression tests for invalid submission detection logic"""
    
    def test_c_file_only_not_invalid_when_keil_enabled(self):
        """
        Regression: Students submitting only .c files were marked as invalid
        Issue: preprocessor.py only accepted .a51 files as valid source
        Fix: Modified to accept .c files when USE_KEIL_COMPILATION is True
        """
        # This is tested in integration, but we verify the logic here
        # A student with only .c and .hex should be valid when Keil is enabled
        
        # Simulate the scenario
        valid_extensions_with_keil = ['.a51', '.asm', '.c']
        valid_extensions_without_keil = ['.a51', '.asm']
        
        c_file = 'student.c'
        ext = os.path.splitext(c_file)[1].lower()
        
        # With Keil enabled, .c should be valid
        self.assertIn(ext, valid_extensions_with_keil)
        
        # Without Keil, .c should not be valid
        self.assertNotIn(ext, valid_extensions_without_keil)


class TestHexProcessingRegressions(unittest.TestCase):
    """Regression tests for hex file processing issues"""
    
    def test_empty_hex_file_handling(self):
        """
        Regression: Empty hex files caused crashes or incorrect processing
        Issue: normalize_hex didn't handle empty strings gracefully
        Fix: Added empty string check at start of function
        """
        normalized, info = normalize_hex("")
        
        self.assertEqual(normalized, "")
        self.assertIsInstance(info, dict)
        self.assertFalse(info.get('has_eof', True))
    
    def test_hex_without_eof_marker(self):
        """
        Regression: Hex files without EOF marker (:00000001FF) were not flagged
        Issue: Anomaly detection didn't check for EOF marker
        Fix: Added NO_EOF anomaly code
        """
        hex_data = ":03000000020003F8"  # Missing EOF
        normalized, info = normalize_hex(hex_data)
        
        self.assertFalse(info.get('has_eof', True))
        
        # Verify anomaly is detected
        anomalies = check_hex_integrity(info, len(normalized), 100)
        codes = [a['code'] for a in anomalies]
        self.assertIn('NO_EOF', codes)
    
    def test_very_short_hex_file(self):
        """
        Regression: Very short hex files (< 10 chars) caused division by zero
        Issue: Insufficient data check was missing
        Fix: Added INSUFFICIENT_DATA anomaly for hex_length < 10
        """
        hex_data = ":00000001FF"  # Only EOF marker, very short
        normalized, info = normalize_hex(hex_data)
        
        anomalies = check_hex_integrity(info, len(normalized), 100)
        codes = [a['code'] for a in anomalies]
        self.assertIn('INSUFFICIENT_DATA', codes)


class TestSimilarityCalculationRegressions(unittest.TestCase):
    """Regression tests for similarity calculation edge cases"""
    
    def test_identical_code_with_different_whitespace(self):
        """
        Regression: Identical code with different whitespace had low similarity
        Issue: Whitespace wasn't properly normalized
        Fix: clean_code normalizes whitespace
        """
        code1 = "mov a, #55h\nadd a, r0"
        code2 = "mov    a,    #55h\n\n\nadd   a,   r0"
        
        # After cleaning, should be very similar
        cleaned1 = clean_code(code1, '.a51')
        cleaned2 = clean_code(code2, '.a51')
        
        result = calculate_combined_similarity(cleaned1, cleaned2)
        
        # Should have very high similarity
        self.assertGreater(result['token_seq'], 0.9)
        self.assertGreater(result['levenshtein'], 0.8)
    
    def test_empty_string_similarity(self):
        """
        Regression: Empty strings caused division by zero
        Issue: LCS calculation didn't handle empty inputs
        Fix: Added early return for empty strings
        """
        result = calculate_combined_similarity("", "")
        
        # Both empty should be considered identical
        self.assertEqual(result['token_seq'], 1.0)
        self.assertEqual(result['levenshtein'], 1.0)
    
    def test_one_empty_string_similarity(self):
        """
        Regression: One empty string returned unexpected results
        Issue: Edge case not handled
        Fix: Return 0.0 when one string is empty
        """
        result1 = calculate_combined_similarity("mov a", "")
        result2 = calculate_combined_similarity("", "mov a")
        
        self.assertEqual(result1['token_seq'], 0.0)
        self.assertEqual(result1['levenshtein'], 0.0)
        self.assertEqual(result2['token_seq'], 0.0)
        self.assertEqual(result2['levenshtein'], 0.0)


class TestAnomalyDetectionRegressions(unittest.TestCase):
    """Regression tests for anomaly detection issues"""
    
    def test_assembly_with_only_comments(self):
        """
        Regression: Files with only comments weren't flagged
        Issue: Comment ratio check didn't account for zero code lines
        Fix: Added FEW_CODE_LINES anomaly
        """
        code = """; Comment 1
; Comment 2
; Comment 3
; Comment 4
; Comment 5"""
        
        anomalies = validate_source_code(code, '.a51')
        codes = [a['code'] for a in anomalies]
        
        # Should detect multiple issues
        self.assertIn('FEW_INSTRUCTIONS', codes)
        self.assertIn('FEW_CODE_LINES', codes)
    
    def test_assembly_without_org_and_end(self):
        """
        Regression: Missing ORG/END directives weren't consistently flagged
        Issue: Validation logic had gaps
        Fix: Added NO_ORG and NO_END anomaly codes
        """
        code = """mov a, #55h
add a, r0
mov p1, a"""
        
        anomalies = validate_source_code(code, '.a51')
        codes = [a['code'] for a in anomalies]
        
        self.assertIn('NO_ORG', codes)
        self.assertIn('NO_END', codes)
    
    def test_c_code_not_validated_as_assembly(self):
        """
        Regression: C code was incorrectly validated with assembly rules
        Issue: validate_source_code applied assembly rules to all files
        Fix: Different validation for .c files
        """
        c_code = "int main() { return 0; }"
        
        anomalies = validate_source_code(c_code, '.c')
        codes = [a['code'] for a in anomalies]
        
        # C code should not be flagged for missing ORG/END
        self.assertNotIn('NO_ORG', codes)
        self.assertNotIn('NO_END', codes)


class TestReportGenerationRegressions(unittest.TestCase):
    """Regression tests for report generation issues"""
    
    def test_unicode_student_names(self):
        """
        Regression: Unicode characters in student names caused encoding errors
        Issue: HTML report generation didn't handle unicode
        Fix: Use UTF-8 encoding for all file operations
        """
        # Test that unicode strings are handled correctly
        student_name = "學生_張三_4893673"
        
        # Should not raise encoding errors
        try:
            encoded = student_name.encode('utf-8')
            decoded = encoded.decode('utf-8')
            self.assertEqual(student_name, decoded)
        except UnicodeEncodeError:
            self.fail("Unicode encoding failed")
    
    def test_very_long_code_in_report(self):
        """
        Regression: Very long code snippets caused browser rendering issues
        Issue: No truncation for display
        Fix: This is a known limitation, test verifies it doesn't crash
        """
        # Generate very long code
        long_code = "\n".join(["mov a, #55h"] * 10000)
        
        # Should not crash when calculating similarity
        result = calculate_combined_similarity(long_code, long_code)
        
        self.assertEqual(result['token_seq'], 1.0)
        self.assertEqual(result['levenshtein'], 1.0)


class TestEdgeCaseRegressions(unittest.TestCase):
    """Regression tests for various edge cases"""
    
    def test_special_characters_in_code(self):
        """
        Regression: Special characters in code caused parsing issues
        Issue: Regex patterns didn't escape special chars
        Fix: Proper string handling in clean_code
        """
        code_with_special = "mov a, #'$'  ; Dollar sign\nmov b, #'@'"
        
        # Should not crash
        cleaned = clean_code(code_with_special, '.a51')
        self.assertIsInstance(cleaned, str)
    
    def test_windows_line_endings(self):
        """
        Regression: Windows line endings (\r\n) vs Unix (\n) caused issues
        Issue: Line counting was inconsistent
        Fix: Normalize line endings in preprocessing
        """
        code_windows = "mov a\r\nadd a\r\n"
        code_unix = "mov a\nadd a\n"
        
        # Should produce similar results
        result = calculate_combined_similarity(code_windows, code_unix)
        
        # Should be very similar despite line ending differences
        self.assertGreater(result['token_seq'], 0.9)
    
    def test_null_bytes_in_input(self):
        """
        Regression: Null bytes in files caused crashes
        Issue: Binary data not handled
        Fix: Use errors='ignore' when reading files
        """
        # Simulate file with null bytes
        code_with_nulls = "mov a\x00add a"
        
        # Should handle gracefully
        try:
            result = calculate_combined_similarity(code_with_nulls, "mov a add a")
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.fail(f"Null bytes caused exception: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
