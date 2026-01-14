# 📡 SELA 訂閱精選後端更新包

## 📅 版本：2026-01-14

## 📦 更新內容

```
app/
└── main.py    # 更新：新增訂閱路由和排程
```

### 修改說明

1. **新增 import**：`from app.routers.subscription import router as subscription_router`
2. **新增路由註冊**：`app.include_router(subscription_router)`
3. **新增排程任務**：每小時自動抓取訂閱源

---

## 🚀 部署步驟

1. 將 `app/main.py` 覆蓋到專案
2. 提交並推送到 Railway
3. 部署完成後執行初始化：

```bash
curl -X POST https://web-develop-e7d7.up.railway.app/api/subscription/admin/init

curl -X POST "https://web-develop-e7d7.up.railway.app/api/subscription/admin/fetch?backfill=true"
```

---

## ✅ 驗證

```bash
curl https://web-develop-e7d7.up.railway.app/api/subscription/sources
```

應返回 `{"success": true, "data": [...]}`
