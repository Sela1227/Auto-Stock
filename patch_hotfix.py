#!/usr/bin/env python3
"""
SELA 緊急修復補丁 - 修正 patch_target_price.py 引入的問題
==========================================================
修復:
1. watchlist.py - direction 變數未定義
2. ma_advanced_service.py - numpy 類型無法 JSON 序列化

使用方式:
    python patch_hotfix.py

作者: Claude
日期: 2026-01-17
"""

import os
import sys
import shutil
from datetime import datetime

# 顏色輸出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def log_success(msg):
    print(f"{Colors.GREEN}[✓]{Colors.END} {msg}")

def log_warning(msg):
    print(f"{Colors.YELLOW}[!]{Colors.END} {msg}")

def log_error(msg):
    print(f"{Colors.RED}[✗]{Colors.END} {msg}")

def backup_file(filepath):
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.hotfix.{timestamp}"
        shutil.copy2(filepath, backup_path)
        print(f"  備份: {backup_path}")


# ============================================================
# 修復 1: watchlist.py - direction 變數問題
# ============================================================

def fix_watchlist_py(filepath):
    """修復 watchlist.py 中的 direction 變數問題"""
    if not os.path.exists(filepath):
        log_error(f"找不到: {filepath}")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 問題: 補丁可能加入了錯誤的 direction 判斷
    # 修正方案: 確保 direction 在正確位置定義
    
    # 方案 A: 如果有錯誤的 direction 使用，修正它
    # 錯誤模式: 在 target_reached 判斷中使用了未定義的 direction
    
    # 找到並修正錯誤的 target_reached 邏輯
    bad_patterns = [
        # 模式 1: direction 在 if 外使用但只在 if 內定義
        "direction = getattr(item, 'target_direction', 'above') or 'above'\n            target_reached = (current_price <= target_price) if direction == 'below' else (current_price >= target_price)",
        # 模式 2: 只有 target_reached 使用 direction 但沒有定義
        "target_reached = (current_price <= target_price) if direction == 'below' else (current_price >= target_price)",
    ]
    
    # 正確的邏輯 - 在 if current_price and target_price 區塊內
    correct_logic = """if current_price and target_price:
                direction = getattr(item, 'target_direction', 'above') or 'above'
                target_reached = (current_price <= target_price) if direction == 'below' else (current_price >= target_price)"""
    
    # 尋找原本的 target_reached 判斷並替換
    old_pattern1 = """if current_price and target_price:
                target_reached = current_price >= target_price"""
    
    old_pattern2 = """if current_price and target_price:
            target_reached = current_price >= target_price"""
    
    modified = False
    
    # 檢查是否有錯誤模式需要修正
    for bad in bad_patterns:
        if bad in content:
            # 如果是模式2，需要在前面加上 direction 定義
            content = content.replace(bad, correct_logic)
            modified = True
            log_success("修正了錯誤的 direction 使用")
    
    # 如果沒有錯誤模式，檢查是否需要更新原始邏輯
    if not modified:
        if old_pattern1 in content:
            content = content.replace(old_pattern1, correct_logic)
            modified = True
        elif old_pattern2 in content:
            # 注意縮排差異
            correct_logic_alt = """if current_price and target_price:
            direction = getattr(item, 'target_direction', 'above') or 'above'
            target_reached = (current_price <= target_price) if direction == 'below' else (current_price >= target_price)"""
            content = content.replace(old_pattern2, correct_logic_alt)
            modified = True
    
    # 確保回傳資料包含 target_direction
    if '"target_price": target_price,' in content and '"target_direction"' not in content:
        content = content.replace(
            '"target_price": target_price,',
            '"target_price": target_price,\n                "target_direction": getattr(item, \'target_direction\', \'above\') or \'above\',' 
        )
        modified = True
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        log_success(f"已修復: {filepath}")
    else:
        log_warning(f"未找到需要修復的模式: {filepath}")
    
    return True


# ============================================================
# 修復 2: ma_advanced_service.py - numpy 類型問題
# ============================================================

