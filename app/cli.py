#!/usr/bin/env python3
"""
股票分析系統 CLI
命令列查詢介面
"""
import sys
import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from app.database import init_db_sync, get_sync_session
from app.services.stock_service import StockService
from app.services.crypto_service import CryptoService
from app.services.chart_service import chart_service
from app.data_sources.coingecko import CRYPTO_MAP
from app.config import settings

console = Console()

# 支援的加密貨幣代號
SUPPORTED_CRYPTO = set(k for k in CRYPTO_MAP.keys() if k not in ("BITCOIN", "ETHEREUM"))


def print_header():
    """顯示標題"""
    console.print()
    console.print(Panel.fit(
        "[bold orange1]📈 股票技術分析系統[/bold orange1]\n"
        f"[dim]版本 {settings.APP_VERSION}[/dim]",
        border_style="orange1",
    ))
    console.print()


def is_crypto(symbol: str) -> bool:
    """判斷是否為加密貨幣"""
    return symbol.upper() in SUPPORTED_CRYPTO


def print_stock_analysis(analysis: dict):
    """顯示股票分析報告"""
    symbol = analysis["symbol"]
    name = analysis["name"]
    price_info = analysis["price"]
    change_info = analysis["change"]
    volume_info = analysis.get("volume", {})
    indicators = analysis["indicators"]
    signals = analysis["signals"]
    score = analysis["score"]
    
    # 標題
    console.print(Panel(
        f"[bold]{symbol}[/bold] - {name}",
        border_style="blue",
    ))
    
    # 價格資訊
    price_table = Table(title="💰 價格資訊", box=box.ROUNDED, show_header=False)
    price_table.add_column("項目", style="cyan")
    price_table.add_column("數值", justify="right")
    
    current_price = price_info["current"]
    price_table.add_row("現價", f"[bold green]${current_price:,.2f}[/bold green]")
    
    if price_info.get("high_52w"):
        price_table.add_row("52週最高", f"${price_info['high_52w']:,.2f}")
    if price_info.get("low_52w"):
        price_table.add_row("52週最低", f"${price_info['low_52w']:,.2f}")
    if price_info.get("from_high_pct"):
        pct = price_info["from_high_pct"]
        color = "red" if pct < 0 else "green"
        price_table.add_row("距高點", f"[{color}]{pct:+.2f}%[/{color}]")
    if price_info.get("from_low_pct"):
        pct = price_info["from_low_pct"]
        color = "green" if pct > 0 else "red"
        price_table.add_row("距低點", f"[{color}]{pct:+.2f}%[/{color}]")
    
    console.print(price_table)
    console.print()
    
    # 漲跌幅
    change_table = Table(title="📊 漲跌幅", box=box.ROUNDED)
    change_table.add_column("日", justify="center")
    change_table.add_column("週", justify="center")
    change_table.add_column("月", justify="center")
    change_table.add_column("季", justify="center")
    change_table.add_column("年", justify="center")
    
    def format_change(val):
        if val is None:
            return "-"
        color = "green" if val >= 0 else "red"
        return f"[{color}]{val:+.2f}%[/{color}]"
    
    change_table.add_row(
        format_change(change_info.get("day")),
        format_change(change_info.get("week")),
        format_change(change_info.get("month")),
        format_change(change_info.get("quarter")),
        format_change(change_info.get("year")),
    )
    
    console.print(change_table)
    console.print()
    
    # 成交量
    if volume_info:
        vol_table = Table(title="📈 成交量", box=box.ROUNDED, show_header=False)
        vol_table.add_column("項目", style="cyan")
        vol_table.add_column("數值", justify="right")
        
        vol_table.add_row("今日成交量", f"{volume_info.get('today', 0):,}")
        if volume_info.get("avg_20d"):
            vol_table.add_row("20日均量", f"{volume_info['avg_20d']:,}")
        if volume_info.get("ratio"):
            ratio = volume_info["ratio"]
            color = "yellow" if ratio >= 2.0 else ("green" if ratio >= 1.0 else "dim")
            vol_table.add_row("量比", f"[{color}]{ratio:.2f}[/{color}]")
        
        console.print(vol_table)
        console.print()
    
    # 技術指標
    _print_indicators(indicators)
    
    # 訊號
    if signals:
        signal_panel = Panel(
            "\n".join([f"• {s['description']}" for s in signals]),
            title="⚡ 最新訊號",
            border_style="yellow",
        )
        console.print(signal_panel)
        console.print()
    
    # 綜合評分
    _print_score(score)
    
    # 更新時間
    console.print()
    console.print(f"[dim]更新時間: {analysis.get('updated_at', '-')}[/dim]")


