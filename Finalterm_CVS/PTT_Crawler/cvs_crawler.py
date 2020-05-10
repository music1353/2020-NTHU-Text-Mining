import json
import requests
import time
import re

from bs4 import BeautifulSoup
from bs4.element import NavigableString

from .ptt_crawler import PttCrawler

class CVS_PttCrawler(PttCrawler):
    def __init__(self):
        super().__init__()

    def parse_score_and_cotent(self, tags):
        SCORE_TAG = '【評分】：'
        CONTENT_TAG = '【心得】：'
        END_TAG = '--'
        
        info = {
            'status': 404,
            'score': '',
            'content': ''
        }
        
        tags_text = tags.text
        if SCORE_TAG not in tags_text or CONTENT_TAG not in tags_text:
            print('格式不符')
            return info
        
        
        tags_text_split = re.split('【評分】：|【心得】：|--', tags_text)
        
        # score
        score = tags_text_split[1].split('\n')[0]
        
        # content
        content = ''
        for sent in tags_text_split[2].split('\n'):
            if sent and '--' not in sent:
                content = content + ' ' + sent
                
        info['status'] = 200

        # 處理score
        if '分' in score:
            score = score.split('分')[0]
        if '>' in score:
            score = score.split('>')[0]
        # 只保留数字
        temp_score = filter(str.isdigit, score)
        score = ''.join(list(temp_score))
        
        info['score'] = score

        # 處理content
        url_reg = r'[a-z]*[:.]+\S+'
        content = re.sub(url_reg, '', content)
        info['content'] = content
        
        return info

    def parse_article(self, url):
        raw  = self.session.get(url, verify=False)
        soup = BeautifulSoup(raw.text, "lxml")

        try:
            article = {}

            # 取得文章作者與文章標題
            article["Author"] = soup.select(".article-meta-value")[0].contents[0].split(" ")[0]
            article["Title"]  = soup.select(".article-meta-value")[2].contents[0]
            
            # 取得內文
            if '[商品]' in article["Title"]:
                tags = soup.select("#main-content")[0]
                info = self.parse_score_and_cotent(tags)

                if info['status'] == 200:
                    article['Score'] = info['score']
                    article['Content'] = info['content']

        except Exception as e:
            print(e)
            print(u"在分析 %s 時出現錯誤" % url)

        return article
    
    def crawl(self, board="Gossiping", start=1, end=2, sleep_time=0.5):
        count = 0
        crawl_range = range(start, end)

        for page in self.pages(board, crawl_range):
            res = []
            
            for article in self.articles(page):
                article_data = self.parse_article(article)

                if 'Score' in article_data:
                    res.append(article_data)
                    count += 1

                time.sleep(sleep_time)
            
            print(u"已經完成 %s 頁面第 %d 頁的爬取" %(board, start))
            self.output('cvs_data/' + board + str(start), res)
            
            start += 1

        print('成功爬取', count, '筆資料')