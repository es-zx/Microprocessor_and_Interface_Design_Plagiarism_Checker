"""
Module for compiling C code to assembly using Keil C51
"""
import os
import subprocess
import tempfile
import shutil
import re
from pathlib import Path


def compile_c_to_asm_keil(c_file_path, output_dir=None, keil_path=None):
    """
    Compile a C file to assembly using Keil C51 compiler.
    
    Args:
        c_file_path (str): Path to the C source file
        output_dir (str, optional): Directory to store output files. If None, creates a temporary directory
        keil_path (str, optional): Path to Keil C51 installation. If None, tries common installation paths
    
    Returns:
        tuple: (success: bool, asm_content: str, error_message: str)
    """
    # Try to find Keil C51 installation
    if not keil_path:
        keil_path = find_keil_c51()
        if not keil_path:
            return False, "", "Keil C51 compiler not found. Please provide keil_path parameter or install Keil C51."
    
    # Get the C compiler executable
    c51_compiler = os.path.join(keil_path, "BIN", "C51.exe")
    if not os.path.exists(c51_compiler):
        return False, "", f"C51 compiler not found at {c51_compiler}"
    
    # Create output directory if not specified
    if not output_dir:
        output_dir = tempfile.mkdtemp()
    
    # Copy C file to output directory to ensure compiler can find it
    c_filename = os.path.basename(c_file_path)
    temp_c_path = os.path.join(output_dir, c_filename)
    shutil.copy2(c_file_path, temp_c_path)
    
    try:
        # Build command to compile with C51
        # Use the ASL directive to generate assembly listing
        cmd = [
            c51_compiler,
            temp_c_path,
            f"OBJECT({os.path.splitext(c_filename)[0]}.obj)",
            "DEBUG",  # Include debug info
            "OPTIMIZE(9)",  # High optimization level
            f"INCDIR({os.path.join(keil_path, 'INC')})"  # Include path
        ]
        
        # Run the C51 compiler
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,  # 30-second timeout
            cwd=output_dir
        )
        
        if result.returncode != 0:
            # Combine stdout and stderr for error message
            output = result.stdout + "\n" + result.stderr
            error_msg = f"Compilation failed (Code {result.returncode}): {output.strip()}"
            return False, "", error_msg
        
        # Find the generated assembly file
        asm_filename = os.path.splitext(c_filename)[0] + ".lst"
        asm_path = os.path.join(output_dir, asm_filename)
        
        if not os.path.exists(asm_path):
            # Look for .a51 file if .lst doesn't exist
            asm_path = os.path.join(output_dir, os.path.splitext(c_filename)[0] + ".a51")
            if not os.path.exists(asm_path):
                return False, "", f"Assembly file not found after compilation: {asm_path}"
        
        # Read the assembly content
        with open(asm_path, 'r', encoding='utf-8', errors='ignore') as f:
            asm_content = f.read()
        
        return True, asm_content, ""
        
    except subprocess.TimeoutExpired:
        return False, "", "Compilation timed out"
    except Exception as e:
        return False, "", f"Compilation error: {str(e)}"
    finally:
        # Clean up temporary C file if it was copied
        if temp_c_path != c_file_path and os.path.exists(temp_c_path):
            try:
                os.remove(temp_c_path)
            except:
                pass


def find_keil_c51():
    """
    Attempt to find Keil C51 installation on the system.
    
    Returns:
        str or None: Path to Keil C51 installation, or None if not found
    """
    # Common installation paths for Keil C51
    common_paths = [
        r"C:\Keil_v5\C51",
        r"C:\Keil\C51",
        r"C:\Program Files\Keil_v5\C51",
        r"C:\Program Files (x86)\Keil_v5\C51",
        r"C:\Program Files\Keil\C51",
        r"C:\Program Files (x86)\Keil\C51",
    ]
    
    # Add common paths from environment variables
    keil_env = os.environ.get("C51ROOT") or os.environ.get("KEIL_C51")
    if keil_env:
        common_paths.insert(0, keil_env)
    
    for path in common_paths:
        if os.path.exists(path):
            # Verify that the C51 compiler exists in this path
            c51_path = os.path.join(path, "BIN", "C51.exe")
            if os.path.exists(c51_path):
                return path
    
    return None


def extract_code_from_listing(asm_listing_content):
    """
    Extract just the assembly code from a Keil listing file, removing extra information.
    
    Args:
        asm_listing_content (str): Content of the .lst file from Keil
    
    Returns:
        str: Cleaned assembly code with just instructions and comments
    """
    if not asm_listing_content:
        return ""
    
    lines = asm_listing_content.splitlines()
    cleaned_lines = []
    
    # Pattern to match assembly code lines (typically have addresses followed by opcodes)
    asm_pattern = re.compile(r'^\s*\d+\s+[0-9A-F]+\s+([A-Z]+.*$)', re.IGNORECASE)
    
    for line in lines:
        # Skip header lines and other non-assembly content
        line = line.strip()
        
        # Skip if it looks like a header or summary line
        if line.startswith(';') or line.startswith('MODULE') or line.startswith('COMPILER') or \
           line.startswith('SUMMARY') or line.startswith('FUNCTION') or line.startswith('NAME'):
            continue
        
        # Try to extract assembly instruction using pattern
        match = asm_pattern.match(line)
        if match:
            asm_instruction = match.group(1).strip()
            # Only add if it looks like an actual instruction
            if asm_instruction and not asm_instruction.startswith('.'):
                cleaned_lines.append(asm_instruction)
        elif any(op in line.upper() for op in ['MOV', 'ADD', 'SUB', 'MUL', 'DIV', 'JMP', 'CALL', 'RET', 'PUSH', 'POP']):
            # If it contains common assembly operations, consider it assembly code
            # Remove any leading line numbers or addresses
            clean_line = re.sub(r'^\s*\d+\s+', '', line)
            if clean_line.strip():
                cleaned_lines.append(clean_line.strip())
    
    return '\n'.join(cleaned_lines)


def compile_and_extract_asm(c_file_path, keil_path=None):
    """
    Convenience function that compiles a C file to assembly and extracts clean assembly code.
    
    Args:
        c_file_path (str): Path to the C source file
        keil_path (str, optional): Path to Keil C51 installation
    
    Returns:
        tuple: (success: bool, asm_code: str, error_message: str)
    """
    success, asm_content, error = compile_c_to_asm_keil(c_file_path, keil_path=keil_path)
    if not success:
        return False, "", error
    
    # Extract just the assembly code from the listing
    cleaned_asm = extract_code_from_listing(asm_content)
    return True, cleaned_asm, ""