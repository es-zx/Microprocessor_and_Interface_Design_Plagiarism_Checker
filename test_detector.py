import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from detector import calculate_combined_similarity

code1 = "mov a, #0x55; add a, r0"
code2 = "mov a, #0x55; add a, r1" # Small change
code3 = "clr a; mov r0, a" # Different

print(f"Code 1: {code1}")
print(f"Code 2: {code2}")
print(f"Code 3: {code3}")

sim12 = calculate_combined_similarity(code1, code2)
print(f"\nSimilarity 1-2: {sim12}")

sim13 = calculate_combined_similarity(code1, code3)
print(f"Similarity 1-3: {sim13}")

# Test with empty strings
print(f"\nSimilarity Empty: {calculate_combined_similarity('', '')}")
