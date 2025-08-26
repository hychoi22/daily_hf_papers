from crawling import crawling_data
from summary import summarize_with_llm
from telegram import send_telegram_msg
from send_email import send_automated_email

papers, date = crawling_data()
summarize = summarize_with_llm(papers)
send_telegram_msg(date, summarize) 
# send_automated_email(date, summarize)