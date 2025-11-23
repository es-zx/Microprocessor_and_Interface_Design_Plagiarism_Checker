import os
import itertools
from tqdm import tqdm
from preprocessor import crawl_directory, clean_code, normalize_hex, validate_source_code, check_hex_integrity
from detector import calculate_combined_similarity, calculate_levenshtein_similarity
from llm_analyzer import analyze_pair_with_llm
from reporter import generate_html_report
from c51_compiler import compile_and_extract_asm, find_keil_c51


def read_file_with_encoding(file_path):
    """
    Try to read file with UTF-8, then CP950 (Big5).
    """
    encodings = ['utf-8', 'cp950', 'latin-1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading {file_path} with {enc}: {e}")
            return ""
    return ""

def check_plagiarism(root_path, filter_mode="threshold", 
                    hex_threshold=0.7, src_threshold=0.8, 
                    top_metric="avg_score", top_percent=0.05,
                    lab_name="Lab", use_keil_compilation=False, keil_path=None):

    """
    Main function to check plagiarism.
    """
    print("Step 1: Crawling and preprocessing...")
    student_files = crawl_directory(root_path)
    student_data = {}

    # Preprocess all data
    for student, files in student_files.items():
        student_data[student] = {
            'source': "", 
            'hex': "", 
            'original_source': "", 
            'asm_source': "",         # Compiled assembly or raw assembly
            'illegal_submission': False, 
            'illegal_reason': "",
            'hex_anomalies': [],      # List of hex anomalies
            'source_anomalies': [],   # List of source code anomalies
            'has_anomaly': False,     # Flag for any anomaly
            'hex_length': 0,          # Hex data length
            'hex_info': {}            # Hex validation info
        }
        
        # Check for illegal submission (no valid source files or no hex files)
        # Determine valid extensions based on configuration
        valid_extensions = ['.a51', '.asm']
        if use_keil_compilation:
            valid_extensions.append('.c')
            
        has_valid_source = False
        for src_file in files['source']:
            ext = os.path.splitext(src_file)[1].lower()
            if ext in valid_extensions:
                has_valid_source = True
                break
                
        if not has_valid_source:
            student_data[student]['illegal_submission'] = True
            if files['all_files']:
                # Found files but not valid source
                exts = set([os.path.splitext(f)[1] for f in files['all_files']])
                student_data[student]['illegal_reason'] = f"無效提交：找到 {', '.join(exts)} 檔案，但需要 {', '.join(valid_extensions)} 檔案"
            else:
                student_data[student]['illegal_reason'] = "未找到任何檔案"
        
        # Combine all source files
        full_source = ""
        full_asm_source = ""  # For compiled assembly from C files
        full_original_source = ""
        
        c_files_for_compilation = []  # Track C files to compile if needed
        asm_files_content = []  # Track regular assembly files

        for src_file in files['source']:
            try:
                content = read_file_with_encoding(src_file)
                if not content:
                    print(f"Warning: Could not read {src_file} or file is empty")
                    continue
                    
                ext = os.path.splitext(src_file)[1].lower()  # Lowercase for case-insensitive comparison
                
                # Store original content with filename header for display
                filename = os.path.basename(src_file)
                full_original_source += f"--- {filename} ---\n{content}\n\n"  
                
                if ext in ['.c']:
                    cleaned = clean_code(content, ext)
                    full_source += cleaned + " "
                    if use_keil_compilation:
                        c_files_for_compilation.append(src_file)
                elif ext in ['.a51', '.asm']:
                    cleaned = clean_code(content, ext)
                    full_source += cleaned + " "
                    asm_files_content.append(content)
                
                # Validate source code quality
                anomalies = validate_source_code(content, ext)
                student_data[student]['source_anomalies'].extend(anomalies)
            except Exception as e:
                print(f"Error reading {src_file}: {e}")      

        # If we need to compile C to assembly
        if use_keil_compilation and c_files_for_compilation:
            print(f"Compiling C files to assembly for student {student}...")
            for c_file in c_files_for_compilation:
                success, asm_code, error = compile_and_extract_asm(c_file, keil_path)
                if success:
                    full_asm_source += asm_code + " "
                    # print(f"  Successfully compiled {c_file} to assembly")
                else:
                    print(f"  Failed to compile {c_file}: {error}")

        # Add regular assembly files to asm_source as well
        for asm_content in asm_files_content:
            full_asm_source += clean_code(asm_content, '.a51') + " "

        student_data[student]['source'] = full_source.strip()
        student_data[student]['asm_source'] = full_asm_source.strip()
        student_data[student]['original_source'] = full_original_source.strip()
        
        # Combine all hex files and collect validation info
        full_hex = ""
        all_hex_info = {
            'has_eof': False,
            'format_errors': [],
            'valid_lines': 0,
            'data_length': 0
        }
        
        for hex_file in files['hex']:
            try:
                content = read_file_with_encoding(hex_file)
                if not content:
                    continue
                    
                hex_data, hex_info = normalize_hex(content)
                full_hex += hex_data
                
                # Aggregate hex info
                if hex_info['has_eof']:
                    all_hex_info['has_eof'] = True
                all_hex_info['format_errors'].extend(hex_info['format_errors'])
                all_hex_info['valid_lines'] += hex_info['valid_lines']

            except Exception as e:
                print(f"Error reading {hex_file}: {e}")

        student_data[student]['hex'] = full_hex
        student_data[student]['hex_length'] = len(full_hex)
        all_hex_info['data_length'] = len(full_hex)
        student_data[student]['hex_info'] = all_hex_info
        

        # Check if hex is empty (illegal submission - not anomaly)
        if not full_hex or full_hex.strip() == "":
            student_data[student]['illegal_submission'] = True
            if student_data[student]['illegal_reason']:
                student_data[student]['illegal_reason'] += " | 未找到有效的 hex 檔案"
            else:
                student_data[student]['illegal_reason'] = "無效提交：未找到有效的 hex 檔案"
        
    
    # Find median hex length across all students (excluding empty ones)
    hex_lengths = [data['hex_length'] for data in student_data.values() if data['hex_length'] > 0]
    median_hex_length = 0
    
    if hex_lengths:
        hex_lengths.sort()
        n = len(hex_lengths)
        if n % 2 == 0:
            median_hex_length = (hex_lengths[n//2 - 1] + hex_lengths[n//2]) / 2
        else:
            median_hex_length = hex_lengths[n//2]
    
    # Check hex integrity for all students (as anomalies, not illegal submissions)
    for student, data in student_data.items():
        if data['hex_length'] > 0:
            hex_anomalies = check_hex_integrity(
                data['hex_info'], 
                data['hex_length'], 
                median_hex_length
            )
            student_data[student]['hex_anomalies'].extend(hex_anomalies)
    
    # Mark students with anomalies
    for student, data in student_data.items():
        if data['hex_anomalies'] or data['source_anomalies']:
            student_data[student]['has_anomaly'] = True
        

    print("Step 2: Calculating similarities...")
    students = list(student_data.keys())
    pairs = list(itertools.combinations(students, 2))

    all_comparisons = []

    for student1, student2 in tqdm(pairs, desc="Calculating pairs", unit="pair"):
        # Source comparison
        if use_keil_compilation:
            src1 = student_data[student1]['asm_source']
            src2 = student_data[student2]['asm_source']
        else:
            src1 = student_data[student1]['source']
            src2 = student_data[student2]['source']
            
        src_sim = {'token_seq': 0, 'levenshtein': 0}

        if src1 and src2:
            src_sim = calculate_combined_similarity(src1, src2)

        # Hex comparison - only use Levenshtein
        hex1 = student_data[student1]['hex']
        hex2 = student_data[student2]['hex']
        hex_lev = 0
        if hex1 and hex2:
            hex_lev = calculate_levenshtein_similarity(hex1, hex2)
   
        # Calculate scores
        max_hex_sim = hex_lev
        avg_score = (src_sim['token_seq'] + src_sim['levenshtein']) / 2.0
        
        # Store all data for filtering
        all_comparisons.append({
            'student1': student1,
            'student2': student2,
            'source_similarity': src_sim,
            'hex_levenshtein': hex_lev,
            'max_hex_sim': max_hex_sim,
            'avg_score': avg_score
        })

    print(f"Step 3: Filtering pairs (Mode: {filter_mode})...")
    filtered_pairs = []

    if filter_mode == "threshold":
        # Filter by threshold
        # Mode 1: Check if Average Score > SRC_THRESHOLD OR Hex > HEX_THRESHOLD
        for comp in all_comparisons:
            if comp['max_hex_sim'] > hex_threshold or comp['avg_score'] > src_threshold:
                filtered_pairs.append(comp)
                
    elif filter_mode == "top_percent":
        # Sort and take top N%
        total_pairs = len(all_comparisons)
        top_n = int(total_pairs * top_percent)
        if top_n < 1: top_n = 1
        
        # Determine sort key
        def get_sort_key(comp):
            if top_metric == "avg_score":
                return comp['avg_score'] # Average of 2 source metrics
            elif top_metric == "levenshtein":
                return comp['source_similarity']['levenshtein'] # Ignore Hex levenshtein
            elif top_metric in comp['source_similarity']:
                return comp['source_similarity'][top_metric]
            else:
                return comp['avg_score'] # Fallback
        
        all_comparisons.sort(key=get_sort_key, reverse=True)
        filtered_pairs = all_comparisons[:top_n]
        print(f"Selected top {top_n} pairs ({top_percent*100}%) based on {top_metric}")

    
    print(f"Step 4: Analyzing {len(filtered_pairs)} suspicious pairs...")
    results = []
    
    for comp in tqdm(filtered_pairs, desc="Analyzing pairs", unit="pair"):
        student1 = comp['student1']
        student2 = comp['student2']
        
        llm_result = None
        llm_triggered = False
        verdict = "未抄襲"
        verdict_reason = ""
        
        # Rule 1: Hex max score = 1.0 OR Source avg score = 1.0 → Definite plagiarism, skip LLM
        if comp['max_hex_sim'] == 1.0 or comp['avg_score'] == 1.0:
            verdict = "抄襲"
            verdict_reason = "Hex檔案或原始碼完全相同 (100%)"
            llm_triggered = False

        # Rule 2: Trigger LLM for ALL suspicious pairs (except definite plagiarism)
        else:
            llm_triggered = True
            # Need to retrieve source code again
            src1 = student_data[student1]['source']
            src2 = student_data[student2]['source']
            
            llm_result = analyze_pair_with_llm(src1, src2)
            
            # Rule 3: Use LLM result if available
            if llm_result and 'is_plagiarized' in llm_result:
                verdict = "抄襲" if llm_result['is_plagiarized'] else "未抄襲"
                verdict_reason = f"LLM分析: {llm_result.get('reasoning', 'N/A')}"
            else:
                # LLM unavailable, fallback to algorithm
                verdict = "抄襲" if comp['avg_score'] > 0.85 else "未抄襲"
                verdict_reason = f"LLM分析不可用 - 演算法分析: Hex={comp['max_hex_sim']:.2f}, Source Avg={comp['avg_score']:.2f}"
        
        
        # Check for illegal submission - but only override if NOT plagiarized
        if (student_data[student1]['illegal_submission'] or student_data[student2]['illegal_submission']) and verdict != "抄襲":
            verdict = "無效提交"
            illegal_names = []
            if student_data[student1]['illegal_submission']:
                illegal_names.append(student1)
            if student_data[student2]['illegal_submission']:
                illegal_names.append(student2)
            verdict_reason = f"無效提交: {', '.join(illegal_names)}"
        
        # Merge comparison data with analysis results
        result_entry = comp.copy()
        result_entry.update({
            'llm_analysis': llm_result,
            'llm_triggered': llm_triggered,
            'final_verdict': verdict,
            'verdict_reason': verdict_reason,
            'source_code1': student_data[student1]['source'],
            'source_code2': student_data[student2]['source'],
            'original_source1': student_data[student1]['original_source'],
            'original_source2': student_data[student2]['original_source'],
            'illegal_submission1': student_data[student1]['illegal_submission'],
            'illegal_reason1': student_data[student1]['illegal_reason'],
            'illegal_submission2': student_data[student2]['illegal_submission'],
            'illegal_reason2': student_data[student2]['illegal_reason'],
            'illegal_reason2': student_data[student2]['illegal_reason'],
            'hex_code1': student_data[student1]['hex'],
            'hex_code2': student_data[student2]['hex'],
            'asm_source1': student_data[student1]['asm_source'],
            'asm_source2': student_data[student2]['asm_source']
        })
        
        results.append(result_entry)
            

    # Identify illegal students
    illegal_students = []
    for student, data in student_data.items():
        if data['illegal_submission']:
            illegal_students.append({
                'student': student,
                'reason': data['illegal_reason'],
                'files': data.get('all_files', [])
            })
    
    # Identify students with anomalies (but not illegal)
    anomaly_students = []
    for student, data in student_data.items():
        if data['has_anomaly'] and not data['illegal_submission']:
            anomaly_students.append({
                'student': student,
                'hex_anomalies': data['hex_anomalies'],
                'source_anomalies': data['source_anomalies'],
                'original_source': data['original_source'],
                'hex': data['hex']
            })

    # Sort by average score descending
    results.sort(key=lambda x: x['avg_score'], reverse=True)
    
    # Generate Report
    generate_html_report(results, hex_threshold, src_threshold, illegal_students, anomaly_students, lab_name,
                        filter_mode=filter_mode, top_metric=top_metric, top_percent=top_percent,
                        use_keil_compilation=use_keil_compilation)
    
    return results


if __name__ == "__main__":
    # --- Configuration ---
    LAB_NAME = "Lab 6"
    
    # Filter Configuration
    # Options: "threshold", "top_percent"
    FILTER_MODE = "top_percent"  
    
    # Mode 1: Threshold (Existing)
    HEX_THRESHOLD = 0.7
    SRC_THRESHOLD = 0.6

    # Mode 2: Top Percent (New)
    # Options: "token_seq", "levenshtein", "avg_score"
    TOP_METRIC = "avg_score"   
    TOP_PERCENT = 0.05         # Top 5% of pairs
    
    # C51 Compilation Configuration
    USE_KEIL_COMPILATION = False  # Set to True to enable C compilation
    KEIL_PATH = None              # Set path if not in default locations
    # ---------------------

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    root_path = os.path.join(repo_root, 'Lab 6')
    print(f"\nProcessing root path: {root_path}")

    results = check_plagiarism(
        root_path, 
        filter_mode=FILTER_MODE,
        hex_threshold=HEX_THRESHOLD, 
        src_threshold=SRC_THRESHOLD,
        top_metric=TOP_METRIC,
        top_percent=TOP_PERCENT,
        lab_name=LAB_NAME,
        use_keil_compilation=USE_KEIL_COMPILATION,
        keil_path=KEIL_PATH
    )
    

    print(f"\nFound {len(results)} suspicious pairs.")
