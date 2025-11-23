"""
Unit tests for c51_compiler.py
Tests Keil C51 compilation functionality with mocks
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from c51_compiler import (
    find_keil_c51,
    extract_code_from_listing,
    compile_c_to_asm_keil,
    compile_and_extract_asm
)


class TestFindKeilC51(unittest.TestCase):
    """Test Keil C51 path detection"""
    
    @patch('os.path.exists')
    def test_find_common_path(self, mock_exists):
        # Mock that C:\Keil_v5\C51 exists
        def exists_side_effect(path):
            return path in [r"C:\Keil_v5\C51", r"C:\Keil_v5\C51\BIN\C51.exe"]
        
        mock_exists.side_effect = exists_side_effect
        
        result = find_keil_c51()
        self.assertEqual(result, r"C:\Keil_v5\C51")
        
    @patch('os.path.exists')
    def test_not_found(self, mock_exists):
        # Mock that no paths exist
        mock_exists.return_value = False
        
        result = find_keil_c51()
        self.assertIsNone(result)
        
    @patch('os.environ.get')
    @patch('os.path.exists')
    def test_environment_variable(self, mock_exists, mock_env_get):
        # Mock environment variable
        mock_env_get.return_value = r"C:\Custom\Keil\C51"
        
        def exists_side_effect(path):
            return path in [r"C:\Custom\Keil\C51", r"C:\Custom\Keil\C51\BIN\C51.exe"]
        
        mock_exists.side_effect = exists_side_effect
        
        result = find_keil_c51()
        self.assertEqual(result, r"C:\Custom\Keil\C51")


class TestExtractCodeFromListing(unittest.TestCase):
    """Test assembly code extraction from listing files"""
    
    def test_empty_content(self):
        result = extract_code_from_listing("")
        self.assertEqual(result, "")
        
    def test_extract_instructions(self):
        listing = """
        C51 COMPILER V9.60.7.0
        
        1     0000 7855      MOV A,#55H
        2     0002 F590      MOV P1,A
        3     0004 80FE      SJMP $
        
        MODULE INFORMATION:
        """
        result = extract_code_from_listing(listing)
        # Should extract MOV and SJMP instructions
        self.assertIn('MOV', result)
        self.assertIn('SJMP', result)
        
    def test_skip_header_lines(self):
        listing = """
        C51 COMPILER V9.60.7.0
        MODULE: test
        COMPILER INVOKED BY: ...
        
        1     0000 7855      MOV A,#55H
        """
        result = extract_code_from_listing(listing)
        # Should not include header
        self.assertNotIn('COMPILER', result)
        self.assertNotIn('MODULE', result)
        
    def test_skip_summary_lines(self):
        listing = """
        1     0000 7855      MOV A,#55H
        
        SUMMARY:
        CODE SIZE: 100
        """
        result = extract_code_from_listing(listing)
        # Should not include summary
        self.assertNotIn('SUMMARY', result)
        self.assertNotIn('CODE SIZE', result)


class TestCompileCToAsmKeil(unittest.TestCase):
    """Test C to assembly compilation"""
    
    @patch('c51_compiler.find_keil_c51')
    def test_keil_not_found(self, mock_find):
        mock_find.return_value = None
        
        success, content, error = compile_c_to_asm_keil("test.c")
        
        self.assertFalse(success)
        self.assertEqual(content, "")
        self.assertIn("not found", error)
        
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('c51_compiler.find_keil_c51')
    @patch('shutil.copy2')
    @patch('tempfile.mkdtemp')
    def test_compilation_success(self, mock_mkdtemp, mock_copy, mock_find, 
                                 mock_exists, mock_run):
        # Setup mocks
        mock_find.return_value = r"C:\Keil_v5\C51"
        mock_mkdtemp.return_value = r"C:\Temp\test"
        
        # Mock successful compilation
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Mock file existence
        def exists_side_effect(path):
            return True
        mock_exists.side_effect = exists_side_effect
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data="MOV A,#55H")):
            success, content, error = compile_c_to_asm_keil("test.c")
        
        self.assertTrue(success)
        self.assertIn("MOV", content)
        self.assertEqual(error, "")
        
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('c51_compiler.find_keil_c51')
    @patch('shutil.copy2')
    @patch('tempfile.mkdtemp')
    def test_compilation_failure(self, mock_mkdtemp, mock_copy, mock_find,
                                 mock_exists, mock_run):
        # Setup mocks
        mock_find.return_value = r"C:\Keil_v5\C51"
        mock_mkdtemp.return_value = r"C:\Temp\test"
        mock_exists.return_value = True
        
        # Mock failed compilation
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error: syntax error"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, content, error = compile_c_to_asm_keil("test.c")
        
        self.assertFalse(success)
        self.assertEqual(content, "")
        self.assertIn("syntax error", error)
        
    @patch('subprocess.run')
    @patch('c51_compiler.find_keil_c51')
    @patch('shutil.copy2')
    @patch('tempfile.mkdtemp')
    def test_compilation_timeout(self, mock_mkdtemp, mock_copy, mock_find, mock_run):
        mock_find.return_value = r"C:\Keil_v5\C51"
        mock_mkdtemp.return_value = r"C:\Temp\test"
        
        # Mock timeout
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)
        
        success, content, error = compile_c_to_asm_keil("test.c")
        
        self.assertFalse(success)
        self.assertIn("timed out", error)


class TestCompileAndExtractAsm(unittest.TestCase):
    """Test the convenience function"""
    
    @patch('c51_compiler.compile_c_to_asm_keil')
    @patch('c51_compiler.extract_code_from_listing')
    def test_success_flow(self, mock_extract, mock_compile):
        # Mock successful compilation
        listing_content = "1  0000  7855  MOV A,#55H"
        mock_compile.return_value = (True, listing_content, "")
        mock_extract.return_value = "MOV A,#55H"
        
        success, asm_code, error = compile_and_extract_asm("test.c")
        
        self.assertTrue(success)
        self.assertEqual(asm_code, "MOV A,#55H")
        self.assertEqual(error, "")
        
    @patch('c51_compiler.compile_c_to_asm_keil')
    def test_compilation_failure_flow(self, mock_compile):
        # Mock failed compilation
        mock_compile.return_value = (False, "", "Compilation error")
        
        success, asm_code, error = compile_and_extract_asm("test.c")
        
        self.assertFalse(success)
        self.assertEqual(asm_code, "")
        self.assertEqual(error, "Compilation error")


if __name__ == '__main__':
    unittest.main(verbosity=2)