def print_crypto_analysis(analysis: dict):
    """顯示加密貨幣分析報告"""
    symbol = analysis["symbol"]
    name = analysis["name"]
    price_info = analysis["price"]
    change_info = analysis["change"]
    market_info = analysis.get("market", {})
    indicators = analysis["indicators"]
    signals = analysis["signals"]
    score = analysis["score"]
    
    # 標題
    console.print(Panel(
        f"[bold]{symbol}[/bold] - {name} [dim](加密貨幣)[/dim]",
        border_style="yellow",
    ))
    
    # 價格資訊
    price_table = Table(title="💰 價格資訊", box=box.ROUNDED, show_header=False)
    price_table.add_column("項目", style="cyan")
    price_table.add_column("數值", justify="right")
    
    current_price = price_info["current"]
    if current_price >= 1000:
        price_table.add_row("現價", f"[bold green]${current_price:,.2f}[/bold green]")
    else:
        price_table.add_row("現價", f"[bold green]${current_price:,.4f}[/bold green]")
    
    if price_info.get("ath"):
        price_table.add_row("歷史最高 (ATH)", f"${price_info['ath']:,.2f}")
    if price_info.get("from_ath_pct"):
        pct = price_info["from_ath_pct"]
        color = "red" if pct < 0 else "green"
        price_table.add_row("距 ATH", f"[{color}]{pct:+.2f}%[/{color}]")
    if price_info.get("high_24h"):
        price_table.add_row("24H 最高", f"${price_info['high_24h']:,.2f}")
    if price_info.get("low_24h"):
        price_table.add_row("24H 最低", f"${price_info['low_24h']:,.2f}")
    
    console.print(price_table)
    console.print()
    
    # 市場資訊
    if market_info:
        market_table = Table(title="🌐 市場資訊", box=box.ROUNDED, show_header=False)
        market_table.add_column("項目", style="cyan")
        market_table.add_column("數值", justify="right")
        
        if market_info.get("market_cap"):
            market_table.add_row("市值", f"${market_info['market_cap']:,.0f}")
        if market_info.get("market_cap_rank"):
            market_table.add_row("市值排名", f"#{market_info['market_cap_rank']}")
        if market_info.get("volume_24h"):
            market_table.add_row("24H 成交量", f"${market_info['volume_24h']:,.0f}")
        
        console.print(market_table)
        console.print()
    
    # 漲跌幅
    change_table = Table(title="📊 漲跌幅", box=box.ROUNDED)
    change_table.add_column("24H", justify="center")
    change_table.add_column("7D", justify="center")
    change_table.add_column("30D", justify="center")
    change_table.add_column("1Y", justify="center")
    
    def format_change(val):
        if val is None:
            return "-"
        color = "green" if val >= 0 else "red"
        return f"[{color}]{val:+.2f}%[/{color}]"
    
    change_table.add_row(
        format_change(change_info.get("day")),
        format_change(change_info.get("week")),
        format_change(change_info.get("month")),
        format_change(change_info.get("year")),
    )
    
    console.print(change_table)
    console.print()
    
    # 技術指標
    _print_crypto_indicators(indicators)
    
    # 訊號
    if signals:
        signal_panel = Panel(
            "\n".join([f"• {s['description']}" for s in signals]),
            title="⚡ 最新訊號",
            border_style="yellow",
        )
        console.print(signal_panel)
        console.print()
    
    # 綜合評分
    _print_score(score)
    
    # 更新時間
    console.print()
    console.print(f"[dim]更新時間: {analysis.get('updated_at', '-')}[/dim]")


