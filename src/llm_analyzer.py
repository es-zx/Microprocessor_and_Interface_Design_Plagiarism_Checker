"""LLM analyzer (moved to src root)."""
import os

def get_llm_prompt(code1, code2):
    """
    Generates a prompt for the LLM to analyze two code snippets.
    """
    prompt = f"""
You are an expert code plagiarism detector for 8051 assembly and C.
Compare the following two code snippets and determine if they are plagiarized.
The codes are implemented for the same project, thus it is acceptable for algorithms to be very very similar, as long as some part of logic is different.
Ignore variable renaming, comment changes, or whitespace differences.
Focus on logic, use of registers, control flow, and algorithm structure.

左部分:
```
{code1}
```

右部分:
```
{code2}
```

Analyze the similarities and differences.
Conclude with a JSON object in the following format:
{{
    "reasoning": "Brief explanation of why...",
    "is_plagiarized": true/false
}}

Use Traditional Chinese to respond.
"""
    return prompt.strip()

import json
import re

import json
import re
import os

try:
    import google.generativeai as genai
except ImportError:
    genai = None

def analyze_pair_with_llm(code1, code2, api_key=None):
    """
    Sends the code pair to an LLM for analysis using Google Gemini API.
    """
    if not genai:
        return {
            "is_plagiarized": False,
            "reasoning": "Google Generative AI library not installed. Please run `pip install google-generativeai`."
        }
        
    # Try to get API key from env if not provided
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        
    if not api_key:
        return {
            "is_plagiarized": False,
            "reasoning": "No API Key provided. Please set GEMINI_API_KEY environment variable."
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite') # Use a fast and capable model
        
        prompt = get_llm_prompt(code1, code2)
        # Force JSON format in prompt if not already clear, though the prompt function does it.
        # Gemini doesn't have a strict 'json_object' mode like OpenAI, so we rely on the prompt.
        
        response = model.generate_content(prompt)
        content = response.text
        
        # Parse JSON response
        try:
            # Clean up markdown code blocks if present
            content = content.replace('```json', '').replace('```', '')
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # Fallback if not valid JSON (try to extract json block)
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                return {
                    "is_plagiarized": False,
                    "confidence_score": 0.0,
                    "reasoning": f"Failed to parse LLM response: {content[:100]}..."
                }
                
    except Exception as e:
        return {
            "is_plagiarized": False,
            "confidence_score": 0.0,
            "reasoning": f"LLM API Error: {str(e)}"
        }

def analyze_pair_dummy(code1, code2):
    """
    Dummy analysis for testing without API.
    """
    return {
        "is_plagiarized": True,
        "confidence_score": 0.95,
        "reasoning": "Mock analysis: High structural similarity detected (Dummy Mode)."
    }
