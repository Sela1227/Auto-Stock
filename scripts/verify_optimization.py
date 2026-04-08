#!/usr/bin/env python3
"""
SELA 優化驗證腳本
檢查優化是否正確部署

使用方式:
    python verify_optimization.py [--url https://your-domain.railway.app]
"""
import argparse
import json
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("需要安裝 requests: pip install requests")
    sys.exit(1)


def check_health(base_url: str) -> bool:
    """檢查服務是否運行"""
    try:
        resp = requests.get(f"{base_url}/health", timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ 服務運行中: {data.get('version', 'unknown')}")
            return True
        else:
            print(f"❌ 健康檢查失敗: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 無法連接到服務: {e}")
        return False


def check_scheduler_status(base_url: str) -> dict:
    """檢查排程器狀態"""
    try:
        resp = requests.get(f"{base_url}/api/admin/scheduler-status", timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            
            print(f"\n📅 排程器狀態:")
            print(f"   運行中: {'✅ 是' if data.get('running') else '❌ 否'}")
            print(f"   任務數量: {data.get('job_count', len(data.get('jobs', [])))}")
            
            # 檢查市場狀態
            market = data.get('market_status', {})
            print(f"\n🌍 市場狀態:")
            print(f"   台股: {'🟢 開盤' if market.get('tw_open') else '🔴 收盤'}")
            print(f"   美股: {'🟢 開盤' if market.get('us_open') else '🔴 收盤'}")
            
            # 檢查優化版本
            opt = data.get('optimization', {})
            if opt:
                print(f"\n🔧 優化版本:")
                print(f"   版本: {opt.get('version', 'N/A')}")
                print(f"   效果: {opt.get('savings_estimate', 'N/A')}")
            else:
                print(f"\n⚠️ 未檢測到優化版本標記（可能使用舊版）")
            
            return data
        else:
            print(f"❌ 無法獲取排程狀態: {resp.status_code}")
            return {}
    except Exception as e:
        print(f"❌ 排程狀態檢查失敗: {e}")
        return {}


def check_sentiment_api(base_url: str) -> bool:
    """檢查情緒指數 API"""
    print(f"\n📊 情緒指數 API 檢查:")
    
    # 檢查正確的端點（有快取）
    try:
        start = datetime.now()
        resp = requests.get(f"{base_url}/market/sentiment", timeout=30)
        elapsed = (datetime.now() - start).total_seconds() * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                print(f"   ✅ /market/sentiment: {elapsed:.0f}ms")
                
                stock = data.get('data', {}).get('stock', {})
                crypto = data.get('data', {}).get('crypto', {})
                
                if stock:
                    print(f"      美股情緒: {stock.get('value', 'N/A')}")
                if crypto:
                    print(f"      幣圈情緒: {crypto.get('value', 'N/A')}")
                
                # 判斷是否使用了快取
                if elapsed < 500:
                    print(f"   ✅ 回應時間正常，可能使用了資料庫快取")
                else:
                    print(f"   ⚠️ 回應時間較慢，可能在打外部 API")
                
                return True
            else:
                print(f"   ❌ API 返回失敗")
                return False
        else:
            print(f"   ❌ /market/sentiment: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 情緒 API 檢查失敗: {e}")
        return False


def check_cost_metrics(base_url: str) -> dict:
    """檢查成本指標"""
    try:
        resp = requests.get(f"{base_url}/api/admin/cost-metrics", timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            
            print(f"\n💰 成本指標:")
            scheduler = data.get('scheduler', {})
            print(f"   每日預估執行次數: {scheduler.get('daily_executions_estimate', 'N/A')}")
            
            opts = data.get('optimizations_applied', [])
            if opts:
                print(f"   已套用優化:")
                for opt in opts:
                    print(f"      - {opt}")
            
            return data
        else:
            print(f"   ⚠️ 成本指標 API 不可用（可能使用舊版本）")
            return {}
    except Exception as e:
        print(f"   ⚠️ 成本指標檢查失敗: {e}")
        return {}


def check_database_indexes(base_url: str) -> bool:
    """通過 API 檢查是否可以快速查詢"""
    # 這個檢查通過回應時間來間接判斷
    print(f"\n🗄️ 資料庫效能檢查:")
    print(f"   (通過 API 回應時間間接判斷)")
    return True


def main():
    parser = argparse.ArgumentParser(description='SELA 優化驗證腳本')
    parser.add_argument('--url', default='http://localhost:8000',
                        help='API 基礎 URL (預設: http://localhost:8000)')
    args = parser.parse_args()
    
    base_url = args.url.rstrip('/')
    
    print("=" * 60)
    print("🔍 SELA 優化驗證")
    print("=" * 60)
    print(f"目標: {base_url}")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 執行檢查
    results = {
        'health': check_health(base_url),
        'scheduler': bool(check_scheduler_status(base_url)),
        'sentiment': check_sentiment_api(base_url),
        'cost': bool(check_cost_metrics(base_url)),
    }
    
    # 總結
    print("\n" + "=" * 60)
    print("📋 驗證總結")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {check}: {status}")
    
    print(f"\n   總計: {passed}/{total} 項通過")
    
    if passed == total:
        print("\n🎉 所有檢查通過！優化已正確部署。")
    else:
        print("\n⚠️ 部分檢查失敗，請檢查上方詳細資訊。")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