def _print_indicators(indicators: dict):
    """列印技術指標（股票版）"""
    ind_table = Table(title="📐 技術指標", box=box.ROUNDED)
    ind_table.add_column("指標", style="cyan")
    ind_table.add_column("數值", justify="right")
    ind_table.add_column("狀態", justify="center")
    
    # MA
    ma = indicators.get("ma", {})
    alignment = ma.get("alignment", "neutral")
    alignment_text = {
        "bullish": "[green]多頭排列[/green]",
        "bearish": "[red]空頭排列[/red]",
        "neutral": "[yellow]盤整[/yellow]",
    }.get(alignment, alignment)
    
    for ma_key in [f"ma{settings.MA_SHORT}", f"ma{settings.MA_MID}", f"ma{settings.MA_LONG}"]:
        val = ma.get(ma_key)
        pos = ma.get(f"price_vs_{ma_key}")
        pos_text = "[green]▲[/green]" if pos == "above" else "[red]▼[/red]" if pos == "below" else ""
        ind_table.add_row(
            ma_key.upper(),
            f"${val:,.2f}" if val else "-",
            pos_text,
        )
    
    ind_table.add_row("排列", "", alignment_text)
    
    # RSI
    rsi = indicators.get("rsi", {})
    rsi_val = rsi.get("value")
    rsi_status = rsi.get("status", "")
    rsi_color = "red" if rsi_status == "overbought" else "green" if rsi_status == "oversold" else "white"
    rsi_status_text = {
        "overbought": "[red]超買[/red]",
        "oversold": "[green]超賣[/green]",
        "neutral": "中性",
    }.get(rsi_status, rsi_status)
    
    ind_table.add_row(
        "RSI",
        f"[{rsi_color}]{rsi_val:.1f}[/{rsi_color}]" if rsi_val else "-",
        rsi_status_text,
    )
    
    # MACD
    macd = indicators.get("macd", {})
    macd_hist = macd.get("histogram")
    macd_status = macd.get("status", "")
    macd_color = "green" if macd_status == "bullish" else "red"
    
    ind_table.add_row(
        "MACD 柱",
        f"[{macd_color}]{macd_hist:.4f}[/{macd_color}]" if macd_hist is not None else "-",
        f"[{macd_color}]{'多' if macd_status == 'bullish' else '空'}[/{macd_color}]",
    )
    
    # Bollinger
    bb = indicators.get("bollinger", {})
    bb_pos = bb.get("position", "")
    bb_pos_text = {
        "above_upper": "[red]超出上軌[/red]",
        "below_lower": "[green]跌破下軌[/green]",
        "upper_half": "通道上半",
        "lower_half": "通道下半",
    }.get(bb_pos, bb_pos)
    
    ind_table.add_row(
        "布林",
        f"↑{bb.get('upper'):.2f} ↓{bb.get('lower'):.2f}" if bb.get("upper") else "-",
        bb_pos_text,
    )
    
    console.print(ind_table)
    console.print()


def _print_crypto_indicators(indicators: dict):
    """列印技術指標（加密貨幣版）"""
    ind_table = Table(title="📐 技術指標", box=box.ROUNDED)
    ind_table.add_column("指標", style="cyan")
    ind_table.add_column("數值", justify="right")
    ind_table.add_column("狀態", justify="center")
    
    # MA（幣圈週期）
    ma = indicators.get("ma", {})
    alignment = ma.get("alignment", "neutral")
    alignment_text = {
        "bullish": "[green]多頭排列[/green]",
        "bearish": "[red]空頭排列[/red]",
        "neutral": "[yellow]盤整[/yellow]",
    }.get(alignment, alignment)
    
    for ma_key in ["ma7", "ma25", "ma99"]:
        val = ma.get(ma_key)
        ind_table.add_row(
            ma_key.upper(),
            f"${val:,.2f}" if val else "-",
            "",
        )
    
    ind_table.add_row("排列", "", alignment_text)
    
    # RSI
    rsi = indicators.get("rsi", {})
    rsi_val = rsi.get("value")
    rsi_status = rsi.get("status", "")
    rsi_color = "red" if rsi_status == "overbought" else "green" if rsi_status == "oversold" else "white"
    rsi_status_text = {
        "overbought": "[red]超買[/red]",
        "oversold": "[green]超賣[/green]",
        "neutral": "中性",
    }.get(rsi_status, rsi_status)
    
    ind_table.add_row(
        "RSI",
        f"[{rsi_color}]{rsi_val:.1f}[/{rsi_color}]" if rsi_val else "-",
        rsi_status_text,
    )
    
    # MACD
    macd = indicators.get("macd", {})
    macd_hist = macd.get("histogram")
    macd_status = macd.get("status", "")
    macd_color = "green" if macd_status == "bullish" else "red"
    
    ind_table.add_row(
        "MACD",
        f"[{macd_color}]{macd_hist:.2f}[/{macd_color}]" if macd_hist is not None else "-",
        f"[{macd_color}]{'多' if macd_status == 'bullish' else '空'}[/{macd_color}]",
    )
    
    console.print(ind_table)
    console.print()


