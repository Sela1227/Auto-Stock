"""
認證 API 路由
LINE Login 整合
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import hashlib
import hmac
import time
import urllib.parse
import logging

from app.database import get_async_session
from app.services.auth_service import AuthService
from app.schemas.schemas import LoginResponse, UserResponse, ErrorResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["認證"])

# 版本標識
AUTH_VERSION = "2.1.0-admin-update"


# ============================================================
# 🆕 管理員登入自動更新
# ============================================================

async def trigger_admin_updates():
    """
    管理員登入觸發的背景更新（優化版）
    - 🆕 只在股市開盤時間更新股票價格
    - 更新市場情緒指數（不受時間限制）
    """
    from app.database import SessionLocal
    from app.services.price_cache_service import is_tw_market_open, is_us_market_open
    
    tw_open = is_tw_market_open()
    us_open = is_us_market_open()
    
    logger.info(f"🔄 管理員登入，檢查更新狀態...")
    logger.info(f"   台股: {'開盤' if tw_open else '收盤'}, 美股: {'開盤' if us_open else '收盤'}")
    
    try:
        db = SessionLocal()
        
        # 1. 更新股票價格快取（🆕 只在開盤時）
        if tw_open or us_open:
            try:
                from app.services.price_cache_service import PriceCacheService
                cache_service = PriceCacheService(db)
                result = cache_service.update_all_prices()
                logger.info(f"✅ 股票價格更新完成: {result}")
            except Exception as e:
                logger.error(f"❌ 股票價格更新失敗: {e}")
        else:
            logger.info("💤 台股美股皆收盤，跳過股票價格更新")
        
        # 2. 更新市場情緒（總是更新）
        try:
            from app.services.market_service import market_service
            market_service.update_fear_greed()
            logger.info("✅ 市場情緒更新完成")
        except Exception as e:
            logger.error(f"❌ 市場情緒更新失敗: {e}")
        
        # 3. 抓取訂閱精選（如果有）
        try:
            from app.services.subscription_service import SubscriptionService
            sub_service = SubscriptionService(db)
            sub_result = sub_service.fetch_all_sources(backfill=False)
            logger.info(f"✅ 訂閱精選更新完成: {sub_result}")
        except Exception as e:
            logger.warning(f"⚠️ 訂閱精選更新跳過: {e}")
        
        db.close()
        logger.info("🎉 管理員自動更新完成")
        
    except Exception as e:
        logger.error(f"❌ 管理員自動更新失敗: {e}")


@router.get("/version", summary="認證模組版本")
async def auth_version():
    """回傳認證模組版本，用於確認部署"""
    return {
        "auth_version": AUTH_VERSION,
        "state_method": "HMAC",
        "jwt_key_set": bool(settings.JWT_SECRET_KEY and settings.JWT_SECRET_KEY != "your-secret-key-change-in-production"),
        "admin_auto_update": True,  # 🆕
    }


def create_state_token() -> str:
    """建立 state token (HMAC 簽名，有效期 10 分鐘)"""
    # 格式: timestamp.nonce.signature
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(8)  # 16 字元

    # 簽名
    message = f"{timestamp}.{nonce}"
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # 只取前 16 字元

    state = f"{timestamp}.{nonce}.{signature}"
    logger.info(f"Created state: {state}")
    return state


def verify_state_token(state: str) -> bool:
    """驗證 state token"""
    logger.info(f"Verifying state: {state}")
    try:
        parts = state.split(".")
        logger.info(f"State parts count: {len(parts)}")

        if len(parts) != 3:
            logger.warning(f"Invalid state format, expected 3 parts, got {len(parts)}")
            return False

        timestamp, nonce, signature = parts
        logger.info(f"timestamp={timestamp}, nonce={nonce}, signature={signature}")

        # 檢查是否過期 (10 分鐘)
        time_diff = int(time.time()) - int(timestamp)
        logger.info(f"Time difference: {time_diff} seconds")
        if time_diff > 600:
            logger.warning(f"State expired, time_diff={time_diff}")
            return False

        # 驗證簽名
        message = f"{timestamp}.{nonce}"
        expected_signature = hmac.new(
            settings.JWT_SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]

        logger.info(f"Expected signature: {expected_signature}")
        result = hmac.compare_digest(signature, expected_signature)
        logger.info(f"Signature match: {result}")

        return result
    except Exception as e:
        logger.error(f"State verification error: {e}")
        return False


@router.get("/line", summary="LINE 登入")
async def line_login():
    """
    導向 LINE 登入授權頁面
    """
    if not settings.LINE_LOGIN_CHANNEL_ID:
        raise HTTPException(
            status_code=500,
            detail="LINE Login 尚未設定"
        )

    # 產生 state
    state = create_state_token()

    # URL encode callback URL
    callback_url = urllib.parse.quote(settings.LINE_LOGIN_CALLBACK_URL, safe='')

    # 建立授權 URL
    auth_url = (
        "https://access.line.me/oauth2/v2.1/authorize"
        f"?response_type=code"
        f"&client_id={settings.LINE_LOGIN_CHANNEL_ID}"
        f"&redirect_uri={callback_url}"
        f"&state={state}"
        f"&scope=profile%20openid%20email"
    )

    logger.info(f"Redirecting to LINE with state: {state}")

    return RedirectResponse(url=auth_url)


@router.get("/line/callback", summary="LINE 登入回調")
async def line_callback(
    request: Request,
    background_tasks: BackgroundTasks,  # 🆕 加入 BackgroundTasks
    code: str = Query(..., description="授權碼"),
    state: str = Query(..., description="State"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    LINE 登入回調處理
    
    - 驗證 state
    - 用 code 換取 access token
    - 取得用戶資料
    - 建立/更新用戶
    - 🆕 管理員登入時觸發背景更新
    - 回傳 HTML 頁面儲存 Token 並跳轉
    """
    from fastapi.responses import HTMLResponse

    # 驗證 state (使用 JWT 驗證)
    if not verify_state_token(state):
        raise HTTPException(
            status_code=400,
            detail="Invalid state"
        )

    # 取得客戶端資訊
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # 執行登入流程
    auth_service = AuthService(db)
    result = await auth_service.login_with_line(code, client_ip, user_agent)

    if not result:
        # 可能是被封鎖的用戶
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SELA 自動選股系統</title>
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                .card {
                    background: white;
                    padding: 3rem;
                    border-radius: 1rem;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                    text-align: center;
                }
                h2 { color: #dc2626; margin: 0 0 1rem; }
                p { color: #64748b; margin: 0; }
                a { color: #3b82f6; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>⚠️ 登入失敗</h2>
                <p>您的帳號已被停用或登入過程發生錯誤</p>
                <p style="margin-top: 1rem;"><a href="/static/index.html">返回首頁</a></p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=403)

    # 回傳 HTML 頁面，將 Token 存入 localStorage 並跳轉到儀表板
    token = result["token"]
    user = result["user"]

    # 記錄登入成功的 log
    logger.info(f"=== 登入成功，準備跳轉 ===")
    logger.info(f"用戶 ID: {user.id}, LINE ID: {user.line_user_id}, 名稱: {user.display_name}")

    # 🆕 管理員登入觸發自動更新
    is_admin = getattr(user, 'is_admin', False)
    if is_admin:
        logger.info(f"🔑 管理員 {user.display_name} 登入，觸發背景更新")
        background_tasks.add_task(trigger_admin_updates)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>SELA 自動選股系統</title>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            .card {{
                background: white;
                padding: 3rem;
                border-radius: 1rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                text-align: center;
            }}
            .logo {{
                background-color: #FA7A35;
                color: white;
                font-weight: bold;
                font-size: 1.5rem;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                display: inline-block;
                margin-bottom: 1.5rem;
            }}
            .spinner {{
                width: 50px;
                height: 50px;
                border: 4px solid #e2e8f0;
                border-top: 4px solid #FA7A35;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1.5rem;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            h2 {{ color: #1e293b; margin: 0 0 0.5rem; }}
            p {{ color: #64748b; margin: 0; }}
            .admin-badge {{
                background: #fef3c7;
                color: #92400e;
                padding: 0.25rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.75rem;
                margin-top: 0.5rem;
                display: inline-block;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo">SELA</div>
            <div class="spinner"></div>
            <h2>登入成功！</h2>
            <p>歡迎回來，{user.display_name}</p>
            {'<div class="admin-badge">🔄 管理員模式 - 正在背景更新數據</div>' if is_admin else ''}
        </div>
        <script>
            // ★★★ 重要：先清除所有舊資料，避免 A 用戶看到 B 用戶的資料 ★★★
            localStorage.clear();
            sessionStorage.clear();
            
            // 設定新的用戶資料
            localStorage.setItem('token', '{token}');
            localStorage.setItem('user', JSON.stringify({{
                id: {user.id},
                display_name: "{user.display_name}",
                picture_url: "{user.picture_url or ''}",
                line_user_id: "{user.line_user_id}",
                is_admin: {'true' if is_admin else 'false'}
            }}));
            localStorage.setItem('login_time', new Date().toISOString());
            
            console.log('登入成功: 用戶 ID = {user.id}, LINE ID = {user.line_user_id}, 管理員 = {str(is_admin).lower()}');
            
            setTimeout(function() {{
                window.location.href = '/static/dashboard.html';
            }}, 1500);
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.post("/logout", summary="登出")
async def logout():
    """
    登出（前端清除 Token 即可）
    """
    return {"success": True, "message": "已登出"}


@router.get("/me", summary="取得當前用戶", response_model=UserResponse)
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得當前登入用戶資訊
    
    需要在 Header 帶入 Authorization: Bearer {token}
    """
    # 從 Header 取得 Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="未提供認證 Token"
        )

    token = auth_header.split(" ")[1]

    # 驗證 Token 並取得用戶
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="無效的 Token"
        )

    return UserResponse.model_validate(user)