def fix_ma_advanced_service(filepath):
    """修復 ma_advanced_service.py 中的 numpy 類型問題"""
    if not os.path.exists(filepath):
        log_warning(f"找不到: {filepath} (可能未部署 MA 進階分析)")
        return True
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 確保有 numpy 類型轉換的輔助函數
    helper_function = '''
def _to_python_type(value):
    """將 numpy 類型轉換為 Python 原生類型"""
    if value is None:
        return None
    if hasattr(value, 'item'):  # numpy scalar
        return value.item()
    if isinstance(value, (list, tuple)):
        return [_to_python_type(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_python_type(v) for k, v in value.items()}
    return value

'''
    
    # 檢查是否已有這個函數
    if '_to_python_type' not in content:
        # 在 import 區塊後加入
        import_end = content.find('\n\nlogger = ')
        if import_end == -1:
            import_end = content.find('\n\ndef ')
        
        if import_end != -1:
            content = content[:import_end] + '\n' + helper_function + content[import_end:]
            log_success("已加入 _to_python_type 輔助函數")
    
    # 確保 analyze_ma_advanced 回傳時轉換類型
    old_return = 'return result'
    new_return = 'return _to_python_type(result)'
    
    if old_return in content and new_return not in content:
        content = content.replace(old_return, new_return)
        log_success("已加入回傳值類型轉換")
    
    # 同時確保各個數值都用 float() 或 int() 包裝
    # 修正 round() 結果可能是 numpy 類型
    content = content.replace(
        "result[dist_key] = round((current_price - ma_value) / ma_value * 100, 2)",
        "result[dist_key] = float(round((current_price - ma_value) / ma_value * 100, 2))"
    )
    
    content = content.replace(
        "'distance_pct': round((current_price - ma_value) / ma_value * 100, 2)",
        "'distance_pct': float(round((current_price - ma_value) / ma_value * 100, 2))"
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    log_success(f"已修復: {filepath}")
    return True


# ============================================================
# 修復 3: stock.py - 確保 ma_advanced 回傳值安全
# ============================================================

def fix_stock_py(filepath):
    """修復 stock.py 確保 ma_advanced 安全合併"""
    if not os.path.exists(filepath):
        log_error(f"找不到: {filepath}")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 如果有 **ma_advanced 合併，確保它不會因為 numpy 類型出錯
    # 加入安全轉換
    
    if 'ma_advanced = analyze_ma_advanced' in content:
        # 確保有安全的類型轉換
        old_call = 'ma_advanced = analyze_ma_advanced(df, current_price_adj)'
        new_call = '''ma_advanced = analyze_ma_advanced(df, current_price_adj)
        # 確保所有值都是 JSON 可序列化的類型
        def safe_value(v):
            if hasattr(v, 'item'): return v.item()
            if isinstance(v, dict): return {k: safe_value(val) for k, val in v.items()}
            if isinstance(v, list): return [safe_value(x) for x in v]
            return v
        ma_advanced = safe_value(ma_advanced) if ma_advanced else {}'''
        
        if old_call in content and 'safe_value' not in content:
            content = content.replace(old_call, new_call)
            log_success("已加入 ma_advanced 安全轉換")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    return True


# ============================================================
# 主程式
# ============================================================

def main():
    print()
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}  🚨 SELA 緊急修復補丁 (Hotfix){Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print()
    print("修復問題:")
    print(f"  {Colors.RED}1.{Colors.END} watchlist - UnboundLocalError: direction")
    print(f"  {Colors.RED}2.{Colors.END} stock - TypeError: numpy.int64 not iterable")
    print()
    
    # 確認目錄
    if not os.path.exists("app"):
        log_error("請在專案根目錄執行此腳本")
        sys.exit(1)
    
    print(f"{Colors.CYAN}--- 開始修復 ---{Colors.END}")
    print()
    
    # 1. 修復 watchlist.py
    print(f"{Colors.BLUE}[1/3]{Colors.END} 修復 watchlist.py")
    if os.path.exists('app/routers/watchlist.py'):
        fix_watchlist_py('app/routers/watchlist.py')
    else:
        log_warning("watchlist.py 不存在")
    
    # 2. 修復 ma_advanced_service.py
    print(f"\n{Colors.BLUE}[2/3]{Colors.END} 修復 ma_advanced_service.py")
    if os.path.exists('app/services/ma_advanced_service.py'):
        fix_ma_advanced_service('app/services/ma_advanced_service.py')
    else:
        log_warning("ma_advanced_service.py 不存在 (可能未部署)")
    
    # 3. 修復 stock.py
    print(f"\n{Colors.BLUE}[3/3]{Colors.END} 修復 stock.py")
    if os.path.exists('app/routers/stock.py'):
        fix_stock_py('app/routers/stock.py')
    else:
        log_warning("stock.py 不存在")
    
    # 完成訊息
    print()
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}✅ 緊急修復完成！{Colors.END}")
    print()
    print("下一步: 重新部署應用程式")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print()


if __name__ == "__main__":
    main()
