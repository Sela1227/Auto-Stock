# 券商功能部署指南

## 📁 檔案清單

| 檔案 | 目標位置 | 說明 |
|------|----------|------|
| `broker.py` (模型) | `app/models/broker.py` | 券商資料模型 |
| `broker_router.py` | `app/routers/broker.py` | 券商 API |
| `broker.js` | `static/js/broker.js` | 券商管理前端 |
| `transaction.js` | `static/js/transaction.js` | 交易表單（含券商選擇） |
| `modals.js` | `static/js/modals.js` | Modal 模板（含券商選擇 UI） |

---

## 🔧 後端修改

### 1. 新增檔案

```bash
# 複製模型
cp broker.py app/models/broker.py

# 複製 API（注意改名）
cp broker_router.py app/routers/broker.py
```

### 2. 修改 main.py

```python
# 加入 import
from app.routers.broker import router as broker_router

# 加入 router（在其他 include_router 附近）
app.include_router(broker_router)
```

### 3. 修改 database.py

在 `run_migrations()` 函數中加入：

```python
async def migrate_add_brokers():
    """新增券商表和交易表 broker_id 欄位"""
    async with engine.begin() as conn:
        # 建立 brokers 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS brokers (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(50) NOT NULL,
                color VARCHAR(20) DEFAULT '#6B7280',
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_broker_user ON brokers(user_id)
        """))
        
        # 在交易表加入 broker_id
        try:
            await conn.execute(text("""
                ALTER TABLE portfolio_transactions 
                ADD COLUMN IF NOT EXISTS broker_id INTEGER REFERENCES brokers(id) ON DELETE SET NULL
            """))
        except Exception as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"broker_id: {e}")
        
        logger.info("✅ brokers 遷移完成")

# 在 run_migrations() 中呼叫
await migrate_add_brokers()
```

### 4. 修改 portfolio.py (Schema)

```python
class TransactionCreate(BaseModel):
    # ... 現有欄位 ...
    broker_id: Optional[int] = Field(None, description="券商 ID")  # 新增

class TransactionUpdate(BaseModel):
    # ... 現有欄位 ...
    broker_id: Optional[int] = None  # 新增
```

### 5. 修改 portfolio.py (建立交易)

在建立 `PortfolioTransaction` 時加入：

```python
transaction = PortfolioTransaction(
    # ... 現有欄位 ...
    broker_id=data.broker_id,  # 新增
)
```

### 6. 修改 PortfolioTransaction 模型

```python
class PortfolioTransaction(Base):
    # ... 現有欄位 ...
    broker_id = Column(Integer, ForeignKey("brokers.id", ondelete="SET NULL"), nullable=True)
```

---

## 🎨 前端修改

### 1. 複製檔案

```bash
cp transaction.js static/js/transaction.js
cp modals.js static/js/modals.js
cp broker.js static/js/broker.js
```

### 2. 在 dashboard.html 加入 broker.js

```html
<script src="/static/js/broker.js"></script>
```

### 3. 在投資記錄頁面加入券商管理區塊

```html
<!-- 券商管理區塊 -->
<div class="bg-white rounded-xl shadow p-4 mt-4">
    <h3 class="font-semibold text-gray-700 mb-3 flex items-center justify-between">
        <span><i class="fas fa-building mr-2 text-purple-500"></i>券商管理</span>
        <button onclick="addBroker()" class="text-sm bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded-lg">
            <i class="fas fa-plus mr-1"></i>新增
        </button>
    </h3>
    <div id="brokerManagerList" class="space-y-2">
        <p class="text-center py-4 text-gray-400">載入中...</p>
    </div>
</div>
```

### 4. 初始化券商管理

在頁面載入時呼叫：

```javascript
if (typeof loadBrokerManager === 'function') {
    loadBrokerManager();
}
```

---

## ✅ 功能說明

### 新增交易時
- 下拉選單可選擇已建立的券商
- 選擇「+ 新增券商...」可快速建立新券商
- 預設券商會自動選中

### 券商管理
- 在投資記錄頁面可管理券商
- 支援新增、編輯、刪除
- 可設定預設券商

---

## 📝 測試檢查清單

- [ ] 新增券商
- [ ] 編輯券商名稱
- [ ] 刪除券商
- [ ] 新增交易時選擇券商
- [ ] 新增交易時快速建立券商
- [ ] 預設券商自動選中
