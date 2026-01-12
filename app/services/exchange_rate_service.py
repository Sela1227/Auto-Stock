"""
匯率服務
從 Yahoo Finance 抓取 USD/TWD 匯率
"""
import logging
from datetime import datetime
from typing import Optional

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.portfolio import ExchangeRate

logger = logging.getLogger(__name__)

# 預設匯率
DEFAULT_USD_TWD_RATE = 32.5


def fetch_usd_twd_rate() -> Optional[float]:
    """
    從 Yahoo Finance 抓取 USD/TWD 匯率
    返回 None 表示抓取失敗
    """
    try:
        ticker = yf.Ticker("TWD=X")
        data = ticker.history(period="1d")
        
        if data.empty:
            logger.warning("無法取得 USD/TWD 匯率資料")
            return None
        
        rate = float(data['Close'].iloc[-1])
        logger.info(f"取得 USD/TWD 匯率: {rate:.4f}")
        return rate
        
    except Exception as e:
        logger.error(f"抓取 USD/TWD 匯率失敗: {e}")
        return None


def update_exchange_rate_sync(db: Session) -> float:
    """
    同步更新匯率（供排程使用）
    返回當前匯率
    """
    rate = fetch_usd_twd_rate()
    
    if rate is None:
        # 抓取失敗，使用現有匯率或預設值
        existing = db.query(ExchangeRate).filter_by(
            from_currency="USD",
            to_currency="TWD"
        ).first()
        
        if existing:
            logger.info(f"使用現有匯率: {existing.rate}")
            return existing.rate
        else:
            logger.info(f"使用預設匯率: {DEFAULT_USD_TWD_RATE}")
            return DEFAULT_USD_TWD_RATE
    
    # 更新或新增匯率
    existing = db.query(ExchangeRate).filter_by(
        from_currency="USD",
        to_currency="TWD"
    ).first()
    
    if existing:
        existing.rate = rate
        existing.updated_at = datetime.utcnow()
    else:
        new_rate = ExchangeRate(
            from_currency="USD",
            to_currency="TWD",
            rate=rate,
        )
        db.add(new_rate)
    
    db.commit()
    logger.info(f"匯率已更新: USD/TWD = {rate:.4f}")
    return rate


async def get_exchange_rate(db: AsyncSession) -> dict:
    """
    取得 USD/TWD 匯率
    """
    stmt = select(ExchangeRate).where(
        ExchangeRate.from_currency == "USD",
        ExchangeRate.to_currency == "TWD"
    )
    result = await db.execute(stmt)
    rate_record = result.scalar_one_or_none()
    
    if rate_record:
        return {
            "rate": rate_record.rate,
            "updated_at": rate_record.updated_at.isoformat() if rate_record.updated_at else None,
        }
    else:
        return {
            "rate": DEFAULT_USD_TWD_RATE,
            "updated_at": None,
            "is_default": True,
        }


async def set_exchange_rate(db: AsyncSession, rate: float) -> dict:
    """
    手動設定匯率
    """
    stmt = select(ExchangeRate).where(
        ExchangeRate.from_currency == "USD",
        ExchangeRate.to_currency == "TWD"
    )
    result = await db.execute(stmt)
    rate_record = result.scalar_one_or_none()
    
    if rate_record:
        rate_record.rate = rate
        rate_record.updated_at = datetime.utcnow()
    else:
        rate_record = ExchangeRate(
            from_currency="USD",
            to_currency="TWD",
            rate=rate,
        )
        db.add(rate_record)
    
    await db.commit()
    await db.refresh(rate_record)
    
    return rate_record.to_dict()
