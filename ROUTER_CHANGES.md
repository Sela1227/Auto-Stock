# 📋 Router 修改快速參考

以下是各 router 檔案需要修改的具體內容。

---

## 🔧 通用修改模式

### 刪除（約 15-20 行）

找到並**刪除**類似以下的重複程式碼：

```python
# ❌ 刪除這整段
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """依賴注入：取得當前用戶"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("API: 未提供認證 Token")
        raise HTTPException(
            status_code=401,
            detail="未提供認證 Token"
        )
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        logger.warning("API: Token 驗證失敗")
        raise HTTPException(
            status_code=401,
            detail="無效的 Token"
        )
    
    return user
```

也要刪除可能存在的 `get_optional_user` 和 `get_current_admin` 重複定義。

### 新增（1 行）

在檔案開頭的 import 區加入：

```python
# ✅ 加入這行
from app.dependencies import get_current_user, get_admin_user, get_optional_user
```

---

## 📁 各檔案具體修改

### 1. `app/routers/subscription.py`

```python
# 刪除約第 20-40 行的 get_current_user 定義

# 在 import 區加入
from app.dependencies import get_current_user, get_admin_user
```

**已提供完整修改後版本**: `sela_p0_fix/app/routers/subscription.py`

---

### 2. `app/routers/portfolio.py`

```python
# 刪除約第 70-90 行的 get_current_user 定義

# 在 import 區加入（約第 15 行）
from app.dependencies import get_current_user
```

**注意**: portfolio.py 只用到 `get_current_user`，不需要 admin

---

### 3. `app/routers/compare.py`

```python
# 刪除約第 20-50 行的 get_current_user 和 get_optional_user 定義

# 在 import 區加入
from app.dependencies import get_current_user, get_optional_user
```

---

### 4. `app/routers/watchlist.py`

```python
# 刪除重複的 get_current_user 定義

# 在 import 區加入
from app.dependencies import get_current_user
```

---

### 5. `app/routers/market.py`

```python
# 刪除約第 20-50 行的 get_current_user_optional 和 get_current_admin 定義

# 在 import 區加入
from app.dependencies import get_optional_user, get_admin_user

# 注意：market.py 使用的是 get_current_user_optional，需要改成 get_optional_user
# 或者使用向下相容別名 get_current_user_optional
```

---

### 6. `app/routers/admin.py`

```python
# admin.py 已經有自己的 get_admin_user，可以改用統一版本

# 在 import 區加入
from app.dependencies import get_admin_user

# 刪除原本的 get_admin_user 定義
```

---

## 🔍 快速搜尋指令

使用以下指令找出所有需要修改的檔案：

```bash
# 找出所有定義 get_current_user 的檔案
grep -rn "async def get_current_user" app/routers/

# 找出所有定義 get_current_admin 的檔案  
grep -rn "async def get_current_admin" app/routers/

# 找出所有定義 get_optional_user 的檔案
grep -rn "async def get_optional_user" app/routers/
grep -rn "async def get_current_user_optional" app/routers/
```

---

## ✅ 修改檢查清單

| 檔案 | 刪除重複認證 | 加入 import | 測試 |
|------|-------------|-------------|------|
| subscription.py | ☐ | ☐ | ☐ |
| portfolio.py | ☐ | ☐ | ☐ |
| compare.py | ☐ | ☐ | ☐ |
| watchlist.py | ☐ | ☐ | ☐ |
| market.py | ☐ | ☐ | ☐ |
| admin.py | ☐ | ☐ | ☐ |

---

## 💡 小技巧

1. **逐一修改**: 每改一個檔案就測試，確保沒問題再改下一個
2. **保留備份**: 修改前先 `cp file.py file.py.bak`
3. **IDE 搜尋**: 使用 VS Code 的全域搜尋功能更方便
