"""
圖表繪製服務
使用 matplotlib + mplfinance 繪製技術分析圖表
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

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 顏色定義
COLORS = {
    "price": "#2196F3",      # 價格線 - 藍色
    "ma_short": "#FF9800",   # MA20 - 橙色
    "ma_mid": "#9C27B0",     # MA50 - 紫色
    "ma_long": "#F44336",    # MA200 - 紅色
    "volume_up": "#4CAF50",  # 上漲成交量 - 綠色
    "volume_down": "#F44336", # 下跌成交量 - 紅色
    "bb_fill": "#E3F2FD",    # 布林通道填充 - 淺藍
    "bb_line": "#90CAF9",    # 布林通道線 - 藍色
    "rsi": "#673AB7",        # RSI - 深紫
    "macd_dif": "#2196F3",   # MACD DIF - 藍色
    "macd_dea": "#FF9800",   # MACD DEA - 橙色
    "macd_hist_pos": "#4CAF50",  # MACD 正柱 - 綠色
    "macd_hist_neg": "#F44336",  # MACD 負柱 - 紅色
    "kd_k": "#2196F3",       # K 線 - 藍色
    "kd_d": "#FF9800",       # D 線 - 橙色
    "golden_cross": "#4CAF50",   # 黃金交叉 - 綠色
    "death_cross": "#F44336",    # 死亡交叉 - 紅色
    "grid": "#E0E0E0",       # 網格線
    "overbought": "#FFCDD2", # 超買區 - 淺紅
    "oversold": "#C8E6C9",   # 超賣區 - 淺綠
}


class ChartService:
    """圖表繪製服務"""
    
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
        繪製完整股票分析圖表
        
        Args:
            df: 含有價格和指標的 DataFrame
            symbol: 股票代號
            name: 股票名稱
            show_ma: 顯示均線
            show_bollinger: 顯示布林通道
            show_volume: 顯示成交量
            show_rsi: 顯示 RSI
            show_macd: 顯示 MACD
            show_kd: 顯示 KD
            show_signals: 標記交叉訊號
            days: 顯示天數
            save_path: 儲存路徑（不指定則自動生成）
            
        Returns:
            圖表檔案路徑
        """
        # 只取最近 N 天資料
        if len(df) > days:
            df = df.tail(days).copy()
        else:
            df = df.copy()
        
        # 確保 date 欄位正確
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        # 計算子圖數量
        n_subplots = 1  # 主圖
        if show_volume:
            n_subplots += 1
        if show_rsi:
            n_subplots += 1
        if show_macd:
            n_subplots += 1
        if show_kd:
            n_subplots += 1
        
        # 設定子圖高度比例
        height_ratios = [3]  # 主圖
        if show_volume:
            height_ratios.append(1)
        if show_rsi:
            height_ratios.append(1)
        if show_macd:
            height_ratios.append(1.2)
        if show_kd:
            height_ratios.append(1)
        
        # 建立圖表
        fig, axes = plt.subplots(
            n_subplots, 1,
            figsize=(14, 3 + n_subplots * 2),
            gridspec_kw={'height_ratios': height_ratios},
            sharex=True,
        )
        
        if n_subplots == 1:
            axes = [axes]
        
        ax_idx = 0
        
        # === 主圖：價格 + 均線 + 布林通道 ===
        ax_main = axes[ax_idx]
        ax_idx += 1
        
        self._plot_price(ax_main, df, show_ma, show_bollinger, show_signals)
        
        # 標題
        title = f"{symbol}"
        if name:
            title += f" - {name}"
        title += f"\n最後更新: {df.index[-1].strftime('%Y-%m-%d')} | 收盤: ${df['close'].iloc[-1]:.2f}"
        ax_main.set_title(title, fontsize=14, fontweight='bold', pad=10)
        
        # === 成交量 ===
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
        
        # 調整布局
        plt.tight_layout()
        
        # 儲存圖表
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"{symbol}_{timestamp}.png"
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"圖表已儲存: {save_path}")
        return str(save_path)
    
    def _plot_price(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        show_ma: bool,
        show_bollinger: bool,
        show_signals: bool,
    ):
        """繪製價格主圖"""
        # 布林通道（先畫，作為背景）
        if show_bollinger and 'bb_upper' in df.columns:
            ax.fill_between(
                df.index,
                df['bb_lower'],
                df['bb_upper'],
                color=COLORS['bb_fill'],
                alpha=0.5,
                label='布林通道',
            )
            ax.plot(df.index, df['bb_middle'], color=COLORS['bb_line'], 
                   linewidth=0.8, linestyle='--', alpha=0.7)
        
        # 價格線
        ax.plot(df.index, df['close'], color=COLORS['price'], 
               linewidth=1.5, label='收盤價')
        
        # 均線
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
        
        # 標記交叉訊號
        if show_signals and show_ma:
            self._mark_crossovers(ax, df)
        
        # 設定
        ax.set_ylabel('價格 ($)', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
        ax.set_xlim(df.index[0], df.index[-1])
    
    def _mark_crossovers(self, ax: plt.Axes, df: pd.DataFrame):
        """標記均線交叉點"""
        ma_short = f"ma{settings.MA_SHORT}"
        ma_mid = f"ma{settings.MA_MID}"
        
        if ma_short not in df.columns or ma_mid not in df.columns:
            return
        
        for i in range(1, len(df)):
            # 黃金交叉
            if (df[ma_short].iloc[i-1] < df[ma_mid].iloc[i-1] and 
                df[ma_short].iloc[i] > df[ma_mid].iloc[i]):
                ax.scatter(df.index[i], df['close'].iloc[i], 
                          color=COLORS['golden_cross'], s=100, marker='^', 
                          zorder=5, edgecolors='white', linewidths=1)
            
            # 死亡交叉
            elif (df[ma_short].iloc[i-1] > df[ma_mid].iloc[i-1] and 
                  df[ma_short].iloc[i] < df[ma_mid].iloc[i]):
                ax.scatter(df.index[i], df['close'].iloc[i], 
                          color=COLORS['death_cross'], s=100, marker='v', 
                          zorder=5, edgecolors='white', linewidths=1)
    
    def _plot_volume(self, ax: plt.Axes, df: pd.DataFrame):
        """繪製成交量"""
        colors = []
        for i in range(len(df)):
            if i == 0:
                colors.append(COLORS['volume_up'])
            elif df['close'].iloc[i] >= df['close'].iloc[i-1]:
                colors.append(COLORS['volume_up'])
            else:
                colors.append(COLORS['volume_down'])
        
        ax.bar(df.index, df['volume'], color=colors, alpha=0.7, width=0.8)
        
        # 20日均量線
        if 'volume_ma20' in df.columns:
            ax.plot(df.index, df['volume_ma20'], color='orange', 
                   linewidth=1, label='20日均量')
            ax.legend(loc='upper left', fontsize=8)
        
        ax.set_ylabel('成交量', fontsize=10)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
        
        # 格式化 Y 軸
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
    
    def _plot_rsi(self, ax: plt.Axes, df: pd.DataFrame):
        """繪製 RSI"""
        # 超買超賣區域
        ax.axhspan(settings.RSI_OVERBOUGHT, 100, color=COLORS['overbought'], alpha=0.3)
        ax.axhspan(0, settings.RSI_OVERSOLD, color=COLORS['oversold'], alpha=0.3)
        
        # 中線
        ax.axhline(y=50, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=settings.RSI_OVERBOUGHT, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=settings.RSI_OVERSOLD, color='green', linestyle='--', linewidth=0.8, alpha=0.5)
        
        # RSI 線
        ax.plot(df.index, df['rsi'], color=COLORS['rsi'], linewidth=1.2, label='RSI')
        
        # 設定
        ax.set_ylabel('RSI', fontsize=10)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
        
        # 標記最新值
        latest_rsi = df['rsi'].iloc[-1]
        if not pd.isna(latest_rsi):
            ax.annotate(f'{latest_rsi:.1f}', 
                       xy=(df.index[-1], latest_rsi),
                       xytext=(5, 0), textcoords='offset points',
                       fontsize=9, color=COLORS['rsi'])
    
    def _plot_macd(self, ax: plt.Axes, df: pd.DataFrame):
        """繪製 MACD"""
        # 零軸
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
        
        # MACD 柱狀圖
        colors = [COLORS['macd_hist_pos'] if v >= 0 else COLORS['macd_hist_neg'] 
                 for v in df['macd_hist']]
        ax.bar(df.index, df['macd_hist'], color=colors, alpha=0.6, width=0.8)
        
        # DIF 和 DEA 線
        ax.plot(df.index, df['macd_dif'], color=COLORS['macd_dif'], 
               linewidth=1.2, label='DIF')
        ax.plot(df.index, df['macd_dea'], color=COLORS['macd_dea'], 
               linewidth=1.2, label='DEA')
        
        # 標記交叉點
        for i in range(1, len(df)):
            if pd.isna(df['macd_dif'].iloc[i]) or pd.isna(df['macd_dea'].iloc[i]):
                continue
            # 黃金交叉
            if (df['macd_dif'].iloc[i-1] < df['macd_dea'].iloc[i-1] and 
                df['macd_dif'].iloc[i] > df['macd_dea'].iloc[i]):
                ax.scatter(df.index[i], df['macd_dif'].iloc[i], 
                          color=COLORS['golden_cross'], s=50, marker='^', zorder=5)
            # 死亡交叉
            elif (df['macd_dif'].iloc[i-1] > df['macd_dea'].iloc[i-1] and 
                  df['macd_dif'].iloc[i] < df['macd_dea'].iloc[i]):
                ax.scatter(df.index[i], df['macd_dif'].iloc[i], 
                          color=COLORS['death_cross'], s=50, marker='v', zorder=5)
        
        # 設定
        ax.set_ylabel('MACD', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
    
    def _plot_kd(self, ax: plt.Axes, df: pd.DataFrame):
        """繪製 KD"""
        # 超買超賣區域
        ax.axhspan(80, 100, color=COLORS['overbought'], alpha=0.3)
        ax.axhspan(0, 20, color=COLORS['oversold'], alpha=0.3)
        
        # 中線
        ax.axhline(y=50, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=80, color='red', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.axhline(y=20, color='green', linestyle='--', linewidth=0.8, alpha=0.5)
        
        # K 和 D 線
        ax.plot(df.index, df['kd_k'], color=COLORS['kd_k'], linewidth=1.2, label='K')
        ax.plot(df.index, df['kd_d'], color=COLORS['kd_d'], linewidth=1.2, label='D')
        
        # 設定
        ax.set_ylabel('KD', fontsize=10)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, color=COLORS['grid'], linestyle='-', linewidth=0.5, alpha=0.7)
        ax.set_xlabel('日期', fontsize=10)
    
    def plot_candlestick(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str = "",
        days: int = 60,
        save_path: Optional[str] = None,
    ) -> str:
        """
        繪製 K 線圖（使用 mplfinance）
        
        Args:
            df: OHLCV DataFrame
            symbol: 股票代號
            name: 股票名稱
            days: 顯示天數
            save_path: 儲存路徑
            
        Returns:
            圖表檔案路徑
        """
        try:
            import mplfinance as mpf
        except ImportError:
            logger.warning("mplfinance 未安裝，使用替代方案")
            return self._plot_candlestick_fallback(df, symbol, name, days, save_path)
        
        # 準備資料
        if len(df) > days:
            df = df.tail(days).copy()
        else:
            df = df.copy()
        
        # 確保索引為 DatetimeIndex
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        # 確保欄位名稱正確（mplfinance 需要大寫）
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
        })
        
        # 準備均線
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
        
        # 設定樣式
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
        
        # 儲存路徑
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"{symbol}_kline_{timestamp}.png"
        
        # 標題
        title = f"{symbol}"
        if name:
            title += f" - {name}"
        
        # 繪製
        mpf.plot(
            df,
            type='candle',
            style=style,
            title=title,
            ylabel='價格 ($)',
            ylabel_lower='成交量',
            volume=True,
            addplot=addplots if addplots else None,
            figsize=(14, 8),
            savefig=str(save_path),
        )
        
        logger.info(f"K線圖已儲存: {save_path}")
        return str(save_path)
    
    def _plot_candlestick_fallback(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str,
        days: int,
        save_path: Optional[str],
    ) -> str:
        """當 mplfinance 不可用時的替代 K 線圖"""
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
        
        # K 線
        width = 0.6
        width2 = 0.1
        
        up = df[df['close'] >= df['open']]
        down = df[df['close'] < df['open']]
        
        # 上漲 K 線
        ax1.bar(up.index, up['close'] - up['open'], width, bottom=up['open'], 
               color='#4CAF50', edgecolor='#4CAF50')
        ax1.bar(up.index, up['high'] - up['close'], width2, bottom=up['close'], 
               color='#4CAF50')
        ax1.bar(up.index, up['low'] - up['open'], width2, bottom=up['open'], 
               color='#4CAF50')
        
        # 下跌 K 線
        ax1.bar(down.index, down['close'] - down['open'], width, bottom=down['open'], 
               color='#F44336', edgecolor='#F44336')
        ax1.bar(down.index, down['high'] - down['open'], width2, bottom=down['open'], 
               color='#F44336')
        ax1.bar(down.index, down['low'] - down['close'], width2, bottom=down['close'], 
               color='#F44336')
        
        # 標題
        title = f"{symbol}"
        if name:
            title += f" - {name}"
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('價格 ($)')
        ax1.grid(True, alpha=0.3)
        
        # 成交量
        colors = ['#4CAF50' if df['close'].iloc[i] >= df['open'].iloc[i] 
                 else '#F44336' for i in range(len(df))]
        ax2.bar(df.index, df['volume'], color=colors, alpha=0.7)
        ax2.set_ylabel('成交量')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"{symbol}_kline_{timestamp}.png"
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        return str(save_path)


# 建立預設實例
chart_service = ChartService()
