"""
認證 API 路由
LINE Login 整合
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
AUTH_VERSION = "2.0.0-hmac"


@router.get("/version", summary="認證模組版本")
async def auth_version():
    """回傳認證模組版本，用於確認部署"""
    return {
        "auth_version": AUTH_VERSION,
        "state_method": "HMAC",
        "jwt_key_set": bool(settings.JWT_SECRET_KEY and settings.JWT_SECRET_KEY != "your-secret-key-change-in-production"),
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
    - 回傳 HTML 頁面儲存 Token 並跳轉
    """
    from fastapi.responses import HTMLResponse
    
    # 驗證 state (使用 JWT 驗證)
    if not verify_state_token(state):
        raise HTTPException(
            status_code=400,
            detail="Invalid state"
        )
    
    # 執行登入流程
    auth_service = AuthService(db)
    result = await auth_service.login_with_line(code)
    
    if not result:
        raise HTTPException(
            status_code=401,
            detail="LINE 登入失敗"
        )
    
    # 回傳 HTML 頁面，將 Token 存入 localStorage 並跳轉到儀表板
    token = result["token"]
    user = result["user"]
    
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
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo">SELA</div>
            <div class="spinner"></div>
            <h2>登入成功！</h2>
            <p>歡迎回來，{user.display_name}</p>
        </div>
        <script>
            localStorage.setItem('token', '{token}');
            localStorage.setItem('user', JSON.stringify({{
                id: {user.id},
                display_name: "{user.display_name}",
                picture_url: "{user.picture_url or ''}",
                line_user_id: "{user.line_user_id}"
            }}));
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
