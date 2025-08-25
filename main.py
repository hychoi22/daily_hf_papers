from crawling import crawling_data
from summary import summarize_with_llm
from telegram import send_telegram_msg

papers, date = crawling_data()
summarize = summarize_with_llm(papers)
send_telegram_msg(date, summarize) #Telegram
