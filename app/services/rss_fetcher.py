"""
訂閱源爬蟲服務
負責抓取 RSS feed 並解析股票代碼
"""
import re
import logging
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

# 常見英文詞彙，排除這些（不是股票代碼）
COMMON_WORDS = {
    # 常見詞
    'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD',
    'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'HAS', 'HIS', 'HOW', 'ITS', 'MAY',
    'NEW', 'NOW', 'OLD', 'SEE', 'WAY', 'WHO', 'BOY', 'DID', 'GET', 'HIM',
    'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'DAY', 'HAS', 'HIM', 'HIS',
    # 金融相關常見詞
    'ETF', 'IPO', 'CEO', 'CFO', 'COO', 'NYSE', 'SEC', 'FED', 'GDP', 'CPI',
    'EPS', 'ROE', 'ROA', 'DCF', 'ATH', 'ATL', 'YOY', 'QOQ', 'MOM', 'TTM',
    'USA', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'TWD',
    # 其他
    'AI', 'API', 'AWS', 'CEO', 'CTO', 'FAQ', 'CEO', 'PDF', 'URL', 'RSS',
    'BUY', 'SELL', 'HOLD', 'LONG', 'SHORT',
    # 月份/星期
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
    'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN',
}

# 已知的有效美股代碼模式（可選：增加白名單）
KNOWN_SYMBOLS = {
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
    'BRK', 'UNH', 'JNJ', 'V', 'XOM', 'WMT', 'JPM', 'MA', 'PG', 'HD',
    'CVX', 'MRK', 'ABBV', 'LLY', 'PFE', 'KO', 'PEP', 'COST', 'TMO',
    'AVGO', 'MCD', 'CSCO', 'ACN', 'ABT', 'DHR', 'NKE', 'TXN', 'NEE',
    'PM', 'UNP', 'RTX', 'HON', 'LOW', 'IBM', 'ORCL', 'AMD', 'INTC',
    'QCOM', 'SPGI', 'CAT', 'GE', 'BA', 'SBUX', 'INTU', 'AMAT', 'GS',
    'BLK', 'DE', 'MDLZ', 'AXP', 'ADI', 'ISRG', 'GILD', 'VRTX', 'REGN',
    'BKNG', 'SYK', 'MMC', 'ZTS', 'LRCX', 'ETN', 'CB', 'CI', 'SO',
    'DUK', 'CME', 'PLD', 'BSX', 'CL', 'MO', 'AON', 'APD', 'ICE',
    'SCHW', 'SHW', 'NOC', 'FIS', 'EQIX', 'NSC', 'FCX', 'MCK', 'EMR',
    'PNC', 'GM', 'F', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI',
    'PLTR', 'SNOW', 'NET', 'DDOG', 'ZS', 'CRWD', 'PANW', 'OKTA',
    'SQ', 'SHOP', 'PYPL', 'COIN', 'HOOD', 'SOFI', 'UPST', 'AFRM',
    'RBLX', 'U', 'TTWO', 'EA', 'ATVI', 'NFLX', 'DIS', 'PARA', 'WBD',
    'ABNB', 'UBER', 'LYFT', 'DASH', 'GRAB', 'SE',
    'ARM', 'SMCI', 'DELL', 'HPQ', 'HPE',
    'CCJ', 'VST', 'LENZ', 'GOOS', 'CAVA', 'QS', 'ONDS',
    # 更多可以持續添加...
}


class RSSFetcher:
    """RSS 爬蟲"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_feed(self, url: str, since_date: datetime = None) -> List[Dict]:
        """
        抓取 RSS feed
        
        Args:
            url: RSS feed URL
            since_date: 只抓取此日期之後的文章
        
        Returns:
            文章列表 [{title, link, published, content}, ...]
        """
        logger.info(f"抓取 RSS: {url}")
        
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS 解析警告: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries:
                # 解析發布日期
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])
                
                # 過濾日期
                if since_date and published and published < since_date:
                    continue
                
                # 取得內容
                content = ""
                if hasattr(entry, 'content') and entry.content:
                    content = entry.content[0].value
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                
                articles.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': published,
                    'content': content,
                })
            
            logger.info(f"取得 {len(articles)} 篇文章")
            return articles
            
        except Exception as e:
            logger.error(f"抓取 RSS 失敗: {e}")
            return []
    
    def extract_symbols(self, text: str) -> Set[str]:
        """
        從文章內容提取股票代碼
        
        規則：
        - 1-5 個大寫字母
        - 排除常見英文詞
        - 常見格式：$AAPL, (AAPL), AAPL:
        """
        if not text:
            return set()
        
        # 移除 HTML 標籤
        soup = BeautifulSoup(text, 'html.parser')
        clean_text = soup.get_text()
        
        symbols = set()
        
        # 模式 1: $AAPL 格式（高可信度）
        dollar_pattern = r'\$([A-Z]{1,5})\b'
        for match in re.findall(dollar_pattern, clean_text):
            if match not in COMMON_WORDS:
                symbols.add(match)
        
        # 模式 2: (AAPL) 括號格式（高可信度）
        paren_pattern = r'\(([A-Z]{1,5})\)'
        for match in re.findall(paren_pattern, clean_text):
            if match not in COMMON_WORDS:
                symbols.add(match)
        
        # 模式 3: 獨立的 1-5 大寫字母（需額外過濾）
        # 只抓已知的股票代碼，避免誤判
        word_pattern = r'\b([A-Z]{1,5})\b'
        for match in re.findall(word_pattern, clean_text):
            if match in KNOWN_SYMBOLS:
                symbols.add(match)
        
        return symbols
    
    def fetch_and_parse(self, url: str, since_date: datetime = None) -> List[Dict]:
        """
        抓取並解析，回傳股票代碼列表
        
        Returns:
            [{symbol, article_url, article_title, article_date}, ...]
        """
        articles = self.fetch_feed(url, since_date)
        
        results = []
        for article in articles:
            symbols = self.extract_symbols(article['content'])
            # 標題也找一下
            symbols.update(self.extract_symbols(article['title']))
            
            for symbol in symbols:
                results.append({
                    'symbol': symbol,
                    'article_url': article['link'],
                    'article_title': article['title'],
                    'article_date': article['published'].date() if article['published'] else None,
                })
        
        logger.info(f"解析出 {len(results)} 個股票提及")
        return results


# 單例
rss_fetcher = RSSFetcher()
