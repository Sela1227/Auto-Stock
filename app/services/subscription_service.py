"""
è¨‚é–±ç²¾é¸æœå‹™
è² è²¬ç®¡ç†è¨‚é–±æºã€è™•ç†æŠ“å–çµæžœã€ç”¨æˆ¶è¨‚é–±
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.subscription import SubscriptionSource, AutoPick, UserSubscription
from app.services.rss_fetcher import rss_fetcher

logger = logging.getLogger(__name__)


class SubscriptionService:
    """è¨‚é–±ç²¾é¸æœå‹™"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================
    # è¨‚é–±æºç®¡ç†
    # ============================================================
    
    def get_all_sources(self, enabled_only: bool = True) -> List[SubscriptionSource]:
        """å–å¾—æ‰€æœ‰è¨‚é–±æº"""
        query = self.db.query(SubscriptionSource)
        if enabled_only:
            query = query.filter(SubscriptionSource.enabled == True)
        return query.all()
    
    def get_source_by_slug(self, slug: str) -> Optional[SubscriptionSource]:
        """æ ¹æ“š slug å–å¾—è¨‚é–±æº"""
        return self.db.query(SubscriptionSource).filter(
            SubscriptionSource.slug == slug
        ).first()
    
    def create_source(self, name: str, slug: str, url: str, 
                      type: str = "substack", description: str = None) -> SubscriptionSource:
        """å»ºç«‹è¨‚é–±æº"""
        source = SubscriptionSource(
            name=name,
            slug=slug,
            url=url,
            type=type,
            description=description,
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        logger.info(f"å»ºç«‹è¨‚é–±æº: {name} ({slug})")
        return source
    
    def init_default_sources(self):
        """åˆå§‹åŒ–é è¨­è¨‚é–±æº"""
        defaults = [
            {
                "name": "ç¾Žè‚¡å¤§å”",
                "slug": "uncle-stock",
                "url": "https://unclestocknotes.substack.com/feed",
                "type": "substack",
                "description": "ç¾Žè‚¡å¤§å”çš„æŠ•è³‡ç­†è¨˜",
            },
        ]
        
        for source_data in defaults:
            existing = self.get_source_by_slug(source_data["slug"])
            if not existing:
                self.create_source(**source_data)
    
    # ============================================================
    # æŠ“å–èˆ‡æ›´æ–°
    # ============================================================
    
    def fetch_source(self, source: SubscriptionSource, 
                     since_date: datetime = None, 
                     backfill: bool = False) -> Dict:
        """
        æŠ“å–å–®ä¸€è¨‚é–±æº
        
        Args:
            source: è¨‚é–±æº
            since_date: èµ·å§‹æ—¥æœŸ
            backfill: æ˜¯å¦ç‚ºå›žæº¯æ¨¡å¼ï¼ˆé¦–æ¬¡æŠ“å–ï¼‰
        
        Returns:
            {new: int, updated: int, symbols: [...]}
        """
        logger.info(f"é–‹å§‹æŠ“å–: {source.name}")
        
        # æ±ºå®šèµ·å§‹æ—¥æœŸ
        if backfill:
            since_date = datetime.now() - timedelta(days=30)
        elif since_date is None:
            # ä½¿ç”¨ä¸Šæ¬¡æŠ“å–æ™‚é–“ï¼Œæˆ–é è¨­ 1 å¤©å‰
            since_date = source.last_fetched_at or (datetime.now() - timedelta(days=1))
        
        # æŠ“å– RSS
        picks = rss_fetcher.fetch_and_parse(source.url, since_date)
        
        result = {"new": 0, "updated": 0, "symbols": []}
        
        # ç”¨ä¾†è¿½è¹¤æœ¬æ¬¡è™•ç†éŽçš„ symbolsï¼ˆé¿å…é‡è¤‡æ’å…¥ï¼‰
        processed_symbols = {}
        
        for pick in picks:
            symbol = pick["symbol"]
            
            # æª¢æŸ¥æ˜¯å¦åœ¨æœ¬æ¬¡è¿´åœˆä¸­å·²è™•ç†éŽ
            if symbol in processed_symbols:
                # æ›´æ–°æœ¬æ¬¡è¿´åœˆä¸­çš„è¨˜éŒ„
                existing_pick = processed_symbols[symbol]
                existing_pick.update_mention(
                    article_url=pick["article_url"],
                    article_title=pick["article_title"],
                    article_date=pick["article_date"],
                )
                result["updated"] += 1
                continue
            
            # æª¢æŸ¥è³‡æ–™åº«ä¸­æ˜¯å¦å·²å­˜åœ¨
            existing = self.db.query(AutoPick).filter(
                and_(
                    AutoPick.source_id == source.id,
                    AutoPick.symbol == symbol
                )
            ).first()
            
            if existing:
                # æ›´æ–°æåŠ
                existing.update_mention(
                    article_url=pick["article_url"],
                    article_title=pick["article_title"],
                    article_date=pick["article_date"],
                )
                processed_symbols[symbol] = existing
                result["updated"] += 1
            else:
                # æ–°å¢ž
                new_pick = AutoPick(
                    source_id=source.id,
                    symbol=symbol,
                    article_url=pick["article_url"],
                    article_title=pick["article_title"],
                    article_date=pick["article_date"],
                    first_seen_at=datetime.now(),
                    last_seen_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=30),
                    mention_count=1,
                )
                self.db.add(new_pick)
                processed_symbols[symbol] = new_pick
                result["new"] += 1
            
            if symbol not in result["symbols"]:
                result["symbols"].append(symbol)
        
        # æ›´æ–°æœ€å¾ŒæŠ“å–æ™‚é–“
        source.last_fetched_at = datetime.now()
        self.db.commit()
        
        logger.info(f"æŠ“å–å®Œæˆ: æ–°å¢ž {result['new']}, æ›´æ–° {result['updated']}")
        return result
    
    def fetch_all_sources(self, backfill: bool = False) -> Dict:
        """æŠ“å–æ‰€æœ‰å•Ÿç”¨çš„è¨‚é–±æº"""
        sources = self.get_all_sources(enabled_only=True)
        
        total_result = {"sources": [], "total_new": 0, "total_updated": 0}
        
        for source in sources:
            result = self.fetch_source(source, backfill=backfill)
            total_result["sources"].append({
                "name": source.name,
                "slug": source.slug,
                **result
            })
            total_result["total_new"] += result["new"]
            total_result["total_updated"] += result["updated"]
        
        return total_result
    
    # ============================================================
    # ç”¨æˆ¶è¨‚é–±
    # ============================================================
    
    def subscribe(self, user_id: int, source_id: int) -> bool:
        """ç”¨æˆ¶è¨‚é–±ä¾†æº"""
        existing = self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.source_id == source_id
            )
        ).first()
        
        if existing:
            return False  # å·²è¨‚é–±
        
        subscription = UserSubscription(
            user_id=user_id,
            source_id=source_id,
        )
        self.db.add(subscription)
        self.db.commit()
        logger.info(f"ç”¨æˆ¶ {user_id} è¨‚é–±äº†ä¾†æº {source_id}")
        return True
    
    def unsubscribe(self, user_id: int, source_id: int) -> bool:
        """ç”¨æˆ¶å–æ¶ˆè¨‚é–±"""
        subscription = self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.source_id == source_id
            )
        ).first()
        
        if not subscription:
            return False
        
        self.db.delete(subscription)
        self.db.commit()
        logger.info(f"ç”¨æˆ¶ {user_id} å–æ¶ˆè¨‚é–±ä¾†æº {source_id}")
        return True
    
    def get_user_subscriptions(self, user_id: int) -> List[SubscriptionSource]:
        """å–å¾—ç”¨æˆ¶è¨‚é–±çš„ä¾†æº"""
        subscriptions = self.db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id
        ).all()
        
        source_ids = [s.source_id for s in subscriptions]
        if not source_ids:
            return []
        
        return self.db.query(SubscriptionSource).filter(
            SubscriptionSource.id.in_(source_ids)
        ).all()
    
    def is_subscribed(self, user_id: int, source_id: int) -> bool:
        """æª¢æŸ¥ç”¨æˆ¶æ˜¯å¦å·²è¨‚é–±"""
        return self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.source_id == source_id
            )
        ).first() is not None
    
    # ============================================================
    # æŸ¥è©¢ç²¾é¸
    # ============================================================
    
    def get_active_picks(self, source_id: int = None, limit: int = 50) -> List[AutoPick]:
        """å–å¾—æœ‰æ•ˆçš„ç²¾é¸ï¼ˆæœªéŽæœŸï¼‰"""
        query = self.db.query(AutoPick).filter(
            AutoPick.expires_at > datetime.now()
        )
        
        if source_id:
            query = query.filter(AutoPick.source_id == source_id)
        
        return query.order_by(AutoPick.last_seen_at.desc()).limit(limit).all()
    
    def get_user_picks(self, user_id: int, limit: int = 50) -> List[Dict]:
        """å–å¾—ç”¨æˆ¶è¨‚é–±çš„æ‰€æœ‰ç²¾é¸"""
        # å–å¾—ç”¨æˆ¶è¨‚é–±çš„ä¾†æº
        subscribed_sources = self.get_user_subscriptions(user_id)
        if not subscribed_sources:
            return []
        
        source_ids = [s.id for s in subscribed_sources]
        
        # æŸ¥è©¢æœ‰æ•ˆçš„ç²¾é¸
        picks = self.db.query(AutoPick).filter(
            and_(
                AutoPick.source_id.in_(source_ids),
                AutoPick.expires_at > datetime.now()
            )
        ).order_by(AutoPick.last_seen_at.desc()).limit(limit).all()
        
        # çµ„åˆçµæžœ
        source_map = {s.id: s for s in subscribed_sources}
        results = []
        for pick in picks:
            pick_dict = pick.to_dict()
            pick_dict["source_name"] = source_map[pick.source_id].name
            pick_dict["source_slug"] = source_map[pick.source_id].slug
            results.append(pick_dict)
        
        return results
    
    def get_pick_by_symbol(self, source_id: int, symbol: str) -> Optional[AutoPick]:
        """æ ¹æ“šä¾†æºå’Œä»£ç¢¼å–å¾—ç²¾é¸"""
        return self.db.query(AutoPick).filter(
            and_(
                AutoPick.source_id == source_id,
                AutoPick.symbol == symbol
            )
        ).first()