# SELA 部署包 2026-01-15

## 包含功能
1. ✅ 追蹤清單 500 錯誤修復（target_price 遷移）
2. ✅ Token 有效期調整（一般用戶 10 分鐘 / 管理員 60 分鐘）
3. ✅ 目標價功能前端（🎯 按鈕 + 達標變色）

## 目錄結構
```
app/
├── config.py              # 新增 JWT_EXPIRE_MINUTES_USER/ADMIN
├── database.py            # 新增 target_price 遷移
└── services/
    └── auth_service.py    # Token 過期時間依角色設定
static/
└── dashboard.html         # 目標價 UI + 動態閒置時間
```

## 部署步驟
```bash
cd /Users/sela/Documents/Python/自動選股系統

# 解壓到專案目錄（會覆蓋對應檔案）
unzip -o deploy-2026-01-15.zip

# 部署
git add .
git commit -m "feat: Token有效期調整 + 目標價功能 + 遷移修復"
git push
```

## 驗證
- 一般用戶登入：閒置計時器顯示 10:00
- 管理員登入：閒置計時器顯示 60:00
- 追蹤清單：🎯 按鈕可設定目標價
