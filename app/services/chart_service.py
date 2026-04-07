"""
åœ–è¡¨ç¹ªè£½æœå‹™
ä½¿ç”¨ matplotlib + mplfinance ç¹ªè£½æŠ€è¡“åˆ†æžåœ–è¡¨
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Circle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging

from app.config import settings, CHARTS_DIR

logger = logging.getLogger(__name__)

# è¨­å®šä¸­æ–‡å­—é«”
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# é¡è‰²å®šç¾©
COLORS = {
    "price": "#2196F3",      # åƒ¹æ ¼ç·š - è—è‰²
    "ma_short": "#FF9800",   # MA20 - æ©™è‰²
    "ma_mid": "#9C27B0",     # MA50 - ç´«è‰²
    "ma_long": "#F44336",    # MA200 - ç´…è‰²
    "volume_up": "#4CAF50",  # ä¸Šæ¼²æˆäº¤é‡ - ç¶ è‰²
    "volume_down": "#F44336", # ä¸‹è·Œæˆäº¤é‡ - ç´…è‰²
    "bb_fill": "#E3F2FD",    # å¸ƒæž—é€šé“å¡«å…… - æ·ºè—
    "bb_line": "#90CAF9",    # å¸ƒæž—é€šé“ç·š - è—è‰²
    "rsi": "#673AB7",        # RSI - æ·±ç´«
    "macd_dif": "#2196F3",   # MACD DIF - è—è‰²
    "macd_dea": "#FF9800",   # MACD DEA - æ©™è‰²
    "macd_hist_pos": "#4CAF50",  # MACD æ­£æŸ± - ç¶ è‰²
    "macd_hist_neg": "#F44336",  # MACD è² æŸ± - ç´…è‰²
    "kd_k": "#2196F3",       # K ç·š - è—è‰²
    "kd_d": "#FF9800",       # D ç·š - æ©™è‰²
    "golden_cross": "#4CAF50",   # é»ƒé‡‘äº¤å‰ - ç¶ è‰²
    "death_cross": "#F44336",    # æ­»äº¡äº¤å‰ - ç´…è‰²
    "grid": "#E0E0E0",       # ç¶²æ ¼ç·š
    "overbought": "#FFCDD2", # è¶…è²·å€ - æ·ºç´…
    "oversold": "#C8E6C9",   # è¶…è³£å€ - æ·ºç¶ 
}


class ChartService:
    """åœ–è¡¨ç¹ªè£½æœå‹™"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or CHARTS_DIR
        self.output_dir.mkdir(exist_ok=True)
    
    def plot_stock_analysis(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str = "",
        show_ma: bool = True,
        show_bollinger: bool = True,
        show_volume: bool = True,
        show_rsi: bool = True,
        show_macd: bool = True,
        show_kd: bool = False,
        show_signals: bool = True,
        days: int = 120,
        save_path: Optional[str] = None,
    ) -> str:
        """
        ç¹ªè£½å®Œæ•´è‚¡ç¥¨åˆ†æžåœ–è¡¨
        
        Args:
            df: å«æœ‰åƒ¹æ ¼å’ŒæŒ‡æ¨™çš„ DataFrame
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            name: è‚¡ç¥¨åç¨±
            show_ma: é¡¯ç¤ºå‡ç·š
            show_bollinger: é¡¯ç¤ºå¸ƒæž—é€šé“
            show_volume: é¡¯ç¤ºæˆäº¤é‡
            show_rsi: é¡¯ç¤º RSI
            show_macd: é¡¯ç¤º MACD
            show_kd: é¡¯ç¤º KD
            show_signals: æ¨™è¨˜äº¤å‰è¨Šè™Ÿ
            days: é¡¯ç¤ºå¤©æ•¸
            save_path: å„²å­˜è·¯å¾‘ï¼ˆä¸æŒ‡å®šå‰‡è‡ªå‹•ç”Ÿæˆï¼‰
            
        Returns:
            åœ–è¡¨æª”æ¡ˆè·¯å¾‘
        """
        # åªå–æœ€è¿‘ N å¤©è³‡æ–™
        if len(df) > days:
            df = df.tail(days).copy()
        else:
            df = df.copy()
        
        # ç¢ºä¿ date æ¬„ä½æ­£ç¢º
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        # è¨ˆç®—å­åœ–æ•¸é‡
        n_subplots = 1  # ä¸»åœ–
        if show_volume:
            n_subplots += 1
        if show_rsi:
            n_subplots += 1
        if show_macd:
            n_subplots += 1
        if show_kd:
            n_subplots += 1
        
        # è¨­å®šå­åœ–é«˜åº¦æ¯”ä¾‹
        height_ratios = [3]  # ä¸»åœ–
        if show_volume:
            height_ratios.append(1)
        if show_rsi:
            height_ratios.append(1)
        if show_macd:
            height_ratios.append(1.2)
        if show_kd:
            height_ratios.append(1)
        
        # å»ºç«‹åœ–è¡¨
        fig, axes = plt.subplots(
            n_subplots, 1,
            figsize=(14, 3 + n_subplots * 2),
            gridspec_kw={'height_ratios': height_ratios},
            sharex=True,
        )
        
        if n_subplots == 1:
            axes = [axes]
        
        ax_idx = 0
        
        # === ä¸»åœ–ï¼šåƒ¹æ ¼ + å‡ç·š + å¸ƒæž—é€šé“ ===
        ax_main = axes[ax_idx]
        ax_idx += 1
        
        self._plot_price(ax_main, df, show_ma, show_bollinger, show_signals)
        
        # æ¨™é¡Œ
        title = f"{symbol}"
        if name:
            title += f" - {name}"
        title += f"\næœ€å¾Œæ›´æ–°: {df.index[-1].strftime('%Y-%m-%d')} | æ”¶ç›¤: ${df['close'].iloc[-1]:.2f}"
        ax_main.set_title(title, fontsize=14, fontweight='bold', pad=10)
        
        # === æˆäº¤é‡ ===
        if show_volume:
            self._plot_volume(axes[ax_idx], df)
            ax_idx += 1
        
        # === RSI ===
        if show_rsi and 'rsi' in df.columns:
            self._plot_rsi(axes[ax_idx], df)
            ax_idx += 1
        
        # === MACD ===
        if show_macd and 'macd_dif' in df.columns:
            self._plot_macd(axes[ax_idx], df)
            ax_idx += 1
        
        # === KD ===
        if show_kd and 'kd_k' in df.columns:
            self._plot_kd(axes[ax_idx], df)
            ax_idx += 1
        
        # èª¿æ•´å¸ƒå±€
        plt.tight_layout()
        
        # å„²å­˜åœ–è¡¨
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"{symbol}_{timestamp}.png"
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"åœ–è¡¨å·²å„²å­˜: {save_path}")
        return str(save_path)
    
    def _plot_price(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        show_ma: bool,
        show_bollinger: bool,
        show_signals: bool,
    ):
        """ç¹ªè£½åƒ¹æ ¼ä¸»åœ–"""
        # å¸ƒæž—é€šé“ï¼ˆå…ˆç•«ï¼Œä½œç‚ºèƒŒæ™¯ï¼‰
        if show_bollinger and 'bb_upper' in df.columns:
            ax.fill_between(
                df.index,
                df['bb_lower'],
                df['bb_upper'],
                color=COLORS['bb_fill'],
                alpha=0.5,
                label='å¸ƒæž—é€šé“',
            )
            ax.plot(df.index, df['bb_middle'], color=COLORS['bb_line'], 
                   linewidth=0.8, linestyle='--', alpha=0.7)
        
        # åƒ¹æ ¼ç·š
        ax.plot(df.index, df['close'], color=COLORS['price'], 
               linewidth=1.5, label='æ”¶ç›¤åƒ¹')
        
        # å‡ç·š
        if show_ma:
            ma_short = f"ma{settings.MA_SHORT}"
            ma_mid = f"ma{settings.MA_MID}"
            ma_long = f"ma{settings.MA_LONG}"
            
            if ma_short in df.columns:
                ax.plot(df.index, df[ma_short], color=COLORS['ma_short'],
                       linewidth=1, label=f'MA{settings.MA_SHORT}')
            if ma_mid in df.columns:
                ax.plot(df.index, df[ma_mid], color=COLORS['ma_mid'],
                       linewidth=1, label=f'MA{settings.MA_MID}')
            if ma_long in df.columns:
                ax.plot(df.index, df[ma_long], color=COLORS['ma_long'],
                       linewidth=1, label=f'MA{settings.MA_LONG}')
        
        # æ¨™è¨˜äº¤å‰è¨Šè™Ÿ
        if show_signals and show_ma:
            self._mark_crossovers(ax, df)
        
        # è¨­å®š
        ax.set_ylabel('åƒ¹æ ¼ ($)', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
        ax.set_xlim(df.index[0], df.index[-1])
    
    def _mark_crossovers(self, ax: plt.Axes, df: pd.DataFrame):
        """æ¨™è¨˜å‡ç·šäº¤å‰é»ž"""
        ma_short = f"ma{settings.MA_SHORT}"
        ma_mid = f"ma{settings.MA_MID}"
        
        if ma_short not in df.columns or ma_mid not in df.columns:
            return
        
        for i in range(1, len(df)):
            # é»ƒé‡‘äº¤å‰
            if (df[ma_short].iloc[i-1] < df[ma_mid].iloc[i-1] and 
                df[ma_short].iloc[i] > df[ma_mid].iloc[i]):
                ax.scatter(df.index[i], df['close'].iloc[i], 
                          color=COLORS['golden_cross'], s=100, marker='^', 
                          zorder=5, edgecolors='white', linewidths=1)
            
            # æ­»äº¡äº¤å‰
            elif (df[ma_short].iloc[i-1] > df[ma_mid].iloc[i-1] and 
                  df[ma_short].iloc[i] < df[ma_mid].iloc[i]):
                ax.scatter(df.index[i], df['close'].iloc[i], 
                          color=COLORS['death_cross'], s=100, marker='v', 
                          zorder=5, edgecolors='white', linewidths=1)
    
    def _plot_volume(self, ax: plt.Axes, df: pd.DataFrame):
        """ç¹ªè£½æˆäº¤é‡"""
        colors = []
        for i in range(len(df)):
            if i == 0:
                colors.append(COLORS['volume_up'])
            elif df['close'].iloc[i] >= df['close'].iloc[i-1]:
                colors.append(COLORS['volume_up'])
            else:
                colors.append(COLORS['volume_down'])
        
        ax.bar(df.index, df['volume'], color=colors, alpha=0.7, width=0.8)
        
        # 20æ—¥å‡é‡ç·š
        if 'volume_ma20' in df.columns:
            ax.plot(df.index, df['volume_ma20'], color='orange', 
                   linewidth=1, label='20æ—¥å‡é‡')
            ax.legend(loc='upper left', fontsize=8)
        
        ax.set_ylabel('æˆäº¤é‡', fontsize=10)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
        
        # æ ¼å¼åŒ– Y è»¸
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
    
    def _plot_rsi(self, ax: plt.Axes, df: pd.DataFrame):
        """ç¹ªè£½ RSI"""
        # è¶…è²·è¶…è³£å€åŸŸ
        ax.axhspan(settings.RSI_OVERBOUGHT, 100, color=COLORS['overbought'], alpha=0.3)
        ax.axhspan(0, settings.RSI_OVERSOLD, color=COLORS['oversold'], alpha=0.3)
        
        # ä¸­ç·š
        ax.axhline(y=50, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=settings.RSI_OVERBOUGHT, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=settings.RSI_OVERSOLD, color='green', linestyle='--', linewidth=0.8, alpha=0.5)
        
        # RSI ç·š
        ax.plot(df.index, df['rsi'], color=COLORS['rsi'], linewidth=1.2, label='RSI')
        
        # è¨­å®š
        ax.set_ylabel('RSI', fontsize=10)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
        
        # æ¨™è¨˜æœ€æ–°å€¼
        latest_rsi = df['rsi'].iloc[-1]
        if not pd.isna(latest_rsi):
            ax.annotate(f'{latest_rsi:.1f}', 
                       xy=(df.index[-1], latest_rsi),
                       xytext=(5, 0), textcoords='offset points',
                       fontsize=9, color=COLORS['rsi'])
    
    def _plot_macd(self, ax: plt.Axes, df: pd.DataFrame):
        """ç¹ªè£½ MACD"""
        # é›¶è»¸
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
        
        # MACD æŸ±ç‹€åœ–
        colors = [COLORS['macd_hist_pos'] if v >= 0 else COLORS['macd_hist_neg'] 
                 for v in df['macd_hist']]
        ax.bar(df.index, df['macd_hist'], color=colors, alpha=0.6, width=0.8)
        
        # DIF å’Œ DEA ç·š
        ax.plot(df.index, df['macd_dif'], color=COLORS['macd_dif'], 
               linewidth=1.2, label='DIF')
        ax.plot(df.index, df['macd_dea'], color=COLORS['macd_dea'], 
               linewidth=1.2, label='DEA')
        
        # æ¨™è¨˜äº¤å‰é»ž
        for i in range(1, len(df)):
            if pd.isna(df['macd_dif'].iloc[i]) or pd.isna(df['macd_dea'].iloc[i]):
                continue
            # é»ƒé‡‘äº¤å‰
            if (df['macd_dif'].iloc[i-1] < df['macd_dea'].iloc[i-1] and 
                df['macd_dif'].iloc[i] > df['macd_dea'].iloc[i]):
                ax.scatter(df.index[i], df['macd_dif'].iloc[i], 
                          color=COLORS['golden_cross'], s=50, marker='^', zorder=5)
            # æ­»äº¡äº¤å‰
            elif (df['macd_dif'].iloc[i-1] > df['macd_dea'].iloc[i-1] and 
                  df['macd_dif'].iloc[i] < df['macd_dea'].iloc[i]):
                ax.scatter(df.index[i], df['macd_dif'].iloc[i], 
                          color=COLORS['death_cross'], s=50, marker='v', zorder=5)
        
        # è¨­å®š
        ax.set_ylabel('MACD', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
    
    def _plot_kd(self, ax: plt.Axes, df: pd.DataFrame):
        """ç¹ªè£½ KD"""
        # è¶…è²·è¶…è³£å€åŸŸ
        ax.axhspan(80, 100, color=COLORS['overbought'], alpha=0.3)
        ax.axhspan(0, 20, color=COLORS['oversold'], alpha=0.3)
        
        # ä¸­ç·š
        ax.axhline(y=50, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=80, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=20, color='green', linestyle='--', linewidth=0.8, alpha=0.5)
        
        # K å’Œ D ç·š
        ax.plot(df.index, df['kd_k'], color=COLORS['kd_k'], linewidth=1.2, label='K')
        ax.plot(df.index, df['kd_d'], color=COLORS['kd_d'], linewidth=1.2, label='D')
        
        # è¨­å®š
        ax.set_ylabel('KD', fontsize=10)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
        ax.set_xlabel('æ—¥æœŸ', fontsize=10)
    
    def plot_candlestick(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str = "",
        days: int = 60,
        save_path: Optional[str] = None,
    ) -> str:
        """
        ç¹ªè£½ K ç·šåœ–ï¼ˆä½¿ç”¨ mplfinanceï¼‰
        
        Args:
            df: OHLCV DataFrame
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            name: è‚¡ç¥¨åç¨±
            days: é¡¯ç¤ºå¤©æ•¸
            save_path: å„²å­˜è·¯å¾‘
            
        Returns:
            åœ–è¡¨æª”æ¡ˆè·¯å¾‘
        """
        try:
            import mplfinance as mpf
        except ImportError:
            logger.warning("mplfinance æœªå®‰è£ï¼Œä½¿ç”¨æ›¿ä»£æ–¹æ¡ˆ")
            return self._plot_candlestick_fallback(df, symbol, name, days, save_path)
        
        # æº–å‚™è³‡æ–™
        if len(df) > days:
            df = df.tail(days).copy()
        else:
            df = df.copy()
        
        # ç¢ºä¿ç´¢å¼•ç‚º DatetimeIndex
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        # ç¢ºä¿æ¬„ä½åç¨±æ­£ç¢ºï¼ˆmplfinance éœ€è¦å¤§å¯«ï¼‰
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
        })
        
        # æº–å‚™å‡ç·š
        ma_short = f"ma{settings.MA_SHORT}"
        ma_mid = f"ma{settings.MA_MID}"
        ma_long = f"ma{settings.MA_LONG}"
        
        addplots = []
        if ma_short in df.columns:
            addplots.append(mpf.make_addplot(df[ma_short], color=COLORS['ma_short']))
        if ma_mid in df.columns:
            addplots.append(mpf.make_addplot(df[ma_mid], color=COLORS['ma_mid']))
        if ma_long in df.columns:
            addplots.append(mpf.make_addplot(df[ma_long], color=COLORS['ma_long']))
        
        # è¨­å®šæ¨£å¼
        mc = mpf.make_marketcolors(
            up='#4CAF50',
            down='#F44336',
            edge='inherit',
            wick='inherit',
            volume='inherit',
        )
        style = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle='-',
            gridcolor=COLORS['grid'],
        )
        
        # å„²å­˜è·¯å¾‘
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"{symbol}_kline_{timestamp}.png"
        
        # æ¨™é¡Œ
        title = f"{symbol}"
        if name:
            title += f" - {name}"
        
        # ç¹ªè£½
        mpf.plot(
            df,
            type='candle',
            style=style,
            title=title,
            ylabel='åƒ¹æ ¼ ($)',
            ylabel_lower='æˆäº¤é‡',
            volume=True,
            addplot=addplots if addplots else None,
            figsize=(14, 8),
            savefig=str(save_path),
        )
        
        logger.info(f"Kç·šåœ–å·²å„²å­˜: {save_path}")
        return str(save_path)
    
    def _plot_candlestick_fallback(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str,
        days: int,
        save_path: Optional[str],
    ) -> str:
        """ç•¶ mplfinance ä¸å¯ç”¨æ™‚çš„æ›¿ä»£ K ç·šåœ–"""
        if len(df) > days:
            df = df.tail(days).copy()
        else:
            df = df.copy()
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), 
                                        gridspec_kw={'height_ratios': [3, 1]},
                                        sharex=True)
        
        # K ç·š
        width = 0.6
        width2 = 0.1
        
        up = df[df['close'] >= df['open']]
        down = df[df['close'] < df['open']]
        
        # ä¸Šæ¼² K ç·š
        ax1.bar(up.index, up['close'] - up['open'], width, bottom=up['open'], 
               color='#4CAF50', edgecolor='#4CAF50')
        ax1.bar(up.index, up['high'] - up['close'], width2, bottom=up['close'], 
               color='#4CAF50')
        ax1.bar(up.index, up['low'] - up['open'], width2, bottom=up['open'], 
               color='#4CAF50')
        
        # ä¸‹è·Œ K ç·š
        ax1.bar(down.index, down['close'] - down['open'], width, bottom=down['open'], 
               color='#F44336', edgecolor='#F44336')
        ax1.bar(down.index, down['high'] - down['open'], width2, bottom=down['open'], 
               color='#F44336')
        ax1.bar(down.index, down['low'] - down['close'], width2, bottom=down['close'], 
               color='#F44336')
        
        # æ¨™é¡Œ
        title = f"{symbol}"
        if name:
            title += f" - {name}"
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('åƒ¹æ ¼ ($)')
        ax1.grid(True, alpha=0.3)
        
        # æˆäº¤é‡
        colors = ['#4CAF50' if df['close'].iloc[i] >= df['open'].iloc[i] 
                 else '#F44336' for i in range(len(df))]
        ax2.bar(df.index, df['volume'], color=colors, alpha=0.7)
        ax2.set_ylabel('æˆäº¤é‡')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"{symbol}_kline_{timestamp}.png"
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        return str(save_path)


# å»ºç«‹é è¨­å¯¦ä¾‹
chart_service = ChartService()