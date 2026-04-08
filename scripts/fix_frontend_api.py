#!/usr/bin/env python3
"""
前端 API 端點修復腳本
將 /api/market/sentiment 改為 /market/sentiment（使用 DB 快取的版本）

使用方式:
    python fix_frontend_api.py
"""
import os
import re
from pathlib import Path


def fix_file(filepath: str) -> tuple[int, list[str]]:
    """
    修復單一檔案中的 API 端點
    
    Returns:
        (修改次數, 修改的行列表)
    """
    if not os.path.exists(filepath):
        return 0, []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 記錄修改
    changes = []
    
    # 修復模式
    patterns = [
        # sentiment API
        (r'/api/market/sentiment', '/market/sentiment'),
    ]
    
    new_content = content
    total_count = 0
    
    for old, new in patterns:
        count = new_content.count(old)
        if count > 0:
            new_content = new_content.replace(old, new)
            total_count += count
            changes.append(f"  '{old}' → '{new}' ({count} 處)")
    
    if total_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return total_count, changes


def main():
    print("=" * 60)
    print("🔧 前端 API 端點修復腳本")
    print("=" * 60)
    print()
    
    # 找到專案根目錄
    project_root = Path('.')
    if not (project_root / 'static').exists():
        project_root = Path('..')
        if not (project_root / 'static').exists():
            print("❌ 錯誤：找不到 static 目錄，請在專案根目錄執行此腳本")
            return
    
    # 要檢查的檔案
    files_to_check = [
        project_root / 'static/js/dashboard.js',
        project_root / 'static/dashboard.html',
    ]
    
    total_fixes = 0
    
    for filepath in files_to_check:
        filepath_str = str(filepath)
        if not filepath.exists():
            print(f"⏭️  跳過（不存在）: {filepath_str}")
            continue
        
        count, changes = fix_file(filepath_str)
        
        if count > 0:
            print(f"✅ 修復: {filepath_str}")
            for change in changes:
                print(change)
            total_fixes += count
        else:
            print(f"✓  無需修改: {filepath_str}")
    
    print()
    print("=" * 60)
    if total_fixes > 0:
        print(f"✅ 完成！共修復 {total_fixes} 處")
        print()
        print("下一步：")
        print("1. git add .")
        print("2. git commit -m '🔧 修復 sentiment API 端點使用快取版本'")
        print("3. git push")
    else:
        print("✓ 所有檔案已是最新，無需修改")
    print("=" * 60)


if __name__ == "__main__":
    main()
