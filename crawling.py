import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def get_previous_weekday():
    today = datetime.now()
    day_of_week = today.weekday()
    
    if day_of_week == 0: # today = 월요일, previous = 금요일; 3일 전
        previous_day = today-timedelta(days=3)
    elif day_of_week == 6: # today = 일요일, previous = 금요일; 2일 전
        previous_day = today - timedelta(days=2)
    else:
        previous_day = today-timedelta(days=1)
    
    return previous_day.strftime("%Y-%m-%d")

# 허깅페이스 url
def crawling_data():
    
    base_url = "https://huggingface.co"
    date = get_previous_weekday()
    paper_url = f"https://huggingface.co/papers/date/{date}"
    print(paper_url)
    
    paper_page = requests.get(paper_url)
    paper_soup = BeautifulSoup(paper_page.text, "html.parser")

    today_papers_list = paper_soup.find_all("article")
    print(f"{date} 페이퍼 개수 : {len(today_papers_list)}개")

    papers = {}
    for paper in today_papers_list:
        link = paper.a.get("href")
        full_url = base_url+link
        
        content = requests.get(full_url)
        soup = BeautifulSoup(content.text, "html.parser")
        
        # 내용 추출
        title = soup.find("h1", class_="mb-2 text-2xl font-semibold sm:text-3xl lg:pr-6 lg:text-3xl xl:pr-10 2xl:text-4xl").text.replace("\n ","")
        abstract = soup.find("p", class_="text-gray-600").text
        papers[(title, full_url)] = abstract
    print(papers, len(papers))
    
    return papers, date