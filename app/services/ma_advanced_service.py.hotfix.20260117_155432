"""
MA 強化分析服務
===============
提供均線進階分析功能
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def analyze_ma_advanced(df: pd.DataFrame, current_price: float, lookback_days: int = 30) -> Dict[str, Any]:
    """計算 MA 進階分析"""
    result = {}
    
    try:
        # 1. 距離均線百分比
        for ma_col, dist_key in [('ma20', 'dist_ma20'), ('ma50', 'dist_ma50'), ('ma200', 'dist_ma200'), ('ma250', 'dist_ma250')]:
            if ma_col in df.columns and len(df) > 0:
                ma_value = df[ma_col].iloc[-1]
                if pd.notna(ma_value) and ma_value > 0:
                    result[dist_key] = round((current_price - ma_value) / ma_value * 100, 2)
        
        # 2. 交叉偵測
        for short_ma, long_ma, prefix in [('ma20', 'ma50', '20_50'), ('ma50', 'ma200', '50_200'), ('ma20', 'ma200', '20_200')]:
            cross = _find_cross(df, short_ma, long_ma, lookback_days)
            if cross:
                if cross['type'] == 'golden':
                    result[f'golden_cross_{prefix}'] = True
                    result[f'golden_cross_{prefix}_days'] = cross['days_ago']
                else:
                    result[f'death_cross_{prefix}'] = True
                    result[f'death_cross_{prefix}_days'] = cross['days_ago']
        
        # 3. 排列分析
        result.update(_analyze_alignment(df, current_price))
        
        # 4. 支撐壓力
        result.update(_analyze_support_resistance(df, current_price))
        
    except Exception as e:
        logger.error(f"MA 進階分析錯誤: {e}")
    
    return result


def _find_cross(df: pd.DataFrame, short_ma: str, long_ma: str, lookback_days: int):
    """尋找交叉點"""
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
    """分析均線排列"""
    result = {'alignment_status': 'neutral', 'alignment_detail': '盤整', 'alignment_score': 2}
    
    if len(df) == 0:
        return result
    
    ma20 = df['ma20'].iloc[-1] if 'ma20' in df.columns else None
    ma50 = df['ma50'].iloc[-1] if 'ma50' in df.columns else None
    ma200 = df['ma200'].iloc[-1] if 'ma200' in df.columns else None
    
    if any(x is None or pd.isna(x) for x in [ma20, ma50, ma200]):
        return result
    
    score = sum([current_price > ma20, ma20 > ma50, ma50 > ma200, current_price > ma200])
    result['alignment_score'] = score
    
    if score >= 4 and current_price > ma20 > ma50 > ma200:
        result.update({'alignment_status': 'bullish', 'alignment_detail': '完美多頭排列'})
    elif score >= 3:
        result.update({'alignment_status': 'bullish', 'alignment_detail': '多頭排列'})
    elif score <= 1 and current_price < ma20 < ma50 < ma200:
        result.update({'alignment_status': 'bearish', 'alignment_detail': '完美空頭排列'})
    elif score <= 1:
        result.update({'alignment_status': 'bearish', 'alignment_detail': '空頭排列'})
    
    return result


def _analyze_support_resistance(df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
    """分析支撐壓力"""
    result = {'support_levels': [], 'resistance_levels': [], 'nearest_support': None, 'nearest_resistance': None}
    
    if len(df) == 0:
        return result
    
    supports, resistances = [], []
    
    for ma_name, ma_col in [('MA20', 'ma20'), ('MA50', 'ma50'), ('MA200', 'ma200'), ('MA250', 'ma250')]:
        if ma_col not in df.columns:
            continue
        ma_value = df[ma_col].iloc[-1]
        if pd.isna(ma_value):
            continue
        
        info = {'ma': ma_name, 'price': round(float(ma_value), 2), 'distance_pct': round((current_price - ma_value) / ma_value * 100, 2)}
        (supports if ma_value < current_price else resistances).append(info)
    
    supports.sort(key=lambda x: x['price'], reverse=True)
    resistances.sort(key=lambda x: x['price'])
    
    result['support_levels'] = supports
    result['resistance_levels'] = resistances
    if supports:
        result['nearest_support'] = supports[0]
    if resistances:
        result['nearest_resistance'] = resistances[0]
    
    return result
