#!/usr/bin/env python3
"""
SELA 追蹤清單分階段載入優化腳本
在專案根目錄執行：python3 fix_watchlist_progressive_load.py
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """備份檔案"""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{filepath}.bak.{timestamp}"
        shutil.copy2(filepath, backup_path)
        print(f"  📦 已備份: {backup_path}")
        return True
    return False


def fix_watchlist_router():
    """修改 app/routers/watchlist.py - 新增 /basic API"""
    filepath = "app/routers/watchlist.py"
    
    print(f"\n🔧 修改 {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  ❌ 檔案不存在: {filepath}")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經有 /basic API
    if '"/basic"' in content or "'/basic'" in content:
        print("  ⚠️ /basic API 已存在，跳過")
        return True
    
    # 新的 /basic API 代碼
    basic_api_code = '''
# ============================================================
# 🆕 基本資料 API（快速版，用於分階段載入）
# ============================================================

@router.get("/basic", summary="追蹤清單（基本資料，快速）")
async def get_watchlist_basic(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶追蹤清單基本資料（不含價格，毫秒級回應）
    
    🚀 效能優化：用於分階段載入的第一階段
    - 只查 watchlist 表和標籤
    - 不查 stock_price_cache
    - 價格欄位回傳 null，前端顯示「載入中」
    """
    logger.info(f"API: 追蹤清單(基本) - user_id={user.id}")

    try:
        # 1. 取得用戶的追蹤清單
        stmt = (
            select(Watchlist)
            .where(Watchlist.user_id == user.id)
            .order_by(Watchlist.added_at.desc())
        )
        result = await db.execute(stmt)
        watchlist_items = list(result.scalars().all())

        if not watchlist_items:
            return {
                "success": True,
                "data": [],
                "total": 0,
            }

        watchlist_ids = [item.id for item in watchlist_items]

        # 2. 批次取得所有標籤關聯
        tags_map = {}
        try:
            tags_stmt = (
                select(
                    watchlist_tags.c.watchlist_id,
                    UserTag
                )
                .join(UserTag, UserTag.id == watchlist_tags.c.tag_id)
                .where(watchlist_tags.c.watchlist_id.in_(watchlist_ids))
            )
            tags_result = await db.execute(tags_stmt)
            
            for row in tags_result:
                wl_id = row[0]
                tag = row[1]
                if wl_id not in tags_map:
                    tags_map[wl_id] = []
                tags_map[wl_id].append({
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color,
                    "icon": tag.icon,
                })
        except Exception as e:
            logger.warning(f"載入標籤失敗: {e}")

        # 3. 組合資料（不含價格）
        data = []
        for item in watchlist_items:
            target_price = float(item.target_price) if item.target_price else None
            target_direction = getattr(item, 'target_direction', 'above') or 'above'

            data.append({
                "id": item.id,
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "note": item.note,
                "target_price": target_price,
                "target_direction": target_direction,
                "target_reached": False,  # 沒有價格無法判斷
                "added_at": item.added_at.isoformat() if item.added_at else None,
                # 價格欄位全部 null（前端會顯示「載入中」）
                "name": None,
                "price": None,
                "change": None,
                "change_pct": None,
                "ma20": None,
                "price_updated_at": None,
                # 標籤
                "tags": tags_map.get(item.id, []),
            })

        return {
            "success": True,
            "data": data,
            "total": len(data),
        }

    except Exception as e:
        logger.error(f"取得追蹤清單(基本)失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


'''
    
    # 找到插入點：在 "# 價格快取 API" 或 "/with-prices" 之前
    # 嘗試多種定位方式
    insert_markers = [
        '# ============================================================\n# 價格快取 API',
        '# 價格快取 API（⭐ 優化版',
        '@router.get("/with-prices"',
    ]
    
    inserted = False
    for marker in insert_markers:
        if marker in content:
            content = content.replace(marker, basic_api_code + marker)
            inserted = True
            print(f"  ✅ 已在 '{marker[:30]}...' 之前插入 /basic API")
            break
    
    if not inserted:
        print("  ❌ 找不到插入點，請手動新增")
        return False
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ {filepath} 修改完成")
    return True


def fix_watchlist_js():
    """修改 static/js/watchlist.js - 替換 loadWatchlist 函數"""
    filepath = "static/js/watchlist.js"
    
    print(f"\n🔧 修改 {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  ❌ 檔案不存在: {filepath}")
        return False
    
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經有 updateWatchlistPrices 函數
    if 'updateWatchlistPrices' in content:
        print("  ⚠️ updateWatchlistPrices 已存在，跳過")
        return True
    
    # 新的 loadWatchlist 函數
    new_loadWatchlist = '''    async function loadWatchlist() {
        const container = $('watchlistContent');
        const currentUser = typeof getCurrentUser === 'function' ? getCurrentUser() : window.currentUser;

        if (!currentUser || !currentUser.id) {
            console.error('loadWatchlist: 用戶未登入');
            if (container) {
                container.innerHTML = '<p class="text-red-500 text-center py-4">請先登入</p>';
            }
            return;
        }

        // ✅ 檢查 AppState 是否已有完整資料（含價格）
        if (window.AppState && AppState.watchlistLoaded && AppState.watchlist.length > 0) {
            const hasPrice = AppState.watchlist.some(item => item.price !== null);
            if (hasPrice) {
                renderWatchlistCards(AppState.watchlist);
                return;
            }
        }

        // 🆕 階段 1：先載入基本資料（毫秒級）
        try {
            if (typeof loadTags === 'function') {
                await loadTags();
            }

            console.log('📦 階段1: 載入基本資料...');
            const basicRes = await apiRequest('/api/watchlist/basic');
            const basicData = await basicRes.json();

            if (!basicData.success || !basicData.data || basicData.data.length === 0) {
                if (container) {
                    container.innerHTML = `
                        <div class="text-center py-12">
                            <i class="fas fa-star text-4xl text-gray-300 mb-3"></i>
                            <p class="text-gray-500">尚無追蹤清單</p>
                            <button data-action="show-add-modal" class="mt-4 px-4 py-2 bg-orange-500 text-white rounded-lg">
                                <i class="fas fa-plus mr-2"></i>新增追蹤
                            </button>
                        </div>
                    `;
                    initWatchlistEventDelegation();
                }
                return;
            }

            // 更新標籤 map
            watchlistTagsMap = {};
            basicData.data.forEach(item => {
                watchlistTagsMap[item.id] = item.tags || [];
            });

            // 🆕 立即渲染（價格顯示「載入中」）
            renderWatchlistCards(basicData.data);
            console.log('✅ 階段1完成: 顯示基本資料');

            // 🆕 階段 2：背景載入價格
            console.log('📦 階段2: 背景載入價格...');
            const priceRes = await apiRequest('/api/watchlist/with-prices');
            const priceData = await priceRes.json();

            if (priceData.success && priceData.data) {
                priceData.data.forEach(item => {
                    watchlistTagsMap[item.id] = item.tags || [];
                });

                // 🆕 平滑更新（不閃爍）
                updateWatchlistPrices(priceData.data);
                console.log('✅ 階段2完成: 價格已更新');
            }

        } catch (e) {
            console.error('載入追蹤清單失敗:', e);
            if (container) {
                container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗，請稍後再試</p>';
            }
        }
    }

    /**
     * 🆕 平滑更新價格（不重新渲染整個清單）
     */
    function updateWatchlistPrices(data) {
        // 更新全域資料
        watchlistData = data;
        if (window.AppState) {
            AppState.setWatchlist(data);
        }

        // 逐一更新卡片價格
        data.forEach(item => {
            const card = document.querySelector(`.stock-card[data-symbol="${item.symbol}"]`);
            if (!card) return;

            // 找到價格區域並更新
            const priceContainer = card.querySelector('.flex.items-baseline');
            if (priceContainer && item.price !== null) {
                const change = item.change_pct || 0;
                const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
                const changeIcon = change >= 0 ? '▲' : '▼';
                const ma20Badge = getMa20Badge(item);

                // 目標價 badge
                let targetBadge = '';
                const hasTarget = item.target_price !== null && item.target_price !== undefined;
                if (hasTarget) {
                    const isAbove = item.target_direction !== 'below';
                    const dirIcon = isAbove ? 'fa-arrow-up' : 'fa-arrow-down';
                    const dirText = isAbove ? '↑' : '↓';
                    
                    if (item.target_reached) {
                        targetBadge = `<span class="ml-2 px-3 py-1 text-sm font-bold rounded-full bg-yellow-400 text-yellow-900 animate-pulse shadow">
                            <i class="fas fa-bell mr-1"></i>${dirText} 已達標 $${item.target_price.toLocaleString()}
                        </span>`;
                    } else {
                        const diff = ((item.target_price - item.price) / item.price * 100).toFixed(1);
                        const badgeStyle = isAbove 
                            ? 'bg-green-100 text-green-700 border border-green-400' 
                            : 'bg-red-100 text-red-700 border border-red-400';
                        targetBadge = `<span class="ml-2 px-3 py-1 text-sm font-medium rounded-full ${badgeStyle}">
                            <i class="fas ${dirIcon} mr-1"></i>目標 $${item.target_price.toLocaleString()} (${diff > 0 ? '+' : ''}${diff}%)
                        </span>`;
                    }
                }

                priceContainer.innerHTML = `
                    <span class="text-xl font-bold text-gray-800">$${item.price.toLocaleString()}</span>
                    <span class="${changeClass} text-sm font-medium">${changeIcon} ${Math.abs(change).toFixed(2)}%</span>
                    ${ma20Badge}
                    ${targetBadge}
                `;

                // 淡入效果
                priceContainer.style.opacity = '0';
                priceContainer.style.transition = 'opacity 0.3s';
                setTimeout(() => { priceContainer.style.opacity = '1'; }, 50);
            }

            // 更新名稱
            if (item.name) {
                const nameSpan = card.querySelector('.text-gray-500.text-sm.ml-2');
                if (nameSpan) {
                    nameSpan.textContent = item.name;
                }
            }

            // 更新到價提示
            if (item.target_reached) {
                card.classList.add('border-yellow-500', 'ring-2', 'ring-yellow-300');
                card.classList.remove('border-blue-500', 'border-purple-500');
            }
        });
    }

'''
    
    # 使用正則表達式找到舊的 loadWatchlist 函數並替換
    # 模式：從 "async function loadWatchlist()" 到下一個同級函數
    old_pattern = r'(    async function loadWatchlist\(\) \{[\s\S]*?\n    \}\n)\n    async function loadAllWatchlistTags'
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_loadWatchlist + '\n    async function loadAllWatchlistTags', content)
        print("  ✅ 已替換 loadWatchlist 函數並新增 updateWatchlistPrices")
    else:
        # 備用方案：直接字串替換
        old_func_start = '    async function loadWatchlist() {'
        old_func_marker = '    async function loadAllWatchlistTags(items) {'
        
        if old_func_start in content and old_func_marker in content:
            # 找到 loadWatchlist 開始位置
            start_idx = content.find(old_func_start)
            # 找到 loadAllWatchlistTags 開始位置
            end_idx = content.find(old_func_marker)
            
            if start_idx < end_idx:
                # 替換這段區域
                content = content[:start_idx] + new_loadWatchlist + content[end_idx:]
                print("  ✅ 已替換 loadWatchlist 函數並新增 updateWatchlistPrices (備用方案)")
            else:
                print("  ❌ 函數位置異常，請手動修改")
                return False
        else:
            print("  ❌ 找不到 loadWatchlist 函數，請手動修改")
            return False
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ {filepath} 修改完成")
    return True


def main():
    print("=" * 60)
    print("🚀 SELA 追蹤清單分階段載入優化")
    print("=" * 60)
    
    # 檢查是否在專案根目錄
    if not os.path.exists("app/routers/watchlist.py"):
        print("\n❌ 請在專案根目錄執行此腳本")
        print("   預期檔案: app/routers/watchlist.py")
        return
    
    success = True
    
    # 1. 修改後端
    if not fix_watchlist_router():
        success = False
    
    # 2. 修改前端
    if not fix_watchlist_js():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有修改完成！")
        print("\n📦 部署命令:")
        print("   git add app/routers/watchlist.py static/js/watchlist.js")
        print('   git commit -m "追蹤清單分階段載入：先顯示基本資料，背景載入價格"')
        print("   git push origin main")
        print("\n📋 驗證方式:")
        print("   開啟 F12 Console，點擊「追蹤」Tab")
        print("   應看到：")
        print("   📦 階段1: 載入基本資料...")
        print("   ✅ 階段1完成: 顯示基本資料")
        print("   📦 階段2: 背景載入價格...")
        print("   ✅ 階段2完成: 價格已更新")
    else:
        print("⚠️ 部分修改失敗，請檢查上方訊息")
    print("=" * 60)


if __name__ == "__main__":
    main()
