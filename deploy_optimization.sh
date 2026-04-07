#!/bin/bash
# SELA 優化補丁自動部署腳本
# 使用方式: bash deploy_optimization.sh

set -e

echo "=========================================="
echo "🔧 SELA 優化補丁部署腳本"
echo "=========================================="

# 檢查是否在專案目錄
if [ ! -f "app/main.py" ]; then
    echo "❌ 錯誤: 請在 SELA 專案根目錄執行此腳本"
    exit 1
fi

echo ""
echo "📦 步驟 1: 備份現有檔案..."

# 建立備份目錄
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 備份檔案
cp app/main.py "$BACKUP_DIR/main.py.bak"
cp app/services/price_cache_service.py "$BACKUP_DIR/price_cache_service.py.bak" 2>/dev/null || true
cp railway.json "$BACKUP_DIR/railway.json.bak" 2>/dev/null || true

echo "✅ 備份完成: $BACKUP_DIR"

echo ""
echo "📝 步驟 2: 覆蓋優化檔案..."

# 取得腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 覆蓋檔案
cp "$SCRIPT_DIR/app/main.py" app/main.py
cp "$SCRIPT_DIR/app/services/price_cache_service.py" app/services/price_cache_service.py
cp "$SCRIPT_DIR/railway.json" railway.json

# 複製遷移腳本
mkdir -p migrations
cp "$SCRIPT_DIR/migrations/add_optimized_indexes.py" migrations/

echo "✅ 檔案覆蓋完成"

echo ""
echo "🗄️ 步驟 3: 執行資料庫索引優化..."
echo "(如果失敗，請稍後手動執行: python -m migrations.add_optimized_indexes)"

python -m migrations.add_optimized_indexes --run 2>/dev/null || echo "⚠️ 索引優化需要在有資料庫連線的環境執行"

echo ""
echo "=========================================="
echo "✅ 優化補丁部署完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. git add ."
echo "2. git commit -m '🔧 優化排程減少 60%'"
echo "3. git push"
echo ""
echo "可選: 在 Railway Dashboard 啟用睡眠模式可額外省 50%+"
echo ""
echo "驗證: curl https://your-domain/api/admin/scheduler-status"
echo ""
