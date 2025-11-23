"""Preprocessor utilities (moved to src root)."""
import os
import re

def crawl_directory(root_path):
    """
    Recursively finds relevant files (.a51, .hex) in the directory.
    Returns a dictionary where keys are student IDs (folder names) and values are lists of file paths.
    Also tracks 'all_files' to help identify illegal submissions.
    Only .a51 files are considered valid source code.
    """
    student_files = {}
    
    # Walk through the directory
    for root, dirs, files in os.walk(root_path):
        # Assuming the immediate subdirectories of root_path are student folders
        # We need to identify which folder belongs to which student
        # The structure seems to be: root_path / student_folder / files...
        
        rel_path = os.path.relpath(root, root_path)
        if rel_path == '.':
            continue
            
        # Extract student ID from the first level folder
        path_parts = rel_path.split(os.sep)
        student_id = path_parts[0]
        
        if student_id not in student_files:
            student_files[student_id] = {'source': [], 'hex': [], 'all_files': []}
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            full_path = os.path.join(root, file)
            
            student_files[student_id]['all_files'].append(full_path)
            
            if ext in ['.a51', '.asm', '.c']:  # .a51, .asm, and .c files are valid source code
                student_files[student_id]['source'].append(full_path)
            elif ext == '.hex':
                student_files[student_id]['hex'].append(full_path)
                
    return student_files

