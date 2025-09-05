import os
import re
from llama_cpp import Llama
# 답변 유효성 체크
def valid_response(text):
    msg = ""
    korean_pattern = re.compile(r"[가-힣]")
    foreign_pattern = re.compile(r'[ひらがなカタカナ]|[ぁ-ゔ]|[ァ-ヾ]|[\u4e00-\u9fff\u3400-\u4dbf]')
    
    # <think> 태그 처리
    if "<think>" in text:
        msg = f"불필요한 추론 과정을 제거하고, 아래 논문의 핵심 내용만 한국어 한 문장으로 요약해줘:\n {text}"
        return msg, False
    else:
        if bool(korean_pattern.search(text)) and not bool(foreign_pattern.search(text)):
            return msg, True
        msg = f"아래 논문을 한국어로 번역해줘. 중국어나 일본어 문자는 모두 제거하고, 영어 단어와 숫자는 그대로 유지해줘:\n {text}"
    return msg, False


def postprocess_response(llm, text, max_retry=3):

    gen_kwargs = {
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "repeat_penalty": 1.15, 
        "stream": False,
    }

    result = (text.split("</think>")[-1]).strip()

    retry = 0
    while retry <= max_retry:
        reask_msg, is_valid = valid_response(result)
        if is_valid:
            return result 

        if retry == max_retry:
            return None 

        out = llm.create_chat_completion(
            messages=[{"role": "user", "content": reask_msg}],
            **gen_kwargs,
        )
        result = (out["choices"][0]["message"]["content"]).split("</think>")[-1].strip()
        retry += 1

    return None


# LLM 모델 답변 생성
def generate_response(llm, PROMPT, content):
    
    msg = [
            {"role": "system", "content":PROMPT},
            {"role": "user", "content": f"아래 영어 논문을 한국어 한 문장으로 간결하게 요약해줘.\n {content}"}
        ]
    
    output = llm.create_chat_completion(
            messages = msg,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            repeat_penalty=1.15,
            stream=False
        )
    first_rsp = (output['choices'][0]['message']['content']).split("</think>")[-1].strip()
    
    
    return postprocess_response(llm, first_rsp)


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
    repo_id_1 = "Qwen/Qwen3-4B-GGUF"
    file_name_1 = "Qwen3-4B-Q8_0.gguf"
    
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
        # print(f"{idx}>>", output1)
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