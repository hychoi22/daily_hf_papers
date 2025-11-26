import os
import re
import time
import json
import google.generativeai as genai

# 통합된 LLM 요청 함수 (요약 + 도메인 분류)
def generate_summary_and_domain(model, PROMPT_1, PROMPT_2, content):
    
    # 프롬프트 통합
    full_prompt = f"""
    You are a helpful assistant for summarizing and classifying research papers.
    
    Task 1: Summarize the following paper in Korean.
    - {PROMPT_1}
    - The summary must be a single concise sentence in Korean.
    - Remove any Chinese or Japanese characters. Keep English words and numbers.
    
    Task 2: Classify the paper into one research domain.
    - {PROMPT_2}
    - Choose the most appropriate domain. If unsure, use "ETC".
    
    Input Paper Content:
    {content}
    
    Output Format:
    Provide the result in JSON format with keys "summary" and "domain".
    Example:
    {{
        "summary": "이 논문은 ...에 대한 것입니다.",
        "domain": "CV"
    }}
    """
    
    try:
        response = model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
        result_text = response.text.strip()
        
        # JSON 파싱
        try:
            result_json = json.loads(result_text)
            summary = result_json.get("summary", "요약 실패")
            domain = result_json.get("domain", "ETC")
            return summary, domain
        except json.JSONDecodeError:
            print(f"JSON parsing failed. Raw response: {result_text}")
            return None, "ETC"
            
    except Exception as e:
        print(f"Error during generation: {e}")
        return None, "ETC"


# 요약 및 번역
def summarize_with_llm(papers):
    PROMPT_1 = os.environ.get("PROMPT_1", "Summarize this paper.")
    PROMPT_2 = os.environ.get("PROMPT_2", "Classify this paper.")
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return []

    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    print("Gemini 모델 설정 완료")
    
    summarize = []

    for idx, (key, content) in enumerate(papers.items(), 1):
        title, link = key
        print("="*10, idx, title, "="*10)
        
        summary_text, domain = generate_summary_and_domain(model, PROMPT_1, PROMPT_2, content)
        
        result = {
            "title": title,
            "link": link,
            "response": summary_text,
            "keywords": domain
        }
        
        summarize.append(result)
        print(result)
        
        # Rate Limit 방지를 위한 대기 (10초)
        if idx < len(papers):
            print("Waiting 10 seconds for rate limit...")
            time.sleep(10)

    return summarize