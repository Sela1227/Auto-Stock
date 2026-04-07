"""
MA å¼·åŒ–åˆ†æžæœå‹™
===============
æä¾›å‡ç·šé€²éšŽåˆ†æžåŠŸèƒ½
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

def _to_python_type(value):
    """å°‡ numpy é¡žåž‹è½‰æ›ç‚º Python åŽŸç”Ÿé¡žåž‹"""
    if value is None:
        return None
    if hasattr(value, 'item'):  # numpy scalar
        return value.item()
    if isinstance(value, (list, tuple)):
        return [_to_python_type(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_python_type(v) for k, v in value.items()}
    return value



logger = logging.getLogger(__name__)


def analyze_ma_advanced(df: pd.DataFrame, current_price: float, lookback_days: int = 30) -> Dict[str, Any]:
    """è¨ˆç®— MA é€²éšŽåˆ†æž"""
    result = {}
    
    try:
        # 1. è·é›¢å‡ç·šç™¾åˆ†æ¯”
        for ma_col, dist_key in [('ma20', 'dist_ma20'), ('ma50', 'dist_ma50'), ('ma200', 'dist_ma200'), ('ma250', 'dist_ma250')]:
            if ma_col in df.columns and len(df) > 0:
                ma_value = df[ma_col].iloc[-1]
                if pd.notna(ma_value) and ma_value > 0:
                    result[dist_key] = float(round((current_price - ma_value) / ma_value * 100, 2))
        
        # 2. äº¤å‰åµæ¸¬
        for short_ma, long_ma, prefix in [('ma20', 'ma50', '20_50'), ('ma50', 'ma200', '50_200'), ('ma20', 'ma200', '20_200')]:
            cross = _find_cross(df, short_ma, long_ma, lookback_days)
            if cross:
                if cross['type'] == 'golden':
                    result[f'golden_cross_{prefix}'] = True
                    result[f'golden_cross_{prefix}_days'] = cross['days_ago']
                else:
                    result[f'death_cross_{prefix}'] = True
                    result[f'death_cross_{prefix}_days'] = cross['days_ago']
        
        # 3. æŽ’åˆ—åˆ†æž
        result.update(_analyze_alignment(df, current_price))
        
        # 4. æ”¯æ’å£“åŠ›
        result.update(_analyze_support_resistance(df, current_price))
        
    except Exception as e:
        logger.error(f"MA é€²éšŽåˆ†æžéŒ¯èª¤: {e}")
    
    return _to_python_type(result)


def _find_cross(df: pd.DataFrame, short_ma: str, long_ma: str, lookback_days: int):
    """å°‹æ‰¾äº¤å‰é»ž"""
    if short_ma not in df.columns or long_ma not in df.columns or len(df) < 2:
        return None
    
    max_lookback = min(lookback_days, len(df) - 1)
    
    for i in range(1, max_lookback + 1):
        idx, prev_idx = -i, -i - 1
        if abs(prev_idx) > len(df):
            break
        
        s_today, s_yest = df[short_ma].iloc[idx], df[short_ma].iloc[prev_idx]
        l_today, l_yest = df[long_ma].iloc[idx], df[long_ma].iloc[prev_idx]
        
        if any(pd.isna(x) for x in [s_today, s_yest, l_today, l_yest]):
            continue
        
        if s_yest < l_yest and s_today >= l_today:
            return {'type': 'golden', 'days_ago': i}
        if s_yest > l_yest and s_today <= l_today:
            return {'type': 'death', 'days_ago': i}
    
    return None


def _analyze_alignment(df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
    """åˆ†æžå‡ç·šæŽ’åˆ—"""
    result = {'alignment_status': 'neutral', 'alignment_detail': 'ç›¤æ•´', 'alignment_score': 2}
    
    if len(df) == 0:
        return _to_python_type(result)
    
    ma20 = df['ma20'].iloc[-1] if 'ma20' in df.columns else None
    ma50 = df['ma50'].iloc[-1] if 'ma50' in df.columns else None
    ma200 = df['ma200'].iloc[-1] if 'ma200' in df.columns else None
    
    if any(x is None or pd.isna(x) for x in [ma20, ma50, ma200]):
        return _to_python_type(result)
    
    score = sum([current_price > ma20, ma20 > ma50, ma50 > ma200, current_price > ma200])
    result['alignment_score'] = score
    
    if score >= 4 and current_price > ma20 > ma50 > ma200:
        result.update({'alignment_status': 'bullish', 'alignment_detail': 'å®Œç¾Žå¤šé ­æŽ’åˆ—'})
    elif score >= 3:
        result.update({'alignment_status': 'bullish', 'alignment_detail': 'å¤šé ­æŽ’åˆ—'})
    elif score <= 1 and current_price < ma20 < ma50 < ma200:
        result.update({'alignment_status': 'bearish', 'alignment_detail': 'å®Œç¾Žç©ºé ­æŽ’åˆ—'})
    elif score <= 1:
        result.update({'alignment_status': 'bearish', 'alignment_detail': 'ç©ºé ­æŽ’åˆ—'})
    
    return _to_python_type(result)


def _analyze_support_resistance(df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
    """åˆ†æžæ”¯æ’å£“åŠ›"""
    result = {'support_levels': [], 'resistance_levels': [], 'nearest_support': None, 'nearest_resistance': None}
    
    if len(df) == 0:
        return _to_python_type(result)
    
    supports, resistances = [], []
    
    for ma_name, ma_col in [('MA20', 'ma20'), ('MA50', 'ma50'), ('MA200', 'ma200'), ('MA250', 'ma250')]:
        if ma_col not in df.columns:
            continue
        ma_value = df[ma_col].iloc[-1]
        if pd.isna(ma_value):
            continue
        
        info = {'ma': ma_name, 'price': round(float(ma_value), 2), 'distance_pct': float(round((current_price - ma_value) / ma_value * 100, 2))}
        (supports if ma_value < current_price else resistances).append(info)
    
    supports.sort(key=lambda x: x['price'], reverse=True)
    resistances.sort(key=lambda x: x['price'])
    
    result['support_levels'] = supports
    result['resistance_levels'] = resistances
    if supports:
        result['nearest_support'] = supports[0]
    if resistances:
        result['nearest_resistance'] = resistances[0]
    
    return _to_python_type(result)