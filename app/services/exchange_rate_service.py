"""
åŒ¯çŽ‡æœå‹™
å¾ž Yahoo Finance æŠ“å– USD/TWD åŒ¯çŽ‡
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

# é è¨­åŒ¯çŽ‡
DEFAULT_USD_TWD_RATE = 32.5


def fetch_usd_twd_rate() -> Optional[float]:
    """
    å¾ž Yahoo Finance æŠ“å– USD/TWD åŒ¯çŽ‡
    è¿”å›ž None è¡¨ç¤ºæŠ“å–å¤±æ•—
    """
    try:
        ticker = yf.Ticker("TWD=X")
        data = ticker.history(period="1d")
        
        if data.empty:
            logger.warning("ç„¡æ³•å–å¾— USD/TWD åŒ¯çŽ‡è³‡æ–™")
            return None
        
        rate = float(data['Close'].iloc[-1])
        logger.info(f"å–å¾— USD/TWD åŒ¯çŽ‡: {rate:.4f}")
        return rate
        
    except Exception as e:
        logger.error(f"æŠ“å– USD/TWD åŒ¯çŽ‡å¤±æ•—: {e}")
        return None


def update_exchange_rate_sync(db: Session) -> float:
    """
    åŒæ­¥æ›´æ–°åŒ¯çŽ‡ï¼ˆä¾›æŽ’ç¨‹ä½¿ç”¨ï¼‰
    è¿”å›žç•¶å‰åŒ¯çŽ‡
    """
    rate = fetch_usd_twd_rate()
    
    if rate is None:
        # æŠ“å–å¤±æ•—ï¼Œä½¿ç”¨ç¾æœ‰åŒ¯çŽ‡æˆ–é è¨­å€¼
        existing = db.query(ExchangeRate).filter_by(
            from_currency="USD",
            to_currency="TWD"
        ).first()
        
        if existing:
            logger.info(f"ä½¿ç”¨ç¾æœ‰åŒ¯çŽ‡: {existing.rate}")
            return existing.rate
        else:
            logger.info(f"ä½¿ç”¨é è¨­åŒ¯çŽ‡: {DEFAULT_USD_TWD_RATE}")
            return DEFAULT_USD_TWD_RATE
    
    # æ›´æ–°æˆ–æ–°å¢žåŒ¯çŽ‡
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
    logger.info(f"åŒ¯çŽ‡å·²æ›´æ–°: USD/TWD = {rate:.4f}")
    return rate


async def get_exchange_rate(db: AsyncSession) -> dict:
    """
    å–å¾— USD/TWD åŒ¯çŽ‡
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
    æ‰‹å‹•è¨­å®šåŒ¯çŽ‡
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