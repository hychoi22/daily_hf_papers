import os
import re
from llama_cpp import Llama
# 답변 유효성 체크
def valid_response(text):
    msg = ""
    korean_pattern = re.compile(r"[가-힣]")
    foreign_pattern = re.compile(r'[ひらがなカタカナ]|[ぁ-ゔ]|[ァ-ヾ]|[\u4e00-\u9fff\u3400-\u4dbf]')
    
    # <think> 태그  처리
    if "<think>" in text:
        msg = f"Provide only the essential information in one line to Korean: {text}"
        return msg, False
    else:
        if bool(korean_pattern.search(text)):
            if not bool(foreign_pattern.search(text)):
                return msg, True
        msg = f"Translate to Korean. Remove all Chinese characters and Japanese characters. Keep English words and numbers unchanged: {text}"
    return msg, False

# LLM 모델 답변 생성
def generate_response(llm, PROMPT, content):
    
    msg = [
            {"role": "system", "content":PROMPT},
            {"role": "user", "content": f"Please read the following text and provide a one-sentence summary in Korean: {content}"}
        ]
    
    output = llm.create_chat_completion(
            messages = msg,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            stream=False
        )
    result = (output['choices'][0]['message']['content']).split("</think>")[-1].strip()
    
    MAX_RETRY = 3
    while MAX_RETRY>0:
        content, flag = valid_response(result)
        if flag:
            break
        print("답변 정제 시작 >> ", result)
        msg = [
            {"role": "user", "content": content}
        ]
        output = llm.create_chat_completion(
            messages = msg,
            max_tokens = 1024,
            temperature = 0.7,
            top_p = 0.9,
            stream = False
        )
        result = (output['choices'][0]['message']['content']).split("</think>")[-1].strip()
        MAX_RETRY -= 1
    
    if not flag:
        result = None
    
    return result


# LLM 모델 도메인 분류
def generate_domain (llm, PROMPT, content):
    msg = [
            {"role": "system", "content":PROMPT},
            {"role": "user", "content": f"Classify this research paper into one research domain: {content}"}
        ]
    output = llm.create_chat_completion(
            messages = msg,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            stream=False
        )
    result = (output['choices'][0]['message']['content']).split("</think>")[-1].strip()
    if "<think>" in result:
        result = "ETC"
    return result


# 요약 및 번역
def summarize_with_llm(papers):
    PROMPT_1 = os.environ.get("PROMPT_1")
    PROMPT_2 = os.environ.get("PROMPT_2")
    
    settings = {
        "n_ctx": 2048,
        "n_batch": 512,
        "n_threads": 4,
        "n_gpu_layers": 0, # CPU 사용
        "verbose": False,
        "seed": -1,
        "f16_kv": True,
        "use_mlock": False,
        "use_mmap": True,
    }
    
    # 요약 및 번역
    repo_id_1 = "Qwen/Qwen3-1.7B-GGUF"
    file_name_1 = "Qwen3-1.7B-Q8_0.gguf"
    
    llm1 = Llama.from_pretrained(
        repo_id=repo_id_1,
        filename=file_name_1,
        **settings,
        chat_format = "qwen"
    )
    print("요약 모델 업로드 완료")
    temp={}
    
    for idx, (key, content) in enumerate(papers.items(),1):
        output1 = generate_response(llm1, PROMPT_1, content)
        print(f"{idx}>>", output1)
        temp[key] = output1
    
    # 첫 번째 모델 해제
    del llm1
    print("요약 완료 및 모델 해제")
    
    # 키워드
    repo_id_2 = "Qwen/Qwen3-0.6B-GGUF"
    file_name_2 = "Qwen3-0.6B-Q8_0.gguf"
    
    llm2 = Llama.from_pretrained(
        repo_id=repo_id_2,
        filename=file_name_2,
        **settings,
        chat_format = "qwen"
    )
    print("키워드 모델 업로드 완료")
    summarize = []

    for idx, (key, content) in enumerate(papers.items(),1):
        title, link = key
        result={
            "title": title,
            "link": link,
            "response" : temp[key],
            "keywords" : None
        }
        print("="*10, idx, title, "="*10)
        
        output2 = generate_domain(llm2, PROMPT_2, content)
        
        result["keywords"] = output2
        summarize.append(result)
        print(result)

    return summarize