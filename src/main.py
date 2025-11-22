import os
import itertools
from tqdm import tqdm
from preprocessor import crawl_directory, clean_code, normalize_hex
from detector import calculate_combined_similarity
from llm_analyzer import analyze_pair_with_llm
from reporter import generate_html_report


def check_plagiarism(root_path, hex_threshold, src_threshold, lab_name="Lab"):

    """
    Main function to check plagiarism.

    """
    print("Step 1: Crawling and preprocessing...")
    student_files = crawl_directory(root_path)
    student_data = {}

    # Preprocess all data
    for student, files in student_files.items():
        student_data[student] = {'source': "", 'hex': "", 'original_source': "", 'illegal_submission': False, 'illegal_reason': ""}
        
        # Check for illegal submission (no source files or no hex files)
        if not files['source']:
            student_data[student]['illegal_submission'] = True
            if files['all_files']:
                # Found files but not valid source
                exts = set([os.path.splitext(f)[1] for f in files['all_files']])
                student_data[student]['illegal_reason'] = f"無效提交：找到 {', '.join(exts)} 檔案，但需要 .a51 檔案"
            else:
                student_data[student]['illegal_reason'] = "未找到任何檔案"
        
        # Combine all source files
        full_source = ""
        full_original_source = ""
        for src_file in files['source']:
            try:
                with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    ext = os.path.splitext(src_file)[1]
                    
                    # Store original content with filename header for display
                    filename = os.path.basename(src_file)
                    full_original_source += f"--- {filename} ---\n{content}\n\n"  
                    full_source += clean_code(content, ext) + " "
            except Exception as e:
                print(f"Error reading {src_file}: {e}")      

        student_data[student]['source'] = full_source.strip()
        student_data[student]['original_source'] = full_original_source.strip()
        
        # Combine all hex files
        full_hex = ""
        for hex_file in files['hex']:
            try:
                with open(hex_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    full_hex += normalize_hex(content)

            except Exception as e:
                print(f"Error reading {hex_file}: {e}")

        student_data[student]['hex'] = full_hex
        

        # Check if hex is empty (illegal submission)
        if not full_hex or full_hex.strip() == "":
            student_data[student]['illegal_submission'] = True
            if student_data[student]['illegal_reason']:
                student_data[student]['illegal_reason'] += " | 未找到有效的 hex 檔案"
            else:
                student_data[student]['illegal_reason'] = "無效提交：未找到有效的 hex 檔案"
        

    print("Step 2: Pairwise comparison...")
    students = list(student_data.keys())
    pairs = list(itertools.combinations(students, 2))

    results = []

    for student1, student2 in tqdm(pairs, desc="Comparing pairs", unit="pair"):
        # Source comparison
        src1 = student_data[student1]['source']
        src2 = student_data[student2]['source']
        src_sim = {'jaccard': 0, 'cosine': 0, 'levenshtein': 0}

        if src1 and src2:
            src_sim = calculate_combined_similarity(src1, src2)
            

        # Hex comparison
        hex1 = student_data[student1]['hex']
        hex2 = student_data[student2]['hex']
        hex_sim = {'jaccard': 0, 'cosine': 0, 'levenshtein': 0}
        if hex1 and hex2:
            hex_sim = calculate_combined_similarity(hex1, hex2)
   
        # Calculate max scores (Composite scores removed)
        max_src_sim = max(src_sim.values()) if src_sim else 0
        max_hex_sim = max(hex_sim.values()) if hex_sim else 0
        current_max = max(max_src_sim, max_hex_sim)
        
        # Screening: Hex any metric > 0.7 OR Source any metric > 0.8
        if max_hex_sim > hex_threshold or max_src_sim > src_threshold:
            llm_result = None
            llm_triggered = False
            verdict = "未抄襲"
            verdict_reason = ""
            
            # Rule 1: Hex max score = 1.0 → Definite plagiarism, skip LLM
            if max_hex_sim == 1.0:
                verdict = "抄襲"
                verdict_reason = "Hex檔案完全相同 (100%)"
                llm_triggered = False

            # Rule 2: Trigger LLM for ALL suspicious pairs (except definite plagiarism)
            else:
                llm_triggered = True
                llm_result = analyze_pair_with_llm(src1, src2)
                
                # Rule 3: Use LLM result if available
                if llm_result and 'is_plagiarized' in llm_result:
                    verdict = "抄襲" if llm_result['is_plagiarized'] else "未抄襲"
                    verdict_reason = f"LLM分析: {llm_result.get('reasoning', 'N/A')}"
                else:
                    # LLM unavailable, fallback to algorithm
                    verdict = "抄襲" if current_max > 0.85 else "未抄襲"
                    verdict_reason = f"LLM分析不可用 - 演算法分析: Hex Max={max_hex_sim:.2f}, Source Max={max_src_sim:.2f}"
            
            
            # Check for illegal submission - but only override if NOT plagiarized
            if (student_data[student1]['illegal_submission'] or student_data[student2]['illegal_submission']) and verdict != "抄襲":
                verdict = "無效提交"
                illegal_names = []
                if student_data[student1]['illegal_submission']:
                    illegal_names.append(student1)
                if student_data[student2]['illegal_submission']:
                    illegal_names.append(student2)
                verdict_reason = f"無效提交: {', '.join(illegal_names)}"
            
            results.append({
                'student1': student1,
                'student2': student2,
                'source_similarity': src_sim,
                'hex_similarity': hex_sim,
                'max_hex_sim': max_hex_sim,
                'max_src_sim': max_src_sim,
                'max_score': current_max,
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

                'hex_code1': hex1,

                'hex_code2': hex2

            })
            

    # Identify illegal students
    illegal_students = []

    for student, data in student_data.items():
        if data['illegal_submission']:
            illegal_students.append({
                'student': student,
                'reason': data['illegal_reason'],
                'files': data.get('all_files', [])
            })

    # Sort by max score descending
    results.sort(key=lambda x: x['max_score'], reverse=True)
    
    # Generate Report
    generate_html_report(results, hex_threshold, src_threshold, illegal_students, lab_name)
    
    return results


if __name__ == "__main__":
    # User can modify these directly
    lab_name = "Lab 5"
    hex_threshold = 0.7
    src_threshold = 0.8

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    root_path = os.path.join(repo_root, 'Lab 5')
    print(f"\nProcessing root path: {root_path}")

    results = check_plagiarism(root_path, hex_threshold, src_threshold, lab_name)
    

    print(f"\nFound {len(results)} suspicious pairs.")
    # for res in results[:5]:
    #     print(f"{res['student1']} vs {res['student2']}")
    #     print(f"  Source: {res['source_similarity']}")
    #     print(f"  Hex: {res['hex_similarity']}")

