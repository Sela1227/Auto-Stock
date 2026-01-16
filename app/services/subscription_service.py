"""
訂閱精選服務
負責管理訂閱源、處理抓取結果、用戶訂閱
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
    """訂閱精選服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================
    # 訂閱源管理
    # ============================================================
    
    def get_all_sources(self, enabled_only: bool = True) -> List[SubscriptionSource]:
        """取得所有訂閱源"""
        query = self.db.query(SubscriptionSource)
        if enabled_only:
            query = query.filter(SubscriptionSource.enabled == True)
        return query.all()
    
    def get_source_by_slug(self, slug: str) -> Optional[SubscriptionSource]:
        """根據 slug 取得訂閱源"""
        return self.db.query(SubscriptionSource).filter(
            SubscriptionSource.slug == slug
        ).first()
    
    def create_source(self, name: str, slug: str, url: str, 
                      type: str = "substack", description: str = None) -> SubscriptionSource:
        """建立訂閱源"""
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
        logger.info(f"建立訂閱源: {name} ({slug})")
        return source
    
    def init_default_sources(self):
        """初始化預設訂閱源"""
        defaults = [
            {
                "name": "美股大叔",
                "slug": "uncle-stock",
                "url": "https://unclestocknotes.substack.com/feed",
                "type": "substack",
                "description": "美股大叔的投資筆記",
            },
        ]
        
        for source_data in defaults:
            existing = self.get_source_by_slug(source_data["slug"])
            if not existing:
                self.create_source(**source_data)
    
    # ============================================================
    # 抓取與更新
    # ============================================================
    
    def fetch_source(self, source: SubscriptionSource, 
                     since_date: datetime = None, 
                     backfill: bool = False) -> Dict:
        """
        抓取單一訂閱源
        
        Args:
            source: 訂閱源
            since_date: 起始日期
            backfill: 是否為回溯模式（首次抓取）
        
        Returns:
            {new: int, updated: int, symbols: [...]}
        """
        logger.info(f"開始抓取: {source.name}")
        
        # 決定起始日期
        if backfill:
            since_date = datetime.now() - timedelta(days=30)
        elif since_date is None:
            # 使用上次抓取時間，或預設 1 天前
            since_date = source.last_fetched_at or (datetime.now() - timedelta(days=1))
        
        # 抓取 RSS
        picks = rss_fetcher.fetch_and_parse(source.url, since_date)
        
        result = {"new": 0, "updated": 0, "symbols": []}
        
        # 用來追蹤本次處理過的 symbols（避免重複插入）
        processed_symbols = {}
        
        for pick in picks:
            symbol = pick["symbol"]
            
            # 檢查是否在本次迴圈中已處理過
            if symbol in processed_symbols:
                # 更新本次迴圈中的記錄
                existing_pick = processed_symbols[symbol]
                existing_pick.update_mention(
                    article_url=pick["article_url"],
                    article_title=pick["article_title"],
                    article_date=pick["article_date"],
                )
                result["updated"] += 1
                continue
            
            # 檢查資料庫中是否已存在
            existing = self.db.query(AutoPick).filter(
                and_(
                    AutoPick.source_id == source.id,
                    AutoPick.symbol == symbol
                )
            ).first()
            
            if existing:
                # 更新提及
                existing.update_mention(
                    article_url=pick["article_url"],
                    article_title=pick["article_title"],
                    article_date=pick["article_date"],
                )
                processed_symbols[symbol] = existing
                result["updated"] += 1
            else:
                # 新增
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
        
        # 更新最後抓取時間
        source.last_fetched_at = datetime.now()
        self.db.commit()
        
        logger.info(f"抓取完成: 新增 {result['new']}, 更新 {result['updated']}")
        return result
    
    def fetch_all_sources(self, backfill: bool = False) -> Dict:
        """抓取所有啟用的訂閱源"""
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
    # 用戶訂閱
    # ============================================================
    
    def subscribe(self, user_id: int, source_id: int) -> bool:
        """用戶訂閱來源"""
        existing = self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.source_id == source_id
            )
        ).first()
        
        if existing:
            return False  # 已訂閱
        
        subscription = UserSubscription(
            user_id=user_id,
            source_id=source_id,
        )
        self.db.add(subscription)
        self.db.commit()
        logger.info(f"用戶 {user_id} 訂閱了來源 {source_id}")
        return True
    
    def unsubscribe(self, user_id: int, source_id: int) -> bool:
        """用戶取消訂閱"""
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
        logger.info(f"用戶 {user_id} 取消訂閱來源 {source_id}")
        return True
    
    def get_user_subscriptions(self, user_id: int) -> List[SubscriptionSource]:
        """取得用戶訂閱的來源"""
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
        """檢查用戶是否已訂閱"""
        return self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.source_id == source_id
            )
        ).first() is not None
    
    # ============================================================
    # 查詢精選
    # ============================================================
    
    def get_active_picks(self, source_id: int = None, limit: int = 50) -> List[AutoPick]:
        """取得有效的精選（未過期）"""
        query = self.db.query(AutoPick).filter(
            AutoPick.expires_at > datetime.now()
        )
        
        if source_id:
            query = query.filter(AutoPick.source_id == source_id)
        
        return query.order_by(AutoPick.last_seen_at.desc()).limit(limit).all()
    
    def get_user_picks(self, user_id: int, limit: int = 50) -> List[Dict]:
        """取得用戶訂閱的所有精選"""
        # 取得用戶訂閱的來源
        subscribed_sources = self.get_user_subscriptions(user_id)
        if not subscribed_sources:
            return []
        
        source_ids = [s.id for s in subscribed_sources]
        
        # 查詢有效的精選
        picks = self.db.query(AutoPick).filter(
            and_(
                AutoPick.source_id.in_(source_ids),
                AutoPick.expires_at > datetime.now()
            )
        ).order_by(AutoPick.last_seen_at.desc()).limit(limit).all()
        
        # 組合結果
        source_map = {s.id: s for s in subscribed_sources}
        results = []
        for pick in picks:
            pick_dict = pick.to_dict()
            pick_dict["source_name"] = source_map[pick.source_id].name
            pick_dict["source_slug"] = source_map[pick.source_id].slug
            results.append(pick_dict)
        
        return results
    
    def get_pick_by_symbol(self, source_id: int, symbol: str) -> Optional[AutoPick]:
        """根據來源和代碼取得精選"""
        return self.db.query(AutoPick).filter(
            and_(
                AutoPick.source_id == source_id,
                AutoPick.symbol == symbol
            )
        ).first()