def _print_score(score: dict):
    """列印綜合評分"""
    buy_score = score.get("buy_score", 0)
    sell_score = score.get("sell_score", 0)
    rating = score.get("rating", "neutral")
    details = score.get("details", [])
    
    rating_text = {
        "strong_buy": "[bold green]強烈買進 ⭐⭐⭐⭐⭐[/bold green]",
        "buy": "[green]買進 ⭐⭐⭐⭐[/green]",
        "neutral": "[yellow]中性 ⭐⭐⭐[/yellow]",
        "sell": "[red]賣出 ⭐⭐[/red]",
        "strong_sell": "[bold red]強烈賣出 ⭐[/bold red]",
        "insufficient_data": "[dim]資料不足[/dim]",
    }.get(rating, rating)
    
    score_content = f"買進訊號: {buy_score} / 賣出訊號: {sell_score}\n"
    score_content += f"綜合評等: {rating_text}\n\n"
    if details:
        score_content += "\n".join(details)
    
    console.print(Panel(
        score_content,
        title="🎯 綜合評分",
        border_style="magenta",
    ))


def print_sentiment(sentiment: dict):
    """顯示市場情緒"""
    console.print(Panel.fit(
        "[bold]📊 市場情緒指數[/bold]",
        border_style="cyan",
    ))
    
    sent_table = Table(box=box.ROUNDED)
    sent_table.add_column("市場", style="cyan")
    sent_table.add_column("指數", justify="center")
    sent_table.add_column("狀態", justify="center")
    sent_table.add_column("建議", justify="left")
    
    from app.data_sources.fear_greed import fear_greed as fg_client
    
    for market, data in sentiment.items():
        if not data:
            continue
        
        value = data.get("value", 0)
        classification_zh = data.get("classification_zh", "")
        
        # 根據數值決定顏色
        if value <= 25:
            color = "green"
            emoji = "😱"
        elif value <= 45:
            color = "cyan"
            emoji = "😟"
        elif value <= 55:
            color = "yellow"
            emoji = "😐"
        elif value <= 75:
            color = "orange1"
            emoji = "😊"
        else:
            color = "red"
            emoji = "🤑"
        
        market_name = "美股" if market == "stock" else "加密貨幣"
        advice = fg_client.get_sentiment_advice(value)
        
        sent_table.add_row(
            market_name,
            f"[{color}]{value}[/{color}] {emoji}",
            f"[{color}]{classification_zh}[/{color}]",
            advice[:30] + "..." if len(advice) > 30 else advice,
        )
    
    console.print(sent_table)


def cmd_query(args):
    """查詢股票或加密貨幣"""
    symbol = args.symbol.upper()
    
    db = get_sync_session()
    try:
        if is_crypto(symbol):
            # 加密貨幣
            with console.status(f"[bold green]正在分析 {symbol} (加密貨幣)..."):
                service = CryptoService(db)
                analysis = service.get_crypto_analysis(symbol, force_refresh=args.refresh)
                
                if analysis is None:
                    console.print(f"[red]❌ 找不到加密貨幣: {symbol}[/red]")
                    return 1
                
                print_crypto_analysis(analysis)
        else:
            # 股票
            with console.status(f"[bold green]正在分析 {symbol}..."):
                service = StockService(db)
                analysis = service.get_stock_analysis(symbol, force_refresh=args.refresh)
                
                if analysis is None:
                    console.print(f"[red]❌ 找不到股票: {symbol}[/red]")
                    return 1
                
                print_stock_analysis(analysis)
        
        return 0
    finally:
        db.close()


def cmd_sentiment(args):
    """查詢市場情緒"""
    with console.status("[bold green]正在取得市場情緒..."):
        db = get_sync_session()
        try:
            service = CryptoService(db)
            sentiment = service.get_market_sentiment("all")
            
            if not sentiment:
                console.print("[yellow]⚠️ 無法取得市場情緒資料[/yellow]")
                return 1
            
            print_sentiment(sentiment)
            return 0
        finally:
            db.close()


def cmd_chart(args):
    """生成圖表"""
    symbol = args.symbol.upper()
    
    db = get_sync_session()
    try:
        if is_crypto(symbol):
            service = CryptoService(db)
            with console.status(f"[bold green]正在生成 {symbol} 圖表..."):
                df = service.get_crypto_data(symbol)
        else:
            service = StockService(db)
            with console.status(f"[bold green]正在生成 {symbol} 圖表..."):
                df = service.get_stock_data(symbol)
        
        if df is None:
            console.print(f"[red]❌ 無法取得資料: {symbol}[/red]")
            return 1
        
        # 生成圖表
        chart_path = chart_service.plot_stock_analysis(
            df,
            symbol,
            days=args.days,
            show_kd=args.kd,
        )
        
        console.print(f"[green]✅ 圖表已儲存: {chart_path}[/green]")
        return 0
        
    finally:
        db.close()


