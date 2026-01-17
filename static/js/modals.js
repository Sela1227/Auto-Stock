/**
 * Modal 動態生成模組
 * 將所有 Modal HTML 從 dashboard.html 移出，改為 JavaScript 動態創建
 * 
 * 使用方式：
 * 1. 在 dashboard.html 引入此檔案
 * 2. 在 DOMContentLoaded 或適當時機調用 initAllModals()
 */

(function() {
    'use strict';

    // ============================================================
    // Modal 模板定義
    // ============================================================

    const MODAL_TEMPLATES = {
        // ===== 全螢幕圖表 =====
        chartFullscreen: `
            <div id="chartFullscreen" class="chart-fullscreen">
                <div class="chart-container h-full flex flex-col">
                    <div class="rotate-banner">
                        📱 橫向放置手機可獲得更好的圖表體驗
                    </div>
                    <div class="flex items-center justify-between p-3 border-b bg-white">
                        <button onclick="closeChartFullscreen()" class="p-2 text-gray-600 touch-target">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                        <span id="chartFullscreenTitle" class="font-bold text-lg"></span>
                        <div class="w-10"></div>
                    </div>
                    <div class="flex-1 p-4 bg-gray-50" style="min-height: 200px;">
                        <canvas id="fullscreenChart"></canvas>
                    </div>
                    <div class="flex items-center justify-center gap-2 p-3 bg-white border-t" id="chartRangeButtons">
                        <button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target" data-days="22">1M</button>
                        <button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target active" data-days="65">3M</button>
                        <button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target" data-days="130">6M</button>
                        <button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target" data-days="252">1Y</button>
                        <button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target" data-days="756">3Y</button>
                        <button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target" data-days="1260">5Y</button>
                        <button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target" data-days="99999">MAX</button>
                    </div>
                </div>
            </div>
        `,

        // ===== 指數圖表 Modal =====
        indexChartModal: `
            <div id="indexChartModal" class="chart-fullscreen">
                <div class="chart-container h-full flex flex-col">
                    <div class="rotate-banner">
                        📱 橫向放置手機可獲得更好的圖表體驗
                    </div>
                    <div class="flex items-center justify-between p-3 border-b bg-white">
                        <button onclick="closeIndexModal()" class="p-2 text-gray-600 touch-target">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                        <span id="indexModalTitle" class="font-bold text-lg"></span>
                        <div class="w-10"></div>
                    </div>
                    <div class="flex-1 p-4 bg-gray-50" style="min-height: 200px;">
                        <canvas id="indexModalChart"></canvas>
                    </div>
                    <div class="flex items-center justify-center gap-2 p-3 bg-white border-t">
                        <button type="button" onclick="loadIndexModalChart(30)" class="index-modal-btn px-4 py-2 text-sm rounded border touch-target">1M</button>
                        <button type="button" onclick="loadIndexModalChart(90)" class="index-modal-btn px-4 py-2 text-sm rounded border touch-target">3M</button>
                        <button type="button" onclick="loadIndexModalChart(365)" class="index-modal-btn px-4 py-2 text-sm rounded border touch-target active">1Y</button>
                        <button type="button" onclick="loadIndexModalChart(1825)" class="index-modal-btn px-4 py-2 text-sm rounded border touch-target">5Y</button>
                    </div>
                </div>
            </div>
        `,

        // ===== 情緒圖表 Modal =====
        sentimentChartModal: `
            <div id="sentimentChartModal" class="chart-fullscreen">
                <div class="chart-container h-full flex flex-col">
                    <div class="rotate-banner">
                        📱 橫向放置手機可獲得更好的圖表體驗
                    </div>
                    <div class="flex items-center justify-between p-3 border-b bg-white">
                        <button onclick="closeSentimentModal()" class="p-2 text-gray-600 touch-target">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                        <span id="sentimentModalTitle" class="font-bold text-lg"></span>
                        <div class="w-10"></div>
                    </div>
                    <div class="flex-1 p-4 bg-gray-50" style="min-height: 200px;">
                        <canvas id="sentimentModalChart"></canvas>
                    </div>
                    <div class="flex items-center justify-center gap-2 p-3 bg-white border-t">
                        <button type="button" onclick="loadSentimentModalChart(30)" class="sentiment-modal-btn px-4 py-2 text-sm rounded border touch-target">1M</button>
                        <button type="button" onclick="loadSentimentModalChart(90)" class="sentiment-modal-btn px-4 py-2 text-sm rounded border touch-target">3M</button>
                        <button type="button" onclick="loadSentimentModalChart(180)" class="sentiment-modal-btn px-4 py-2 text-sm rounded border touch-target active">6M</button>
                        <button type="button" onclick="loadSentimentModalChart(365)" class="sentiment-modal-btn px-4 py-2 text-sm rounded border touch-target">1Y</button>
                    </div>
                </div>
            </div>
        `,

        // ===== 年化報酬率 Modal =====
        returnsModal: `
            <div id="returnsModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-[3000] p-4">
                <div class="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
                    <div class="sticky top-0 bg-white p-4 border-b flex items-center justify-between">
                        <h3 class="text-lg font-bold text-gray-800">
                            <i class="fas fa-percentage text-green-600 mr-2"></i>
                            <span id="returnsModalTitle">年化報酬率</span>
                        </h3>
                        <button onclick="closeReturnsModal()" class="p-2 text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    <div id="returnsModalContent" class="p-4">
                        <div class="text-center py-8">
                            <i class="fas fa-spinner fa-spin text-2xl text-green-600"></i>
                            <p class="mt-2 text-gray-500">計算中...</p>
                        </div>
                    </div>
                </div>
            </div>
        `,

        // ===== 台股交易 Modal =====
        twTransactionModal: `
            <div id="twTransactionModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-[3000] p-4">
                <div class="bg-white rounded-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
                    <div class="sticky top-0 bg-white p-4 border-b flex items-center justify-between">
                        <h3 class="text-lg font-bold text-gray-800">
                            <i class="fas fa-landmark text-red-500 mr-2"></i>
                            <span id="twModalTitle">新增台股交易</span>
                        </h3>
                        <button onclick="closeTwModal()" class="p-2 text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    <div class="p-4">
                        <input type="hidden" id="twEditId">
                        
                        <!-- 交易類型 -->
                        <div class="flex gap-2 mb-4">
                            <button type="button" onclick="setTwType('buy')" id="twBtnBuy" class="flex-1 py-2 rounded-lg font-medium transition-all bg-green-500 text-white">
                                <i class="fas fa-arrow-down mr-1"></i>買入
                            </button>
                            <button type="button" onclick="setTwType('sell')" id="twBtnSell" class="flex-1 py-2 rounded-lg font-medium transition-all bg-gray-200 text-gray-600">
                                <i class="fas fa-arrow-up mr-1"></i>賣出
                            </button>
                        </div>
                        <input type="hidden" id="twTxType" value="buy">
                        
                        <!-- 股票代碼 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">股票代碼 <span class="text-red-500">*</span></label>
                            <input type="text" id="twSymbol" placeholder="例: 2330" 
                                   oninput="lookupTwStock()"
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500">
                        </div>
                        
                        <!-- 股票名稱（唯讀） -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">股票名稱</label>
                            <div id="twNameDisplay" class="w-full px-4 py-2 border rounded-lg bg-gray-50 text-gray-600 min-h-[42px] flex items-center">
                                <span class="text-gray-400">輸入代碼自動帶入</span>
                            </div>
                            <input type="hidden" id="twName">
                        </div>
                        
                        <!-- 數量：張 + 零股 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">數量 <span class="text-red-500">*</span></label>
                            <div class="grid grid-cols-2 gap-3">
                                <div class="relative">
                                    <input type="number" id="twLots" placeholder="0" min="0"
                                           oninput="updateTwQuantity()"
                                           class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 pr-10">
                                    <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">張</span>
                                </div>
                                <div class="relative">
                                    <input type="number" id="twOddLot" placeholder="0" min="0" max="999"
                                           oninput="updateTwQuantity()"
                                           class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 pr-12">
                                    <span class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">零股</span>
                                </div>
                            </div>
                            <p id="twQuantityDisplay" class="text-xs text-gray-500 mt-1">= 0 股</p>
                        </div>
                        
                        <!-- 成交價 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">成交價 <span class="text-red-500">*</span></label>
                            <input type="number" id="twPrice" placeholder="850" step="0.01" min="0.01"
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500">
                        </div>
                        <!-- 手續費和交易稅（隱藏） -->
                        <input type="hidden" id="twFee" value="0">
                        <input type="hidden" id="twTax" value="0">
                        
                        <!-- 券商選擇 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">券商（選填）</label>
                            <select id="twBroker" onchange="handleBrokerChange('twBroker')"
                                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500">
                                <option value="">不指定券商</option>
                            </select>
                        </div>
                        
                        <!-- 交易日期 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">交易日期 <span class="text-red-500">*</span></label>
                            <input type="date" id="twDate" 
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500">
                        </div>
                        
                        <!-- 備註 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">備註</label>
                            <input type="text" id="twNote" placeholder="選填" 
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-red-500">
                        </div>
                        
                        <!-- 送出 -->
                        <button onclick="submitTwTransaction()" class="w-full py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium">
                            <i class="fas fa-check mr-2"></i>確認
                        </button>
                    </div>
                </div>
            </div>
        `,

        // ===== 美股交易 Modal =====
        usTransactionModal: `
            <div id="usTransactionModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-[3000] p-4">
                <div class="bg-white rounded-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
                    <div class="sticky top-0 bg-white p-4 border-b flex items-center justify-between">
                        <h3 class="text-lg font-bold text-gray-800">
                            <i class="fas fa-flag-usa text-blue-500 mr-2"></i>
                            <span id="usModalTitle">新增美股交易</span>
                        </h3>
                        <button onclick="closeUsModal()" class="p-2 text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    <div class="p-4">
                        <input type="hidden" id="usEditId">
                        
                        <!-- 交易類型 -->
                        <div class="flex gap-2 mb-4">
                            <button type="button" onclick="setUsType('buy')" id="usBtnBuy" class="flex-1 py-2 rounded-lg font-medium transition-all bg-green-500 text-white">
                                <i class="fas fa-arrow-down mr-1"></i>買入
                            </button>
                            <button type="button" onclick="setUsType('sell')" id="usBtnSell" class="flex-1 py-2 rounded-lg font-medium transition-all bg-gray-200 text-gray-600">
                                <i class="fas fa-arrow-up mr-1"></i>賣出
                            </button>
                        </div>
                        <input type="hidden" id="usTxType" value="buy">
                        
                        <!-- 股票代碼 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">股票代碼 <span class="text-red-500">*</span></label>
                            <input type="text" id="usSymbol" placeholder="例: AAPL" 
                                   oninput="lookupUsStock()"
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 uppercase">
                        </div>
                        
                        <!-- 股票名稱（唯讀） -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">股票名稱</label>
                            <div id="usNameDisplay" class="w-full px-4 py-2 border rounded-lg bg-gray-50 text-gray-600 min-h-[42px] flex items-center">
                                <span class="text-gray-400">輸入代碼自動帶入</span>
                            </div>
                            <input type="hidden" id="usName">
                        </div>
                        
                        <!-- 股數 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">股數 <span class="text-red-500">*</span></label>
                            <input type="number" id="usQuantity" placeholder="10" min="1"
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                        </div>
                        
                        <!-- 成交價 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">成交價 (USD) <span class="text-red-500">*</span></label>
                            <input type="number" id="usPrice" placeholder="185.50" step="0.01" min="0.01"
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                        </div>
                        <!-- 手續費和交易稅（隱藏） -->
                        <input type="hidden" id="usFee" value="0">
                        <input type="hidden" id="usTax" value="0">
                        
                        <!-- 券商選擇 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">券商（選填）</label>
                            <select id="usBroker" onchange="handleBrokerChange('usBroker')"
                                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                                <option value="">不指定券商</option>
                            </select>
                        </div>
                        
                        <!-- 交易日期 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">交易日期 <span class="text-red-500">*</span></label>
                            <input type="date" id="usDate" 
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                        </div>
                        
                        <!-- 備註 -->
                        <div class="mb-4">
                            <label class="block text-gray-700 mb-2 text-sm">備註</label>
                            <input type="text" id="usNote" placeholder="選填" 
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                        </div>
                        
                        <!-- 送出 -->
                        <button onclick="submitUsTransaction()" class="w-full py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium">
                            <i class="fas fa-check mr-2"></i>確認
                        </button>
                    </div>
                </div>
            </div>
        `,

        // ===== 新增追蹤清單 Modal =====
        addWatchlistModal: `
            <div id="addWatchlistModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-[3000] p-4">
                <div class="bg-white rounded-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
                    <h3 class="text-lg font-bold text-gray-800 mb-4">新增追蹤</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-gray-700 mb-2 text-sm">股票/加密貨幣代號</label>
                            <input type="text" id="addSymbol" placeholder="如 AAPL、BTC" 
                                class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 text-base">
                        </div>
                        <div>
                            <label class="block text-gray-700 mb-2 text-sm">類型</label>
                            <select id="addAssetType" class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 text-base">
                                <option value="stock">股票</option>
                                <option value="crypto">加密貨幣</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-gray-700 mb-2 text-sm">備註（選填）</label>
                            <input type="text" id="addNote" placeholder="自訂備註" 
                                class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 text-base">
                        </div>
                    </div>
                    <div class="flex gap-3 mt-6">
                        <button onclick="hideAddWatchlistModal()" class="flex-1 px-4 py-3 border rounded-lg hover:bg-gray-50 touch-target">取消</button>
                        <button onclick="addToWatchlist()" class="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 touch-target">新增</button>
                    </div>
                </div>
            </div>
        `,

        // ===== 匯入追蹤清單 Modal =====
        importWatchlistModal: `
            <div id="importWatchlistModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-[3000] p-4">
                <div class="bg-white rounded-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
                    <h3 class="text-lg font-bold text-gray-800 mb-4">
                        <i class="fas fa-upload mr-2 text-orange-500"></i>匯入追蹤清單
                    </h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-gray-700 mb-2 text-sm">選擇檔案 (JSON 或 CSV)</label>
                            <input type="file" id="importWatchlistFile" accept=".json,.csv" onchange="previewWatchlistFile(this)"
                                class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 text-base">
                        </div>
                        <div id="importWatchlistPreview" class="min-h-[60px]"></div>
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <p class="text-xs text-gray-500">
                                <i class="fas fa-info-circle mr-1"></i>
                                CSV 格式需包含 symbol 欄位，可選 asset_type, note, target_price
                            </p>
                        </div>
                    </div>
                    <div class="flex gap-3 mt-6">
                        <button onclick="hideImportWatchlistModal()" class="flex-1 px-4 py-3 border rounded-lg hover:bg-gray-50 touch-target">取消</button>
                        <button onclick="importWatchlist()" class="flex-1 px-4 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 touch-target">匯入</button>
                    </div>
                </div>
            </div>
        `,

        // ===== 匯入持股交易 Modal =====
        importPortfolioModal: `
            <div id="importPortfolioModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-[3000] p-4">
                <div class="bg-white rounded-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
                    <h3 class="text-lg font-bold text-gray-800 mb-4">
                        <i class="fas fa-upload mr-2 text-orange-500"></i>匯入交易紀錄
                    </h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-gray-700 mb-2 text-sm">選擇檔案 (JSON 或 CSV)</label>
                            <input type="file" id="importPortfolioFile" accept=".json,.csv" onchange="previewPortfolioFile(this)"
                                class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 text-base">
                        </div>
                        <div id="importPortfolioPreview" class="min-h-[60px]"></div>
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <p class="text-xs text-gray-500">
                                <i class="fas fa-info-circle mr-1"></i>
                                必填欄位: symbol, quantity, price, transaction_date (YYYY-MM-DD)<br>
                                可選欄位: name, market (tw/us), transaction_type (buy/sell), fee, tax, note
                            </p>
                        </div>
                    </div>
                    <div class="flex gap-3 mt-6">
                        <button onclick="hideImportPortfolioModal()" class="flex-1 px-4 py-3 border rounded-lg hover:bg-gray-50 touch-target">取消</button>
                        <button onclick="importPortfolio()" class="flex-1 px-4 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 touch-target">匯入</button>
                    </div>
                </div>
            </div>
        `,

        // ===== 目標價設定 Modal =====
        targetPriceModal: `
            <div id="targetPriceModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-[3000] p-4">
                <div class="bg-white rounded-xl w-full max-w-sm p-6">
                    <h3 class="text-lg font-bold text-gray-800 mb-4">
                        <i class="fas fa-crosshairs mr-2 text-yellow-500"></i>設定目標價
                    </h3>
                    <div class="space-y-4">
                        <div class="text-center">
                            <span id="targetPriceSymbol" class="text-2xl font-bold text-gray-800"></span>
                        </div>
                        <div>
                            <label class="block text-gray-700 mb-2 text-sm">目標價格</label>
                            <input type="number" id="targetPriceInput" step="0.01" placeholder="輸入目標價格" 
                                class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-yellow-500 text-base text-center text-lg">
                        </div>
                        <div>
                            <label class="block text-gray-700 mb-2 text-sm">提醒方向</label>
                            <div class="grid grid-cols-2 gap-3">
                                <label id="labelAbove" class="flex items-center justify-center p-3 border-2 rounded-lg cursor-pointer hover:bg-green-50 border-gray-200">
                                    <input type="radio" name="targetDirection" id="directionAbove" value="above" checked class="sr-only" onchange="updateDirectionStyle()">
                                    <span class="text-center">
                                        <i class="fas fa-arrow-up text-green-500 text-lg"></i>
                                        <div class="text-sm font-medium mt-1">高於時提醒</div>
                                        <div class="text-xs text-gray-500">突破買入</div>
                                    </span>
                                </label>
                                <label id="labelBelow" class="flex items-center justify-center p-3 border-2 rounded-lg cursor-pointer hover:bg-red-50 border-gray-200">
                                    <input type="radio" name="targetDirection" id="directionBelow" value="below" class="sr-only" onchange="updateDirectionStyle()">
                                    <span class="text-center">
                                        <i class="fas fa-arrow-down text-red-500 text-lg"></i>
                                        <div class="text-sm font-medium mt-1">低於時提醒</div>
                                        <div class="text-xs text-gray-500">跌破停損</div>
                                    </span>
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-3 mt-6">
                        <button onclick="hideTargetPriceModal()" class="flex-1 px-4 py-3 border rounded-lg hover:bg-gray-50 touch-target">取消</button>
                        <button onclick="clearTargetPrice()" class="px-4 py-3 text-red-500 hover:bg-red-50 rounded-lg touch-target">清除</button>
                        <button onclick="saveTargetPrice()" class="flex-1 px-4 py-3 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 touch-target">儲存</button>
                    </div>
                </div>
            </div>
        `,

        // ===== Toast 通知 =====
        toast: `
            <div id="toast" class="fixed bottom-20 md:bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-auto bg-gray-800 text-white px-6 py-3 rounded-lg shadow-lg hidden transition-opacity text-center">
                <span id="toastMessage"></span>
            </div>
        `,

        // ===== 標籤編輯 Modal =====
        tagEditModal: `
            <div id="tagEditModal" class="hidden fixed inset-0 bg-black bg-opacity-50 items-center justify-center z-50">
                <div class="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 id="tagModalTitle" class="text-lg font-bold text-gray-800">
                            <i class="fas fa-tag mr-2 text-blue-500"></i>新增標籤
                        </h3>
                        <button onclick="hideTagEditModal()" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">標籤名稱</label>
                            <input type="text" id="tagNameInput" placeholder="例如：長期持有" maxlength="50"
                                   class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">顏色</label>
                            <div class="flex flex-wrap gap-2" id="tagColorOptions">
                                <button type="button" onclick="selectTagColor('#3B82F6')" class="w-8 h-8 rounded-full bg-blue-500 ring-2 ring-offset-2 ring-blue-500"></button>
                                <button type="button" onclick="selectTagColor('#10B981')" class="w-8 h-8 rounded-full bg-emerald-500 hover:ring-2 hover:ring-offset-2 hover:ring-emerald-500"></button>
                                <button type="button" onclick="selectTagColor('#EF4444')" class="w-8 h-8 rounded-full bg-red-500 hover:ring-2 hover:ring-offset-2 hover:ring-red-500"></button>
                                <button type="button" onclick="selectTagColor('#F59E0B')" class="w-8 h-8 rounded-full bg-amber-500 hover:ring-2 hover:ring-offset-2 hover:ring-amber-500"></button>
                                <button type="button" onclick="selectTagColor('#8B5CF6')" class="w-8 h-8 rounded-full bg-violet-500 hover:ring-2 hover:ring-offset-2 hover:ring-violet-500"></button>
                                <button type="button" onclick="selectTagColor('#EC4899')" class="w-8 h-8 rounded-full bg-pink-500 hover:ring-2 hover:ring-offset-2 hover:ring-pink-500"></button>
                                <button type="button" onclick="selectTagColor('#6366F1')" class="w-8 h-8 rounded-full bg-indigo-500 hover:ring-2 hover:ring-offset-2 hover:ring-indigo-500"></button>
                                <button type="button" onclick="selectTagColor('#06B6D4')" class="w-8 h-8 rounded-full bg-cyan-500 hover:ring-2 hover:ring-offset-2 hover:ring-cyan-500"></button>
                                <button type="button" onclick="selectTagColor('#F97316')" class="w-8 h-8 rounded-full bg-orange-500 hover:ring-2 hover:ring-offset-2 hover:ring-orange-500"></button>
                                <button type="button" onclick="selectTagColor('#6B7280')" class="w-8 h-8 rounded-full bg-gray-500 hover:ring-2 hover:ring-offset-2 hover:ring-gray-500"></button>
                            </div>
                            <input type="hidden" id="tagColorInput" value="#3B82F6">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">圖示</label>
                            <div class="flex flex-wrap gap-2" id="tagIconOptions">
                                <button type="button" onclick="selectTagIcon('fa-tag')" class="w-10 h-10 rounded-lg border-2 border-blue-500 bg-blue-50 text-blue-500 flex items-center justify-center"><i class="fas fa-tag"></i></button>
                                <button type="button" onclick="selectTagIcon('fa-star')" class="w-10 h-10 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-500 flex items-center justify-center text-gray-400"><i class="fas fa-star"></i></button>
                                <button type="button" onclick="selectTagIcon('fa-heart')" class="w-10 h-10 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-500 flex items-center justify-center text-gray-400"><i class="fas fa-heart"></i></button>
                                <button type="button" onclick="selectTagIcon('fa-bookmark')" class="w-10 h-10 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-500 flex items-center justify-center text-gray-400"><i class="fas fa-bookmark"></i></button>
                                <button type="button" onclick="selectTagIcon('fa-flag')" class="w-10 h-10 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-500 flex items-center justify-center text-gray-400"><i class="fas fa-flag"></i></button>
                                <button type="button" onclick="selectTagIcon('fa-folder')" class="w-10 h-10 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-500 flex items-center justify-center text-gray-400"><i class="fas fa-folder"></i></button>
                                <button type="button" onclick="selectTagIcon('fa-fire')" class="w-10 h-10 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-500 flex items-center justify-center text-gray-400"><i class="fas fa-fire"></i></button>
                                <button type="button" onclick="selectTagIcon('fa-bolt')" class="w-10 h-10 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-500 flex items-center justify-center text-gray-400"><i class="fas fa-bolt"></i></button>
                            </div>
                            <input type="hidden" id="tagIconInput" value="fa-tag">
                        </div>
                    </div>
                    <div class="flex justify-end gap-2 mt-6">
                        <button onclick="hideTagEditModal()" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">取消</button>
                        <button onclick="saveTagFromModal()" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"><i class="fas fa-check mr-2"></i>儲存</button>
                    </div>
                </div>
            </div>
        `,

        // ===== 標籤指派 Modal =====
        assignTagModal: `
            <div id="assignTagModal" class="hidden fixed inset-0 bg-black bg-opacity-50 items-center justify-center z-50">
                <div class="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-bold text-gray-800">
                            <i class="fas fa-tags mr-2 text-blue-500"></i>設定標籤 - <span id="assignTagSymbol" class="text-blue-600"></span>
                        </h3>
                        <button onclick="hideAssignTagModal()" class="text-gray-400 hover:text-gray-600"><i class="fas fa-times text-xl"></i></button>
                    </div>
                    <div id="assignTagList" class="space-y-2 max-h-80 overflow-y-auto mb-4">
                        <p class="text-gray-400 text-center">載入中...</p>
                    </div>
                    <div class="flex justify-end gap-2">
                        <button onclick="hideAssignTagModal()" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">取消</button>
                        <button onclick="saveAssignedTags()" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"><i class="fas fa-check mr-2"></i>儲存</button>
                    </div>
                </div>
            </div>
        `
    };

    // ============================================================
    // Modal 容器
    // ============================================================

    let modalContainer = null;

    /**
     * 初始化 Modal 容器
     */
    function initModalContainer() {
        if (modalContainer) return modalContainer;
        
        modalContainer = document.getElementById('modal-container');
        if (!modalContainer) {
            modalContainer = document.createElement('div');
            modalContainer.id = 'modal-container';
            document.body.appendChild(modalContainer);
        }
        return modalContainer;
    }

    /**
     * 初始化所有 Modals
     */
    function initAllModals() {
        const container = initModalContainer();
        
        // 按順序插入所有 Modal
        const modalOrder = [
            'chartFullscreen',
            'indexChartModal',
            'sentimentChartModal',
            'returnsModal',
            'twTransactionModal',
            'usTransactionModal',
            'addWatchlistModal',
            'importWatchlistModal',
            'importPortfolioModal',
            'targetPriceModal',
            'toast',
            'tagEditModal',
            'assignTagModal'
        ];

        let html = '';
        for (const key of modalOrder) {
            if (MODAL_TEMPLATES[key]) {
                html += MODAL_TEMPLATES[key];
            }
        }
        
        container.innerHTML = html;
        console.log('✅ 所有 Modal 已初始化');
    }

    /**
     * 動態載入單一 Modal（按需載入）
     */
    function loadModal(modalKey) {
        if (!MODAL_TEMPLATES[modalKey]) {
            console.error(`Modal "${modalKey}" 不存在`);
            return null;
        }

        const existingModal = document.getElementById(modalKey);
        if (existingModal) {
            return existingModal;
        }

        const container = initModalContainer();
        const temp = document.createElement('div');
        temp.innerHTML = MODAL_TEMPLATES[modalKey];
        const modal = temp.firstElementChild;
        container.appendChild(modal);
        
        return modal;
    }

    // ============================================================
    // 目標價方向選擇樣式更新
    // ============================================================
    
    function updateDirectionStyle() {
        const labelAbove = document.getElementById('labelAbove');
        const labelBelow = document.getElementById('labelBelow');
        const radioAbove = document.getElementById('directionAbove');
        const radioBelow = document.getElementById('directionBelow');
        
        if (labelAbove && radioAbove) {
            if (radioAbove.checked) {
                labelAbove.classList.remove('border-gray-200');
                labelAbove.classList.add('border-green-500', 'bg-green-50');
            } else {
                labelAbove.classList.add('border-gray-200');
                labelAbove.classList.remove('border-green-500', 'bg-green-50');
            }
        }
        
        if (labelBelow && radioBelow) {
            if (radioBelow.checked) {
                labelBelow.classList.remove('border-gray-200');
                labelBelow.classList.add('border-red-500', 'bg-red-50');
            } else {
                labelBelow.classList.add('border-gray-200');
                labelBelow.classList.remove('border-red-500', 'bg-red-50');
            }
        }
    }
    
    // 導出到全域
    window.updateDirectionStyle = updateDirectionStyle;

    // ============================================================
    // 導出到全域
    // ============================================================

    window.initAllModals = initAllModals;
    window.loadModal = loadModal;

    // 自動初始化（當 DOM 載入完成時）
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllModals);
    } else {
        // DOM 已經載入完成
        initAllModals();
    }

})();