def clean_code(content, file_extension):
    """
    Removes comments and normalizes whitespace.
    """
    # Remove comments based on extension
    if file_extension in ['.a51', '.asm']:
        # Assembly comments start with ;
        content = re.sub(r';.*', '', content)
    elif file_extension in ['.c', '.txt']: # Assuming txt is C-like or mixed
        # C comments // and /* */
        content = re.sub(r'//.*', '', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
    # Normalize whitespace
    # Replace multiple spaces/tabs with single space
    content = re.sub(r'\s+', ' ', content)
    
    # Convert to lowercase for case-insensitive comparison
    content = content.lower()
    
    # Normalize hex immediates: 0x?? -> ??h
    # This matches 0x followed by hex digits and converts to hex digits + h
    content = re.sub(r'0x([0-9a-f]+)', r'\1h', content)
    
    # Strip leading zeros from hex values ending in h (e.g. 012h -> 12h, 0ah -> ah)
    # But preserve single 0 (0h -> 0h)
    content = re.sub(r'\b0+([0-9a-f]+h)', r'\1', content)
    
    return content.strip()

def normalize_hex(content):
    """
    Parses Intel HEX format, extracts data payload.
    Returns: (data_payload, hex_info)
        - data_payload: extracted hex data
        - hex_info: dict with validation information
    """
    data_payload = ""
    lines = content.splitlines()
    has_eof = False
    format_errors = []
    valid_lines = 0
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        if not line.startswith(':'):
            format_errors.append(f"Line {line_num}: Missing ':' prefix")
            continue
            
        # Intel HEX format: :LLAAAATT[DD...]CC
        try:
            if len(line) < 11:  # Minimum valid line length
                format_errors.append(f"Line {line_num}: Line too short")
                continue
                
            byte_count = int(line[1:3], 16)
            record_type = int(line[7:9], 16)
            
            # Record Type 00 is Data
            if record_type == 0:
                data_start = 9
                data_end = 9 + (byte_count * 2)
                # Be more lenient - just check we have enough data
                if len(line) < data_end:
                    format_errors.append(f"Line {line_num}: Insufficient data")
                    continue
                data = line[data_start:data_end]
                data_payload += data
                valid_lines += 1
            # Record Type 01 is EOF
            elif record_type == 1:
                has_eof = True
        except (ValueError, IndexError) as e:
            format_errors.append(f"Line {line_num}: Parse error - {str(e)}")
            continue
    
    hex_info = {
        'has_eof': has_eof,
        'format_errors': format_errors,
        'valid_lines': valid_lines,
        'data_length': len(data_payload)
    }
    
    return data_payload.lower(), hex_info


def validate_source_code(content, file_extension):
    """
    Validates assembly source code quality.
    Returns: list of anomalies
    """
    anomalies = []
    
    if file_extension not in ['.a51', '.asm']:
        return anomalies
    
    lines = content.splitlines()
    total_lines = len(lines)
    
    if total_lines == 0:
        anomalies.append({
            'code': 'EMPTY_FILE',
            'severity': 'error',
            'message': '原始碼檔案為空'
        })
        return anomalies
    
    # Count different line types
    blank_lines = 0
    comment_lines = 0
    code_lines = 0
    instructions = []
    
    # Key assembly instructions to look for
    key_instructions = ['org', 'end', 'mov', 'jmp', 'call', 'ret']
    found_instructions = set()
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            blank_lines += 1
        elif stripped.startswith(';'):
            comment_lines += 1
        else:
            code_lines += 1
            # Extract instruction (first word)
            parts = stripped.lower().split()
            if parts:
                instr = parts[0].rstrip(':')  # Remove label colon
                instructions.append(instr)
                if instr in key_instructions:
                    found_instructions.add(instr)
    
    # Check 1: Minimum instruction count
    if len(instructions) < 10:
        anomalies.append({
            'code': 'FEW_INSTRUCTIONS',
            'severity': 'warning',
            'message': f'指令數量過少 ({len(instructions)} 條)',
            'details': {'count': len(instructions)}
        })
    
    # Check 2: Key instructions existence
    if 'org' not in found_instructions:
        anomalies.append({
            'code': 'NO_ORG',
            'severity': 'warning',
            'message': '缺少 ORG 指令'
        })
    
    if 'end' not in found_instructions:
        anomalies.append({
            'code': 'NO_END',
            'severity': 'warning',
            'message': '缺少 END 指令'
        })
    
    # Check 3: Comment ratio
    if total_lines > 0:
        comment_ratio = comment_lines / total_lines
        if comment_ratio > 0.8:
            anomalies.append({
                'code': 'HIGH_COMMENT_RATIO',
                'severity': 'warning',
                'message': f'註解比例過高 ({comment_ratio*100:.1f}%)',
                'details': {'ratio': comment_ratio}
            })
    
    # Check 4: Blank line ratio
    if total_lines > 0:
        blank_ratio = blank_lines / total_lines
        if blank_ratio > 0.5:
            anomalies.append({
                'code': 'HIGH_BLANK_RATIO',
                'severity': 'warning',
                'message': f'空白行比例過高 ({blank_ratio*100:.1f}%)',
                'details': {'ratio': blank_ratio}
            })
    
    # Check 5: Effective code lines
    if code_lines < 5:
        anomalies.append({
            'code': 'FEW_CODE_LINES',
            'severity': 'error',
            'message': f'有效程式碼行數過少 ({code_lines} 行)',
            'details': {'count': code_lines}
        })
    
    return anomalies


def check_hex_integrity(hex_info, hex_length, median_length):
    """
    Checks hex file integrity based on validation info.
    Returns: list of anomalies
    """
    anomalies = []
    
    # Check 1: EOF marker
    if not hex_info['has_eof']:
        anomalies.append({
            'code': 'NO_EOF',
            'severity': 'warning',
            'message': '缺少 EOF 標記'
        })
    
    # Check 2: Format errors
    if hex_info['format_errors']:
        error_count = len(hex_info['format_errors'])
        anomalies.append({
            'code': 'FORMAT_ERRORS',
            'severity': 'error',
            'message': f'格式錯誤 ({error_count} 處)',
            'details': {'errors': hex_info['format_errors'][:5]}  # First 5 errors
        })
    
    # Check 3: Length check (median ± 25%)
    if median_length > 0:
        lower_threshold = median_length * 0.75
        upper_threshold = median_length * 1.25
        
        if hex_length < lower_threshold:
            anomalies.append({
                'code': 'SHORT_LENGTH',
                'severity': 'warning',
                'message': f'長度過短 ({hex_length}，中位數{int(median_length)})',
                'details': {'length': hex_length, 'median': median_length}
            })
        elif hex_length > upper_threshold:
            anomalies.append({
                'code': 'LONG_LENGTH',
                'severity': 'warning',
                'message': f'長度過長 ({hex_length}，中位數{int(median_length)})',
                'details': {'length': hex_length, 'median': median_length}
            })
    
    # Check 4: Minimum data
    if hex_length < 20:
        anomalies.append({
            'code': 'INSUFFICIENT_DATA',
            'severity': 'error',
            'message': f'資料量不足 ({hex_length} 字元)',
            'details': {'length': hex_length}
        })
    
    return anomalies