def cmd_refresh(args):
    """更新資料"""
    symbol = args.symbol.upper()
    
    db = get_sync_session()
    try:
        if is_crypto(symbol):
            with console.status(f"[bold green]正在更新 {symbol}..."):
                service = CryptoService(db)
                success = service.fetch_and_cache_crypto(symbol)
        else:
            with console.status(f"[bold green]正在更新 {symbol}..."):
                service = StockService(db)
                success = service.fetch_and_cache_stock(symbol)
        
        if success:
            console.print(f"[green]✅ 已更新 {symbol} 資料[/green]")
            return 0
        else:
            console.print(f"[red]❌ 更新失敗: {symbol}[/red]")
            return 1
    finally:
        db.close()


def cmd_init(args):
    """初始化資料庫"""
    with console.status("[bold green]正在初始化資料庫..."):
        init_db_sync()
    console.print("[green]✅ 資料庫初始化完成[/green]")
    return 0


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="股票技術分析系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用指令")
    
    # init 指令
    init_parser = subparsers.add_parser("init", help="初始化資料庫")
    init_parser.set_defaults(func=cmd_init)
    
    # query 指令
    query_parser = subparsers.add_parser("query", help="查詢股票或加密貨幣")
    query_parser.add_argument("symbol", help="代號 (股票如 AAPL, 加密貨幣如 BTC)")
    query_parser.add_argument("-r", "--refresh", action="store_true", help="強制更新資料")
    query_parser.set_defaults(func=cmd_query)
    
    # sentiment 指令
    sentiment_parser = subparsers.add_parser("sentiment", help="查詢市場情緒")
    sentiment_parser.set_defaults(func=cmd_sentiment)
    
    # chart 指令
    chart_parser = subparsers.add_parser("chart", help="生成技術分析圖表")
    chart_parser.add_argument("symbol", help="代號")
    chart_parser.add_argument("-d", "--days", type=int, default=120, help="顯示天數 (預設 120)")
    chart_parser.add_argument("--kd", action="store_true", help="顯示 KD 指標")
    chart_parser.set_defaults(func=cmd_chart)
    
    # refresh 指令
    refresh_parser = subparsers.add_parser("refresh", help="更新資料")
    refresh_parser.add_argument("symbol", help="代號")
    refresh_parser.set_defaults(func=cmd_refresh)
    
    # 解析參數
    args = parser.parse_args()
    
    print_header()
    
    if not args.command:
        # 互動模式
        console.print("[cyan]輸入代號進行查詢 (股票如 AAPL，加密貨幣如 BTC)[/cyan]")
        console.print("[cyan]輸入 'sentiment' 查看市場情緒，'q' 離開[/cyan]")
        console.print()
        
        init_db_sync()
        db = get_sync_session()
        stock_service = StockService(db)
        crypto_service = CryptoService(db)
        
        try:
            while True:
                try:
                    user_input = console.input("[bold]代號> [/bold]").strip().upper()
                    
                    if user_input in ("Q", "QUIT", "EXIT"):
                        console.print("[yellow]再見！[/yellow]")
                        break
                    
                    if not user_input:
                        continue
                    
                    if user_input == "SENTIMENT":
                        sentiment = crypto_service.get_market_sentiment("all")
                        if sentiment:
                            print_sentiment(sentiment)
                        else:
                            console.print("[yellow]⚠️ 無法取得市場情緒[/yellow]")
                        console.print()
                        continue
                    
                    # 查詢股票或加密貨幣
                    if is_crypto(user_input):
                        with console.status(f"[bold green]正在分析 {user_input}..."):
                            analysis = crypto_service.get_crypto_analysis(user_input)
                        if analysis:
                            print_crypto_analysis(analysis)
                        else:
                            console.print(f"[red]❌ 找不到: {user_input}[/red]")
                    else:
                        with console.status(f"[bold green]正在分析 {user_input}..."):
                            analysis = stock_service.get_stock_analysis(user_input)
                        if analysis:
                            print_stock_analysis(analysis)
                        else:
                            console.print(f"[red]❌ 找不到: {user_input}[/red]")
                    
                    console.print()
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]再見！[/yellow]")
                    break
        finally:
            db.close()
        
        return 0
    
    # 執行指令
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
