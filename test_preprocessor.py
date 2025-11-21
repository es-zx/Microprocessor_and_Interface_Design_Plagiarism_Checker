import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from preprocessor import crawl_directory, clean_code, normalize_hex

# Path to the student data
root_path = r'c:/codes/plagiarism_check_v3/1141_E930600-程式碼與hex-20251120'

print("Crawling directory...")
student_files = crawl_directory(root_path)

print(f"Found {len(student_files)} students.")

for student, files in list(student_files.items())[:3]: # Print first 3 students
    print(f"\nStudent: {student}")
    print(f"Source files: {len(files['source'])}")
    print(f"Hex files: {len(files['hex'])}")
    
    if files['source']:
        with open(files['source'][0], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            cleaned = clean_code(content, os.path.splitext(files['source'][0])[1])
            print(f"Sample cleaned source (first 50 chars): {cleaned[:50]}...")
            
    if files['hex']:
        with open(files['hex'][0], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            normalized = normalize_hex(content)
            print(f"Sample normalized hex (first 50 chars): {normalized[:50]}...")
