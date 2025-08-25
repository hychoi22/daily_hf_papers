import requests
import time
import os

# 포맷팅
def format_result(idx, date, item):
    intro = f"안녕하세요, {date} 페이퍼입니다.\n\n" if idx == 0 else ""
    
    # 기본
    if item["response"] is None:
        text = f"""<b>{idx+1}. [{item["keywords"]}] {item["title"]}</b>
link: {item["link"]}

"""
    else:
        text = f"""<b>{idx+1}. [{item["keywords"]}] {item["title"]}</b>
{item["response"] if item["response"] is not None else ""}
link: {item["link"]}

"""
    return intro+text

# 메시지 청킹
def prepare_msg(date, summarize):
    body = []
    current_text = ""
    max_length = 4000
    
    for idx, item in enumerate(summarize):
        text = format_result(idx, date, item)
        
        if len(current_text)+len(text) > max_length:
            body.append(current_text)
            current_text=text
        else:
            current_text+=text
    body.append(current_text)
    return body

# 메시지 전송
def send_telegram_msg(date, summarize):
    body = prepare_msg(date, summarize)
    
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    CHAT_ID = os.environ.get("CHAT_ID")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    for b in body:
        payload = {
            'chat_id' : CHAT_ID,
            'text': b,
            'parse_mode': 'HTML'
        }
        response=requests.post(url, data=payload)
        time.sleep(1)
    