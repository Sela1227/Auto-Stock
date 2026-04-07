"""
è¨‚é–±æºçˆ¬èŸ²æœå‹™
è² è²¬æŠ“å– RSS feed ä¸¦è§£æžè‚¡ç¥¨ä»£ç¢¼
"""
import re
import logging
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

# å¸¸è¦‹è‹±æ–‡è©žå½™ï¼ŒæŽ’é™¤é€™äº›ï¼ˆä¸æ˜¯è‚¡ç¥¨ä»£ç¢¼ï¼‰
COMMON_WORDS = {
    # å¸¸è¦‹è©ž
    'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD',
    'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'HAS', 'HIS', 'HOW', 'ITS', 'MAY',
    'NEW', 'NOW', 'OLD', 'SEE', 'WAY', 'WHO', 'BOY', 'DID', 'GET', 'HIM',
    'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'DAY', 'HAS', 'HIM', 'HIS',
    # é‡‘èžç›¸é—œå¸¸è¦‹è©ž
    'ETF', 'IPO', 'CEO', 'CFO', 'COO', 'NYSE', 'SEC', 'FED', 'GDP', 'CPI',
    'EPS', 'ROE', 'ROA', 'DCF', 'ATH', 'ATL', 'YOY', 'QOQ', 'MOM', 'TTM',
    'USA', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'TWD',
    # å…¶ä»–
    'AI', 'API', 'AWS', 'CEO', 'CTO', 'FAQ', 'CEO', 'PDF', 'URL', 'RSS',
    'BUY', 'SELL', 'HOLD', 'LONG', 'SHORT',
    # æœˆä»½/æ˜ŸæœŸ
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
    'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN',
}

# å·²çŸ¥çš„æœ‰æ•ˆç¾Žè‚¡ä»£ç¢¼æ¨¡å¼ï¼ˆå¯é¸ï¼šå¢žåŠ ç™½åå–®ï¼‰
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
    # æ›´å¤šå¯ä»¥æŒçºŒæ·»åŠ ...
}


class RSSFetcher:
    """RSS çˆ¬èŸ²"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_feed(self, url: str, since_date: datetime = None) -> List[Dict]:
        """
        æŠ“å– RSS feed
        
        Args:
            url: RSS feed URL
            since_date: åªæŠ“å–æ­¤æ—¥æœŸä¹‹å¾Œçš„æ–‡ç« 
        
        Returns:
            æ–‡ç« åˆ—è¡¨ [{title, link, published, content}, ...]
        """
        logger.info(f"æŠ“å– RSS: {url}")
        
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS è§£æžè­¦å‘Š: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries:
                # è§£æžç™¼å¸ƒæ—¥æœŸ
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])
                
                # éŽæ¿¾æ—¥æœŸ
                if since_date and published and published < since_date:
                    continue
                
                # å–å¾—å…§å®¹
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
            
            logger.info(f"å–å¾— {len(articles)} ç¯‡æ–‡ç« ")
            return articles
            
        except Exception as e:
            logger.error(f"æŠ“å– RSS å¤±æ•—: {e}")
            return []
    
    def extract_symbols(self, text: str) -> Set[str]:
        """
        å¾žæ–‡ç« å…§å®¹æå–è‚¡ç¥¨ä»£ç¢¼
        
        è¦å‰‡ï¼š
        - 1-5 å€‹å¤§å¯«å­—æ¯
        - æŽ’é™¤å¸¸è¦‹è‹±æ–‡è©ž
        - å¸¸è¦‹æ ¼å¼ï¼š$AAPL, (AAPL), AAPL:
        """
        if not text:
            return set()
        
        # ç§»é™¤ HTML æ¨™ç±¤
        soup = BeautifulSoup(text, 'html.parser')
        clean_text = soup.get_text()
        
        symbols = set()
        
        # æ¨¡å¼ 1: $AAPL æ ¼å¼ï¼ˆé«˜å¯ä¿¡åº¦ï¼‰
        dollar_pattern = r'\$([A-Z]{1,5})\b'
        for match in re.findall(dollar_pattern, clean_text):
            if match not in COMMON_WORDS:
                symbols.add(match)
        
        # æ¨¡å¼ 2: (AAPL) æ‹¬è™Ÿæ ¼å¼ï¼ˆé«˜å¯ä¿¡åº¦ï¼‰
        paren_pattern = r'\(([A-Z]{1,5})\)'
        for match in re.findall(paren_pattern, clean_text):
            if match not in COMMON_WORDS:
                symbols.add(match)
        
        # æ¨¡å¼ 3: ç¨ç«‹çš„ 1-5 å¤§å¯«å­—æ¯ï¼ˆéœ€é¡å¤–éŽæ¿¾ï¼‰
        # åªæŠ“å·²çŸ¥çš„è‚¡ç¥¨ä»£ç¢¼ï¼Œé¿å…èª¤åˆ¤
        word_pattern = r'\b([A-Z]{1,5})\b'
        for match in re.findall(word_pattern, clean_text):
            if match in KNOWN_SYMBOLS:
                symbols.add(match)
        
        return symbols
    
    def fetch_and_parse(self, url: str, since_date: datetime = None) -> List[Dict]:
        """
        æŠ“å–ä¸¦è§£æžï¼Œå›žå‚³è‚¡ç¥¨ä»£ç¢¼åˆ—è¡¨
        
        Returns:
            [{symbol, article_url, article_title, article_date}, ...]
        """
        articles = self.fetch_feed(url, since_date)
        
        results = []
        for article in articles:
            symbols = self.extract_symbols(article['content'])
            # æ¨™é¡Œä¹Ÿæ‰¾ä¸€ä¸‹
            symbols.update(self.extract_symbols(article['title']))
            
            for symbol in symbols:
                results.append({
                    'symbol': symbol,
                    'article_url': article['link'],
                    'article_title': article['title'],
                    'article_date': article['published'].date() if article['published'] else None,
                })
        
        logger.info(f"è§£æžå‡º {len(results)} å€‹è‚¡ç¥¨æåŠ")
        return results


# å–®ä¾‹
rss_fetcher = RSSFetcher()